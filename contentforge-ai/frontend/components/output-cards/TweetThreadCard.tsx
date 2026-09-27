"use client";

import React, { useState } from "react";
import {
  TwitterContent,
  GeneratedOutput,
} from "@/lib/api";
import { ConfidenceScoreBadge } from "../shared/ConfidenceScoreBadge";
import { ClaimHighlighter } from "../traceability/ClaimHighlighter";
import { OutputCardProps } from "./LinkedInCard";
import { Button } from "../shared/Button";
import {
  Twitter,
  MessageCircle,
  Repeat2,
  Heart,
  Share,
  Edit2,
  Check,
  X,
  Plus,
  Trash2,
} from "lucide-react";

export const TweetThreadCard: React.FC<OutputCardProps<TwitterContent>> = ({
  output,
  onSelectClaim,
  selectedClaim,
  onUpdateContent,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState<TwitterContent>(output.content);
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

  const updateTweetText = (index: number, text: string) => {
    const updated = [...editedContent.tweets];
    updated[index] = { ...updated[index], text };
    setEditedContent({ ...editedContent, tweets: updated });
  };

  const deleteTweet = (index: number) => {
    const updated = editedContent.tweets.filter((_, i) => i !== index);
    const reordered = updated.map((t, idx) => ({ ...t, order: idx + 1 }));
    setEditedContent({ ...editedContent, tweets: reordered });
  };

  const addTweet = () => {
    const newTweet = {
      order: editedContent.tweets.length + 1,
      text: "",
    };
    setEditedContent({
      ...editedContent,
      tweets: [...editedContent.tweets, newTweet],
    });
  };

  return (
    <div
      data-testid="twitter-card"
      className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
    >
      {/* Card Header Bar */}
      <div className="flex items-center justify-between px-6 py-3.5 bg-slate-50 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-sky-500 text-white flex items-center justify-center">
            <Twitter className="w-4 h-4" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-800">Twitter / X Thread</span>
            <span className="text-[11px] text-slate-500 block">
              {output.content.tweets.length} Connected Tweets
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

      {/* Tweet Thread Body */}
      <div className="p-6 max-w-xl mx-auto space-y-6">
        {isEditing ? (
          <div className="space-y-4">
            {editedContent.tweets.map((tweet, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-2 relative"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-600">
                    Tweet {idx + 1} of {editedContent.tweets.length}
                  </span>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[11px] font-mono ${
                        tweet.text.length > 280 ? "text-red-600 font-bold" : "text-slate-400"
                      }`}
                    >
                      {tweet.text.length}/280
                    </span>
                    {editedContent.tweets.length > 1 && (
                      <button
                        type="button"
                        onClick={() => deleteTweet(idx)}
                        className="text-slate-400 hover:text-red-600 p-1"
                        title="Delete tweet"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
                <textarea
                  rows={3}
                  value={tweet.text}
                  onChange={(e) => updateTweetText(idx, e.target.value)}
                  className="w-full p-2.5 text-sm border rounded-lg focus:ring-2 focus:ring-brand-500 bg-white"
                />
              </div>
            ))}
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={addTweet}
              leftIcon={<Plus className="w-3.5 h-3.5" />}
              className="w-full"
            >
              Add Tweet to Thread
            </Button>
          </div>
        ) : (
          <div className="relative pl-6 space-y-6 before:absolute before:left-3 before:top-4 before:bottom-4 before:w-0.5 before:bg-slate-200">
            {output.content.tweets.map((tweet, idx) => {
              const total = output.content.tweets.length;
              return (
                <div key={idx} className="relative group">
                  {/* Thread Node Dot */}
                  <div className="absolute -left-6 top-3 w-6 h-6 rounded-full bg-sky-50 border-2 border-sky-500 flex items-center justify-center text-[10px] font-bold text-sky-700 shadow-xs z-10">
                    {idx + 1}
                  </div>

                  {/* Tweet Bubble */}
                  <div className="ml-3 p-4 rounded-xl border border-slate-200 bg-white shadow-xs hover:border-slate-300 transition-colors">
                    <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                      <div className="flex items-center gap-1.5">
                        <span className="font-bold text-slate-800">ContentForge</span>
                        <span className="text-slate-400">@contentforge</span>
                      </div>
                      <span className="text-[11px] font-mono text-slate-400">
                        {idx + 1}/{total}
                      </span>
                    </div>

                    {/* Tweet Text with Traceability */}
                    <div className="text-sm text-slate-800 leading-relaxed font-sans">
                      <ClaimHighlighter
                        text={tweet.text}
                        factIdsUsed={output.content.fact_ids_used}
                        unverifiedClaims={output.unverified_claims}
                        selectedClaim={selectedClaim}
                        onSelectClaim={onSelectClaim}
                      />
                    </div>

                    {/* Tweet Actions */}
                    <div className="flex items-center justify-between mt-3 pt-2.5 border-t border-slate-100 text-xs text-slate-400">
                      <span className="flex items-center gap-1 hover:text-sky-500 cursor-pointer">
                        <MessageCircle className="w-3.5 h-3.5" /> 12
                      </span>
                      <span className="flex items-center gap-1 hover:text-emerald-500 cursor-pointer">
                        <Repeat2 className="w-3.5 h-3.5" /> 8
                      </span>
                      <span className="flex items-center gap-1 hover:text-rose-500 cursor-pointer">
                        <Heart className="w-3.5 h-3.5" /> 45
                      </span>
                      <span className="flex items-center gap-1 hover:text-slate-600 cursor-pointer">
                        <Share className="w-3.5 h-3.5" />
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
