"use client";

import React, { useState } from "react";
import { LinkedInContent, GeneratedOutput, cleanPublishableText } from "@/lib/api";
import { ConfidenceScoreBadge } from "../shared/ConfidenceScoreBadge";
import { ClaimHighlighter } from "../traceability/ClaimHighlighter";
import { SelectedClaimInfo } from "../traceability/TraceabilityPanel";
import { Button } from "../shared/Button";
import {
  Linkedin,
  ThumbsUp,
  MessageSquare,
  Share2,
  Send,
  Edit2,
  Check,
  X,
  Globe,
  Copy,
  ShieldCheck,
  Eye,
  EyeOff,
} from "lucide-react";

export interface OutputCardProps<T> {
  output: GeneratedOutput<T>;
  onSelectClaim?: (claim: SelectedClaimInfo) => void;
  selectedClaim?: SelectedClaimInfo | null;
  onUpdateContent?: (updatedContent: T) => Promise<void>;
}

export const LinkedInCard: React.FC<OutputCardProps<LinkedInContent>> = ({
  output,
  onSelectClaim,
  selectedClaim,
  onUpdateContent,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState<LinkedInContent>(output.content);
  const [isSaving, setIsSaving] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  const [showVerificationArea, setShowVerificationArea] = useState(false);

  const currentContent = isEditing ? editedContent : output.content;

  const handleSave = async () => {
    if (onUpdateContent) {
      setIsSaving(true);
      try {
        await onUpdateContent(editedContent);
        setIsEditing(false);
      } finally {
        setIsSaving(false);
      }
    }
  };

  const handleCancel = () => {
    setEditedContent(output.content);
    setIsEditing(false);
  };

  const getCleanPostText = (): string => {
    const hook = cleanPublishableText(currentContent.hook || "");
    const body = cleanPublishableText(currentContent.body || "");
    const cta = cleanPublishableText(currentContent.call_to_action || "");
    const hashtags = (currentContent.hashtags || [])
      .map((t) => (t.startsWith("#") ? t : `#${t}`))
      .join(" ");

    return [hook, body, cta, hashtags].filter(Boolean).join("\n\n");
  };

  const handleCopyPost = () => {
    const postText = getCleanPostText();
    navigator.clipboard.writeText(postText);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2500);
  };

  const renderCleanBody = (rawBody: string) => {
    const cleaned = cleanPublishableText(rawBody);
    if (!cleaned) return null;

    const lines = cleaned
      .split(/\n+/)
      .map((l) => l.trim())
      .filter(Boolean);

    return (
      <div className="space-y-3">
        {lines.map((line, idx) => {
          const isBullet = /^(?:[-•*]|\d+[\.)])\s+/.test(line);

          if (isBullet) {
            const cleanLine = line.replace(/^(?:[-•*]|\d+[\.)])\s+/, "");
            return (
              <div key={idx} className="flex items-start gap-2.5 pl-2 py-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#0A66C2] mt-2 shrink-0" />
                <span className="text-slate-800 text-sm sm:text-[15px] leading-relaxed">
                  {cleanLine}
                </span>
              </div>
            );
          }

          return (
            <p key={idx} className="text-slate-800 text-sm sm:text-[15px] leading-relaxed">
              {line}
            </p>
          );
        })}
      </div>
    );
  };

  return (
    <div
      data-testid="linkedin-card"
      className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
    >
      {/* 1. Outer Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-6 py-4 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-[#0A66C2] text-white flex items-center justify-center shrink-0 shadow-xs">
            <Linkedin className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-900">LinkedIn Post</span>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                Publish-Ready
              </span>
            </div>
            <span className="text-[11px] text-slate-500 block">
              B2B thought leadership & executive awareness
            </span>
          </div>
        </div>

        {/* Outer Toolbar (Source Grounding Badge + Copy Post + Edit + View Sources) */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Grounding Badge positioned OUTSIDE the LinkedIn post preview */}
          <ConfidenceScoreBadge score={output.validation_score} />

          {/* Copy Post Button (Copies ONLY clean publish-ready post) */}
          <Button
            size="sm"
            variant={copySuccess ? "secondary" : "primary"}
            onClick={handleCopyPost}
            leftIcon={
              copySuccess ? (
                <Check className="w-3.5 h-3.5 text-emerald-600" />
              ) : (
                <Copy className="w-3.5 h-3.5" />
              )
            }
            className={
              copySuccess
                ? "border-emerald-300 text-emerald-800 bg-emerald-50"
                : "bg-[#0A66C2] hover:bg-[#084e96] border-none text-white font-medium"
            }
            data-testid="copy-post-btn"
          >
            {copySuccess ? "Copied Post!" : "Copy Post"}
          </Button>

          {/* Edit Button */}
          {isEditing ? (
            <div className="flex items-center gap-1.5">
              <Button size="sm" variant="ghost" onClick={handleCancel} disabled={isSaving}>
                <X className="w-3.5 h-3.5" />
                Cancel
              </Button>
              <Button
                size="sm"
                variant="primary"
                onClick={handleSave}
                isLoading={isSaving}
                data-testid="save-edit-btn"
              >
                <Check className="w-3.5 h-3.5" />
                Save
              </Button>
            </div>
          ) : (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => setIsEditing(true)}
              leftIcon={<Edit2 className="w-3.5 h-3.5 text-slate-500" />}
              data-testid="edit-output-btn"
            >
              Edit
            </Button>
          )}

          {/* View Sources / Claim Inspector Toggle */}
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setShowVerificationArea(!showVerificationArea)}
            leftIcon={
              showVerificationArea ? (
                <EyeOff className="w-3.5 h-3.5 text-brand-600" />
              ) : (
                <Eye className="w-3.5 h-3.5 text-brand-600" />
              )
            }
            className="text-xs font-semibold text-brand-700 hover:bg-brand-50"
            data-testid="view-sources-btn"
          >
            {showVerificationArea ? "Hide Claim Inspector" : "View Sources"}
          </Button>
        </div>
      </div>

      {/* 2. Realistic LinkedIn Post Feed Container */}
      <div className="p-4 sm:p-6 bg-slate-100/70">
        <div className="max-w-2xl mx-auto border border-slate-200 rounded-xl bg-white shadow-sm overflow-hidden">
          {/* Mock Author Info Header */}
          <div className="p-4 sm:p-5 pb-3 flex items-center justify-between border-b border-slate-100">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-full bg-gradient-to-tr from-brand-600 to-blue-700 text-white flex items-center justify-center font-bold text-sm shadow-xs border border-white">
                CF
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <p className="text-sm font-bold text-slate-900 leading-tight hover:text-[#0A66C2] cursor-pointer">
                    ContentForge Editorial
                  </p>
                  <span className="text-[10px] text-slate-400">• 1st</span>
                </div>
                <p className="text-xs text-slate-500">AI Fact-Grounded Executive Publishing</p>
                <div className="flex items-center gap-1 text-[11px] text-slate-400 mt-0.5">
                  <span>Just now</span>
                  <span>•</span>
                  <Globe className="w-3 h-3 text-slate-400" />
                </div>
              </div>
            </div>
            <button className="text-xs font-semibold text-[#0A66C2] hover:bg-blue-50 px-3 py-1 rounded-full border border-blue-200 transition-colors hidden sm:block">
              + Follow
            </button>
          </div>

          {/* Post Content Area */}
          <div className="p-4 sm:p-6 space-y-4">
            {isEditing ? (
              <div className="space-y-4">
                <div>
                  <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    Hook (Opening Line)
                  </label>
                  <input
                    type="text"
                    value={editedContent.hook}
                    onChange={(e) =>
                      setEditedContent({ ...editedContent, hook: e.target.value })
                    }
                    className="w-full mt-1.5 p-2.5 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 font-medium"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    Body Text
                  </label>
                  <textarea
                    rows={8}
                    value={editedContent.body}
                    onChange={(e) =>
                      setEditedContent({ ...editedContent, body: e.target.value })
                    }
                    className="w-full mt-1.5 p-2.5 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 font-mono text-xs leading-relaxed"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    Call to Action (CTA)
                  </label>
                  <input
                    type="text"
                    value={editedContent.call_to_action}
                    onChange={(e) =>
                      setEditedContent({
                        ...editedContent,
                        call_to_action: e.target.value,
                      })
                    }
                    className="w-full mt-1.5 p-2.5 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 font-medium"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    Hashtags (comma separated)
                  </label>
                  <input
                    type="text"
                    value={(editedContent.hashtags || []).join(", ")}
                    onChange={(e) =>
                      setEditedContent({
                        ...editedContent,
                        hashtags: e.target.value
                          .split(",")
                          .map((tag) => tag.trim())
                          .filter(Boolean),
                      })
                    }
                    className="w-full mt-1.5 p-2.5 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Opening Hook */}
                {currentContent.hook && (
                  <div className="text-base sm:text-lg font-bold text-slate-900 tracking-tight leading-snug">
                    {cleanPublishableText(currentContent.hook)}
                  </div>
                )}

                {/* Clean Body Text with Paragraphs and Bullets */}
                {currentContent.body && renderCleanBody(currentContent.body)}

                {/* Highlighted Key Takeaway / CTA */}
                {currentContent.call_to_action && (
                  <div className="mt-4 p-3.5 bg-slate-50 border-l-4 border-[#0A66C2] rounded-r-lg">
                    <p className="text-xs font-semibold uppercase tracking-wider text-[#0A66C2] mb-0.5">
                      Key Takeaway / Action
                    </p>
                    <p className="text-sm font-semibold text-slate-900">
                      {cleanPublishableText(currentContent.call_to_action)}
                    </p>
                  </div>
                )}

                {/* Hashtags */}
                {currentContent.hashtags && currentContent.hashtags.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-100">
                    {currentContent.hashtags.map((tag, i) => (
                      <span
                        key={i}
                        className="text-xs font-semibold text-[#0A66C2] hover:underline cursor-pointer"
                      >
                        {tag.startsWith("#") ? tag : `#${tag}`}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* LinkedIn Engagement Footer Bar */}
          <div className="flex items-center justify-between px-4 py-3 bg-slate-50 border-t border-slate-100 text-xs font-semibold text-slate-600">
            <button className="flex items-center gap-1.5 hover:text-[#0A66C2] hover:bg-slate-200/50 px-2 py-1 rounded transition-colors">
              <ThumbsUp className="w-4 h-4 text-slate-500" /> Like
            </button>
            <button className="flex items-center gap-1.5 hover:text-[#0A66C2] hover:bg-slate-200/50 px-2 py-1 rounded transition-colors">
              <MessageSquare className="w-4 h-4 text-slate-500" /> Comment
            </button>
            <button className="flex items-center gap-1.5 hover:text-[#0A66C2] hover:bg-slate-200/50 px-2 py-1 rounded transition-colors">
              <Share2 className="w-4 h-4 text-slate-500" /> Repost
            </button>
            <button className="flex items-center gap-1.5 hover:text-[#0A66C2] hover:bg-slate-200/50 px-2 py-1 rounded transition-colors">
              <Send className="w-4 h-4 text-slate-500" /> Send
            </button>
          </div>
        </div>
      </div>

      {/* 3. Separate ContentX Verification & Claim Inspector Area */}
      {showVerificationArea && (
        <div className="p-6 bg-slate-50 border-t border-slate-200 space-y-4 animate-in fade-in duration-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-brand-600" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                ContentX Verification & Claim Inspector
              </h3>
            </div>
            <span className="text-[11px] text-slate-500">
              Sentence-by-Sentence Fact Registry Provenance
            </span>
          </div>

          <div className="p-4 bg-white rounded-xl border border-slate-200 space-y-3 text-sm">
            <p className="text-xs text-slate-500">
              Click any sentence below to highlight its exact backing evidence in the Fact Registry:
            </p>

            <div className="space-y-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
              {output.content.hook && (
                <div className="font-semibold text-slate-900">
                  <ClaimHighlighter
                    text={output.content.hook}
                    factIdsUsed={output.content.fact_ids_used}
                    unverifiedClaims={output.unverified_claims}
                    selectedClaim={selectedClaim}
                    onSelectClaim={onSelectClaim}
                  />
                </div>
              )}
              {output.content.body && (
                <div className="whitespace-pre-line text-slate-800 text-xs sm:text-sm">
                  <ClaimHighlighter
                    text={output.content.body}
                    factIdsUsed={output.content.fact_ids_used}
                    unverifiedClaims={output.unverified_claims}
                    selectedClaim={selectedClaim}
                    onSelectClaim={onSelectClaim}
                  />
                </div>
              )}
              {output.content.call_to_action && (
                <div className="font-semibold text-brand-700 text-xs">
                  <ClaimHighlighter
                    text={output.content.call_to_action}
                    factIdsUsed={output.content.fact_ids_used}
                    unverifiedClaims={output.unverified_claims}
                    selectedClaim={selectedClaim}
                    onSelectClaim={onSelectClaim}
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
