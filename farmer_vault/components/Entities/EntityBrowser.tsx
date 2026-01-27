'use client';

import Link from 'next/link';
import { VerificationBadge } from '@/components/shared';
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
        <span className="px-2 py-0.5 bg-slate-800 rounded text-sm font-mono tabular-nums">
          {entities.length}
        </span>
      </h2>

      <div className="space-y-2">
        {entities.map((entity, index) => (
          <Link
            key={entity.id}
            href={`/case/${caseId}/entity/${encodeURIComponent(entity.id)}`}
            className="flex items-center gap-4 p-4 bg-slate-900 border border-slate-800 rounded
                       hover:border-slate-700 hover:bg-slate-800/50 transition-colors
                       focus-visible:ring-2 focus-visible:ring-blue-500 animate-fade-in-up"
            style={{ animationDelay: `${index * 0.03}s` } as React.CSSProperties}
          >
            {/* Entity type icon */}
            <div className="w-10 h-10 flex items-center justify-center bg-slate-800 rounded shrink-0">
              <span className="text-sm font-mono text-slate-400">{config.icon}</span>
            </div>

            {/* Entity info */}
            <div className="flex-1 min-w-0">
              <h3 className="font-mono text-slate-100 truncate">{entity.name}</h3>
              {entity.roleLabel && (
                <p className="text-sm text-slate-400 italic truncate">{entity.roleLabel}</p>
              )}
              <p className="text-xs text-slate-500 mt-1">
                {entity.documentCount} document{entity.documentCount !== 1 ? 's' : ''}
              </p>
            </div>

            {/* Verification badge */}
            <VerificationBadge tier={entity.verification.tier as any} size="small" />

            {/* Arrow */}
            <div className="text-slate-500">
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
  const entityTypes: (keyof GroupedEntities)[] = ['PERSON', 'PROPERTY', 'ORGANIZATION', 'LOCATION'];

  return (
    <div className="max-w-4xl mx-auto p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-mono mb-2">Entities</h1>
        <p className="text-slate-400">
          {totalCount} entities across {documentCount} documents
        </p>
      </header>

      {totalCount === 0 ? (
        <div className="p-8 bg-slate-900 border border-slate-800 border-dashed rounded text-center">
          <p className="text-slate-500 font-mono text-sm">No entities found</p>
        </div>
      ) : (
        entityTypes.map(type => (
          <EntitySection
            key={type}
            type={type}
            entities={entities[type]}
            caseId={caseId}
          />
        ))
      )}
    </div>
  );
}
