'use client';

import useSWR from 'swr';
import type { GraphData } from '@/lib/types';

interface UseGraphReturn {
  data: GraphData | null;
  isLoading: boolean;
  error: Error | null;
}

// PERFORMANCE: SWR provides automatic request deduplication, caching, and revalidation
const fetcher = (url: string) => fetch(url).then(r => {
  if (!r.ok) throw new Error(`Failed to load case: ${r.status}`);
  return r.json();
});

export function useGraph(caseId: string): UseGraphReturn {
  const { data, error, isLoading } = useSWR<GraphData>(
    `/api/cases/${caseId}/graph`,
    fetcher,
    {
      revalidateOnFocus: false,     // Don't refetch on window focus
      revalidateOnReconnect: false, // Don't refetch on reconnect
      dedupingInterval: 60000,      // Dedupe requests within 1 minute
    }
  );

  return {
    data: data ?? null,
    isLoading,
    error: error ?? null,
  };
}
