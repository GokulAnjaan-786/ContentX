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
} from "lucide-react";

export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params?.jobId as string;

  const [job, setJob] = useState<GenerationJobDetail | null>(null);
  const [facts, setFacts] = useState<FactRegistryItem[]>([]);
  const [activeTab, setActiveTab] = useState<OutputType | null>(null);
  const [selectedClaim, setSelectedClaim] = useState<SelectedClaimInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const fetchResults = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const jobData = await generationApi.getJob(jobId);
        setJob(jobData);

        if (jobData.outputs && jobData.outputs.length > 0) {
          setActiveTab(jobData.outputs[0].output_type);
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

  const activeOutput = job?.outputs?.find((o) => o.output_type === activeTab);

  const handleUpdateContent = async (updatedContent: any) => {
    if (!activeOutput) return;
    try {
      const updatedOutput = await outputsApi.update(activeOutput.id, updatedContent);
      // Update local state
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
      // Even if backend PUT is not yet deployed, save locally
      if (job) {
        const updatedOutputs = (job.outputs || []).map((o) =>
          o.id === activeOutput.id ? { ...o, content: updatedContent } : o
        );
        setJob({ ...job, outputs: updatedOutputs });
      }
      setSaveSuccessMsg("Edits saved locally (Backend PUT /outputs/{id} pending Part 4).");
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
            </div>
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              Fact-Grounded Transformation Results
            </h1>
          </div>
        </div>

        {/* Global Output Actions */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
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

          {/* Download PDF/DOCX Stub */}
          <div className="relative group">
            <Button
              variant="secondary"
              size="sm"
              leftIcon={<Download className="w-4 h-4 text-slate-400" />}
              className="text-slate-500"
              title="Enterprise Document Export coming in Part 4"
            >
              Export PDF/DOCX
            </Button>
            <div className="absolute right-0 top-full mt-1.5 hidden group-hover:block z-20 w-48 p-2 rounded-lg bg-slate-900 text-[11px] text-slate-200 shadow-lg text-center">
              PDF/DOCX Document Exporter coming in Part 4.
            </div>
          </div>

          {/* Disabled Send for Review Placeholder (Part 4) */}
          <div className="relative group">
            <Button
              variant="primary"
              size="sm"
              disabled
              leftIcon={<Send className="w-4 h-4 opacity-50" />}
              className="opacity-60 cursor-not-allowed bg-slate-400 border-none"
              data-testid="send-for-review-btn"
            >
              Send for Review
            </Button>
            <div className="absolute right-0 top-full mt-1.5 hidden group-hover:block z-20 w-56 p-2 rounded-lg bg-slate-900 text-[11px] text-slate-200 shadow-lg text-center">
              Reviewer & Approval workflow is scheduled for Part 4.
            </div>
          </div>
        </div>
      </div>

      {saveSuccessMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs font-semibold text-emerald-800 flex items-center gap-2 animate-in fade-in">
          <Check className="w-4 h-4 text-emerald-600" />
          <span>{saveSuccessMsg}</span>
        </div>
      )}

      {/* Tabs Row (1 Tab per Generated Output Type) */}
      <div className="flex border-b border-slate-200 overflow-x-auto gap-2 pb-px" data-testid="results-tabs">
        {job.outputs?.map((output) => {
          const meta = OUTPUT_TYPE_REGISTRY[output.output_type];
          const isActive = output.output_type === activeTab;

          return (
            <button
              key={output.id || output.output_type}
              onClick={() => {
                setActiveTab(output.output_type);
                setSelectedClaim(null); // reset selected claim on tab change
              }}
              data-testid={`tab-${output.output_type}`}
              className={`flex items-center gap-2 px-4 py-3 text-xs sm:text-sm font-semibold border-b-2 whitespace-nowrap transition-colors ${
                isActive
                  ? "border-brand-600 text-brand-600 bg-white"
                  : "border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-100/50"
              }`}
            >
              <span>{meta?.shortLabel || output.output_type}</span>
              <span
                className={`text-[10px] font-mono px-1.5 py-0.2 rounded-full ${
                  isActive
                    ? "bg-brand-100 text-brand-700"
                    : "bg-slate-200 text-slate-600"
                }`}
              >
                {Math.round(output.validation_score * 100)}%
              </span>
            </button>
          );
        })}
      </div>

      {/* Traceability Hint Alert */}
      <div className="p-3 bg-brand-50/60 border border-brand-100 rounded-xl text-xs text-brand-900 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-brand-600 shrink-0" />
          <span>
            <strong>Interactive Traceability:</strong> Click any sentence or claim to inspect its exact source evidence in the Fact Registry. Unverified claims are underlined in orange.
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
    </div>
  );
}
