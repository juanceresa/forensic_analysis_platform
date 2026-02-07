'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { VerificationBadge } from '@/components/shared';
import { Button } from '@/components/ui/button';
import { ButtonGroup } from '@/components/ui/button-group';
import type { EntityType } from '@/lib/types';

interface EntitySummary {
  id: string;
  name: string;
  entity_type: EntityType;
  roleLabel?: string;
  verification: {
    tier: string;
    confidence: number;
  };
  documentCount: number;
}

interface GroupedEntities {
  PERSON: EntitySummary[];
  PROPERTY: EntitySummary[];
  ORGANIZATION: EntitySummary[];
  LOCATION: EntitySummary[];
  DOCUMENT: EntitySummary[];
}

interface TimelineEvent {
  id: string;
  year: number;
  date: string | null;
  eventType: string;
  summary: string;
  parties: string[];
}

interface EntityBrowserProps {
  entities: GroupedEntities;
  totalCount: number;
  documentCount: number;
  caseId: string;
  events?: TimelineEvent[];
}

const ENTITY_TYPE_CONFIG: Record<keyof GroupedEntities, { label: string; icon: string }> = {
  PERSON: { label: 'PEOPLE', icon: 'P' },
  PROPERTY: { label: 'PROPERTIES', icon: 'Pr' },
  ORGANIZATION: { label: 'ORGANIZATIONS', icon: 'O' },
  LOCATION: { label: 'LOCATIONS', icon: 'L' },
  DOCUMENT: { label: 'DOCUMENTS', icon: 'D' },
};

const EVENT_TYPE_STYLE: Record<string, { bg: string; text: string; border: string }> = {
  CONFISCATED: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20' },
  SOLD: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20' },
  INHERITED: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20' },
};

function formatEventDate(dateStr: string | null): string {
  if (!dateStr) return '';
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

function EventsSection({ events, caseId }: { events: TimelineEvent[]; caseId: string }) {
  if (events.length === 0) return null;

  return (
    <section className="mb-8">
      <h2 className="text-lg font-mono uppercase tracking-wider mb-4 flex items-center gap-3">
        <span>Key Events</span>
        <span className="px-2 py-0.5 bg-muted rounded text-sm font-mono tabular-nums">
          {events.length}
        </span>
      </h2>

      <div className="space-y-2">
        {events.map((event, index) => {
          const style = EVENT_TYPE_STYLE[event.eventType] || EVENT_TYPE_STYLE.CONFISCATED;
          return (
            <Link
              key={event.id}
              href={`/case/${caseId}/narrative/event/${event.id}`}
              className="flex items-start gap-4 p-4 bg-[var(--card)] border border-[var(--border)] rounded
                         hover:border-primary/30 hover:bg-muted/50 transition-colors
                         focus-visible:ring-2 focus-visible:ring-ring animate-fade-in-up"
              style={{ animationDelay: `${index * 0.03}s` } as React.CSSProperties}
            >
              {/* Year */}
              <div className="w-10 h-10 flex items-center justify-center shrink-0">
                <span className="text-lg font-mono tabular-nums text-foreground/80">{event.year}</span>
              </div>

              {/* Event info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider border rounded ${style.bg} ${style.text} ${style.border}`}>
                    {event.eventType}
                  </span>
                  {event.date && (
                    <span className="text-xs text-muted-foreground font-mono tabular-nums">
                      {formatEventDate(event.date)}
                    </span>
                  )}
                </div>
                <h3 className="font-mono text-sm text-foreground">{event.summary}</h3>
                {event.parties.length > 0 && (
                  <p className="text-xs text-muted-foreground/70 mt-1 truncate">
                    {event.parties.join(', ')}
                  </p>
                )}
              </div>

              {/* Arrow */}
              <div className="text-muted-foreground shrink-0 mt-2">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </Link>
          );
        })}
      </div>
    </section>
  );
}

function EntitySection({
  type,
  entities,
  caseId,
}: {
  type: keyof GroupedEntities;
  entities: EntitySummary[];
  caseId: string;
}) {
  const config = ENTITY_TYPE_CONFIG[type];

  if (entities.length === 0) return null;

  return (
    <section className="mb-8">
      <h2 className="text-lg font-mono uppercase tracking-wider mb-4 flex items-center gap-3">
        <span>{config.label}</span>
        <span className="px-2 py-0.5 bg-muted rounded text-sm font-mono tabular-nums">
          {entities.length}
        </span>
      </h2>

      <div className="space-y-2">
        {entities.map((entity, index) => (
          <Link
            key={entity.id}
            href={`/case/${caseId}/entity/${encodeURIComponent(entity.id)}`}
            className="flex items-center gap-4 p-4 bg-[var(--card)] border border-[var(--border)] rounded
                       hover:border-primary/30 hover:bg-muted/50 transition-colors
                       focus-visible:ring-2 focus-visible:ring-ring animate-fade-in-up"
            style={{ animationDelay: `${index * 0.03}s` } as React.CSSProperties}
          >
            {/* Entity type icon */}
            <div className="w-10 h-10 flex items-center justify-center bg-muted rounded shrink-0">
              <span className="text-sm font-mono text-muted-foreground">{config.icon}</span>
            </div>

            {/* Entity info */}
            <div className="flex-1 min-w-0">
              <h3 className="font-mono text-foreground truncate">{entity.name}</h3>
              {entity.roleLabel && (
                <p className="text-sm text-muted-foreground italic truncate">{entity.roleLabel}</p>
              )}
              <p className="text-xs text-muted-foreground/70 mt-1">
                {entity.documentCount} document{entity.documentCount !== 1 ? 's' : ''}
              </p>
            </div>

            {/* Verification badge */}
            <VerificationBadge tier={entity.verification.tier as any} size="small" />

            {/* Arrow */}
            <div className="text-muted-foreground">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}

type FilterType = keyof GroupedEntities | 'EVENTS';

export function EntityBrowser({ entities, totalCount, documentCount, caseId, events = [] }: EntityBrowserProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState<FilterType | null>(null);
  const entityTypes: (keyof GroupedEntities)[] = ['PERSON', 'PROPERTY', 'ORGANIZATION', 'LOCATION', 'DOCUMENT'];

  // Only show types that have entities (+ events if available)
  const availableTypes = useMemo(() => {
    const types: FilterType[] = [];
    if (events.length > 0) types.push('EVENTS');
    for (const type of entityTypes) {
      if ((entities[type] || []).length > 0) types.push(type);
    }
    return types;
  }, [entities, events]);

  // Filter entities by search term across all groups
  // Always normalize to ensure all entity types exist (API may omit empty types)
  const filteredEntities = useMemo(() => {
    const term = searchTerm?.toLowerCase() || '';
    return {
      PERSON: (entities.PERSON || []).filter(e => !term || e.name?.toLowerCase().includes(term)),
      PROPERTY: (entities.PROPERTY || []).filter(e => !term || e.name?.toLowerCase().includes(term)),
      ORGANIZATION: (entities.ORGANIZATION || []).filter(e => !term || e.name?.toLowerCase().includes(term)),
      LOCATION: (entities.LOCATION || []).filter(e => !term || e.name?.toLowerCase().includes(term)),
      DOCUMENT: (entities.DOCUMENT || []).filter(e => !term || e.name?.toLowerCase().includes(term)),
    };
  }, [entities, searchTerm]);

  // Filter events by search term too
  const filteredEvents = useMemo(() => {
    const term = searchTerm?.toLowerCase() || '';
    if (!term) return events;
    return events.filter(e =>
      e.summary?.toLowerCase().includes(term) ||
      e.parties?.some(p => p.toLowerCase().includes(term))
    );
  }, [events, searchTerm]);

  // Count filtered results for empty state check
  const filteredCount = useMemo(() => {
    return Object.values(filteredEntities).reduce((sum, arr) => sum + arr.length, 0) + filteredEvents.length;
  }, [filteredEntities, filteredEvents]);

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8">
      <header className="mb-8">
        <p className="text-sm text-muted-foreground">
          People, places, and organizations extracted from{' '}
          <span className="tabular-nums">{documentCount}</span> document{documentCount !== 1 ? 's' : ''} —{' '}
          <span className="tabular-nums">{totalCount}</span> entities identified.
        </p>

        {/* Search input */}
        <div className="mt-4">
          <input
            type="text"
            placeholder="Search Index by name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 bg-[var(--card)] border border-[var(--border)] rounded
                       text-foreground placeholder-muted-foreground font-mono text-sm
                       focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
          />
        </div>

        {/* Type filter */}
        {availableTypes.length > 1 && (
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-sm text-muted-foreground font-mono shrink-0">Filter:</span>
            <ButtonGroup className="flex-wrap">
              <Button
                variant={selectedType === null ? 'default' : 'outline'}
                size="xs"
                onClick={() => setSelectedType(null)}
                className="font-mono"
              >
                All
              </Button>
              {availableTypes.map(type => (
                <Button
                  key={type}
                  variant={selectedType === type ? 'default' : 'outline'}
                  size="xs"
                  onClick={() => setSelectedType(type)}
                  className="font-mono"
                >
                  {type === 'EVENTS' ? 'EVENTS' : ENTITY_TYPE_CONFIG[type].label}
                </Button>
              ))}
            </ButtonGroup>
          </div>
        )}

      </header>

      {totalCount === 0 && events.length === 0 ? (
        <div className="p-8 bg-[var(--card)] border border-[var(--border)] border-dashed rounded text-center">
          <p className="text-muted-foreground font-mono text-sm">No entities found</p>
        </div>
      ) : filteredCount === 0 ? (
        <div className="p-8 bg-[var(--card)] border border-[var(--border)] border-dashed rounded text-center">
          <p className="text-muted-foreground font-mono text-sm">No entities match your filters</p>
          <button
            onClick={() => { setSearchTerm(''); setSelectedType(null); }}
            className="mt-2 text-sm text-primary hover:text-primary/80"
          >
            Clear filters
          </button>
        </div>
      ) : (
        <>
          {/* Events section — show when All or EVENTS filter */}
          {(selectedType === null || selectedType === 'EVENTS') && (
            <EventsSection events={filteredEvents} caseId={caseId} />
          )}

          {/* Entity sections — show when All or a specific entity type */}
          {selectedType !== 'EVENTS' && (
            (selectedType ? [selectedType as keyof GroupedEntities] : entityTypes).map(type => (
              <EntitySection
                key={type}
                type={type}
                entities={filteredEntities[type]}
                caseId={caseId}
              />
            ))
          )}
        </>
      )}
    </div>
  );
}
