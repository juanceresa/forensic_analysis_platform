interface HeroSectionProps {
  caseName: string;
  totalDocuments: number;
  dateRange?: {
    earliest_document?: string;
    latest_document?: string;
  };
}

export default function HeroSection({ caseName, totalDocuments, dateRange }: HeroSectionProps) {
  const earliest = dateRange?.earliest_document
    ? new Date(dateRange.earliest_document).getFullYear()
    : null;
  const latest = dateRange?.latest_document
    ? new Date(dateRange.latest_document).getFullYear()
    : null;

  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center text-center px-8">
      {/* Void atmosphere */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-slate-950/95 to-transparent pointer-events-none" />

      <div className="relative z-10 max-w-3xl space-y-6">
        {/* Classification marker */}
        <p className="font-mono text-[10px] uppercase tracking-[0.3em] text-slate-600">
          Forensic Intelligence Report
        </p>

        {/* Case name */}
        <h1 className="text-5xl md:text-6xl font-display tracking-tight text-slate-50 leading-[1.1]">
          {caseName}
        </h1>

        {/* Dossier rule */}
        <hr className="dossier-rule mx-auto w-48" />

        {/* Stats */}
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 tabular-nums">
          {totalDocuments} document{totalDocuments !== 1 ? 's' : ''}
          {earliest && latest && (
            <> &middot; {earliest} – {latest}</>
          )}
        </p>

        {/* AI Disclaimer */}
        <div className="inline-block px-4 py-2 bg-amber-500/5 border border-amber-500/15 rounded">
          <p className="text-[11px] text-amber-500/70 italic">
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
            AI-generated research analysis — not a legal document. All inferences are TIER_3_AI.
          </p>
        </div>
      </div>

      {/* Scroll chevron */}
      <div className="absolute bottom-12 left-1/2 -translate-x-1/2 z-10">
        <svg
          className="w-6 h-6 text-slate-600 animate-chevron-bounce"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </section>
  );
}
