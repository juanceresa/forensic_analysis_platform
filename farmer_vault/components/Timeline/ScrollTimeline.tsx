'use client';

import { useMemo } from 'react';
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
  const items: TimelineItem[] = useMemo(() => {
    const all: TimelineItem[] = [
      ...events.map(e => ({ type: 'event' as const, data: e, sortYear: e.year })),
      ...gaps.map(g => ({ type: 'gap' as const, data: g, sortYear: g.startYear + 0.5 })),
    ];
    all.sort((a, b) => a.sortYear - b.sortYear);
    return all;
  }, [events, gaps]);

  const years = useMemo(() => {
    const unique = [...new Set(events.map(e => e.year))];
    unique.sort((a, b) => a - b);
    return unique;
  }, [events]);

  if (items.length === 0) {
    return (
      <div className="min-h-[40vh] flex items-center justify-center">
        <p className="text-slate-500 font-mono text-sm">No timeline events available</p>
      </div>
    );
  }

  return (
    <section className="relative">
      {/* Sticky spine on left */}
      <div className="absolute left-0 top-0 bottom-0">
        <StickySpine years={years} />
      </div>

      {/* Continuous vertical line behind events */}
      <div className="absolute left-[1.52rem] top-0 bottom-0 w-px bg-gradient-to-b from-transparent via-slate-700/40 to-transparent" />

      {/* Event/Gap sequence */}
      <div>
        {items.map((item) => {
          if (item.type === 'gap') {
            return <ScrollGap key={item.data.id} gap={item.data} />;
          }
          return (
            <ScrollEventNode
              key={item.data.id}
              event={item.data}
              caseId={caseId}
            />
          );
        })}
      </div>
    </section>
  );
}
