"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  BrainCircuit,
  FolderOpen,
  LayoutDashboard,
  Search,
  Settings,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";

const navigationItems = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Meetings",
    href: "/meetings",
    icon: FolderOpen,
  },
  {
    name: "Analytics",
    href: "/analytics",
    icon: BarChart3,
  },
  {
    name: "Search",
    href: "/search",
    icon: Search,
  },
  {
    name: "Settings",
    href: "/settings",
    icon: Settings,
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 h-screen bg-surface-200 border-r border-surface-border flex flex-col justify-between p-4 fixed left-0 top-0 z-50">
      {/* Brand Logo */}
      <div className="space-y-6">
        <Link href="/dashboard" className="flex items-center gap-3 px-2 py-1 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-primary to-accent-violet flex items-center justify-center shadow-lg shadow-primary/25 border border-primary-light/30 group-hover:scale-105 transition-transform">
            <BrainCircuit className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-base text-white tracking-tight">MeetMind</span>
              <span className="text-[10px] font-semibold bg-primary/20 text-primary-light px-1.5 py-0.5 rounded border border-primary/30">
                AI
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium">Meeting Intelligence</p>
          </div>
        </Link>

        {/* Navigation links */}
        <nav className="space-y-1">
          {navigationItems.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/dashboard" && pathname?.startsWith(item.href));
            const Icon = item.icon;

            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150",
                  isActive
                    ? "bg-primary/10 text-primary-light font-semibold border border-primary/20 shadow-sm"
                    : "text-slate-400 hover:text-slate-100 hover:bg-surface-100"
                )}
              >
                <Icon
                  className={cn(
                    "w-4 h-4 transition-colors",
                    isActive ? "text-primary-light" : "text-slate-400"
                  )}
                />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* RAG Engine Status Card */}
      <div className="p-3.5 bg-surface-100/90 border border-surface-border rounded-xl space-y-2">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs font-semibold text-slate-200">pgvector RAG Engine</span>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          OpenAI Whisper STT & 1536-dim hybrid retrieval active.
        </p>
      </div>
    </aside>
  );
}
