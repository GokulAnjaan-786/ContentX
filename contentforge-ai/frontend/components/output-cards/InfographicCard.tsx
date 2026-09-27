"use client";

import React, { useState } from "react";
import {
  InfographicContent,
  GeneratedOutput,
} from "@/lib/api";
import { ConfidenceScoreBadge } from "../shared/ConfidenceScoreBadge";
import { ClaimHighlighter } from "../traceability/ClaimHighlighter";
import { OutputCardProps } from "./LinkedInCard";
import { Button } from "../shared/Button";
import { Badge } from "../shared/Badge";
import {
  BarChart3,
  Palette,
  Layout,
  Lightbulb,
  Edit2,
  Check,
  X,
  Plus,
  Trash2,
} from "lucide-react";

export const InfographicCard: React.FC<OutputCardProps<InfographicContent>> = ({
  output,
  onSelectClaim,
  selectedClaim,
  onUpdateContent,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState<InfographicContent>(output.content);
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

  const updateSection = (index: number, statOrPoint: string, iconSuggestion: string) => {
    const updated = [...editedContent.sections];
    updated[index] = {
      ...updated[index],
      stat_or_point: statOrPoint,
      icon_suggestion: iconSuggestion,
    };
    setEditedContent({ ...editedContent, sections: updated });
  };

  const addSection = () => {
    setEditedContent({
      ...editedContent,
      sections: [
        ...editedContent.sections,
        {
          order: editedContent.sections.length + 1,
          stat_or_point: "",
          icon_suggestion: "chart-line",
        },
      ],
    });
  };

  const deleteSection = (index: number) => {
    const updated = editedContent.sections
      .filter((_, i) => i !== index)
      .map((sec, idx) => ({ ...sec, order: idx + 1 }));
    setEditedContent({ ...editedContent, sections: updated });
  };

  return (
    <div
      data-testid="infographic-card"
      className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
    >
      {/* Header Bar */}
      <div className="flex items-center justify-between px-6 py-3.5 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-teal-600 text-white flex items-center justify-center">
            <BarChart3 className="w-4 h-4" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-800">Infographic Blueprint</span>
            <span className="text-[11px] text-slate-500 block">
              Visual narrative architecture & statistics
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

      {/* Blueprint Content */}
      <div className="p-6 sm:p-8 space-y-6">
        {isEditing ? (
          <div className="space-y-4">
            <div>
              <label className="text-[11px] font-bold uppercase text-slate-500">
                Headline
              </label>
              <input
                type="text"
                value={editedContent.headline}
                onChange={(e) =>
                  setEditedContent({ ...editedContent, headline: e.target.value })
                }
                className="w-full mt-1 p-2 text-sm border rounded-lg focus:ring-2 focus:ring-brand-500 font-semibold"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] font-bold uppercase text-slate-500">
                  Layout Style
                </label>
                <input
                  type="text"
                  value={editedContent.layout_style}
                  onChange={(e) =>
                    setEditedContent({ ...editedContent, layout_style: e.target.value })
                  }
                  className="w-full mt-1 p-2 text-sm border rounded-lg focus:ring-2 focus:ring-brand-500"
                />
              </div>
              <div>
                <label className="text-[11px] font-bold uppercase text-slate-500">
                  Colour Theme Suggestion
                </label>
                <input
                  type="text"
                  value={editedContent.colour_theme}
                  onChange={(e) =>
                    setEditedContent({ ...editedContent, colour_theme: e.target.value })
                  }
                  className="w-full mt-1 p-2 text-sm border rounded-lg focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            {/* Sections editing */}
            <div className="space-y-3 pt-2">
              <label className="text-[11px] font-bold uppercase text-slate-500">
                Data Points & Sections
              </label>
              {editedContent.sections.map((sec, idx) => (
                <div
                  key={idx}
                  className="p-3 border rounded-xl bg-slate-50 space-y-2 relative"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-600">
                      Section {idx + 1}
                    </span>
                    {editedContent.sections.length > 1 && (
                      <button
                        type="button"
                        onClick={() => deleteSection(idx)}
                        className="text-slate-400 hover:text-red-600 p-1"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                  <input
                    type="text"
                    value={sec.stat_or_point}
                    onChange={(e) =>
                      updateSection(idx, e.target.value, sec.icon_suggestion)
                    }
                    placeholder="Stat or key point"
                    className="w-full p-2 text-xs border rounded bg-white"
                  />
                  <input
                    type="text"
                    value={sec.icon_suggestion}
                    onChange={(e) =>
                      updateSection(idx, sec.stat_or_point, e.target.value)
                    }
                    placeholder="Icon suggestion (e.g. shield, chart, cloud)"
                    className="w-full p-2 text-xs border rounded bg-white"
                  />
                </div>
              ))}
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={addSection}
                leftIcon={<Plus className="w-3.5 h-3.5" />}
              >
                Add Data Section
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Headline */}
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Visual Campaign Headline
              </span>
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mt-1">
                {output.content.headline}
              </h2>
            </div>

            {/* Layout & Colour Metadata Pills */}
            <div className="flex flex-wrap items-center gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200">
              <div className="flex items-center gap-1.5 text-xs text-slate-700">
                <Layout className="w-4 h-4 text-teal-600" />
                <span className="font-semibold text-slate-500">Layout:</span>
                <span className="font-medium text-slate-900">
                  {output.content.layout_style}
                </span>
              </div>
              <span className="text-slate-300">•</span>
              <div className="flex items-center gap-1.5 text-xs text-slate-700">
                <Palette className="w-4 h-4 text-indigo-600" />
                <span className="font-semibold text-slate-500">Theme:</span>
                <span className="font-medium text-slate-900">
                  {output.content.colour_theme}
                </span>
              </div>
            </div>

            {/* Sections / Stats Grid */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Infographic Modules & Statistics
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                {output.content.sections.map((sec, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border border-slate-200 bg-white shadow-xs hover:border-teal-300 transition-colors flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="w-6 h-6 rounded-full bg-teal-50 text-teal-700 font-bold text-xs flex items-center justify-center border border-teal-200">
                          {sec.order || idx + 1}
                        </span>
                        <span className="inline-flex items-center gap-1 text-[11px] font-mono text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                          <Lightbulb className="w-3 h-3" />
                          {sec.icon_suggestion}
                        </span>
                      </div>
                      <div className="text-sm font-medium text-slate-800 leading-relaxed mt-2">
                        <ClaimHighlighter
                          text={sec.stat_or_point}
                          factIdsUsed={output.content.fact_ids_used}
                          unverifiedClaims={output.unverified_claims}
                          selectedClaim={selectedClaim}
                          onSelectClaim={onSelectClaim}
                        />
                      </div>
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
