/**
 * useNarrative Hook
 *
 * Custom React hook for fetching and managing narrative generation.
 * Handles API calls, loading states, error handling, and session tracking.
 */

import { useState, useCallback } from 'react';

// Types matching backend models
interface EvidenceCitation {
  citation_number: number;
  doc_id: string;
  quote: string;
  confidence: number;
  verification_tier: string;
}

interface EventHighlight {
  event_type: 'CONFISCATED' | 'SOLD' | 'INHERITED';
  date: string | null;
  summary: string;
  parties_involved: string[];
  location: string | null;
  document_ids: string[];
}

interface NarrativeResult {
  focal_entity_id: string;
  focal_entity_name: string;
  focal_entity_type: string;
  constellation_size: number;
  model_used: string;
  main_narrative: string;
  facts: EvidenceCitation[];
  total_documents: number;
  total_citations: number;
  generation_cost: number;
  from_cache: boolean;
  highlighted_events: EventHighlight[];
  session_total_cost?: number;
}

interface NarrativeError {
  type: 'validation' | 'cost_limit' | 'insufficient_data' | 'network' | 'unknown';
  message: string;
}

interface UseNarrativeReturn {
  narrative: NarrativeResult | null;
  loading: boolean;
  error: NarrativeError | null;
  generateNarrative: (caseId: string, nodeId: string) => Promise<void>;
  clearNarrative: () => void;
}

// Generate a session ID for cost tracking
const getSessionId = (): string => {
  const storageKey = 'narrative_session_id';
  let sessionId = sessionStorage.getItem(storageKey);

  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    sessionStorage.setItem(storageKey, sessionId);
  }

  return sessionId;
};

export const useNarrative = (): UseNarrativeReturn => {
  const [narrative, setNarrative] = useState<NarrativeResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<NarrativeError | null>(null);

  const generateNarrative = useCallback(async (caseId: string, nodeId: string): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      const sessionId = getSessionId();

      const response = await fetch(`/api/cases/${caseId}/narrative`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          clicked_node_id: nodeId,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        // Parse error response
        const errorData = await response.json().catch(() => null);

        // Map HTTP status to error type
        let errorType: NarrativeError['type'] = 'unknown';
        let errorMessage = errorData?.detail || 'Failed to generate narrative';

        if (response.status === 400) {
          errorType = 'validation';
        } else if (response.status === 429) {
          errorType = 'cost_limit';
          errorMessage = errorData?.detail || 'Session cost limit exceeded';
        } else if (response.status === 404) {
          errorType = 'insufficient_data';
          errorMessage = errorData?.detail || 'Entity not found in graph';
        } else if (response.status >= 500) {
          errorType = 'network';
          errorMessage = 'Server error - please try again';
        }

        throw new Error(JSON.stringify({ type: errorType, message: errorMessage }));
      }

      const data: NarrativeResult = await response.json();
      setNarrative(data);
    } catch (err) {
      // Parse error
      let narrativeError: NarrativeError;

      if (err instanceof Error) {
        try {
          // Try to parse structured error
          const parsed = JSON.parse(err.message);
          narrativeError = parsed;
        } catch {
          // Network or other error
          narrativeError = {
            type: 'network',
            message: err.message || 'Network error - please check your connection',
          };
        }
      } else {
        narrativeError = {
          type: 'unknown',
          message: 'An unexpected error occurred',
        };
      }

      setError(narrativeError);
      setNarrative(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const clearNarrative = useCallback((): void => {
    setNarrative(null);
    setError(null);
  }, []);

  return {
    narrative,
    loading,
    error: error ? error : null,
    generateNarrative,
    clearNarrative,
  };
};
