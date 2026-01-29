import { NextRequest, NextResponse } from 'next/server';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as yaml from 'js-yaml';

const CASES_DIR = path.join(process.cwd(), '../cases');
const CASE_ID_PATTERN = /^[A-Za-z0-9_-]+$/;
// Doc IDs can contain spaces, periods, alphanumerics, underscores, and hyphens
const DOC_ID_PATTERN = /^[A-Za-z0-9_. -]+$/;

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
 * Find the document group matching a doc_ prefixed ID.
 */
async function findGroupForDocId(
  caseDir: string,
  docId: string
): Promise<DocumentGroup | null> {
  if (!docId.startsWith('doc_')) return null;
  const groupsPath = path.join(caseDir, 'document_groups.yaml');
  try {
    const content = await fs.readFile(groupsPath, 'utf-8');
    const config = yaml.load(content) as DocumentGroupsConfig;
    if (config?.status !== 'CONFIRMED' || !config.groups) return null;
    const targetId = docId.replace(/^doc_/, '');
    return config.groups.find(g => g.id === targetId) || null;
  } catch {
    return null;
  }
}

/**
 * Find extraction files that belong to a document group.
 * Group files like "Some Doc.1pdf.pdf" produce extractions like "Some Doc.1pdf_page_0.json".
 */
async function findGroupExtractionFiles(
  extractionsDir: string,
  group: DocumentGroup
): Promise<string[]> {
  const allFiles = await fs.readdir(extractionsDir);
  const jsonFiles = allFiles.filter(f => f.endsWith('.json'));

  // Build stems from group files for matching
  const groupStems = new Set(
    group.files.map(f => f.replace(/\.(pdf|jpg|png)$/i, ''))
  );

  return jsonFiles.filter(f => {
    const baseName = f.replace(/\.json$/i, '');
    const stripped = baseName.replace(/_page_\d+$/i, '');
    return groupStems.has(stripped);
  });
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

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ caseId: string; docId: string }> }
) {
  try {
    const { caseId, docId } = await params;
    const decodedDocId = decodeURIComponent(docId);

    // Validate caseId to prevent path traversal
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

    // Check if this is a grouped document
    const group = await findGroupForDocId(caseDir, decodedDocId);

    if (group) {
      return await handleGroupedDocument(caseId, caseDir, extractionsDir, group);
    }

    // --- Standalone document (original logic) ---
    const baseDocName = decodedDocId.replace(/_page_\d+$/, '');
    if (!DOC_ID_PATTERN.test(baseDocName)) {
      return NextResponse.json({ error: 'Invalid docId' }, { status: 400 });
    }

    const hasPageSuffix = /_page_\d+$/.test(decodedDocId);
    const extractionDocId = hasPageSuffix ? decodedDocId : `${decodedDocId}_page_0`;

    const extractionPath = path.join(extractionsDir, `${extractionDocId}.json`);
    const ocrPath = path.join(caseDir, 'ocr', `${extractionDocId}.txt`);

    const extractionContent = await fs.readFile(extractionPath, 'utf-8');
    const extraction = JSON.parse(extractionContent);

    let ocrText = '';
    try {
      ocrText = await fs.readFile(ocrPath, 'utf-8');
    } catch {
      ocrText = extraction.ocr_result?.text || '';
    }

    const intakeFiles = await fs.readdir(intakeDir);
    const matchingIntake = intakeFiles.find(f =>
      f.replace(/\.(pdf|jpg|png)$/i, '') === baseDocName
    );

    let date: string | null = null;
    if (extraction.processing_metadata?.llm_metadata?.document_date) {
      date = extraction.processing_metadata.llm_metadata.document_date;
    }

    const detectedLanguage = extraction.ocr_result?.metadata?.language ||
      extraction.processing_metadata?.ocr_metadata?.language ||
      'unknown';

    const translatedPath = path.join(caseDir, 'ocr_translated', `${extractionDocId}.txt`);
    let translatedText: string | null = null;
    try {
      translatedText = await fs.readFile(translatedPath, 'utf-8');
    } catch {
      // No translation available
    }

    const document = {
      id: decodedDocId,
      filename: matchingIntake || `${baseDocName}.pdf`,
      date,
      type: inferType(decodedDocId),
      entityCount: extraction.entities?.length || 0,
      confidence: extraction.confidence_scores?.ocr_confidence || 0,
      imagePath: `/api/cases/${caseId}/document/${encodeURIComponent(decodedDocId)}/image`,
      ocrText,
      translatedText,
      entities: extraction.entities || [],
      detectedLanguage,
    };

    return NextResponse.json(document);
  } catch (error) {
    console.error('Error fetching document:', error);
    return NextResponse.json(
      { error: 'Failed to fetch document details' },
      { status: 500 }
    );
  }
}

/**
 * Handle fetching a grouped document by aggregating all its extraction files.
 */
async function handleGroupedDocument(
  caseId: string,
  caseDir: string,
  extractionsDir: string,
  group: DocumentGroup
) {
  const groupDocId = `doc_${group.id}`;
  const extractionFiles = await findGroupExtractionFiles(extractionsDir, group);

  if (extractionFiles.length === 0) {
    return NextResponse.json(
      { error: 'No extraction files found for this document group' },
      { status: 404 }
    );
  }

  // Sort extraction files to match group.files YAML order
  const groupStemOrder = group.files.map(f => f.replace(/\.(pdf|jpg|png)$/i, ''));
  extractionFiles.sort((a, b) => {
    const stemA = a.replace(/\.json$/i, '').replace(/_page_\d+$/i, '');
    const stemB = b.replace(/\.json$/i, '').replace(/_page_\d+$/i, '');
    const idxA = groupStemOrder.indexOf(stemA);
    const idxB = groupStemOrder.indexOf(stemB);
    return (idxA === -1 ? 999 : idxA) - (idxB === -1 ? 999 : idxB);
  });

  // Build per-page data from all extraction files
  const pages: {
    ocrText: string;
    translatedText: string | null;
    imagePath: string;
    entities: any[];
  }[] = [];
  let allEntities: any[] = [];
  let maxConfidence = 0;
  let date: string | null = group.date || null;
  let detectedLanguage = 'unknown';

  for (let i = 0; i < extractionFiles.length; i++) {
    const extFile = extractionFiles[i];
    const extPath = path.join(extractionsDir, extFile);
    const content = await fs.readFile(extPath, 'utf-8');
    const extraction = JSON.parse(content);

    const pageEntities = extraction.entities || [];
    allEntities = allEntities.concat(pageEntities);

    const conf = extraction.confidence_scores?.ocr_confidence || 0;
    if (conf > maxConfidence) maxConfidence = conf;

    if (!date && extraction.processing_metadata?.llm_metadata?.document_date) {
      date = extraction.processing_metadata.llm_metadata.document_date;
    }

    if (detectedLanguage === 'unknown') {
      detectedLanguage = extraction.ocr_result?.metadata?.language ||
        extraction.processing_metadata?.ocr_metadata?.language ||
        'unknown';
    }

    // Read OCR text for this page
    const partDocId = extFile.replace(/\.json$/i, '');
    let ocrText = '';
    try {
      ocrText = await fs.readFile(path.join(caseDir, 'ocr', `${partDocId}.txt`), 'utf-8');
    } catch {
      ocrText = extraction.ocr_result?.text || '';
    }

    // Read translated text for this page
    let translatedText: string | null = null;
    try {
      translatedText = await fs.readFile(path.join(caseDir, 'ocr_translated', `${partDocId}.txt`), 'utf-8');
    } catch {
      // No translation for this page
    }

    pages.push({
      ocrText,
      translatedText,
      imagePath: `/api/cases/${caseId}/document/${encodeURIComponent(groupDocId)}/image?page=${i}`,
      entities: pageEntities,
    });
  }

  const document = {
    id: groupDocId,
    filename: group.name,
    date,
    type: group.document_type || inferType(group.name),
    entityCount: allEntities.length,
    confidence: maxConfidence,
    imagePath: `/api/cases/${caseId}/document/${encodeURIComponent(groupDocId)}/image?page=0`,
    ocrText: pages[0]?.ocrText || '',
    translatedText: pages[0]?.translatedText || null,
    entities: allEntities,
    detectedLanguage,
    pages,
  };

  return NextResponse.json(document);
}
