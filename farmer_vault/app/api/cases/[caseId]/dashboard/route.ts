import { NextRequest, NextResponse } from 'next/server';
import * as fs from 'fs/promises';
import * as path from 'path';
import type { GraphData } from '@/lib/types';

const CASES_DIR = path.join(process.cwd(), '../cases');
const CASE_ID_PATTERN = /^[A-Za-z0-9_-]+$/;

interface DashboardData {
  metrics: {
    documents: number;
    entities: number;
    relationships: number;
    stage: string;
    stageProgress: number;
  };
  verificationDistribution: {
    TIER_3_AI: number;
    TIER_2_ANALYST: number;
    TIER_1_CERTIFIED: number;
    TIER_4_SOURCE: number;
  };
  entityTypeSummary: Record<string, number>;
  dateRange: {
    earliest: string | null;
    latest: string | null;
  };
  workflowStages: {
    intake: { complete: boolean; items: { label: string; complete: boolean }[] };
    processing: { complete: boolean; items: { label: string; complete: boolean }[] };
    analysis: { complete: boolean; items: { label: string; complete: boolean }[] };
    certification: { complete: boolean; items: { label: string; complete: boolean }[] };
  };
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

    // Read graph data
    const graphDataPath = path.join(CASES_DIR, caseId, 'output', 'graph_data.json');
    const graphDataContent = await fs.readFile(graphDataPath, 'utf-8');
    const graphData: GraphData = JSON.parse(graphDataContent);

    // Count documents from extractions directory
    const extractionsDir = path.join(CASES_DIR, caseId, 'extractions');
    const extractionFiles = await fs.readdir(extractionsDir);
    const documentCount = extractionFiles.filter(f => f.endsWith('.json')).length;

    // Filter out DOCUMENT type entities for entity count
    const entityNodes = graphData.nodes.filter(n => n.entity_type !== 'DOCUMENT');
    const entityCount = entityNodes.length;
    const relationshipCount = graphData.links.length;

    // Calculate verification distribution
    const verificationDistribution = {
      TIER_3_AI: 0,
      TIER_2_ANALYST: 0,
      TIER_1_CERTIFIED: 0,
      TIER_4_SOURCE: 0,
    };

    for (const node of entityNodes) {
      const tier = node.verification.tier as keyof typeof verificationDistribution;
      if (tier in verificationDistribution) {
        verificationDistribution[tier]++;
      }
    }

    // Calculate entity type summary
    const entityTypeSummary: Record<string, number> = {};
    for (const node of entityNodes) {
      entityTypeSummary[node.entity_type] = (entityTypeSummary[node.entity_type] || 0) + 1;
    }

    // Determine workflow stage based on verification distribution
    let stage = 'Processing';
    let stageProgress = 68;

    const totalVerified = verificationDistribution.TIER_2_ANALYST + 
                          verificationDistribution.TIER_1_CERTIFIED;
    const verifiedPercent = entityCount > 0 ? (totalVerified / entityCount) * 100 : 0;

    if (verificationDistribution.TIER_1_CERTIFIED > entityCount * 0.5) {
      stage = 'Certification';
      stageProgress = 95;
    } else if (verifiedPercent > 50) {
      stage = 'Analysis';
      stageProgress = 85;
    } else if (documentCount > 0 && entityCount > 0) {
      stage = 'Processing';
      stageProgress = 68;
    } else {
      stage = 'Intake';
      stageProgress = 25;
    }

    // Build workflow stages checklist
    const workflowStages = {
      intake: {
        complete: documentCount > 0,
        items: [
          { label: 'Documents uploaded', complete: documentCount > 0 },
          { label: 'Family intake form', complete: true }, // Assume complete if case exists
          { label: 'Methodology documentation', complete: true },
        ],
      },
      processing: {
        complete: entityCount > 0 && relationshipCount > 0,
        items: [
          { label: 'OCR extraction complete', complete: documentCount > 0 },
          { label: 'Entity extraction complete', complete: entityCount > 0 },
          { label: 'Graph construction complete', complete: relationshipCount > 0 },
        ],
      },
      analysis: {
        complete: verifiedPercent > 50,
        items: [
          { label: 'Analyst review in progress', complete: verifiedPercent > 0 },
          { label: 'Narrative generation', complete: false },
          { label: 'Gap identification', complete: false },
        ],
      },
      certification: {
        complete: false,
        items: [
          { label: 'Legal review', complete: false },
          { label: 'Final report delivery', complete: false },
          { label: 'Case closure', complete: false },
        ],
      },
    };

    const dashboardData: DashboardData = {
      metrics: {
        documents: documentCount,
        entities: entityCount,
        relationships: relationshipCount,
        stage,
        stageProgress,
      },
      verificationDistribution,
      entityTypeSummary,
      dateRange: {
        earliest: graphData.metadata.date_range?.earliest_document || null,
        latest: graphData.metadata.date_range?.latest_document || null,
      },
      workflowStages,
    };

    return NextResponse.json(dashboardData);
  } catch (error) {
    console.error('Error fetching dashboard data:', error);
    return NextResponse.json(
      { error: 'Failed to fetch dashboard data' },
      { status: 500 }
    );
  }
}
