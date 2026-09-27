"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { documentsApi } from "@/lib/api";
import { Uploader } from "@/components/upload/Uploader";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { Loader2, Sparkles, FileText, CheckCircle2 } from "lucide-react";

export default function UploadPage() {
  const router = useRouter();
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const pollDocumentStatus = async (documentId: string) => {
    setProcessingStatus("Document uploaded. Parsing and chunking content...");
    const maxAttempts = 30;
    let attempts = 0;

    const interval = setInterval(async () => {
      attempts++;
      try {
        const doc = await documentsApi.get(documentId);
        if (doc.processed_status === "processed") {
          clearInterval(interval);
          setProcessingStatus("Processing complete! Redirecting to Content Preview...");
          setTimeout(() => {
            router.push(`/new-transformation/preview?documentId=${documentId}`);
          }, 600);
        } else if (doc.processed_status === "failed") {
          clearInterval(interval);
          setIsProcessing(false);
          setError(
            doc.error_message ||
              "Document ingestion and processing failed. Please verify the document format."
          );
        } else {
          setProcessingStatus(
            `Analyzing document text structure (attempt ${attempts})...`
          );
        }
      } catch (err: any) {
        clearInterval(interval);
        setIsProcessing(false);
        setError("Error checking document status. Backend service may be unreachable.");
      }

      if (attempts >= maxAttempts) {
        clearInterval(interval);
        setIsProcessing(false);
        setError("Document processing timed out. Please try again.");
      }
    }, 2000);
  };

  const handleUploadFile = async (file: File) => {
    setIsProcessing(true);
    setError(null);
    setProcessingStatus("Uploading file to secure storage...");

    try {
      const response = await documentsApi.upload(file);
      await pollDocumentStatus(response.document_id);
    } catch (err: any) {
      setIsProcessing(false);
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        "Upload failed. Please check network connection and file format.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    }
  };

  const handleUploadText = async (text: string, title?: string) => {
    setIsProcessing(true);
    setError(null);
    setProcessingStatus("Submitting text for chunking and ingestion...");

    try {
      const response = await documentsApi.upload(text, title);
      await pollDocumentStatus(response.document_id);
    } catch (err: any) {
      setIsProcessing(false);
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        "Text submission failed. Please try again.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-in fade-in duration-200">
      {/* Step Indicator Header */}
      <div>
        <div className="flex items-center gap-2 text-xs font-semibold text-brand-600 mb-1">
          <span>STEP 1 OF 3</span>
          <span>•</span>
          <span>SOURCE INGESTION</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Input Source Document
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Upload a research report, security advisory, or article. The engine will ingest and chunk the text before initiating the Fact Registry Understanding Pass.
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <ErrorMessage
          title="Upload or Processing Error"
          message={error}
          onRetry={() => {
            setError(null);
            setIsProcessing(false);
          }}
        />
      )}

      {/* Processing Overlay / Loading Card */}
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
              Processing Source Content
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              {processingStatus}
            </p>
          </div>

          <div className="pt-4 flex items-center justify-center gap-2 text-xs text-slate-400">
            <FileText className="w-4 h-4" />
            <span>Validating MIME, Antivirus scanning & text chunking</span>
          </div>
        </div>
      ) : (
        <Uploader
          onUploadFile={handleUploadFile}
          onUploadText={handleUploadText}
          isSubmitting={isProcessing}
        />
      )}
    </div>
  );
}
