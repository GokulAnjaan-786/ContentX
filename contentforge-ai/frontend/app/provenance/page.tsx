"use client";

import React from "react";
import Link from "next/link";
import {
  GitBranch,
  QrCode,
  ShieldCheck,
  CheckCircle2,
  Lock,
  Cpu,
  ExternalLink,
  Copy,
  Clock,
  Layers,
} from "lucide-react";
import { Badge } from "@/components/shared/Badge";
import { Button } from "@/components/shared/Button";

export default function ProvenancePage() {
  const provenanceRecord = {
    verification_id: "ver_9f83a2e104b281",
    document_title: "Windows Licensing RCE Security Advisory (CVE-2024-38077)",
    source_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    output_sha256: "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
    issuer: "ContentX Trust Engine v1.0",
    approval_status: "Approved & Published",
    timestamp: "2026-09-27T12:00:00Z",
    blockchain_anchored: true,
    chain_network: "Polygon Amoy Testnet (Chain ID: 80002)",
    anchor_tx_hash: "0x8f2a1b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a",
    contract_address: "0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Page Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-bold border border-brand-200 mb-2">
            <GitBranch className="w-3.5 h-3.5" />
            Cryptographic Integrity & Chain of Custody
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Provenance & Trust Layer</h1>
          <p className="text-sm text-slate-500 mt-1">
            Every approved transformation generates a cryptographically signed SHA-256 fingerprint record with optional blockchain anchoring.
          </p>
        </div>

        <Link href={`/verify/${provenanceRecord.verification_id}`}>
          <Button size="md" className="bg-brand-600 text-white font-bold" leftIcon={<QrCode className="w-4 h-4" />}>
            Open Public Verification Page
          </Button>
        </Link>
      </div>

      {/* Main Record Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-lg font-extrabold text-slate-900">{provenanceRecord.document_title}</h2>
            <p className="text-xs text-slate-500 mt-0.5">Verification ID: <span className="font-mono font-bold text-slate-800">{provenanceRecord.verification_id}</span></p>
          </div>
          <Badge variant="success">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
            {provenanceRecord.approval_status}
          </Badge>
        </div>

        {/* SHA-256 Fingerprints */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
              Source Document SHA-256 Fingerprint
            </span>
            <p className="font-mono text-xs text-slate-900 break-all bg-white p-2 rounded border border-slate-200">
              {provenanceRecord.source_sha256}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
              Generated Outputs SHA-256 Fingerprint
            </span>
            <p className="font-mono text-xs text-slate-900 break-all bg-white p-2 rounded border border-slate-200">
              {provenanceRecord.output_sha256}
            </p>
          </div>
        </div>

        {/* Blockchain Anchor Section */}
        <div className="p-5 rounded-2xl bg-gradient-to-r from-slate-900 to-indigo-950 text-white space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cpu className="w-5 h-5 text-brand-400" />
              <h3 className="text-sm font-bold">Polygon Amoy Testnet Blockchain Anchor</h3>
            </div>
            <span className="text-[10px] font-bold px-2.5 py-1 rounded bg-brand-500/20 text-brand-300 border border-brand-500/30">
              ON-CHAIN ANCHORED
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-slate-300 pt-1">
            <div>
              <span className="text-slate-400 text-[10px] block">Network & Chain ID:</span>
              <span className="font-semibold text-white">{provenanceRecord.chain_network}</span>
            </div>
            <div>
              <span className="text-slate-400 text-[10px] block">Anchor Contract Address:</span>
              <span className="font-mono text-white text-[11px]">{provenanceRecord.contract_address}</span>
            </div>
            <div className="md:col-span-2">
              <span className="text-slate-400 text-[10px] block">Transaction Hash:</span>
              <span className="font-mono text-white text-[11px] break-all">{provenanceRecord.anchor_tx_hash}</span>
            </div>
          </div>
        </div>

        {/* Audit Record Timeline */}
        <div className="space-y-3 pt-2">
          <h3 className="text-xs font-extrabold text-slate-900 uppercase tracking-wider">Audit Record Timeline</h3>
          <div className="space-y-2 border-l-2 border-brand-200 pl-4 text-xs text-slate-700">
            <div>
              <span className="font-bold text-slate-900 block">12:00:00 UTC — Document Ingestion & Malware Scan</span>
              <span className="text-slate-500">MIME type validated, ClamAV clean, SHA-256 fingerprint recorded.</span>
            </div>
            <div>
              <span className="font-bold text-slate-900 block">12:00:05 UTC — Understanding & Fact Registry Extraction</span>
              <span className="text-slate-500">18 immutable facts extracted with 100% certainty ranking.</span>
            </div>
            <div>
              <span className="font-bold text-slate-900 block">12:00:15 UTC — Validation Gate & Provenance Signing</span>
              <span className="text-slate-500">Source grounding, cybersecurity domain pack, and cross-output consistency verified.</span>
            </div>
            <div>
              <span className="font-bold text-slate-900 block">12:00:20 UTC — Polygon Amoy On-Chain Anchoring</span>
              <span className="text-slate-500">Cryptographic state hash committed to contract 0x71C7...976F.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
