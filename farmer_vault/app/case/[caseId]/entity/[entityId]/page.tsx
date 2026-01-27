import { EntityDetail } from '@/components/Entities/EntityDetail';

interface EntityPageProps {
  params: Promise<{ caseId: string; entityId: string }>;
}

async function fetchEntity(caseId: string, entityId: string) {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000';
  const res = await fetch(`${baseUrl}/api/cases/${caseId}/entity/${encodeURIComponent(entityId)}`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error('Failed to fetch entity');
  }

  return res.json();
}

export default async function EntityPage({ params }: EntityPageProps) {
  const { caseId, entityId } = await params;
  const data = await fetchEntity(caseId, decodeURIComponent(entityId));

  return <EntityDetail entity={data.entity} sourceDocuments={data.sourceDocuments} connections={data.connections} caseId={caseId} />;
}
