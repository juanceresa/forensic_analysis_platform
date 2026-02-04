import { NextRequest, NextResponse } from 'next/server';
import * as fs from 'fs/promises';
import * as path from 'path';
import {
  loadDocumentGroups,
  buildFileToGroupMap,
  matchExtractionToGroup,
  inferType,
} from '@/lib/document-groups';

const CASES_DIR = path.join(process.cwd(), '../cases');
const CASE_ID_PATTERN = /^[A-Za-z0-9_-]+$/;

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
    const extractionsDir = path.join(caseDir, 'extractions');
    const intakeDir = path.join(caseDir, 'intake');

    const groupConfig = await loadDocumentGroups(caseDir);
    const fileToGroup = groupConfig ? buildFileToGroupMap(groupConfig.groups) : null;

    const extractionFiles = await fs.readdir(extractionsDir);
    const jsonFiles = extractionFiles.filter(f => f.endsWith('.json'));
    const intakeFiles = await fs.readdir(intakeDir);

    const docMap = new Map<string, {
      id: string;
      filename: string;
      date: string | null;
      type: string | null;
      entityCount: number;
      confidence: number;
      partCount: number;
      imagePath: string;
      entityIds: Set<string>;
    }>();

    for (const filename of jsonFiles) {
      const extractionPath = path.join(extractionsDir, filename);
      const content = await fs.readFile(extractionPath, 'utf-8');
      const extraction = JSON.parse(content);

      const baseName = filename.replace(/\.json$/i, '');
      const docId = baseName.replace(/_page_\d+$/i, '');

      const group = fileToGroup ? matchExtractionToGroup(baseName, fileToGroup) : null;

      // Collect entity IDs from this extraction
      const extractionEntityIds = new Set<string>();
      if (extraction.entities && Array.isArray(extraction.entities)) {
        for (const entity of extraction.entities) {
          if (entity.id) extractionEntityIds.add(entity.id);
        }
      }

      if (group) {
        const groupKey = `group:${group.id}`;
        const existing = docMap.get(groupKey);
        const entityCount = extraction.entities?.length || 0;
        const confidence = extraction.confidence_scores?.ocr_confidence || 0;

        if (existing) {
          existing.entityCount += entityCount;
          existing.confidence = Math.max(existing.confidence, confidence);
          existing.partCount += 1;
          // Merge entity IDs
          for (const id of extractionEntityIds) {
            existing.entityIds.add(id);
          }
          if (!existing.date && extraction.processing_metadata?.llm_metadata?.document_date) {
            existing.date = extraction.processing_metadata.llm_metadata.document_date;
          }
        } else {
          let date: string | null = group.date || null;
          if (!date && extraction.processing_metadata?.llm_metadata?.document_date) {
            date = extraction.processing_metadata.llm_metadata.document_date;
          }

          docMap.set(groupKey, {
            id: `doc_${group.id}`,
            filename: group.name,
            date,
            type: group.document_type || inferType(group.name),
            entityCount,
            confidence,
            partCount: 1,
            imagePath: `/api/cases/${caseId}/documents/${encodeURIComponent(`doc_${group.id}`)}/image`,
            entityIds: extractionEntityIds,
          });
        }
      } else {
        const standaloneKey = `standalone:${docId}`;
        if (!docMap.has(standaloneKey)) {
          const matchingIntake = intakeFiles.find((f) => {
            const intakeBase = f.replace(/\.(pdf|jpg|png)$/i, '');
            return intakeBase === docId;
          });

          let date: string | null = null;
          if (extraction.processing_metadata?.llm_metadata?.document_date) {
            date = extraction.processing_metadata.llm_metadata.document_date;
          }

          docMap.set(standaloneKey, {
            id: docId,
            filename: matchingIntake || `${docId}.pdf`,
            date,
            type: inferType(filename),
            entityCount: extraction.entities?.length || 0,
            confidence: extraction.confidence_scores?.ocr_confidence || 0,
            partCount: 1,
            imagePath: `/api/cases/${caseId}/documents/${encodeURIComponent(docId)}/image`,
            entityIds: extractionEntityIds,
          });
        }
      }
    }

    // Convert Sets to arrays for JSON serialization
    const documents = Array.from(docMap.values()).map(doc => ({
      ...doc,
      entityIds: Array.from(doc.entityIds),
    }));

    documents.sort((a, b) => {
      if (!a.date && !b.date) return 0;
      if (!a.date) return 1;
      if (!b.date) return -1;
      return new Date(a.date).getTime() - new Date(b.date).getTime();
    });

    return NextResponse.json({ documents });
  } catch (error) {
    console.error('Error fetching documents:', error);
    return NextResponse.json(
      { error: 'Failed to fetch documents' },
      { status: 500 }
    );
  }
}
