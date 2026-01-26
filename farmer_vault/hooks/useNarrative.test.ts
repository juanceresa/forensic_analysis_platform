import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useNarrative } from './useNarrative';
import type { NarrativeResult } from '@/lib/types';

// Mock fetch
global.fetch = vi.fn();

describe('useNarrative', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockNarrative: NarrativeResult = {
    focal_entity_id: 'node-123',
    focal_entity_name: 'Mario Ceresa',
    focal_entity_type: 'PERSON',
    constellation_size: 5,
    model_used: 'claude-3-haiku',
    main_narrative: 'Test narrative about Mario Ceresa.',
    facts: [
      {
        claim_text: 'Mario Ceresa owned property in Havana',
        citation_number: 1,
        evidence: [
          {
            doc_id: 'DOC-001',
            page: 1,
            quote: 'Mario Ceresa, propietario',
            confidence: 0.95,
            verification_tier: 'TIER_2_ANALYST',
          },
        ],
      },
    ],
    highlighted_events: [],
    total_documents: 3,
    total_citations: 1,
    generation_cost: 0.05,
    from_cache: false,
  };

  it('generates narrative successfully', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => mockNarrative,
    } as Response);

    const { result } = renderHook(() => useNarrative());

    expect(result.current.loading).toBe(false);
    expect(result.current.narrative).toBe(null);
    expect(result.current.error).toBe(null);

    // Generate narrative
    await waitFor(async () => {
      await result.current.generateNarrative('TEST-CASE', 'node-123', 'session-1');
    });

    await waitFor(() => {
      expect(result.current.narrative).toEqual(mockNarrative);
    });

    expect(result.current.error).toBe(null);
    expect(fetch).toHaveBeenCalledWith('/api/cases/TEST-CASE/narrative', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        clicked_node_id: 'node-123',
        session_id: 'session-1',
      }),
    });
  });

  it('caches narrative results', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => mockNarrative,
    } as Response);

    const { result } = renderHook(() => useNarrative());

    // First call - should fetch
    await waitFor(async () => {
      await result.current.generateNarrative('TEST-CASE', 'node-123-cache', 'session-1');
    });

    await waitFor(() => {
      expect(result.current.narrative).toEqual(mockNarrative);
    });

    const firstCallCount = vi.mocked(fetch).mock.calls.length;

    // Second call with same params - should use cache
    await waitFor(async () => {
      await result.current.generateNarrative('TEST-CASE', 'node-123-cache', 'session-2');
    });

    // Should not make another fetch call
    expect(vi.mocked(fetch).mock.calls.length).toBe(firstCallCount);
    expect(result.current.narrative).toEqual(mockNarrative);
  });

  it('handles validation errors (400)', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ error: 'Invalid request' }),
    } as Response);

    const { result } = renderHook(() => useNarrative());

    await waitFor(async () => {
      await result.current.generateNarrative('TEST-CASE', 'node-validation', 'session-1');
    });

    await waitFor(() => {
      expect(result.current.error).toEqual({
        type: 'validation',
        message: 'Invalid request',
      });
    });

    expect(result.current.narrative).toBe(null);
  });

  it('handles cost limit errors (402)', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 402,
      json: async () => ({ error: 'Cost limit exceeded' }),
    } as Response);

    const { result } = renderHook(() => useNarrative());

    await waitFor(async () => {
      await result.current.generateNarrative('TEST-CASE', 'node-cost-limit', 'session-1');
    });

    await waitFor(() => {
      expect(result.current.error).toEqual({
        type: 'cost_limit',
        message: 'Cost limit exceeded',
      });
    });
  });

  it('handles insufficient data errors (422)', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({ error: 'Not enough documents' }),
    } as Response);

    const { result } = renderHook(() => useNarrative());

    await waitFor(async () => {
      await result.current.generateNarrative('TEST-CASE', 'node-insufficient', 'session-1');
    });

    await waitFor(() => {
      expect(result.current.error).toEqual({
        type: 'insufficient_data',
        message: 'Not enough documents',
      });
    });
  });

  it('handles server errors (500)', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ error: 'Server error' }),
    } as Response);

    const { result } = renderHook(() => useNarrative());

    await waitFor(async () => {
      await result.current.generateNarrative('TEST-CASE', 'node-server-error', 'session-1');
    });

    await waitFor(() => {
      expect(result.current.error).toEqual({
        type: 'network',
        message: 'Server error',
      });
    });
  });

  it('handles network errors', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('Network failure'));

    const { result } = renderHook(() => useNarrative());

    await waitFor(async () => {
      await result.current.generateNarrative('TEST-CASE', 'node-network-fail', 'session-1');
    });

    await waitFor(() => {
      expect(result.current.error).toEqual({
        type: 'network',
        message: 'Network failure',
      });
    });
  });

  it('clears narrative and error', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => mockNarrative,
    } as Response);

    const { result } = renderHook(() => useNarrative());

    await waitFor(async () => {
      await result.current.generateNarrative('TEST-CASE', 'node-clear-test', 'session-1');
    });

    await waitFor(() => {
      expect(result.current.narrative).toEqual(mockNarrative);
    });

    await waitFor(() => {
      result.current.clearNarrative();
    });

    await waitFor(() => {
      expect(result.current.narrative).toBe(null);
      expect(result.current.error).toBe(null);
    });
  });
});
