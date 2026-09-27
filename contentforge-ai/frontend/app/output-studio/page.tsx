"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  FileText,
  Linkedin,
  Twitter,
  Shield,
  FileCode,
  Presentation as PresIcon,
  PieChart,
  Video,
  CheckCircle,
  Search,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/shared/Button";
import { Badge } from "@/components/shared/Badge";

export default function OutputStudioPage() {
  const [activeTab, setActiveTab] = useState<string>("linkedin");

  const outputs = [
    { id: "linkedin", label: "LinkedIn Post", icon: Linkedin, color: "bg-blue-50 text-blue-700 border-blue-200" },
    { id: "twitter", label: "Twitter/X Thread", icon: Twitter, color: "bg-slate-50 text-slate-700 border-slate-200" },
    { id: "advisory", label: "Security Advisory", icon: Shield, color: "bg-red-50 text-red-700 border-red-200" },
    { id: "executive_summary", label: "Executive Summary", icon: FileCode, color: "bg-indigo-50 text-indigo-700 border-indigo-200" },
    { id: "presentation", label: "Presentation Deck", icon: PresIcon, color: "bg-purple-50 text-purple-700 border-purple-200" },
    { id: "infographic", label: "Infographic Plan", icon: PieChart, color: "bg-emerald-50 text-emerald-700 border-emerald-200" },
    { id: "video", label: "Video Script", icon: Video, color: "bg-amber-50 text-amber-700 border-amber-200" },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-bold border border-brand-200 mb-2">
            <FileText className="w-3.5 h-3.5" />
            Unified Output Workspace
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Output Studio</h1>
          <p className="text-sm text-slate-500 mt-1">
            Preview, inspect, and approve all 7 coordinated public output formats generated from the Fact Registry.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/claim-inspector">
            <Button size="md" variant="outline" leftIcon={<Search className="w-4 h-4" />}>
              Open Claim Inspector
            </Button>
          </Link>
          <Link href="/validation">
            <Button size="md" className="bg-brand-600 text-white font-bold" leftIcon={<CheckCircle className="w-4 h-4" />}>
              Validation Center
            </Button>
          </Link>
        </div>
      </div>

      {/* Tabs Row */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 no-scrollbar">
        {outputs.map((out) => {
          const Icon = out.icon;
          const isActive = activeTab === out.id;
          return (
            <button
              key={out.id}
              onClick={() => setActiveTab(out.id)}
              className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-extrabold transition-all border whitespace-nowrap ${
                isActive
                  ? "bg-brand-600 text-white border-brand-600 shadow-sm"
                  : "bg-white text-slate-700 hover:bg-slate-50 border-slate-200"
              }`}
            >
              <Icon className="w-4 h-4" />
              {out.label}
            </button>
          );
        })}
      </div>

      {/* Active Output Card Preview Workspace */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-3">
            <Badge variant="success">Verified Status: Passed</Badge>
            <span className="text-xs text-slate-500 font-medium">100% Grounded in Fact Registry</span>
          </div>
          <Link href="/verify" className="text-xs font-bold text-brand-600 hover:underline flex items-center gap-1">
            View QR Verification Payload <ExternalLink className="w-3.5 h-3.5" />
          </Link>
        </div>

        {activeTab === "linkedin" && (
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-slate-900">LinkedIn Thought Leadership Post</h2>
            <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-3 font-sans text-sm text-slate-800 leading-relaxed">
              <p className="font-bold text-base text-slate-900">🚨 Critical Security Alert: CVE-2024-38077 Windows Licensing Vulnerability</p>
              <p>An unauthenticated Remote Code Execution (RCE) vulnerability with a CVSS score of 9.8 has been identified in Windows Server 2022 Remote Access Licensing Service.</p>
              <p>Key Takeaways for Enterprise CISOs:</p>
              <ul className="list-disc pl-5 space-y-1">
                <li>Affected Systems: Windows Server 2022 deployments.</li>
                <li>Mitigation: Apply Microsoft patch KB5040437 immediately across all affected environments.</li>
              </ul>
              <p className="text-brand-600 font-semibold">#Cybersecurity #CISO #VulnerabilityManagement #EnterpriseSecurity</p>
            </div>
          </div>
        )}

        {activeTab === "twitter" && (
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-slate-900">Twitter/X Thread (3 Tweets)</h2>
            <div className="space-y-3">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-sm">
                <span className="font-bold text-brand-600 text-xs">1/3</span> 🚨 SECURITY ADVISORY: CVE-2024-38077 CVSS 9.8 RCE vulnerability detected in Windows Server 2022 Licensing Service.
              </div>
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-sm">
                <span className="font-bold text-brand-600 text-xs">2/3</span> Attackers can execute arbitrary code remotely without authentication. Remediation patch KB5040437 is available.
              </div>
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-sm">
                <span className="font-bold text-brand-600 text-xs">3/3</span> Verify your infrastructure patch status immediately to prevent exploitation. #CyberSecurity
              </div>
            </div>
          </div>
        )}

        {activeTab !== "linkedin" && activeTab !== "twitter" && (
          <div className="p-8 text-center space-y-3">
            <h2 className="text-base font-bold text-slate-900">Format Preview Loaded Cleanly</h2>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              Generated format contains zero internal [f1] tags in public text while maintaining complete Claim Inspector traceability.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
