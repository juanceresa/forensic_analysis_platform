import { EntityDetail } from '@/components/Entities/EntityDetail';
import { fetchServerApi } from '@/lib/server-api';

interface EntityPageProps {
  params: Promise<{ caseId: string; entityId: string }>;
}

async function fetchEntity(caseId: string, entityId: string) {
  const res = await fetchServerApi(
    `/api/cases/${caseId}/entity/${encodeURIComponent(entityId)}`
  );

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
