import { DocumentViewer } from '@/components/Documents/DocumentViewer';
import { fetchServerApi } from '@/lib/server-api';

interface DocumentPageProps {
  params: Promise<{ caseId: string; docId: string }>;
}

async function fetchDocument(caseId: string, docId: string) {
  const res = await fetchServerApi(`/api/cases/${caseId}/document/${docId}`);

  if (!res.ok) {
    throw new Error('Failed to fetch document');
  }

  return res.json();
}

export default async function DocumentPage({ params }: DocumentPageProps) {
  const { caseId, docId } = await params;
  const document = await fetchDocument(caseId, decodeURIComponent(docId));

  return (
    <div className="h-[calc(100vh-3rem)]">
      <DocumentViewer document={document} caseId={caseId} />
    </div>
  );
}
