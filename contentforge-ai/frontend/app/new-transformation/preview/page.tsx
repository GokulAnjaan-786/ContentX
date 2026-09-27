"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  documentsApi,
  factsApi,
  DocumentMetadata,
  ContentMetadata,
  FactRegistryItem,
} from "@/lib/api";
import { ContentPreview } from "@/components/preview/ContentPreview";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { Skeleton } from "@/components/shared/Skeleton";
import { Sparkles } from "lucide-react";

function PreviewContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const documentId = searchParams.get("documentId");

  const [document, setDocument] = useState<DocumentMetadata | null>(null);
  const [metadata, setMetadata] = useState<ContentMetadata | null>(null);
  const [facts, setFacts] = useState<FactRegistryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadingStep, setLoadingStep] = useState("Loading document metadata...");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!documentId) {
      router.replace("/new-transformation/upload");
      return;
    }

    const loadData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        setLoadingStep("Fetching document record...");
        const doc = await documentsApi.get(documentId);
        setDocument(doc);

        setLoadingStep("Extracting Fact Registry & running Understanding Pass...");
        let factsList = await factsApi.list(documentId).catch(() => ({ facts: [] }));

        let meta: ContentMetadata | null = null;
        try {
          meta = await factsApi.getMetadata(documentId);
        } catch {
          try {
            const passRes = await factsApi.runUnderstandingPass(documentId);
            meta = {
              id: "pass-" + documentId,
              document_id: documentId,
              summary: passRes.summary,
              document_type: passRes.document_type,
              entities: passRes.entities,
              topics: passRes.topics,
              created_at: new Date().toISOString(),
            };
            factsList = await factsApi.list(documentId);
          } catch {
            meta = {
              id: "meta-" + documentId,
              document_id: documentId,
              summary: "Document ingested and ready for coordinated generation.",
              document_type: doc.source_type,
              entities: { people: [], organisations: [], locations: [], products_systems: [] },
              topics: ["general"],
              created_at: new Date().toISOString(),
            };
          }
        }

        setMetadata(meta);
        setFacts(factsList.facts || []);
      } catch (err: any) {
        const msg =
          err?.response?.data?.detail ||
          err?.message ||
          "Failed to load document facts and understanding pass data.";
        setError(typeof msg === "string" ? msg : JSON.stringify(msg));
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [documentId, router]);

  const handleProceed = () => {
    router.push(`/new-transformation/output-selection?documentId=${documentId}`);
  };

  const handleBack = () => {
    router.push("/new-transformation/upload");
  };

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6 py-12">
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-4">
          <div className="relative w-14 h-14 mx-auto">
            <div className="w-14 h-14 rounded-full border-4 border-brand-100 border-t-brand-600 animate-spin" />
            <Sparkles className="w-5 h-5 text-brand-600 absolute inset-0 m-auto" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-slate-900">
              Understanding Pass In Progress
            </h3>
            <p className="text-xs text-slate-500">{loadingStep}</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <ErrorMessage
          title="Content Preview Error"
          message={error}
          onRetry={() => window.location.reload()}
        />
        <button
          onClick={handleBack}
          className="text-xs font-semibold text-brand-600 hover:underline"
        >
          ← Return to Upload Screen
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center gap-2 text-xs font-semibold text-brand-600">
        <span>STEP 2 OF 3</span>
        <span>•</span>
        <span>CONTENT UNDERSTANDING & FACT VERIFICATION</span>
      </div>

      <ContentPreview
        document={document}
        metadata={metadata}
        facts={facts}
        onProceed={handleProceed}
        onBack={handleBack}
      />
    </div>
  );
}

export default function PreviewPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-4xl mx-auto space-y-6 py-12 text-center">
          <div className="w-10 h-10 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin mx-auto" />
        </div>
      }
    >
      <PreviewContent />
    </Suspense>
  );
}
