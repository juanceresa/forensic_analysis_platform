'use client';

import Link from 'next/link';
import type { BaseNode } from '@/lib/types';
import { VerificationBadge } from '@/components/shared';

interface SourceDocument {
  id: string;
  filename: string;
}

interface Connection {
  relation_type: string;
  targetEntity: {
    id: string;
    name: string;
    entity_type: string;
    verification: {
      tier: string;
      confidence: number;
    };
  };
}

interface EntityDetailProps {
  entity: BaseNode;
  sourceDocuments: SourceDocument[];
  connections: Connection[];
  caseId: string;
}

export function EntityDetail({ entity, sourceDocuments, connections, caseId }: EntityDetailProps) {
  // Group connections by relation type
  const groupConnectionsByType = (conns: Connection[]) => {
    return conns.reduce((acc, conn) => {
      const type = conn.relation_type;
      if (!acc[type]) {
        acc[type] = [];
      }
      acc[type].push(conn);
      return acc;
    }, {} as Record<string, Connection[]>);
  };

  const groupedConnections = groupConnectionsByType(connections);

  // Render entity-specific metadata
  const renderMetadata = () => {
    switch (entity.entity_type) {
      case 'PERSON':
        return (
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 text-sm">
            {entity.birth_date ? (
              <>
                <dt className="text-muted-foreground font-mono uppercase tracking-wider text-xs">Birth Date</dt>
                <dd className="text-foreground/80 font-mono tabular-nums">{String(entity.birth_date)}</dd>
              </>
            ) : null}
            {entity.nationality ? (
              <>
                <dt className="text-muted-foreground font-mono uppercase tracking-wider text-xs">Nationality</dt>
                <dd className="text-foreground/80">{String(entity.nationality)}</dd>
              </>
            ) : null}
            {entity.profession ? (
              <>
                <dt className="text-muted-foreground font-mono uppercase tracking-wider text-xs">Profession</dt>
                <dd className="text-foreground/80">{String(entity.profession)}</dd>
              </>
            ) : null}
            {entity.residence ? (
              <>
                <dt className="text-muted-foreground font-mono uppercase tracking-wider text-xs">Residence</dt>
                <dd className="text-foreground/80">{String(entity.residence)}</dd>
              </>
            ) : null}
          </dl>
        );
      case 'PROPERTY':
        return (
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 text-sm">
            {entity.address ? (
              <>
                <dt className="text-muted-foreground font-mono uppercase tracking-wider text-xs">Address</dt>
                <dd className="text-foreground/80">{String(entity.address)}</dd>
              </>
            ) : null}
            {entity.area ? (
              <>
                <dt className="text-muted-foreground font-mono uppercase tracking-wider text-xs">Area</dt>
                <dd className="text-foreground/80 font-mono tabular-nums">
                  {String(entity.area)} {entity.area_unit ? String(entity.area_unit) : ''}
                </dd>
              </>
            ) : null}
            {entity.registry_number ? (
              <>
                <dt className="text-muted-foreground font-mono uppercase tracking-wider text-xs">Registry</dt>
                <dd className="text-foreground/80 font-mono">{String(entity.registry_number)}</dd>
              </>
            ) : null}
          </dl>
        );
      case 'ORGANIZATION':
        return (
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 text-sm">
            {entity.org_type ? (
              <>
                <dt className="text-muted-foreground font-mono uppercase tracking-wider text-xs">Type</dt>
                <dd className="text-foreground/80">{String(entity.org_type)}</dd>
              </>
            ) : null}
            {entity.address ? (
              <>
                <dt className="text-muted-foreground font-mono uppercase tracking-wider text-xs">Address</dt>
                <dd className="text-foreground/80">{String(entity.address)}</dd>
              </>
            ) : null}
          </dl>
        );
      case 'LOCATION':
        return (
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 text-sm">
            {entity.location_type ? (
              <>
                <dt className="text-muted-foreground font-mono uppercase tracking-wider text-xs">Type</dt>
                <dd className="text-foreground/80">{String(entity.location_type)}</dd>
              </>
            ) : null}
            {entity.country ? (
              <>
                <dt className="text-muted-foreground font-mono uppercase tracking-wider text-xs">Country</dt>
                <dd className="text-foreground/80">{String(entity.country)}</dd>
              </>
            ) : null}
          </dl>
        );
      case 'DOCUMENT':
        return (
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3 text-sm">
            {entity.document_type ? (
              <>
                <dt className="text-muted-foreground font-mono uppercase tracking-wider text-xs">Type</dt>
                <dd className="text-foreground/80">{String(entity.document_type)}</dd>
              </>
            ) : null}
            {entity.date ? (
              <>
                <dt className="text-muted-foreground font-mono uppercase tracking-wider text-xs">Date</dt>
                <dd className="text-foreground/80 font-mono tabular-nums">{String(entity.date)}</dd>
              </>
            ) : null}
            {entity.page_count ? (
              <>
                <dt className="text-muted-foreground font-mono uppercase tracking-wider text-xs">Pages</dt>
                <dd className="text-foreground/80 font-mono tabular-nums">{String(entity.page_count)}</dd>
              </>
            ) : null}
          </dl>
        );
      default:
        return null;
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-4 sm:p-6 lg:p-8">
      {/* Entity Header Card */}
      <header className="mb-6 sm:mb-8 p-4 sm:p-6 bg-[var(--card)] border border-[var(--border)] rounded">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 sm:gap-6">
          <div className="flex-1">
            {/* Entity type badge */}
            <div className="mb-2">
              <span className="px-2 py-1 bg-muted rounded text-xs uppercase tracking-wider text-muted-foreground font-mono">
                {entity.entity_type}
              </span>
            </div>

            {/* Entity name */}
            <h1 className="text-2xl sm:text-3xl font-mono mb-3 text-foreground">{entity.name || entity.id}</h1>

            {/* TODO: Role label when available */}

            {/* Metadata grid */}
            {renderMetadata()}
          </div>

          {/* Verification badge (prominent) */}
          <div className="sm:text-right">
            <div className="text-xs text-muted-foreground font-mono uppercase tracking-wider mb-2">
              Verification
            </div>
            <VerificationBadge tier={entity.verification.tier as any} size="large" />
            <div className="mt-2 text-xs text-muted-foreground font-mono tabular-nums">
              {Math.round(entity.verification.confidence * 100)}% confidence
            </div>
          </div>
        </div>
      </header>

      {/* AI-Generated Description (Placeholder - will be added in Phase 3) */}
      <details className="mb-6 sm:mb-8 group">
        <summary className="flex items-center gap-3 p-4 bg-[var(--card)] border border-[var(--border)] rounded
                       cursor-pointer hover:bg-muted/50 transition-colors
                       group-open:rounded-b-none list-none focus-visible:ring-2 focus-visible:ring-ring">
          <div className="flex items-center gap-2 flex-1">
            <span className="font-mono text-sm uppercase tracking-wider text-foreground">About</span>
            <span className="px-2 py-0.5 bg-amber-500/10 border border-amber-500/20 rounded text-xs text-amber-400 font-mono">
              TIER_3_AI
            </span>
          </div>
          <svg
            className="w-4 h-4 text-muted-foreground transition-transform group-open:rotate-180"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </summary>

        <div className="p-4 sm:p-6 bg-[var(--card)] border border-t-0 border-[var(--border)] rounded-b">
          <p className="text-muted-foreground leading-relaxed italic">
            AI-generated description will be available after role label generation is implemented in the backend.
          </p>
          <div className="mt-4 p-3 bg-amber-500/5 border border-amber-500/20 rounded">
            <p className="text-xs text-amber-400/80 leading-relaxed">
              ⚠️ This description was generated by AI based on document analysis.
              It has not been verified by human analysts and should be reviewed carefully.
            </p>
          </div>
        </div>
      </details>

      {/* Source Documents Section */}
      <section className="mb-6 sm:mb-8">
        <h2 className="text-lg font-mono uppercase tracking-wider mb-4 flex items-center gap-3 text-foreground">
          <span>Source Documents</span>
          <span className="px-2 py-0.5 bg-muted rounded text-sm font-mono tabular-nums text-muted-foreground">
            {sourceDocuments.length}
          </span>
        </h2>

        <div className="space-y-3">
          {sourceDocuments.map((doc, index) => (
            <Link
              key={doc.id}
              href={`/case/${caseId}/document/${encodeURIComponent(doc.id)}`}
              className="block p-4 bg-[var(--card)] border border-[var(--border)] rounded
                         hover:border-primary/30 hover:bg-muted/50 transition-colors
                         focus-visible:ring-2 focus-visible:ring-ring animate-fade-in-up"
              style={{ animationDelay: `${index * 0.05}s` } as React.CSSProperties}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <h3 className="font-mono text-foreground truncate">{doc.filename}</h3>
                </div>
                <div className="text-muted-foreground">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Connections Section */}
      <section>
        <h2 className="text-lg font-mono uppercase tracking-wider mb-4 flex items-center gap-3 text-foreground">
          <span>Connections</span>
          <span className="px-2 py-0.5 bg-muted rounded text-sm font-mono tabular-nums text-muted-foreground">
            {connections.length}
          </span>
        </h2>

        {connections.length === 0 ? (
          <div className="p-8 bg-[var(--card)] border border-[var(--border)] border-dashed rounded text-center">
            <p className="text-muted-foreground font-mono text-sm">No connections found</p>
          </div>
        ) : (
          <div className="space-y-4">
            {Object.entries(groupedConnections).map(([relationType, conns]) => (
              <div key={relationType} className="p-4 bg-[var(--card)] border border-[var(--border)] rounded">
                <h3 className="text-xs uppercase tracking-wider text-muted-foreground font-mono mb-3">
                  {relationType}
                </h3>
                <div className="space-y-2">
                  {conns.map((conn, index) => (
                    <Link
                      key={`${conn.targetEntity.id}-${index}`}
                      href={`/case/${caseId}/entity/${encodeURIComponent(conn.targetEntity.id)}`}
                      className="flex items-center gap-3 p-3 bg-muted/50 rounded
                                 hover:bg-muted transition-colors
                                 focus-visible:ring-2 focus-visible:ring-ring animate-fade-in-up"
                      style={{ animationDelay: `${index * 0.05}s` } as React.CSSProperties}
                    >
                      {/* Entity type icon placeholder */}
                      <div className="w-8 h-8 flex items-center justify-center bg-background rounded shrink-0">
                        <span className="text-xs font-mono text-muted-foreground">
                          {conn.targetEntity.entity_type[0]}
                        </span>
                      </div>

                      {/* Entity info */}
                      <div className="flex-1 min-w-0">
                        <div className="font-mono text-sm text-foreground truncate">
                          {conn.targetEntity.name}
                        </div>
                        {/* TODO: Add roleLabel when available */}
                      </div>

                      {/* Verification badge */}
                      <VerificationBadge tier={conn.targetEntity.verification.tier as any} size="small" />

                      {/* Arrow */}
                      <div className="text-muted-foreground">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
