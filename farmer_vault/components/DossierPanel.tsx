import { useMemo } from 'react';
import type { BaseNode, GraphData } from '@/lib/types';
import { NodeBadge } from './NodeBadge';

interface DossierPanelProps {
  node: BaseNode | null;
  graphData: GraphData;
  onGenerateNarrative: () => void;
}

// PERFORMANCE: Hoist static JSX outside component
const EMPTY_STATE = (
  <div className="p-6 text-center text-slate-500 font-mono text-sm">
    <div className="mb-2 text-slate-600">◇</div>
    Click a node to view details
  </div>
);

export function DossierPanel({
  node,
  graphData,
  onGenerateNarrative,
}: DossierPanelProps) {
  // PERFORMANCE: Memoize expensive filter operation
  const relatedLinks = useMemo(
    () => graphData.links.filter(
      (l) => l.source === node?.id || l.target === node?.id
    ),
    [graphData.links, node?.id]
  );

  // PERFORMANCE: Memoize string split operation
  const sourceDocIds = useMemo(
    () => node?.extracted_from?.split(/\s*,\s*/) || [],
    [node?.extracted_from]
  );

  // DEBUG: Log dossier state
  console.log('DossierPanel render:', {
    hasNode: Boolean(node),
    nodeId: node?.id,
    nodeName: node?.name,
  });

  if (!node) return EMPTY_STATE;

  return (
    <div className="p-4 space-y-4">
      {/* Header - Enhanced Entity Card */}
      <div className="relative">
        {/* Holographic border glow */}
        <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500/20 via-blue-500/20 to-purple-500/20 rounded-lg blur-sm opacity-75" />

        {/* Card content */}
        <div className="relative bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border border-cyan-500/30 rounded-lg p-4 space-y-3 shadow-[0_0_20px_rgba(6,182,212,0.15)]">
          {/* Top bar with badge */}
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <h2 className="text-xl font-display uppercase tracking-wide text-cyan-50 truncate">
                {node.name || node.id}
              </h2>
              <p className="text-xs text-cyan-400/70 font-mono uppercase tracking-wider mt-1">
                {node.entity_type}
              </p>
            </div>
            <NodeBadge tier={node.verification.tier} />
          </div>

          {/* Node ID chip */}
          <div className="inline-flex items-center gap-2 px-2 py-1 bg-slate-950/50 border border-cyan-500/20 rounded text-[10px] font-mono text-slate-400">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_4px_rgba(6,182,212,0.6)]" />
            {node.id}
          </div>
        </div>
      </div>

      {/* Generate Narrative Button */}
      <button
        onClick={onGenerateNarrative}
        className="w-full min-h-[44px] px-4 py-2 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 rounded font-display text-sm uppercase tracking-wider transition-all shadow-lg hover:shadow-cyan-500/50 text-slate-900 font-bold"
        aria-label="Generate narrative for this entity"
        style={{
          textShadow: '0 0 10px rgba(6, 182, 212, 0.3)'
        }}
      >
        📖 Generate Intelligence Briefing
      </button>

      {/* Verification Info - Data Readout Style */}
      <section className="relative bg-gradient-to-br from-slate-900/50 to-slate-800/50 border border-cyan-500/20 rounded-lg p-4 backdrop-blur-sm">
        {/* Scan line animation */}
        <div className="absolute inset-0 bg-gradient-to-b from-cyan-500/5 via-transparent to-transparent rounded-lg pointer-events-none" />

        <div className="relative space-y-3">
          <h3 className="text-[10px] font-display uppercase tracking-widest text-cyan-400/70 flex items-center gap-2">
            <span className="w-1 h-1 rounded-full bg-cyan-400" />
            Verification Status
          </h3>

          {/* Confidence bar */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-slate-400">Confidence</span>
              <span className="font-mono text-sm text-cyan-300 font-bold">
                {(node.verification.confidence * 100).toFixed(0)}%
              </span>
            </div>
            <div className="h-1.5 bg-slate-950 rounded-full overflow-hidden border border-cyan-500/20">
              <div
                className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 shadow-[0_0_8px_rgba(6,182,212,0.5)] transition-all duration-1000"
                style={{ width: `${node.verification.confidence * 100}%` }}
              />
            </div>
          </div>

          {node.verification.tier === 'TIER_3_AI' && (
            <div className="p-2.5 bg-cyan-950/20 border border-cyan-600/40 rounded flex items-start gap-2">
              <span className="text-cyan-400 text-sm">⚠️</span>
              <p className="text-xs text-cyan-300 font-mono leading-relaxed">
                UNVERIFIED: AI-extracted data. Requires analyst review.
              </p>
            </div>
          )}
        </div>
      </section>

      {/* Related Entities - Connection Graph */}
      {relatedLinks.length > 0 && (
        <section className="bg-gradient-to-br from-slate-900/50 to-slate-800/50 border border-blue-500/20 rounded-lg p-4 backdrop-blur-sm">
          <h3 className="text-[10px] font-display uppercase tracking-widest text-blue-400/70 mb-3 flex items-center gap-2">
            <span className="w-1 h-1 rounded-full bg-blue-400" />
            Connected Entities ({relatedLinks.length})
          </h3>
          <ul className="space-y-2">
            {relatedLinks.slice(0, 5).map((link, idx) => {
              const otherId = link.source === node.id ? link.target : link.source;
              const otherNode = graphData.nodes.find((n) => n.id === otherId);
              return (
                <li key={idx} className="group">
                  <div className="flex items-center gap-2 p-2 rounded bg-slate-950/30 border border-blue-500/10 hover:border-blue-400/30 hover:bg-blue-950/20 transition-all">
                    {/* Relation type badge */}
                    <span className="px-2 py-0.5 bg-blue-500/20 border border-blue-400/30 rounded text-[10px] font-mono text-blue-300 uppercase tracking-wider whitespace-nowrap">
                      {link.relation_type}
                    </span>
                    {/* Arrow */}
                    <svg className="w-3 h-3 text-blue-400/50 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    {/* Entity name */}
                    <span className="text-sm text-slate-300 truncate font-body group-hover:text-blue-200 transition-colors">
                      {otherNode?.name || otherId}
                    </span>
                  </div>
                </li>
              );
            })}
            {relatedLinks.length > 5 && (
              <li className="text-slate-500 italic text-xs font-mono pl-2 pt-1">
                +{relatedLinks.length - 5} more connections
              </li>
            )}
          </ul>
        </section>
      )}

      {/* Source Documents - Evidence Archive */}
      {sourceDocIds.length > 0 && (
        <section className="bg-gradient-to-br from-slate-900/50 to-slate-800/50 border border-purple-500/20 rounded-lg p-4 backdrop-blur-sm">
          <h3 className="text-[10px] font-display uppercase tracking-widest text-purple-400/70 mb-3 flex items-center gap-2">
            <span className="w-1 h-1 rounded-full bg-purple-400" />
            Evidence Archive ({sourceDocIds.length})
          </h3>
          <ul className="space-y-1.5">
            {sourceDocIds.slice(0, 5).map((docId, idx) => (
              <li key={idx} className="group">
                <div className="flex items-start gap-2 p-2 rounded bg-slate-950/30 border border-purple-500/10 hover:border-purple-400/30 hover:bg-purple-950/20 transition-all">
                  <svg className="w-4 h-4 text-purple-400/50 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span className="text-xs font-mono text-slate-400 group-hover:text-purple-300 transition-colors break-all">
                    {docId}
                  </span>
                </div>
              </li>
            ))}
            {sourceDocIds.length > 5 && (
              <li className="text-slate-500 italic text-xs font-mono pl-2 pt-1">
                +{sourceDocIds.length - 5} more documents
              </li>
            )}
          </ul>
        </section>
      )}
    </div>
  );
}
