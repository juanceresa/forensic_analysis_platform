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

  const sortedDocuments = useMemo(() => {
    const docs = [...documents];

    if (sortBy === 'date') {
      // Sort by date (earliest first)
      return docs.sort((a, b) => {
        if (!a.date && !b.date) return 0;
        if (!a.date) return 1;
        if (!b.date) return -1;
        return new Date(a.date).getTime() - new Date(b.date).getTime();
      });
    } else {
      // Sort by type, then by date within type
      return docs.sort((a, b) => {
        if (!a.type && !b.type) return 0;
        if (!a.type) return 1;
        if (!b.type) return -1;
        if (a.type !== b.type) return a.type.localeCompare(b.type);
        // Within same type, sort by date
        if (!a.date && !b.date) return 0;
        if (!a.date) return 1;
        if (!b.date) return -1;
        return new Date(a.date).getTime() - new Date(b.date).getTime();
      });
    }
  }, [documents, sortBy]);

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

        {/* Sort controls */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-500 font-mono mr-2">Sort by:</span>
          <button
            onClick={() => setSortBy('date')}
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
      </header>

      {/* Document grid */}
      <div className="grid gap-3">
        {sortedDocuments.map((doc, index) => (
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

      {sortedDocuments.length === 0 && (
        <div className="p-8 bg-slate-900 border border-slate-800 border-dashed rounded text-center">
          <p className="text-slate-500 font-mono text-sm">No documents found</p>
        </div>
      )}
    </>
  );
}
