"use client";

import React, { useState } from "react";
import {
  VideoPackageContent,
  GeneratedOutput,
} from "@/lib/api";
import { ConfidenceScoreBadge } from "../shared/ConfidenceScoreBadge";
import { ClaimHighlighter } from "../traceability/ClaimHighlighter";
import { OutputCardProps } from "./LinkedInCard";
import { Button } from "../shared/Button";
import { Badge } from "../shared/Badge";
import {
  Video,
  Clapperboard,
  Clock,
  Eye,
  Mic,
  Subtitles,
  Edit2,
  Check,
  X,
  Plus,
  Trash2,
} from "lucide-react";

export const VideoScriptCard: React.FC<OutputCardProps<VideoPackageContent>> = ({
  output,
  onSelectClaim,
  selectedClaim,
  onUpdateContent,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState<VideoPackageContent>(output.content);
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

  const updateScene = (index: number, field: string, value: any) => {
    const updated = [...editedContent.scenes];
    updated[index] = { ...updated[index], [field]: value };
    setEditedContent({ ...editedContent, scenes: updated });
  };

  const addScene = () => {
    const newScene = {
      scene_no: editedContent.scenes.length + 1,
      narration: "New voiceover narration",
      visual_description: "B-roll and graphics",
      subtitle_text: "New subtitle line",
      duration_estimate_sec: 10,
    };
    setEditedContent({
      ...editedContent,
      scenes: [...editedContent.scenes, newScene],
    });
  };

  const deleteScene = (index: number) => {
    if (editedContent.scenes.length <= 1) return;
    const updated = editedContent.scenes
      .filter((_, i) => i !== index)
      .map((s, idx) => ({ ...s, scene_no: idx + 1 }));
    setEditedContent({ ...editedContent, scenes: updated });
  };

  return (
    <div
      data-testid="video-package-card"
      className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
    >
      {/* Header Bar */}
      <div className="flex items-center justify-between px-6 py-3.5 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-purple-600 text-white flex items-center justify-center">
            <Video className="w-4 h-4" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-800">Video Script & Storyboard</span>
            <span className="text-[11px] text-slate-500 block">
              Production script with narration, timing, and visual cues
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

      {/* Script & Storyboard Body */}
      <div className="p-6 sm:p-8 space-y-6">
        {isEditing ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="md:col-span-2">
                <label className="text-[11px] font-bold uppercase text-slate-500">
                  Video Title
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
                  Total Runtime Estimate
                </label>
                <input
                  type="text"
                  value={editedContent.total_duration_estimate}
                  onChange={(e) =>
                    setEditedContent({
                      ...editedContent,
                      total_duration_estimate: e.target.value,
                    })
                  }
                  className="w-full mt-1 p-2 text-sm border rounded-lg focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            {/* Scenes Editing */}
            <div className="space-y-3 pt-3">
              <label className="text-[11px] font-bold uppercase text-slate-500">
                Scenes Breakdown
              </label>
              {editedContent.scenes.map((scene, idx) => (
                <div
                  key={idx}
                  className="p-4 border rounded-xl bg-slate-50 space-y-3 relative"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-700">
                      Scene {idx + 1}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-500">
                        Duration (sec):
                      </span>
                      <input
                        type="number"
                        value={scene.duration_estimate_sec}
                        onChange={(e) =>
                          updateScene(
                            idx,
                            "duration_estimate_sec",
                            Number(e.target.value)
                          )
                        }
                        className="w-16 p-1 text-xs border rounded bg-white text-center"
                      />
                      {editedContent.scenes.length > 1 && (
                        <button
                          type="button"
                          onClick={() => deleteScene(idx)}
                          className="text-slate-400 hover:text-red-600 p-1"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>

                  <div>
                    <label className="text-[10px] font-bold uppercase text-slate-500">
                      Narration Voiceover
                    </label>
                    <textarea
                      rows={2}
                      value={scene.narration}
                      onChange={(e) =>
                        updateScene(idx, "narration", e.target.value)
                      }
                      className="w-full mt-1 p-2 text-xs border rounded bg-white"
                    />
                  </div>

                  <div>
                    <label className="text-[10px] font-bold uppercase text-slate-500">
                      Visual Direction / B-Roll
                    </label>
                    <input
                      type="text"
                      value={scene.visual_description}
                      onChange={(e) =>
                        updateScene(idx, "visual_description", e.target.value)
                      }
                      className="w-full mt-1 p-2 text-xs border rounded bg-white"
                    />
                  </div>

                  <div>
                    <label className="text-[10px] font-bold uppercase text-slate-500">
                      On-Screen Subtitle
                    </label>
                    <input
                      type="text"
                      value={scene.subtitle_text}
                      onChange={(e) =>
                        updateScene(idx, "subtitle_text", e.target.value)
                      }
                      className="w-full mt-1 p-2 text-xs border rounded bg-white"
                    />
                  </div>
                </div>
              ))}
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={addScene}
                leftIcon={<Plus className="w-3.5 h-3.5" />}
              >
                Add Scene
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Package Info Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                  Video Package
                </span>
                <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mt-0.5">
                  {output.content.title}
                </h2>
              </div>
              <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-purple-50 text-purple-700 border border-purple-200 text-xs font-semibold shrink-0">
                <Clock className="w-3.5 h-3.5" />
                <span>Runtime: {output.content.total_duration_estimate}</span>
              </div>
            </div>

            {/* Scene-by-Scene Timeline */}
            <div className="space-y-4">
              {output.content.scenes.map((scene, idx) => (
                <div
                  key={idx}
                  className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs hover:border-purple-300 transition-colors space-y-3.5"
                >
                  {/* Scene Number & Duration Header */}
                  <div className="flex items-center justify-between pb-2 border-b border-slate-100 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded-full bg-purple-100 text-purple-800 font-bold text-[11px] font-mono">
                        SCENE {scene.scene_no || idx + 1}
                      </span>
                    </div>
                    <span className="text-slate-500 font-mono text-xs flex items-center gap-1">
                      <Clock className="w-3 h-3 text-slate-400" />
                      ~{scene.duration_estimate_sec}s
                    </span>
                  </div>

                  {/* Narration Script */}
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1 mb-1">
                      <Mic className="w-3 h-3 text-purple-600" />
                      Voiceover Narration
                    </span>
                    <div className="text-sm font-semibold text-slate-900 leading-relaxed font-sans">
                      <ClaimHighlighter
                        text={scene.narration}
                        factIdsUsed={output.content.fact_ids_used}
                        unverifiedClaims={output.unverified_claims}
                        selectedClaim={selectedClaim}
                        onSelectClaim={onSelectClaim}
                      />
                    </div>
                  </div>

                  {/* Visual Description & Subtitle Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/70 text-xs">
                      <span className="font-bold text-slate-500 uppercase tracking-wide flex items-center gap-1 mb-1 text-[10px]">
                        <Eye className="w-3 h-3 text-slate-400" />
                        Visual / Action Cues
                      </span>
                      <p className="text-slate-700 italic leading-relaxed">
                        {scene.visual_description}
                      </p>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-900 text-white text-xs">
                      <span className="font-bold text-slate-400 uppercase tracking-wide flex items-center gap-1 mb-1 text-[10px]">
                        <Subtitles className="w-3 h-3 text-brand-400" />
                        On-Screen Subtitle
                      </span>
                      <p className="font-mono text-slate-200 leading-relaxed">
                        &ldquo;{scene.subtitle_text}&rdquo;
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
