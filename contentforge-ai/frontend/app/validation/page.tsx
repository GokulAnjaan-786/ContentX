"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  ShieldCheck,
  Search,
  RotateCcw,
  CheckCircle2,
  Lock,
} from "lucide-react";
import { Badge } from "@/components/shared/Badge";
import { Button } from "@/components/shared/Button";

export default function ValidationCenterPage() {
  const [activeFilter, setActiveFilter] = useState<"all" | "passed" | "review">("all");

  const validationRuns = [
    {
      id: "val-1",
      document_title: "Windows Licensing RCE Security Advisory (CVE-2024-38077)",
      domain: "Cybersecurity Intelligence",
      status: "passed",
      confidence_score: 1.0,
      checks: [
        { name: "Source Grounding Check", status: "passed", detail: "All claims verified against Fact Registry" },
        { name: "Cross-Output Metric Consistency", status: "passed", detail: "CVSS 9.8 and KB5040437 match across all 7 formats" },
        { name: "Domain ID Preservation", status: "passed", detail: "CVE-2024-38077 correctly matched source" },
        { name: "Prompt Injection & Security Scan", status: "passed", detail: "Zero prompt injection vectors detected" },
      ],
      issues: [],
    },
    {
      id: "val-2",
      document_title: "Polygon Amoy On-Chain Incident Report",
      domain: "Blockchain Intelligence",
      status: "review_required",
      confidence_score: 0.65,
      checks: [
        { name: "Source Grounding Check", status: "passed", detail: "On-chain transaction facts grounded" },
        { name: "Cross-Output Metric Consistency", status: "failed", detail: "Number conflict detected: 15,000 MATIC reported in Advisory vs 150,000 MATIC reported in Presentation" },
        { name: "Domain ID Preservation", status: "passed", detail: "Tx hash 0x8f2a... matched exactly" },
      ],
      issues: [
        {
          type: "cross_output_number_mismatch",
          severity: "critical",
          description: "Cross-Output Metric Failure: Presentation slide cites '150,000 MATIC' while source Fact Registry specifies '15,000 MATIC'.",
        },
      ],
    },
  ];

  const filteredRuns = validationRuns.filter((run) => {
    if (activeFilter === "passed") return run.status === "passed";
    if (activeFilter === "review") return run.status === "review_required";
    return true;
  });

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-bold border border-brand-200 mb-2">
            <CheckCircle className="w-3.5 h-3.5" />
            Automated Quality & Integrity Guard
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Validation Center</h1>
          <p className="text-sm text-slate-500 mt-1">
            Every output must pass source grounding, cross-output consistency, domain identifier matching, and security scans before publishing.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveFilter("all")}
            className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${
              activeFilter === "all" ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            All Runs
          </button>
          <button
            onClick={() => setActiveFilter("passed")}
            className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${
              activeFilter === "passed" ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            Passed
          </button>
          <button
            onClick={() => setActiveFilter("review")}
            className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${
              activeFilter === "review" ? "bg-amber-600 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            Review Required
          </button>
        </div>
      </div>

      {/* Validation Run Cards */}
      <div className="space-y-6">
        {filteredRuns.map((run) => (
          <div key={run.id} className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-extrabold text-slate-900">{run.document_title}</h3>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                    {run.domain}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">Overall Confidence: {(run.confidence_score * 100).toFixed(0)}%</p>
              </div>

              {run.status === "passed" ? (
                <Badge variant="success">Verified (Passed)</Badge>
              ) : (
                <Badge variant="warning">Review Required (Publish Blocked)</Badge>
              )}
            </div>

            {/* Checks List */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase text-slate-500 tracking-wider">Validation Checks</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {run.checks.map((chk, idx) => (
                  <div key={idx} className="p-3 rounded-xl border border-slate-200 bg-slate-50/50 flex items-start gap-2 text-xs">
                    {chk.status === "passed" ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    )}
                    <div>
                      <span className="font-bold text-slate-900 block">{chk.name}</span>
                      <span className="text-slate-600">{chk.detail}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Issues Section if review required */}
            {run.issues.length > 0 && (
              <div className="p-4 rounded-xl bg-red-50 border border-red-200 space-y-2">
                <div className="flex items-center gap-2 text-red-800 font-bold text-xs uppercase">
                  <AlertTriangle className="w-4 h-4 text-red-600" /> Critical Validation Issue (Human Review Required)
                </div>
                {run.issues.map((iss, idx) => (
                  <p key={idx} className="text-xs text-red-700 font-semibold leading-relaxed">
                    • {iss.description}
                  </p>
                ))}
                <div className="pt-2 flex items-center gap-3">
                  <Button size="sm" className="bg-red-600 text-white font-bold hover:bg-red-700">
                    Fix & Regenerate Presentation
                  </Button>
                  <Button size="sm" variant="outline">
                    Dismiss Warning
                  </Button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
