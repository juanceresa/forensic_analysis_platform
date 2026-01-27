import { NextRequest, NextResponse } from 'next/server';
import * as fs from 'fs/promises';
import * as path from 'path';

const CASES_DIR = path.join(process.cwd(), '../cases');

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ caseId: string; docId: string }> }
) {
  try {
    const { caseId, docId } = await params;
    const decodedDocId = decodeURIComponent(docId);

    // Strip _page_N suffix to get base document name
    const baseDocName = decodedDocId.replace(/_page_\d+$/, '');

    const intakeDir = path.join(CASES_DIR, caseId, 'intake');

    // Find matching intake file
    const intakeFiles = await fs.readdir(intakeDir);
    const matchingFile = intakeFiles.find(f =>
      f.replace(/\.(pdf|jpg|png)$/i, '') === baseDocName
    );

    if (!matchingFile) {
      return NextResponse.json(
        { error: 'Document image not found' },
        { status: 404 }
      );
    }

    const imagePath = path.join(intakeDir, matchingFile);
    const imageBuffer = await fs.readFile(imagePath);

    // Determine content type
    const ext = path.extname(matchingFile).toLowerCase();
    let contentType = 'application/pdf';
    if (ext === '.jpg' || ext === '.jpeg') {
      contentType = 'image/jpeg';
    } else if (ext === '.png') {
      contentType = 'image/png';
    }

    return new NextResponse(imageBuffer, {
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=31536000, immutable',
      },
    });
  } catch (error) {
    console.error('Error fetching document image:', error);
    return NextResponse.json(
      { error: 'Failed to fetch document image' },
      { status: 500 }
    );
  }
}
