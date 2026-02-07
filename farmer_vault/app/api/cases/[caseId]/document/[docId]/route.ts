import { NextRequest, NextResponse } from 'next/server';
import * as fs from 'fs/promises';
import * as path from 'path';
import {
  findGroupForDocId,
  findGroupExtractionFiles,
  inferType,
  type DocumentGroup,
} from '@/lib/document-groups';

const CASES_DIR = path.join(process.cwd(), '../cases');
const CASE_ID_PATTERN = /^[A-Za-z0-9_-]+$/;
// Doc IDs can contain spaces, periods, alphanumerics, underscores, and hyphens
const DOC_ID_PATTERN = /^[A-Za-z0-9_. -]+$/;

/**
 * Normalize OCR text for better readability.
 * Joins hard line breaks from OCR into flowing paragraphs.
 */
function normalizeOcrText(text: string): string {
  if (!text) return text;

  return text
    // Fix hyphenated line breaks (word-\n continuation)
    .replace(/-\s*\n\s*/g, '')
    // Normalize line endings
    .replace(/\r\n/g, '\n')
    .replace(/\r/g, '\n')
    // Mark paragraph breaks (2+ newlines) with placeholder
    .replace(/\n{2,}/g, '¶¶')
    // Join all remaining single newlines with space
    .replace(/\n/g, ' ')
    // Restore paragraph breaks
    .replace(/¶¶/g, '\n\n')
    // Collapse multiple spaces
    .replace(/  +/g, ' ')
    .trim();
}

interface OcrBlock {
  text: string;
  confidence: number;
  bounding_box: number[]; // [x, y, width, height]
  block_type: string;
}

/**
 * Build structured OCR text from Vision API blocks.
 * Sorts blocks by vertical position and filters noise,
 * preserving the document's original paragraph structure.
 */
function buildTextFromBlocks(blocks: OcrBlock[]): string {
  if (!blocks || blocks.length === 0) return '';

  // Sort by Y position (top to bottom), then X (left to right)
  const sorted = [...blocks].sort((a, b) => {
    const ay = a.bounding_box[1];
    const by = b.bounding_box[1];
    if (Math.abs(ay - by) > 20) return ay - by; // different row
    return a.bounding_box[0] - b.bounding_box[0]; // same row, left to right
  });

  // Filter OCR noise using tiered confidence thresholds.
  // Short blocks need higher confidence; long blocks tolerate lower.
  const meaningful = sorted.filter(b => {
    const text = b.text.trim();
    if (text.length === 0) return false;

    const words = text.split(/\s+/).length;
    const alphaChars = text.replace(/[^a-zA-ZáéíóúñüÁÉÍÓÚÑÜ]/g, '').length;
    const alphaRatio = alphaChars / text.length;

    // Pure symbols/punctuation with no letters — always noise
    if (alphaRatio === 0 && words <= 3) return false;

    // Single word: high bar (catches "AI", "03", "☑", stray marks)
    if (words === 1) return b.confidence >= 0.7 && alphaRatio > 0.3;

    // 2-4 words: moderate bar (keeps dates like "May 26/66", filters "smade for moral")
    if (words <= 4) return b.confidence >= 0.6;

    // 5+ words: lower bar but still filters gibberish/bleed-through
    return b.confidence >= 0.5;
  });

  if (meaningful.length === 0) return '';

  // Normalize each block's text (fix hyphenation, collapse whitespace)
  return meaningful
    .map(b => b.text.trim()
      .replace(/-\s*\n\s*/g, '')
      .replace(/\s+/g, ' ')
    )
    .filter(t => t.length > 0)
    .join('\n\n');
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ caseId: string; docId: string }> }
) {
  try {
    const { caseId, docId } = await params;
    const decodedDocId = decodeURIComponent(docId);

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

    // Build raw OCR text from blocks or fallback sources
    const blocks: OcrBlock[] = extraction.ocr_result?.blocks || [];
    let rawOcrText = '';
    if (blocks.length > 0) {
      rawOcrText = buildTextFromBlocks(blocks);
    } else {
      try {
        rawOcrText = normalizeOcrText(await fs.readFile(ocrPath, 'utf-8'));
      } catch {
        rawOcrText = normalizeOcrText(extraction.ocr_result?.text || '');
      }
    }

    // Prefer LLM-cleaned text if available, otherwise use raw
    const cleanedPath = path.join(caseDir, 'ocr_cleaned', `${extractionDocId}.txt`);
    let ocrText = rawOcrText;
    try {
      ocrText = await fs.readFile(cleanedPath, 'utf-8');
    } catch {
      // No cleaned text — use raw (already assigned above)
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
      rawOcrText: ocrText !== rawOcrText ? rawOcrText : undefined,
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

  // Build per-page data from all extraction files
  const pages: {
    ocrText: string;
    rawOcrText?: string;
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

    const partDocId = extFile.replace(/\.json$/i, '');
    const pageBlocks: OcrBlock[] = extraction.ocr_result?.blocks || [];
    let rawOcrText = '';
    if (pageBlocks.length > 0) {
      rawOcrText = buildTextFromBlocks(pageBlocks);
    } else {
      try {
        rawOcrText = normalizeOcrText(await fs.readFile(path.join(caseDir, 'ocr', `${partDocId}.txt`), 'utf-8'));
      } catch {
        rawOcrText = normalizeOcrText(extraction.ocr_result?.text || '');
      }
    }

    // Prefer LLM-cleaned text if available
    let ocrText = rawOcrText;
    try {
      ocrText = await fs.readFile(path.join(caseDir, 'ocr_cleaned', `${partDocId}.txt`), 'utf-8');
    } catch {
      // No cleaned text — use raw
    }

    let translatedText: string | null = null;
    try {
      translatedText = await fs.readFile(path.join(caseDir, 'ocr_translated', `${partDocId}.txt`), 'utf-8');
    } catch {
      // No translation for this page
    }

    pages.push({
      ocrText,
      rawOcrText: ocrText !== rawOcrText ? rawOcrText : undefined,
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
    rawOcrText: pages[0]?.rawOcrText,
    translatedText: pages[0]?.translatedText || null,
    entities: allEntities,
    detectedLanguage,
    pages,
  };

  return NextResponse.json(document);
}
