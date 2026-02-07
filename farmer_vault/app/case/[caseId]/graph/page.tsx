import { redirect } from 'next/navigation';

interface GraphPageProps {
  params: Promise<{ caseId: string }>;
}

export default async function GraphPage({ params }: GraphPageProps) {
  const { caseId } = await params;
  redirect(`/case/${caseId}/narrative/graph`);
}
