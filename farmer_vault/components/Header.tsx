import type { GraphData } from '@/lib/types';

interface HeaderProps {
  graphData: GraphData;
  caseId: string;
}

export function Header({ graphData, caseId }: HeaderProps) {
  const { metadata } = graphData;

  return (
    <header className="border-b-2 border-amber-500/20 bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Case ID with Active Indicator */}
        <div>
          <h1 className="text-3xl font-display tracking-wider text-amber-100 flex items-center gap-2">
            {caseId}
            <span className="text-red-500 text-xl animate-pulse" aria-label="Active case">
              ●
            </span>
          </h1>
          <p className="text-xs text-amber-500/70 uppercase tracking-widest font-mono mt-1">
            [ Forensic Intelligence • Tier System Active ]
          </p>
        </div>

        {/* Evidence Counters - Stamp Style */}
        <div className="flex gap-6">
          {[
            { label: 'Entities', count: metadata.entity_count, icon: '👤' },
            { label: 'Relations', count: metadata.relation_count, icon: '🔗' },
            { label: 'Documents', count: metadata.document_count, icon: '📄' },
          ].map(({ label, count, icon }) => (
            <div key={label} className="relative">
              {/* Glow effect */}
              <div className="absolute -inset-1 bg-amber-500/10 blur rounded-lg" />
              {/* Counter card */}
              <div className="relative bg-slate-900 border border-amber-500/30 px-4 py-2 rounded">
                <div className="text-2xl font-mono font-bold text-amber-400">
                  <span className="mr-1">{icon}</span>
                  {count}
                </div>
                <div className="text-[10px] text-amber-600 uppercase tracking-wider font-display">
                  {label}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </header>
  );
}
