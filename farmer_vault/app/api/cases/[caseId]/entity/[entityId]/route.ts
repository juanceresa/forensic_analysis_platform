import { NextRequest, NextResponse } from 'next/server';
import * as fs from 'fs/promises';
import * as path from 'path';
import type { GraphData } from '@/lib/types';

const CASES_DIR = path.join(process.cwd(), '../cases');
const CASE_ID_PATTERN = /^[A-Za-z0-9_-]+$/;
// Entity IDs can contain spaces, alphanumerics, underscores, and hyphens
const ENTITY_ID_PATTERN = /^[A-Za-z0-9_ -]+$/;

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ caseId: string; entityId: string }> }
) {
  try {
    const { caseId, entityId } = await params;

    // Validate caseId to prevent path traversal
    if (!CASE_ID_PATTERN.test(caseId)) {
      return NextResponse.json({ error: 'Invalid caseId' }, { status: 400 });
    }

    const resolvedCaseDir = path.resolve(CASES_DIR, caseId);
    const resolvedCasesRoot = path.resolve(CASES_DIR);
    if (!resolvedCaseDir.startsWith(resolvedCasesRoot)) {
      return NextResponse.json({ error: 'Invalid caseId' }, { status: 400 });
    }

    // Validate entityId
    const decodedEntityId = decodeURIComponent(entityId);
    if (!ENTITY_ID_PATTERN.test(decodedEntityId)) {
      return NextResponse.json({ error: 'Invalid entityId' }, { status: 400 });
    }

    const graphDataPath = path.join(CASES_DIR, caseId, 'output', 'graph_data.json');
    const graphDataContent = await fs.readFile(graphDataPath, 'utf-8');
    const graphData: GraphData = JSON.parse(graphDataContent);

    // Find the entity
    const entity = graphData.nodes.find(n => n.id === decodedEntityId);

    if (!entity) {
      return NextResponse.json(
        { error: 'Entity not found' },
        { status: 404 }
      );
    }

    // Find source documents (from extracted_from field) with null-safety
    const sourceDocIds = entity.extracted_from?.split(',').map(s => s.trim()) || [];
    const sourceDocuments = sourceDocIds.map(docId => ({
      id: docId,
      filename: `${docId}.pdf`, // Simplified for now
    }));

    // Find connections (links where this entity is source or target)
    const connections = graphData.links.filter(
      link => link.source === entity.id || link.target === entity.id
    ).map(link => {
      const isSource = link.source === entity.id;
      const targetNodeId = isSource ? link.target : link.source;
      const targetNode = graphData.nodes.find(n => n.id === targetNodeId);

      return {
        relation_type: link.relation_type,
        targetEntity: targetNode ? {
          id: targetNode.id,
          name: targetNode.name || targetNode.id,
          entity_type: targetNode.entity_type,
          verification: targetNode.verification,
        } : null,
      };
    }).filter(conn => conn.targetEntity !== null);

    return NextResponse.json({
      entity,
      sourceDocuments,
      connections,
    });
  } catch (error) {
    console.error('Error fetching entity:', error);
    return NextResponse.json(
      { error: 'Failed to fetch entity details' },
      { status: 500 }
    );
  }
}
