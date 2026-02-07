import { GraphView } from '@/components/Graph';

interface GraphPageProps {
  params: Promise<{ caseId: string }>;
}

export default async function NarrativeGraphPage({ params }: GraphPageProps) {
  const { caseId } = await params;

  return (
    <div className="absolute inset-0 overflow-hidden">
      <GraphView caseId={caseId} />
    </div>
  );
}
