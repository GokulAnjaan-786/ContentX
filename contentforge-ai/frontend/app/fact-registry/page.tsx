"use client";

import React, { useState } from "react";
import {
  Database,
  Search,
  Filter,
  FileText,
  Tag,
  Calendar,
  Hash,
  Layers,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";
import { Badge } from "@/components/shared/Badge";
import { Button } from "@/components/shared/Button";

export default function FactRegistryPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedImportance, setSelectedImportance] = useState<string>("all");

  const registryFacts = [
    {
      fact_id: "f1",
      statement: "An unauthenticated Remote Code Execution (RCE) vulnerability (CVE-2024-38077) affects Windows Server 2022 Remote Access Licensing Service.",
      importance: "high",
      certainty: "confirmed",
      source_snippet: "Security researchers identified CVE-2024-38077 allowing unauthenticated remote code execution in Windows Server 2022 licensing stack.",
      source_page: 2,
      source_section: "Executive Advisory / Vulnerability Details",
      entities: ["Windows Server 2022", "Remote Access Licensing Service", "CVE-2024-38077"],
      dates: ["2024-07-09"],
      numbers: ["CVSS 9.8"],
      related_facts: ["f3", "f5"],
      used_outputs: ["Advisory", "LinkedIn", "Twitter/X", "Executive Summary", "Presentation"],
    },
    {
      fact_id: "f2",
      statement: "Transaction hash 0x8f2a1b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a transferred 15,000 MATIC on Polygon Amoy testnet.",
      importance: "high",
      certainty: "confirmed",
      source_snippet: "Polygon Amoy incident log records tx 0x8f2a1b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a moving 15,000 MATIC token payload.",
      source_page: 4,
      source_section: "Blockchain On-Chain Audit Log",
      entities: ["Polygon Amoy", "MATIC", "0x8f2a...0f1a"],
      dates: ["2026-09-27"],
      numbers: ["15,000", "80002"],
      related_facts: ["f4"],
      used_outputs: ["Advisory", "Infographic", "Video Script"],
    },
    {
      fact_id: "f3",
      statement: "Patch KB5040437 was deployed to mitigate CVE-2024-38077 across all affected server infrastructure.",
      importance: "medium",
      certainty: "confirmed",
      source_snippet: "Microsoft released patch KB5040437 to remediate memory corruption in licensing handler.",
      source_page: 3,
      source_section: "Remediation Guidance",
      entities: ["Microsoft", "KB5040437"],
      dates: ["2024-07-11"],
      numbers: ["100% Patch Rate"],
      related_facts: ["f1"],
      used_outputs: ["Advisory", "Executive Summary"],
    },
  ];

  const filteredFacts = registryFacts.filter((f) => {
    const matchesSearch =
      f.statement.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.fact_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.entities.some((e) => e.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesImp = selectedImportance === "all" || f.importance === selectedImportance;
    return matchesSearch && matchesImp;
  });

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Page Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-bold border border-brand-200 mb-2">
            <Database className="w-3.5 h-3.5" />
            Immutable Grounding Layer
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Fact Registry</h1>
          <p className="text-sm text-slate-500 mt-1">
            Central repository of extracted source facts, snippets, entity linkages, and public output citations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="success">
            <ShieldCheck className="w-3.5 h-3.5 mr-1" />
            3 Active Fact Entries
          </Badge>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3 bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search facts by ID, statement, entity, or snippet..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-500" />
          <select
            value={selectedImportance}
            onChange={(e) => setSelectedImportance(e.target.value)}
            className="px-3 py-2 text-sm border border-slate-200 rounded-lg bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
          >
            <option value="all">All Importance</option>
            <option value="high">High Importance</option>
            <option value="medium">Medium Importance</option>
            <option value="low">Low Importance</option>
          </select>
        </div>
      </div>

      {/* Fact Cards */}
      <div className="space-y-4">
        {filteredFacts.map((fact) => (
          <div key={fact.fact_id} className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4 hover:border-brand-300 transition-colors">
            {/* Header line */}
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-black px-2.5 py-1 rounded bg-brand-600 text-white shadow-xs">
                  {fact.fact_id}
                </span>
                <Badge variant={fact.importance === "high" ? "brand" : "neutral"}>
                  {fact.importance.toUpperCase()} IMPORTANCE
                </Badge>
                <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Status: {fact.certainty}
                </span>
              </div>

              <div className="text-xs text-slate-500 font-medium">
                Page {fact.source_page} • Section: <span className="font-semibold text-slate-700">{fact.source_section}</span>
              </div>
            </div>

            {/* Fact Statement */}
            <div>
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                Fact Statement
              </h3>
              <p className="text-base font-bold text-slate-900 leading-snug">
                {fact.statement}
              </p>
            </div>

            {/* Source Snippet Evidence */}
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 space-y-1">
              <div className="font-bold text-slate-500 uppercase text-[10px] tracking-wide flex items-center gap-1">
                <FileText className="w-3 h-3 text-brand-600" /> Source Snippet Evidence
              </div>
              <p className="italic font-mono text-slate-800">"{fact.source_snippet}"</p>
            </div>

            {/* Entity & Metadata Badges */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs pt-2">
              <div>
                <span className="font-bold text-slate-500 text-[10px] uppercase block mb-1">Entities</span>
                <div className="flex flex-wrap gap-1">
                  {fact.entities.map((e, idx) => (
                    <span key={idx} className="px-2 py-0.5 rounded bg-slate-100 text-slate-800 text-[11px] font-medium border border-slate-200">
                      {e}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <span className="font-bold text-slate-500 text-[10px] uppercase block mb-1">Dates & Metrics</span>
                <div className="flex flex-wrap gap-1">
                  {fact.dates.map((d, idx) => (
                    <span key={idx} className="px-2 py-0.5 rounded bg-purple-50 text-purple-700 text-[11px] font-semibold border border-purple-200">
                      {d}
                    </span>
                  ))}
                  {fact.numbers.map((n, idx) => (
                    <span key={idx} className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-[11px] font-semibold border border-blue-200">
                      {n}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <span className="font-bold text-slate-500 text-[10px] uppercase block mb-1">Used In Outputs</span>
                <div className="flex flex-wrap gap-1">
                  {fact.used_outputs.map((out, idx) => (
                    <span key={idx} className="px-2 py-0.5 rounded bg-brand-50 text-brand-700 text-[11px] font-semibold border border-brand-200">
                      {out}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
