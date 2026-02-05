'use client';

import { Bookmark, BookmarkCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useBookmarks } from '@/hooks/use-bookmarks';
import { cn } from '@/lib/utils';

interface BookmarkButtonProps {
  type: 'document' | 'entity';
  id: string;
  className?: string;
}

export function BookmarkButton({ type, id, className }: BookmarkButtonProps) {
  const { isBookmarked, toggleBookmark, isLoaded } = useBookmarks();
  const bookmarked = isBookmarked(type, id);

  return (
    <Button
      variant="ghost"
      size="icon-sm"
      onClick={() => toggleBookmark(type, id)}
      disabled={!isLoaded}
      className={cn(
        'transition-colors',
        bookmarked && 'text-primary hover:text-primary/80',
        className
      )}
      aria-label={bookmarked ? `Remove ${type} from bookmarks` : `Add ${type} to bookmarks`}
      aria-pressed={bookmarked}
    >
      {bookmarked ? (
        <BookmarkCheck className="size-4 fill-current" />
      ) : (
        <Bookmark className="size-4" />
      )}
    </Button>
  );
}
