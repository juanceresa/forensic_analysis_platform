'use client';

import { useState } from 'react';
import Link from 'next/link';
import type { DocumentDetail, DocumentAnalysis } from '@/lib/document-types';
import type { BaseNode } from '@/lib/types';
import { VerificationBadge } from '@/components/shared';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from '@/components/ui/resizable';
import { useIsMobile } from '@/hooks/use-mobile';
import { BookmarkButton } from '@/components/Bookmarks';

interface DocumentViewerProps {
  document: DocumentDetail;
  caseId: string;
}

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

const RELEVANCE_COLORS: Record<string, string> = {
  CRITICAL: 'bg-red-500/20 text-red-400 border-red-500/30',
  HIGH: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  MEDIUM: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  LOW: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
};

const OCR_QUALITY_COLORS: Record<string, string> = {
  EXCELLENT: 'text-green-400',
  GOOD: 'text-blue-400',
  FAIR: 'text-yellow-400',
  POOR: 'text-red-400',
};

function AnalysisContent({ analysis }: { analysis: DocumentAnalysis }) {
  const relevanceColor = RELEVANCE_COLORS[analysis.claim_relevance.level] || RELEVANCE_COLORS.LOW;
  const ocrColor = OCR_QUALITY_COLORS[analysis.quality_notes.ocr_quality] || '';

  return (
    <>
      {/* TIER_3_AI Disclaimer */}
      <div className="rounded border border-amber-500/30 bg-amber-500/10 px-4 py-3">
        <p className="text-xs text-amber-400 font-mono leading-relaxed">
          AI-Generated Analysis — This commentary is produced by AI and has not been verified.
          It may contain errors or misinterpretations. Always refer to the original document text.
        </p>
      </div>

      {/* Document Type */}
      <div>
        <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">Document Type</span>
        <p className="mt-1 text-sm text-foreground">{analysis.document_type}</p>
      </div>

      {/* Executive Summary */}
      <div>
        <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">Executive Summary</span>
        <p className="mt-1 text-sm text-foreground leading-relaxed">{analysis.executive_summary}</p>
      </div>

      {/* Claim Relevance */}
      <div>
        <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">Claim Relevance</span>
        <div className="mt-2 flex items-start gap-3">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded text-xs font-mono font-semibold border ${relevanceColor}`}>
            {analysis.claim_relevance.level}
          </span>
          <p className="text-sm text-muted-foreground leading-relaxed flex-1">
            {analysis.claim_relevance.reasoning}
          </p>
        </div>
      </div>

      {/* Key Facts */}
      {analysis.key_facts.length > 0 && (
        <div>
          <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">Key Facts</span>
          <ul className="mt-2 space-y-1.5">
            {analysis.key_facts.map((fact, i) => (
              <li key={i} className="flex gap-2 text-sm text-foreground">
                <span className="text-muted-foreground shrink-0 mt-0.5">•</span>
                <span className="leading-relaxed">{fact}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Cross-References */}
      {analysis.cross_references.length > 0 && (
        <div>
          <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">Cross-References</span>
          <ul className="mt-2 space-y-1.5">
            {analysis.cross_references.map((ref, i) => (
              <li key={i} className="flex gap-2 text-sm text-foreground">
                <span className="text-muted-foreground shrink-0 mt-0.5">→</span>
                <span className="leading-relaxed">{ref}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Quality Notes */}
      <div>
        <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">Quality Notes</span>
        <div className="mt-2 space-y-2">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">OCR Quality:</span>
            <span className={`font-mono font-semibold ${ocrColor}`}>
              {analysis.quality_notes.ocr_quality}
            </span>
          </div>
          {analysis.quality_notes.missing_information.length > 0 && (
            <div>
              <span className="text-xs text-muted-foreground">Missing Information:</span>
              <ul className="mt-1 space-y-1">
                {analysis.quality_notes.missing_information.map((item, i) => (
                  <li key={i} className="text-sm text-yellow-400/80 flex gap-2">
                    <span className="shrink-0">⚠</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {analysis.quality_notes.verification_needed.length > 0 && (
            <div>
              <span className="text-xs text-muted-foreground">Verification Needed:</span>
              <ul className="mt-1 space-y-1">
                {analysis.quality_notes.verification_needed.map((item, i) => (
                  <li key={i} className="text-sm text-orange-400/80 flex gap-2">
                    <span className="shrink-0">?</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export function DocumentViewer({ document, caseId }: DocumentViewerProps) {
  const [currentPage, setCurrentPage] = useState(0);
  const [showRawOcr, setShowRawOcr] = useState(false);
  const isMobile = useIsMobile();

  const pages = document.pages;
  const totalPages = pages ? pages.length : 1;
  const isMultiPage = totalPages > 1;

  // Current page data
  const currentOcrText = pages ? pages[currentPage]?.ocrText : document.ocrText;
  const currentRawOcrText = pages ? pages[currentPage]?.rawOcrText : document.rawOcrText;
  const currentTranslatedText = pages ? pages[currentPage]?.translatedText : document.translatedText;
  const currentImagePath = pages ? pages[currentPage]?.imagePath : document.imagePath;
  const currentEntities = pages ? pages[currentPage]?.entities : document.entities;

  const hasCleanedText = !!currentRawOcrText;
  const displayOcrText = showRawOcr && hasCleanedText ? currentRawOcrText : currentOcrText;

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


  // Document image section (reused in both layouts)
  const documentImageSection = (
    <section
      className={`bg-[var(--card)] overflow-auto flex flex-col ${isMobile ? 'h-[50vh]' : 'h-full'}`}
      aria-label="Document image"
    >
      <div className="flex flex-col flex-1 min-h-0 p-2">
        {/* Document image/PDF — browser handles zoom natively */}
        <iframe
          key={currentImagePath}
          src={currentImagePath}
          className="w-full flex-1 border border-[var(--border)] rounded"
          title={`Document: ${document.filename}${isMultiPage ? ` - Page ${currentPage + 1}` : ''}`}
        />
      </div>

      {/* Page navigation bar at bottom of image pane */}
      {isMultiPage && (
        <nav className="flex items-center justify-center gap-3 px-4 py-3 bg-background border-t border-[var(--border)]">
          <Button
            variant="outline"
            size="icon"
            aria-label="Previous page"
            disabled={currentPage === 0}
            onClick={() => goToPage(currentPage - 1)}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Button>
          <span className="font-mono text-sm text-muted-foreground tabular-nums min-w-[5rem] text-center">
            {currentPage + 1} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="icon"
            aria-label="Next page"
            disabled={currentPage === totalPages - 1}
            onClick={() => goToPage(currentPage + 1)}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Button>
        </nav>
      )}
    </section>
  );

  // Tabbed content section (reused in both layouts)
  const tabbedContentSection = (
    <section className={`flex flex-col bg-background overflow-hidden ${isMobile ? 'flex-1' : 'h-full'}`}>
      {/* Document header */}
      <header className="p-4 sm:p-6">
        <div className="flex items-start justify-between gap-2 mb-2">
          <h1 className="text-base sm:text-lg font-mono truncate text-foreground" title={document.filename}>
            {document.filename}
          </h1>
          <BookmarkButton type="document" id={document.id} />
        </div>
        <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-sm text-muted-foreground">
          <time dateTime={document.date || undefined} className="font-mono tabular-nums">
            {formatDate(document.date)}
          </time>
          {document.confidence && (
            <Badge variant="outline" className="font-mono tabular-nums">
              {Math.round(document.confidence * 100)}% OCR
            </Badge>
          )}
          {isMultiPage && (
            <Badge variant="secondary" className="font-mono tabular-nums">
              {totalPages} pages
            </Badge>
          )}
        </div>
      </header>

      <Separator />

      {/* Tabs */}
      <Tabs defaultValue="ocr" className="flex-1 flex flex-col min-h-0">
        <TabsList variant="line" className="w-full justify-start px-4 sm:px-6 pt-2 overflow-x-auto scrollbar-hide">
          <TabsTrigger value="ocr" className="font-mono text-sm shrink-0">
            OCR {languageDisplayName && <span className="text-xs opacity-60">({languageDisplayName})</span>}
          </TabsTrigger>
          {hasTranslation && (
            <TabsTrigger value="translated" className="font-mono text-sm shrink-0">
              English
            </TabsTrigger>
          )}
          <TabsTrigger value="entities" className="font-mono text-sm shrink-0">
            Entities ({(currentEntities || []).length})
          </TabsTrigger>
          {document.analysis && (
            <TabsTrigger value="analysis" className="font-mono text-sm shrink-0">
              Analysis
            </TabsTrigger>
          )}
        </TabsList>

        {/* OCR Panel */}
        <TabsContent value="ocr" className="flex-1 min-h-0 flex flex-col">
          {hasCleanedText && (
            <div className="flex items-center gap-2 px-4 sm:px-6 pt-3 pb-1">
              <button
                type="button"
                onClick={() => setShowRawOcr(!showRawOcr)}
                className="text-xs font-mono px-2 py-1 rounded border border-[var(--border)] text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
              >
                {showRawOcr ? 'Show Cleaned' : 'Show Raw OCR'}
              </button>
              {showRawOcr && (
                <span className="text-xs text-muted-foreground/60">Unprocessed OCR output</span>
              )}
            </div>
          )}
          <ScrollArea className="flex-1 min-h-0">
            <div className="p-4 sm:p-6 max-w-prose">
              {(displayOcrText || '').split(/\n\n+/).map((paragraph, i) => (
                <p key={i} className="mb-4 text-[15px] leading-7 text-foreground">
                  {paragraph}
                </p>
              ))}
            </div>
          </ScrollArea>
        </TabsContent>

        {/* Translated Panel */}
        {hasTranslation && (
          <TabsContent value="translated" className="flex-1 min-h-0">
            <ScrollArea className="h-full">
              <div className="p-4 sm:p-6 max-w-prose">
                {currentTranslatedText ? (
                  (currentTranslatedText || '').split(/\n\n+/).map((paragraph, i) => (
                    <p key={i} className="mb-4 text-[15px] leading-7 text-foreground">
                      {paragraph}
                    </p>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground/60">
                    No translation available for this page.
                  </p>
                )}
              </div>
            </ScrollArea>
          </TabsContent>
        )}

        {/* Entities Panel */}
        <TabsContent value="entities" className="flex-1 min-h-0">
          <ScrollArea className="h-full">
            <div className="p-4 sm:p-6 space-y-6">
              {Object.entries(groupedEntities).map(([type, entities]) => (
                <section key={type}>
                  <div className="flex items-center gap-2 mb-3">
                    <Badge variant="outline" className="text-xs uppercase tracking-wider font-mono">
                      {type}
                    </Badge>
                    <span className="text-xs text-muted-foreground tabular-nums">
                      {entities.length}
                    </span>
                  </div>
                  <div className="space-y-2">
                    {entities.map((entity, index) => (
                      <Link
                        key={entity.id}
                        href={`/case/${caseId}/entity/${encodeURIComponent(entity.id)}`}
                        className="block p-3 bg-[var(--card)] border border-[var(--border)] rounded
                                   hover:border-primary/30 hover:bg-muted/50 transition-colors
                                   focus-visible:ring-2 focus-visible:ring-ring animate-fade-in-up"
                        style={{ animationDelay: `${index * 0.05}s` } as React.CSSProperties}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1 min-w-0">
                            <div className="font-mono text-sm text-foreground truncate">
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
                <p className="text-sm text-muted-foreground/60 font-mono">
                  No entities extracted from this page.
                </p>
              )}
            </div>
          </ScrollArea>
        </TabsContent>

        {/* Analysis Panel */}
        {document.analysis && (
          <TabsContent value="analysis" className="flex-1 min-h-0">
            <ScrollArea className="h-full">
              <div className="p-4 sm:p-6 space-y-6">
                <AnalysisContent analysis={document.analysis} />
              </div>
            </ScrollArea>
          </TabsContent>
        )}
      </Tabs>
    </section>
  );

  // Mobile: vertical stack layout
  if (isMobile) {
    return (
      <div className="h-full flex flex-col overflow-hidden">
        {documentImageSection}
        {tabbedContentSection}
      </div>
    );
  }

  // Desktop: resizable horizontal panels
  return (
    <ResizablePanelGroup orientation="horizontal" className="h-full">
      {/* Left: Original Image */}
      <ResizablePanel defaultSize="55%" minSize="30%">
        {documentImageSection}
      </ResizablePanel>

      <ResizableHandle withHandle />

      {/* Right: Tabbed Content */}
      <ResizablePanel defaultSize="45%" minSize="30%" collapsible collapsedSize="0%">
        {tabbedContentSection}
      </ResizablePanel>
    </ResizablePanelGroup>
  );
}
