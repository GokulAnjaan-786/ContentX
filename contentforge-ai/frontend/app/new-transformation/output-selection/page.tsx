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
import { Sparkles, CheckCircle2, Users, SlidersHorizontal, ShieldCheck } from "lucide-react";

interface AudienceOption {
  id: string;
  label: string;
  description: string;
}

const AUDIENCE_OPTIONS: AudienceOption[] = [
  { id: "technical", label: "Technical", description: "Preserves exact technical jargon, CVEs, version numbers, and deep implementation detail." },
  { id: "executive", label: "Executive", description: "Focuses on strategic impact, risk, key findings, and decision-maker recommendations." },
  { id: "professional", label: "Professional", description: "Balanced technical depth with high readability for general business publishing." },
  { id: "general_public", label: "General Public", description: "Simplifies complex jargon into clear language while preserving all underlying numbers & facts." },
];

function OutputSelectionContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const documentId = searchParams.get("documentId");

  const [selectedOutputs, setSelectedOutputs] = useState<OutputType[]>([
    "linkedin",
    "executive_summary",
  ]);

  const [selectedAudiences, setSelectedAudiences] = useState<string[]>(["automatic"]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [slideCount, setSlideCount] = useState<number>(5);

  const defaultSettings: GenerationSettings = {
    audience: "Executive / C-Suite",
    tone: "Authoritative & Direct",
    language: "English",
    detail_level: "standard",
    objective: "Strategic stakeholder briefing and publication-ready transformation",
    slide_count: slideCount,
  };

  const toggleOutput = (type: OutputType) => {
    if (selectedOutputs.includes(type)) {
      setSelectedOutputs(selectedOutputs.filter((t) => t !== type));
    } else {
      setSelectedOutputs([...selectedOutputs, type]);
    }
  };

  const handleSelectAllOutputs = () => {
    setSelectedOutputs([...ALL_OUTPUT_TYPES]);
  };

  const handleClearAllOutputs = () => {
    setSelectedOutputs([]);
  };

  const toggleAudience = (audId: string) => {
    if (audId === "automatic") {
      setSelectedAudiences(["automatic"]);
      return;
    }

    const withoutAuto = selectedAudiences.filter((a) => a !== "automatic");
    if (withoutAuto.includes(audId)) {
      const remaining = withoutAuto.filter((a) => a !== audId);
      setSelectedAudiences(remaining.length === 0 ? ["automatic"] : remaining);
    } else {
      setSelectedAudiences([...withoutAuto, audId]);
    }
  };

  const isAutomatic = selectedAudiences.includes("automatic");

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
        selected_audiences: selectedAudiences,
        settings: {
          ...defaultSettings,
          slide_count: slideCount,
        },
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
    <div className="max-w-4xl mx-auto space-y-10 animate-in fade-in duration-200">
      {/* Page Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-bold border border-brand-200 mb-3">
          <Sparkles className="w-3.5 h-3.5 text-brand-600" />
          ContentX Truth Compression Engine
        </div>
        <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
          Select Formats & Target Audience Understanding
        </h1>
        <p className="text-sm text-slate-500 mt-1 max-w-2xl">
          Change the complexity of the message, not the truth behind it. ContentX uses the exact same verified Fact Registry across all output formats and audience profiles.
        </p>
      </div>

      {error && (
        <ErrorMessage
          title="Generation Error"
          message={error}
          onRetry={() => setError(null)}
        />
      )}

      {/* SECTION 1: Output Formats */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-3">
          <div>
            <span className="text-xs font-mono font-bold text-brand-600 uppercase tracking-wider block mb-0.5">Section 1</span>
            <h2 className="text-lg font-bold text-slate-900">What would you like to generate?</h2>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSelectAllOutputs}
              className="text-xs"
            >
              Select All
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearAllOutputs}
              className="text-xs text-slate-500"
            >
              Clear All
            </Button>
          </div>
        </div>

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
                className={`p-5 rounded-2xl border-2 cursor-pointer transition-all flex flex-col justify-between gap-3 ${
                  isSelected
                    ? "border-brand-600 bg-brand-50/30 shadow-xs"
                    : "border-slate-200 bg-white hover:border-slate-300"
                }`}
              >
                <div className="flex items-start gap-4">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => {}} // Handled by div onClick
                    className="mt-1 w-4 h-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500 shrink-0 cursor-pointer"
                  />
                  <div className="space-y-1">
                    <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      <span>{meta.label}</span>
                      {type === "presentation" && isSelected && (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 border border-purple-200">
                          {slideCount} Slides (Default: 5)
                        </span>
                      )}
                    </h3>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      {meta.description}
                    </p>
                  </div>
                </div>

                {type === "presentation" && isSelected && (
                  <div
                    onClick={(e) => e.stopPropagation()}
                    className="mt-2 pt-2 border-t border-purple-100 flex items-center justify-between"
                  >
                    <label className="text-xs font-semibold text-slate-700">Slide Count:</label>
                    <div className="flex items-center gap-1.5">
                      {[5, 6, 7, 8, 10, 12].map((num) => (
                        <button
                          key={num}
                          type="button"
                          onClick={() => setSlideCount(num)}
                          className={`text-xs px-2.5 py-1 rounded-lg border font-bold transition-all ${
                            slideCount === num
                              ? "bg-purple-600 border-purple-600 text-white shadow-xs"
                              : "bg-white border-slate-200 text-slate-700 hover:border-purple-300"
                          }`}
                        >
                          {num}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* SECTION 2: Audience & Understanding (TRUTH COMPRESSION) */}
      <div className="space-y-4 pt-4 border-t border-slate-200">
        <div>
          <span className="text-xs font-mono font-bold text-brand-600 uppercase tracking-wider block mb-0.5">Section 2</span>
          <h2 className="text-lg font-bold text-slate-900">Who should understand this content?</h2>
          <p className="text-xs text-slate-500 mt-1">
            ContentX will adjust the complexity and explanation level while keeping the underlying facts consistent.
          </p>
        </div>

        {/* Automatic Toggle Control */}
        <div
          onClick={() => toggleAudience("automatic")}
          className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex items-center justify-between ${
            isAutomatic
              ? "border-brand-600 bg-brand-50/40 shadow-xs"
              : "border-slate-200 bg-white hover:border-slate-300"
          }`}
        >
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={isAutomatic}
              onChange={() => {}}
              className="w-4 h-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500 shrink-0 cursor-pointer"
            />
            <div>
              <div className="flex items-center gap-2">
                <h4 className="text-sm font-bold text-slate-900">Automatic Audience Mapping</h4>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-brand-100 text-brand-700">Recommended</span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Automatically selects optimal audience complexity for each format (e.g. Advisory → Technical, Exec Summary → Executive, LinkedIn → Professional).
              </p>
            </div>
          </div>
          <SlidersHorizontal className="w-5 h-5 text-brand-600 hidden sm:block shrink-0" />
        </div>

        {/* Audience Profile Selection Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
          {AUDIENCE_OPTIONS.map((aud) => {
            const isSelected = !isAutomatic && selectedAudiences.includes(aud.id);
            return (
              <div
                key={aud.id}
                onClick={() => toggleAudience(aud.id)}
                className={`p-4 rounded-xl border-2 cursor-pointer transition-all flex items-start gap-3 ${
                  isSelected
                    ? "border-brand-600 bg-brand-50/30 shadow-xs"
                    : "border-slate-200 bg-white hover:border-slate-300 opacity-90"
                }`}
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => {}}
                  className="mt-0.5 w-4 h-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500 shrink-0 cursor-pointer"
                />
                <div>
                  <h4 className="text-sm font-bold text-slate-900">{aud.label}</h4>
                  <p className="text-xs text-slate-500 leading-relaxed mt-0.5">{aud.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Truth Compression Guarantee Banner */}
      <div className="p-4 rounded-xl bg-slate-900 text-slate-200 text-xs flex items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0" />
          <span>
            <strong>Immutable Fact Guarantee:</strong> Facts, numbers, dates, CVEs, and certainty remain identical regardless of selected audience.
          </span>
        </div>
      </div>

      {/* Primary Action Button */}
      <div className="pt-2 flex justify-end">
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

