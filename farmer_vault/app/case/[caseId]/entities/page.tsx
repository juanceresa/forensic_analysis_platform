import { EntityBrowser } from '@/components/Entities/EntityBrowser';
import { fetchServerApi } from '@/lib/server-api';

interface EntitiesPageProps {
  params: Promise<{ caseId: string }>;
}

async function getEntities(caseId: string) {
  const res = await fetchServerApi(`/api/cases/${caseId}/entities`);

  if (!res.ok) {
    throw new Error('Failed to fetch entities');
  }

  return res.json();
}

async function getTimelineEvents(caseId: string) {
  try {
    const res = await fetchServerApi(`/api/cases/${caseId}/timeline`);
    if (!res.ok) return [];
    const data = await res.json();
    // Only return high-signal events, not FILED
    return (data.events || []).filter(
      (e: any) => e.eventType !== 'FILED'
    );
  } catch {
    return [];
  }
}

export default async function EntitiesPage({ params }: EntitiesPageProps) {
  const { caseId } = await params;

  try {
    const [data, events] = await Promise.all([
      getEntities(caseId),
      getTimelineEvents(caseId),
    ]);

    return (
      <EntityBrowser
        entities={data.entities}
        totalCount={data.totalCount}
        documentCount={data.documentCount}
        caseId={caseId}
        events={events}
      />
    );
  } catch (error) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="max-w-4xl mx-auto">
          <header className="mb-8">
            <h1 className="text-2xl font-mono mb-2">Dictionary</h1>
            <p className="text-muted-foreground">Case: {caseId}</p>
          </header>

          <div className="p-8 bg-[var(--card)] border border-red-800/50 rounded text-center">
            <p className="text-red-400 font-mono text-sm">Failed to load entities</p>
          </div>
        </div>
      </div>
    );
  }
}
