import { existsSync, statSync, createReadStream } from 'fs';
import path from 'path';
import { NextRequest } from 'next/server';

// TODO: Add auth check - Phase 8B
// TODO: Add audit logging - Phase 8B

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ caseId: string }> }
) {
  const { caseId } = await params;

  // DEV-GUARD: Remove once Phase 8B ships
  if (process.env.NODE_ENV === 'production' && process.env.ENABLE_DOSSIER_DOWNLOAD !== 'true') {
    return new Response('Not enabled', { status: 403 });
  }

  // Validate caseId to prevent path traversal
  if (!/^[A-Za-z0-9_-]+$/.test(caseId)) {
    return new Response('Invalid caseId', { status: 400 });
  }

  const pdfPath = path.join(
    process.cwd(),
    '..',
    'cases',
    caseId,
    'output',
    `${caseId}_dossier.pdf`
  );

  if (!existsSync(pdfPath)) {
    return new Response('Dossier not found', { status: 404 });
  }

  const stat = statSync(pdfPath);
  const stream = createReadStream(pdfPath);

  // @ts-expect-error - ReadStream is compatible with Response body
  return new Response(stream, {
    headers: {
      'Content-Type': 'application/pdf',
      'Content-Disposition': `attachment; filename="${caseId}_dossier.pdf"`,
      'Content-Length': stat.size.toString(),
      'Cache-Control': 'private, no-store',
    },
  });
}

export async function HEAD(
  request: NextRequest,
  { params }: { params: Promise<{ caseId: string }> }
) {
  const { caseId } = await params;

  // Validate caseId to prevent path traversal
  if (!/^[A-Za-z0-9_-]+$/.test(caseId)) {
    return new Response(null, { status: 400 });
  }

  const pdfPath = path.join(
    process.cwd(),
    '..',
    'cases',
    caseId,
    'output',
    `${caseId}_dossier.pdf`
  );

  return new Response(null, {
    status: existsSync(pdfPath) ? 200 : 404,
  });
}
