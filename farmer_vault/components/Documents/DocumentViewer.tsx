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
  const [currentPage, setCurrentPage] = useState(0);

  const pages = document.pages;
  const totalPages = pages ? pages.length : 1;
  const isMultiPage = totalPages > 1;

  // Current page data
  const currentOcrText = pages ? pages[currentPage]?.ocrText : document.ocrText;
  const currentTranslatedText = pages ? pages[currentPage]?.translatedText : document.translatedText;
  const currentImagePath = pages ? pages[currentPage]?.imagePath : document.imagePath;
  const currentEntities = pages ? pages[currentPage]?.entities : document.entities;

  const languageDisplayName = document.detectedLanguage
    ? LANGUAGE_NAMES[document.detectedLanguage] || document.detectedLanguage.toUpperCase()
    : null;

  const hasTranslation = pages
    ? pages.some(p => !!p.translatedText)
    : !!document.translatedText;

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

  const groupedEntities = groupEntitiesByType(currentEntities || []);

  const goToPage = (page: number) => {
    if (page >= 0 && page < totalPages) {
      setCurrentPage(page);
    }
  };

  return (
    <div className="h-full flex">
      {/* Left: Original Image */}
      <section
        className="flex-1 bg-slate-900 border-r border-slate-800 overflow-auto flex flex-col"
        aria-label="Document image"
      >
        <div className="flex flex-col flex-1 min-h-0 p-2">
          {/* Document image/PDF — browser handles zoom natively */}
          <iframe
            key={currentImagePath}
            src={currentImagePath}
            className="w-full flex-1 border border-slate-800 rounded"
            title={`Document: ${document.filename}${isMultiPage ? ` - Page ${currentPage + 1}` : ''}`}
          />
        </div>

        {/* Page navigation bar at bottom of image pane */}
        {isMultiPage && (
          <nav className="flex items-center justify-center gap-3 px-4 py-3 bg-slate-950 border-t border-slate-800">
            <button
              aria-label="Previous page"
              disabled={currentPage === 0}
              onClick={() => goToPage(currentPage - 1)}
              className="p-2 rounded bg-slate-800 hover:bg-slate-700 transition-colors
                         disabled:opacity-30 disabled:cursor-not-allowed
                         focus-visible:ring-2 focus-visible:ring-blue-500"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <span className="font-mono text-sm text-slate-300 tabular-nums min-w-[5rem] text-center">
              {currentPage + 1} / {totalPages}
            </span>
            <button
              aria-label="Next page"
              disabled={currentPage === totalPages - 1}
              onClick={() => goToPage(currentPage + 1)}
              className="p-2 rounded bg-slate-800 hover:bg-slate-700 transition-colors
                         disabled:opacity-30 disabled:cursor-not-allowed
                         focus-visible:ring-2 focus-visible:ring-blue-500"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </nav>
        )}
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
            {isMultiPage && (
              <div className="flex items-center gap-1.5">
                <span className="text-xs uppercase tracking-wider">Pages</span>
                <span className="font-mono tabular-nums">{totalPages}</span>
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
            Entities ({(currentEntities || []).length})
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
                {currentOcrText}
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
              {currentTranslatedText ? (
                <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed text-slate-300">
                  {currentTranslatedText}
                </pre>
              ) : (
                <p className="text-sm text-slate-500 font-mono">
                  No translation available for this page.
                </p>
              )}
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
                          </div>
                          <VerificationBadge tier={entity.verification.tier} size="small" />
                        </div>
                      </Link>
                    ))}
                  </div>
                </section>
              ))}
              {Object.keys(groupedEntities).length === 0 && (
                <p className="text-sm text-slate-500 font-mono">
                  No entities extracted from this page.
                </p>
              )}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
