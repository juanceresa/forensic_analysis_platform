'use client';

import { useRef, useEffect, useState } from 'react';
import EventDetail from './EventDetail';

export interface TimelineEventData {
  id: string;
  year: number;
  date: string | null;
  eventType: 'CONFISCATED' | 'SOLD' | 'INHERITED' | 'FILED';
  summary: string;
  parties: string[];
  documentIds: string[];
  entityIds: string[];
  periodId: string;
}

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

interface EventNodeProps {
  event: TimelineEventData;
  period: PeriodData | undefined;
  caseId: string;
  isExpanded: boolean;
  onToggle: () => void;
  index: number;
}

const EVENT_DOT_COLOR: Record<string, string> = {
  CONFISCATED: 'bg-red-500',
  INHERITED: 'bg-blue-400',
  SOLD: 'bg-emerald-400',
  FILED: 'bg-slate-500',
};

const EVENT_BADGE_CLASS: Record<string, string> = {
  CONFISCATED: 'bg-red-500/10 text-red-400 border-red-500/20',
  INHERITED: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  SOLD: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  FILED: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
};

export default function EventNode({ event, period, caseId, isExpanded, onToggle, index }: EventNodeProps) {
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

  const dotColor = EVENT_DOT_COLOR[event.eventType] || 'bg-slate-500';
  const badgeClass = EVENT_BADGE_CLASS[event.eventType] || EVENT_BADGE_CLASS.FILED;
  const isPulsing = event.eventType === 'CONFISCATED';

  return (
    <div
      ref={ref}
      className="relative pl-10 transition-all duration-300"
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(12px)',
      }}
    >
      {/* Dot on spine */}
      <div
        className={`absolute left-0 top-3 w-3 h-3 -translate-x-1/2 rounded-full ${dotColor} ring-[3px] ring-slate-950 ${
          isPulsing ? 'pulse-red' : ''
        }`}
      />

      {/* Event row */}
      <button
        onClick={onToggle}
        className="w-full text-left group cursor-pointer py-2 focus-visible:ring-2 focus-visible:ring-blue-500 rounded"
      >
        <div className="flex items-baseline gap-3">
          <time className="text-lg font-mono tabular-nums text-slate-200 shrink-0">
            {event.year}
          </time>
          <span className={`inline-block px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider border rounded ${badgeClass}`}>
            {event.eventType}
          </span>
        </div>
        <p className="text-slate-300 text-sm mt-0.5 truncate group-hover:text-slate-200 transition-colors">
          {event.summary}
        </p>
        <p className="text-slate-500 font-mono text-xs mt-0.5">
          {event.documentIds.length} document{event.documentIds.length !== 1 ? 's' : ''}
          {event.entityIds.length > 0 && <> &middot; {event.entityIds.length} entit{event.entityIds.length !== 1 ? 'ies' : 'y'}</>}
        </p>
      </button>

      {/* Expanded detail */}
      {isExpanded && period && (
        <div className="animate-expand mt-1 mb-2">
          <EventDetail event={event} period={period} caseId={caseId} />
        </div>
      )}
    </div>
  );
}
