import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import { join } from 'path';
import type { NarrativeResult, NarrativeError } from '@/lib/types';

const CASE_ID_PATTERN = /^[A-Za-z0-9_-]+$/;
// Node IDs can contain spaces, periods, alphanumerics, underscores, and hyphens
const NODE_ID_PATTERN = /^[A-Za-z0-9_. -]+$/;
const SESSION_ID_PATTERN = /^[A-Za-z0-9_-]+$/;

const STATUS_BY_TYPE: Record<string, number> = {
  cost_limit: 402,
  insufficient_data: 422,
  validation: 400,
  unknown: 500,
};

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ caseId: string }> }
) {
  try {
    const { caseId } = await params;
    const body = await request.json();
    const { clicked_node_id, session_id, max_cost } = body;

    // Validate caseId to prevent path traversal and injection
    if (!CASE_ID_PATTERN.test(caseId)) {
      return NextResponse.json({ error: 'Invalid caseId' }, { status: 400 });
    }

    // Validate required fields
    if (!clicked_node_id || !session_id) {
      return NextResponse.json(
        { error: 'Missing clicked_node_id or session_id' },
        { status: 400 }
      );
    }

    // Validate clicked_node_id format
    if (!NODE_ID_PATTERN.test(clicked_node_id)) {
      return NextResponse.json({ error: 'Invalid clicked_node_id' }, { status: 400 });
    }

    // Validate session_id format
    if (!SESSION_ID_PATTERN.test(session_id)) {
      return NextResponse.json({ error: 'Invalid session_id' }, { status: 400 });
    }

    // Validate max_cost if provided
    if (max_cost !== undefined && (typeof max_cost !== 'number' || max_cost < 0 || max_cost > 100)) {
      return NextResponse.json({ error: 'Invalid max_cost' }, { status: 400 });
    }

    // Call Python script
    const result = await callPythonNarrativeAPI({
      caseId,
      clickedNodeId: clicked_node_id,
      sessionId: session_id,
      maxCost: max_cost ?? 1.0,
    });

    return NextResponse.json(result);
  } catch (error: any) {
    console.error('Narrative generation error:', error);

    const message = error.message || 'Unknown error';

    // Parse JSON error payload if present
    let errorType = 'unknown';
    let errorPayload: NarrativeError | null = null;
    try {
      errorPayload = JSON.parse(message);
      errorType = errorPayload?.type || errorType;
    } catch {
      if (message.includes('cost_limit')) errorType = 'cost_limit';
      if (message.includes('insufficient_data')) errorType = 'insufficient_data';
      if (message.includes('validation')) errorType = 'validation';
    }

    const status = STATUS_BY_TYPE[errorType] ?? 500;

    return NextResponse.json(
      errorPayload ?? { error: message, type: errorType },
      { status }
    );
  }
}

async function callPythonNarrativeAPI(params: {
  caseId: string;
  clickedNodeId: string;
  sessionId: string;
  maxCost: number;
}): Promise<NarrativeResult> {
  return new Promise((resolve, reject) => {
    const scriptPath = join(
      process.cwd(),
      '..',
      'farmer_factory',
      'scripts',
      'generate_narrative.py'
    );

    const proc = spawn('python3', [
      scriptPath,
      '--case-id', params.caseId,
      '--node-id', params.clickedNodeId,
      '--session-id', params.sessionId,
      '--max-cost', String(params.maxCost),
      '--json',
    ], {
      cwd: join(process.cwd(), '..'), // Run from project root
    });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
    proc.stderr.on('data', (chunk) => { stderr += chunk.toString(); });

    proc.on('close', (code) => {
      if (code !== 0) {
        // Try to parse error JSON from stderr
        try {
          const errorData = JSON.parse(stderr);
          reject(new Error(JSON.stringify(errorData)));
        } catch {
          reject(new Error(stderr || 'Python script failed'));
        }
        return;
      }

      try {
        const result = JSON.parse(stdout);
        resolve(result);
      } catch {
        reject(new Error('Failed to parse narrative response'));
      }
    });

    proc.on('error', (err) => {
      reject(new Error(`Failed to spawn Python process: ${err.message}`));
    });
  });
}
