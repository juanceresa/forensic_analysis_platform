import { DocumentViewer } from '@/components/Documents/DocumentViewer';

interface DocumentPageProps {
  params: Promise<{ caseId: string; docId: string }>;
}

async function fetchDocument(caseId: string, docId: string) {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000';
  const res = await fetch(`${baseUrl}/api/cases/${caseId}/document/${docId}`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error('Failed to fetch document');
  }

  return res.json();
}

export default async function DocumentPage({ params }: DocumentPageProps) {
  const { caseId, docId } = await params;
  const document = await fetchDocument(caseId, decodeURIComponent(docId));

  return <DocumentViewer document={document} caseId={caseId} />;
}
