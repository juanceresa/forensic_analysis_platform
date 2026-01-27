import { NextRequest, NextResponse } from 'next/server';
import * as fs from 'fs/promises';
import * as path from 'path';

const CASES_DIR = path.join(process.cwd(), '../../cases');

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ caseId: string }> }
) {
  try {
    const { caseId } = await params;

    const extractionsDir = path.join(CASES_DIR, caseId, 'extractions');
    const intakeDir = path.join(CASES_DIR, caseId, 'intake');

    // Read all extraction files
    const extractionFiles = await fs.readdir(extractionsDir);
    const jsonFiles = extractionFiles.filter(f => f.endsWith('.json'));

    const documents = await Promise.all(
      jsonFiles.map(async (filename) => {
        const extractionPath = path.join(extractionsDir, filename);
        const content = await fs.readFile(extractionPath, 'utf-8');
        const extraction = JSON.parse(content);

        // Extract document ID (filename without _page_0.json)
        const docId = filename.replace('_page_0.json', '');

        // Try to find matching intake file
        const intakeFiles = await fs.readdir(intakeDir);
        const matchingIntake = intakeFiles.find(f =>
          f.replace(/\.(pdf|jpg|png)$/i, '') === docId
        );

        // Extract date from processing metadata or filename
        let date: string | null = null;
        if (extraction.processing_metadata?.llm_metadata?.document_date) {
          date = extraction.processing_metadata.llm_metadata.document_date;
        }

        // Extract document type from filename (simple heuristic)
        let type: string | null = null;
        const lowerFilename = filename.toLowerCase();
        if (lowerFilename.includes('will') || lowerFilename.includes('testament')) {
          type = 'Will';
        } else if (lowerFilename.includes('contract')) {
          type = 'Contract';
        } else if (lowerFilename.includes('transfer') || lowerFilename.includes('trans')) {
          type = 'Transfer';
        } else if (lowerFilename.includes('deed')) {
          type = 'Deed';
        } else if (lowerFilename.includes('report')) {
          type = 'Report';
        }

        return {
          id: docId,
          filename: matchingIntake || `${docId}.pdf`,
          date,
          type,
          entityCount: extraction.entities?.length || 0,
          confidence: extraction.confidence_scores?.ocr_confidence || 0,
          imagePath: `/api/cases/${caseId}/documents/${encodeURIComponent(docId)}/image`,
        };
      })
    );

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
