import { Card } from '@/components/shared';

interface NarrativePageProps {
  params: Promise<{ caseId: string }>;
}

export default async function NarrativePage({ params }: NarrativePageProps) {
  const { caseId } = await params;

  return (
    <div className="p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <h1 className="text-2xl font-mono mb-2">Narrative</h1>
          <p className="text-slate-400">Case: {caseId}</p>
        </header>

        <Card>
          <p className="text-slate-400">
            Timeline narrative view coming soon. Will show expandable periods with supporting documents and entities.
          </p>
        </Card>
      </div>
    </div>
  );
}
