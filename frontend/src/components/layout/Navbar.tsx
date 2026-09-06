"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Bell,
  ChevronDown,
  LogOut,
  Plus,
  Search,
  Sparkles,
  User as UserIcon,
} from "lucide-react";
import { useAuth } from "@/lib/auth/auth-context";
import { Button } from "@/lib/../components/ui/Button";

interface NavbarProps {
  onNewMeetingClick?: () => void;
}

export function Navbar({ onNewMeetingClick }: NavbarProps) {
  const { user, logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const router = useRouter();

  return (
    <header className="sticky top-0 z-40 w-full h-16 bg-surface-200/80 backdrop-blur-md border-b border-surface-border px-6 flex items-center justify-between">
      {/* Search Bar / Quick Action */}
      <div className="flex items-center gap-4 flex-1 max-w-md">
        <div
          onClick={() => router.push("/search")}
          className="w-full flex items-center gap-2.5 px-3 py-1.5 bg-surface-100 border border-surface-border rounded-lg text-sm text-slate-400 cursor-pointer hover:border-slate-600 transition-colors"
        >
          <Search className="w-4 h-4 text-slate-500" />
          <span>Search meetings, transcripts, decisions...</span>
          <kbd className="ml-auto text-[10px] bg-surface-50 border border-surface-border px-1.5 py-0.5 rounded text-slate-500 font-mono">
            Ctrl+K
          </kbd>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3">
        {onNewMeetingClick && (
          <Button
            size="sm"
            onClick={onNewMeetingClick}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            New Meeting
          </Button>
        )}

        {/* User Dropdown */}
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2.5 p-1.5 rounded-lg hover:bg-surface-100 transition-colors border border-transparent hover:border-surface-border"
          >
            <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center text-primary-light font-medium text-sm">
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : "U"}
            </div>
            <span className="text-sm font-medium text-slate-200 hidden sm:inline-block max-w-[120px] truncate">
              {user?.full_name || user?.email?.split("@")[0] || "User"}
            </span>
            <ChevronDown className="w-4 h-4 text-slate-500" />
          </button>

          {dropdownOpen && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setDropdownOpen(false)}
              />
              <div className="absolute right-0 mt-2 w-56 bg-surface-100 border border-surface-border rounded-xl shadow-xl z-20 py-1.5 animate-fade-in">
                <div className="px-4 py-2 border-b border-surface-border/50">
                  <p className="text-xs font-medium text-slate-400">Signed in as</p>
                  <p className="text-sm font-semibold text-slate-200 truncate">{user?.email}</p>
                </div>

                <Link
                  href="/settings"
                  onClick={() => setDropdownOpen(false)}
                  className="flex items-center gap-2.5 px-4 py-2 text-sm text-slate-300 hover:bg-surface-50 hover:text-white transition-colors"
                >
                  <UserIcon className="w-4 h-4 text-slate-500" />
                  Account Settings
                </Link>

                <button
                  onClick={() => {
                    setDropdownOpen(false);
                    logout();
                  }}
                  className="w-full flex items-center gap-2.5 px-4 py-2 text-sm text-rose-400 hover:bg-rose-500/10 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
