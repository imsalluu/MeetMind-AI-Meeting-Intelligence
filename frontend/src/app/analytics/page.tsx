"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  BarChart3,
  Calendar,
  CheckCircle2,
  Clock,
  FolderOpen,
  ListTodo,
  Loader2,
  PieChart,
  Sparkles,
  Tag,
  TrendingUp,
} from "lucide-react";
import { api } from "@/lib/api/client";
import { formatDate, formatSecondsToTimestamp } from "@/lib/utils/formatters";
import { AppShell } from "@/components/layout/AppShell";
import { Badge } from "@/components/ui/Badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

interface AnalyticsData {
  total_meetings: number;
  total_duration_hours: number;
  avg_meeting_duration_minutes: number;
  total_action_items: number;
  pending_action_items: number;
  completed_action_items: number;
  action_item_completion_rate: number;
  total_decisions: number;
  total_topics: number;
  status_distribution: { status: string; count: number }[];
  top_topics: { topic: string; count: number }[];
  recent_meetings: any[];
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const res = await api.get<AnalyticsData>("/analytics/overview");
        setData(res);
      } catch (err) {
        console.error("Failed to load analytics", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  return (
    <AppShell>
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Meeting Intelligence Analytics</h1>
          <p className="text-sm text-slate-400 mt-1">
            Aggregate metrics, action item completion tracking, and topic distributions across all your meetings.
          </p>
        </div>

        {isLoading ? (
          <div className="p-16 flex flex-col items-center justify-center gap-3">
            <Loader2 className="w-8 h-8 text-primary animate-spin" />
            <p className="text-sm text-slate-400">Computing analytics metrics...</p>
          </div>
        ) : !data || data.total_meetings === 0 ? (
          <Card className="p-12 text-center flex flex-col items-center justify-center space-y-3">
            <BarChart3 className="w-12 h-12 text-slate-500 mb-2" />
            <h3 className="text-base font-semibold text-slate-200">No Analytics Data Yet</h3>
            <p className="text-sm text-slate-400 max-w-sm">
              Upload meeting recordings to generate intelligence insights, metrics, and topic trends.
            </p>
            <Link href="/dashboard" className="pt-3">
              <Badge variant="purple" className="px-4 py-1.5 text-xs cursor-pointer">
                Go to Dashboard →
              </Badge>
            </Link>
          </Card>
        ) : (
          <>
            {/* Top Metrics Row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
              <Card glow className="p-5 flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-xs font-medium text-slate-400">Total Meetings</p>
                  <p className="text-2xl font-bold text-slate-100">{data.total_meetings}</p>
                  <p className="text-[11px] text-slate-500">Avg {data.avg_meeting_duration_minutes}m per meeting</p>
                </div>
                <div className="w-11 h-11 rounded-xl bg-primary/15 border border-primary/30 flex items-center justify-center text-primary-light">
                  <FolderOpen className="w-5 h-5" />
                </div>
              </Card>

              <Card glow className="p-5 flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-xs font-medium text-slate-400">Hours Recorded</p>
                  <p className="text-2xl font-bold text-slate-100">{data.total_duration_hours}h</p>
                  <p className="text-[11px] text-emerald-400 flex items-center gap-1">
                    <Sparkles className="w-3 h-3" />
                    Transcribed with Whisper
                  </p>
                </div>
                <div className="w-11 h-11 rounded-xl bg-accent-violet/15 border border-accent-violet/30 flex items-center justify-center text-accent-violet">
                  <Clock className="w-5 h-5" />
                </div>
              </Card>

              <Card glow className="p-5 flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-xs font-medium text-slate-400">Action Completion</p>
                  <p className="text-2xl font-bold text-slate-100">{data.action_item_completion_rate}%</p>
                  <p className="text-[11px] text-slate-400">
                    {data.completed_action_items} of {data.total_action_items} completed
                  </p>
                </div>
                <div className="w-11 h-11 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
              </Card>

              <Card glow className="p-5 flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-xs font-medium text-slate-400">Decisions Recorded</p>
                  <p className="text-2xl font-bold text-slate-100">{data.total_decisions}</p>
                  <p className="text-[11px] text-accent-cyan flex items-center gap-1">
                    <TrendingUp className="w-3 h-3" />
                    Indexed in pgvector
                  </p>
                </div>
                <div className="w-11 h-11 rounded-xl bg-accent-cyan/15 border border-accent-cyan/30 flex items-center justify-center text-accent-cyan">
                  <Sparkles className="w-5 h-5" />
                </div>
              </Card>
            </div>

            {/* Visual Progress & Distributions */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Action Item Status Card */}
              <Card className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                    <ListTodo className="w-4 h-4 text-emerald-400" />
                    Action Items Overview
                  </h3>
                  <Badge variant="success">{data.action_item_completion_rate}% Done</Badge>
                </div>

                <div className="space-y-2">
                  <div className="w-full h-3 bg-surface-200 rounded-full overflow-hidden flex">
                    <div
                      className="bg-emerald-500 transition-all duration-500"
                      style={{ width: `${data.action_item_completion_rate}%` }}
                    />
                    <div
                      className="bg-amber-500/60 transition-all duration-500"
                      style={{ width: `${100 - data.action_item_completion_rate}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-slate-400 pt-1">
                    <span className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-emerald-500" />
                      Completed: {data.completed_action_items}
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-amber-500" />
                      Pending: {data.pending_action_items}
                    </span>
                  </div>
                </div>
              </Card>

              {/* Status Distribution */}
              <Card className="p-6 space-y-4">
                <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                  <PieChart className="w-4 h-4 text-primary-light" />
                  Meeting Pipeline Status
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {data.status_distribution.map((st) => (
                    <div
                      key={st.status}
                      className="p-3 bg-surface-200/50 border border-surface-border rounded-lg text-center space-y-1"
                    >
                      <p className="text-xs text-slate-400 uppercase font-mono">{st.status}</p>
                      <p className="text-lg font-bold text-slate-100">{st.count}</p>
                    </div>
                  ))}
                </div>
              </Card>
            </div>

            {/* Top Discussed Topics */}
            {data.top_topics.length > 0 && (
              <Card className="p-6 space-y-4">
                <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                  <Tag className="w-4 h-4 text-accent-violet" />
                  Top Discussed Topics Across Meetings
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                  {data.top_topics.map((item, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 bg-surface-200/50 border border-surface-border rounded-xl flex items-center justify-between"
                    >
                      <span className="text-xs font-semibold text-slate-200 truncate mr-2">
                        {item.topic}
                      </span>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-primary/20 text-primary-light border border-primary/30">
                        {item.count} {item.count === 1 ? "meeting" : "meetings"}
                      </span>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Recent Activity Table */}
            <Card className="p-6 space-y-4">
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-primary-light" />
                Recent Meeting Intelligence Sessions
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-surface-200/60 text-slate-400 uppercase font-mono border-b border-surface-border">
                    <tr>
                      <th className="p-3">Title</th>
                      <th className="p-3">Status</th>
                      <th className="p-3">Duration</th>
                      <th className="p-3">Created</th>
                      <th className="p-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-border/50">
                    {data.recent_meetings.map((m) => (
                      <tr key={m.id} className="hover:bg-surface-100/50 transition-colors">
                        <td className="p-3 font-medium text-slate-200 max-w-[200px] truncate">
                          {m.title}
                        </td>
                        <td className="p-3">
                          <Badge variant={m.status === "COMPLETED" ? "success" : "purple"}>
                            {m.status}
                          </Badge>
                        </td>
                        <td className="p-3 font-mono">
                          {formatSecondsToTimestamp(m.duration_seconds)}
                        </td>
                        <td className="p-3 text-slate-400">{formatDate(m.created_at)}</td>
                        <td className="p-3 text-right">
                          <Link
                            href={`/meetings/${m.id}`}
                            className="text-primary-light hover:underline font-medium"
                          >
                            Open →
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </>
        )}
      </div>
    </AppShell>
  );
}
