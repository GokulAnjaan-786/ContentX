"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Brain,
  Database,
  Hash,
  Calendar,
  Layers,
  AlertTriangle,
  GitCommit,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  Lock,
} from "lucide-react";
import { Button } from "@/components/shared/Button";
import { Badge } from "@/components/shared/Badge";

export default function UnderstandingPage() {
  const [selectedDomain, setSelectedDomain] = useState<"all" | "cybersecurity" | "blockchain">("all");

  const sampleFacts = [
    {
      id: "f1",
      statement: "An unauthenticated Remote Code Execution (RCE) vulnerability (CVE-2024-38077) affects Windows Server 2022 Remote Access Licensing Service.",
      importance: "high",
      certainty: "confirmed",
      domain: "cybersecurity",
      entities: ["Windows Server 2022", "Remote Access Licensing Service", "CVE-2024-38077"],
      dates: ["2024-07-09"],
      numbers: ["CVSS 9.8"],
    },
    {
      id: "f2",
      statement: "Transaction hash 0x8f2a1b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a transferred 15,000 MATIC on Polygon Amoy testnet.",
      importance: "high",
      certainty: "confirmed",
      domain: "blockchain",
      entities: ["Polygon Amoy", "0x8f2a...0f1a", "MATIC"],
      dates: ["2026-09-27"],
      numbers: ["15,000", "80002"],
    },
    {
      id: "f3",
      statement: "Security patches were made available across all supported deployment regions on 15 September 2026.",
      importance: "medium",
      certainty: "confirmed",
      domain: "cybersecurity",
      entities: ["Security Team"],
      dates: ["15 September 2026"],
      numbers: ["100%"],
    },
  ];

  const filteredFacts = sampleFacts.filter(
    (f) => selectedDomain === "all" || f.domain === selectedDomain
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-bold border border-brand-200 mb-2">
            <Brain className="w-3.5 h-3.5" />
            Document Understanding Pass
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            Extracted Knowledge & Structure
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Overview of extracted facts, entities, metrics, timelines, and relationships prior to format generation.
          </p>
        </div>

        <Link href="/fact-registry">
          <Button
            size="md"
            className="bg-brand-600 text-white hover:bg-brand-700 font-bold"
            leftIcon={<Database className="w-4 h-4" />}
          >
            Open Fact Registry UI
          </Button>
        </Link>
      </div>

      {/* Metric Cards (7 Core Understanding Metrics) */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center gap-2 text-slate-500 text-xs font-bold uppercase">
            <Database className="w-3.5 h-3.5 text-brand-600" /> Facts
          </div>
          <p className="text-2xl font-black text-slate-900 mt-2">18</p>
          <p className="text-[10px] text-slate-400">Extracted</p>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center gap-2 text-slate-500 text-xs font-bold uppercase">
            <Layers className="w-3.5 h-3.5 text-indigo-600" /> Entities
          </div>
          <p className="text-2xl font-black text-slate-900 mt-2">14</p>
          <p className="text-[10px] text-slate-400">Identified</p>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center gap-2 text-slate-500 text-xs font-bold uppercase">
            <Hash className="w-3.5 h-3.5 text-emerald-600" /> Topics
          </div>
          <p className="text-2xl font-black text-slate-900 mt-2">6</p>
          <p className="text-[10px] text-slate-400">Classified</p>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center gap-2 text-slate-500 text-xs font-bold uppercase">
            <Calendar className="w-3.5 h-3.5 text-purple-600" /> Dates
          </div>
          <p className="text-2xl font-black text-slate-900 mt-2">5</p>
          <p className="text-[10px] text-slate-400">Timelines</p>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center gap-2 text-slate-500 text-xs font-bold uppercase">
            <Hash className="w-3.5 h-3.5 text-blue-600" /> Numbers
          </div>
          <p className="text-2xl font-black text-slate-900 mt-2">8</p>
          <p className="text-[10px] text-slate-400">Metrics</p>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center gap-2 text-slate-500 text-xs font-bold uppercase">
            <GitCommit className="w-3.5 h-3.5 text-amber-600" /> Rel.
          </div>
          <p className="text-2xl font-black text-slate-900 mt-2">11</p>
          <p className="text-[10px] text-slate-400">Graph Edges</p>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center gap-2 text-slate-500 text-xs font-bold uppercase">
            <AlertTriangle className="w-3.5 h-3.5 text-emerald-600" /> Conflicts
          </div>
          <p className="text-2xl font-black text-emerald-600 mt-2">0</p>
          <p className="text-[10px] text-emerald-600 font-bold">Clean</p>
        </div>
      </div>

      {/* Representative Facts Section */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-extrabold text-slate-900">Representative Source Facts</h2>
            <p className="text-xs text-slate-500">Immutable fact items registered from active source documents</p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setSelectedDomain("all")}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                selectedDomain === "all" ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              All Domains
            </button>
            <button
              onClick={() => setSelectedDomain("cybersecurity")}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                selectedDomain === "cybersecurity" ? "bg-red-600 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              Cybersecurity
            </button>
            <button
              onClick={() => setSelectedDomain("blockchain")}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                selectedDomain === "blockchain" ? "bg-purple-600 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              Blockchain
            </button>
          </div>
        </div>

        <div className="space-y-3">
          {filteredFacts.map((fact) => (
            <div key={fact.id} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition-colors space-y-2">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-brand-100 text-brand-800">
                    [{fact.id}]
                  </span>
                  <Badge variant={fact.importance === "high" ? "brand" : "neutral"}>
                    {fact.importance.toUpperCase()}
                  </Badge>
                  <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    Status: {fact.certainty}
                  </span>
                </div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wide">
                  Domain: {fact.domain}
                </span>
              </div>

              <p className="text-sm font-semibold text-slate-800 leading-relaxed">
                {fact.statement}
              </p>

              <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 pt-1">
                {fact.entities.map((e, idx) => (
                  <span key={idx} className="px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-700 text-[11px]">
                    Entity: {e}
                  </span>
                ))}
                {fact.dates.map((d, idx) => (
                  <span key={idx} className="px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 text-[11px]">
                    Date: {d}
                  </span>
                ))}
                {fact.numbers.map((n, idx) => (
                  <span key={idx} className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 text-[11px]">
                    Metric: {n}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
