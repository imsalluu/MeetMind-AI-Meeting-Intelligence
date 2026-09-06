"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  ArrowUp,
  Brain,
  CheckCircle2,
  Clock,
  HelpCircle,
  Loader2,
  Play,
  Quote,
  Send,
  ShieldCheck,
  Sparkles,
  User,
} from "lucide-react";
import { api } from "@/lib/api/client";
import { AskMeetingResponse, ChatMessage, ChatSession, SourceCitation } from "@/lib/types";
import { formatSecondsToTimestamp } from "@/lib/utils/formatters";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

interface AskMeetingChatProps {
  meetingId: string;
  onJumpToTimestamp: (seconds: number) => void;
}

const SUGGESTED_QUESTIONS = [
  "What decisions were made in this meeting?",
  "What are the action items and who owns them?",
  "What deadlines or target dates were mentioned?",
  "What problems or risks were discussed?",
  "What was said about architecture and technology?",
];

export function AskMeetingChat({ meetingId, onJumpToTimestamp }: AskMeetingChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load prior chat sessions for this meeting if available
  useEffect(() => {
    const loadSession = async () => {
      try {
        const sessions = await api.get<ChatSession[]>(`/meetings/${meetingId}/chat/sessions`);
        if (sessions && sessions.length > 0) {
          const latest = sessions[0];
          setSessionId(latest.id);
          const fullSession = await api.get<ChatSession>(
            `/meetings/${meetingId}/chat/sessions/${latest.id}`
          );
          setMessages(fullSession.messages || []);
        }
      } catch (err) {
        console.error("Failed to load chat session", err);
      }
    };
    loadSession();
  }, [meetingId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSendMessage = async (queryText?: string) => {
    const question = queryText || inputQuery;
    if (!question.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: `temp_user_${Date.now()}`,
      session_id: sessionId || "temp_session",
      role: "user",
      content: question.trim(),
      sources: [],
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputQuery("");
    setIsLoading(true);

    try {
      const response = await api.post<AskMeetingResponse>(`/meetings/${meetingId}/ask`, {
        question: question.trim(),
        session_id: sessionId || undefined,
      });

      setSessionId(response.session_id);

      const assistantMessage: ChatMessage = {
        id: response.message_id,
        session_id: response.session_id,
        role: "assistant",
        content: response.answer,
        sources: response.sources,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: ChatMessage = {
        id: `err_${Date.now()}`,
        session_id: sessionId || "temp_session",
        role: "assistant",
        content: `Error: ${err.message || "Failed to retrieve grounded answer."}`,
        sources: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="flex flex-col h-[700px] overflow-hidden border-surface-border">
      {/* Header with Guardrail Indicator */}
      <div className="p-4 bg-surface-200/90 border-b border-surface-border flex items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-primary/20 border border-primary/40 flex items-center justify-center text-primary-light">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              Ask This Meeting
              <span className="text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-1.5 py-0.5 rounded">
                Grounded RAG
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">
              Answers are synthesized strictly from indexed meeting transcripts.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 text-[11px] text-slate-400 hidden sm:flex">
          <ShieldCheck className="w-3.5 h-3.5 text-primary-light" />
          <span>Zero Hallucination Policy</span>
        </div>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-6">
            <div className="w-12 h-12 rounded-2xl bg-surface-50 border border-surface-border flex items-center justify-center text-slate-400">
              <Brain className="w-6 h-6 text-primary-light" />
            </div>
            <div>
              <h4 className="text-base font-semibold text-slate-200">
                Ask anything about this meeting
              </h4>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                MeetMind retrieves relevant semantic vector chunks and provides exact timestamp
                citations that synchronize with the audio player.
              </p>
            </div>

            {/* Suggested Question Pills */}
            <div className="space-y-2 w-full text-left">
              <p className="text-[11px] font-medium text-slate-400">Suggested questions:</p>
              <div className="flex flex-col gap-1.5">
                {SUGGESTED_QUESTIONS.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(q)}
                    className="w-full text-left p-2.5 rounded-lg bg-surface-100 border border-surface-border/70 text-xs text-slate-300 hover:bg-surface-hover hover:border-primary/40 hover:text-white transition-all text-ellipsis overflow-hidden"
                  >
                    👉 {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg) => {
            const isUser = msg.role === "user";

            return (
              <div
                key={msg.id}
                className={`flex gap-3 animate-fade-in ${
                  isUser ? "justify-end" : "justify-start"
                }`}
              >
                {!isUser && (
                  <div className="w-7 h-7 rounded-lg bg-primary/20 border border-primary/40 flex items-center justify-center text-primary-light shrink-0 mt-1">
                    <Sparkles className="w-3.5 h-3.5" />
                  </div>
                )}

                <div
                  className={`max-w-[80%] rounded-2xl p-4 space-y-3 ${
                    isUser
                      ? "bg-primary text-white rounded-br-none shadow-md shadow-primary/15"
                      : "bg-surface-100 border border-surface-border text-slate-200 rounded-bl-none"
                  }`}
                >
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>

                  {/* Grounded Source Citations */}
                  {!isUser && msg.sources && msg.sources.length > 0 && (
                    <div className="pt-2 border-t border-surface-border/60 space-y-2">
                      <p className="text-[11px] font-semibold text-slate-400 flex items-center gap-1.5">
                        <Quote className="w-3 h-3 text-primary-light" />
                        Source Citations:
                      </p>
                      <div className="grid grid-cols-1 gap-2">
                        {msg.sources.map((source, sIdx) => (
                          <div
                            key={sIdx}
                            onClick={() => onJumpToTimestamp(source.start_time)}
                            className="p-2.5 bg-surface-200/70 border border-surface-border/70 hover:border-primary/50 hover:bg-surface-200 rounded-lg cursor-pointer transition-all group"
                          >
                            <div className="flex items-center justify-between gap-2 mb-1">
                              <span className="text-[11px] font-semibold text-slate-300">
                                {source.speaker || "Speaker"}
                              </span>
                              <div className="flex items-center gap-1 text-[10px] font-mono text-primary-light group-hover:text-white px-1.5 py-0.5 bg-primary/10 rounded group-hover:bg-primary transition-colors">
                                <Play className="w-2.5 h-2.5" />
                                <span>{source.formatted_timestamp}</span>
                              </div>
                            </div>
                            <p className="text-xs text-slate-400 italic line-clamp-2">
                              &ldquo;{source.text}&rdquo;
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {isUser && (
                  <div className="w-7 h-7 rounded-lg bg-surface-50 border border-surface-border flex items-center justify-center text-slate-300 shrink-0 mt-1">
                    <User className="w-3.5 h-3.5" />
                  </div>
                )}
              </div>
            );
          })
        )}

        {isLoading && (
          <div className="flex gap-3 animate-fade-in">
            <div className="w-7 h-7 rounded-lg bg-primary/20 border border-primary/40 flex items-center justify-center text-primary-light shrink-0">
              <Sparkles className="w-3.5 h-3.5" />
            </div>
            <div className="p-4 bg-surface-100 border border-surface-border rounded-2xl rounded-bl-none flex items-center gap-2.5 text-xs text-slate-400">
              <Loader2 className="w-4 h-4 text-primary animate-spin" />
              <span>Retrieving pgvector chunks & grounding response...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="p-4 bg-surface-200/90 border-t border-surface-border">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="relative flex items-center"
        >
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Ask anything about decisions, action items, deadlines..."
            disabled={isLoading}
            className="w-full bg-surface-100 border border-surface-border text-slate-100 placeholder-slate-500 text-sm rounded-xl pl-4 pr-12 py-3 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!inputQuery.trim() || isLoading}
            className="absolute right-2 p-2 bg-primary hover:bg-primary-hover disabled:opacity-40 disabled:hover:bg-primary text-white rounded-lg transition-all"
            title="Send query"
          >
            <ArrowUp className="w-4 h-4" />
          </button>
        </form>
      </div>
    </Card>
  );
}
