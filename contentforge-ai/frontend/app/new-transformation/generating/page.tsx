"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { generationApi, GenerationJobDetail, OutputType } from "@/lib/api";
import { OUTPUT_TYPE_REGISTRY } from "@/components/output-cards";
import { ErrorMessage } from "@/components/shared/ErrorMessage";
import { Badge } from "@/components/shared/Badge";
import {
  Sparkles,
  Loader2,
  CheckCircle2,
  Clock,
  ShieldCheck,
} from "lucide-react";

function GeneratingContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const jobId = searchParams.get("jobId");
  const documentId = searchParams.get("documentId");

  const [job, setJob] = useState<GenerationJobDetail | null>(null);
  const [secondsElapsed, setSecondsElapsed] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) {
      router.replace("/new-transformation/upload");
      return;
    }

    const timer = setInterval(() => {
      setSecondsElapsed((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [jobId, router]);

  useEffect(() => {
    if (!jobId) return;

    let isMounted = true;
    const pollInterval = setInterval(async () => {
      try {
        const jobData = await generationApi.getJob(jobId);
        if (!isMounted) return;
        setJob(jobData);

        if (
          jobData.status === "completed" ||
          jobData.status === "completed_with_warnings"
        ) {
          clearInterval(pollInterval);
          setTimeout(() => {
            router.push(`/results/${jobId}`);
          }, 800);
        } else if (jobData.status === "failed") {
          clearInterval(pollInterval);
          setError(
            jobData.error_message ||
              "Generation job encountered an error during parallel synthesis."
          );
        }
      } catch (err: any) {
        console.warn("Poll attempt notice:", err.message);
      }
    }, 2000);

    return () => {
      isMounted = false;
      clearInterval(pollInterval);
    };
  }, [jobId, router]);

  const completedOutputs = job?.outputs?.map((o) => o.output_type) || [];

  return (
    <div className="max-w-2xl mx-auto space-y-8 py-8 animate-in fade-in duration-200">
      {/* Center Spinner Banner */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-8 sm:p-10 text-center space-y-6">
        <div className="relative w-20 h-20 mx-auto">
          <div className="w-20 h-20 rounded-full border-4 border-brand-100 border-t-brand-600 animate-spin" />
          <Sparkles className="w-8 h-8 text-brand-600 absolute inset-0 m-auto animate-pulse" />
        </div>

        <div className="space-y-2">
          <Badge variant="brand" size="md">
            AI ORCHESTRATOR PASS IN PROGRESS
          </Badge>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Synthesizing Fact-Grounded Outputs
          </h1>
          <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
            The orchestrator is generating each selected output format in parallel from the single Fact Registry, then applying strict schema validation and citation verification.
          </p>
        </div>

        {/* Timer Banner */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 text-slate-600 text-xs font-mono">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>Elapsed Time: {secondsElapsed}s (Est. 10-25s)</span>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <ErrorMessage
          title="Generation Failed"
          message={error}
          onRetry={() => {
            setError(null);
            router.push(`/new-transformation/output-selection?documentId=${documentId || ""}`);
          }}
        />
      )}

      {/* Granular Output Status List */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Pipeline Progress by Output Channel
          </h3>
          <span className="text-xs font-mono text-brand-600 font-semibold">
            {completedOutputs.length} / {job?.outputs?.length || 1} Ready
          </span>
        </div>

        <div className="space-y-3">
          {job?.outputs && job.outputs.length > 0 ? (
            job.outputs.map((output) => {
              const meta = OUTPUT_TYPE_REGISTRY[output.output_type];
              const isDone = output.status === "completed" || output.status === "completed_with_warnings";

              return (
                <div
                  key={output.id || output.output_type}
                  className="flex items-center justify-between p-3.5 rounded-xl border border-slate-200 bg-slate-50/50"
                >
                  <div className="flex items-center gap-3">
                    {isDone ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                    ) : (
                      <Loader2 className="w-5 h-5 text-brand-600 animate-spin shrink-0" />
                    )}
                    <div>
                      <p className="text-xs font-bold text-slate-900">
                        {meta?.label || output.output_type}
                      </p>
                      <p className="text-[11px] text-slate-400">
                        {isDone
                          ? `Validated • ${Math.round(output.validation_score * 100)}% source-grounded`
                          : "Evaluating citations against Fact Registry..."}
                      </p>
                    </div>
                  </div>

                  <div>
                    {isDone ? (
                      <Badge variant="success" size="sm">Done</Badge>
                    ) : (
                      <Badge variant="brand" size="sm">Processing</Badge>
                    )}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="space-y-2.5">
              {["Orchestrator dispatching parallel generators...", "Extracting citations from Fact Registry...", "Validating consistency across channels..."].map((step, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-3 p-3 rounded-xl border border-slate-200 bg-slate-50/40 text-xs text-slate-600"
                >
                  <Loader2 className="w-4 h-4 text-brand-600 animate-spin shrink-0" />
                  <span>{step}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
          <span className="flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            Automatic Hallucination Guard Active
          </span>
          <span>Will automatically advance to Results</span>
        </div>
      </div>
    </div>
  );
}

export default function GeneratingPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-2xl mx-auto space-y-6 py-12 text-center">
          <div className="w-10 h-10 border-4 border-brand-200 border-t-brand-600 rounded-full animate-spin mx-auto" />
        </div>
      }
    >
      <GeneratingContent />
    </Suspense>
  );
}
