'use client';

import { useEffect, useState } from 'react';
import { EntityDetail } from '../Entities/EntityDetail';
import type { BaseNode } from '@/lib/types';

interface EntityData {
  entity: BaseNode;
  sourceDocuments: { id: string; filename: string }[];
  connections: {
    relation_type: string;
    targetEntity: {
      id: string;
      name: string;
      entity_type: string;
      verification: { tier: string; confidence: number };
    };
  }[];
}

interface EntitySidebarProps {
  selectedNodeId: string | null;
  caseId: string;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export function EntitySidebar({
  selectedNodeId,
  caseId,
  isCollapsed,
  onToggleCollapse,
}: EntitySidebarProps) {
  const [entityData, setEntityData] = useState<EntityData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedNodeId) {
      setEntityData(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetch(`/api/cases/${caseId}/entity/${encodeURIComponent(selectedNodeId)}`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch entity');
        return res.json();
      })
      .then((data) => {
        if (!cancelled) setEntityData(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  }, [caseId, selectedNodeId]);

  const hasSelection = Boolean(selectedNodeId);

  if (isCollapsed) {
    return (
      <div className="vault-panel vault-panel--strong w-12 shrink-0 border-l border-cyan-500/20 flex flex-col items-center relative group transition-colors duration-300 z-20">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

        <button
          onClick={onToggleCollapse}
          aria-label="Expand sidebar"
          className="w-full flex-1 flex flex-col items-center justify-center text-cyan-300 hover:text-cyan-100 hover:bg-cyan-500/10 transition-colors transition-transform duration-200 relative z-10 group/btn gap-8"
          title="Expand Panel [Click anywhere]"
        >
          <div className="flex items-center justify-center">
            <svg
              className="w-6 h-6 transition-transform group-hover/btn:translate-x-1 drop-shadow-[0_0_4px_rgba(6,182,212,0.5)]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              strokeWidth={2.5}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </div>

          <div className="flex flex-col items-center gap-3">
            {hasSelection && (
              <div
                className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse motion-reduce:animate-none shadow-[0_0_8px_rgba(6,182,212,0.6)]"
                title="Node selected"
              />
            )}
            <div className="w-1.5 h-1.5 rounded-full bg-slate-600/50" />
            <div className="w-1.5 h-1.5 rounded-full bg-slate-600/50" />
            <div className="w-1.5 h-1.5 rounded-full bg-slate-600/50" />
          </div>

          <div>
            <div
              className="text-[10px] font-display uppercase tracking-widest text-slate-400 origin-center group-hover/btn:text-cyan-300 transition-colors"
              style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}
            >
              Panel
            </div>
          </div>
        </button>
      </div>
    );
  }

  return (
    <div className="vault-panel vault-panel--strong w-[500px] shrink-0 border-l border-cyan-500/20 flex flex-col relative transition-colors duration-300">
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent" />

      {/* Header with collapse button */}
      <div className="border-b border-cyan-500/15 flex items-center relative">
        <div className="flex-1 px-4 py-3 font-display text-sm uppercase tracking-wider text-cyan-300">
          Entity Details
        </div>
        <button
          onClick={onToggleCollapse}
          aria-label="Collapse sidebar"
          className="w-12 h-full flex items-center justify-center text-cyan-400/60 hover:text-cyan-300 hover:bg-cyan-500/10 transition-colors transition-transform duration-200 border-l border-cyan-500/20 group"
          title="Collapse Panel"
        >
          <svg
            className="w-4 h-4 transition-transform group-hover:-translate-x-0.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {!selectedNodeId && (
          <div className="flex items-center justify-center h-full p-8">
            <p className="text-slate-500 font-mono text-sm text-center">
              Select a node in the graph to view entity details
            </p>
          </div>
        )}

        {selectedNodeId && loading && (
          <div className="flex items-center justify-center h-full p-8">
            <div className="text-center">
              <div className="animate-spin motion-reduce:animate-none rounded-full h-8 w-8 border-b-2 border-cyan-400 mx-auto mb-3" />
              <p className="text-slate-400 font-mono text-sm">Loading entity...</p>
            </div>
          </div>
        )}

        {selectedNodeId && error && (
          <div className="p-6">
            <div className="p-4 bg-slate-900 border border-red-800/50 rounded">
              <p className="text-red-400 font-mono text-sm">{error}</p>
            </div>
          </div>
        )}

        {selectedNodeId && !loading && !error && entityData && (
          <EntityDetail
            entity={entityData.entity}
            sourceDocuments={entityData.sourceDocuments}
            connections={entityData.connections}
            caseId={caseId}
          />
        )}
      </div>
    </div>
  );
}
