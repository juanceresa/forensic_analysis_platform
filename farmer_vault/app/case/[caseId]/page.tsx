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
  TIER_3_AI: { bg: 'bg-amber-500', hex: '#f59e0b', label: 'AI Extracted' },
  TIER_2_ANALYST: { bg: 'bg-blue-500', hex: '#3b82f6', label: 'Analyst Verified' },
  TIER_1_CERTIFIED: { bg: 'bg-emerald-500', hex: '#10b981', label: 'Certified' },
  TIER_4_SOURCE: { bg: 'bg-purple-500', hex: '#a855f7', label: 'Source Document' },
};

function WorkflowChecklist({ stages, caseId }: { stages: any; caseId: string }) {
  const stageOrder = ['intake', 'processing', 'analysis', 'certification'] as const;
  const stageLabels = {
    intake: 'Intake',
    processing: 'Processing',
    analysis: 'Analysis',
    certification: 'Certification',
  };

  // Calculate stats for each stage
  const stageStats = stageOrder.map((stageKey) => {
    const stage = stages[stageKey];
    const total = stage.items.length;
    const completed = stage.items.filter((item: any) => item.complete).length;
    const remaining = total - completed;
    const percent = total > 0 ? (completed / total) * 100 : 0;
    return { stageKey, stage, total, completed, remaining, percent, isComplete: stage.complete };
  });

  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{
        backgroundColor: '#161616',
        border: '1px solid #222222',
      }}
    >
      {/* Table Header */}
      <div
        className="grid gap-4 px-4 py-3"
        style={{
          gridTemplateColumns: '1fr 100px 80px 100px',
          borderBottom: '1px solid #222222',
        }}
      >
        <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'rgba(255,255,255,0.4)' }}>
          Stage
        </span>
        <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'rgba(255,255,255,0.4)', textAlign: 'center' }}>
          Progress
        </span>
        <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'rgba(255,255,255,0.4)', textAlign: 'center' }}>
          Tasks
        </span>
        <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'rgba(255,255,255,0.4)', textAlign: 'right' }}>
          Status
        </span>
      </div>

      {/* Table Rows */}
      {stageStats.map(({ stageKey, stage, total, completed, remaining, percent, isComplete }, index) => (
        <details key={stageKey} className="group" open={!isComplete && remaining > 0}>
          {/* Row */}
          <summary
            className="grid gap-4 px-4 py-3 cursor-pointer list-none transition-colors hover:bg-white/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-inset"
            style={{
              gridTemplateColumns: '1fr 100px 80px 100px',
              borderBottom: index < stageStats.length - 1 ? '1px solid #1a1a1a' : 'none',
            }}
          >
            {/* Stage Name with Chevron */}
            <div className="flex items-center gap-2">
              <svg
                className="w-4 h-4 text-slate-500 transition-transform duration-200 group-open:rotate-90"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <span className="text-sm font-medium text-slate-200">
                {stageLabels[stageKey]}
              </span>
            </div>

            {/* Mini Progress Bar */}
            <div className="flex items-center justify-center">
              <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: 'rgba(255,255,255,0.1)' }}>
                <div
                  className="h-full rounded-full transition-all duration-300"
                  style={{
                    width: `${percent}%`,
                    backgroundColor: isComplete ? '#10b981' : '#3b82f6',
                    boxShadow: isComplete ? '0 0 8px rgba(16, 185, 129, 0.5)' : '0 0 8px rgba(59, 130, 246, 0.5)',
                  }}
                />
              </div>
            </div>

            {/* Tasks Count */}
            <div className="flex items-center justify-center">
              <span className="text-sm font-mono tabular-nums" style={{ color: 'rgba(255,255,255,0.6)' }}>
                {completed}/{total}
              </span>
            </div>

            {/* Status Badge */}
            <div className="flex items-center justify-end">
              {isComplete ? (
                <span
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
                  style={{ backgroundColor: 'rgba(16, 185, 129, 0.15)', color: '#34d399' }}
                >
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Done
                </span>
              ) : remaining === total ? (
                <span
                  className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                  style={{ backgroundColor: 'rgba(255, 255, 255, 0.05)', color: 'rgba(255,255,255,0.4)' }}
                >
                  Pending
                </span>
              ) : (
                <span
                  className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                  style={{ backgroundColor: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa' }}
                >
                  In Progress
                </span>
              )}
            </div>
          </summary>

          {/* Expanded Tasks */}
          <div
            className="px-4 py-3 space-y-2"
            style={{
              backgroundColor: 'rgba(0, 0, 0, 0.2)',
              borderBottom: index < stageStats.length - 1 ? '1px solid #1a1a1a' : 'none',
            }}
          >
            {stage.items.map((item: any, itemIndex: number) => (
              <div
                key={itemIndex}
                className="flex items-center gap-3 py-1.5 px-2 rounded-lg transition-colors hover:bg-white/5"
                style={{ marginLeft: '20px' }}
              >
                {/* Checkbox */}
                {item.complete ? (
                  <div
                    className="w-5 h-5 rounded flex items-center justify-center shrink-0"
                    style={{ backgroundColor: 'rgba(16, 185, 129, 0.2)' }}
                  >
                    <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                ) : (
                  <div
                    className="w-5 h-5 rounded shrink-0"
                    style={{ border: '1.5px solid rgba(255,255,255,0.2)' }}
                  />
                )}
                {/* Task Label */}
                <span
                  className="text-sm"
                  style={{ color: item.complete ? 'rgba(255,255,255,0.4)' : 'rgba(255,255,255,0.7)' }}
                >
                  {item.label}
                </span>
              </div>
            ))}
          </div>
        </details>
      ))}

      {/* Dossier Download Footer */}
      <div
        className="px-4 py-4"
        style={{ borderTop: '1px solid #222222' }}
      >
        <DossierDownload caseId={caseId} />
      </div>
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

    // Format date range for display
    const dateRangeText = data.dateRange.earliest && data.dateRange.latest
      ? `${new Date(data.dateRange.earliest).getFullYear()} — ${new Date(data.dateRange.latest).getFullYear()}`
      : null;

    return (
      <div>
        {/* Ambient Hero Header */}
        <header className="relative overflow-hidden" style={{ minHeight: '180px' }}>
          {/* Background Image Layer */}
          <div
            className="absolute inset-0"
            style={{
              backgroundImage: 'url(https://images.unsplash.com/photo-1639322537228-f710d846310a?w=1920&q=80)',
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              opacity: 0.08,
              filter: 'grayscale(100%)',
            }}
          />

          {/* Gradient Overlay */}
          <div
            className="absolute inset-0"
            style={{
              background: 'linear-gradient(180deg, transparent 0%, #0D0D0D 85%)',
            }}
          />

          {/* Subtle Top Glow */}
          <div
            className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[200px]"
            style={{
              background: 'radial-gradient(ellipse at center, rgba(167, 243, 208, 0.06) 0%, transparent 70%)',
              pointerEvents: 'none',
            }}
          />

          {/* Content */}
          <div className="relative z-10 max-w-6xl mx-auto px-8 pt-10 pb-8">
            {/* Case ID Badge */}
            <div className="flex items-center gap-3 mb-4">
              <span
                className="inline-flex items-center px-2.5 py-1 rounded-md"
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  fontSize: '10px',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.1em',
                  color: 'rgba(255, 255, 255, 0.5)',
                }}
              >
                Case File
              </span>
              {dateRangeText && (
                <span
                  className="inline-flex items-center gap-1.5"
                  style={{
                    fontSize: '10px',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    color: 'rgba(255, 255, 255, 0.3)',
                  }}
                >
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  {dateRangeText}
                </span>
              )}
            </div>

            {/* Case Name */}
            <h1
              className="font-mono tracking-tight"
              style={{
                fontSize: '2.5rem',
                fontWeight: 600,
                color: '#f1f5f9',
                lineHeight: 1.1,
              }}
            >
              {caseId}
            </h1>

            {/* Quick Stats Row */}
            <div className="flex items-center gap-6 mt-4">
              <div className="flex items-center gap-2">
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: '#A7F3D0', boxShadow: '0 0 6px rgba(167, 243, 208, 0.5)' }}
                />
                <span style={{ fontSize: '12px', color: 'rgba(255, 255, 255, 0.5)' }}>
                  <strong style={{ color: 'rgba(255, 255, 255, 0.8)' }}>{data.metrics.documents}</strong> documents
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: '#3b82f6', boxShadow: '0 0 6px rgba(59, 130, 246, 0.5)' }}
                />
                <span style={{ fontSize: '12px', color: 'rgba(255, 255, 255, 0.5)' }}>
                  <strong style={{ color: 'rgba(255, 255, 255, 0.8)' }}>{data.metrics.entities}</strong> entities
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: '#a855f7', boxShadow: '0 0 6px rgba(168, 85, 247, 0.5)' }}
                />
                <span style={{ fontSize: '12px', color: 'rgba(255, 255, 255, 0.5)' }}>
                  <strong style={{ color: 'rgba(255, 255, 255, 0.8)' }}>{data.metrics.relationships}</strong> relationships
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <div className="px-8 pb-8">
          <div className="max-w-6xl mx-auto space-y-8">

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
                      style={{
                        width: `${data.metrics.stageProgress}%`,
                        boxShadow: '0 0 12px rgba(59, 130, 246, 0.5)',
                      }}
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
              {tierPercentages.map(({ tier, percent }) => {
                const tierConfig = TIER_COLORS[tier as keyof typeof TIER_COLORS];
                return percent > 0 && (
                  <div
                    key={tier}
                    className={`${tierConfig?.bg || 'bg-slate-600'} transition-all`}
                    style={{
                      width: `${percent}%`,
                      boxShadow: tierConfig?.hex ? `0 0 14px ${tierConfig.hex}80` : undefined,
                    }}
                    title={`${tierConfig?.label}: ${Math.round(percent)}%`}
                  />
                );
              })}
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

          {/* Case Progression */}
          <div className="space-y-4">
            <h2 className="text-sm font-mono uppercase tracking-wider text-slate-400">
              Case Progression
            </h2>
            <WorkflowChecklist stages={data.workflowStages} caseId={caseId} />
          </div>

          </div>
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
