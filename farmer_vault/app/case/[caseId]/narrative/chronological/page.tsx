import { TimelineView } from '@/components/Timeline';

interface ChronologicalPageProps {
  params: Promise<{ caseId: string }>;
}

async function getTimeline(caseId: string) {
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000';
  const res = await fetch(`${baseUrl}/api/cases/${caseId}/timeline`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error('Failed to fetch timeline');
  }

  return res.json();
}

export default async function ChronologicalPage({ params }: ChronologicalPageProps) {
  const { caseId } = await params;

  try {
    const data = await getTimeline(caseId);

    return (
      <div className="p-8">
        <div className="max-w-5xl mx-auto">
          <header className="mb-6">
            <h1 className="text-4xl font-display tracking-tight text-slate-50 mb-1">
              Chronological View
            </h1>
            <hr className="dossier-rule mt-4 mb-2" />
            <p className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
              {data.totalDocuments} documents spanning{' '}
              {data.dateRange?.earliest_document && data.dateRange?.latest_document
                ? `${new Date(data.dateRange.earliest_document).getFullYear()} – ${new Date(data.dateRange.latest_document).getFullYear()}`
                : 'multiple years'}
            </p>
          </header>

          <div className="mb-8 px-4 py-2 bg-amber-500/5 border border-amber-500/15 rounded">
            <p className="text-xs text-amber-500/70 italic">
              <svg
                className="inline-block w-3.5 h-3.5 mr-1.5 -mt-0.5 text-amber-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              AI-generated research analysis — not a legal document, no evidentiary value. All inferences are TIER_3_AI.
            </p>
          </div>

          {(!data.events || data.events.length === 0) ? (
            <div className="p-8 bg-slate-900 border border-slate-800 border-dashed rounded text-center">
              <p className="text-slate-500 font-mono text-sm">No timeline data available</p>
            </div>
          ) : (
            <section>
              <h2 className="text-xs font-mono uppercase tracking-[0.2em] text-slate-500 border-l-2 border-slate-600 pl-3 mb-6">
                Chronological Analysis
              </h2>
              <TimelineView
                events={data.events}
                gaps={data.gaps || []}
                periods={data.periods}
                caseId={caseId}
              />
            </section>
          )}
        </div>
      </div>
    );
  } catch {
    return (
      <div className="p-8">
        <div className="max-w-5xl mx-auto">
          <header className="mb-8">
            <h1 className="text-4xl font-display tracking-tight text-slate-50">Chronological View</h1>
            <hr className="dossier-rule mt-4 mb-2" />
          </header>
          <div className="p-8 bg-slate-900 border border-red-800/50 rounded text-center">
            <p className="text-red-400 font-mono text-sm">Failed to load timeline data</p>
          </div>
        </div>
      </div>
    );
  }
}
