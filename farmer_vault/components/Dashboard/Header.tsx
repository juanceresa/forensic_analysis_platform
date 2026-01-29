import type { GraphData } from '@/lib/types';

interface HeaderProps {
  graphData: GraphData;
  caseId: string;
}

export function Header({ graphData, caseId }: HeaderProps) {
  const { metadata } = graphData;

  return (
    <header className="border-b-2 border-cyan-500/20 bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 px-6 py-4 relative">
      {/* Holographic scan line */}
      <div className="absolute inset-0 bg-gradient-to-b from-cyan-500/5 via-transparent to-transparent opacity-50" />

      <div className="flex items-center justify-between relative">
        {/* Case ID with Active Indicator */}
        <div>
          <h1 className="text-3xl font-display tracking-wider text-cyan-50 flex items-center gap-2">
            {caseId}
            <span className="text-cyan-400 text-xl animate-pulse" aria-label="Active case" style={{
              textShadow: '0 0 10px rgba(6, 182, 212, 0.6)'
            }}>
              ●
            </span>
          </h1>
          <p className="text-xs text-cyan-400/70 uppercase tracking-widest font-mono mt-1">
            [ Forensic Intelligence • Tier System Active ]
          </p>
        </div>

        {/* Evidence Counters - Holographic Style */}
        <div className="flex gap-6">
          {[
            { label: 'Entities', count: metadata.entity_count, icon: '👤' },
            { label: 'Relations', count: metadata.relation_count, icon: '🔗' },
            { label: 'Documents', count: metadata.document_count, icon: '📄' },
          ].map(({ label, count, icon }) => (
            <div key={label} className="relative">
              {/* Cyan glow effect */}
              <div className="absolute -inset-1 bg-cyan-500/10 blur rounded-lg" />
              {/* Counter card */}
              <div className="relative bg-slate-900 border border-cyan-500/30 px-4 py-2 rounded backdrop-blur-sm">
                <div className="text-2xl font-mono font-bold text-cyan-300">
                  <span className="mr-1">{icon}</span>
                  {count}
                </div>
                <div className="text-[10px] text-cyan-500 uppercase tracking-wider font-display">
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
