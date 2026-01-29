'use client';

import Link from 'next/link';
import { VerificationBadge } from '@/components/shared';

interface DocumentInfo {
  id: string;
  filename: string;
  date: string | null;
}

interface EntityInfo {
  id: string;
  name: string;
  entity_type: string;
  verification: {
    tier: string;
    confidence: number;
  };
}

interface HighlightedEvent {
  event_type: string;
  summary: string;
  date: string | null;
  parties_involved: string[];
}

interface TimePeriodData {
  id: string;
  dateRange: string;
  startYear: number;
  endYear: number;
  title: string;
  documents: DocumentInfo[];
  entities: EntityInfo[];
  documentCount: number;
  entityCount: number;
  narrative: string | null;
  highlightedEvents: HighlightedEvent[];
}

interface TimelinePeriodProps {
  period: TimePeriodData;
  caseId: string;
  index: number;
  defaultOpen?: boolean;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'Unknown date';
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

export function TimelinePeriod({ period, caseId, index, defaultOpen = false }: TimelinePeriodProps) {
  return (
    <div
      className="relative pl-8 pb-8 animate-fade-in-up"
      style={{ animationDelay: `${index * 0.1}s` } as React.CSSProperties}
    >
      {/* Timeline spine */}
      <div className="absolute left-0 top-0 bottom-0 w-px bg-slate-800" />

      {/* Timeline dot */}
      <div className="absolute left-0 top-2 w-2 h-2 -translate-x-1/2 rounded-full bg-slate-600 border-2 border-slate-800" />

      <details className="group" open={defaultOpen}>
        <summary
          className="flex items-start gap-4 p-4 bg-slate-900 border border-slate-800 rounded
                     cursor-pointer hover:bg-slate-800/50 transition-colors
                     group-open:rounded-b-none list-none
                     focus-visible:ring-2 focus-visible:ring-blue-500"
        >
          {/* Date range badge */}
          <div className="shrink-0">
            <time
              dateTime={`${period.startYear}`}
              className="inline-block px-3 py-1 bg-slate-800 rounded text-sm font-mono tabular-nums text-slate-300"
            >
              {period.dateRange}
            </time>
          </div>

          {/* Title and metadata */}
          <div className="flex-1 min-w-0">
            <h2 className="text-lg font-mono text-slate-100">{period.title}</h2>
            <div className="mt-1 text-sm text-slate-500">
              {period.documentCount} document{period.documentCount !== 1 ? 's' : ''} &middot;{' '}
              {period.entityCount} entit{period.entityCount !== 1 ? 'ies' : 'y'}
            </div>
          </div>

          {/* Expand/collapse indicator */}
          <div className="shrink-0 text-slate-400">
            <svg
              className="w-5 h-5 transition-transform group-open:rotate-180"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </summary>

        <div className="p-6 bg-slate-900 border border-t-0 border-slate-800 rounded-b space-y-6">
          {/* AI Narrative */}
          {period.narrative && (
            <section>
              <div className="prose prose-invert prose-sm max-w-none text-slate-300 leading-relaxed">
                {period.narrative.split('\n\n').map((paragraph, i) => (
                  <p key={i} className="mb-3 last:mb-0">{paragraph}</p>
                ))}
              </div>
              {period.highlightedEvents.length > 0 && (
                <div className="mt-4 space-y-2">
                  {period.highlightedEvents.map((event, i) => (
                    <div
                      key={i}
                      className={`flex items-center gap-2 px-3 py-2 rounded text-sm ${
                        event.event_type === 'CONFISCATED'
                          ? 'bg-red-500/10 border border-red-500/20 text-red-300'
                          : event.event_type === 'SOLD'
                            ? 'bg-blue-500/10 border border-blue-500/20 text-blue-300'
                            : 'bg-amber-500/10 border border-amber-500/20 text-amber-300'
                      }`}
                    >
                      <span className="font-mono text-xs uppercase tracking-wider opacity-70">
                        {event.event_type}
                      </span>
                      <span>{event.summary}</span>
                      {event.date && (
                        <span className="ml-auto text-xs opacity-60">{event.date}</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
              <hr className="border-slate-800 mt-4" />
            </section>
          )}

          {/* Supporting Documents */}
          <section>
            <h3 className="text-sm font-mono uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              Supporting Documents ({period.documentCount})
            </h3>

            <div className="space-y-2">
              {period.documents.map((doc) => (
                <Link
                  key={doc.id}
                  href={`/case/${caseId}/document/${encodeURIComponent(doc.id)}`}
                  className="flex items-center gap-3 p-3 bg-slate-800/50 rounded
                             hover:bg-slate-800 transition-colors
                             focus-visible:ring-2 focus-visible:ring-blue-500"
                >
                  <svg className="w-5 h-5 text-slate-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                    />
                  </svg>
                  <span className="flex-1 min-w-0 font-mono text-sm text-slate-300 truncate">
                    {doc.filename}
                  </span>
                  <time dateTime={doc.date || ''} className="text-xs text-slate-500 tabular-nums shrink-0">
                    {formatDate(doc.date)}
                  </time>
                </Link>
              ))}
            </div>
          </section>

          {/* Key Entities */}
          {period.entities.length > 0 && (
            <section>
              <h3 className="text-sm font-mono uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                  />
                </svg>
                Key Entities ({period.entityCount})
              </h3>

              <div className="flex flex-wrap gap-2">
                {period.entities.map((entity) => (
                  <Link
                    key={entity.id}
                    href={`/case/${caseId}/entity/${encodeURIComponent(entity.id)}`}
                    className="inline-flex items-center gap-2 px-3 py-1.5 bg-slate-800/50 rounded
                               hover:bg-slate-800 transition-colors
                               focus-visible:ring-2 focus-visible:ring-blue-500"
                  >
                    <span className="text-sm text-slate-300">{entity.name}</span>
                    <VerificationBadge tier={entity.verification.tier as any} size="tiny" />
                  </Link>
                ))}
              </div>
            </section>
          )}
        </div>
      </details>
    </div>
  );
}
