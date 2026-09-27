"use client";

import React, { useState } from "react";
import {
  AdvisoryContent,
  GeneratedOutput,
} from "@/lib/api";
import { ConfidenceScoreBadge } from "../shared/ConfidenceScoreBadge";
import { ClaimHighlighter } from "../traceability/ClaimHighlighter";
import { OutputCardProps } from "./LinkedInCard";
import { Button } from "../shared/Button";
import { Badge } from "../shared/Badge";
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  FileText,
  ExternalLink,
  Edit2,
  Check,
  X,
  Target,
  ListChecks,
} from "lucide-react";

export const AdvisoryCard: React.FC<OutputCardProps<AdvisoryContent>> = ({
  output,
  onSelectClaim,
  selectedClaim,
  onUpdateContent,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState<AdvisoryContent>(output.content);
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

  const severityLower = (editedContent.severity || "medium").toLowerCase();
  const severityBadgeVariant =
    severityLower.includes("crit") || severityLower.includes("high")
      ? "danger"
      : severityLower.includes("med")
      ? "warning"
      : "brand";

  return (
    <div
      data-testid="advisory-card"
      className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
    >
      {/* Header Bar */}
      <div className="flex items-center justify-between px-6 py-3.5 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-red-600 text-white flex items-center justify-center">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-800">Security & Operational Advisory</span>
            <span className="text-[11px] text-slate-500 block">
              Formal threat analysis & remediation guidance
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

      {/* Advisory Body */}
      <div className="p-6 sm:p-8 space-y-6">
        {isEditing ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="md:col-span-2">
                <label className="text-[11px] font-bold uppercase text-slate-500">
                  Advisory Title
                </label>
                <input
                  type="text"
                  value={editedContent.title}
                  onChange={(e) =>
                    setEditedContent({ ...editedContent, title: e.target.value })
                  }
                  className="w-full mt-1 p-2 text-sm border rounded-lg focus:ring-2 focus:ring-brand-500"
                />
              </div>
              <div>
                <label className="text-[11px] font-bold uppercase text-slate-500">
                  Severity Level
                </label>
                <select
                  value={editedContent.severity}
                  onChange={(e) =>
                    setEditedContent({ ...editedContent, severity: e.target.value })
                  }
                  className="w-full mt-1 p-2 text-sm border rounded-lg focus:ring-2 focus:ring-brand-500"
                >
                  <option value="CRITICAL">CRITICAL</option>
                  <option value="HIGH">HIGH</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="LOW">LOW</option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-[11px] font-bold uppercase text-slate-500">
                Scope / Impacted Systems
              </label>
              <input
                type="text"
                value={editedContent.scope}
                onChange={(e) =>
                  setEditedContent({ ...editedContent, scope: e.target.value })
                }
                className="w-full mt-1 p-2 text-sm border rounded-lg focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="text-[11px] font-bold uppercase text-slate-500">
                Summary
              </label>
              <textarea
                rows={3}
                value={editedContent.summary}
                onChange={(e) =>
                  setEditedContent({ ...editedContent, summary: e.target.value })
                }
                className="w-full mt-1 p-2 text-sm border rounded-lg focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="text-[11px] font-bold uppercase text-slate-500">
                Technical Details
              </label>
              <textarea
                rows={5}
                value={editedContent.details}
                onChange={(e) =>
                  setEditedContent({ ...editedContent, details: e.target.value })
                }
                className="w-full mt-1 p-2 text-sm border rounded-lg focus:ring-2 focus:ring-brand-500 font-mono text-xs"
              />
            </div>

            <div>
              <label className="text-[11px] font-bold uppercase text-slate-500">
                Recommended Actions (one per line)
              </label>
              <textarea
                rows={4}
                value={editedContent.recommended_actions.join("\n")}
                onChange={(e) =>
                  setEditedContent({
                    ...editedContent,
                    recommended_actions: e.target.value
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
            {/* Title & Metadata Header */}
            <div className="pb-5 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant={severityBadgeVariant} size="md">
                    SEVERITY: {output.content.severity.toUpperCase()}
                  </Badge>
                  <span className="text-xs text-slate-400">•</span>
                  <span className="text-xs font-mono text-slate-500">
                    ID: ADV-{output.id.slice(0, 8)}
                  </span>
                </div>
                <h2 className="text-xl font-bold text-slate-900 leading-snug">
                  {output.content.title}
                </h2>
              </div>
            </div>

            {/* Scope Alert Box */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 flex items-start gap-3">
              <Target className="w-5 h-5 text-brand-600 shrink-0 mt-0.5" />
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Target Scope & Impacted Systems
                </span>
                <p className="text-sm font-semibold text-slate-800 mt-0.5">
                  {output.content.scope}
                </p>
              </div>
            </div>

            {/* Summary Section */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Executive Overview
              </h3>
              <div className="text-sm text-slate-800 leading-relaxed bg-white p-4 rounded-xl border border-slate-200">
                <ClaimHighlighter
                  text={output.content.summary}
                  factIdsUsed={output.content.fact_ids_used}
                  unverifiedClaims={output.unverified_claims}
                  selectedClaim={selectedClaim}
                  onSelectClaim={onSelectClaim}
                />
              </div>
            </div>

            {/* Details Section */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Technical Analysis & Impact
              </h3>
              <div className="text-sm text-slate-800 leading-relaxed bg-white p-4 rounded-xl border border-slate-200 whitespace-pre-line">
                <ClaimHighlighter
                  text={output.content.details}
                  factIdsUsed={output.content.fact_ids_used}
                  unverifiedClaims={output.unverified_claims}
                  selectedClaim={selectedClaim}
                  onSelectClaim={onSelectClaim}
                />
              </div>
            </div>

            {/* Recommended Actions */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
                <ListChecks className="w-4 h-4 text-emerald-600" />
                Recommended Remediation Actions
              </h3>
              <div className="space-y-2">
                {output.content.recommended_actions.map((action, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl border border-slate-200 bg-white flex items-start gap-3 hover:border-slate-300"
                  >
                    <span className="w-5 h-5 rounded-full bg-emerald-50 text-emerald-700 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5 border border-emerald-200">
                      {idx + 1}
                    </span>
                    <div className="text-sm text-slate-800 leading-relaxed">
                      <ClaimHighlighter
                        text={action}
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

            {/* References */}
            {output.content.references && output.content.references.length > 0 && (
              <div className="pt-4 border-t border-slate-100">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                  Official References
                </h4>
                <div className="flex flex-wrap gap-2">
                  {output.content.references.map((ref, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 text-xs text-brand-600 bg-brand-50 px-2.5 py-1 rounded-md border border-brand-200 font-mono"
                    >
                      <ExternalLink className="w-3 h-3" />
                      {ref}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
