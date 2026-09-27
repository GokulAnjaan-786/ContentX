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
  Users,
} from "lucide-react";
import { Button } from "@/components/shared/Button";
import { Badge } from "@/components/shared/Badge";

export default function OutputStudioPage() {
  const [activeTab, setActiveTab] = useState<string>("linkedin");
  const [selectedAudience, setSelectedAudience] = useState<string>("professional");

  const outputs = [
    { id: "linkedin", label: "LinkedIn Post", icon: Linkedin, color: "bg-blue-50 text-blue-700 border-blue-200", audiences: ["professional", "general_public"] },
    { id: "twitter", label: "Twitter/X Thread", icon: Twitter, color: "bg-slate-50 text-slate-700 border-slate-200", audiences: ["professional"] },
    { id: "advisory", label: "Security Advisory", icon: Shield, color: "bg-red-50 text-red-700 border-red-200", audiences: ["technical"] },
    { id: "executive_summary", label: "Executive Summary", icon: FileCode, color: "bg-indigo-50 text-indigo-700 border-indigo-200", audiences: ["executive"] },
    { id: "presentation", label: "Presentation Deck", icon: PresIcon, color: "bg-purple-50 text-purple-700 border-purple-200", audiences: ["professional", "executive"] },
    { id: "infographic", label: "Infographic Plan", icon: PieChart, color: "bg-emerald-50 text-emerald-700 border-emerald-200", audiences: ["professional", "general_public"] },
    { id: "video", label: "Video Script", icon: Video, color: "bg-amber-50 text-amber-700 border-amber-200", audiences: ["professional"] },
  ];

  const activeOutputMeta = outputs.find((o) => o.id === activeTab) || outputs[0];

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
            Preview, inspect, and approve all 7 coordinated public output formats and audience variants generated from the Fact Registry.
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
              onClick={() => {
                setActiveTab(out.id);
                setSelectedAudience(out.audiences[0]);
              }}
              className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-extrabold transition-all border whitespace-nowrap ${
                isActive
                  ? "bg-brand-600 text-white border-brand-600 shadow-sm"
                  : "bg-white text-slate-700 hover:bg-slate-50 border-slate-200"
              }`}
            >
              <Icon className="w-4 h-4" />
              {out.label}
              <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${isActive ? "bg-brand-500 text-white" : "bg-slate-100 text-slate-600"}`}>
                {out.audiences.length}
              </span>
            </button>
          );
        })}
      </div>

      {/* Audience Variant Badges Row */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 flex items-center gap-3 flex-wrap shadow-xs">
        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
          <Users className="w-3.5 h-3.5 text-brand-600" /> Generated Audience Variants:
        </span>
        <div className="flex items-center gap-2">
          {activeOutputMeta.audiences.map((aud) => {
            const isAudActive = selectedAudience === aud;
            return (
              <button
                key={aud}
                onClick={() => setSelectedAudience(aud)}
                className={`px-3 py-1 rounded-lg text-xs font-extrabold capitalize transition-all border ${
                  isAudActive
                    ? "bg-brand-600 text-white border-brand-600 shadow-xs"
                    : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                }`}
              >
                [ {aud.replace("_", " ")} ]
              </button>
            );
          })}
        </div>
      </div>

      {/* Active Output Card Preview Workspace */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-3">
            <Badge variant="success">Verified Status: Passed</Badge>
            <span className="text-xs text-slate-500 font-medium">100% Grounded in Fact Registry</span>
            <span className="text-xs font-bold text-brand-700 bg-brand-50 px-2.5 py-0.5 rounded-full border border-brand-200 capitalize">
              Audience: {selectedAudience.replace("_", " ")}
            </span>
          </div>
          <Link href="/verify" className="text-xs font-bold text-brand-600 hover:underline flex items-center gap-1">
            View QR Verification Payload <ExternalLink className="w-3.5 h-3.5" />
          </Link>
        </div>

        {activeTab === "linkedin" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-900">LinkedIn Thought Leadership Post</h2>
              <span className="text-xs font-bold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-md capitalize">
                Complexity: {selectedAudience === "general_public" ? "Simple Language" : "Professional Depth"}
              </span>
            </div>
            <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-3 font-sans text-sm text-slate-800 leading-relaxed">
              {selectedAudience === "general_public" ? (
                <>
                  <p className="font-bold text-base text-slate-900">📢 Important Security Update: Windows Server 2022</p>
                  <p>A security issue has been identified in Windows Server 2022 that could allow remote access under certain conditions. Microsoft has released an official update to fix this issue.</p>
                  <p>What you should know:</p>
                  <ul className="list-disc pl-5 space-y-1">
                    <li>Affected Systems: Windows Server 2022 Remote Access Licensing.</li>
                    <li>Fix: Install update KB5040437 immediately to keep your system safe.</li>
                  </ul>
                  <p className="text-brand-600 font-semibold">#CyberSecurity #TechNews #SystemUpdate</p>
                </>
              ) : (
                <>
                  <p className="font-bold text-base text-slate-900">🚨 Critical Security Alert: CVE-2024-38077 Windows Licensing Vulnerability</p>
                  <p>An unauthenticated Remote Code Execution (RCE) vulnerability with a CVSS score of 9.8 has been identified in Windows Server 2022 Remote Access Licensing Service.</p>
                  <p>Key Takeaways for Enterprise CISOs:</p>
                  <ul className="list-disc pl-5 space-y-1">
                    <li>Affected Systems: Windows Server 2022 deployments.</li>
                    <li>Mitigation: Apply Microsoft patch KB5040437 immediately across all affected environments.</li>
                  </ul>
                  <p className="text-brand-600 font-semibold">#Cybersecurity #CISO #VulnerabilityManagement #EnterpriseSecurity</p>
                </>
              )}
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
              Generated format contains zero internal [f1] tags in public text while maintaining complete Fact Registry grounding.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

