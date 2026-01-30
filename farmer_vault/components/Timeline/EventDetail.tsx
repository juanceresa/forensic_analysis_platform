'use client';

import Link from 'next/link';
import { VerificationBadge } from '@/components/shared';
import type { TimelineEventData } from './EventNode';

const ENTITY_BORDER_COLOR: Record<string, string> = {
  PERSON: 'border-blue-400/50',
  ORGANIZATION: 'border-amber-400/50',
  PROPERTY: 'border-emerald-400/50',
  LOCATION: 'border-purple-400/50',
};

const EVENT_ACCENT: Record<string, string> = {
  CONFISCATED: 'border-l-red-500',
  INHERITED: 'border-l-blue-400',
  SOLD: 'border-l-emerald-400',
  FILED: 'border-l-slate-500',
};

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

interface EventDetailProps {
  event: TimelineEventData;
  period: PeriodData;
  caseId: string;
}

function renderNarrativeWithEntities(
  text: string,
  inlineEntities: PeriodData['inlineEntities'],
  caseId: string,
): React.ReactNode[] {
  if (!inlineEntities || inlineEntities.length === 0) {
    return [text];
  }

  const sorted = [...inlineEntities].sort((a, b) => b.name.length - a.name.length);
  const escaped = sorted.map(e => e.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const pattern = new RegExp(`(${escaped.join('|')})`, 'g');
  const entityMap = new Map(sorted.map(e => [e.name, e]));
  const parts = text.split(pattern);

  return parts.map((part, i) => {
    const entity = entityMap.get(part);
    if (entity) {
      const borderClass = ENTITY_BORDER_COLOR[entity.entityType] || 'border-slate-400/50';
      return (
        <Link
          key={`${entity.entityId}-${i}`}
          href={`/case/${caseId}/entity/${encodeURIComponent(entity.entityId)}`}
          className={`bg-slate-800/40 px-1 rounded border-b ${borderClass} hover:bg-slate-700/50 transition-colors`}
          title={`${entity.entityType} · ${entity.verificationTier}`}
        >
          {part}
        </Link>
      );
    }
    return part;
  });
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

export default function EventDetail({ event, period, caseId }: EventDetailProps) {
  const accent = EVENT_ACCENT[event.eventType] || 'border-l-slate-500';

  // First 2 paragraphs of narrative
  const narrativeParagraphs = period.narrative
    ? period.narrative.split('\n\n').slice(0, 2)
    : [];

  // Filter entities relevant to this event
  const relevantEntities = event.entityIds.length > 0
    ? period.entities.filter(e => event.entityIds.includes(e.id))
    : period.entities.slice(0, 6);

  // Filter documents relevant to this event
  const relevantDocs = event.documentIds.length > 0
    ? period.documents.filter(d => event.documentIds.includes(d.id))
    : period.documents;

  return (
    <div className={`vault-panel rounded border-l-2 ${accent} p-4 space-y-4`}>
      {/* Narrative excerpt */}
      {narrativeParagraphs.length > 0 && (
        <div className="dossier-prose">
          {narrativeParagraphs.map((p, i) => (
            <p key={i}>
              {renderNarrativeWithEntities(p, period.inlineEntities, caseId)}
            </p>
          ))}
        </div>
      )}

      {/* Entity chips */}
      {relevantEntities.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {relevantEntities.map(entity => {
            const borderClass = ENTITY_BORDER_COLOR[entity.entity_type] || 'border-slate-400/50';
            return (
              <Link
                key={entity.id}
                href={`/case/${caseId}/entity/${encodeURIComponent(entity.id)}`}
                className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/50 border ${borderClass} text-xs text-slate-300 hover:bg-slate-700/50 transition-colors`}
              >
                {entity.name}
                <VerificationBadge tier={entity.verification.tier as any} size="tiny" />
              </Link>
            );
          })}
        </div>
      )}

      {/* Document links */}
      {relevantDocs.length > 0 && (
        <div className="space-y-1">
          {relevantDocs.map(doc => (
            <Link
              key={doc.id}
              href={`/case/${caseId}/document/${encodeURIComponent(doc.id)}`}
              className="flex items-center gap-2 px-2 py-1 rounded text-xs hover:bg-slate-800/50 transition-colors"
            >
              <span className="text-slate-500 tabular-nums font-mono">{formatDate(doc.date)}</span>
              <span className="text-slate-400 truncate">{doc.filename}</span>
            </Link>
          ))}
        </div>
      )}

      {/* CTA */}
      <Link
        href={`/case/${caseId}/narrative/event/${event.id}`}
        className="inline-block text-xs text-slate-400 hover:text-slate-200 transition-colors"
      >
        Explore this event &rarr;
      </Link>
    </div>
  );
}
