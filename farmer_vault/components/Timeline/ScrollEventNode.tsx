'use client';

import { useRef, useEffect, useState } from 'react';
import Link from 'next/link';

export interface ScrollEventData {
  id: string;
  year: number;
  date: string | null;
  eventType: 'CONFISCATED' | 'SOLD' | 'INHERITED' | 'FILED';
  summary: string;
  parties: string[];
  documentIds: string[];
  entityIds: string[];
  periodId: string;
  narrative?: string | null;
}

interface ScrollEventNodeProps {
  event: ScrollEventData;
  caseId: string;
}

const EVENT_BADGE_CLASS: Record<string, string> = {
  CONFISCATED: 'bg-red-500/10 text-red-400 border-red-500/20',
  INHERITED: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  SOLD: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  FILED: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
};

const EVENT_DOT_COLOR: Record<string, string> = {
  CONFISCATED: 'bg-red-500',
  INHERITED: 'bg-blue-400',
  SOLD: 'bg-emerald-400',
  FILED: 'bg-slate-500',
};

export default function ScrollEventNode({ event, caseId }: ScrollEventNodeProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [revealLevel, setRevealLevel] = useState(0);
  const maxLevel = useRef(0);

  // Check reduced motion preference
  const prefersReducedMotion = useRef(false);
  useEffect(() => {
    prefersReducedMotion.current = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion.current) {
      setRevealLevel(3);
      maxLevel.current = 3;
    }
  }, []);

  useEffect(() => {
    if (prefersReducedMotion.current) return;
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          let level = 0;
          if (entry.intersectionRatio >= 0.6) level = 3;
          else if (entry.intersectionRatio >= 0.3) level = 2;
          else if (entry.intersectionRatio > 0) level = 1;

          // Only increase, never decrease (once revealed, stays revealed)
          if (level > maxLevel.current) {
            maxLevel.current = level;
            setRevealLevel(level);
          }
        }
      },
      { threshold: [0, 0.3, 0.6, 1.0] }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const isConfiscated = event.eventType === 'CONFISCATED';
  const dotColor = EVENT_DOT_COLOR[event.eventType] || 'bg-slate-500';
  const badgeClass = EVENT_BADGE_CLASS[event.eventType] || EVENT_BADGE_CLASS.FILED;

  // Extract first 2 sentences from narrative or summary for bullet snapshot
  const bulletText = event.narrative || event.summary;
  const sentences = bulletText.match(/[^.!?]+[.!?]+/g) || [bulletText];
  const snippet = sentences.slice(0, 2).join(' ').trim();

  return (
    <div
      ref={ref}
      className={`relative min-h-[60vh] flex items-center pl-16 pr-8 ${
        isConfiscated ? 'era-expropriation' : ''
      }`}
    >
      {/* Spine dot */}
      <div className="absolute left-6 top-1/2 -translate-y-1/2">
        <div
          className={`w-3 h-3 rounded-full ${dotColor} ring-[3px] ring-slate-950 ${
            isConfiscated ? 'pulse-red' : ''
          }`}
        />
      </div>

      {/* Content */}
      <div className="max-w-2xl w-full space-y-3 py-12">
        {/* Level 1: Year + Badge */}
        {revealLevel >= 1 && (
          <div className="scroll-reveal-year flex items-baseline gap-3">
            <time className="text-3xl font-mono tabular-nums text-slate-200 tracking-tight">
              {event.year}
            </time>
            <span className={`inline-block px-2.5 py-0.5 text-[10px] font-mono uppercase tracking-wider border rounded ${badgeClass}`}>
              {event.eventType}
            </span>
            {event.date && (
              <span className="text-slate-600 font-mono text-xs">
                {event.date}
              </span>
            )}
          </div>
        )}

        {/* Level 2: Summary + Bullets */}
        {revealLevel >= 2 && (
          <div className="scroll-reveal-summary space-y-2">
            <p className="text-slate-300 text-[15px] leading-relaxed">
              {event.summary}
            </p>
            {snippet !== event.summary && (
              <p className="text-slate-500 text-sm italic leading-relaxed border-l-2 border-slate-800 pl-3">
                {snippet}
              </p>
            )}
          </div>
        )}

        {/* Level 3: Full detail + Explore link */}
        {revealLevel >= 3 && (
          <div className="scroll-reveal-full space-y-2 pt-1">
            <p className="text-slate-600 font-mono text-xs">
              {event.documentIds.length} document{event.documentIds.length !== 1 ? 's' : ''}
              {event.parties.length > 0 && (
                <> &middot; {event.parties.slice(0, 3).join(', ')}{event.parties.length > 3 ? '...' : ''}</>
              )}
            </p>
            <Link
              href={`/case/${caseId}/narrative/event/${event.id}`}
              className="inline-flex items-center gap-1.5 text-xs font-mono text-slate-500 hover:text-slate-300 transition-colors group"
            >
              Explore this event
              <svg className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
