"use client";

import React, { useState } from "react";
import {
  ContentMetadata,
  FactRegistryItem,
  DocumentMetadata,
} from "@/lib/api";
import {
  FileCheck2,
  Tag,
  Building2,
  Users,
  MapPin,
  Cpu,
  ArrowRight,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Search,
  Quote,
} from "lucide-react";
import { Badge } from "../shared/Badge";
import { Button } from "../shared/Button";

export interface ContentPreviewProps {
  document: DocumentMetadata | null;
  metadata: ContentMetadata | null;
  facts: FactRegistryItem[];
  onProceed: () => void;
  onBack?: () => void;
}

export const ContentPreview: React.FC<ContentPreviewProps> = ({
  document,
  metadata,
  facts,
  onProceed,
  onBack,
}) => {
  const [searchFilter, setSearchFilter] = useState("");

  const filteredFacts = facts.filter((f) => {
    if (!searchFilter.trim()) return true;
    const query = searchFilter.toLowerCase();
    return (
      f.fact_statement.toLowerCase().includes(query) ||
      f.fact_id_string.toLowerCase().includes(query) ||
      (f.source_snippet && f.source_snippet.toLowerCase().includes(query))
    );
  });

  return (
    <div className="w-full space-y-8 animate-in fade-in duration-300">
      {/* Overview Banner */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                <FileCheck2 className="w-3.5 h-3.5" />
                Understanding Pass Complete
              </span>
              <span className="text-xs text-slate-400">•</span>
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                Type: {metadata?.document_type || document?.source_type || "Document"}
              </span>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 mt-1">
              {document?.file_name || "Source Content Extraction"}
            </h1>
          </div>
          <div className="flex items-center gap-3">
            {onBack && (
              <Button variant="secondary" onClick={onBack}>
                Re-upload
              </Button>
            )}
            <Button
              size="lg"
              onClick={onProceed}
              rightIcon={<ArrowRight className="w-4 h-4" />}
              data-testid="continue-to-output-btn"
            >
              Looks good, continue
            </Button>
          </div>
        </div>

        {/* PII Detection Alert */}
        {document?.pii_detected && (
          <div
            data-testid="pii-warning-banner"
            className="mt-4 p-3.5 rounded-xl border border-amber-300 bg-amber-50 text-amber-900 text-xs flex items-start gap-3"
          >
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Personally Identifiable Information (PII) Detected:</span>
              <p className="mt-0.5 text-amber-800 leading-relaxed">
                This document contains sensitive information matching categories:{" "}
                <span className="font-mono font-semibold uppercase">
                  {(document.pii_types || []).join(", ")}
                </span>
                . Please verify source grounding and ensure private data is not broadcast to public channels.
              </p>
            </div>
          </div>
        )}

        {/* Prompt Injection Warning Alert */}
        {document?.injection_flagged && (
          <div
            data-testid="injection-warning-banner"
            className="mt-4 p-3.5 rounded-xl border border-rose-300 bg-rose-50 text-rose-900 text-xs flex items-start gap-3"
          >
            <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Adversarial Instructions Quarantined:</span>
              <p className="mt-0.5 text-rose-800 leading-relaxed">
                Text patterns resembling prompt injection were identified in the source content. ContentForge AI has isolated these directives to prevent output schema hijacking.
              </p>
            </div>
          </div>
        )}

        {/* AI Summary */}
        <div className="mt-6">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
            Executive Summary (Understanding Pass)
          </h2>
          <p className="text-slate-800 leading-relaxed text-sm bg-slate-50 p-4 rounded-xl border border-slate-200/80">
            {metadata?.summary ||
              "The document was successfully parsed, tokenized, and embedded. Key facts and entities have been cataloged below."}
          </p>
        </div>

        {/* Entities and Topics Grid */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Entities */}
          <div className="p-4 rounded-xl border border-slate-200 bg-white">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5 text-brand-600" />
              Detected Entities
            </h3>
            <div className="space-y-2 text-xs">
              {metadata?.entities?.organisations && metadata.entities.organisations.length > 0 && (
                <div className="flex items-start gap-2">
                  <span className="text-slate-400 shrink-0 font-medium">Orgs:</span>
                  <div className="flex flex-wrap gap-1">
                    {metadata.entities.organisations.map((org, i) => (
                      <Badge key={i} variant="brand" size="sm">
                        {org}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              {metadata?.entities?.products_systems && metadata.entities.products_systems.length > 0 && (
                <div className="flex items-start gap-2">
                  <span className="text-slate-400 shrink-0 font-medium">Systems:</span>
                  <div className="flex flex-wrap gap-1">
                    {metadata.entities.products_systems.map((item, i) => (
                      <Badge key={i} variant="neutral" size="sm">
                        {item}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              {metadata?.entities?.people && metadata.entities.people.length > 0 && (
                <div className="flex items-start gap-2">
                  <span className="text-slate-400 shrink-0 font-medium">People:</span>
                  <div className="flex flex-wrap gap-1">
                    {metadata.entities.people.map((p, i) => (
                      <Badge key={i} variant="neutral" size="sm">
                        {p}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              {metadata?.entities?.locations && metadata.entities.locations.length > 0 && (
                <div className="flex items-start gap-2">
                  <span className="text-slate-400 shrink-0 font-medium">Locations:</span>
                  <div className="flex flex-wrap gap-1">
                    {metadata.entities.locations.map((loc, i) => (
                      <Badge key={i} variant="neutral" size="sm">
                        {loc}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Topics */}
          <div className="p-4 rounded-xl border border-slate-200 bg-white">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
              <Tag className="w-3.5 h-3.5 text-brand-600" />
              Detected Topics & Taxonomy
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {metadata?.topics && metadata.topics.length > 0 ? (
                metadata.topics.map((t, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200"
                  >
                    #{t}
                  </span>
                ))
              ) : (
                <span className="text-xs text-slate-400 italic">No specific taxonomy tags</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Fact Registry Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-brand-600" />
              <h2 className="text-lg font-bold text-slate-900">
                Fact Registry ({facts.length} Verified Facts)
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Immutable ground-truth facts extracted during the single understanding pass. All 7 generators will cite these exact entries.
            </p>
          </div>

          {/* Search Facts */}
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search facts or snippets..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
        </div>

        {/* Fact Cards */}
        <div className="mt-5 space-y-3">
          {filteredFacts.map((fact) => (
            <div
              key={fact.id || fact.fact_id_string}
              className="p-4 rounded-xl border border-slate-200/90 bg-slate-50/50 hover:bg-white hover:border-brand-300 transition-colors"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-brand-50 text-brand-700 border border-brand-200">
                    [{fact.fact_id_string.toUpperCase()}]
                  </span>
                  <span className="text-xs text-slate-400">•</span>
                  <span className="text-xs text-slate-500 font-medium">
                    Confidence: {Math.round(fact.confidence * 100)}%
                  </span>
                </div>
              </div>

              {/* Fact Statement */}
              <p className="text-sm font-semibold text-slate-900 mt-2">
                {fact.fact_statement}
              </p>

              {/* Source Snippet */}
              {fact.source_snippet && (
                <div className="mt-2.5 p-3 rounded-lg bg-white border border-slate-200 text-xs text-slate-600 flex items-start gap-2">
                  <Quote className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                  <p className="italic font-serif leading-relaxed">
                    &ldquo;{fact.source_snippet}&rdquo;
                  </p>
                </div>
              )}
            </div>
          ))}

          {filteredFacts.length === 0 && (
            <div className="py-8 text-center text-slate-500 text-xs">
              No facts match the filter &ldquo;{searchFilter}&rdquo;.
            </div>
          )}
        </div>

        {/* Footer Proceed CTA */}
        <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
          <p className="text-xs text-slate-500 italic">
            Review only. Fact registry statements are locked to preserve source integrity.
          </p>
          <Button
            size="lg"
            onClick={onProceed}
            rightIcon={<ArrowRight className="w-4 h-4" />}
            data-testid="bottom-continue-btn"
          >
            Looks good, continue
          </Button>
        </div>
      </div>
    </div>
  );
};
