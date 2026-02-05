'use client';

import { useState, useEffect, useCallback } from 'react';

interface Bookmarks {
  documents: string[];
  entities: string[];
}

const STORAGE_KEY = 'civictable-bookmarks';

function getStoredBookmarks(): Bookmarks {
  if (typeof window === 'undefined') {
    return { documents: [], entities: [] };
  }
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      return {
        documents: Array.isArray(parsed.documents) ? parsed.documents : [],
        entities: Array.isArray(parsed.entities) ? parsed.entities : [],
      };
    }
  } catch {
    // Invalid JSON or localStorage not available
  }
  return { documents: [], entities: [] };
}

function setStoredBookmarks(bookmarks: Bookmarks): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(bookmarks));
  } catch {
    // localStorage full or not available
  }
}

export function useBookmarks() {
  const [bookmarks, setBookmarks] = useState<Bookmarks>({ documents: [], entities: [] });
  const [isLoaded, setIsLoaded] = useState(false);

  // Load bookmarks from localStorage on mount
  useEffect(() => {
    setBookmarks(getStoredBookmarks());
    setIsLoaded(true);
  }, []);

  // Sync to localStorage when bookmarks change
  useEffect(() => {
    if (isLoaded) {
      setStoredBookmarks(bookmarks);
    }
  }, [bookmarks, isLoaded]);

  const toggleBookmark = useCallback((type: 'document' | 'entity', id: string) => {
    setBookmarks((prev) => {
      const key = type === 'document' ? 'documents' : 'entities';
      const list = prev[key];
      const isBookmarked = list.includes(id);

      return {
        ...prev,
        [key]: isBookmarked ? list.filter((item) => item !== id) : [...list, id],
      };
    });
  }, []);

  const isBookmarked = useCallback(
    (type: 'document' | 'entity', id: string): boolean => {
      const key = type === 'document' ? 'documents' : 'entities';
      return bookmarks[key].includes(id);
    },
    [bookmarks]
  );

  const getBookmarks = useCallback(() => bookmarks, [bookmarks]);

  return {
    bookmarks,
    toggleBookmark,
    isBookmarked,
    getBookmarks,
    isLoaded,
  };
}
