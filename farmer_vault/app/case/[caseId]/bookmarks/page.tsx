'use client';

import { use, useEffect, useState } from 'react';
import Link from 'next/link';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { BookmarkButton } from '@/components/Bookmarks';
import { useBookmarks } from '@/hooks/use-bookmarks';
import { FileText, Users, Bookmark } from 'lucide-react';

interface BookmarksPageProps {
  params: Promise<{ caseId: string }>;
}

interface BookmarkedDocument {
  id: string;
  filename: string;
  date: string | null;
}

interface BookmarkedEntity {
  id: string;
  name: string;
  entity_type: string;
}

export default function BookmarksPage({ params }: BookmarksPageProps) {
  const { caseId } = use(params);
  const { bookmarks, isLoaded } = useBookmarks();
  const [documents, setDocuments] = useState<BookmarkedDocument[]>([]);
  const [entities, setEntities] = useState<BookmarkedEntity[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch bookmarked items metadata
  useEffect(() => {
    if (!isLoaded) return;

    async function fetchBookmarkedItems() {
      setLoading(true);

      // Fetch documents
      const docPromises = bookmarks.documents.map(async (id) => {
        try {
          const res = await fetch(`/api/cases/${caseId}/document/${encodeURIComponent(id)}`);
          if (!res.ok) return null;
          const data = await res.json();
          return { id, filename: data.filename, date: data.date };
        } catch {
          return null;
        }
      });

      // Fetch entities
      const entityPromises = bookmarks.entities.map(async (id) => {
        try {
          const res = await fetch(`/api/cases/${caseId}/entity/${encodeURIComponent(id)}`);
          if (!res.ok) return null;
          const data = await res.json();
          return { id, name: data.entity.name || id, entity_type: data.entity.entity_type };
        } catch {
          return null;
        }
      });

      const [docResults, entityResults] = await Promise.all([
        Promise.all(docPromises),
        Promise.all(entityPromises),
      ]);

      setDocuments(docResults.filter((d): d is BookmarkedDocument => d !== null));
      setEntities(entityResults.filter((e): e is BookmarkedEntity => e !== null));
      setLoading(false);
    }

    fetchBookmarkedItems();
  }, [caseId, bookmarks, isLoaded]);

  const totalBookmarks = bookmarks.documents.length + bookmarks.entities.length;

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8">
      <header className="mb-6 sm:mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Bookmark className="size-6 text-primary" />
          <h1 className="text-2xl sm:text-3xl font-mono text-foreground">Bookmarks</h1>
        </div>
        <p className="text-muted-foreground text-sm font-mono">
          {totalBookmarks} bookmarked item{totalBookmarks !== 1 ? 's' : ''}
        </p>
      </header>

      <Tabs defaultValue="documents" className="w-full">
        <TabsList variant="line" className="w-full justify-start mb-6">
          <TabsTrigger value="documents" className="font-mono text-sm flex items-center gap-2">
            <FileText className="size-4" />
            Documents ({bookmarks.documents.length})
          </TabsTrigger>
          <TabsTrigger value="entities" className="font-mono text-sm flex items-center gap-2">
            <Users className="size-4" />
            Entities ({bookmarks.entities.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="documents">
          {loading ? (
            <div className="p-8 text-center">
              <p className="text-muted-foreground font-mono text-sm">Loading...</p>
            </div>
          ) : documents.length === 0 ? (
            <div className="p-8 bg-[var(--card)] border border-[var(--border)] border-dashed rounded text-center">
              <FileText className="size-8 mx-auto mb-3 text-muted-foreground/50" />
              <p className="text-muted-foreground font-mono text-sm">No bookmarked documents</p>
              <p className="text-muted-foreground/60 font-mono text-xs mt-1">
                Click the bookmark icon on any document to save it here
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {documents.map((doc, index) => (
                <div
                  key={doc.id}
                  className="flex items-center gap-3 p-4 bg-[var(--card)] border border-[var(--border)] rounded
                             hover:border-primary/30 hover:bg-muted/50 transition-colors animate-fade-in-up"
                  style={{ animationDelay: `${index * 0.05}s` } as React.CSSProperties}
                >
                  <Link
                    href={`/case/${caseId}/document/${encodeURIComponent(doc.id)}`}
                    className="flex-1 min-w-0 focus-visible:ring-2 focus-visible:ring-ring rounded"
                  >
                    <h3 className="font-mono text-foreground truncate">{doc.filename}</h3>
                    {doc.date && (
                      <p className="text-xs text-muted-foreground font-mono tabular-nums mt-1">
                        {new Date(doc.date).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })}
                      </p>
                    )}
                  </Link>
                  <BookmarkButton type="document" id={doc.id} />
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="entities">
          {loading ? (
            <div className="p-8 text-center">
              <p className="text-muted-foreground font-mono text-sm">Loading...</p>
            </div>
          ) : entities.length === 0 ? (
            <div className="p-8 bg-[var(--card)] border border-[var(--border)] border-dashed rounded text-center">
              <Users className="size-8 mx-auto mb-3 text-muted-foreground/50" />
              <p className="text-muted-foreground font-mono text-sm">No bookmarked entities</p>
              <p className="text-muted-foreground/60 font-mono text-xs mt-1">
                Click the bookmark icon on any entity to save it here
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {entities.map((entity, index) => (
                <div
                  key={entity.id}
                  className="flex items-center gap-3 p-4 bg-[var(--card)] border border-[var(--border)] rounded
                             hover:border-primary/30 hover:bg-muted/50 transition-colors animate-fade-in-up"
                  style={{ animationDelay: `${index * 0.05}s` } as React.CSSProperties}
                >
                  <Link
                    href={`/case/${caseId}/entity/${encodeURIComponent(entity.id)}`}
                    className="flex-1 min-w-0 focus-visible:ring-2 focus-visible:ring-ring rounded"
                  >
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 bg-muted rounded text-xs uppercase tracking-wider text-muted-foreground font-mono">
                        {entity.entity_type}
                      </span>
                    </div>
                    <h3 className="font-mono text-foreground truncate mt-1">{entity.name}</h3>
                  </Link>
                  <BookmarkButton type="entity" id={entity.id} />
                </div>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
