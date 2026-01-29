import { NextRequest, NextResponse } from 'next/server';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as yaml from 'js-yaml';

const CASES_DIR = path.join(process.cwd(), '../cases');
const CASE_ID_PATTERN = /^[A-Za-z0-9_-]+$/;

interface DocumentGroup {
  id: string;
  name: string;
  document_type?: string;
  date?: string;
  files: string[];
}

interface DocumentGroupsConfig {
  status: string;
  groups: DocumentGroup[];
  standalone?: string[];
}

/**
 * Load document_groups.yaml if it exists and is CONFIRMED.
 * Returns a map from extraction basename (no .json, no _page_N) to group info,
 * plus the set of standalone file stems.
 */
async function loadDocumentGroups(caseDir: string): Promise<{
  fileToGroup: Map<string, DocumentGroup>;
  groups: DocumentGroup[];
} | null> {
  const groupsPath = path.join(caseDir, 'document_groups.yaml');
  try {
    const content = await fs.readFile(groupsPath, 'utf-8');
    const config = yaml.load(content) as DocumentGroupsConfig;
    if (config?.status !== 'CONFIRMED' || !config.groups) return null;

    // Map each group file stem to its group
    const fileToGroup = new Map<string, DocumentGroup>();
    for (const group of config.groups) {
      for (const filename of group.files) {
        // Store both full filename and stem for flexible matching
        fileToGroup.set(filename, group);
        const stem = filename.replace(/\.(pdf|jpg|png)$/i, '');
        fileToGroup.set(stem, group);
      }
    }
    return { fileToGroup, groups: config.groups };
  } catch {
    return null;
  }
}

/**
 * Match an extraction file basename to a document group.
 * Extraction files look like "Some Doc.1pdf_page_0" — we strip _page_N
 * and try matching the result against group file stems.
 */
function findGroup(
  baseName: string,
  fileToGroup: Map<string, DocumentGroup>
): DocumentGroup | null {
  // baseName example: "3 27 1916 Trans Prop Holdings L. Queral.1pdf_page_0"
  const stripped = baseName.replace(/_page_\d+$/i, '');
  // Try exact stem match
  if (fileToGroup.has(stripped)) return fileToGroup.get(stripped)!;
  // Try with .pdf appended
  if (fileToGroup.has(stripped + '.pdf')) return fileToGroup.get(stripped + '.pdf')!;
  return null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ caseId: string }> }
) {
  try {
    const { caseId } = await params;

    // Validate caseId to prevent traversal
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

    // Load document groups config
    const groupConfig = await loadDocumentGroups(caseDir);

    // Read all extraction files
    const extractionFiles = await fs.readdir(extractionsDir);
    const jsonFiles = extractionFiles.filter(f => f.endsWith('.json'));
    const intakeFiles = await fs.readdir(intakeDir);

    // Parse each extraction file and assign to group or standalone
    // Key: group id or standalone doc id -> aggregated data
    const docMap = new Map<string, {
      id: string;
      filename: string;
      date: string | null;
      type: string | null;
      entityCount: number;
      confidence: number;
      partCount: number;
      imagePath: string;
    }>();

    for (const filename of jsonFiles) {
      const extractionPath = path.join(extractionsDir, filename);
      const content = await fs.readFile(extractionPath, 'utf-8');
      const extraction = JSON.parse(content);

      const baseName = filename.replace(/\.json$/i, '');
      const docId = baseName.replace(/_page_\d+$/i, '');

      // Check if this extraction belongs to a group
      const group = groupConfig ? findGroup(baseName, groupConfig.fileToGroup) : null;

      if (group) {
        const groupKey = `group:${group.id}`;
        const existing = docMap.get(groupKey);
        const entityCount = extraction.entities?.length || 0;
        const confidence = extraction.confidence_scores?.ocr_confidence || 0;

        if (existing) {
          // Aggregate into existing group entry
          existing.entityCount += entityCount;
          existing.confidence = Math.max(existing.confidence, confidence);
          existing.partCount += 1;
          // Use earliest date
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
          });
        }
      } else {
        // Standalone document
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
          });
        }
      }
    }

    const documents = Array.from(docMap.values());

    // Sort by date (earliest first) by default
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

function inferType(name: string): string | null {
  const lower = name.toLowerCase();
  if (lower.includes('will') || lower.includes('testament')) return 'Will';
  if (lower.includes('contract')) return 'Contract';
  if (lower.includes('transfer') || lower.includes('trans')) return 'Transfer';
  if (lower.includes('deed')) return 'Deed';
  if (lower.includes('report')) return 'Report';
  if (lower.includes('hacienda') || lower.includes('finca')) return 'Property';
  if (lower.includes('millage') || lower.includes('survey')) return 'Survey';
  if (lower.includes('credit')) return 'Financial';
  if (lower.includes('heir') || lower.includes('herencia')) return 'Inheritance';
  return null;
}
