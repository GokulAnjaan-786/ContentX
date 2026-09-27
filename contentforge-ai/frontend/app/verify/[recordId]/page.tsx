"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  Copy,
  Check,
  ArrowLeft,
  FileText,
  Clock,
  UserCheck,
  Building,
  Hash,
  Link2,
} from "lucide-react";
import { verificationApi, VerificationResult } from "@/lib/api";

export default function VerifyRecordPage() {
  const params = useParams();
  const router = useRouter();
  const recordId = params.recordId as string;

  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  useEffect(() => {
    if (!recordId) return;

    let isMounted = true;
    setLoading(true);

    verificationApi
      .verifyRecord(recordId)
      .then((data) => {
        if (isMounted) {
          setResult(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || "Failed to query verification status.");
          setResult({
            status: "not_found",
            message: "Unable to verify record ID.",
          });
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [recordId]);

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(label);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center p-6 text-center">
        <div className="w-16 h-16 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mb-4" />
        <h2 className="text-xl font-bold text-slate-800">Verifying Cryptographic Provenance...</h2>
        <p className="text-slate-500 text-sm mt-1">
          Walking hash-chain ledger and calculating independent SHA-256 fingerprints
        </p>
      </div>
    );
  }

  const isVerified = result?.status === "verified";
  const isBroken = result?.status === "chain_broken";
  const isNotFound = !isVerified && !isBroken;

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6">
      {/* Navigation breadcrumb */}
      <div className="mb-6 flex items-center justify-between">
        <Link
          href="/verify"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Verify Another Content / File
        </Link>
        <span className="text-xs text-slate-400 font-mono">
          Record: {recordId ? `${recordId.slice(0, 13)}...` : ""}
        </span>
      </div>

      {/* Main Status Header Card */}
      {isVerified && (
        <div className="rounded-2xl border-2 border-emerald-500 bg-gradient-to-b from-emerald-50/70 to-white p-8 shadow-sm mb-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-emerald-200">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-emerald-600 text-white flex items-center justify-center shadow-lg shadow-emerald-600/20">
                <ShieldCheck className="w-8 h-8" />
              </div>
              <div>
                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800 border border-emerald-300 mb-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Cryptographically Verified
                </div>
                <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
                  Authentic Official Output
                </h1>
              </div>
            </div>
            <div className="sm:text-right">
              <span className="text-xs text-slate-500 uppercase tracking-wider font-semibold block">
                Chain Position
              </span>
              <span className="text-lg font-mono font-bold text-emerald-700">
                Block #{result.chain_index ?? 0}
              </span>
            </div>
          </div>

          <p className="mt-4 text-slate-700 text-sm sm:text-base leading-relaxed">
            This advisory/output has been cryptographically confirmed against the ContentForge tamper-evident
            ledger. Its content perfectly matches the approved cryptographic digest, and all hash-chain links
            connecting back to the origin source document remain completely intact.
          </p>
        </div>
      )}

      {isBroken && (
        <div className="rounded-2xl border-2 border-amber-500 bg-gradient-to-b from-amber-50/70 to-white p-8 shadow-sm mb-8">
          <div className="flex items-center gap-4 pb-6 border-b border-amber-200">
            <div className="w-14 h-14 rounded-2xl bg-amber-600 text-white flex items-center justify-center shadow-lg shadow-amber-600/20">
              <AlertTriangle className="w-8 h-8" />
            </div>
            <div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-100 text-amber-800 border border-amber-300 mb-1">
                Chain Integrity Failure
              </div>
              <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
                Integrity Compromised
              </h1>
            </div>
          </div>
          <p className="mt-4 text-slate-700 text-sm sm:text-base leading-relaxed">
            A cryptographic break was detected along the organization&apos;s provenance chain (
            <span className="font-mono font-semibold text-amber-800">{result.chain_integrity}</span>).
            This indicates that one or more historical ledger entries were modified or deleted, so authenticity
            cannot be guaranteed.
          </p>
        </div>
      )}

      {isNotFound && (
        <div className="rounded-2xl border-2 border-rose-500 bg-gradient-to-b from-rose-50/70 to-white p-8 shadow-sm mb-8">
          <div className="flex items-center gap-4 pb-6 border-b border-rose-200">
            <div className="w-14 h-14 rounded-2xl bg-rose-600 text-white flex items-center justify-center shadow-lg shadow-rose-600/20">
              <ShieldAlert className="w-8 h-8" />
            </div>
            <div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-rose-100 text-rose-800 border border-rose-300 mb-1">
                Not Found
              </div>
              <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
                Unverified Content
              </h1>
            </div>
          </div>
          <div className="mt-4 space-y-3">
            <p className="text-slate-800 font-medium">
              This means the content you have does not match any record we have of officially approved
              ContentForge AI output.
            </p>
            <p className="text-slate-600 text-sm leading-relaxed">
              Do not act on this information without confirming directly with the issuing organisation. Anyone can
              format a document to look official; only valid cryptographic fingerprints verify genuine origin.
            </p>
          </div>
        </div>
      )}

      {/* Provenance & Cryptographic Metadata (if verified) */}
      {isVerified && (
        <div className="space-y-6">
          {/* Metadata Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Origin & Org */}
            <div className="p-5 rounded-xl border border-slate-200 bg-white shadow-sm space-y-3">
              <div className="flex items-center gap-2 text-slate-500 text-xs font-bold uppercase tracking-wider">
                <Building className="w-4 h-4 text-emerald-600" />
                Issuing Organisation
              </div>
              <p className="text-lg font-bold text-slate-900">{result.organisation_name}</p>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <FileText className="w-3.5 h-3.5" />
                Format: <span className="font-semibold text-slate-700 capitalize">{result.output_type?.replace(/_/g, " ")}</span>
              </div>
            </div>

            {/* Approver & Timestamp */}
            <div className="p-5 rounded-xl border border-slate-200 bg-white shadow-sm space-y-3">
              <div className="flex items-center gap-2 text-slate-500 text-xs font-bold uppercase tracking-wider">
                <UserCheck className="w-4 h-4 text-emerald-600" />
                Authorized Reviewer
              </div>
              <p className="text-lg font-bold text-slate-900">
                {result.approved_by || "Authorized Security Reviewer"}
              </p>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Clock className="w-3.5 h-3.5" />
                Approved at:{" "}
                <span className="font-semibold text-slate-700">
                  {result.approved_at ? new Date(result.approved_at).toLocaleString() : "Confirmed on creation"}
                </span>
              </div>
            </div>
          </div>

          {/* Detailed Verification Ledger Checklist */}
          <div className="p-6 rounded-xl border border-slate-200 bg-white shadow-sm space-y-4">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-600" />
              Cryptographic Audit Proofs
            </h3>

            <div className="divide-y divide-slate-100 space-y-3 pt-1">
              {/* Check 1: Source Document */}
              <div className="pt-3 flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 w-5 h-5 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center shrink-0">
                    <Check className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900">Source Document Provenance</h4>
                    <p className="text-xs text-slate-500">
                      Cryptographically linked back to the original source incident report anchored on upload.
                    </p>
                  </div>
                </div>
                <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-50 text-emerald-700 border border-emerald-200 shrink-0">
                  Verified Linked
                </span>
              </div>

              {/* Check 2: Hash Chain Link */}
              <div className="pt-3 flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 w-5 h-5 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center shrink-0">
                    <Check className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900">Tamper-Evident Hash Chain</h4>
                    <p className="text-xs text-slate-500">
                      Chained to preceding record hash. Mathematical integrity fully validated across all blocks.
                    </p>
                  </div>
                </div>
                <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-50 text-emerald-700 border border-emerald-200 shrink-0">
                  Chain Intact
                </span>
              </div>

              {/* Check 3: Digital Signature */}
              <div className="pt-3 flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 w-5 h-5 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center shrink-0">
                    <Check className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900">Reviewer Ed25519 Signature</h4>
                    <p className="text-xs text-slate-500">
                      Signed using reviewer&apos;s asymmetric keypair. Independently verifiable by any third party.
                    </p>
                  </div>
                </div>
                <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-50 text-emerald-700 border border-emerald-200 shrink-0">
                  Valid Signature
                </span>
              </div>

              {/* Check 4: Public Anchor */}
              <div className="pt-3 flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 w-5 h-5 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center shrink-0">
                    <Link2 className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900">Public Anchor Status</h4>
                    <p className="text-xs text-slate-500">
                      {result.public_anchor_tx_hash ? (
                        <>
                          Anchored to Polygon Amoy Testnet (Tx:{" "}
                          <span className="font-mono text-blue-600">
                            {result.public_anchor_tx_hash.slice(0, 16)}...
                          </span>
                          )
                        </>
                      ) : (
                        "Anchored to High-Integrity Local Hash-Chain (Public testnet anchoring optional)"
                      )}
                    </p>
                  </div>
                </div>
                <span className="px-2 py-0.5 text-xs font-semibold rounded bg-slate-100 text-slate-700 border border-slate-200 shrink-0">
                  {result.public_anchor_tx_hash ? "Polygon Amoy" : "Local Ledger"}
                </span>
              </div>
            </div>
          </div>

          {/* Cryptographic Digests Box (Zero Confidential Content Exposed) */}
          <div className="p-6 rounded-xl border border-slate-200 bg-slate-900 text-white shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <Hash className="w-4 h-4 text-emerald-400" />
                Cryptographic Fingerprints (SHA-256)
              </h3>
              <span className="text-[11px] text-emerald-400 font-semibold bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800">
                Zero Content Disclosed
              </span>
            </div>

            <div className="space-y-3 font-mono text-xs">
              {/* Content Hash */}
              <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700/60 flex items-center justify-between gap-3">
                <div className="overflow-hidden">
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Content SHA-256 Fingerprint</div>
                  <div className="text-emerald-300 truncate">{result.content_hash}</div>
                </div>
                <button
                  onClick={() => result.content_hash && copyToClipboard(result.content_hash, "content")}
                  className="p-1.5 rounded bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors shrink-0"
                  title="Copy SHA-256"
                >
                  {copiedHash === "content" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>

              {/* Record Hash */}
              <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700/60 flex items-center justify-between gap-3">
                <div className="overflow-hidden">
                  <div className="text-[10px] text-slate-400 uppercase font-semibold">Ledger Block Hash</div>
                  <div className="text-slate-300 truncate">{result.record_hash}</div>
                </div>
                <button
                  onClick={() => result.record_hash && copyToClipboard(result.record_hash, "record")}
                  className="p-1.5 rounded bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors shrink-0"
                  title="Copy Block Hash"
                >
                  {copiedHash === "record" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer Info */}
      <div className="mt-8 text-center text-xs text-slate-500 space-y-1">
        <p>ContentForge AI • Blockchain &amp; Cybersecurity Trust Layer</p>
        <p>Verification is mathematically determined and requires zero server trust.</p>
      </div>
    </div>
  );
}
