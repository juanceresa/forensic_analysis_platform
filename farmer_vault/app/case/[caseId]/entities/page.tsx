import { Card } from '@/components/shared';

interface EntitiesPageProps {
  params: Promise<{ caseId: string }>;
}

export default async function EntitiesPage({ params }: EntitiesPageProps) {
  const { caseId } = await params;

  return (
    <div className="p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <h1 className="text-2xl font-mono mb-2">Entities</h1>
          <p className="text-slate-400">Case: {caseId}</p>
        </header>

        <Card>
          <p className="text-slate-400">
            Entity browser coming soon. Will show all entities grouped by type (Person, Property, Organization, Location).
          </p>
        </Card>
      </div>
    </div>
  );
}
