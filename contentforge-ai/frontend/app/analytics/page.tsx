"use client";

import React from "react";
import {
  BarChart3,
  TrendingUp,
  ShieldCheck,
  CheckCircle,
  AlertTriangle,
  Layers,
  Cpu,
  Lock,
} from "lucide-react";
import { Badge } from "@/components/shared/Badge";

export default function AnalyticsPage() {
  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-bold border border-brand-200 mb-2">
            <BarChart3 className="w-3.5 h-3.5" />
            Quality & Verification Metrics
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Analytics & Intelligence</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time performance metrics, domain breakdown, source grounding confidence trends, and validation issue analytics.
          </p>
        </div>

        <Badge variant="success">System Quality Index: 98.4%</Badge>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase">Avg Grounding Score</span>
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-3xl font-black text-slate-900 mt-2">99.2%</p>
          <p className="text-[11px] text-emerald-600 font-semibold mt-1">↑ 1.4% vs last month</p>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase">Cybersecurity Domain</span>
            <Lock className="w-4 h-4 text-red-600" />
          </div>
          <p className="text-3xl font-black text-slate-900 mt-2">12</p>
          <p className="text-[11px] text-slate-400 mt-1">CVE Advisories Processed</p>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase">Blockchain Domain</span>
            <Cpu className="w-4 h-4 text-purple-600" />
          </div>
          <p className="text-3xl font-black text-slate-900 mt-2">8</p>
          <p className="text-[11px] text-slate-400 mt-1">On-Chain Incident Reports</p>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase">Cross-Output Mismatches</span>
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          </div>
          <p className="text-3xl font-black text-amber-600 mt-2">1</p>
          <p className="text-[11px] text-amber-600 font-semibold mt-1">Blocked before publishing</p>
        </div>
      </div>

      {/* Analytics Breakdown Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4">
          <h2 className="text-base font-extrabold text-slate-900">Transformation Volume by Output Format</h2>
          <div className="space-y-3">
            {[
              { format: "LinkedIn Post", percentage: "100%", count: "20" },
              { format: "Twitter/X Thread", percentage: "100%", count: "20" },
              { format: "Security Advisory", percentage: "95%", count: "19" },
              { format: "Executive Summary", percentage: "100%", count: "20" },
              { format: "Presentation Deck", percentage: "90%", count: "18" },
              { format: "Infographic Plan", percentage: "100%", count: "20" },
              { format: "Video Script", percentage: "100%", count: "20" },
            ].map((item, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex justify-between text-xs font-bold text-slate-700">
                  <span>{item.format}</span>
                  <span>{item.count} Generated ({item.percentage})</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                  <div className="h-full bg-brand-600 rounded-full" style={{ width: item.percentage }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4">
          <h2 className="text-base font-extrabold text-slate-900">Validation & Security Guard Summary</h2>
          <div className="space-y-3">
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-800">Deterministic Source Grounding</span>
              <span className="font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">100% Pass</span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-800">CVE / CWE Technical ID Preservation</span>
              <span className="font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">100% Pass</span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-800">Blockchain Hex Hash & Address Verification</span>
              <span className="font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">100% Pass</span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-800">Prompt Injection & Malicious Delimiter Scanning</span>
              <span className="font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">0 Threat Escapes</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
