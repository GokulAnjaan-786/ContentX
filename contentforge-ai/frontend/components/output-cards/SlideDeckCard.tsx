"use client";

import React, { useState } from "react";
import {
  PresentationContent,
  GeneratedOutput,
} from "@/lib/api";
import { ConfidenceScoreBadge } from "../shared/ConfidenceScoreBadge";
import { ClaimHighlighter } from "../traceability/ClaimHighlighter";
import { OutputCardProps } from "./LinkedInCard";
import { Button } from "../shared/Button";
import {
  Presentation,
  ChevronLeft,
  ChevronRight,
  Tv,
  MessageSquare,
  Sparkles,
  Edit2,
  Check,
  X,
  Plus,
  Trash2,
} from "lucide-react";

export const SlideDeckCard: React.FC<OutputCardProps<PresentationContent>> = ({
  output,
  onSelectClaim,
  selectedClaim,
  onUpdateContent,
}) => {
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState<PresentationContent>(output.content);
  const [isSaving, setIsSaving] = useState(false);

  const totalSlides = editedContent.slides.length;
  const currentSlide = editedContent.slides[currentSlideIndex] || editedContent.slides[0];

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

  const updateSlideField = (index: number, field: string, value: any) => {
    const updated = [...editedContent.slides];
    updated[index] = { ...updated[index], [field]: value };
    setEditedContent({ ...editedContent, slides: updated });
  };

  const addSlide = () => {
    const newSlide = {
      slide_no: editedContent.slides.length + 1,
      title: "New Slide",
      bullets: ["Key bullet point"],
      speaker_notes: "Speaker commentary here",
      visual_suggestion: "Diagram or high-resolution illustration",
    };
    setEditedContent({
      ...editedContent,
      slides: [...editedContent.slides, newSlide],
    });
    setCurrentSlideIndex(editedContent.slides.length);
  };

  const deleteSlide = (index: number) => {
    if (editedContent.slides.length <= 1) return;
    const updated = editedContent.slides
      .filter((_, i) => i !== index)
      .map((s, idx) => ({ ...s, slide_no: idx + 1 }));
    setEditedContent({ ...editedContent, slides: updated });
    if (currentSlideIndex >= updated.length) {
      setCurrentSlideIndex(updated.length - 1);
    }
  };

  return (
    <div
      data-testid="presentation-card"
      className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
    >
      {/* Header Bar */}
      <div className="flex items-center justify-between px-6 py-3.5 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-orange-600 text-white flex items-center justify-center">
            <Presentation className="w-4 h-4" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-800">Slide Deck Presentation</span>
            <span className="text-[11px] text-slate-500 block">
              {totalSlides} Slides • Slide-by-slide viewer
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

      {/* Main Slide Viewer / Editor */}
      <div className="p-6 sm:p-8 space-y-6">
        {isEditing ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-700">Select Slide to Edit:</span>
                <select
                  value={currentSlideIndex}
                  onChange={(e) => setCurrentSlideIndex(Number(e.target.value))}
                  className="p-1.5 text-xs border rounded-md"
                >
                  {editedContent.slides.map((s, idx) => (
                    <option key={idx} value={idx}>
                      Slide {idx + 1}: {s.title}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="secondary" onClick={addSlide} leftIcon={<Plus className="w-3.5 h-3.5" />}>
                  Add Slide
                </Button>
                {editedContent.slides.length > 1 && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => deleteSlide(currentSlideIndex)}
                    leftIcon={<Trash2 className="w-3.5 h-3.5 text-red-500" />}
                  >
                    Delete Current
                  </Button>
                )}
              </div>
            </div>

            <div>
              <label className="text-[11px] font-bold uppercase text-slate-500">
                Slide {currentSlideIndex + 1} Title
              </label>
              <input
                type="text"
                value={currentSlide?.title || ""}
                onChange={(e) => updateSlideField(currentSlideIndex, "title", e.target.value)}
                className="w-full mt-1 p-2 text-sm border rounded-lg focus:ring-2 focus:ring-brand-500 font-semibold"
              />
            </div>

            <div>
              <label className="text-[11px] font-bold uppercase text-slate-500">
                Bullets (one per line)
              </label>
              <textarea
                rows={4}
                value={currentSlide?.bullets?.join("\n") || ""}
                onChange={(e) =>
                  updateSlideField(
                    currentSlideIndex,
                    "bullets",
                    e.target.value.split("\n").filter((l) => l.trim().length > 0)
                  )
                }
                className="w-full mt-1 p-2 text-sm border rounded-lg focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="text-[11px] font-bold uppercase text-slate-500">
                Visual / Layout Suggestion
              </label>
              <input
                type="text"
                value={currentSlide?.visual_suggestion || ""}
                onChange={(e) =>
                  updateSlideField(currentSlideIndex, "visual_suggestion", e.target.value)
                }
                className="w-full mt-1 p-2 text-sm border rounded-lg focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="text-[11px] font-bold uppercase text-slate-500">
                Speaker Notes
              </label>
              <textarea
                rows={3}
                value={currentSlide?.speaker_notes || ""}
                onChange={(e) =>
                  updateSlideField(currentSlideIndex, "speaker_notes", e.target.value)
                }
                className="w-full mt-1 p-2 text-sm border rounded-lg focus:ring-2 focus:ring-brand-500 font-mono text-xs"
              />
            </div>
          </div>
        ) : (
          <div>
            {/* Slide Presentation Frame (16:9 aspect ratio look) */}
            <div className="relative rounded-2xl border-2 border-slate-300 bg-gradient-to-br from-white to-slate-50 shadow-md p-8 sm:p-10 min-h-[340px] flex flex-col justify-between">
              {/* Top Bar of Slide */}
              <div>
                <div className="flex items-center justify-between text-xs text-slate-400 mb-4 pb-2 border-b border-slate-100">
                  <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-brand-600">
                    <Tv className="w-3.5 h-3.5" />
                    ContentForge AI Keynote
                  </div>
                  <span className="font-mono font-bold text-slate-500">
                    Slide {currentSlideIndex + 1} / {totalSlides}
                  </span>
                </div>

                {/* Slide Title */}
                <h3 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight leading-snug">
                  {currentSlide?.title}
                </h3>

                {/* Bullets */}
                <div className="mt-6 space-y-3">
                  {currentSlide?.bullets?.map((bullet, bIdx) => (
                    <div key={bIdx} className="flex items-start gap-3">
                      <span className="w-2 h-2 rounded-full bg-brand-600 mt-2 shrink-0" />
                      <div className="text-sm sm:text-base text-slate-800 leading-relaxed">
                        <ClaimHighlighter
                          text={bullet}
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

              {/* Visual Suggestion Banner inside slide */}
              {currentSlide?.visual_suggestion && (
                <div className="mt-8 pt-4 border-t border-slate-200/60 flex items-center gap-2 text-xs text-slate-600 bg-slate-100/70 p-3 rounded-xl">
                  <Sparkles className="w-4 h-4 text-amber-500 shrink-0" />
                  <span className="font-semibold text-slate-500 shrink-0">Visual Design:</span>
                  <span className="italic">{currentSlide.visual_suggestion}</span>
                </div>
              )}
            </div>

            {/* Slide Navigation Controls */}
            <div className="flex items-center justify-between mt-5 pt-3">
              <Button
                variant="secondary"
                size="sm"
                onClick={() =>
                  setCurrentSlideIndex((prev) => Math.max(0, prev - 1))
                }
                disabled={currentSlideIndex === 0}
                leftIcon={<ChevronLeft className="w-4 h-4" />}
                data-testid="prev-slide-btn"
              >
                Previous Slide
              </Button>

              {/* Slide Dots / Indicator */}
              <div className="flex items-center gap-1.5">
                {output.content.slides.map((_, dotIdx) => (
                  <button
                    key={dotIdx}
                    onClick={() => setCurrentSlideIndex(dotIdx)}
                    className={`h-2 rounded-full transition-all ${
                      dotIdx === currentSlideIndex
                        ? "w-6 bg-brand-600"
                        : "w-2 bg-slate-300 hover:bg-slate-400"
                    }`}
                    aria-label={`Jump to slide ${dotIdx + 1}`}
                  />
                ))}
              </div>

              <Button
                variant="secondary"
                size="sm"
                onClick={() =>
                  setCurrentSlideIndex((prev) => Math.min(totalSlides - 1, prev + 1))
                }
                disabled={currentSlideIndex === totalSlides - 1}
                rightIcon={<ChevronRight className="w-4 h-4" />}
                data-testid="next-slide-btn"
              >
                Next Slide
              </Button>
            </div>

            {/* Speaker Notes Drawer */}
            {currentSlide?.speaker_notes && (
              <div className="mt-5 p-4 rounded-xl bg-amber-50/60 border border-amber-200/80">
                <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-amber-900 mb-1.5">
                  <MessageSquare className="w-3.5 h-3.5 text-amber-700" />
                  Speaker Notes (Presenter View)
                </div>
                <div className="text-xs text-amber-950 font-mono leading-relaxed">
                  <ClaimHighlighter
                    text={currentSlide.speaker_notes}
                    factIdsUsed={output.content.fact_ids_used}
                    unverifiedClaims={output.unverified_claims}
                    selectedClaim={selectedClaim}
                    onSelectClaim={onSelectClaim}
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
