import { DocumentList } from '@/components/Documents/DocumentList';

interface DocumentsPageProps {
  params: Promise<{ caseId: string }>;
}

async function fetchDocuments(caseId: string) {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000';
  const res = await fetch(`${baseUrl}/api/cases/${caseId}/documents`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error('Failed to fetch documents');
  }

  return res.json();
}

async function fetchEntities(caseId: string) {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000';
  const res = await fetch(`${baseUrl}/api/cases/${caseId}/entities`, {
    cache: 'no-store',
  });

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
