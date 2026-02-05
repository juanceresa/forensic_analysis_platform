import { EntityBrowser } from '@/components/Entities/EntityBrowser';

interface EntitiesPageProps {
  params: Promise<{ caseId: string }>;
}

async function getEntities(caseId: string) {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000';
  const res = await fetch(`${baseUrl}/api/cases/${caseId}/entities`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error('Failed to fetch entities');
  }

  return res.json();
}

export default async function EntitiesPage({ params }: EntitiesPageProps) {
  const { caseId } = await params;

  try {
    const data = await getEntities(caseId);

    return (
      <EntityBrowser
        entities={data.entities}
        totalCount={data.totalCount}
        documentCount={data.documentCount}
        caseId={caseId}
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
