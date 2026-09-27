"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  ShieldAlert,
  UploadCloud,
  FileText,
  Search,
  CheckCircle2,
  AlertTriangle,
  Copy,
  Check,
  ExternalLink,
  Building,
  UserCheck,
  Clock,
  Hash,
} from "lucide-react";
import { verificationApi, VerificationResult } from "@/lib/api";

export default function VerifyPortalPage() {
  const [activeTab, setActiveTab] = useState<"text" | "file">("text");
  const [textInput, setTextInput] = useState("");
  const [fileInput, setFileInput] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleVerifyText = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim()) return;

    setLoading(true);
    setHasSearched(true);
    try {
      const res = await verificationApi.verifyByText(textInput.trim());
      setResult(res);
    } catch (err: any) {
      setResult({
        status: "not_found",
        message: err.message || "Failed to verify text content.",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyFile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fileInput) return;

    setLoading(true);
    setHasSearched(true);
    try {
      const res = await verificationApi.verifyByFile(fileInput);
      setResult(res);
    } catch (err: any) {
      setResult({
        status: "not_found",
        message: err.message || "Failed to verify uploaded file.",
      });
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isVerified = result?.status === "verified";
  const isBroken = result?.status === "chain_broken";
  const isNotFound = hasSearched && !isVerified && !isBroken;

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6">
      {/* Header */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 mb-3">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          Public Provenance &amp; Verification Portal
        </div>
        <h1 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
          Verify Content Authenticity
        </h1>
        <p className="mt-2 text-slate-600 text-sm sm:text-base max-w-2xl mx-auto">
          Received a cybersecurity bulletin, executive advisory, or public report? Paste its text or upload
          the document to mathematically confirm it originated from an authorized ContentForge AI issuer without
          alteration.
        </p>
      </div>

      {/* Input Form Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 mb-8">
        {/* Tab switch */}
        <div className="flex border-b border-slate-200 mb-6">
          <button
            type="button"
            onClick={() => {
              setActiveTab("text");
              setHasSearched(false);
              setResult(null);
            }}
            className={`flex items-center gap-2 pb-3 px-4 font-semibold text-sm transition-colors border-b-2 ${
              activeTab === "text"
                ? "border-emerald-600 text-emerald-700"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <FileText className="w-4 h-4" />
            Paste Content Text
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab("file");
              setHasSearched(false);
              setResult(null);
            }}
            className={`flex items-center gap-2 pb-3 px-4 font-semibold text-sm transition-colors border-b-2 ${
              activeTab === "file"
                ? "border-emerald-600 text-emerald-700"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <UploadCloud className="w-4 h-4" />
            Upload File (PDF / DOCX / TXT)
          </button>
        </div>

        {activeTab === "text" ? (
          <form onSubmit={handleVerifyText} className="space-y-4">
            <div>
              <label htmlFor="verify-text" className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                Paste Received Content
              </label>
              <textarea
                id="verify-text"
                rows={6}
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Paste the full text of the advisory, post, or summary here..."
                className="w-full rounded-xl border border-slate-300 p-3 text-sm font-sans focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading || !textInput.trim()}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-emerald-600 text-white font-semibold text-sm shadow hover:bg-emerald-700 transition disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Calculating SHA-256 &amp; Verifying...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  Verify Content Authenticity
                </>
              )}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyFile} className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                Upload Original Document
              </label>
              <div className="border-2 border-dashed border-slate-300 rounded-xl p-6 text-center hover:border-emerald-400 transition bg-slate-50/50">
                <UploadCloud className="w-10 h-10 text-slate-400 mx-auto mb-2" />
                <input
                  type="file"
                  id="verify-file"
                  accept=".pdf,.docx,.txt"
                  onChange={(e) => setFileInput(e.target.files?.[0] || null)}
                  className="hidden"
                />
                <label
                  htmlFor="verify-file"
                  className="cursor-pointer text-sm font-semibold text-emerald-600 hover:text-emerald-700 block"
                >
                  {fileInput ? fileInput.name : "Select or drag document to verify"}
                </label>
                <p className="text-xs text-slate-400 mt-1">Supports PDF, DOCX, and TXT exports</p>
              </div>
            </div>
            <button
              type="submit"
              disabled={loading || !fileInput}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-emerald-600 text-white font-semibold text-sm shadow hover:bg-emerald-700 transition disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Verifying File...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  Verify File Authenticity
                </>
              )}
            </button>
          </form>
        )}
      </div>

      {/* Verification Result Display */}
      {hasSearched && isVerified && result && (
        <div className="rounded-2xl border-2 border-emerald-500 bg-emerald-50/70 p-6 sm:p-8 shadow-sm space-y-6 animate-fadeIn">
          <div className="flex items-center justify-between gap-4 pb-4 border-b border-emerald-200">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-emerald-600 text-white flex items-center justify-center">
                <ShieldCheck className="w-7 h-7" />
              </div>
              <div>
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800 border border-emerald-300">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Authentic Official Record
                </span>
                <h2 className="text-xl sm:text-2xl font-black text-slate-900 mt-1">
                  Content Perfectly Verified
                </h2>
              </div>
            </div>
            {result.record_id && (
              <Link
                href={`/verify/${result.record_id}`}
                className="hidden sm:inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-800 hover:text-emerald-950 underline"
              >
                View Full Ledger Proof <ExternalLink className="w-3.5 h-3.5" />
              </Link>
            )}
          </div>

          <p className="text-sm text-slate-700 leading-relaxed">
            The submitted content matches the exact SHA-256 fingerprint anchored on the ContentForge tamper-evident
            ledger. No tampering, character deletions, or alterations were detected.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="p-4 rounded-xl bg-white border border-emerald-200 shadow-xs">
              <div className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1 mb-1">
                <Building className="w-3.5 h-3.5 text-emerald-600" /> Issuing Organisation
              </div>
              <div className="font-bold text-slate-900 text-sm truncate">{result.organisation_name}</div>
            </div>
            <div className="p-4 rounded-xl bg-white border border-emerald-200 shadow-xs">
              <div className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1 mb-1">
                <UserCheck className="w-3.5 h-3.5 text-emerald-600" /> Approved By
              </div>
              <div className="font-bold text-slate-900 text-sm truncate">
                {result.approved_by || "Authorized Security Reviewer"}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-white border border-emerald-200 shadow-xs">
              <div className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1 mb-1">
                <Clock className="w-3.5 h-3.5 text-emerald-600" /> Anchored Timestamp
              </div>
              <div className="font-bold text-slate-900 text-sm truncate">
                {result.created_at ? new Date(result.created_at).toLocaleDateString() : "Active Record"}
              </div>
            </div>
          </div>
        </div>
      )}

      {hasSearched && isNotFound && (
        <div className="rounded-2xl border-2 border-rose-500 bg-rose-50/70 p-6 sm:p-8 shadow-sm space-y-4 animate-fadeIn">
          <div className="flex items-center gap-3 pb-3 border-b border-rose-200">
            <div className="w-12 h-12 rounded-xl bg-rose-600 text-white flex items-center justify-center">
              <ShieldAlert className="w-7 h-7" />
            </div>
            <div>
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-rose-100 text-rose-800 border border-rose-300">
                Not Verified
              </span>
              <h2 className="text-xl sm:text-2xl font-black text-slate-900 mt-1">
                No Official Matching Record Found
              </h2>
            </div>
          </div>
          <p className="text-sm text-slate-800 font-medium">
            This content does not match any officially approved ContentForge AI record.
          </p>
          <p className="text-xs text-slate-600 leading-relaxed">
            Even a single altered punctuation mark, word change, or unauthorized distribution will alter the SHA-256
            hash and trigger this warning. Do not act on instructions or threat details in this text without
            independent out-of-band verification with the issuing organization.
          </p>
        </div>
      )}

      {hasSearched && isBroken && (
        <div className="rounded-2xl border-2 border-amber-500 bg-amber-50/70 p-6 sm:p-8 shadow-sm space-y-4 animate-fadeIn">
          <div className="flex items-center gap-3 pb-3 border-b border-amber-200">
            <div className="w-12 h-12 rounded-xl bg-amber-600 text-white flex items-center justify-center">
              <AlertTriangle className="w-7 h-7" />
            </div>
            <div>
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-100 text-amber-800 border border-amber-300">
                Warning
              </span>
              <h2 className="text-xl sm:text-2xl font-black text-slate-900 mt-1">
                Ledger Chain Integrity Compromised
              </h2>
            </div>
          </div>
          <p className="text-sm text-slate-700 leading-relaxed">
            A historical ledger break was identified in the organization&apos;s hash-chain. Authenticity cannot be
            guaranteed.
          </p>
        </div>
      )}
    </div>
  );
}
