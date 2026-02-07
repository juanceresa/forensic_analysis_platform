'use client';

import { useMemo, useEffect, useState, useRef, useCallback } from 'react';
import StickySpine from './StickySpine';
import ScrollEventNode, { type ScrollEventData } from './ScrollEventNode';
import ScrollGap, { type ScrollGapData } from './ScrollGap';

type TimelineItem =
  | { type: 'event'; data: ScrollEventData; sortYear: number }
  | { type: 'gap'; data: ScrollGapData; sortYear: number };

interface ScrollTimelineProps {
  events: ScrollEventData[];
  gaps: ScrollGapData[];
  caseId: string;
}

export default function ScrollTimeline({ events, gaps, caseId }: ScrollTimelineProps) {
  const contentRef = useRef<HTMLDivElement>(null);
  const [activeYear, setActiveYear] = useState<number | null>(null);

  const items: TimelineItem[] = useMemo(() => {
    const all: TimelineItem[] = [
      ...events.map(e => ({ type: 'event' as const, data: e, sortYear: e.year })),
      ...gaps.map(g => ({ type: 'gap' as const, data: g, sortYear: g.startYear + 0.5 })),
    ];
    all.sort((a, b) => a.sortYear - b.sortYear);
    return all;
  }, [events, gaps]);

  // Track which year label is closest to viewport center
  const handleScroll = useCallback(() => {
    if (!contentRef.current) return;
    const viewportCenter = window.innerHeight / 2;
    const labels = contentRef.current.querySelectorAll<HTMLElement>('[data-spine-year]');
    let closest: number | null = null;
    let closestDist = Infinity;
    labels.forEach(el => {
      const rect = el.getBoundingClientRect();
      const dist = Math.abs(rect.top + rect.height / 2 - viewportCenter);
      if (dist < closestDist) {
        closestDist = dist;
        closest = parseInt(el.getAttribute('data-spine-year')!, 10);
      }
    });
    setActiveYear(closest);
  }, []);

  useEffect(() => {
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  if (items.length === 0) {
    return (
      <div className="min-h-[40vh] flex items-center justify-center">
        <p className="text-slate-500 font-mono text-sm">No timeline events available</p>
      </div>
    );
  }

  // Build rendered items, inserting year markers at year boundaries
  const rendered: React.ReactNode[] = [];
  let lastYear: number | null = null;

  for (const item of items) {
    const year = item.type === 'event' ? item.data.year : item.data.startYear;
    const isNewYear = year !== lastYear;
    lastYear = year;

    const node = item.type === 'gap'
      ? <ScrollGap gap={item.data} />
      : <ScrollEventNode event={item.data} caseId={caseId} />;

    if (isNewYear) {
      // Wrap the first item of each year so we can position a year label on the spine
      rendered.push(
        <div key={item.data.id} className="relative">
          {/* Year label on the spine line — positioned near top of the event */}
          <div
            data-spine-year={year}
            data-active={year === activeYear}
            className="spine-year-marker absolute left-[1.52rem] -translate-x-1/2 top-4 font-mono text-[9px] tabular-nums text-slate-600 -rotate-90 origin-center whitespace-nowrap pointer-events-none select-none z-20"
          >
            {year}
          </div>
          {node}
        </div>
      );
    } else {
      rendered.push(
        <div key={item.data.id}>{node}</div>
      );
    }
  }

  return (
    <section className="relative">
      {/* Sticky animated line overlay */}
      <div className="absolute left-0 top-0 bottom-0">
        <StickySpine />
      </div>

      {/* Continuous vertical line behind events */}
      <div className="absolute left-[1.52rem] top-0 bottom-0 w-px bg-gradient-to-b from-transparent via-slate-700/40 to-transparent" />

      {/* Event/Gap sequence with inline year markers */}
      <div ref={contentRef}>
        {rendered}
      </div>
    </section>
  );
}
