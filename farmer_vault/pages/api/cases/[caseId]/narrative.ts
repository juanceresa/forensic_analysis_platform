/**
 * Next.js API route for narrative generation.
 *
 * POST /api/cases/[caseId]/narrative
 */

import type { NextApiRequest, NextApiResponse } from 'next';
import { spawn } from 'child_process';
import path from 'path';

interface NarrativeRequest {
  clicked_node_id: string;
  session_id: string;
}

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

interface NarrativeResponse {
  focal_entity_id: string;
  focal_entity_name: string;
  focal_entity_type: string;
  constellation_size: number;
  model_used: 'haiku' | 'sonnet';
  main_narrative: string;
  facts: EvidenceCitation[];
  total_documents: number;
  total_citations: number;
  generation_cost: number;
  from_cache: boolean;
  highlighted_events: EventHighlight[];
  session_total_cost: number;
}

interface ErrorResponse {
  error: string;
  details?: string;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<NarrativeResponse | ErrorResponse>
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { caseId } = req.query;
  const { clicked_node_id, session_id } = req.body as NarrativeRequest;

  // Validate input
  if (!clicked_node_id) {
    return res.status(400).json({ error: 'Missing clicked_node_id' });
  }

  if (!session_id) {
    return res.status(400).json({ error: 'Missing session_id' });
  }

  try {
    // Call Python backend via subprocess
    // In production, this would be a proper HTTP API call
    const result = await callPythonNarrativeAPI({
      caseId: caseId as string,
      clickedNodeId: clicked_node_id,
      sessionId: session_id,
    });

    return res.status(200).json(result);
  } catch (error) {
    console.error('Narrative generation error:', error);

    const message = error instanceof Error ? error.message : 'Unknown error';

    if (message.includes('cost limit exceeded') || message.includes('cost_limit')) {
      return res.status(429).json({
        error: 'Session cost limit exceeded',
        details: message,
      });
    }

    if (message.includes('not found') || message.includes('insufficient_data')) {
      return res.status(404).json({
        error: 'Entity not found',
        details: message,
      });
    }

    return res.status(500).json({
      error: 'Internal server error',
      details: message,
    });
  }
}

/**
 * Call Python narrative API via subprocess.
 *
 * In production, replace this with actual HTTP API call to Python backend.
 */
async function callPythonNarrativeAPI(params: {
  caseId: string;
  clickedNodeId: string;
  sessionId: string;
}): Promise<NarrativeResponse> {
  return new Promise((resolve, reject) => {
    const scriptPath = path.join(
      process.cwd(),
      '../farmer_factory/scripts/generate_narrative.py'
    );

    const pythonProcess = spawn('python3', [
      scriptPath,
      '--case-id',
      params.caseId,
      '--node-id',
      params.clickedNodeId,
      '--session-id',
      params.sessionId,
      '--json',
    ]);

    let stdout = '';
    let stderr = '';

    pythonProcess.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        // Try to parse error JSON from stderr
        try {
          const errorData = JSON.parse(stderr);
          reject(new Error(`${errorData.type}: ${errorData.error}`));
        } catch {
          reject(new Error(`Python script failed: ${stderr}`));
        }
        return;
      }

      try {
        const result = JSON.parse(stdout);
        resolve(result);
      } catch (err) {
        reject(new Error(`Failed to parse Python output: ${stdout}`));
      }
    });

    pythonProcess.on('error', (err) => {
      reject(new Error(`Failed to spawn Python process: ${err.message}`));
    });
  });
}
