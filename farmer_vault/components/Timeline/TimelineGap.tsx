'use client';

import { useRef, useEffect, useState } from 'react';

export interface TimelineGapData {
  id: string;
  startYear: number;
  endYear: number;
  duration: number;
  contextHint: string;
}

interface TimelineGapProps {
  gap: TimelineGapData;
  index: number;
}

export default function TimelineGap({ gap, index }: TimelineGapProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setTimeout(() => setVisible(true), index * 60);
          observer.disconnect();
        }
      },
      { threshold: 0.1 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [index]);

  return (
    <div
      ref={ref}
      className="relative pl-10 py-4 transition-all duration-300"
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(12px)',
      }}
    >
      {/* Dashed spine segment */}
      <div className="absolute left-0 top-0 bottom-0 w-px border-l border-dashed border-amber-500/20" />

      {/* Amber pulsing dot */}
      <div className="absolute left-0 top-1/2 w-2.5 h-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-amber-500/60 pulse-amber" />

      <div className="era-revolutionary rounded px-3 py-2">
        <p className="font-mono text-sm tabular-nums text-amber-400/70">
          {gap.startYear} — {gap.endYear}
        </p>
        <p className="text-slate-500 text-xs italic mt-0.5">
          {gap.duration} years &middot; No documents available
        </p>
        <p className="text-amber-400/50 text-xs mt-0.5">
          {gap.contextHint}
        </p>
      </div>
    </div>
  );
}
