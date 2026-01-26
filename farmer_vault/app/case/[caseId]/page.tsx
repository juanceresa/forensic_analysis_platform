import { Card } from '@/components/shared';

interface DashboardPageProps {
  params: Promise<{ caseId: string }>;
}

export default async function DashboardPage({ params }: DashboardPageProps) {
  const { caseId } = await params;

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <header className="mb-12">
          <h1 className="text-4xl font-mono mb-2">Dashboard</h1>
          <p className="text-slate-400">Case: {caseId}</p>
        </header>

        {/* Placeholder metrics */}
        <div className="grid grid-cols-4 gap-4">
          <Card>
            <div className="text-xs text-slate-400 font-mono uppercase tracking-wider">
              Stage
            </div>
            <div className="mt-2 text-3xl font-mono">Processing</div>
            <div className="mt-2 text-sm text-slate-400">68% complete</div>
          </Card>

          <Card>
            <div className="text-xs text-slate-400 font-mono uppercase tracking-wider">
              Documents
            </div>
            <div className="mt-2 text-4xl font-mono tabular-nums">18</div>
          </Card>

          <Card>
            <div className="text-xs text-slate-400 font-mono uppercase tracking-wider">
              Entities
            </div>
            <div className="mt-2 text-4xl font-mono tabular-nums">87</div>
          </Card>

          <Card>
            <div className="text-xs text-slate-400 font-mono uppercase tracking-wider">
              Relationships
            </div>
            <div className="mt-2 text-4xl font-mono tabular-nums">142</div>
          </Card>
        </div>

        <Card>
          <p className="text-slate-400">
            Full dashboard implementation coming in Phase 2. This placeholder demonstrates
            the new navigation structure with sidebar and header.
          </p>
        </Card>
      </div>
    </div>
  );
}
