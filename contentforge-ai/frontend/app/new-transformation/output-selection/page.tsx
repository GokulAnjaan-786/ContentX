"use client";

import React, { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  OutputType,
  GenerationSettings,
  generationApi,
} from "@/lib/api";
import {
  OUTPUT_TYPE_REGISTRY,
  ALL_OUTPUT_TYPES,
} from "@/components/output-cards";
import { Button } from "@/components/shared/Button";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { Sparkles, CheckCircle2 } from "lucide-react";

function OutputSelectionContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const documentId = searchParams.get("documentId");

  const [selectedOutputs, setSelectedOutputs] = useState<OutputType[]>([
    "linkedin",
    "executive_summary",
  ]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Default background settings
  const defaultSettings: GenerationSettings = {
    audience: "Executive / C-Suite",
    tone: "Authoritative & Direct",
    language: "English",
    detail_level: "standard",
    objective: "Strategic stakeholder briefing and publication-ready transformation",
  };

  const toggleOutput = (type: OutputType) => {
    if (selectedOutputs.includes(type)) {
      setSelectedOutputs(selectedOutputs.filter((t) => t !== type));
    } else {
      setSelectedOutputs([...selectedOutputs, type]);
    }
  };

  const handleSelectAll = () => {
    setSelectedOutputs([...ALL_OUTPUT_TYPES]);
  };

  const handleClearAll = () => {
    setSelectedOutputs([]);
  };

  const handleGenerate = async () => {
    if (!documentId) {
      router.push("/dashboard");
      return;
    }

    if (selectedOutputs.length === 0) {
      setError("Please select at least one output format to generate.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await generationApi.generate({
        document_id: documentId,
        selected_outputs: selectedOutputs,
        settings: defaultSettings,
      });

      router.push(
        `/new-transformation/generating?jobId=${response.job_id}&documentId=${documentId}`
      );
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        "Failed to initiate content generation. Please try again.";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            What would you like ContentX to generate?
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Select one or multiple output formats to synthesize from the verified source.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleSelectAll}
            className="text-xs"
          >
            Select All
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearAll}
            className="text-xs text-slate-500"
          >
            Clear All
          </Button>
        </div>
      </div>

      {error && (
        <ErrorMessage
          title="Generation Error"
          message={error}
          onRetry={() => setError(null)}
        />
      )}

      {/* Selectable Output Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {ALL_OUTPUT_TYPES.map((type) => {
          const meta = OUTPUT_TYPE_REGISTRY[type];
          const isSelected = selectedOutputs.includes(type);

          return (
            <div
              key={type}
              onClick={() => toggleOutput(type)}
              data-testid={`output-card-${type}`}
              className={`p-5 rounded-2xl border-2 cursor-pointer transition-all flex items-start gap-4 ${
                isSelected
                  ? "border-brand-600 bg-brand-50/30 shadow-xs"
                  : "border-slate-200 bg-white hover:border-slate-300"
              }`}
            >
              <input
                type="checkbox"
                checked={isSelected}
                onChange={() => {}} // Handled by div onClick
                className="mt-1 w-4 h-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500 shrink-0 cursor-pointer"
              />
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-slate-900">
                  {meta.label}
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  {meta.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Primary Action Button */}
      <div className="pt-4 flex justify-end">
        <Button
          size="lg"
          onClick={handleGenerate}
          disabled={selectedOutputs.length === 0 || isSubmitting}
          isLoading={isSubmitting}
          rightIcon={<Sparkles className="w-4 h-4 text-white" />}
          className="w-full sm:w-auto bg-brand-600 hover:bg-brand-700 text-white font-bold px-8 shadow-md"
          data-testid="generate-outputs-btn"
        >
          {selectedOutputs.length === 0
            ? "Select at Least 1 Output"
            : `Generate ${selectedOutputs.length} Format${selectedOutputs.length > 1 ? "s" : ""}`}
        </Button>
      </div>
    </div>
  );
}

export default function OutputSelectionPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-4xl mx-auto space-y-6 py-12 text-center">
          <div className="w-10 h-10 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin mx-auto" />
        </div>
      }
    >
      <OutputSelectionContent />
    </Suspense>
  );
}
