"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  FileAudio,
  FileText,
  ListTodo,
  Loader2,
  Play,
  Search as SearchIcon,
  Sparkles,
  Tag,
} from "lucide-react";
import { api } from "@/lib/api/client";
import { formatSecondsToTimestamp } from "@/lib/utils/formatters";
import { AppShell } from "@/components/layout/AppShell";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";

interface SearchResultItem {
  meeting_id: string;
  meeting_title: string;
  match_type: "transcript" | "action_item" | "decision" | "topic" | "title";
  snippet: string;
  timestamp?: number | null;
}

interface SearchResponse {
  query: string;
  results: SearchResultItem[];
  total_matches: number;
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [totalMatches, setTotalMatches] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setHasSearched(true);
    try {
      const res = await api.get<SearchResponse>("/meetings/search", { q: query.trim() });
      setResults(res.results || []);
      setTotalMatches(res.total_matches || 0);
    } catch (err) {
      console.error("Search failed", err);
    } finally {
      setIsLoading(false);
    }
  };

  const getMatchBadge = (type: SearchResultItem["match_type"]) => {
    switch (type) {
      case "transcript":
        return (
          <Badge variant="purple" className="gap-1">
            <FileText className="w-3 h-3" />
            Transcript
          </Badge>
        );
      case "action_item":
        return (
          <Badge variant="success" className="gap-1">
            <ListTodo className="w-3 h-3" />
            Action Item
          </Badge>
        );
      case "decision":
        return (
          <Badge variant="default" className="gap-1">
            <CheckCircle2 className="w-3 h-3" />
            Decision
          </Badge>
        );
      case "topic":
        return (
          <Badge variant="warning" className="gap-1">
            <Tag className="w-3 h-3" />
            Topic
          </Badge>
        );
      default:
        return <Badge variant="outline">Meeting</Badge>;
    }
  };

  return (
    <AppShell>
      <div className="space-y-6 max-w-4xl mx-auto">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Global Knowledge Search</h1>
          <p className="text-sm text-slate-400 mt-1">
            Instant full-text and semantic search across all your recorded meetings, transcripts,
            decisions, and action items.
          </p>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="relative flex items-center">
          <SearchIcon className="absolute left-4 w-5 h-5 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search keywords, e.g., pricing, pgvector, launch, Alice, deadlines..."
            className="w-full bg-surface-100 border border-surface-border text-slate-100 placeholder-slate-500 text-base rounded-xl pl-12 pr-28 py-3.5 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary shadow-lg shadow-black/20"
          />
          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="absolute right-2.5 px-4 py-2 bg-primary hover:bg-primary-hover disabled:opacity-40 text-white rounded-lg text-sm font-medium transition-all"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Search"}
          </button>
        </form>

        {/* Results Stream */}
        {isLoading ? (
          <div className="p-16 flex flex-col items-center justify-center gap-3">
            <Loader2 className="w-8 h-8 text-primary animate-spin" />
            <p className="text-sm text-slate-400">Searching meeting transcripts...</p>
          </div>
        ) : hasSearched && results.length === 0 ? (
          <Card className="p-12 text-center flex flex-col items-center justify-center space-y-2">
            <SearchIcon className="w-10 h-10 text-slate-600 mb-2" />
            <h3 className="text-base font-semibold text-slate-200">No matches found</h3>
            <p className="text-sm text-slate-400 max-w-sm">
              We couldn&apos;t find any meetings, transcripts, or action items matching &ldquo;{query}&rdquo;.
            </p>
          </Card>
        ) : (
          results.length > 0 && (
            <div className="space-y-4">
              <p className="text-xs font-mono text-slate-400">
                Found {totalMatches} {totalMatches === 1 ? "match" : "matches"} for &ldquo;{query}&rdquo;
              </p>

              <div className="space-y-3">
                {results.map((res, idx) => (
                  <Link
                    key={idx}
                    href={`/meetings/${res.meeting_id}`}
                    className="block group"
                  >
                    <Card className="p-4 hover:border-primary/40 hover:bg-surface-100/90 transition-all space-y-2">
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          {getMatchBadge(res.match_type)}
                          <span className="text-xs font-semibold text-slate-300 group-hover:text-primary-light transition-colors">
                            {res.meeting_title}
                          </span>
                        </div>

                        {res.timestamp !== null && res.timestamp !== undefined && (
                          <span className="flex items-center gap-1 text-[11px] font-mono text-slate-400 bg-surface-50 px-2 py-0.5 rounded border border-surface-border">
                            <Play className="w-2.5 h-2.5" />
                            {formatSecondsToTimestamp(res.timestamp)}
                          </span>
                        )}
                      </div>

                      <p className="text-sm text-slate-200 leading-relaxed font-normal">
                        {res.snippet}
                      </p>
                    </Card>
                  </Link>
                ))}
              </div>
            </div>
          )
        )}
      </div>
    </AppShell>
  );
}
