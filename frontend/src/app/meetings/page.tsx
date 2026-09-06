"use client";

import React, { useEffect, useState } from "react";
import { FolderOpen, Loader2, Plus, Search } from "lucide-react";
import { api } from "@/lib/api/client";
import { Meeting, MeetingListResponse } from "@/lib/types";
import { AppShell } from "@/components/layout/AppShell";
import { MeetingCard } from "@/components/meetings/MeetingCard";
import { NewMeetingModal } from "@/components/meetings/NewMeetingModal";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export default function MeetingsPage() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fetchMeetings = async () => {
    setIsLoading(true);
    try {
      const res = await api.get<MeetingListResponse>("/meetings", {
        page,
        page_size: 12,
        status: statusFilter !== "ALL" ? statusFilter : undefined,
        q: searchQuery || undefined,
      });
      setMeetings(res.items);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error("Failed to load meetings", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMeetings();
  }, [page, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchMeetings();
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/meetings/${id}`);
      setMeetings((prev) => prev.filter((m) => m.id !== id));
    } catch (err) {
      console.error("Failed to delete meeting", err);
    }
  };

  return (
    <AppShell onNewMeetingClick={() => setIsModalOpen(true)}>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-100">Meetings Repository</h1>
            <p className="text-sm text-slate-400 mt-1">
              Browse, search, and manage all your processed audio sessions.
            </p>
          </div>

          <Button
            onClick={() => setIsModalOpen(true)}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            Upload Recording
          </Button>
        </div>

        {/* Search & Filter Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <form onSubmit={handleSearchSubmit} className="relative w-full sm:w-96">
            <Search className="absolute left-3 top-3 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search meetings by keyword..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-surface-100 border border-surface-border text-slate-200 text-sm rounded-lg pl-9 pr-4 py-2 focus:outline-none focus:border-primary"
            />
          </form>

          <div className="flex items-center gap-1.5 self-start sm:self-auto bg-surface-100 p-1 border border-surface-border rounded-lg">
            {["ALL", "COMPLETED", "PROCESSING", "FAILED"].map((s) => (
              <button
                key={s}
                onClick={() => {
                  setStatusFilter(s);
                  setPage(1);
                }}
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

        {/* Content Grid */}
        {isLoading ? (
          <div className="p-16 flex flex-col items-center justify-center gap-3">
            <Loader2 className="w-8 h-8 text-primary animate-spin" />
            <p className="text-sm text-slate-400">Fetching meetings...</p>
          </div>
        ) : meetings.length === 0 ? (
          <Card className="p-12 text-center flex flex-col items-center justify-center">
            <FolderOpen className="w-12 h-12 text-slate-500 mb-3" />
            <h3 className="text-base font-semibold text-slate-200">No meetings found</h3>
            <p className="text-sm text-slate-400 mt-1 max-w-sm">
              Try adjusting your search terms or upload a new meeting recording.
            </p>
          </Card>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {meetings.map((meeting) => (
                <MeetingCard
                  key={meeting.id}
                  meeting={meeting}
                  onDelete={handleDelete}
                />
              ))}
            </div>

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 pt-6">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <span className="text-xs text-slate-400 font-mono px-3">
                  Page {page} of {totalPages}
                </span>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            )}
          </>
        )}
      </div>

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
