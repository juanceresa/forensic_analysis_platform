import { NextRequest, NextResponse } from 'next/server';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as yaml from 'js-yaml';

const CASES_DIR = path.join(process.cwd(), '../cases');
const CASE_ID_PATTERN = /^[A-Za-z0-9_-]+$/;
const DOC_ID_PATTERN = /^[A-Za-z0-9_. -]+$/;

interface DocumentGroup {
  id: string;
  name: string;
  files: string[];
}

interface DocumentGroupsConfig {
  status: string;
  groups: DocumentGroup[];
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
    const intakeDir = path.join(caseDir, 'intake');
    const intakeFiles = await fs.readdir(intakeDir);

    // Support ?page=N for grouped documents
    const pageParam = request.nextUrl.searchParams.get('page');
    const pageIndex = pageParam !== null ? parseInt(pageParam, 10) : 0;

    // For grouped documents (doc_ prefix), find the file at the requested page index
    let matchingFile: string | undefined;

    if (decodedDocId.startsWith('doc_')) {
      const groupsPath = path.join(caseDir, 'document_groups.yaml');
      try {
        const content = await fs.readFile(groupsPath, 'utf-8');
        const config = yaml.load(content) as DocumentGroupsConfig;
        if (config?.status === 'CONFIRMED' && config.groups) {
          const targetId = decodedDocId.replace(/^doc_/, '');
          const group = config.groups.find(g => g.id === targetId);
          if (group && group.files.length > 0) {
            // Get the file at the requested page index
            const targetFile = group.files[pageIndex] || group.files[0];
            if (intakeFiles.includes(targetFile)) {
              matchingFile = targetFile;
            }
          }
        }
      } catch {
        // Fall through to standard matching
      }
    }

    // Standard matching for standalone docs
    if (!matchingFile) {
      const baseDocName = decodedDocId.replace(/_page_\d+$/, '');
      if (!DOC_ID_PATTERN.test(baseDocName)) {
        return NextResponse.json({ error: 'Invalid docId' }, { status: 400 });
      }
      matchingFile = intakeFiles.find(f =>
        f.replace(/\.(pdf|jpg|png)$/i, '') === baseDocName
      );
    }

    if (!matchingFile) {
      return NextResponse.json(
        { error: 'Document image not found' },
        { status: 404 }
      );
    }

    const imagePath = path.join(intakeDir, matchingFile);
    const imageBuffer = await fs.readFile(imagePath);

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
