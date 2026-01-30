import { GraphView } from '@/components/Graph';

interface GraphPageProps {
  params: Promise<{ caseId: string }>;
}

export default async function NarrativeGraphPage({ params }: GraphPageProps) {
  const { caseId } = await params;

  return (
    <div className="h-full">
      <GraphView caseId={caseId} />
    </div>
  );
}
