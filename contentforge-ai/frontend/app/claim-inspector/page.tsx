"use client";

import React, { useState } from "react";
import {
  Search,
  CheckCircle2,
  FileText,
  Database,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
  HelpCircle,
} from "lucide-react";
import { Badge } from "@/components/shared/Badge";

export default function ClaimInspectorPage() {
  const [selectedClaimIndex, setSelectedClaimIndex] = useState<number>(0);

  const claims = [
    {
      generated_claim: "An unauthenticated Remote Code Execution (RCE) vulnerability with a CVSS score of 9.8 has been identified in Windows Server 2022 Remote Access Licensing Service.",
      fact_id: "f1",
      fact_statement: "An unauthenticated Remote Code Execution (RCE) vulnerability (CVE-2024-38077) affects Windows Server 2022 Remote Access Licensing Service.",
      original_source_snippet: "Security researchers identified CVE-2024-38077 allowing unauthenticated remote code execution in Windows Server 2022 licensing stack.",
      source_page: 2,
      certainty: "confirmed",
      validation_status: "passed",
      output_format: "LinkedIn / Advisory / Twitter",
    },
    {
      generated_claim: "Transaction hash 0x8f2a1b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a transferred 15,000 MATIC on Polygon Amoy testnet.",
      fact_id: "f2",
      fact_statement: "Transaction hash 0x8f2a1b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a transferred 15,000 MATIC on Polygon Amoy testnet.",
      original_source_snippet: "Polygon Amoy incident log records tx 0x8f2a1b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a moving 15,000 MATIC token payload.",
      source_page: 4,
      certainty: "confirmed",
      validation_status: "passed",
      output_format: "Blockchain Advisory / Infographic",
    },
  ];

  const activeClaim = claims[selectedClaimIndex];

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-bold border border-brand-200 mb-2">
          <Search className="w-3.5 h-3.5" />
          Traceability & Verification Feature
        </div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight">Claim Inspector</h1>
        <p className="text-sm text-slate-500 mt-1">
          Inspect generated claims to trace their exact source snippets, Fact Registry IDs, page numbers, certainty, and grounding status.
        </p>
      </div>

      {/* Main Grid: Left Claim Selector, Right Traceability Pipeline */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Generated Claims */}
        <div className="lg:col-span-5 space-y-3">
          <h2 className="text-sm font-extrabold text-slate-900 uppercase tracking-wider">
            Generated Claims ({claims.length})
          </h2>

          <div className="space-y-2">
            {claims.map((item, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedClaimIndex(idx)}
                className={`w-full text-left p-4 rounded-xl border transition-all ${
                  selectedClaimIndex === idx
                    ? "bg-brand-50/80 border-brand-500 shadow-sm ring-1 ring-brand-500"
                    : "bg-white border-slate-200 hover:bg-slate-50"
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <span className="text-[11px] font-bold text-slate-500 uppercase">
                    Claim #{idx + 1}
                  </span>
                  <Badge variant="success">Passed</Badge>
                </div>
                <p className="text-xs font-bold text-slate-900 line-clamp-3 leading-relaxed">
                  {item.generated_claim}
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* Right Column: Traceability Chain (Generated Claim -> Fact ID -> Fact Statement -> Source Snippet -> Source Page -> Certainty -> Validation Status) */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-brand-600" /> Grounding Pipeline Inspection
            </h2>
            <Badge variant="success">Validation Status: {activeClaim.validation_status.toUpperCase()}</Badge>
          </div>

          <div className="space-y-4">
            {/* Step 1: Generated Claim */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[10px] font-bold uppercase text-brand-700 tracking-wider">
                1. Public Generated Claim (Clean — No exposed [f1] tags)
              </span>
              <p className="text-sm font-bold text-slate-900">
                &quot;{activeClaim.generated_claim}&quot;
              </p>
            </div>

            <div className="flex justify-center">
              <ArrowRight className="w-4 h-4 text-slate-400 rotate-90" />
            </div>

            {/* Step 2: Internal Fact ID & Fact Statement */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase text-slate-500 tracking-wider">
                  2. Fact Registry Link
                </span>
                <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-brand-100 text-brand-800">
                  Fact ID: [{activeClaim.fact_id}]
                </span>
              </div>
              <p className="text-xs font-semibold text-slate-800">
                {activeClaim.fact_statement}
              </p>
            </div>

            <div className="flex justify-center">
              <ArrowRight className="w-4 h-4 text-slate-400 rotate-90" />
            </div>

            {/* Step 3: Source Snippet & Page */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase text-slate-500 tracking-wider">
                  3. Original Source Evidence
                </span>
                <span className="text-xs font-medium text-slate-600">
                  Source Page: {activeClaim.source_page}
                </span>
              </div>
              <p className="text-xs italic font-mono text-slate-900 bg-white p-2.5 rounded border border-slate-200">
                &quot;{activeClaim.original_source_snippet}&quot;
              </p>
            </div>

            <div className="flex justify-center">
              <ArrowRight className="w-4 h-4 text-slate-400 rotate-90" />
            </div>

            {/* Step 4: Certainty & Status */}
            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-between text-xs text-emerald-900 font-bold">
              <span>Certainty Status: {activeClaim.certainty.toUpperCase()}</span>
              <span className="flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                100% Grounded
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
