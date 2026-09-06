"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  FastForward,
  Pause,
  Play,
  Rewind,
  Volume2,
  VolumeX,
} from "lucide-react";
import { formatSecondsToTimestamp } from "@/lib/utils/formatters";

interface AudioPlayerProps {
  audioUrl: string;
  currentTime: number;
  onTimeUpdate: (time: number) => void;
  onSeek: (time: number) => void;
}

export function AudioPlayer({
  audioUrl,
  currentTime,
  onTimeUpdate,
  onSeek,
}: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(1);

  // Sync external seek requests (e.g. from clicking transcript segment or RAG citation)
  useEffect(() => {
    if (audioRef.current && Math.abs(audioRef.current.currentTime - currentTime) > 0.5) {
      audioRef.current.currentTime = currentTime;
    }
  }, [currentTime]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().catch(() => {});
      setIsPlaying(true);
    }
  };

  const handleTimeUpdate = () => {
    if (!audioRef.current) return;
    onTimeUpdate(audioRef.current.currentTime);
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration || 0);
    }
  };

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newTime = parseFloat(e.target.value);
    onSeek(newTime);
    if (audioRef.current) {
      audioRef.current.currentTime = newTime;
    }
  };

  const handleSkip = (seconds: number) => {
    if (!audioRef.current) return;
    const newTime = Math.max(0, Math.min(duration, audioRef.current.currentTime + seconds));
    onSeek(newTime);
    audioRef.current.currentTime = newTime;
  };

  const cyclePlaybackRate = () => {
    const rates = [1, 1.25, 1.5, 2];
    const nextRate = rates[(rates.indexOf(playbackRate) + 1) % rates.length];
    setPlaybackRate(nextRate);
    if (audioRef.current) {
      audioRef.current.playbackRate = nextRate;
    }
  };

  const toggleMute = () => {
    if (!audioRef.current) return;
    const newMuted = !isMuted;
    setIsMuted(newMuted);
    audioRef.current.muted = newMuted;
  };

  const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="w-full bg-surface-100 border border-surface-border rounded-xl p-4 shadow-xl flex flex-col gap-3">
      <audio
        ref={audioRef}
        src={audioUrl}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={() => setIsPlaying(false)}
        preload="metadata"
      />

      {/* Progress Scrubber */}
      <div className="flex items-center gap-3">
        <span className="text-xs font-mono text-slate-400 min-w-[42px]">
          {formatSecondsToTimestamp(currentTime)}
        </span>

        <div className="relative flex-1 flex items-center group">
          <input
            type="range"
            min={0}
            max={duration || 100}
            step={0.1}
            value={currentTime}
            onChange={handleSliderChange}
            className="w-full h-1.5 bg-surface-50 rounded-lg appearance-none cursor-pointer accent-primary focus:outline-none"
          />
        </div>

        <span className="text-xs font-mono text-slate-500 min-w-[42px]">
          {formatSecondsToTimestamp(duration)}
        </span>
      </div>

      {/* Player Controls Bar */}
      <div className="flex items-center justify-between gap-4 pt-1">
        {/* Playback rate pill */}
        <button
          onClick={cyclePlaybackRate}
          className="px-2.5 py-1 text-xs font-mono font-medium rounded-lg bg-surface-50 text-slate-300 hover:text-white hover:bg-surface-hover transition-colors border border-surface-border"
          title="Playback speed"
        >
          {playbackRate}x
        </button>

        {/* Center transport buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleSkip(-10)}
            className="p-2 text-slate-400 hover:text-slate-100 hover:bg-surface-50 rounded-lg transition-colors"
            title="Rewind 10 seconds"
          >
            <Rewind className="w-4 h-4" />
          </button>

          <button
            onClick={togglePlay}
            className="w-10 h-10 rounded-full bg-primary hover:bg-primary-hover text-white flex items-center justify-center shadow-lg shadow-primary/30 transition-transform active:scale-95"
            title={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
          </button>

          <button
            onClick={() => handleSkip(10)}
            className="p-2 text-slate-400 hover:text-slate-100 hover:bg-surface-50 rounded-lg transition-colors"
            title="Forward 10 seconds"
          >
            <FastForward className="w-4 h-4" />
          </button>
        </div>

        {/* Volume control */}
        <div className="flex items-center gap-2">
          <button
            onClick={toggleMute}
            className="p-1.5 text-slate-400 hover:text-slate-100 transition-colors"
          >
            {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
          </button>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={isMuted ? 0 : volume}
            onChange={(e) => {
              const val = parseFloat(e.target.value);
              setVolume(val);
              setIsMuted(val === 0);
              if (audioRef.current) {
                audioRef.current.volume = val;
                audioRef.current.muted = val === 0;
              }
            }}
            className="w-16 h-1 bg-surface-50 rounded-lg appearance-none cursor-pointer accent-primary hidden sm:inline-block"
          />
        </div>
      </div>
    </div>
  );
}
