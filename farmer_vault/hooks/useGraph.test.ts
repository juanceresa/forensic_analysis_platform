import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useGraph } from './useGraph';
import type { GraphData } from '@/lib/types';

// Mock fetch
global.fetch = vi.fn();

describe('useGraph', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockGraphData: GraphData = {
    metadata: {
      case_id: 'TEST-CASE',
      created_at: '2025-01-25',
      updated_at: '2025-01-25',
      factory_version: '1.0.0',
      entity_count: 10,
      relation_count: 5,
      document_count: 3,
    },
    nodes: [
      {
        id: 'node-1',
        entity_type: 'PERSON',
        name: 'Mario Ceresa',
        verification: {
          tier: 'TIER_2_ANALYST',
          confidence: 0.95,
        },
        extracted_from: 'DOC-001',
      },
    ],
    links: [],
  };

  it('fetches graph data successfully', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => mockGraphData,
    } as Response);

    const { result } = renderHook(() => useGraph('TEST-CASE'));

    expect(result.current.isLoading).toBe(true);
    expect(result.current.data).toBe(null);
    expect(result.current.error).toBe(null);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockGraphData);
    expect(result.current.error).toBe(null);
    expect(fetch).toHaveBeenCalledWith('/api/cases/TEST-CASE/graph');
  });

  it('handles fetch errors', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 404,
    } as Response);

    const { result } = renderHook(() => useGraph('MISSING-CASE'));

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toBe(null);
    expect(result.current.error).toBeTruthy();
    expect(result.current.error?.message).toContain('Failed to load case');
  });

  it('handles network errors', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('Network error'));

    // Use different case ID to avoid SWR cache collision
    const { result } = renderHook(() => useGraph('NETWORK-ERROR-CASE'));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toBe(null);
    expect(result.current.error).toBeTruthy();
  });

  it('does not refetch on window focus', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => mockGraphData,
    } as Response);

    const { result } = renderHook(() => useGraph('TEST-CASE'));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const callCount = vi.mocked(fetch).mock.calls.length;

    // Simulate window focus (SWR should not refetch due to config)
    window.dispatchEvent(new Event('focus'));

    // Wait a bit to ensure no additional fetch
    await new Promise(resolve => setTimeout(resolve, 100));

    expect(vi.mocked(fetch).mock.calls.length).toBe(callCount);
  });
});
