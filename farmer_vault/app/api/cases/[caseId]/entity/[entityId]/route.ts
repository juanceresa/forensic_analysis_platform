import { NextRequest, NextResponse } from 'next/server';
import * as fs from 'fs/promises';
import * as path from 'path';
import type { GraphData } from '@/lib/types';
import {
  loadDocumentGroups,
  buildFileToGroupMap,
  matchExtractionToGroup,
} from '@/lib/document-groups';

const CASES_DIR = path.join(process.cwd(), '../cases');
const CASE_ID_PATTERN = /^[A-Za-z0-9_-]+$/;
// Entity IDs can contain spaces, alphanumerics, underscores, hyphens, dots, and parentheses
const ENTITY_ID_PATTERN = /^[A-Za-z0-9_ .\-()]+$/;

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ caseId: string; entityId: string }> }
) {
  try {
    const { caseId, entityId } = await params;

    if (!CASE_ID_PATTERN.test(caseId)) {
      return NextResponse.json({ error: 'Invalid caseId' }, { status: 400 });
    }

    const resolvedCaseDir = path.resolve(CASES_DIR, caseId);
    const resolvedCasesRoot = path.resolve(CASES_DIR);
    if (!resolvedCaseDir.startsWith(resolvedCasesRoot)) {
      return NextResponse.json({ error: 'Invalid caseId' }, { status: 400 });
    }

    const decodedEntityId = decodeURIComponent(entityId);
    if (!ENTITY_ID_PATTERN.test(decodedEntityId)) {
      return NextResponse.json({ error: 'Invalid entityId' }, { status: 400 });
    }

    const caseDir = path.join(CASES_DIR, caseId);
    const graphDataPath = path.join(caseDir, 'output', 'graph_data.json');
    const graphDataContent = await fs.readFile(graphDataPath, 'utf-8');
    const graphData: GraphData = JSON.parse(graphDataContent);

    const entity = graphData.nodes.find(n => n.id === decodedEntityId);

    if (!entity) {
      return NextResponse.json(
        { error: 'Entity not found' },
        { status: 404 }
      );
    }

    // Resolve source documents, mapping raw extraction stems to document groups
    const groupConfig = await loadDocumentGroups(caseDir);
    const fileToGroup = groupConfig ? buildFileToGroupMap(groupConfig.groups) : null;

    const rawDocIds = entity.extracted_from?.split(',').map(s => s.trim()) || [];
    const seenIds = new Set<string>();
    const sourceDocuments: { id: string; filename: string }[] = [];

    // Build a quick group-by-id lookup
    const groupById = new Map<string, { id: string; name: string }>();
    if (groupConfig) {
      for (const g of groupConfig.groups) {
        groupById.set(g.id, g);
      }
    }

    for (const rawId of rawDocIds) {
      let docId: string;
      let filename: string;

      if (rawId.startsWith('doc_')) {
        // Already a merged group ID — look up group directly
        const gid = rawId.replace(/^doc_/, '');
        const group = groupById.get(gid);
        docId = rawId;
        filename = group ? group.name : `${rawId}.pdf`;
      } else {
        // Raw extraction stem — try matching to a group
        const stem = rawId.replace(/_page_\d+$/i, '');
        const group = fileToGroup ? matchExtractionToGroup(stem, fileToGroup) : null;
        docId = group ? `doc_${group.id}` : stem;
        filename = group ? group.name : `${stem}.pdf`;
      }

      if (seenIds.has(docId)) continue;
      seenIds.add(docId);
      sourceDocuments.push({ id: docId, filename });
    }

    // Load entity description from separate file (survives graph rebuilds)
    let description: string | null = null;
    try {
      const descriptionsPath = path.join(caseDir, 'output', 'entity_descriptions.json');
      const descriptionsContent = await fs.readFile(descriptionsPath, 'utf-8');
      const descriptions: Record<string, string> = JSON.parse(descriptionsContent);
      description = descriptions[decodedEntityId] ?? null;
    } catch {
      // entity_descriptions.json doesn't exist yet — that's fine
    }

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
      entity: { ...entity, description },
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
