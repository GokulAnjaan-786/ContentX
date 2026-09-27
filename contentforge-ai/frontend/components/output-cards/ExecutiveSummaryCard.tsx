"use client";

import React, { useState } from "react";
import {
  ExecutiveSummaryContent,
  GeneratedOutput,
} from "@/lib/api";
import { ConfidenceScoreBadge } from "../shared/ConfidenceScoreBadge";
import { ClaimHighlighter } from "../traceability/ClaimHighlighter";
import { OutputCardProps } from "./LinkedInCard";
import { Button } from "../shared/Button";
import {
  Briefcase,
  CheckCircle,
  FileText,
  Edit2,
  Check,
  X,
  Sparkles,
} from "lucide-react";

export const ExecutiveSummaryCard: React.FC<OutputCardProps<ExecutiveSummaryContent>> = ({
  output,
  onSelectClaim,
  selectedClaim,
  onUpdateContent,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState<ExecutiveSummaryContent>(output.content);
  const [isSaving, setIsSaving] = useState(false);

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

  return (
    <div
      data-testid="executive-summary-card"
      className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
    >
      {/* Header Bar */}
      <div className="flex items-center justify-between px-6 py-3.5 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center">
            <Briefcase className="w-4 h-4" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-800">Executive Summary</span>
            <span className="text-[11px] text-slate-500 block">
              Leadership briefing & strategic takeaways
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <ConfidenceScoreBadge score={output.validation_score} />
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
              leftIcon={<Edit2 className="w-3 h-3" />}
              data-testid="edit-output-btn"
            >
              Edit
            </Button>
          )}
        </div>
      </div>

      {/* Summary Content */}
      <div className="p-6 sm:p-8 space-y-6">
        {isEditing ? (
          <div className="space-y-4">
            <div>
              <label className="text-[11px] font-bold uppercase text-slate-500">
                Briefing Title
              </label>
              <input
                type="text"
                value={editedContent.title}
                onChange={(e) =>
                  setEditedContent({ ...editedContent, title: e.target.value })
                }
                className="w-full mt-1 p-2 text-sm border rounded-lg focus:ring-2 focus:ring-brand-500 font-semibold"
              />
            </div>

            <div>
              <label className="text-[11px] font-bold uppercase text-slate-500">
                Core Summary Statement
              </label>
              <textarea
                rows={5}
                value={editedContent.summary_text}
                onChange={(e) =>
                  setEditedContent({ ...editedContent, summary_text: e.target.value })
                }
                className="w-full mt-1 p-2 text-sm border rounded-lg focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="text-[11px] font-bold uppercase text-slate-500">
                Key Strategic Takeaways (one per line)
              </label>
              <textarea
                rows={5}
                value={editedContent.key_takeaways.join("\n")}
                onChange={(e) =>
                  setEditedContent({
                    ...editedContent,
                    key_takeaways: e.target.value
                      .split("\n")
                      .map((l) => l.trim())
                      .filter(Boolean),
                  })
                }
                className="w-full mt-1 p-2 text-sm border rounded-lg focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 leading-snug">
                {output.content.title}
              </h2>
            </div>

            {/* Core Narrative */}
            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200/80">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-2">
                Executive Synthesis
              </span>
              <div className="text-sm text-slate-800 leading-relaxed font-sans">
                <ClaimHighlighter
                  text={output.content.summary_text}
                  factIdsUsed={output.content.fact_ids_used}
                  unverifiedClaims={output.unverified_claims}
                  selectedClaim={selectedClaim}
                  onSelectClaim={onSelectClaim}
                />
              </div>
            </div>

            {/* Key Takeaways */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-brand-600" />
                Key Strategic Takeaways
              </h3>
              <div className="grid grid-cols-1 gap-2.5">
                {output.content.key_takeaways.map((takeaway, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl border border-slate-200 bg-white flex items-start gap-3 shadow-xs hover:border-slate-300"
                  >
                    <CheckCircle className="w-4 h-4 text-brand-600 shrink-0 mt-0.5" />
                    <div className="text-sm text-slate-800 leading-relaxed">
                      <ClaimHighlighter
                        text={takeaway}
                        factIdsUsed={output.content.fact_ids_used}
                        unverifiedClaims={output.unverified_claims}
                        selectedClaim={selectedClaim}
                        onSelectClaim={onSelectClaim}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
