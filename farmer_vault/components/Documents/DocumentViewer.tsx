'use client';

import { useState } from 'react';
import Link from 'next/link';
import type { DocumentDetail } from '@/lib/document-types';
import type { BaseNode } from '@/lib/types';
import { VerificationBadge } from '@/components/shared';

interface DocumentViewerProps {
  document: DocumentDetail;
  caseId: string;
}

type TabType = 'ocr' | 'translated' | 'entities';

// Language code to display name mapping
const LANGUAGE_NAMES: Record<string, string> = {
  es: 'Spanish',
  fr: 'French',
  de: 'German',
  it: 'Italian',
  pt: 'Portuguese',
  ru: 'Russian',
  zh: 'Chinese',
  ja: 'Japanese',
  ko: 'Korean',
  ar: 'Arabic',
};

export function DocumentViewer({ document, caseId }: DocumentViewerProps) {
  const [activeTab, setActiveTab] = useState<TabType>('ocr');
  const [zoom, setZoom] = useState(0.25); // Start zoomed out to fit document

  const languageDisplayName = document.detectedLanguage
    ? LANGUAGE_NAMES[document.detectedLanguage] || document.detectedLanguage.toUpperCase()
    : null;

  // Translation is pre-generated during processing
  const hasTranslation = !!document.translatedText;

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'No date';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const groupEntitiesByType = (entities: BaseNode[]) => {
    return entities.reduce((acc, entity) => {
      const type = entity.entity_type;
      if (!acc[type]) {
        acc[type] = [];
      }
      acc[type].push(entity);
      return acc;
    }, {} as Record<string, BaseNode[]>);
  };

  const groupedEntities = groupEntitiesByType(document.entities);

  return (
    <div className="h-full flex">
      {/* Left: Original Image */}
      <section
        className="flex-1 bg-slate-900 border-r border-slate-800 overflow-auto"
        aria-label="Document image"
      >
        <div className="p-8">
          {/* Zoom controls */}
          <div className="mb-4 flex items-center gap-2">
            <button
              aria-label="Zoom out"
              className="p-2 bg-slate-800 hover:bg-slate-700 rounded transition-colors
                         focus-visible:ring-2 focus-visible:ring-blue-500"
              onClick={() => setZoom(z => Math.max(0.1, z - 0.1))}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
              </svg>
            </button>
            <span className="px-3 py-1 bg-slate-800 rounded font-mono text-sm tabular-nums min-w-[4rem] text-center">
              {Math.round(zoom * 100)}%
            </span>
            <button
              aria-label="Zoom in"
              className="p-2 bg-slate-800 hover:bg-slate-700 rounded transition-colors
                         focus-visible:ring-2 focus-visible:ring-blue-500"
              onClick={() => setZoom(z => Math.min(1, z + 0.1))}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
            <button
              aria-label="Reset zoom"
              className="ml-auto px-3 py-1 bg-slate-800 hover:bg-slate-700 rounded text-sm transition-colors
                         focus-visible:ring-2 focus-visible:ring-blue-500"
              onClick={() => setZoom(0.25)}
            >
              Reset
            </button>
          </div>

          {/* Document image/PDF */}
          {document.imagePath.endsWith('.pdf') ? (
            <iframe
              src={document.imagePath}
              className="w-full h-[calc(100vh-12rem)] border border-slate-800 rounded"
              title={`Document: ${document.filename}`}
              style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}
            />
          ) : (
            <img
              src={document.imagePath}
              alt={`Document: ${document.filename}`}
              width={2550}
              height={4200}
              style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}
              className="max-w-none transition-transform"
            />
          )}
        </div>
      </section>

      {/* Right: Tabbed Content */}
      <section className="w-[500px] flex flex-col bg-slate-950">
        {/* Document header */}
        <header className="p-6 border-b border-slate-800">
          <h1 className="text-lg font-mono mb-2 truncate" title={document.filename}>
            {document.filename}
          </h1>
          <div className="flex items-center gap-4 text-sm text-slate-400">
            <time dateTime={document.date || undefined} className="font-mono tabular-nums">
              {formatDate(document.date)}
            </time>
            {document.confidence && (
              <div className="flex items-center gap-1.5">
                <span className="text-xs uppercase tracking-wider">OCR</span>
                <span className="font-mono tabular-nums">{Math.round(document.confidence * 100)}%</span>
              </div>
            )}
          </div>
        </header>

        {/* Tabs */}
        <div role="tablist" className="flex border-b border-slate-800">
          <button
            role="tab"
            aria-selected={activeTab === 'ocr'}
            aria-controls="ocr-panel"
            id="ocr-tab"
            className={`flex-1 px-4 py-3 font-mono text-sm border-b-2 transition-colors
                       focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-inset
                       ${
                         activeTab === 'ocr'
                           ? 'border-blue-500 text-blue-400'
                           : 'border-transparent text-slate-400 hover:text-slate-300'
                       }`}
            onClick={() => setActiveTab('ocr')}
          >
            OCR {languageDisplayName && <span className="text-xs opacity-60">({languageDisplayName})</span>}
          </button>
          {hasTranslation && (
            <button
              role="tab"
              aria-selected={activeTab === 'translated'}
              aria-controls="translated-panel"
              id="translated-tab"
              className={`flex-1 px-4 py-3 font-mono text-sm border-b-2 transition-colors
                         focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-inset
                         ${
                           activeTab === 'translated'
                             ? 'border-blue-500 text-blue-400'
                             : 'border-transparent text-slate-400 hover:text-slate-300'
                         }`}
              onClick={() => setActiveTab('translated')}
            >
              English
            </button>
          )}
          <button
            role="tab"
            aria-selected={activeTab === 'entities'}
            aria-controls="entities-panel"
            id="entities-tab"
            className={`flex-1 px-4 py-3 font-mono text-sm border-b-2 transition-colors
                       focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-inset
                       ${
                         activeTab === 'entities'
                           ? 'border-blue-500 text-blue-400'
                           : 'border-transparent text-slate-400 hover:text-slate-300'
                       }`}
            onClick={() => setActiveTab('entities')}
          >
            Entities ({document.entities.length})
          </button>
        </div>

        {/* Tab panels */}
        <div className="flex-1 overflow-y-auto">
          {/* OCR Panel */}
          {activeTab === 'ocr' && (
            <div
              role="tabpanel"
              id="ocr-panel"
              aria-labelledby="ocr-tab"
              className="p-6"
            >
              <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed text-slate-300">
                {document.ocrText}
              </pre>
            </div>
          )}

          {/* Translated Panel */}
          {activeTab === 'translated' && (
            <div
              role="tabpanel"
              id="translated-panel"
              aria-labelledby="translated-tab"
              className="p-6"
            >
              <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed text-slate-300">
                {document.translatedText}
              </pre>
            </div>
          )}

          {/* Entities Panel */}
          {activeTab === 'entities' && (
            <div
              role="tabpanel"
              id="entities-panel"
              aria-labelledby="entities-tab"
              className="p-6 space-y-6"
            >
              {Object.entries(groupedEntities).map(([type, entities]) => (
                <section key={type}>
                  <h3 className="text-xs uppercase tracking-wider text-slate-500 font-mono mb-3">
                    {type} ({entities.length})
                  </h3>
                  <div className="space-y-2">
                    {entities.map((entity, index) => (
                      <Link
                        key={entity.id}
                        href={`/case/${caseId}/entity/${encodeURIComponent(entity.id)}`}
                        className="block p-3 bg-slate-900 border border-slate-800 rounded
                                   hover:border-slate-700 hover:bg-slate-800/50 transition-colors
                                   focus-visible:ring-2 focus-visible:ring-blue-500 animate-fade-in-up"
                        style={{ animationDelay: `${index * 0.05}s` } as React.CSSProperties}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1 min-w-0">
                            <div className="font-mono text-sm text-slate-100 truncate">
                              {entity.name || entity.id}
                            </div>
                            {/* TODO: Add roleLabel when available */}
                          </div>

                          {/* Verification badge */}
                          <VerificationBadge tier={entity.verification.tier} size="small" />
                        </div>
                      </Link>
                    ))}
                  </div>
                </section>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
