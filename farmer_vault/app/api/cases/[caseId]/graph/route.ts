import { NextRequest, NextResponse } from 'next/server';
import { cache } from 'react';
import { readFile } from 'fs/promises';
import { join } from 'path';
import type { GraphData } from '@/lib/types';

// PERFORMANCE: React.cache() ensures getGraphData is called only once per request
// even if multiple components need it (eliminates waterfalls)
export const getGraphData = cache(async (caseId: string): Promise<GraphData> => {
  // Validate caseId format
  if (!/^[A-Z0-9-]+$/.test(caseId)) {
    throw new Error('Invalid case ID format');
  }

  // Read from Factory output (air gap maintained)
  const graphPath = join(
    process.cwd(),
    '..',
    'cases',
    caseId,
    'output',
    'graph_data.json'
  );

  const graphData = await readFile(graphPath, 'utf-8');
  return JSON.parse(graphData);
});

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ caseId: string }> }
) {
  try {
    const { caseId } = await params;
    const data = await getGraphData(caseId);
    return NextResponse.json(data);
  } catch (error: any) {
    if (error.code === 'ENOENT') {
      return NextResponse.json(
        { error: 'Case not found' },
        { status: 404 }
      );
    }

    console.error('Graph load error:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to load graph data' },
      { status: 500 }
    );
  }
}
