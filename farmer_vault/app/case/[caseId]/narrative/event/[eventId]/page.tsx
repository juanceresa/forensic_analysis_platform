import Link from 'next/link';
import { VerificationBadge } from '@/components/shared';
import { fetchServerApi } from '@/lib/server-api';

interface EventPageProps {
  params: Promise<{ caseId: string; eventId: string }>;
}

const ENTITY_BORDER_COLOR: Record<string, string> = {
  PERSON: 'border-blue-400/50',
  ORGANIZATION: 'border-amber-400/50',
  PROPERTY: 'border-emerald-400/50',
  LOCATION: 'border-purple-400/50',
};

const EVENT_TYPE_COLOR: Record<string, string> = {
  CONFISCATED: 'bg-red-500/10 text-red-400 border-red-500/20',
  INHERITED: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  SOLD: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  FILED: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
};

function renderNarrativeWithEntities(
  text: string,
  inlineEntities: Array<{ name: string; entityId: string; entityType: string; verificationTier: string }>,
  caseId: string,
): React.ReactNode[] {
  if (!inlineEntities || inlineEntities.length === 0) return [text];

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
      month: 'long',
      day: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

async function getTimeline(caseId: string) {
  const res = await fetchServerApi(`/api/cases/${caseId}/timeline`);
  if (!res.ok) throw new Error('Failed to fetch timeline');
  return res.json();
}

export default async function EventPage({ params }: EventPageProps) {
  const { caseId, eventId } = await params;

  try {
    const data = await getTimeline(caseId);
    const event = data.events?.find((e: any) => e.id === eventId);

    if (!event) {
      return (
        <div className="p-8">
          <div className="max-w-5xl mx-auto">
            <Link href={`/case/${caseId}/narrative`} className="text-sm text-slate-400 hover:text-slate-200 transition-colors">
              &larr; Back to timeline
            </Link>
            <div className="mt-8 p-8 bg-slate-900 border border-slate-800 rounded text-center">
              <p className="text-slate-500 font-mono text-sm">Event not found</p>
            </div>
          </div>
        </div>
      );
    }

    const period = data.periods?.find((p: any) => p.id === event.periodId);
    const badgeClass = EVENT_TYPE_COLOR[event.eventType] || EVENT_TYPE_COLOR.FILED;

    // All entities from the period for this event
    const entities = period?.entities || [];
    const documents = period?.documents || [];
    const inlineEntities = period?.inlineEntities || [];

    return (
      <div className="p-8">
        <div className="max-w-5xl mx-auto">
          {/* Back link */}
          <Link
            href={`/case/${caseId}/narrative`}
            className="inline-block text-sm text-slate-400 hover:text-slate-200 transition-colors mb-8"
          >
            &larr; Back to timeline
          </Link>

          {/* Year display */}
          <div className="mb-6">
            <time className="block text-5xl font-mono tabular-nums text-slate-100 tracking-tight">
              {event.year}
            </time>
            {event.date && (
              <p className="text-sm text-slate-500 mt-1 font-mono">{formatDate(event.date)}</p>
            )}
          </div>

          {/* Event type badge */}
          <span className={`inline-block px-3 py-1 text-xs font-mono uppercase tracking-wider border rounded mb-6 ${badgeClass}`}>
            {event.eventType}
          </span>

          {/* Summary */}
          <h1 className="text-2xl font-display tracking-tight text-slate-100 mb-2">
            {event.summary}
          </h1>

          {/* Parties */}
          {event.parties && event.parties.length > 0 && (
            <p className="text-sm text-slate-400 mb-6">
              Parties: {event.parties.join(', ')}
            </p>
          )}

          <hr className="dossier-rule my-6" />

          {/* AI Disclaimer */}
          <div className="mb-8 px-4 py-2 bg-amber-500/5 border border-amber-500/15 rounded">
            <p className="text-xs text-amber-500/70 italic">
              AI-generated research analysis — not a legal document, no evidentiary value. All inferences are TIER_3_AI.
            </p>
          </div>

          {/* Full narrative */}
          {period?.narrative && (
            <section className="mb-8">
              <h2 className="text-xs font-mono uppercase tracking-[0.2em] text-slate-500 border-l-2 border-slate-600 pl-3 mb-4">
                Period Narrative
              </h2>
              <div className="dossier-prose">
                {period.narrative.split('\n\n').map((paragraph: string, i: number) => (
                  <p key={i}>
                    {renderNarrativeWithEntities(paragraph, inlineEntities, caseId)}
                  </p>
                ))}
              </div>
            </section>
          )}

          {/* Entities grid */}
          {entities.length > 0 && (
            <section className="mb-8">
              <h2 className="text-xs font-mono uppercase tracking-[0.2em] text-slate-500 border-l-2 border-slate-600 pl-3 mb-4">
                Entities ({entities.length})
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {entities.map((entity: any) => {
                  const borderClass = ENTITY_BORDER_COLOR[entity.entity_type] || 'border-slate-400/50';
                  return (
                    <Link
                      key={entity.id}
                      href={`/case/${caseId}/entity/${encodeURIComponent(entity.id)}`}
                      className={`vault-panel--muted p-3 rounded border ${borderClass} hover:bg-slate-800/50 transition-colors`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-slate-200 truncate">{entity.name}</span>
                        <VerificationBadge tier={entity.verification.tier} size="tiny" />
                      </div>
                      <p className="text-[10px] font-mono uppercase tracking-wider text-slate-500 mt-1">
                        {entity.entity_type}
                      </p>
                    </Link>
                  );
                })}
              </div>
            </section>
          )}

          {/* Documents */}
          {documents.length > 0 && (
            <section className="mb-8">
              <h2 className="text-xs font-mono uppercase tracking-[0.2em] text-slate-500 border-l-2 border-slate-600 pl-3 mb-4">
                Documents ({documents.length})
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {documents.map((doc: any) => (
                  <Link
                    key={doc.id}
                    href={`/case/${caseId}/document/${encodeURIComponent(doc.id)}`}
                    className="flex items-center gap-3 p-3 bg-slate-800/50 border border-slate-800/50 rounded hover:bg-slate-800 hover:border-slate-700 transition-colors"
                  >
                    <svg className="w-5 h-5 text-slate-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                      />
                    </svg>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm text-slate-300 truncate font-mono">{doc.filename}</p>
                      <p className="text-xs text-slate-500 tabular-nums">{formatDate(doc.date)}</p>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          )}
        </div>
      </div>
    );
  } catch {
    return (
      <div className="p-8">
        <div className="max-w-5xl mx-auto">
          <Link href={`/case/${caseId}/narrative`} className="text-sm text-slate-400 hover:text-slate-200 transition-colors">
            &larr; Back to timeline
          </Link>
          <div className="mt-8 p-8 bg-slate-900 border border-red-800/50 rounded text-center">
            <p className="text-red-400 font-mono text-sm">Failed to load event data</p>
          </div>
        </div>
      </div>
    );
  }
}
