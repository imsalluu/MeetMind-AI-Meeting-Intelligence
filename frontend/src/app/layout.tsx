import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AuthProvider } from "@/lib/auth/auth-context";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "MeetMind — AI Meeting Intelligence & Transcript RAG",
  description:
    "Enterprise-grade AI Meeting Intelligence platform with speech-to-text, executive summaries, timestamped action items, and conversational transcript RAG.",
  keywords: ["AI Meeting Assistant", "Whisper STT", "pgvector RAG", "Transcript Intelligence", "FastAPI"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans bg-background text-slate-100 antialiased min-h-screen`}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
