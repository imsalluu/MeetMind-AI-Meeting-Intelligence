"use client";

import React, { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Check, FileAudio, Loader2, UploadCloud, X } from "lucide-react";
import { api } from "@/lib/api/client";
import { Meeting } from "@/lib/types";
import { formatFileSize } from "@/lib/utils/formatters";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";

interface NewMeetingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onMeetingCreated?: (meeting: Meeting) => void;
}

const ALLOWED_EXTENSIONS = [".mp3", ".wav", ".m4a", ".mp4", ".aac", ".flac", ".webm"];

export function NewMeetingModal({ isOpen, onClose, onMeetingCreated }: NewMeetingModalProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    setError(null);
    const ext = "." + selectedFile.name.split(".").pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setError(`Unsupported format. Please upload: ${ALLOWED_EXTENSIONS.join(", ")}`);
      return;
    }
    if (selectedFile.size > 100 * 1024 * 1024) {
      setError("File size exceeds 100 MB limit.");
      return;
    }
    setFile(selectedFile);
    if (!title) {
      // Auto-populate title from filename
      const defaultName = selectedFile.name.replace(/\.[^/.]+$/, "").replace(/[_-]/g, " ");
      setTitle(defaultName.charAt(0).toUpperCase() + defaultName.slice(1));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError("Please enter a meeting title.");
      return;
    }
    if (!file) {
      setError("Please select or drop an audio recording.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // 1. Create meeting entity
      const createdMeeting = await api.post<Meeting>("/meetings", {
        title: title.trim(),
        description: description.trim() || undefined,
      });

      // 2. Upload audio file
      const formData = new FormData();
      formData.append("file", file);
      const uploadedMeeting = await api.post<Meeting>(
        `/meetings/${createdMeeting.id}/upload`,
        formData
      );

      if (onMeetingCreated) {
        onMeetingCreated(uploadedMeeting);
      }

      onClose();
      // Redirect to meeting intelligence detail page
      router.push(`/meetings/${uploadedMeeting.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to upload and create meeting.");
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Upload Meeting Recording"
      description="Upload an audio file (MP3, WAV, M4A, MP4) to generate transcription and intelligence."
      maxWidth="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-xs text-rose-400">
            {error}
          </div>
        )}

        <Input
          label="Meeting Title"
          placeholder="e.g., Q3 Product Roadmap & Architecture Sync"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />

        <div className="space-y-1.5">
          <label className="block text-xs font-medium text-slate-300">
            Description / Context (Optional)
          </label>
          <textarea
            className="w-full bg-surface-200/80 border border-surface-border text-slate-100 placeholder-slate-500 text-sm rounded-lg px-3.5 py-2.5 transition-all duration-150 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary min-h-[70px] resize-none"
            placeholder="Key background context, participants, or goals for this session..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>

        {/* Audio Drag & Drop Area */}
        <div className="space-y-1.5">
          <label className="block text-xs font-medium text-slate-300">Audio Recording</label>
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept=".mp3,.wav,.m4a,.mp4,.aac,.flac,.webm"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                validateAndSetFile(e.target.files[0]);
              }
            }}
          />

          {!file ? (
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200 flex flex-col items-center justify-center gap-2.5 ${
                isDragging
                  ? "border-primary bg-primary/10"
                  : "border-surface-border hover:border-slate-600 bg-surface-200/50"
              }`}
            >
              <div className="w-12 h-12 rounded-full bg-surface-100 flex items-center justify-center text-slate-400 border border-surface-border">
                <UploadCloud className="w-6 h-6 text-primary-light" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-200">
                  Click to browse or drag and drop audio
                </p>
                <p className="text-xs text-slate-500 mt-0.5">
                  Supports MP3, WAV, M4A, MP4 (Max 100 MB)
                </p>
              </div>
            </div>
          ) : (
            <div className="p-4 bg-surface-200/80 border border-primary/30 rounded-xl flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-primary/20 border border-primary/40 flex items-center justify-center text-primary-light">
                  <FileAudio className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-200 max-w-[280px] truncate">
                    {file.name}
                  </p>
                  <p className="text-xs text-slate-400 font-mono">{formatFileSize(file.size)}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setFile(null)}
                className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 pt-4 border-t border-surface-border">
          <Button type="button" variant="ghost" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button
            type="submit"
            isLoading={isLoading}
            disabled={!file || !title.trim()}
            leftIcon={<UploadCloud className="w-4 h-4" />}
          >
            Start Processing Pipeline
          </Button>
        </div>
      </form>
    </Modal>
  );
}
