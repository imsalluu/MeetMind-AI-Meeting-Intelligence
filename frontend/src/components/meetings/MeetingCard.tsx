"use client";

import React from "react";
import Link from "next/link";
import {
  AlertCircle,
  Calendar,
  CheckCircle2,
  Clock,
  FileAudio,
  Loader2,
  Trash2,
} from "lucide-react";
import { Meeting } from "@/lib/types";
import { formatDate, formatRelativeTime, formatSecondsToTimestamp } from "@/lib/utils/formatters";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";

interface MeetingCardProps {
  meeting: Meeting;
  onDelete?: (id: string) => void;
}

export function MeetingCard({ meeting, onDelete }: MeetingCardProps) {
  const getStatusBadge = (status: Meeting["status"], stage?: Meeting["processing_stage"] | null) => {
    switch (status) {
      case "COMPLETED":
        return (
          <Badge variant="success" className="gap-1">
            <CheckCircle2 className="w-3 h-3" />
            Ready
          </Badge>
        );
      case "PROCESSING":
        return (
          <Badge variant="purple" className="gap-1 animate-pulse-subtle">
            <Loader2 className="w-3 h-3 animate-spin" />
            {stage ? stage.charAt(0) + stage.slice(1).toLowerCase() : "Processing"}
          </Badge>
        );
      case "PENDING":
        return (
          <Badge variant="warning" className="gap-1">
            <Clock className="w-3 h-3" />
            Queued
          </Badge>
        );
      case "FAILED":
        return (
          <Badge variant="destructive" className="gap-1">
            <AlertCircle className="w-3 h-3" />
            Failed
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <Card className="hover:border-surface-hover hover:bg-surface-100/90 transition-all duration-200 group flex flex-col justify-between overflow-hidden">
      <div className="p-5 space-y-3.5">
        {/* Header: Title & Status */}
        <div className="flex items-start justify-between gap-2">
          <Link
            href={`/meetings/${meeting.id}`}
            className="text-base font-semibold text-slate-100 hover:text-primary-light transition-colors line-clamp-1 group-hover:text-primary-light"
          >
            {meeting.title}
          </Link>
          <div className="shrink-0">{getStatusBadge(meeting.status, meeting.processing_stage)}</div>
        </div>

        {/* Description or Audio note */}
        <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed min-h-[32px]">
          {meeting.description || "No description provided."}
        </p>

        {/* Metadata Badges */}
        <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 pt-2 border-t border-surface-border/40">
          <div className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-slate-500" />
            <span>{formatDate(meeting.created_at)}</span>
          </div>

          {meeting.duration_seconds !== null && meeting.duration_seconds !== undefined && (
            <div className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              <span>{formatSecondsToTimestamp(meeting.duration_seconds)}</span>
            </div>
          )}

          {meeting.audio_filename && (
            <div className="flex items-center gap-1.5 max-w-[140px] truncate">
              <FileAudio className="w-3.5 h-3.5 text-slate-500 shrink-0" />
              <span className="truncate">{meeting.audio_filename}</span>
            </div>
          )}
        </div>
      </div>

      {/* Card Footer: Action Links */}
      <div className="px-5 py-3 bg-surface-200/50 border-t border-surface-border/50 flex items-center justify-between">
        <span className="text-[11px] text-slate-500 font-mono">
          {formatRelativeTime(meeting.created_at)}
        </span>

        <div className="flex items-center gap-2">
          {onDelete && (
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                if (confirm(`Delete meeting "${meeting.title}"?`)) {
                  onDelete(meeting.id);
                }
              }}
              className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
              title="Delete meeting"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}

          <Link
            href={`/meetings/${meeting.id}`}
            className="text-xs font-semibold text-primary-light hover:underline"
          >
            Open Intelligence →
          </Link>
        </div>
      </div>
    </Card>
  );
}
