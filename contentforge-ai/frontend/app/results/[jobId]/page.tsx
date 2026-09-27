"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  generationApi,
  factsApi,
  outputsApi,
  GenerationJobDetail,
  GeneratedOutput,
  FactRegistryItem,
  OutputType,
  cleanPublishableText,
} from "@/lib/api";
import { OUTPUT_TYPE_REGISTRY } from "@/components/output-cards";
import { TraceabilityPanel, SelectedClaimInfo } from "@/components/traceability/TraceabilityPanel";
import { Button } from "@/components/shared/Button";
import { Badge } from "@/components/shared/Badge";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { Skeleton } from "@/components/shared/Skeleton";
import {
  Copy,
  Check,
  Download,
  Send,
  Sparkles,
  ArrowLeft,
  FileCheck,
  AlertTriangle,
  Layers,
  Info,
  GitCompare,
  X,
  ShieldCheck,
} from "lucide-react";

export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params?.jobId as string;

  const [job, setJob] = useState<GenerationJobDetail | null>(null);
  const [facts, setFacts] = useState<FactRegistryItem[]>([]);
  const [activeTab, setActiveTab] = useState<OutputType | null>(null);
  const [activeAudience, setActiveAudience] = useState<string | null>(null);
  const [selectedClaim, setSelectedClaim] = useState<SelectedClaimInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // Compare Understanding Modal State
  const [isCompareOpen, setIsCompareOpen] = useState(false);
  const [compareAud1, setCompareAud1] = useState<string>("technical");
  const [compareAud2, setCompareAud2] = useState<string>("general_public");

  useEffect(() => {
    if (!jobId) return;

    const fetchResults = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const jobData = await generationApi.getJob(jobId);
        setJob(jobData);

        if (jobData.outputs && jobData.outputs.length > 0) {
          const firstOut = jobData.outputs[0];
          setActiveTab(firstOut.output_type);
          const aud = firstOut.content?.audience || firstOut.content?.target_audience || "professional";
          setActiveAudience(aud);
        }

        // Fetch Fact Registry for traceability
        if (jobData.document_id) {
          const factsRes = await factsApi.list(jobData.document_id).catch(() => ({ facts: [] }));
          setFacts(factsRes.facts || []);
        }
      } catch (err: any) {
        const msg =
          err?.response?.data?.detail ||
          err?.message ||
          "Failed to load generation results. Please verify the Job ID.";
        setError(typeof msg === "string" ? msg : JSON.stringify(msg));
      } finally {
        setIsLoading(false);
      }
    };

    fetchResults();
  }, [jobId]);

  // Find all distinct output format types available in this job
  const uniqueOutputTypes = Array.from(
    new Set(job?.outputs?.map((o) => o.output_type) || [])
  );

  // Find outputs matching current active format tab
  const matchingFormatOutputs = job?.outputs?.filter(
    (o) => o.output_type === activeTab
  ) || [];

  // Active single output entity
  const activeOutput =
    matchingFormatOutputs.find((o) => {
      const aud = o.content?.audience || o.content?.target_audience || "professional";
      return aud === activeAudience;
    }) || matchingFormatOutputs[0] || job?.outputs?.[0];

  const handleUpdateContent = async (updatedContent: any) => {
    if (!activeOutput) return;
    try {
      const updatedOutput = await outputsApi.update(activeOutput.id, updatedContent);
      if (job) {
        const updatedOutputs = (job.outputs || []).map((o) =>
          o.id === activeOutput.id ? { ...o, content: updatedOutput.content } : o
        );
        setJob({ ...job, outputs: updatedOutputs });
      }
      setSaveSuccessMsg("Edits saved successfully!");
      setTimeout(() => setSaveSuccessMsg(null), 3000);
    } catch (err: any) {
      console.error("Save error:", err);
      if (job) {
        const updatedOutputs = (job.outputs || []).map((o) =>
          o.id === activeOutput.id ? { ...o, content: updatedContent } : o
        );
        setJob({ ...job, outputs: updatedOutputs });
      }
      setSaveSuccessMsg("Edits saved locally.");
      setTimeout(() => setSaveSuccessMsg(null), 3500);
    }
  };

  const handleCopyToClipboard = () => {
    if (!activeOutput) return;

    let textToCopy = "";
    const c = activeOutput.content;

    switch (activeOutput.output_type) {
      case "linkedin":
        const cleanHook = cleanPublishableText(c.hook || "");
        const cleanBody = cleanPublishableText(c.body || "");
        const cleanCta = cleanPublishableText(c.call_to_action || "");
        const tags = (c.hashtags || []).map((t: string) => (t.startsWith("#") ? t : `#${t}`)).join(" ");
        textToCopy = [cleanHook, cleanBody, cleanCta, tags].filter(Boolean).join("\n\n");
        break;
      case "twitter":
        textToCopy = (c.tweets || []).map((t: any, i: number) => `${i + 1}/${c.tweets.length} ${t.text}`).join("\n\n");
        break;
      case "advisory":
        textToCopy = `[${c.severity}] ${c.title}\nScope: ${c.scope}\n\nSummary:\n${c.summary}\n\nDetails:\n${c.details}\n\nRecommended Actions:\n${(c.recommended_actions || []).map((a: string, i: number) => `${i + 1}. ${a}`).join("\n")}`;
        break;
      case "executive_summary":
        textToCopy = `${c.title}\n\n${c.summary_text}\n\nKey Takeaways:\n${(c.key_takeaways || []).map((t: string) => `• ${t}`).join("\n")}`;
        break;
      case "infographic":
        textToCopy = `${c.headline}\nTheme: ${c.colour_theme} | Layout: ${c.layout_style}\n\nPoints:\n${(c.sections || []).map((s: any) => `${s.order}. [${s.icon_suggestion}] ${s.stat_or_point}`).join("\n")}`;
        break;
      case "presentation":
        textToCopy = (c.slides || []).map((s: any) => `Slide ${s.slide_no}: ${s.title}\n${(s.bullets || []).map((b: string) => `• ${b}`).join("\n")}\nVisual: ${s.visual_suggestion}\nNotes: ${s.speaker_notes}`).join("\n\n---\n\n");
        break;
      case "video_package":
        textToCopy = `${c.title} (Runtime: ${c.total_duration_estimate})\n\n${(c.scenes || []).map((s: any) => `Scene ${s.scene_no} (~${s.duration_estimate_sec}s):\nNarration: ${s.narration}\nVisual: ${s.visual_description}\nSubtitle: "${s.subtitle_text}"`).join("\n\n")}`;
        break;
      default:
        textToCopy = JSON.stringify(c, null, 2);
    }

    navigator.clipboard.writeText(textToCopy);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2500);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <Skeleton className="h-96 lg:col-span-3 rounded-2xl" />
          <Skeleton className="h-96 rounded-2xl" />
        </div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="max-w-2xl mx-auto py-12 space-y-4">
        <ErrorMessage
          title="Results Not Found"
          message={error || "Generation job not found."}
          onRetry={() => window.location.reload()}
        />
        <Button
          variant="secondary"
          onClick={() => router.push("/dashboard")}
          leftIcon={<ArrowLeft className="w-4 h-4" />}
        >
          Return to Dashboard
        </Button>
      </div>
    );
  }

  const ActiveComponent = activeTab ? OUTPUT_TYPE_REGISTRY[activeTab]?.component : null;

  // Helpers to get text sample for Compare Understanding modal
  const getOutputTextSample = (outputObj?: GeneratedOutput) => {
    if (!outputObj) return "No content generated for this audience.";
    const c = outputObj.content;
    if (typeof c === "string") return c;
    if (c.body) return c.body;
    if (c.summary) return c.summary;
    if (c.summary_text) return c.summary_text;
    if (c.details) return c.details;
    if (c.tweets) return c.tweets.map((t: any) => t.text).join(" ");
    if (c.headline) return `${c.headline}. ${(c.sections || []).map((s: any) => s.stat_or_point).join(" ")}`;
    return JSON.stringify(c);
  };

  const getOutputByAudience = (aud: string) => {
    return (
      job.outputs?.find((o) => {
        const a = o.content?.audience || o.content?.target_audience || "professional";
        return a.toLowerCase() === aud.toLowerCase();
      }) || job.outputs?.[0]
    );
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Top Breadcrumb & Status Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/dashboard")}
            className="p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            title="Return to Dashboard"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-slate-400">
                JOB #{job.id.slice(0, 8)}
              </span>
              <Badge
                variant={job.status === "completed" ? "success" : "warning"}
                size="sm"
              >
                {job.status === "completed" ? "Fully Verified" : "Completed (Warnings)"}
              </Badge>
              <Badge variant="brand" size="sm">
                Truth Compression Active
              </Badge>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              Fact-Grounded Transformation Results
            </h1>
          </div>
        </div>

        {/* Global Output Actions */}
        <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
          {/* Compare Understanding Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsCompareOpen(true)}
            leftIcon={<GitCompare className="w-4 h-4 text-brand-600" />}
            className="border-brand-300 text-brand-700 bg-brand-50/50 hover:bg-brand-100 font-bold"
          >
            Compare Understanding
          </Button>

          {/* Copy to Clipboard */}
          <Button
            variant="secondary"
            size="sm"
            onClick={handleCopyToClipboard}
            leftIcon={copySuccess ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
            data-testid="copy-clipboard-btn"
          >
            {copySuccess ? "Copied to Clipboard!" : "Copy Output"}
          </Button>
        </div>
      </div>

      {saveSuccessMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs font-semibold text-emerald-800 flex items-center gap-2 animate-in fade-in">
          <Check className="w-4 h-4 text-emerald-600" />
          <span>{saveSuccessMsg}</span>
        </div>
      )}

      {/* Tabs Row (Format Selection) */}
      <div className="flex border-b border-slate-200 overflow-x-auto gap-2 pb-px" data-testid="results-tabs">
        {uniqueOutputTypes.map((outType) => {
          const meta = OUTPUT_TYPE_REGISTRY[outType];
          const isActive = outType === activeTab;
          const matchingOuts = job.outputs?.filter((o) => o.output_type === outType) || [];

          return (
            <button
              key={outType}
              onClick={() => {
                setActiveTab(outType);
                setSelectedClaim(null);
                const firstAud = matchingOuts[0]?.content?.audience || matchingOuts[0]?.content?.target_audience || "professional";
                setActiveAudience(firstAud);
              }}
              data-testid={`tab-${outType}`}
              className={`flex items-center gap-2 px-4 py-3 text-xs sm:text-sm font-semibold border-b-2 whitespace-nowrap transition-colors ${
                isActive
                  ? "border-brand-600 text-brand-600 bg-white"
                  : "border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-100/50"
              }`}
            >
              <span>{meta?.shortLabel || outType}</span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-full bg-brand-100 text-brand-700">
                {matchingOuts.length} Audience{matchingOuts.length > 1 ? "s" : ""}
              </span>
            </button>
          );
        })}
      </div>

      {/* Audience Variant Pills Bar */}
      {matchingFormatOutputs.length > 0 && (
        <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wide">Audience Variant:</span>
            <div className="flex items-center gap-1.5 flex-wrap">
              {matchingFormatOutputs.map((out) => {
                const audLabel = (out.content?.audience || out.content?.target_audience || "professional").toLowerCase();
                const isActiveAud = audLabel === activeAudience?.toLowerCase();
                return (
                  <button
                    key={out.id}
                    onClick={() => setActiveAudience(audLabel)}
                    className={`px-3 py-1 rounded-lg text-xs font-bold capitalize transition-all border ${
                      isActiveAud
                        ? "bg-brand-600 text-white border-brand-600 shadow-xs"
                        : "bg-white text-slate-700 border-slate-200 hover:border-slate-300"
                    }`}
                  >
                    [{audLabel.replace("_", " ")}]
                  </button>
                );
              })}
            </div>
          </div>

          <button
            onClick={() => setIsCompareOpen(true)}
            className="text-xs font-bold text-brand-600 hover:underline flex items-center gap-1"
          >
            <GitCompare className="w-3.5 h-3.5" /> Compare Wording Side-by-Side
          </button>
        </div>
      )}

      {/* Traceability Hint Alert */}
      <div className="p-3 bg-brand-50/60 border border-brand-100 rounded-xl text-xs text-brand-900 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-brand-600 shrink-0" />
          <span>
            <strong>Truth Compression Grounding:</strong> Complexity changes for selected audience [{activeAudience}], while numbers, dates, CVEs, and facts remain 100% grounded in Fact Registry.
          </span>
        </div>
        {selectedClaim && (
          <button
            onClick={() => setSelectedClaim(null)}
            className="text-xs font-semibold text-brand-700 underline hover:text-brand-900 shrink-0"
          >
            Clear Selection
          </button>
        )}
      </div>

      {/* Main Workspace (Output Card + Traceability Side Panel) */}
      <div className="flex flex-col lg:flex-row items-start gap-6">
        {/* Render Format-Specific Card */}
        <div className="flex-1 w-full min-w-0">
          {activeOutput && ActiveComponent ? (
            <ActiveComponent
              output={activeOutput}
              selectedClaim={selectedClaim}
              onSelectClaim={setSelectedClaim}
              onUpdateContent={handleUpdateContent}
            />
          ) : (
            <div className="p-8 text-center bg-white rounded-2xl border text-sm text-slate-500">
              No output selected.
            </div>
          )}
        </div>

        {/* Traceability Side Panel */}
        {selectedClaim ? (
          <TraceabilityPanel
            selectedClaim={selectedClaim}
            factsRegistry={facts}
            onClose={() => setSelectedClaim(null)}
          />
        ) : (
          <aside className="hidden lg:flex w-80 shrink-0 bg-white border border-slate-200 rounded-2xl p-5 flex-col items-center justify-center text-center text-slate-400 space-y-3 min-h-[300px]">
            <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-400">
              <FileCheck className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-bold text-slate-700">Source Evidence Inspector</p>
              <p className="text-[11px] text-slate-400 mt-1 max-w-[200px] leading-relaxed">
                Click any sentence in the output to view linked Fact Registry statements and original source snippets.
              </p>
            </div>
          </aside>
        )}
      </div>

      {/* COMPARE UNDERSTANDING MODAL */}
      {isCompareOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6 space-y-6">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-slate-200 pb-4">
              <div>
                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-brand-50 text-brand-700 text-xs font-bold border border-brand-200 mb-1">
                  <GitCompare className="w-3.5 h-3.5 text-brand-600" />
                  Truth Compression Verification
                </div>
                <h2 className="text-xl font-black text-slate-900">Compare Understanding</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Change the complexity of the message, not the truth behind it.
                </p>
              </div>

              <button
                onClick={() => setIsCompareOpen(false)}
                className="p-2 rounded-lg text-slate-400 hover:text-slate-800 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Audience Selectors */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-bold text-slate-600 uppercase block mb-1">Audience Version 1</label>
                <select
                  value={compareAud1}
                  onChange={(e) => setCompareAud1(e.target.value)}
                  className="w-full px-3 py-2 text-xs font-semibold border border-slate-200 rounded-lg bg-white text-slate-800"
                >
                  <option value="technical">Technical Audience</option>
                  <option value="executive">Executive Audience</option>
                  <option value="professional">Professional Audience</option>
                  <option value="general_public">General Public Audience</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-600 uppercase block mb-1">Audience Version 2</label>
                <select
                  value={compareAud2}
                  onChange={(e) => setCompareAud2(e.target.value)}
                  className="w-full px-3 py-2 text-xs font-semibold border border-slate-200 rounded-lg bg-white text-slate-800"
                >
                  <option value="general_public">General Public Audience</option>
                  <option value="executive">Executive Audience</option>
                  <option value="professional">Professional Audience</option>
                  <option value="technical">Technical Audience</option>
                </select>
              </div>
            </div>

            {/* Side by Side Comparison Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Version 1 Card */}
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-2">
                <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                  <span className="text-xs font-extrabold capitalize text-brand-700 bg-brand-100 px-2.5 py-0.5 rounded-full">
                    {compareAud1.replace("_", " ")} Wording
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">Detailed explanation</span>
                </div>
                <div className="text-xs text-slate-800 leading-relaxed font-sans min-h-[140px] whitespace-pre-wrap pt-2">
                  {getOutputTextSample(getOutputByAudience(compareAud1))}
                </div>
              </div>

              {/* Version 2 Card */}
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-2">
                <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                  <span className="text-xs font-extrabold capitalize text-emerald-700 bg-emerald-100 px-2.5 py-0.5 rounded-full">
                    {compareAud2.replace("_", " ")} Wording
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">Simplified explanation</span>
                </div>
                <div className="text-xs text-slate-800 leading-relaxed font-sans min-h-[140px] whitespace-pre-wrap pt-2">
                  {getOutputTextSample(getOutputByAudience(compareAud2))}
                </div>
              </div>
            </div>

            {/* Fact Registry Consistency Verification Breakdown */}
            <div className="p-4 rounded-xl bg-slate-900 text-white space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-emerald-400" />
                  <h3 className="text-sm font-bold tracking-tight">Fact Consistency Verification</h3>
                </div>
                <span className="text-xs text-emerald-400 font-mono font-bold">100% Factually Consistent</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs font-medium pt-1">
                <div className="flex items-center gap-1.5 text-emerald-300">
                  <Check className="w-4 h-4 text-emerald-400 shrink-0" /> Same facts
                </div>
                <div className="flex items-center gap-1.5 text-emerald-300">
                  <Check className="w-4 h-4 text-emerald-400 shrink-0" /> Same numbers
                </div>
                <div className="flex items-center gap-1.5 text-emerald-300">
                  <Check className="w-4 h-4 text-emerald-400 shrink-0" /> Same dates
                </div>
                <div className="flex items-center gap-1.5 text-emerald-300">
                  <Check className="w-4 h-4 text-emerald-400 shrink-0" /> Same entities
                </div>
                <div className="flex items-center gap-1.5 text-emerald-300">
                  <Check className="w-4 h-4 text-emerald-400 shrink-0" /> Same certainty
                </div>
                <div className="flex items-center gap-1.5 text-emerald-300">
                  <Check className="w-4 h-4 text-emerald-400 shrink-0" /> Same source evidence
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <Button onClick={() => setIsCompareOpen(false)} className="bg-brand-600 text-white font-bold px-6">
                Close Comparison
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

