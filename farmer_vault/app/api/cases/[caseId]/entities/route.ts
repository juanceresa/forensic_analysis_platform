import { NextRequest, NextResponse } from 'next/server';
import * as fs from 'fs/promises';
import * as path from 'path';
import type { GraphData, BaseNode, EntityType } from '@/lib/types';

const CASES_DIR = path.join(process.cwd(), '../cases');
const CASE_ID_PATTERN = /^[A-Za-z0-9_-]+$/;

interface EntitySummary {
  id: string;
  name: string;
  entity_type: EntityType;
  roleLabel?: string;
  verification: {
    tier: string;
    confidence: number;
  };
  documentCount: number;
}

interface GroupedEntities {
  PERSON: EntitySummary[];
  PROPERTY: EntitySummary[];
  ORGANIZATION: EntitySummary[];
  LOCATION: EntitySummary[];
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ caseId: string }> }
) {
  try {
    const { caseId } = await params;

    // Validate caseId to prevent path traversal
    if (!CASE_ID_PATTERN.test(caseId)) {
      return NextResponse.json({ error: 'Invalid caseId' }, { status: 400 });
    }

    const resolvedCaseDir = path.resolve(CASES_DIR, caseId);
    const resolvedCasesRoot = path.resolve(CASES_DIR);
    if (!resolvedCaseDir.startsWith(resolvedCasesRoot)) {
      return NextResponse.json({ error: 'Invalid caseId' }, { status: 400 });
    }

    const graphDataPath = path.join(CASES_DIR, caseId, 'output', 'graph_data.json');
    const graphDataContent = await fs.readFile(graphDataPath, 'utf-8');
    const graphData: GraphData = JSON.parse(graphDataContent);

    // Group entities by type
    const grouped: GroupedEntities = {
      PERSON: [],
      PROPERTY: [],
      ORGANIZATION: [],
      LOCATION: [],
    };

    for (const node of graphData.nodes) {
      // Skip DOCUMENT type entities
      if (node.entity_type === 'DOCUMENT') continue;

      const docCount = node.extracted_from
        ? node.extracted_from.split(',').filter(s => s.trim()).length
        : 0;

      const summary: EntitySummary = {
        id: node.id,
        name: node.name || node.id,
        entity_type: node.entity_type,
        roleLabel: node.roleLabel as string | undefined,
        verification: {
          tier: node.verification.tier,
          confidence: node.verification.confidence,
        },
        documentCount: docCount,
      };

      if (node.entity_type in grouped) {
        grouped[node.entity_type as keyof GroupedEntities].push(summary);
      }
    }

    // Sort each group alphabetically by name
    for (const type of Object.keys(grouped) as (keyof GroupedEntities)[]) {
      grouped[type].sort((a, b) => a.name.localeCompare(b.name));
    }

    // Calculate totals
    const totalCount = Object.values(grouped).reduce((sum, arr) => sum + arr.length, 0);
    const documentCount = graphData.metadata.document_count || 0;

    return NextResponse.json({
      entities: grouped,
      totalCount,
      documentCount,
      metadata: {
        case_id: graphData.metadata.case_id,
        entity_type_summary: graphData.metadata.entity_type_summary,
        verification_distribution: graphData.metadata.verification_distribution,
      },
    });
  } catch (error) {
    console.error('Error fetching entities:', error);
    return NextResponse.json(
      { error: 'Failed to fetch entities' },
      { status: 500 }
    );
  }
}
