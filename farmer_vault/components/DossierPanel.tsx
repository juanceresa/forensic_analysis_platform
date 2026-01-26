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

  if (!node) return EMPTY_STATE;

  return (
    <div className="p-4 space-y-4">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-start justify-between">
          <h2 className="text-xl font-display uppercase tracking-wide">
            {node.name || node.id}
          </h2>
          <NodeBadge tier={node.verification.tier} />
        </div>
        <p className="text-xs text-slate-400 font-mono uppercase tracking-wider">
          {node.entity_type} • {node.id}
        </p>
      </div>

      {/* Generate Narrative Button */}
      <button
        onClick={onGenerateNarrative}
        className="w-full min-h-[44px] px-4 py-2 bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-600 rounded font-display text-sm uppercase tracking-wider transition-all shadow-lg hover:shadow-amber-500/50"
        aria-label="Generate narrative for this entity"
      >
        📖 Generate Intelligence Briefing
      </button>

      {/* Verification Info */}
      <section className="bg-slate-800 border border-slate-700 rounded p-3 space-y-2">
        <h3 className="text-xs font-display uppercase tracking-wider text-slate-300">
          Verification Status
        </h3>
        <p className="text-sm text-slate-300">
          Confidence:{' '}
          <span className="font-mono text-amber-400">
            {(node.verification.confidence * 100).toFixed(0)}%
          </span>
        </p>
        {node.verification.tier === 'TIER_3_AI' && (
          <div className="mt-2 p-2 bg-amber-950/50 border border-amber-700/50 rounded">
            <p className="text-xs text-amber-400 font-mono">
              ⚠️ UNVERIFIED: AI-extracted data. Requires analyst review.
            </p>
          </div>
        )}
      </section>

      {/* Related Entities */}
      {relatedLinks.length > 0 && (
        <section className="bg-slate-800 border border-slate-700 rounded p-3">
          <h3 className="text-xs font-display uppercase tracking-wider text-slate-300 mb-2">
            Related Entities ({relatedLinks.length})
          </h3>
          <ul className="space-y-1 text-sm">
            {relatedLinks.slice(0, 5).map((link, idx) => {
              const otherId = link.source === node.id ? link.target : link.source;
              const otherNode = graphData.nodes.find((n) => n.id === otherId);
              return (
                <li key={idx} className="text-slate-300">
                  <span className="font-mono text-xs text-amber-500">
                    {link.relation_type}
                  </span>
                  {' → '}
                  <span className="font-body">{otherNode?.name || otherId}</span>
                </li>
              );
            })}
            {relatedLinks.length > 5 && (
              <li className="text-slate-500 italic text-xs font-mono">
                +{relatedLinks.length - 5} more relations
              </li>
            )}
          </ul>
        </section>
      )}

      {/* Source Documents */}
      {sourceDocIds.length > 0 && (
        <section className="bg-slate-800 border border-slate-700 rounded p-3">
          <h3 className="text-xs font-display uppercase tracking-wider text-slate-300 mb-2">
            Source Documents ({sourceDocIds.length})
          </h3>
          <ul className="space-y-1 text-xs font-mono">
            {sourceDocIds.slice(0, 5).map((docId, idx) => (
              <li key={idx} className="text-slate-400">
                📄 {docId}
              </li>
            ))}
            {sourceDocIds.length > 5 && (
              <li className="text-slate-500 italic">
                +{sourceDocIds.length - 5} more sources
              </li>
            )}
          </ul>
        </section>
      )}
    </div>
  );
}
