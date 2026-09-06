"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  BarChart3,
  Calendar,
  CheckCircle2,
  Clock,
  FileAudio,
  FolderOpen,
  ListTodo,
  Loader2,
  Plus,
  Search,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { api } from "@/lib/api/client";
import { Meeting, MeetingListResponse } from "@/lib/types";
import { formatSecondsToTimestamp } from "@/lib/utils/formatters";
import { AppShell } from "@/components/layout/AppShell";
import { MeetingCard } from "@/components/meetings/MeetingCard";
import { NewMeetingModal } from "@/components/meetings/NewMeetingModal";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";

export default function DashboardPage() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  const fetchMeetings = async () => {
    setIsLoading(true);
    try {
      const res = await api.get<MeetingListResponse>("/meetings", {
        page_size: 50,
      });
      setMeetings(res.items);
    } catch (err) {
      console.error("Failed to load meetings", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMeetings();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/meetings/${id}`);
      setMeetings((prev) => prev.filter((m) => m.id !== id));
    } catch (err) {
      console.error("Failed to delete meeting", err);
    }
  };

  // Metrics computation
  const totalMeetings = meetings.length;
  const totalSeconds = meetings.reduce((acc, m) => acc + (m.duration_seconds || 0), 0);
  const totalHours = (totalSeconds / 3600).toFixed(1);
  const completedMeetings = meetings.filter((m) => m.status === "COMPLETED").length;
  const processingMeetings = meetings.filter(
    (m) => m.status === "PROCESSING" || m.status === "PENDING"
  ).length;

  // Filtered list
  const filteredMeetings = meetings.filter((m) => {
    const matchesSearch =
      m.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (m.description && m.description.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesStatus = statusFilter === "ALL" || m.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <AppShell onNewMeetingClick={() => setIsModalOpen(true)}>
      <div className="space-y-8">
        {/* Welcome Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
              Meeting Intelligence Dashboard
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Overview of your transcribed recordings, action items, and conversational RAG sessions.
            </p>
          </div>

          <Button
            onClick={() => setIsModalOpen(true)}
            size="md"
            leftIcon={<Plus className="w-4 h-4" />}
          >
            New Meeting Recording
          </Button>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <Card glow className="p-5 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-xs font-medium text-slate-400">Total Meetings</p>
              <p className="text-2xl font-bold text-slate-100">{totalMeetings}</p>
              <p className="text-[11px] text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                {completedMeetings} ready for RAG
              </p>
            </div>
            <div className="w-11 h-11 rounded-xl bg-primary/15 border border-primary/30 flex items-center justify-center text-primary-light">
              <FolderOpen className="w-5 h-5" />
            </div>
          </Card>

          <Card glow className="p-5 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-xs font-medium text-slate-400">Total Meeting Hours</p>
              <p className="text-2xl font-bold text-slate-100">{totalHours}h</p>
              <p className="text-[11px] text-slate-500">
                {formatSecondsToTimestamp(totalSeconds)} recorded
              </p>
            </div>
            <div className="w-11 h-11 rounded-xl bg-accent-violet/15 border border-accent-violet/30 flex items-center justify-center text-accent-violet">
              <Clock className="w-5 h-5" />
            </div>
          </Card>

          <Card glow className="p-5 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-xs font-medium text-slate-400">Active Pipelines</p>
              <p className="text-2xl font-bold text-slate-100">{processingMeetings}</p>
              <p className="text-[11px] text-primary-light">
                {processingMeetings > 0 ? "Transcribing & Indexing..." : "All caught up"}
              </p>
            </div>
            <div className="w-11 h-11 rounded-xl bg-accent-cyan/15 border border-accent-cyan/30 flex items-center justify-center text-accent-cyan">
              <Loader2 className={`w-5 h-5 ${processingMeetings > 0 ? "animate-spin" : ""}`} />
            </div>
          </Card>

          <Card glow className="p-5 flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-xs font-medium text-slate-400">RAG Readiness</p>
              <p className="text-2xl font-bold text-slate-100">
                {totalMeetings > 0
                  ? `${Math.round((completedMeetings / totalMeetings) * 100)}%`
                  : "100%"}
              </p>
              <p className="text-[11px] text-slate-400 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-primary-light" />
                pgvector semantic search
              </p>
            </div>
            <div className="w-11 h-11 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <TrendingUp className="w-5 h-5" />
            </div>
          </Card>
        </div>

        {/* Search & Filter Toolbar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Filter meetings by title..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-surface-100 border border-surface-border text-slate-200 text-sm rounded-lg pl-9 pr-4 py-2 focus:outline-none focus:border-primary"
            />
          </div>

          <div className="flex items-center gap-1.5 self-start sm:self-auto bg-surface-100 p-1 border border-surface-border rounded-lg">
            {["ALL", "COMPLETED", "PROCESSING", "FAILED"].map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                  statusFilter === s
                    ? "bg-primary text-white"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {s.charAt(0) + s.slice(1).toLowerCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Meetings Grid / Empty State */}
        {isLoading ? (
          <div className="p-16 flex flex-col items-center justify-center gap-3">
            <Loader2 className="w-8 h-8 text-primary animate-spin" />
            <p className="text-sm text-slate-400">Loading your meetings...</p>
          </div>
        ) : filteredMeetings.length === 0 ? (
          <Card className="p-12 text-center flex flex-col items-center justify-center">
            <div className="w-14 h-14 rounded-2xl bg-surface-50 border border-surface-border flex items-center justify-center text-slate-400 mb-4">
              <FileAudio className="w-7 h-7 text-primary-light" />
            </div>
            <h3 className="text-lg font-semibold text-slate-200">No meetings found</h3>
            <p className="text-sm text-slate-400 max-w-sm mt-1 mb-6">
              {searchQuery || statusFilter !== "ALL"
                ? "No meetings matched your search filter criteria."
                : "Upload your first meeting recording to unlock automatic transcripts, action items, and conversational RAG."}
            </p>
            <Button
              onClick={() => setIsModalOpen(true)}
              leftIcon={<Plus className="w-4 h-4" />}
            >
              Upload First Meeting
            </Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredMeetings.map((meeting) => (
              <MeetingCard
                key={meeting.id}
                meeting={meeting}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </div>

      {/* New Meeting Modal */}
      <NewMeetingModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onMeetingCreated={(newMeeting) => {
          setMeetings((prev) => [newMeeting, ...prev]);
        }}
      />
    </AppShell>
  );
}
