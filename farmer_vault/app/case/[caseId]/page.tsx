import Link from 'next/link';
import { Card } from '@/components/shared';
import { DossierDownload } from '@/components/Dashboard';

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

const TIER_COLORS = {
  TIER_3_AI: { bg: 'bg-amber-500', label: 'AI Extracted' },
  TIER_2_ANALYST: { bg: 'bg-blue-500', label: 'Analyst Verified' },
  TIER_1_CERTIFIED: { bg: 'bg-emerald-500', label: 'Certified' },
  TIER_4_SOURCE: { bg: 'bg-purple-500', label: 'Source Document' },
};

function WorkflowChecklist({ stages }: { stages: any }) {
  const stageOrder = ['intake', 'processing', 'analysis', 'certification'] as const;
  const stageLabels = {
    intake: 'Intake',
    processing: 'Processing',
    analysis: 'Analysis',
    certification: 'Certification',
  };

  return (
    <div className="space-y-4">
      {stageOrder.map((stageKey) => {
        const stage = stages[stageKey];
        const isComplete = stage.complete;

        return (
          <details key={stageKey} className="group" open={!isComplete}>
            <summary className="flex items-center gap-3 cursor-pointer list-none
                               focus-visible:ring-2 focus-visible:ring-blue-500 rounded p-2 -m-2">
              {/* Status indicator */}
              <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0
                             ${isComplete ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-500'}`}>
                {isComplete ? (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <span className="text-xs font-mono">{stageOrder.indexOf(stageKey) + 1}</span>
                )}
              </div>

              <span className={`font-mono text-sm uppercase tracking-wider flex-1
                              ${isComplete ? 'text-slate-400' : 'text-slate-200'}`}>
                {stageLabels[stageKey]}
              </span>

              <svg
                className="w-4 h-4 text-slate-500 transition-transform group-open:rotate-180"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </summary>

            <div className="mt-3 ml-9 space-y-2">
              {stage.items.map((item: any, index: number) => (
                <div key={index} className="flex items-center gap-2 text-sm">
                  {item.complete ? (
                    <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <div className="w-4 h-4 border border-slate-600 rounded" />
                  )}
                  <span className={item.complete ? 'text-slate-400' : 'text-slate-300'}>
                    {item.label}
                  </span>
                </div>
              ))}
            </div>
          </details>
        );
      })}
    </div>
  );
}

export default async function DashboardPage({ params }: DashboardPageProps) {
  const { caseId } = await params;

  try {
    const data = await getDashboardData(caseId);

    const totalEntities = data.metrics.entities;
    const tierPercentages = Object.entries(data.verificationDistribution).map(([tier, count]) => ({
      tier,
      count: count as number,
      percent: totalEntities > 0 ? ((count as number) / totalEntities) * 100 : 0,
    }));

    return (
      <div className="p-8">
        <div className="max-w-6xl mx-auto space-y-8">
          {/* Header */}
          <header>
            <h1 className="text-4xl font-mono mb-2">Dashboard</h1>
            <p className="text-slate-400">
              Case: {caseId}
              {data.dateRange.earliest && data.dateRange.latest && (
                <span className="ml-4 text-slate-500">
                  Documents from {new Date(data.dateRange.earliest).getFullYear()} to{' '}
                  {new Date(data.dateRange.latest).getFullYear()}
                </span>
              )}
            </p>
          </header>

          {/* Metrics Grid */}
          <div className="grid grid-cols-4 gap-4">
            {/* Stage Card */}
            <Card>
              <div className="text-xs text-slate-500 font-mono uppercase tracking-wider">
                Current Stage
              </div>
              <div className="mt-2 text-2xl font-mono">{data.metrics.stage}</div>
              <div className="mt-3">
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 transition-all"
                      style={{ width: `${data.metrics.stageProgress}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-400 font-mono tabular-nums">
                    {data.metrics.stageProgress}%
                  </span>
                </div>
              </div>
            </Card>

            {/* Documents Card */}
            <Link href={`/case/${caseId}/documents`}>
              <Card className="hover:border-slate-700 transition-colors cursor-pointer h-full">
                <div className="text-xs text-slate-500 font-mono uppercase tracking-wider">
                  Documents
                </div>
                <div className="mt-2 text-4xl font-mono tabular-nums">{data.metrics.documents}</div>
                <div className="mt-2 text-xs text-slate-500">View all &rarr;</div>
              </Card>
            </Link>

            {/* Entities Card */}
            <Link href={`/case/${caseId}/entities`}>
              <Card className="hover:border-slate-700 transition-colors cursor-pointer h-full">
                <div className="text-xs text-slate-500 font-mono uppercase tracking-wider">
                  Entities
                </div>
                <div className="mt-2 text-4xl font-mono tabular-nums">{data.metrics.entities}</div>
                <div className="mt-2 text-xs text-slate-500">
                  {Object.entries(data.entityTypeSummary)
                    .map(([type, count]) => `${count} ${type.toLowerCase()}`)
                    .slice(0, 2)
                    .join(', ')}
                </div>
              </Card>
            </Link>

            {/* Relationships Card */}
            <Link href={`/case/${caseId}/graph`}>
              <Card className="hover:border-slate-700 transition-colors cursor-pointer h-full">
                <div className="text-xs text-slate-500 font-mono uppercase tracking-wider">
                  Relationships
                </div>
                <div className="mt-2 text-4xl font-mono tabular-nums">{data.metrics.relationships}</div>
                <div className="mt-2 text-xs text-slate-500">View graph &rarr;</div>
              </Card>
            </Link>
          </div>

          {/* Verification Status */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-mono uppercase tracking-wider text-slate-400">
                Verification Status
              </h2>
              <span className="text-xs text-slate-500 font-mono">
                {totalEntities} total entities
              </span>
            </div>

            {/* Progress Bar */}
            <div className="h-3 bg-slate-800 rounded-full overflow-hidden flex">
              {tierPercentages.map(({ tier, percent }) => (
                percent > 0 && (
                  <div
                    key={tier}
                    className={`${TIER_COLORS[tier as keyof typeof TIER_COLORS]?.bg || 'bg-slate-600'} transition-all`}
                    style={{ width: `${percent}%` }}
                    title={`${TIER_COLORS[tier as keyof typeof TIER_COLORS]?.label}: ${Math.round(percent)}%`}
                  />
                )
              ))}
            </div>

            {/* Legend */}
            <div className="mt-4 flex flex-wrap gap-4">
              {tierPercentages.map(({ tier, count, percent }) => (
                count > 0 && (
                  <div key={tier} className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded ${TIER_COLORS[tier as keyof typeof TIER_COLORS]?.bg || 'bg-slate-600'}`} />
                    <span className="text-xs text-slate-400">
                      {TIER_COLORS[tier as keyof typeof TIER_COLORS]?.label}: {count} ({Math.round(percent)}%)
                    </span>
                  </div>
                )
              ))}
            </div>
          </Card>

          {/* Case Progression Checklist */}
          <Card>
            <h2 className="text-sm font-mono uppercase tracking-wider text-slate-400 mb-6">
              Case Progression
            </h2>
            <WorkflowChecklist stages={data.workflowStages} />

            {/* Dossier Download - Final Deliverable */}
            <div className="mt-6 pt-6 border-t border-slate-800">
              <DossierDownload caseId={caseId} />
            </div>
          </Card>
        </div>
      </div>
    );
  } catch (error) {
    return (
      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          <header className="mb-8">
            <h1 className="text-4xl font-mono mb-2">Dashboard</h1>
            <p className="text-slate-400">Case: {caseId}</p>
          </header>

          <Card>
            <p className="text-red-400 font-mono text-sm">Failed to load dashboard data</p>
          </Card>
        </div>
      </div>
    );
  }
}
