"use client";

import React, { useEffect, useRef, useState } from "react";
import { Clock, Play, Search, User } from "lucide-react";
import { TranscriptSegment } from "@/lib/types";
import { formatSecondsToTimestamp } from "@/lib/utils/formatters";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";

interface TranscriptViewerProps {
  segments: TranscriptSegment[];
  currentTime: number;
  onSeekTo: (seconds: number) => void;
  highlightedTimestamp?: number | null;
}

export function TranscriptViewer({
  segments,
  currentTime,
  onSeekTo,
  highlightedTimestamp,
}: TranscriptViewerProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [autoScroll, setAutoScroll] = useState(true);
  const activeSegmentRef = useRef<HTMLDivElement>(null);

  // Filter segments
  const filteredSegments = segments.filter((s) =>
    s.text.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Auto-scroll into view when active segment changes
  useEffect(() => {
    if (autoScroll && activeSegmentRef.current) {
      activeSegmentRef.current.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }
  }, [currentTime, autoScroll]);

  return (
    <div className="flex flex-col h-full space-y-4">
      {/* Transcript Toolbar */}
      <div className="flex items-center justify-between gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search transcript by keyword..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-surface-100 border border-surface-border text-slate-200 text-xs rounded-lg pl-9 pr-3 py-2 focus:outline-none focus:border-primary"
          />
        </div>

        <button
          onClick={() => setAutoScroll(!autoScroll)}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
            autoScroll
              ? "bg-primary/10 border-primary/30 text-primary-light"
              : "bg-surface-100 border-surface-border text-slate-400"
          }`}
        >
          Auto-scroll: {autoScroll ? "ON" : "OFF"}
        </button>
      </div>

      {/* Segments Stream */}
      <div className="flex-1 overflow-y-auto space-y-2.5 pr-2 max-h-[560px]">
        {filteredSegments.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-sm">
            No matching transcript segments found.
          </div>
        ) : (
          filteredSegments.map((seg) => {
            const isActive =
              currentTime >= seg.start_time && currentTime <= seg.end_time;
            const isTargetHighlight =
              highlightedTimestamp !== undefined &&
              highlightedTimestamp !== null &&
              Math.abs(seg.start_time - highlightedTimestamp) < 3.0;

            return (
              <div
                key={seg.id}
                ref={isActive ? activeSegmentRef : null}
                onClick={() => onSeekTo(seg.start_time)}
                className={`p-3.5 rounded-xl border transition-all duration-150 cursor-pointer group ${
                  isActive
                    ? "bg-primary/15 border-primary/50 shadow-md shadow-primary/10"
                    : isTargetHighlight
                    ? "bg-amber-500/10 border-amber-500/40"
                    : "bg-surface-100/70 border-surface-border/50 hover:bg-surface-100 hover:border-surface-border"
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-surface-50 border border-surface-border flex items-center justify-center text-[10px] text-slate-400 font-medium">
                      <User className="w-3 h-3" />
                    </span>
                    <span className="text-xs font-semibold text-slate-300">
                      {seg.speaker || "Speaker 1"}
                    </span>
                  </div>

                  {/* Clickable timestamp chip */}
                  <div className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-surface-50 group-hover:bg-primary group-hover:text-white transition-colors text-[11px] font-mono text-slate-400">
                    <Play className="w-2.5 h-2.5" />
                    <span>{formatSecondsToTimestamp(seg.start_time)}</span>
                  </div>
                </div>

                <p className="text-sm text-slate-200 leading-relaxed font-normal">
                  {seg.text}
                </p>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
