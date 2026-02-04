'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import type { Document } from '@/lib/document-types';
import React from 'react';
import {
  Combobox,
  ComboboxChip,
  ComboboxChips,
  ComboboxChipsInput,
  ComboboxCollection,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxGroup,
  ComboboxItem,
  ComboboxLabel,
  ComboboxList,
  ComboboxSeparator,
  ComboboxValue,
  useComboboxAnchor,
} from '@/components/ui/combobox';
import { Button } from '@/components/ui/button';
import { ButtonGroup } from '@/components/ui/button-group';

interface EntitySummary {
  id: string;
  name: string;
  entity_type: string;
}

interface GroupedEntities {
  PERSON: EntitySummary[];
  PROPERTY: EntitySummary[];
  ORGANIZATION: EntitySummary[];
  LOCATION: EntitySummary[];
}

interface DocumentListProps {
  documents: Document[];
  entities: GroupedEntities;
  caseId: string;
}

type SortBy = 'date' | 'type';

// Entity type display order and labels
const ENTITY_TYPE_ORDER = ['PERSON', 'PROPERTY', 'LOCATION', 'ORGANIZATION'] as const;
const ENTITY_TYPE_LABELS: Record<string, string> = {
  PERSON: 'People',
  PROPERTY: 'Properties',
  LOCATION: 'Locations',
  ORGANIZATION: 'Organizations',
};

export function DocumentList({ documents, entities, caseId }: DocumentListProps) {
  const [sortBy, setSortBy] = useState<SortBy>('date');
  const [dateOrder, setDateOrder] = useState<'asc' | 'desc'>('asc');
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [selectedEntityIds, setSelectedEntityIds] = useState<string[]>([]);
  const comboboxAnchor = useComboboxAnchor();

  // Build entity groups for combobox - items must be strings (like timezone example)
  const entityGroups = useMemo(() => {
    return ENTITY_TYPE_ORDER
      .filter(type => entities[type]?.length > 0)
      .map(type => ({
        value: type,
        label: ENTITY_TYPE_LABELS[type],
        items: entities[type].map(e => `${e.id}|${e.name}`), // Simple strings
      }));
  }, [entities]);

  // Flatten all entities for lookup
  const entityLookup = useMemo(() => {
    const lookup = new Map<string, EntitySummary>();
    for (const type of ENTITY_TYPE_ORDER) {
      for (const entity of entities[type] || []) {
        lookup.set(entity.id, entity);
      }
    }
    return lookup;
  }, [entities]);

  // Get unique document types for filter chips
  const documentTypes = useMemo(() => {
    const types = new Set<string>();
    documents.forEach(doc => {
      if (doc.type) types.add(doc.type);
    });
    return Array.from(types).sort();
  }, [documents]);

  // Compute summary stats
  const stats = useMemo(() => {
    if (documents.length === 0) return null;

    const dates = documents
      .filter(d => d.date)
      .map(d => new Date(d.date!).getTime());

    const avgConfidence = documents.reduce((sum, d) => sum + d.confidence, 0) / documents.length;

    return {
      total: documents.length,
      dateRange: dates.length > 0
        ? {
            earliest: new Date(Math.min(...dates)),
            latest: new Date(Math.max(...dates))
          }
        : null,
      avgConfidence: Math.round(avgConfidence * 100),
    };
  }, [documents]);

  // Filter and sort documents
  const filteredDocuments = useMemo(() => {
    let docs = [...documents];

    // Apply type filter
    if (selectedType) {
      docs = docs.filter(d => d.type === selectedType);
    }

    // Apply entity filter - document must contain ALL selected entities
    if (selectedEntityIds.length > 0) {
      docs = docs.filter(doc => {
        const docEntitySet = new Set(doc.entityIds || []);
        return selectedEntityIds.every(entityId => docEntitySet.has(entityId));
      });
    }

    // Sort
    if (sortBy === 'date') {
      const dir = dateOrder === 'asc' ? 1 : -1;
      return docs.sort((a, b) => {
        if (!a.date && !b.date) return 0;
        if (!a.date) return 1;
        if (!b.date) return -1;
        return dir * (new Date(a.date).getTime() - new Date(b.date).getTime());
      });
    } else {
      return docs.sort((a, b) => {
        if (!a.type && !b.type) return 0;
        if (!a.type) return 1;
        if (!b.type) return -1;
        if (a.type !== b.type) return a.type.localeCompare(b.type);
        if (!a.date && !b.date) return 0;
        if (!a.date) return 1;
        if (!b.date) return -1;
        return new Date(a.date).getTime() - new Date(b.date).getTime();
      });
    }
  }, [documents, selectedType, selectedEntityIds, sortBy, dateOrder]);

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'No date';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Handle combobox value changes
  const handleEntityChange = (values: string[]) => {
    // Extract entity IDs from composite values
    const ids = values.map(v => v.split('|')[0]);
    setSelectedEntityIds(ids);
  };

  // Get composite values for combobox from selected IDs
  const selectedComboboxValues = useMemo(() => {
    return selectedEntityIds.map(id => {
      const entity = entityLookup.get(id);
      return entity ? `${entity.id}|${entity.name}` : id;
    });
  }, [selectedEntityIds, entityLookup]);

  return (
    <>
      {/* Header */}
      <header className="mb-6">
        <h1 className="text-2xl font-mono mb-4">Documents</h1>

        {/* Summary stats */}
        {stats && (
          <div className="mb-4 p-3 bg-card border border-border rounded flex flex-wrap gap-6 text-sm">
            <div>
              <span className="text-muted-foreground">Total:</span>{' '}
              <span className="font-mono text-foreground">{stats.total}</span>
            </div>
            {stats.dateRange && (
              <div>
                <span className="text-muted-foreground">Date range:</span>{' '}
                <span className="font-mono text-foreground">
                  {stats.dateRange.earliest.getFullYear()} – {stats.dateRange.latest.getFullYear()}
                </span>
              </div>
            )}
            <div>
              <span className="text-muted-foreground">Avg OCR:</span>{' '}
              <span className="font-mono text-foreground">{stats.avgConfidence}%</span>
            </div>
          </div>
        )}

        {/* Entity filter combobox */}
        {entityGroups.length > 0 && (
          <div className="mb-4">
            <label className="block text-sm text-muted-foreground font-mono mb-2">
              Filter by entities:
            </label>
            <Combobox
              items={entityGroups}
              multiple
              autoHighlight
              value={selectedComboboxValues}
              onValueChange={handleEntityChange}
            >
              <ComboboxChips ref={comboboxAnchor} className="min-h-[42px] bg-card border-border">
                <ComboboxValue>
                  {(values: string[]) => (
                    <React.Fragment>
                      {values.map((value) => {
                        const name = value.split('|')[1] || value;
                        return (
                          <ComboboxChip
                            key={value}
                            className="bg-primary/10 text-primary border-primary/20"
                          >
                            {name}
                          </ComboboxChip>
                        );
                      })}
                      <ComboboxChipsInput
                        placeholder={values.length === 0 ? "Search entities..." : "Add more..."}
                        className="placeholder:text-muted-foreground"
                      />
                    </React.Fragment>
                  )}
                </ComboboxValue>
                {selectedEntityIds.length > 0 && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedEntityIds([]);
                    }}
                    className="ml-1 p-1 text-muted-foreground hover:text-foreground rounded hover:bg-sidebar-accent transition-colors"
                    aria-label="Clear all filters"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M18 6 6 18" /><path d="m6 6 12 12" />
                    </svg>
                  </button>
                )}
              </ComboboxChips>
              <ComboboxContent anchor={comboboxAnchor} className="bg-card border-border">
                <ComboboxEmpty>No entities found.</ComboboxEmpty>
                <ComboboxList>
                  {(group, index) => (
                    <ComboboxGroup key={group.value} items={group.items}>
                      <ComboboxLabel className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
                        {group.label}
                      </ComboboxLabel>
                      <ComboboxCollection>
                        {(item) => (
                          <ComboboxItem
                            key={item}
                            value={item}
                            className="font-mono text-sm"
                          >
                            {item.split('|')[1]}
                          </ComboboxItem>
                        )}
                      </ComboboxCollection>
                      {index < entityGroups.length - 1 && <ComboboxSeparator />}
                    </ComboboxGroup>
                  )}
                </ComboboxList>
              </ComboboxContent>
            </Combobox>
          </div>
        )}

        {/* Sort controls */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground font-mono">Sort:</span>
            <ButtonGroup>
              <Button
                variant={sortBy === 'date' ? 'default' : 'outline'}
                size="xs"
                onClick={() => { setSortBy('date'); setSelectedType(null); }}
                className="font-mono"
              >
                By Date
              </Button>
              <Button
                variant={sortBy === 'type' ? 'default' : 'outline'}
                size="xs"
                onClick={() => setSortBy('type')}
                className="font-mono"
              >
                By Type
              </Button>
            </ButtonGroup>
          </div>

          {/* Date order (only when sorting by date) */}
          {sortBy === 'date' && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground font-mono">Order:</span>
              <ButtonGroup>
                <Button
                  variant={dateOrder === 'asc' ? 'default' : 'outline'}
                  size="xs"
                  onClick={() => setDateOrder('asc')}
                  className="font-mono"
                >
                  Ascending
                </Button>
                <Button
                  variant={dateOrder === 'desc' ? 'default' : 'outline'}
                  size="xs"
                  onClick={() => setDateOrder('desc')}
                  className="font-mono"
                >
                  Descending
                </Button>
              </ButtonGroup>
            </div>
          )}

          {/* Type filter (only when sorting by type) */}
          {sortBy === 'type' && documentTypes.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground font-mono">Type:</span>
              <ButtonGroup>
                <Button
                  variant={selectedType === null ? 'default' : 'outline'}
                  size="xs"
                  onClick={() => setSelectedType(null)}
                  className="font-mono"
                >
                  All
                </Button>
                {documentTypes.map(type => (
                  <Button
                    key={type}
                    variant={selectedType === type ? 'default' : 'outline'}
                    size="xs"
                    onClick={() => setSelectedType(type)}
                    className="font-mono uppercase"
                  >
                    {type}
                  </Button>
                ))}
              </ButtonGroup>
            </div>
          )}
        </div>
      </header>

      {/* Document grid */}
      <div className="grid gap-3">
        {filteredDocuments.map((doc, index) => (
          <Link
            key={doc.id}
            href={`/case/${caseId}/document/${encodeURIComponent(doc.id)}`}
            className="group block p-4 bg-card border border-border rounded
                       hover:border-primary/30 hover:bg-sidebar-accent/50 transition-colors
                       focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2
                       focus-visible:ring-offset-background animate-fade-in-up"
            style={{ animationDelay: `${index * 0.03}s` } as React.CSSProperties}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                {/* Document name */}
                <h3 className="font-mono text-foreground truncate group-hover:text-primary transition-colors">
                  {doc.filename}
                </h3>

                {/* Metadata */}
                <div className="mt-2 flex items-center gap-4 text-sm text-muted-foreground">
                  <time dateTime={doc.date || undefined} className="font-mono tabular-nums">
                    {formatDate(doc.date)}
                  </time>
                  {doc.type && (
                    <span className="px-2 py-0.5 bg-sidebar-accent rounded text-xs uppercase tracking-wider">
                      {doc.type}
                    </span>
                  )}
                  <span className="text-xs text-muted-foreground/60">
                    {Math.round(doc.confidence * 100)}% OCR confidence
                  </span>
                </div>
              </div>

              {/* Entity count badge */}
              <div className="flex items-center gap-1.5 text-muted-foreground">
                <span className="font-mono tabular-nums">{doc.entityCount}</span>
                <span className="text-xs">entities</span>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {filteredDocuments.length === 0 && (
        <div className="p-8 bg-card border border-border border-dashed rounded text-center">
          <p className="text-muted-foreground font-mono text-sm">
            {documents.length === 0
              ? 'No documents found'
              : 'No documents match your filters'}
          </p>
          {(selectedType || selectedEntityIds.length > 0) && documents.length > 0 && (
            <button
              onClick={() => {
                setSelectedType(null);
                setSelectedEntityIds([]);
              }}
              className="mt-2 text-sm text-primary hover:text-primary/80"
            >
              Clear filters
            </button>
          )}
        </div>
      )}
    </>
  );
}
