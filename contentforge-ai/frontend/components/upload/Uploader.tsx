"use client";

import React, { useState, useRef } from "react";
import { UploadCloud, FileText, CheckCircle2, AlertCircle, FileCode } from "lucide-react";
import { Button } from "../shared/Button";

export interface UploaderProps {
  onUploadFile: (file: File) => Promise<void>;
  onUploadText: (text: string, title?: string) => Promise<void>;
  isSubmitting?: boolean;
}

export const Uploader: React.FC<UploaderProps> = ({
  onUploadFile,
  onUploadText,
  isSubmitting = false,
}) => {
  const [activeTab, setActiveTab] = useState<"file" | "text">("file");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [rawText, setRawText] = useState("");
  const [textTitle, setTextTitle] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      validateAndSetFile(file);
    }
  };

  const validateAndSetFile = (file: File) => {
    setValidationError(null);
    const validExtensions = [".pdf", ".docx", ".txt"];
    const hasValidExt = validExtensions.some((ext) =>
      file.name.toLowerCase().endsWith(ext)
    );
    if (!hasValidExt) {
      setValidationError("Only PDF (.pdf), Word (.docx), and Text (.txt) documents are supported.");
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      setValidationError("File size exceeds 20MB limit.");
      return;
    }
    setSelectedFile(file);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    if (activeTab === "file") {
      if (!selectedFile) {
        setValidationError("Please select or drop a PDF, DOCX, or TXT file to proceed.");
        return;
      }
      await onUploadFile(selectedFile);
    } else {
      if (!rawText.trim()) {
        setValidationError("Please paste or type content into the text area.");
        return;
      }
      if (rawText.trim().length < 50) {
        setValidationError("Content is too short. Please provide at least 50 characters.");
        return;
      }
      await onUploadText(rawText, textTitle.trim() || undefined);
    }
  };

  return (
    <div className="w-full bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
      {/* Tab Switcher */}
      <div className="flex border-b border-slate-200 mb-6">
        <button
          type="button"
          onClick={() => {
            setActiveTab("file");
            setValidationError(null);
          }}
          className={`flex items-center gap-2 pb-3 px-4 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === "file"
              ? "border-brand-600 text-brand-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <UploadCloud className="w-4 h-4" />
          File Upload (.pdf, .docx, .txt)
        </button>
        <button
          type="button"
          onClick={() => {
            setActiveTab("text");
            setValidationError(null);
          }}
          className={`flex items-center gap-2 pb-3 px-4 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === "text"
              ? "border-brand-600 text-brand-600"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <FileText className="w-4 h-4" />
          Paste Raw Text
        </button>
      </div>

      {validationError && (
        <div className="mb-5 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-800 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{validationError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {activeTab === "file" ? (
          <div>
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
                dragOver
                  ? "border-brand-500 bg-brand-50/50"
                  : selectedFile
                  ? "border-emerald-400 bg-emerald-50/30"
                  : "border-slate-300 hover:border-brand-400 bg-slate-50/50"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt,text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={handleFileChange}
                className="hidden"
                data-testid="file-input"
              />

              {selectedFile ? (
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mb-3">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>
                  <p className="text-sm font-semibold text-slate-900">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • Ready for ingestion
                  </p>
                  <p className="text-xs text-brand-600 font-medium mt-3 hover:underline">
                    Click to replace file
                  </p>
                </div>
              ) : (
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 rounded-full bg-brand-50 text-brand-600 flex items-center justify-center mb-3">
                    <UploadCloud className="w-6 h-6" />
                  </div>
                  <p className="text-sm font-semibold text-slate-800">
                    Drag & drop your document here, or{" "}
                    <span className="text-brand-600">browse files</span>
                  </p>
                  <p className="text-xs text-slate-500 mt-1.5">
                    Supports PDF, DOCX, and TXT files (up to 20MB)
                  </p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label
                htmlFor="document-title"
                className="block text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1"
              >
                Optional Document Title
              </label>
              <input
                id="document-title"
                type="text"
                value={textTitle}
                onChange={(e) => setTextTitle(e.target.value)}
                placeholder="e.g. Q3 Cybersecurity Threat Report 2026"
                className="w-full px-3.5 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <label
                  htmlFor="raw-content"
                  className="block text-xs font-semibold text-slate-700 uppercase tracking-wide"
                >
                  Raw Source Text
                </label>
                <span className="text-xs text-slate-400 font-mono">
                  {rawText.length} characters
                </span>
              </div>
              <textarea
                id="raw-content"
                rows={10}
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                placeholder="Paste the raw text of your report, security advisory, article, or announcement here..."
                className="w-full p-3.5 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-brand-500 font-sans leading-relaxed"
                data-testid="paste-text-input"
              />
            </div>
          </div>
        )}

        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
          <Button
            type="submit"
            size="lg"
            isLoading={isSubmitting}
            className="w-full sm:w-auto"
            data-testid="upload-submit-btn"
          >
            Process Source Content
          </Button>
        </div>
      </form>
    </div>
  );
};
