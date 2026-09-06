import Link from "next/link";
import {
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  FileAudio,
  ListTodo,
  MessageSquare,
  Search,
  Shield,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background text-slate-100 flex flex-col justify-between">
      {/* Navbar */}
      <header className="w-full h-20 border-b border-surface-border px-8 flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-primary to-accent-violet flex items-center justify-center shadow-lg shadow-primary/30">
            <BrainCircuit className="w-6 h-6 text-white" />
          </div>
          <div>
            <span className="font-bold text-xl tracking-tight text-white">MeetMind</span>
            <span className="ml-2 text-xs font-semibold bg-primary/20 text-primary-light px-2 py-0.5 rounded-full border border-primary/30">
              Enterprise AI
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Link href="/login">
            <Button variant="ghost" size="sm">
              Sign In
            </Button>
          </Link>
          <Link href="/register">
            <Button size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
              Get Started Free
            </Button>
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-7xl mx-auto px-8 py-16 flex flex-col items-center text-center">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary-light text-xs font-medium mb-8">
          <Sparkles className="w-3.5 h-3.5 text-primary-light" />
          <span>Next-Generation Transcript-Grounded RAG & STT</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight max-w-4xl text-slate-100 leading-tight">
          Turn Meeting Recordings into{" "}
          <span className="gradient-brand-text">Actionable Intelligence</span>
        </h1>

        <p className="mt-6 text-lg text-slate-400 max-w-2xl leading-relaxed">
          Upload any meeting audio to generate speaker-segmented transcripts, executive summaries,
          action items with deadlines, timestamped decisions, and conversational RAG answers backed
          by zero hallucinations.
        </p>

        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link href="/register">
            <Button size="lg" rightIcon={<ArrowRight className="w-5 h-5" />}>
              Start Analyzing Meetings
            </Button>
          </Link>
          <Link href="/dashboard">
            <Button variant="secondary" size="lg">
              Live Dashboard Demo
            </Button>
          </Link>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-24 text-left w-full">
          <Card glow className="p-6 space-y-4">
            <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center text-primary-light">
              <FileAudio className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-semibold text-slate-100">Whisper Speech-to-Text</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              High-accuracy transcription with exact millisecond segment timestamps, audio waveform playback synchronization, and speaker labeling.
            </p>
          </Card>

          <Card glow className="p-6 space-y-4">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400">
              <ListTodo className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-semibold text-slate-100">Structured Intelligence</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Automated extraction of executive summaries, assignees with deadlines, decisions with source timestamp links, and categorized topics.
            </p>
          </Card>

          <Card glow className="p-6 space-y-4">
            <div className="w-10 h-10 rounded-lg bg-accent-violet/20 flex items-center justify-center text-accent-violet">
              <MessageSquare className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-semibold text-slate-100">pgvector Transcript RAG</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Ask this meeting anything. Grounded answers citing exact timestamps with clickable citations that jump playback directly to that second.
            </p>
          </Card>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-surface-border py-8 px-8 text-center text-xs text-slate-500">
        <p>© 2026 MeetMind — AI Meeting Intelligence. Built with FastAPI, PostgreSQL, pgvector & Next.js.</p>
      </footer>
    </div>
  );
}
