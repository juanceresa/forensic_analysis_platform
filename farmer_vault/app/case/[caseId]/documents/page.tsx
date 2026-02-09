import { DocumentList } from '@/components/Documents/DocumentList';
import { fetchServerApi } from '@/lib/server-api';

interface DocumentsPageProps {
  params: Promise<{ caseId: string }>;
}

async function fetchDocuments(caseId: string) {
  const res = await fetchServerApi(`/api/cases/${caseId}/documents`);

  if (!res.ok) {
    throw new Error('Failed to fetch documents');
  }

  return res.json();
}

async function fetchEntities(caseId: string) {
  const res = await fetchServerApi(`/api/cases/${caseId}/entities`);

  if (!res.ok) {
    throw new Error('Failed to fetch entities');
  }

  return res.json();
}

export default async function DocumentsPage({ params }: DocumentsPageProps) {
  const { caseId } = await params;

  // Fetch documents and entities in parallel
  const [{ documents }, { entities }] = await Promise.all([
    fetchDocuments(caseId),
    fetchEntities(caseId),
  ]);

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="max-w-4xl mx-auto">
        <DocumentList documents={documents} entities={entities} caseId={caseId} />
      </div>
    </div>
  );
}
