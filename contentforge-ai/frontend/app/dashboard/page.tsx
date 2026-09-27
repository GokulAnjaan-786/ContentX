"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { historyApi, documentsApi, HistoryItem } from "@/lib/api";
import { getStoredUser, isAuthenticated } from "@/lib/auth";
import { Uploader } from "@/components/upload/Uploader";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { Badge } from "@/components/shared/Badge";
import { Skeleton } from "@/components/shared/Skeleton";
import {
  ShieldCheck,
  FileText,
  ArrowRight,
  Sparkles,
} from "lucide-react";

export default function DashboardPage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState<string>("");
  const [uploadError, setUploadError] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
    if (!isAuthenticated()) {
      router.replace("/login");
    }
  }, [router]);

  const user = getStoredUser();

  const { data: jobs, isLoading, error: historyError } = useQuery<HistoryItem[]>({
    queryKey: ["recent-jobs"],
    queryFn: () => historyApi.list(5),
    enabled: mounted && isAuthenticated(),
  });

  const pollDocumentStatus = async (documentId: string) => {
    setProcessingStatus("Extracting content...");
    const maxAttempts = 30;
    let attempts = 0;

    const interval = setInterval(async () => {
      attempts++;
      try {
        const doc = await documentsApi.get(documentId);
        if (doc.processed_status === "processed") {
          clearInterval(interval);
          setProcessingStatus("Document analysis completed! Preparing content generation...");
          setTimeout(() => {
            router.push(`/new-transformation/output-selection?documentId=${documentId}`);
          }, 800);
        } else if (doc.processed_status === "failed") {
          clearInterval(interval);
          setIsProcessing(false);
          setUploadError(
            doc.error_message ||
              "Document could not be processed. Please check the file format and try again."
          );
        } else {
          setProcessingStatus(
            attempts < 5
              ? "Extracting content..."
              : attempts < 10
              ? "Understanding document & extracting facts..."
              : "Preparing content generation..."
          );
        }
      } catch (err: any) {
        clearInterval(interval);
        setIsProcessing(false);
        setUploadError("Error checking document status. Please try again.");
      }

      if (attempts >= maxAttempts) {
        clearInterval(interval);
        setIsProcessing(false);
        setUploadError("Document processing timed out. Please try again.");
      }
    }, 2000);
  };

  const handleUploadFile = async (file: File) => {
    setIsProcessing(true);
    setUploadError(null);
    setProcessingStatus("Uploading document...");

    try {
      const response = await documentsApi.upload(file);
      await pollDocumentStatus(response.document_id);
    } catch (err: any) {
      setIsProcessing(false);
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        "Upload failed. Please check network connection and file format.";
      setUploadError(typeof msg === "string" ? msg : JSON.stringify(msg));
    }
  };

  const handleUploadText = async (text: string, title?: string) => {
    setIsProcessing(true);
    setUploadError(null);
    setProcessingStatus("Uploading document...");

    try {
      const response = await documentsApi.upload(text, title);
      await pollDocumentStatus(response.document_id);
    } catch (err: any) {
      setIsProcessing(false);
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        "Text submission failed. Please try again.";
      setUploadError(typeof msg === "string" ? msg : JSON.stringify(msg));
    }
  };

  if (!mounted) return null;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <Badge variant="success">Verified</Badge>;
      case "completed_with_warnings":
        return <Badge variant="warning">Review Required</Badge>;
      case "processing":
        return <Badge variant="brand">Processing</Badge>;
      case "failed":
        return <Badge variant="danger">Failed</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-200">
      {/* Header Banner */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-semibold border border-brand-200">
          <ShieldCheck className="w-4 h-4 text-brand-600" />
          ContentX Platform • Single Source. Multi-Format Transformation.
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          Upload & Transform Your Content
        </h1>
        <p className="text-slate-500 text-sm max-w-xl mx-auto">
          Upload a PDF, DOCX, or TXT document. ContentX automatically analyzes the source, builds the Fact Registry, and generates publication-ready content across formats.
        </p>
      </div>

      {/* Upload Error Alert */}
      {uploadError && (
        <ErrorMessage
          title="Processing Error"
          message={uploadError}
          onRetry={() => {
            setUploadError(null);
            setIsProcessing(false);
          }}
        />
      )}

      {/* Prominent Upload Area */}
      {isProcessing ? (
        <div
          data-testid="upload-processing-indicator"
          className="bg-white rounded-2xl border border-slate-200 shadow-sm p-12 text-center space-y-6"
        >
          <div className="relative w-16 h-16 mx-auto">
            <div className="w-16 h-16 rounded-full border-4 border-brand-100 border-t-brand-600 animate-spin" />
            <Sparkles className="w-6 h-6 text-brand-600 absolute inset-0 m-auto" />
          </div>

          <div className="space-y-2 max-w-sm mx-auto">
            <h3 className="text-lg font-bold text-slate-900">
              Analyzing Document
            </h3>
            <p className="text-xs text-brand-700 font-semibold leading-relaxed">
              {processingStatus}
            </p>
          </div>
        </div>
      ) : (
        <Uploader
          onUploadFile={handleUploadFile}
          onUploadText={handleUploadText}
          isSubmitting={isProcessing}
        />
      )}

      {/* Recent Transformations Section */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900">
              Recent Transformations
            </h2>
            <p className="text-xs text-slate-500">
              Access your previous document transformations & generated outputs
            </p>
          </div>
          {jobs && jobs.length > 0 && (
            <Link
              href="/history"
              className="text-xs font-bold text-brand-600 hover:text-brand-700 flex items-center gap-1"
            >
              View History <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          )}
        </div>

        {isLoading ? (
          <div className="p-6 space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="flex items-center justify-between py-3 border-b">
                <div className="space-y-1">
                  <Skeleton className="h-4 w-48" />
                  <Skeleton className="h-3 w-32" />
                </div>
                <Skeleton className="h-6 w-20 rounded-full" />
              </div>
            ))}
          </div>
        ) : historyError ? (
          <div className="p-6 text-center text-xs text-slate-500">
            History details available after first document upload.
          </div>
        ) : !jobs || jobs.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">
            No transformations yet. Upload a document above to get started.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {jobs.map((job) => (
              <Link
                key={job.id}
                href={`/results/${job.job_id}`}
                className="flex items-center justify-between p-4 hover:bg-slate-50/80 transition-colors group text-xs"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center shrink-0 group-hover:bg-brand-600 group-hover:text-white transition-colors">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 group-hover:text-brand-600 transition-colors">
                      {job.document_title || "Untitled Document"}
                    </h3>
                    <p className="text-slate-400 text-[11px] mt-0.5">
                      {new Date(job.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {getStatusBadge(job.status)}
                  <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-700 transition-colors" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
