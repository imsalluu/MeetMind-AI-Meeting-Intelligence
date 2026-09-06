"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  AlertTriangle,
  ArrowLeft,
  BarChart2,
  Brain,
  Calendar,
  CheckCircle2,
  Clock,
  Download,
  FileAudio,
  FileText,
  HelpCircle,
  ListTodo,
  Loader2,
  MessageSquare,
  Sparkles,
  Tag,
  Trash2,
} from "lucide-react";
import { api } from "@/lib/api/client";
import {
  ActionItem,
  Decision,
  Meeting,
  MeetingInsightsOverview,
  MeetingSummary,
  Topic,
  TranscriptSegment,
} from "@/lib/types";
import { formatDate, formatSecondsToTimestamp } from "@/lib/utils/formatters";
import { AppShell } from "@/components/layout/AppShell";
import { ProcessingStatusBanner } from "@/components/meetings/ProcessingStatusBanner";
import { AudioPlayer } from "@/components/transcript/AudioPlayer";
import { TranscriptViewer } from "@/components/transcript/TranscriptViewer";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { TabItem, Tabs } from "@/components/ui/Tabs";

export default function MeetingDetailPage() {
  const params = useParams();
  const meetingId = params.id as string;
  const router = useRouter();

  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [segments, setSegments] = useState<TranscriptSegment[]>([]);
  const [insights, setInsights] = useState<MeetingInsightsOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  // Audio player sync state
  const [currentTime, setCurrentTime] = useState(0);
  const [highlightedTimestamp, setHighlightedTimestamp] = useState<number | null>(null);

  const fetchMeetingData = async () => {
    try {
      // 1. Fetch meeting metadata
      const m = await api.get<Meeting>(`/meetings/${meetingId}`);
      setMeeting(m);

      // 2. Fetch transcript if available
      try {
        const t = await api.get<{ segments: TranscriptSegment[] }>(
          `/meetings/${meetingId}/transcript`
        );
        setSegments(t.segments || []);
      } catch {}

      // 3. Fetch insights if available
      try {
        const ins = await api.get<MeetingInsightsOverview>(
          `/meetings/${meetingId}/insights`
        );
        setInsights(ins);
      } catch {}
    } catch (err) {
      console.error("Failed to load meeting details", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (meetingId) {
      fetchMeetingData();
    }
  }, [meetingId]);

  const handleSeek = (seconds: number) => {
    setCurrentTime(seconds);
    setHighlightedTimestamp(seconds);
  };

  const handleToggleAction = async (actionId: string, currentCompleted: boolean) => {
    try {
      const updated = await api.patch<ActionItem>(
        `/meetings/${meetingId}/actions/${actionId}`,
        { is_completed: !currentCompleted }
      );
      if (insights) {
        setInsights({
          ...insights,
          action_items: insights.action_items.map((a) =>
            a.id === actionId ? updated : a
          ),
        });
      }
    } catch (err) {
      console.error("Failed to toggle action item", err);
    }
  };

  const tabs: TabItem[] = [
    { id: "overview", label: "Executive Overview", icon: <Sparkles className="w-4 h-4" /> },
    {
      id: "transcript",
      label: "Transcript",
      icon: <FileText className="w-4 h-4" />,
      badge: segments.length,
    },
    {
      id: "actions",
      label: "Action Items",
      icon: <ListTodo className="w-4 h-4" />,
      badge: insights?.action_items.length,
    },
    {
      id: "decisions",
      label: "Decisions",
      icon: <CheckCircle2 className="w-4 h-4" />,
      badge: insights?.decisions.length,
    },
    {
      id: "insights",
      label: "Topics & Risks",
      icon: <Brain className="w-4 h-4" />,
    },
    {
      id: "chat",
      label: "Ask Meeting (RAG)",
      icon: <MessageSquare className="w-4 h-4" />,
    },
  ];

  if (isLoading) {
    return (
      <AppShell>
        <div className="min-h-[60vh] flex flex-col items-center justify-center gap-3">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
          <p className="text-sm text-slate-400">Loading meeting intelligence...</p>
        </div>
      </AppShell>
    );
  }

  if (!meeting) {
    return (
      <AppShell>
        <div className="p-12 text-center space-y-4">
          <h2 className="text-lg font-semibold text-slate-200">Meeting Not Found</h2>
          <p className="text-sm text-slate-400">
            The requested meeting does not exist or you do not have permission to view it.
          </p>
          <Link href="/dashboard">
            <Button variant="outline">Back to Dashboard</Button>
          </Link>
        </div>
      </AppShell>
    );
  }

  const audioUrl = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/meetings/${meeting.id}/audio`;

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Navigation Breadcrumb & Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link
              href="/dashboard"
              className="p-2 text-slate-400 hover:text-white hover:bg-surface-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-2xl font-bold text-slate-100">{meeting.title}</h1>
                <Badge
                  variant={meeting.status === "COMPLETED" ? "success" : "purple"}
                >
                  {meeting.status}
                </Badge>
              </div>
              <p className="text-xs text-slate-400 mt-1 flex items-center gap-3">
                <span className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5" />
                  {formatDate(meeting.created_at)}
                </span>
                {meeting.duration_seconds !== null && (
                  <span className="flex items-center gap-1 font-mono">
                    <Clock className="w-3.5 h-3.5" />
                    {formatSecondsToTimestamp(meeting.duration_seconds)}
                  </span>
                )}
                {meeting.audio_filename && (
                  <span className="flex items-center gap-1">
                    <FileAudio className="w-3.5 h-3.5" />
                    {meeting.audio_filename}
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>

        {/* Live Processing Status Banner */}
        <ProcessingStatusBanner
          meetingId={meeting.id}
          initialStatus={meeting.status}
          initialStage={meeting.processing_stage}
          errorMessage={meeting.error_message}
          onCompleted={() => {
            fetchMeetingData();
          }}
        />

        {/* Synchronized Audio Player */}
        {meeting.audio_path && (
          <AudioPlayer
            audioUrl={audioUrl}
            currentTime={currentTime}
            onTimeUpdate={(t) => setCurrentTime(t)}
            onSeek={handleSeek}
          />
        )}

        {/* Intelligence Tabs Navigation */}
        <Tabs
          tabs={tabs}
          activeTab={activeTab}
          onChange={(tabId) => setActiveTab(tabId)}
        />

        {/* Tab Content Panels */}
        <div className="pt-2">
          {/* 1. Overview Tab */}
          {activeTab === "overview" && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                {/* Executive Summary */}
                <Card glow className="p-6 space-y-4">
                  <div className="flex items-center gap-2 text-primary-light font-semibold text-sm">
                    <Sparkles className="w-4 h-4" />
                    <span>Executive Summary</span>
                  </div>
                  <p className="text-sm text-slate-200 leading-relaxed">
                    {insights?.summary?.executive_summary ||
                      meeting.description ||
                      "Processing meeting intelligence. Please wait..."}
                  </p>
                </Card>

                {/* Key Discussion Points */}
                {insights?.summary?.key_points && insights.summary.key_points.length > 0 && (
                  <Card className="p-6 space-y-3">
                    <h3 className="text-sm font-semibold text-slate-200">
                      Key Discussion Points
                    </h3>
                    <ul className="space-y-2">
                      {insights.summary.key_points.map((point, i) => (
                        <li key={i} className="flex items-start gap-2.5 text-sm text-slate-300">
                          <span className="w-1.5 h-1.5 rounded-full bg-primary mt-2 shrink-0" />
                          <span>{point}</span>
                        </li>
                      ))}
                    </ul>
                  </Card>
                )}

                {/* Detailed Summary */}
                {insights?.summary?.detailed_summary && (
                  <Card className="p-6 space-y-3">
                    <h3 className="text-sm font-semibold text-slate-200">Detailed Breakdown</h3>
                    <div className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed space-y-2">
                      {insights.summary.detailed_summary}
                    </div>
                  </Card>
                )}
              </div>

              {/* Sidebar Insights Preview */}
              <div className="space-y-6">
                {/* Action Items Mini Widget */}
                <Card className="p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                      <ListTodo className="w-4 h-4 text-emerald-400" />
                      Action Items ({insights?.action_items?.length || 0})
                    </h4>
                    <button
                      onClick={() => setActiveTab("actions")}
                      className="text-xs text-primary-light hover:underline"
                    >
                      View all
                    </button>
                  </div>
                  <div className="space-y-2">
                    {insights?.action_items?.slice(0, 3).map((item) => (
                      <div
                        key={item.id}
                        className="p-2.5 bg-surface-200/50 rounded-lg border border-surface-border/50 text-xs space-y-1"
                      >
                        <p className="text-slate-200 font-medium">{item.task}</p>
                        <div className="flex items-center justify-between text-[11px] text-slate-400">
                          <span>Assignee: {item.assignee}</span>
                          <span className="font-mono text-primary-light">
                            {item.deadline}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>

                {/* Decisions Mini Widget */}
                <Card className="p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-primary" />
                      Decisions ({insights?.decisions?.length || 0})
                    </h4>
                    <button
                      onClick={() => setActiveTab("decisions")}
                      className="text-xs text-primary-light hover:underline"
                    >
                      View all
                    </button>
                  </div>
                  <div className="space-y-2">
                    {insights?.decisions?.slice(0, 3).map((dec) => (
                      <div
                        key={dec.id}
                        className="p-2.5 bg-surface-200/50 rounded-lg border border-surface-border/50 text-xs text-slate-300"
                      >
                        {dec.decision}
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            </div>
          )}

          {/* 2. Interactive Transcript Tab */}
          {activeTab === "transcript" && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <Card className="p-6">
                  <TranscriptViewer
                    segments={segments}
                    currentTime={currentTime}
                    onSeekTo={handleSeek}
                    highlightedTimestamp={highlightedTimestamp}
                  />
                </Card>
              </div>
              <div>
                <Card className="p-6 space-y-4">
                  <h3 className="text-sm font-semibold text-slate-200">Transcript Stats</h3>
                  <div className="space-y-3 text-xs">
                    <div className="flex justify-between py-1.5 border-b border-surface-border/50">
                      <span className="text-slate-400">Total Segments:</span>
                      <span className="font-mono font-medium text-slate-200">
                        {segments.length}
                      </span>
                    </div>
                    <div className="flex justify-between py-1.5 border-b border-surface-border/50">
                      <span className="text-slate-400">Total Duration:</span>
                      <span className="font-mono font-medium text-slate-200">
                        {formatSecondsToTimestamp(meeting.duration_seconds)}
                      </span>
                    </div>
                    <div className="flex justify-between py-1.5">
                      <span className="text-slate-400">Speech-to-Text Model:</span>
                      <span className="font-medium text-primary-light">
                        OpenAI Whisper-1
                      </span>
                    </div>
                  </div>
                </Card>
              </div>
            </div>
          )}

          {/* 3. Action Items Tab */}
          {activeTab === "actions" && (
            <Card className="p-6 space-y-4">
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <ListTodo className="w-5 h-5 text-emerald-400" />
                Action Items ({insights?.action_items?.length || 0})
              </h3>
              {(!insights?.action_items || insights.action_items.length === 0) ? (
                <p className="text-sm text-slate-400 py-8 text-center">
                  No action items extracted from this meeting.
                </p>
              ) : (
                <div className="space-y-3">
                  {insights.action_items.map((item) => (
                    <div
                      key={item.id}
                      className={`p-4 rounded-xl border flex items-start justify-between gap-4 transition-all ${
                        item.is_completed
                          ? "bg-surface-200/30 border-surface-border/30 opacity-60"
                          : "bg-surface-100 border-surface-border hover:border-slate-600"
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <input
                          type="checkbox"
                          checked={item.is_completed}
                          onChange={() => handleToggleAction(item.id, item.is_completed)}
                          className="mt-1 w-4 h-4 rounded border-surface-border text-primary focus:ring-primary accent-primary cursor-pointer"
                        />
                        <div className="space-y-1">
                          <p
                            className={`text-sm font-medium ${
                              item.is_completed
                                ? "line-through text-slate-400"
                                : "text-slate-100"
                            }`}
                          >
                            {item.task}
                          </p>
                          <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                            <span>
                              Assignee:{" "}
                              <strong className="text-slate-300">{item.assignee}</strong>
                            </span>
                            <span>
                              Deadline:{" "}
                              <strong className="text-primary-light font-mono">
                                {item.deadline}
                              </strong>
                            </span>
                          </div>
                        </div>
                      </div>

                      {item.source_timestamp !== null && item.source_timestamp !== undefined && (
                        <button
                          onClick={() => handleSeek(item.source_timestamp!)}
                          className="shrink-0 px-2.5 py-1 rounded-lg bg-surface-50 text-[11px] font-mono text-slate-400 hover:text-white hover:bg-primary transition-colors"
                        >
                          Jump: {formatSecondsToTimestamp(item.source_timestamp)}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </Card>
          )}

          {/* 4. Decisions Tab */}
          {activeTab === "decisions" && (
            <Card className="p-6 space-y-4">
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-primary" />
                Key Decisions Agreed Upon ({insights?.decisions?.length || 0})
              </h3>
              {(!insights?.decisions || insights.decisions.length === 0) ? (
                <p className="text-sm text-slate-400 py-8 text-center">
                  No explicit decisions were recorded in this meeting.
                </p>
              ) : (
                <div className="space-y-3">
                  {insights.decisions.map((dec) => (
                    <div
                      key={dec.id}
                      className="p-4 bg-surface-100 border border-surface-border rounded-xl flex items-start justify-between gap-4"
                    >
                      <div className="space-y-1">
                        <p className="text-sm font-medium text-slate-100 leading-relaxed">
                          {dec.decision}
                        </p>
                      </div>

                      {dec.source_timestamp !== null && dec.source_timestamp !== undefined && (
                        <button
                          onClick={() => handleSeek(dec.source_timestamp!)}
                          className="shrink-0 px-2.5 py-1 rounded-lg bg-surface-50 text-[11px] font-mono text-slate-400 hover:text-white hover:bg-primary transition-colors"
                        >
                          Jump: {formatSecondsToTimestamp(dec.source_timestamp)}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </Card>
          )}

          {/* 5. Topics & Risks Tab */}
          {activeTab === "insights" && (
            <div className="space-y-6">
              {/* Topics */}
              <Card className="p-6 space-y-4">
                <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                  <Tag className="w-5 h-5 text-accent-cyan" />
                  Discussed Topics
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {insights?.topics?.map((top) => (
                    <div
                      key={top.id}
                      className="p-4 bg-surface-200/50 border border-surface-border rounded-xl space-y-1.5"
                    >
                      <h4 className="text-sm font-semibold text-slate-200">{top.topic}</h4>
                      <p className="text-xs text-slate-400 leading-relaxed">{top.summary}</p>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Risks & Questions */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className="p-6 space-y-3">
                  <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    Risks & Blockers
                  </h3>
                  {(!insights?.summary?.risks || insights.summary.risks.length === 0) ? (
                    <p className="text-xs text-slate-500">No risks identified.</p>
                  ) : (
                    <ul className="space-y-2">
                      {insights.summary.risks.map((risk, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                          <span>{risk}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </Card>

                <Card className="p-6 space-y-3">
                  <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                    <HelpCircle className="w-4 h-4 text-accent-violet" />
                    Open Follow-up Questions
                  </h3>
                  {(!insights?.summary?.questions || insights.summary.questions.length === 0) ? (
                    <p className="text-xs text-slate-500">No open questions.</p>
                  ) : (
                    <ul className="space-y-2">
                      {insights.summary.questions.map((q, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                          <span className="w-1.5 h-1.5 rounded-full bg-accent-violet mt-1.5 shrink-0" />
                          <span>{q}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </Card>
              </div>
            </div>
          )}

          {/* 6. Ask Meeting (RAG) Tab will be mounted in Phase 13 */}
          {activeTab === "chat" && (
            <div id="ask-meeting-container">
              {/* Dynamic import / mounting of AskMeetingChat component */}
              <AskMeetingChatPlaceholder
                meetingId={meeting.id}
                onJumpToTimestamp={handleSeek}
              />
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}

// Placeholder for Phase 13 full AskMeetingChat component
function AskMeetingChatPlaceholder({
  meetingId,
  onJumpToTimestamp,
}: {
  meetingId: string;
  onJumpToTimestamp: (seconds: number) => void;
}) {
  return (
    <div id="ask-meeting-chat-slot">
      {/* Will be replaced with complete AskMeetingChat component in Phase 13 */}
    </div>
  );
}
