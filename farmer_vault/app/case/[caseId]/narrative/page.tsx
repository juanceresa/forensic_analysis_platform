import HeroSection from '@/components/Timeline/HeroSection';
import ScrollTimeline from '@/components/Timeline/ScrollTimeline';
import PlaceholderSection from '@/components/Timeline/PlaceholderSection';
import { fetchServerApi } from '@/lib/server-api';

interface NarrativePageProps {
  params: Promise<{ caseId: string }>;
}

async function getTimeline(caseId: string) {
  const res = await fetchServerApi(`/api/cases/${caseId}/timeline`);

  if (!res.ok) {
    throw new Error('Failed to fetch timeline');
  }

  return res.json();
}

export default async function NarrativePage({ params }: NarrativePageProps) {
  const { caseId } = await params;

  try {
    const data = await getTimeline(caseId);

    // Enrich events with narrative text from periods
    const periodMap = new Map<string, string>();
    if (data.periods) {
      for (const p of data.periods) {
        if (p.narrative) periodMap.set(p.id, p.narrative);
      }
    }

    const enrichedEvents = (data.events || []).map((e: Record<string, unknown>) => ({
      ...e,
      narrative: periodMap.get(e.periodId as string) || null,
    }));

    return (
      <div>
        <HeroSection
          caseName={caseId.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
          totalDocuments={data.totalDocuments || 0}
          dateRange={data.dateRange}
        />

        <ScrollTimeline
          events={enrichedEvents}
          gaps={data.gaps || []}
          caseId={caseId}
        />

        <PlaceholderSection
          title="Geolocation"
          description="Property geolocation mapping with historical boundary overlays and document-linked markers."
          icon={
            <svg className="w-8 h-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          }
        />

        <PlaceholderSection
          title="Knowledge Graph"
          description="Interactive entity relationship visualization with document provenance trails."
          icon={
            <svg className="w-8 h-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
          }
        />
      </div>
    );
  } catch {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="max-w-5xl mx-auto">
          <header className="mb-8">
            <h1 className="text-2xl sm:text-4xl font-display tracking-tight text-foreground">AI Analysis</h1>
            <hr className="dossier-rule mt-4 mb-2" />
          </header>
          <div className="p-8 bg-[var(--card)] border border-red-800/50 rounded text-center">
            <p className="text-red-400 font-mono text-sm">Failed to load timeline data</p>
          </div>
        </div>
      </div>
    );
  }
}
