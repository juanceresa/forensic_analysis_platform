'use client';

import { useRef, useEffect, useState } from 'react';

export interface ScrollGapData {
  id: string;
  startYear: number;
  endYear: number;
  duration: number;
  contextHint: string;
}

interface ScrollGapProps {
  gap: ScrollGapData;
}

export default function ScrollGap({ gap }: ScrollGapProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setVisible(true);
      return;
    }
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.2 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className="relative min-h-[20vh] flex items-center pl-16 pr-8"
      style={{ opacity: visible ? 1 : 0, transition: 'opacity 0.5s ease-out' }}
    >
      {/* Dashed spine segment */}
      <div className="absolute left-[1.52rem] top-0 bottom-0 w-px border-l border-dashed border-amber-500/20" />

      {/* Amber pulsing dot */}
      <div className="absolute left-6 top-1/2 -translate-y-1/2">
        <div className="w-2.5 h-2.5 rounded-full bg-amber-500/60 pulse-amber" />
      </div>

      <div className="era-revolutionary rounded px-4 py-3 max-w-md">
        <p className="font-mono text-sm tabular-nums text-amber-400/70">
          {gap.startYear} — {gap.endYear}
        </p>
        <p className="text-slate-500 text-xs italic mt-0.5">
          {gap.duration} year{gap.duration !== 1 ? 's' : ''} &middot; No documents available
        </p>
        <p className="text-amber-400/50 text-xs mt-1">
          {gap.contextHint}
        </p>
      </div>
    </div>
  );
}
