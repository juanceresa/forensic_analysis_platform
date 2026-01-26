import { Card } from '@/components/shared';

interface GraphPageProps {
  params: Promise<{ caseId: string }>;
}

export default async function GraphPage({ params }: GraphPageProps) {
  const { caseId } = await params;

  return (
    <div className="p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <h1 className="text-2xl font-mono mb-2">Graph</h1>
          <p className="text-slate-400">Case: {caseId}</p>
        </header>

        <Card>
          <p className="text-slate-400">
            Knowledge graph visualization coming soon. Will integrate existing graph component with new navigation.
          </p>
        </Card>
      </div>
    </div>
  );
}
