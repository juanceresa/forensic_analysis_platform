'use client';

import { useState } from 'react';
import Link from 'next/link';
import type { DocumentDetail } from '@/lib/document-types';
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

export function DocumentViewer({ document, caseId }: DocumentViewerProps) {
  const [currentPage, setCurrentPage] = useState(0);
  const isMobile = useIsMobile();

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
        <h1 className="text-base sm:text-lg font-mono mb-2 truncate text-foreground" title={document.filename}>
          {document.filename}
        </h1>
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
        <TabsList variant="line" className="w-full justify-start px-4 sm:px-6 pt-2 overflow-x-auto">
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
        </TabsList>

        {/* OCR Panel */}
        <TabsContent value="ocr" className="flex-1 min-h-0">
          <ScrollArea className="h-full">
            <div className="p-4 sm:p-6">
              <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed text-muted-foreground">
                {currentOcrText}
              </pre>
            </div>
          </ScrollArea>
        </TabsContent>

        {/* Translated Panel */}
        {hasTranslation && (
          <TabsContent value="translated" className="flex-1 min-h-0">
            <ScrollArea className="h-full">
              <div className="p-4 sm:p-6">
                {currentTranslatedText ? (
                  <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed text-muted-foreground">
                    {currentTranslatedText}
                  </pre>
                ) : (
                  <p className="text-sm text-muted-foreground/60 font-mono">
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
