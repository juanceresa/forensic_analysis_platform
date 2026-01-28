import { NextRequest, NextResponse } from 'next/server';
import * as fs from 'fs/promises';
import * as path from 'path';

const CASES_DIR = path.join(process.cwd(), '../cases');
const CASE_ID_PATTERN = /^[A-Za-z0-9_-]+$/;
// Doc IDs can contain spaces, periods, alphanumerics, underscores, and hyphens
const DOC_ID_PATTERN = /^[A-Za-z0-9_. -]+$/;

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

    // Validate docId (strip page suffix for validation)
    const baseDocName = decodedDocId.replace(/_page_\d+$/, '');
    if (!DOC_ID_PATTERN.test(baseDocName)) {
      return NextResponse.json({ error: 'Invalid docId' }, { status: 400 });
    }

    // Handle both formats: "docname" and "docname_page_0"
    // If docId already ends with _page_N, use it as-is; otherwise append _page_0
    const hasPageSuffix = /_page_\d+$/.test(decodedDocId);
    const extractionDocId = hasPageSuffix ? decodedDocId : `${decodedDocId}_page_0`;

    const extractionPath = path.join(CASES_DIR, caseId, 'extractions', `${extractionDocId}.json`);
    const ocrPath = path.join(CASES_DIR, caseId, 'ocr', `${extractionDocId}.txt`);
    const intakeDir = path.join(CASES_DIR, caseId, 'intake');

    // Read extraction JSON
    const extractionContent = await fs.readFile(extractionPath, 'utf-8');
    const extraction = JSON.parse(extractionContent);

    // Read OCR text
    let ocrText = '';
    try {
      ocrText = await fs.readFile(ocrPath, 'utf-8');
    } catch (error) {
      // If OCR text file doesn't exist, try to get it from extraction
      ocrText = extraction.ocr_result?.text || '';
    }

    // Find matching intake file (uses baseDocName already computed above)
    const intakeFiles = await fs.readdir(intakeDir);
    const matchingIntake = intakeFiles.find(f =>
      f.replace(/\.(pdf|jpg|png)$/i, '') === baseDocName
    );

    // Extract date from processing metadata
    let date: string | null = null;
    if (extraction.processing_metadata?.llm_metadata?.document_date) {
      date = extraction.processing_metadata.llm_metadata.document_date;
    }

    // Extract document type
    let type: string | null = null;
    const lowerDocId = decodedDocId.toLowerCase();
    if (lowerDocId.includes('will') || lowerDocId.includes('testament')) {
      type = 'Will';
    } else if (lowerDocId.includes('contract')) {
      type = 'Contract';
    } else if (lowerDocId.includes('transfer') || lowerDocId.includes('trans')) {
      type = 'Transfer';
    } else if (lowerDocId.includes('deed')) {
      type = 'Deed';
    } else if (lowerDocId.includes('report')) {
      type = 'Report';
    }

    // Get detected language from OCR metadata
    const detectedLanguage = extraction.ocr_result?.metadata?.language ||
      extraction.processing_metadata?.ocr_metadata?.language ||
      'unknown';

    // Check if translation exists (pre-generated during processing)
    const translatedPath = path.join(CASES_DIR, caseId, 'ocr_translated', `${extractionDocId}.txt`);
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
      type,
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
