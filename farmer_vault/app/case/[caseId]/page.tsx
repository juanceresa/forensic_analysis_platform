// SERVER COMPONENT - Pre-fetches graph data
import { getGraphData } from '@/lib/graph-api';
import { DashboardClient } from './DashboardClient';
import { ErrorState } from '@/components/ErrorState';

export default async function CaseDashboard({
  params,
}: {
  params: Promise<{ caseId: string }>;
}) {
  try {
    // NEXT.JS 16: Await params Promise
    const { caseId } = await params;

    // PERFORMANCE: Server-side data fetching eliminates loading state
    const graphData = await getGraphData(caseId);

    return <DashboardClient initialData={graphData} caseId={caseId} />;
  } catch (error) {
    return <ErrorState error={error as Error} />;
  }
}
