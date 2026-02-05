import { Card } from '@/components/ui/card';
import {
  AmbientHero,
  MetricCard,
  VerificationChart,
  WorkflowTable,
} from '@/components/Dashboard';

interface DashboardPageProps {
  params: Promise<{ caseId: string }>;
}

async function getDashboardData(caseId: string) {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000';
  const res = await fetch(`${baseUrl}/api/cases/${caseId}/dashboard`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error('Failed to fetch dashboard data');
  }

  return res.json();
}

export default async function DashboardPage({ params }: DashboardPageProps) {
  const { caseId } = await params;

  try {
    const data = await getDashboardData(caseId);

    return (
      <div className="dark">
        {/* Ambient Hero Header */}
        <AmbientHero
          caseId={caseId}
          dateRange={data.dateRange}
          metrics={{
            documents: data.metrics.documents,
            entities: data.metrics.entities,
            relationships: data.metrics.relationships,
          }}
          entityTypeSummary={data.entityTypeSummary}
        />

        {/* Main Content */}
        <div className="px-4 sm:px-6 lg:px-8 pb-8">
          <div className="max-w-6xl mx-auto space-y-8">
            {/* Metrics Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Stage Card */}
              <MetricCard
                label="Current Stage"
                value={data.metrics.stage}
                progress={{
                  value: data.metrics.stageProgress,
                  glowColor: 'blue',
                }}
                animationDelay={0}
              />

              {/* Documents Card */}
              <MetricCard
                label="Documents"
                value={data.metrics.documents}
                href={`/case/${caseId}/documents`}
                subtitle="View all →"
                animationDelay={0.1}
              />

              {/* Entities Card */}
              <MetricCard
                label="Entities"
                value={data.metrics.entities}
                href={`/case/${caseId}/entities`}
                subtitle={Object.entries(data.entityTypeSummary)
                  .map(([type, count]) => `${count} ${type.toLowerCase()}`)
                  .slice(0, 2)
                  .join(', ')}
                animationDelay={0.2}
              />

              {/* Relationships Card */}
              <MetricCard
                label="Relationships"
                value={data.metrics.relationships}
                href={`/case/${caseId}/graph`}
                subtitle="View graph →"
                animationDelay={0.3}
              />
            </div>

            {/* Verification Status */}
            <VerificationChart
              distribution={data.verificationDistribution}
              totalEntities={data.metrics.entities}
            />

            {/* Case Progression */}
            <div className="space-y-4">
              <h2 className="text-sm font-mono uppercase tracking-wider text-muted-foreground">
                Case Progression
              </h2>
              <WorkflowTable stages={data.workflowStages} caseId={caseId} />
            </div>
          </div>
        </div>
      </div>
    );
  } catch (error) {
    return (
      <div className="p-8 dark">
        <div className="max-w-6xl mx-auto">
          <header className="mb-8">
            <h1 className="text-4xl font-mono mb-2">Dashboard</h1>
            <p className="text-muted-foreground">Case: {caseId}</p>
          </header>

          <Card className="p-6">
            <p className="text-red-400 font-mono text-sm">
              Failed to load dashboard data
            </p>
          </Card>
        </div>
      </div>
    );
  }
}
