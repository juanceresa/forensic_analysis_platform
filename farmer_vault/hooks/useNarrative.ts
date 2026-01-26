'use client';

import { useState, useCallback } from 'react';
import type { NarrativeResult, NarrativeError } from '@/lib/types';

interface UseNarrativeReturn {
  narrative: NarrativeResult | null;
  loading: boolean;
  error: NarrativeError | null;
  generateNarrative: (caseId: string, nodeId: string, sessionId: string) => Promise<void>;
  clearNarrative: () => void;
}

// PERFORMANCE: Session-level cache to avoid re-generating identical narratives
const narrativeCache = new Map<string, NarrativeResult>();

export function useNarrative(): UseNarrativeReturn {
  const [narrative, setNarrative] = useState<NarrativeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<NarrativeError | null>(null);

  const generateNarrative = useCallback(
    async (caseId: string, nodeId: string, sessionId: string) => {
      const cacheKey = `${caseId}:${nodeId}`;

      // Check cache first
      if (narrativeCache.has(cacheKey)) {
        setNarrative(narrativeCache.get(cacheKey)!);
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/cases/${caseId}/narrative`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            clicked_node_id: nodeId,
            session_id: sessionId,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => null);
          let errorType: NarrativeError['type'] = 'unknown';
          let errorMessage = errorData?.error || 'Failed to generate narrative';

          if (response.status === 400) errorType = 'validation';
          else if (response.status === 402) errorType = 'cost_limit';
          else if (response.status === 422) errorType = 'insufficient_data';
          else if (response.status >= 500) errorType = 'network';

          throw { type: errorType, message: errorMessage };
        }

        const data = await response.json();

        // Cache the result
        narrativeCache.set(cacheKey, data);
        setNarrative(data);
      } catch (err: any) {
        const narrativeError: NarrativeError = err.type
          ? err
          : { type: 'network', message: err.message || 'Network error' };
        setError(narrativeError);
        setNarrative(null);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const clearNarrative = useCallback(() => {
    setNarrative(null);
    setError(null);
  }, []);

  return { narrative, loading, error, generateNarrative, clearNarrative };
}
