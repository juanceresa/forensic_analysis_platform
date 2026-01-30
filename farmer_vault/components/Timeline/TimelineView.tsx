'use client';

import { useState, useMemo } from 'react';
import EventNode, { type TimelineEventData } from './EventNode';
import TimelineGap, { type TimelineGapData } from './TimelineGap';
import TimelineSpine from './TimelineSpine';

interface PeriodData {
  id: string;
  narrative: string | null;
  inlineEntities?: Array<{
    name: string;
    entityId: string;
    entityType: string;
    verificationTier: string;
  }>;
  entities: Array<{
    id: string;
    name: string;
    entity_type: string;
    verification: { tier: string; confidence: number };
  }>;
  documents: Array<{
    id: string;
    filename: string;
    date: string | null;
  }>;
}

type TimelineItem =
  | { type: 'event'; data: TimelineEventData; sortYear: number }
  | { type: 'gap'; data: TimelineGapData; sortYear: number };

interface TimelineViewProps {
  events: TimelineEventData[];
  gaps: TimelineGapData[];
  periods: PeriodData[];
  caseId: string;
}

export default function TimelineView({ events, gaps, periods, caseId }: TimelineViewProps) {
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null);

  const periodMap = useMemo(() => {
    const map = new Map<string, PeriodData>();
    for (const p of periods) {
      map.set(p.id, p);
    }
    return map;
  }, [periods]);

  const items: TimelineItem[] = useMemo(() => {
    const all: TimelineItem[] = [
      ...events.map(e => ({ type: 'event' as const, data: e, sortYear: e.year })),
      ...gaps.map(g => ({ type: 'gap' as const, data: g, sortYear: g.startYear + 0.5 })),
    ];
    all.sort((a, b) => a.sortYear - b.sortYear);
    return all;
  }, [events, gaps]);

  if (items.length === 0) {
    return (
      <div className="p-8 bg-slate-900 border border-slate-800 border-dashed rounded text-center">
        <p className="text-slate-500 font-mono text-sm">No timeline events available</p>
      </div>
    );
  }

  return (
    <div className="relative pl-4">
      <TimelineSpine />
      {items.map((item, i) => {
        if (item.type === 'gap') {
          return <TimelineGap key={item.data.id} gap={item.data} index={i} />;
        }
        const event = item.data;
        return (
          <EventNode
            key={event.id}
            event={event}
            period={periodMap.get(event.periodId)}
            caseId={caseId}
            isExpanded={expandedEventId === event.id}
            onToggle={() =>
              setExpandedEventId(prev => (prev === event.id ? null : event.id))
            }
            index={i}
          />
        );
      })}
    </div>
  );
}
