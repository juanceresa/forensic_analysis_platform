'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import type { Document } from '@/lib/document-types';

interface DocumentListProps {
  documents: Document[];
  caseId: string;
}

type SortBy = 'date' | 'type';

export function DocumentList({ documents, caseId }: DocumentListProps) {
  const [sortBy, setSortBy] = useState<SortBy>('date');
  const [dateOrder, setDateOrder] = useState<'asc' | 'desc'>('asc');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState<string | null>(null);

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

    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      docs = docs.filter(d => d.filename.toLowerCase().includes(term));
    }

    // Apply type filter
    if (selectedType) {
      docs = docs.filter(d => d.type === selectedType);
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
  }, [documents, searchTerm, selectedType, sortBy, dateOrder]);

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'No date';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <>
      {/* Header */}
      <header className="mb-6">
        <h1 className="text-2xl font-mono mb-4">Documents</h1>

        {/* Summary stats */}
        {stats && (
          <div className="mb-4 p-3 bg-slate-900 border border-slate-800 rounded flex flex-wrap gap-6 text-sm">
            <div>
              <span className="text-slate-500">Total:</span>{' '}
              <span className="font-mono text-slate-300">{stats.total}</span>
            </div>
            {stats.dateRange && (
              <div>
                <span className="text-slate-500">Date range:</span>{' '}
                <span className="font-mono text-slate-300">
                  {stats.dateRange.earliest.getFullYear()} – {stats.dateRange.latest.getFullYear()}
                </span>
              </div>
            )}
            <div>
              <span className="text-slate-500">Avg OCR:</span>{' '}
              <span className="font-mono text-slate-300">{stats.avgConfidence}%</span>
            </div>
          </div>
        )}

        {/* Search input */}
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search documents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded
                       text-slate-100 placeholder-slate-500 font-mono text-sm
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Sort controls */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-500 font-mono mr-2">Sort by:</span>
          <button
            onClick={() => { setSortBy('date'); setSelectedType(null); }}
            className={`px-3 py-1.5 text-sm font-mono rounded border transition-colors
              focus-visible:ring-2 focus-visible:ring-blue-500
              ${
                sortBy === 'date'
                  ? 'bg-slate-800 border-slate-600 text-slate-100'
                  : 'border-slate-700 text-slate-400 hover:text-slate-300 hover:bg-slate-900'
              }`}
          >
            By Date
          </button>
          <button
            onClick={() => setSortBy('type')}
            className={`px-3 py-1.5 text-sm font-mono rounded border transition-colors
              focus-visible:ring-2 focus-visible:ring-blue-500
              ${
                sortBy === 'type'
                  ? 'bg-slate-800 border-slate-600 text-slate-100'
                  : 'border-slate-700 text-slate-400 hover:text-slate-300 hover:bg-slate-900'
              }`}
          >
            By Type
          </button>
        </div>

        {/* Date order chips (only when sorting by date) */}
        {sortBy === 'date' && (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <span className="text-sm text-slate-500 font-mono mr-1">Order:</span>
            {(['asc', 'desc'] as const).map(order => (
              <button
                key={order}
                onClick={() => setDateOrder(order)}
                className={`px-3 py-1 text-xs font-mono rounded border transition-colors
                  focus-visible:ring-2 focus-visible:ring-blue-500
                  ${
                    dateOrder === order
                      ? 'bg-blue-600 border-blue-500 text-white'
                      : 'border-slate-700 text-slate-400 hover:text-slate-300 hover:bg-slate-900'
                  }`}
              >
                {order === 'asc' ? 'Ascending' : 'Descending'}
              </button>
            ))}
          </div>
        )}

        {/* Type filter chips (only when sorting by type) */}
        {sortBy === 'type' && documentTypes.length > 0 && (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <span className="text-sm text-slate-500 font-mono mr-1">Filter:</span>
            <button
              onClick={() => setSelectedType(null)}
              className={`px-3 py-1 text-xs font-mono rounded border transition-colors
                focus-visible:ring-2 focus-visible:ring-blue-500
                ${
                  selectedType === null
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'border-slate-700 text-slate-400 hover:text-slate-300 hover:bg-slate-900'
                }`}
            >
              All
            </button>
            {documentTypes.map(type => (
              <button
                key={type}
                onClick={() => setSelectedType(type)}
                className={`px-3 py-1 text-xs font-mono uppercase rounded border transition-colors
                  focus-visible:ring-2 focus-visible:ring-blue-500
                  ${
                    selectedType === type
                      ? 'bg-blue-600 border-blue-500 text-white'
                      : 'border-slate-700 text-slate-400 hover:text-slate-300 hover:bg-slate-900'
                  }`}
              >
                {type}
              </button>
            ))}
          </div>
        )}
      </header>

      {/* Document grid */}
      <div className="grid gap-3">
        {filteredDocuments.map((doc, index) => (
          <Link
            key={doc.id}
            href={`/case/${caseId}/document/${encodeURIComponent(doc.id)}`}
            className="group block p-4 bg-slate-900 border border-slate-800 rounded
                       hover:border-slate-700 hover:bg-slate-800/50 transition-colors
                       focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2
                       focus-visible:ring-offset-slate-950 animate-fade-in-up"
            style={{ animationDelay: `${index * 0.03}s` } as React.CSSProperties}
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                {/* Document name */}
                <h3 className="font-mono text-slate-100 truncate group-hover:text-blue-400 transition-colors">
                  {doc.filename}
                </h3>

                {/* Metadata */}
                <div className="mt-2 flex items-center gap-4 text-sm text-slate-400">
                  <time dateTime={doc.date || undefined} className="font-mono tabular-nums">
                    {formatDate(doc.date)}
                  </time>
                  {doc.type && (
                    <span className="px-2 py-0.5 bg-slate-800 rounded text-xs uppercase tracking-wider">
                      {doc.type}
                    </span>
                  )}
                  <span className="text-xs text-slate-500">
                    {Math.round(doc.confidence * 100)}% OCR confidence
                  </span>
                </div>
              </div>

              {/* Entity count badge */}
              <div className="flex items-center gap-1.5 text-slate-400">
                <span className="font-mono tabular-nums">{doc.entityCount}</span>
                <span className="text-xs">entities</span>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {filteredDocuments.length === 0 && (
        <div className="p-8 bg-slate-900 border border-slate-800 border-dashed rounded text-center">
          <p className="text-slate-500 font-mono text-sm">
            {documents.length === 0
              ? 'No documents found'
              : 'No documents match your search'}
          </p>
          {(searchTerm || selectedType) && documents.length > 0 && (
            <button
              onClick={() => {
                setSearchTerm('');
                setSelectedType(null);
              }}
              className="mt-2 text-sm text-blue-400 hover:text-blue-300"
            >
              Clear filters
            </button>
          )}
        </div>
      )}
    </>
  );
}
