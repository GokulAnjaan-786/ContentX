import React from "react";
import { FactRegistryItem, UnverifiedClaim } from "@/lib/api";
import { X, ShieldCheck, AlertTriangle, FileText, ExternalLink, Sparkles } from "lucide-react";
import { Badge } from "../shared/Badge";

export interface SelectedClaimInfo {
  claimText: string;
  factIds?: string[];
  isUnverified?: boolean;
  unverifiedReason?: string;
}

export interface TraceabilityPanelProps {
  selectedClaim: SelectedClaimInfo | null;
  factsRegistry: FactRegistryItem[];
  onClose: () => void;
}

export const TraceabilityPanel: React.FC<TraceabilityPanelProps> = ({
  selectedClaim,
  factsRegistry,
  onClose,
}) => {
  if (!selectedClaim) return null;

  // Find matched facts from registry
  const matchedFacts = (selectedClaim.factIds || [])
    .map((fid) => {
      const cleanFid = fid.toLowerCase().replace(/\[|\]/g, "").trim();
      return factsRegistry.find(
        (f) =>
          f.fact_id_string.toLowerCase() === cleanFid ||
          f.id === fid ||
          f.fact_id_string.toLowerCase() === `f${cleanFid}` ||
          cleanFid.includes(f.fact_id_string.toLowerCase())
      );
    })
    .filter((f): f is FactRegistryItem => !!f);

  const isUnverified =
    selectedClaim.isUnverified ||
    (!selectedClaim.factIds || selectedClaim.factIds.length === 0) ||
    matchedFacts.length === 0;

  return (
    <aside
      data-testid="traceability-panel"
      className="w-full lg:w-96 shrink-0 bg-white border border-slate-200 rounded-2xl shadow-sm p-5 flex flex-col gap-4 animate-in fade-in duration-200"
    >
      {/* Panel Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-brand-50 text-brand-600">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Source Traceability</h3>
            <p className="text-[11px] text-slate-500">Fact Registry Evidence</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
          aria-label="Close traceability panel"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Selected Claim Quote */}
      <div className="rounded-xl bg-slate-50 p-3 border border-slate-200">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
          Selected Claim
        </span>
        <blockquote className="mt-1 text-xs text-slate-800 italic leading-relaxed">
          &ldquo;{selectedClaim.claimText}&rdquo;
        </blockquote>
      </div>

      {/* Verification Status */}
      {isUnverified ? (
        <div
          data-testid="traceability-unverified-alert"
          className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-amber-900"
        >
          <div className="flex items-start gap-2.5">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-bold text-amber-900">
                No matching source text found
              </p>
              <p className="mt-1 text-xs text-amber-800 leading-relaxed">
                This claim could not be matched to the source document.
              </p>
              {selectedClaim.unverifiedReason && (
                <p className="mt-2 text-[11px] text-amber-700 bg-amber-100/60 p-2 rounded-lg font-mono">
                  {selectedClaim.unverifiedReason}
                </p>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Verified Source Grounding</span>
            </div>
            <Badge variant="success" size="sm">
              {matchedFacts.length} Fact{matchedFacts.length > 1 ? "s" : ""} Linked
            </Badge>
          </div>

          {/* Matched Facts Evidence */}
          <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
            {matchedFacts.map((fact) => (
              <div
                key={fact.id || fact.fact_id_string}
                data-testid={`fact-evidence-${fact.fact_id_string}`}
                className="rounded-xl border border-slate-200 bg-white p-3 shadow-xs space-y-2 hover:border-brand-300 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-brand-700 bg-brand-50 px-2 py-0.5 rounded border border-brand-200">
                    [{fact.fact_id_string.toUpperCase()}]
                  </span>
                  <span className="text-[10px] text-slate-500 font-medium">
                    {Math.round(fact.confidence * 100)}% Fact Confidence
                  </span>
                </div>

                <div>
                  <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide">
                    Registered Fact
                  </span>
                  <p className="text-xs text-slate-800 font-medium mt-0.5">
                    {fact.fact_statement}
                  </p>
                </div>

                {fact.source_snippet ? (
                  <div className="mt-2 pt-2 border-t border-slate-100 bg-slate-50 p-2.5 rounded-lg">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                      <ExternalLink className="w-3 h-3 text-slate-400" />
                      Original Source Snippet
                    </span>
                    <p
                      data-testid="traceability-source-snippet"
                      className="mt-1 text-xs text-slate-700 leading-relaxed font-serif bg-white p-2 rounded border border-slate-200"
                    >
                      &ldquo;{fact.source_snippet}&rdquo;
                    </p>
                  </div>
                ) : (
                  <p className="text-[11px] text-slate-400 italic">
                    Source sentence tied directly to document chunk index.
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </aside>
  );
};
