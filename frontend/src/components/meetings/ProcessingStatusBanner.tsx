"use client";

import React, { useEffect, useState } from "react";
import {
  AlertCircle,
  Brain,
  CheckCircle2,
  Database,
  FileAudio,
  Loader2,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { api } from "@/lib/api/client";
import { MeetingStatus, ProcessingStage } from "@/lib/types";

interface ProcessingStatusBannerProps {
  meetingId: string;
  initialStatus: MeetingStatus;
  initialStage?: ProcessingStage | null;
  errorMessage?: string | null;
  onCompleted?: () => void;
}

const STAGES = [
  { key: "UPLOADING", label: "Uploading", icon: FileAudio },
  { key: "TRANSCRIBING", label: "Transcribing (Whisper)", icon: FileAudio },
  { key: "ANALYZING", label: "Analyzing (Intelligence)", icon: Brain },
  { key: "INDEXING", label: "Indexing (pgvector RAG)", icon: Database },
  { key: "READY", label: "Ready", icon: CheckCircle2 },
];

export function ProcessingStatusBanner({
  meetingId,
  initialStatus,
  initialStage,
  errorMessage,
  onCompleted,
}: ProcessingStatusBannerProps) {
  const [status, setStatus] = useState<MeetingStatus>(initialStatus);
  const [stage, setStage] = useState<ProcessingStage | null>(initialStage || "UPLOADING");
  const [error, setError] = useState<string | null>(errorMessage || null);

  useEffect(() => {
    if (status === "COMPLETED" || status === "FAILED") {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const res = await api.get<{
          status: MeetingStatus;
          processing_stage?: ProcessingStage | null;
          error_message?: string | null;
        }>(`/meetings/${meetingId}/status`);

        setStatus(res.status);
        if (res.processing_stage) setStage(res.processing_stage);
        if (res.error_message) setError(res.error_message);

        if (res.status === "COMPLETED") {
          clearInterval(interval);
          if (onCompleted) onCompleted();
        } else if (res.status === "FAILED") {
          clearInterval(interval);
        }
      } catch (err) {
        console.error("Failed to poll status", err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [meetingId, status, onCompleted]);

  if (status === "COMPLETED") {
    return null;
  }

  const currentStageIndex = STAGES.findIndex((s) => s.key === stage);

  return (
    <div
      className={`p-6 rounded-xl border mb-8 animate-fade-in ${
        status === "FAILED"
          ? "bg-rose-500/10 border-rose-500/30 text-rose-300"
          : "bg-surface-100/90 border-primary/30 shadow-lg shadow-primary/5"
      }`}
    >
      <div className="flex items-center justify-between gap-4 mb-4">
        <div className="flex items-center gap-3">
          {status === "FAILED" ? (
            <div className="w-9 h-9 rounded-lg bg-rose-500/20 border border-rose-500/30 flex items-center justify-center text-rose-400">
              <AlertCircle className="w-5 h-5" />
            </div>
          ) : (
            <div className="w-9 h-9 rounded-lg bg-primary/20 border border-primary/30 flex items-center justify-center text-primary-light">
              <Loader2 className="w-5 h-5 animate-spin" />
            </div>
          )}
          <div>
            <h4 className="text-sm font-semibold text-slate-100">
              {status === "FAILED"
                ? "Processing Failed"
                : "MeetMind AI Pipeline In Progress"}
            </h4>
            <p className="text-xs text-slate-400 mt-0.5">
              {status === "FAILED"
                ? error || "An unexpected error occurred during audio processing."
                : "Extracting transcripts, structured intelligence, and generating pgvector embeddings."}
            </p>
          </div>
        </div>

        <div className="hidden sm:flex items-center gap-1 text-xs text-primary-light font-mono">
          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          <span>Live Polling</span>
        </div>
      </div>

      {/* Progress Stepper */}
      {status !== "FAILED" && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2 border-t border-surface-border/50">
          {STAGES.map((s, idx) => {
            const isCompleted = currentStageIndex > idx;
            const isCurrent = currentStageIndex === idx;
            const Icon = s.icon;

            return (
              <div
                key={s.key}
                className={`p-2.5 rounded-lg border text-xs flex items-center gap-2 transition-all ${
                  isCompleted
                    ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                    : isCurrent
                    ? "bg-primary/20 border-primary/40 text-primary-light font-medium"
                    : "bg-surface-200/40 border-surface-border/40 text-slate-500"
                }`}
              >
                {isCompleted ? (
                  <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
                ) : isCurrent ? (
                  <Loader2 className="w-4 h-4 shrink-0 text-primary-light animate-spin" />
                ) : (
                  <Icon className="w-4 h-4 shrink-0" />
                )}
                <span className="truncate">{s.label}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
