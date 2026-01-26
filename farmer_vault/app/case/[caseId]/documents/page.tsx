import { Card } from '@/components/shared';

interface DocumentsPageProps {
  params: Promise<{ caseId: string }>;
}

export default async function DocumentsPage({ params }: DocumentsPageProps) {
  const { caseId } = await params;

  return (
    <div className="p-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <h1 className="text-2xl font-mono mb-2">Documents</h1>
          <p className="text-slate-400">Case: {caseId}</p>
        </header>

        <Card>
          <p className="text-slate-400">
            Document list view coming soon. Will show chronological list of all processed documents.
          </p>
        </Card>
      </div>
    </div>
  );
}
