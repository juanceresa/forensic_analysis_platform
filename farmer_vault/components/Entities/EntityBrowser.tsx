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

interface EntityBrowserProps {
  entities: GroupedEntities;
  totalCount: number;
  documentCount: number;
  caseId: string;
}

const ENTITY_TYPE_CONFIG: Record<keyof GroupedEntities, { label: string; icon: string }> = {
  PERSON: { label: 'People', icon: 'P' },
  PROPERTY: { label: 'Properties', icon: 'Pr' },
  ORGANIZATION: { label: 'Organizations', icon: 'O' },
  LOCATION: { label: 'Locations', icon: 'L' },
  DOCUMENT: { label: 'Documents', icon: 'D' },
};

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

export function EntityBrowser({ entities, totalCount, documentCount, caseId }: EntityBrowserProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState<keyof GroupedEntities | null>(null);
  const entityTypes: (keyof GroupedEntities)[] = ['PERSON', 'PROPERTY', 'ORGANIZATION', 'LOCATION', 'DOCUMENT'];

  // Only show types that have entities
  const availableTypes = useMemo(() => {
    return entityTypes.filter(type => (entities[type] || []).length > 0);
  }, [entities]);

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

  // Count filtered results
  const filteredCount = useMemo(() => {
    return Object.values(filteredEntities).reduce((sum, arr) => sum + arr.length, 0);
  }, [filteredEntities]);

  return (
    <div className="max-w-4xl mx-auto p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-mono mb-2">Dictionary</h1>
        <p className="text-muted-foreground">
          {totalCount} entities across {documentCount} documents
        </p>

        {/* Search input */}
        <div className="mt-4">
          <input
            type="text"
            placeholder="Search entities by name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 bg-[var(--card)] border border-[var(--border)] rounded
                       text-foreground placeholder-muted-foreground font-mono text-sm
                       focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
          />
        </div>

        {/* Type filter */}
        {availableTypes.length > 1 && (
          <div className="mt-4 flex items-center gap-2">
            <span className="text-sm text-muted-foreground font-mono">Filter:</span>
            <ButtonGroup>
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
                  {ENTITY_TYPE_CONFIG[type].label} ({(entities[type] || []).length})
                </Button>
              ))}
            </ButtonGroup>
          </div>
        )}

        {(searchTerm || selectedType) && (
          <p className="mt-2 text-sm text-muted-foreground">
            Showing {filteredCount} of {totalCount} entities
          </p>
        )}
      </header>

      {totalCount === 0 ? (
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
        (selectedType ? [selectedType] : entityTypes).map(type => (
          <EntitySection
            key={type}
            type={type}
            entities={filteredEntities[type]}
            caseId={caseId}
          />
        ))
      )}
    </div>
  );
}
