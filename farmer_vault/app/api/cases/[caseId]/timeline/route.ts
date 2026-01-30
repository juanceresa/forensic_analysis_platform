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

interface NarrativeInlineEntity {
  name: string;
  entity_id: string;
  entity_type: string;
}

interface CaseNarrativeData {
  metadata: Record<string, unknown>;
  case_summary: string;
  periods: Array<{
    period_id: string;
    label: string;
    title?: string;
    narrative: string;
    document_ids: string[];
    entity_ids: string[];
    inline_entities?: NarrativeInlineEntity[];
    highlighted_events: Array<{
      event_type: string;
      summary: string;
      date: string | null;
      parties_involved: string[];
    }>;
    evidence: string[];
  }>;
}

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

interface TimelineEvent {
  id: string;
  year: number;
  date: string | null;
  eventType: 'CONFISCATED' | 'SOLD' | 'INHERITED' | 'FILED';
  summary: string;
  parties: string[];
  documentIds: string[];
  entityIds: string[];
  periodId: string;
}

interface TimelineGap {
  id: string;
  startYear: number;
  endYear: number;
  duration: number;
  contextHint: string;
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
  narrative: string | null;
  inlineEntities: Array<{
    name: string;
    entityId: string;
    entityType: string;
    verificationTier: string;
  }>;
  highlightedEvents: Array<{
    event_type: string;
    summary: string;
    date: string | null;
    parties_involved: string[];
  }>;
}

function getPeriodTitle(startYear: number, endYear: number): string {
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

function getGapContextHint(startYear: number, endYear: number): string {
  if (startYear <= 1959 && endYear >= 1959) {
    return 'Cuban Revolution occurred in 1959';
  }
  if (startYear >= 1959 && endYear <= 1975) {
    return 'Expropriation period — many property records lost or destroyed';
  }
  if (startYear <= 1940 && endYear >= 1940) {
    return 'World War II era — international documentation disrupted';
  }
  if (startYear >= 1898 && endYear <= 1910) {
    return 'Post-independence transition — Spanish colonial records archived';
  }
  return 'No documents available for this period';
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

    if (!CASE_ID_PATTERN.test(caseId)) {
      return NextResponse.json({ error: 'Invalid caseId' }, { status: 400 });
    }

    const resolvedCaseDir = path.resolve(CASES_DIR, caseId);
    const resolvedCasesRoot = path.resolve(CASES_DIR);
    if (!resolvedCaseDir.startsWith(resolvedCasesRoot)) {
      return NextResponse.json({ error: 'Invalid caseId' }, { status: 400 });
    }

    const caseDir = path.join(CASES_DIR, caseId);

    // Read graph data for entities
    const graphDataPath = path.join(caseDir, 'output', 'graph_data.json');
    const graphDataContent = await fs.readFile(graphDataPath, 'utf-8');
    const graphData: GraphData = JSON.parse(graphDataContent);

    // Read case narrative (optional)
    let caseNarrative: CaseNarrativeData | null = null;
    try {
      const narrativePath = path.join(caseDir, 'output', 'case_narrative.json');
      const narrativeContent = await fs.readFile(narrativePath, 'utf-8');
      caseNarrative = JSON.parse(narrativeContent);
    } catch {
      // case_narrative.json not yet generated
    }

    // Load document groups
    const groupConfig = await loadDocumentGroups(caseDir);
    const fileToGroup = groupConfig ? buildFileToGroupMap(groupConfig.groups) : null;

    // Read documents from extractions directory, respecting groups
    const extractionsDir = path.join(caseDir, 'extractions');
    const extractionFiles = await fs.readdir(extractionsDir);
    const jsonFiles = extractionFiles.filter(f => f.endsWith('.json'));

    const documents: DocumentInfo[] = [];
    const entityIdsByDoc: Map<string, Set<string>> = new Map();
    const seenGroupIds = new Set<string>();

    for (const filename of jsonFiles) {
      const extractionPath = path.join(extractionsDir, filename);
      const content = await fs.readFile(extractionPath, 'utf-8');
      const extraction = JSON.parse(content);

      const baseName = filename.replace(/\.json$/i, '');

      // Check if this file belongs to a group
      const group = fileToGroup ? matchExtractionToGroup(baseName, fileToGroup) : null;

      let docId: string;
      let docFilename: string;
      let date: string | null;

      if (group) {
        docId = `doc_${group.id}`;
        if (seenGroupIds.has(docId)) {
          // Already added this group — just aggregate entities
          const entityIds = entityIdsByDoc.get(docId) || new Set<string>();
          for (const entity of (extraction.entities || [])) {
            if (entity.id) entityIds.add(entity.id);
          }
          entityIdsByDoc.set(docId, entityIds);
          continue;
        }
        seenGroupIds.add(docId);
        docFilename = group.name;
        date = group.date || extraction.processing_metadata?.llm_metadata?.document_date || null;
      } else {
        docId = baseName.replace(/_page_\d+$/i, '');
        docFilename = `${docId}.pdf`;
        date = extraction.processing_metadata?.llm_metadata?.document_date || null;
      }

      documents.push({ id: docId, filename: docFilename, date });

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

      const periodEntityIds = new Set<string>();
      for (const doc of periodDocs) {
        const docEntityIds = entityIdsByDoc.get(doc.id);
        if (docEntityIds) {
          for (const id of docEntityIds) {
            periodEntityIds.add(id);
          }
        }
      }

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

      periodDocs.sort((a, b) => {
        if (!a.date && !b.date) return 0;
        if (!a.date) return 1;
        if (!b.date) return -1;
        return new Date(a.date).getTime() - new Date(b.date).getTime();
      });

      const narrativePeriod = caseNarrative?.periods.find(p => p.period_id === periodKey);

      // Resolve inline entities against graph nodes for verification data
      const inlineEntities = (narrativePeriod?.inline_entities || []).map(ie => {
        const node = graphData.nodes.find(n => n.id === ie.entity_id);
        return {
          name: ie.name,
          entityId: ie.entity_id,
          entityType: ie.entity_type,
          verificationTier: node?.verification?.tier || 'TIER_3_AI',
        };
      });

      periods.push({
        id: periodKey,
        dateRange: periodKey,
        startYear,
        endYear,
        title: narrativePeriod?.title || narrativePeriod?.label || getPeriodTitle(startYear, endYear),
        documents: periodDocs,
        entities: periodEntities.slice(0, 10),
        documentCount: periodDocs.length,
        entityCount: periodEntities.length,
        narrative: narrativePeriod?.narrative || null,
        inlineEntities,
        highlightedEvents: narrativePeriod?.highlighted_events || [],
      });
    }

    periods.sort((a, b) => a.startYear - b.startYear);

    // Build events array from highlighted_events + document FILED events
    const events: TimelineEvent[] = [];
    let eventCounter = 0;

    for (const period of periods) {
      // Highlighted events from narrative
      const highlightedDates = new Set<string>();
      for (const he of period.highlightedEvents) {
        const year = he.date ? new Date(he.date).getFullYear() : period.startYear;
        const eventType = (['CONFISCATED', 'SOLD', 'INHERITED', 'FILED'].includes(he.event_type)
          ? he.event_type
          : 'FILED') as TimelineEvent['eventType'];
        highlightedDates.add(he.date || '');
        events.push({
          id: `evt_${eventCounter++}`,
          year,
          date: he.date,
          eventType,
          summary: he.summary,
          parties: he.parties_involved,
          documentIds: period.documents.map(d => d.id),
          entityIds: period.entities.map(e => e.id),
          periodId: period.id,
        });
      }

      // Implicit FILED events for documents not already covered by a highlighted event
      for (const doc of period.documents) {
        if (!doc.date || highlightedDates.has(doc.date)) continue;
        const year = new Date(doc.date).getFullYear();
        events.push({
          id: `evt_${eventCounter++}`,
          year,
          date: doc.date,
          eventType: 'FILED',
          summary: `${doc.filename} entered the record`,
          parties: [],
          documentIds: [doc.id],
          entityIds: [],
          periodId: period.id,
        });
      }
    }

    events.sort((a, b) => a.year - b.year || (a.date || '').localeCompare(b.date || ''));

    // Build gaps array: intervals ≥3 years between consecutive events
    const gaps: TimelineGap[] = [];
    for (let i = 1; i < events.length; i++) {
      const duration = events[i].year - events[i - 1].year;
      if (duration >= 3) {
        const startYear = events[i - 1].year;
        const endYear = events[i].year;
        gaps.push({
          id: `gap_${startYear}_${endYear}`,
          startYear,
          endYear,
          duration,
          contextHint: getGapContextHint(startYear, endYear),
        });
      }
    }

    return NextResponse.json({
      periods,
      events,
      gaps,
      totalDocuments: documents.length,
      dateRange: graphData.metadata.date_range,
      caseSummary: caseNarrative?.case_summary || null,
    });
  } catch (error) {
    console.error('Error fetching timeline:', error);
    return NextResponse.json(
      { error: 'Failed to fetch timeline data' },
      { status: 500 }
    );
  }
}
