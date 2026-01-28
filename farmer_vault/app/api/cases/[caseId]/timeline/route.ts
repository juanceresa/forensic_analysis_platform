import { NextRequest, NextResponse } from 'next/server';
import * as fs from 'fs/promises';
import * as path from 'path';
import type { GraphData } from '@/lib/types';

const CASES_DIR = path.join(process.cwd(), '../cases');
const CASE_ID_PATTERN = /^[A-Za-z0-9_-]+$/;

interface DocumentInfo {
  id: string;
  filename: string;
  date: string | null;
}

interface EntityInfo {
  id: string;
  name: string;
  entity_type: string;
  verification: {
    tier: string;
    confidence: number;
  };
}

interface TimePeriod {
  id: string;
  dateRange: string;
  startYear: number;
  endYear: number;
  title: string;
  documents: DocumentInfo[];
  entities: EntityInfo[];
  documentCount: number;
  entityCount: number;
}

function getPeriodTitle(startYear: number, endYear: number): string {
  // Generate contextual titles based on Cuban history
  if (startYear >= 1959 && endYear <= 1961) {
    return 'Expropriation Period';
  } else if (startYear >= 1945 && endYear < 1959) {
    return 'Post-War Era';
  } else if (startYear >= 1930 && endYear < 1945) {
    return 'Pre-War Period';
  } else if (startYear >= 1910 && endYear < 1930) {
    return 'Early Property Records';
  } else {
    return `${startYear}-${endYear}`;
  }
}

function groupByTimePeriod(documents: DocumentInfo[], periodYears: number = 10): Map<string, DocumentInfo[]> {
  const periods = new Map<string, DocumentInfo[]>();

  for (const doc of documents) {
    if (!doc.date) continue;

    const year = new Date(doc.date).getFullYear();
    const periodStart = Math.floor(year / periodYears) * periodYears;
    const periodEnd = periodStart + periodYears - 1;
    const periodKey = `${periodStart}-${periodEnd}`;

    if (!periods.has(periodKey)) {
      periods.set(periodKey, []);
    }
    periods.get(periodKey)!.push(doc);
  }

  return periods;
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

    // Read graph data for entities
    const graphDataPath = path.join(CASES_DIR, caseId, 'output', 'graph_data.json');
    const graphDataContent = await fs.readFile(graphDataPath, 'utf-8');
    const graphData: GraphData = JSON.parse(graphDataContent);

    // Read documents from extractions directory
    const extractionsDir = path.join(CASES_DIR, caseId, 'extractions');
    const extractionFiles = await fs.readdir(extractionsDir);
    const jsonFiles = extractionFiles.filter(f => f.endsWith('.json'));

    const documents: DocumentInfo[] = [];
    const entityIdsByDoc: Map<string, Set<string>> = new Map();

    for (const filename of jsonFiles) {
      const extractionPath = path.join(extractionsDir, filename);
      const content = await fs.readFile(extractionPath, 'utf-8');
      const extraction = JSON.parse(content);

      const docId = filename.replace('_page_0.json', '');
      const date = extraction.processing_metadata?.llm_metadata?.document_date || null;

      documents.push({
        id: docId,
        filename: `${docId}.pdf`,
        date,
      });

      // Track entities in this document
      const entityIds = new Set<string>();
      for (const entity of (extraction.entities || [])) {
        if (entity.id) entityIds.add(entity.id);
      }
      entityIdsByDoc.set(docId, entityIds);
    }

    // Group documents by time periods
    const periodGroups = groupByTimePeriod(documents, 10);

    // Build timeline periods
    const periods: TimePeriod[] = [];

    for (const [periodKey, periodDocs] of periodGroups.entries()) {
      const [startStr, endStr] = periodKey.split('-');
      const startYear = parseInt(startStr, 10);
      const endYear = parseInt(endStr, 10);

      // Collect unique entities from all documents in this period
      const periodEntityIds = new Set<string>();
      for (const doc of periodDocs) {
        const docEntityIds = entityIdsByDoc.get(doc.id);
        if (docEntityIds) {
          for (const id of docEntityIds) {
            periodEntityIds.add(id);
          }
        }
      }

      // Look up entity details from graph
      const periodEntities: EntityInfo[] = [];
      for (const entityId of periodEntityIds) {
        const node = graphData.nodes.find(n => n.id === entityId);
        if (node && node.entity_type !== 'DOCUMENT') {
          periodEntities.push({
            id: node.id,
            name: node.name || node.id,
            entity_type: node.entity_type,
            verification: {
              tier: node.verification.tier,
              confidence: node.verification.confidence,
            },
          });
        }
      }

      // Sort documents by date
      periodDocs.sort((a, b) => {
        if (!a.date && !b.date) return 0;
        if (!a.date) return 1;
        if (!b.date) return -1;
        return new Date(a.date).getTime() - new Date(b.date).getTime();
      });

      periods.push({
        id: periodKey,
        dateRange: periodKey,
        startYear,
        endYear,
        title: getPeriodTitle(startYear, endYear),
        documents: periodDocs,
        entities: periodEntities.slice(0, 10), // Limit to top 10 entities per period
        documentCount: periodDocs.length,
        entityCount: periodEntities.length,
      });
    }

    // Sort periods chronologically
    periods.sort((a, b) => a.startYear - b.startYear);

    return NextResponse.json({
      periods,
      totalDocuments: documents.length,
      dateRange: graphData.metadata.date_range,
    });
  } catch (error) {
    console.error('Error fetching timeline:', error);
    return NextResponse.json(
      { error: 'Failed to fetch timeline data' },
      { status: 500 }
    );
  }
}
