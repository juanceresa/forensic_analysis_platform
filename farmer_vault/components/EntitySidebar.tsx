'use client';

import { useMemo } from 'react';
import type { BaseNode, GraphData } from '@/lib/types';
import { DossierPanel } from './DossierPanel';
import { NarrativePanel } from './NarrativePanel';
import { useNarrative } from '@/hooks/useNarrative';

type TabType = 'details' | 'narrative';

interface EntitySidebarProps {
  selectedNode: BaseNode | null;
  graphData: GraphData;
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  caseId: string;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export function EntitySidebar({
  selectedNode,
  graphData,
  activeTab,
  onTabChange,
  caseId,
  isCollapsed,
  onToggleCollapse,
}: EntitySidebarProps) {
  const { narrative, loading, error, generateNarrative } = useNarrative();
  const sessionId = useMemo(() => crypto.randomUUID(), []);

  const hasSelection = Boolean(selectedNode);

  // DEBUG: Log sidebar state
  console.log('EntitySidebar render:', {
    hasSelection,
    selectedNodeId: selectedNode?.id,
    activeTab,
    willRenderDossier: activeTab === 'details',
  });

  const handleGenerateNarrative = () => {
    if (selectedNode) {
      onTabChange('narrative');
      generateNarrative(caseId, selectedNode.id, sessionId);
    }
  };

  if (isCollapsed) {
    return (
      <div className="vault-panel vault-panel--strong w-12 shrink-0 border-l border-cyan-500/20 flex flex-col items-center relative group transition-colors duration-300 z-20">
        {/* Vertical scan line effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

        {/* Expand button - FULL HEIGHT CLICKABLE */}
        <button
          onClick={onToggleCollapse}
          aria-label="Expand sidebar"
          className="w-full flex-1 flex flex-col items-center justify-center text-cyan-300 hover:text-cyan-100 hover:bg-cyan-500/10 transition-colors transition-transform duration-200 relative z-10 group/btn gap-8"
          title="Expand Panel [Click anywhere]"
        >
          {/* Chevron icon - top */}
          <div className="flex items-center justify-center">
            <svg
              className="w-6 h-6 transition-transform group-hover/btn:translate-x-1 drop-shadow-[0_0_4px_rgba(6,182,212,0.5)]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              strokeWidth={2.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 5l7 7-7 7"
              />
            </svg>
          </div>

          {/* Vertical indicator dots - middle */}
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

          {/* Vertical text label - bottom */}
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
      {/* Holographic header bar */}
      <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent" />

      {/* ACCESSIBILITY: Tab Headers with ARIA attributes */}
      <div role="tablist" className="border-b border-cyan-500/15 flex relative">
        <button
          role="tab"
          aria-selected={activeTab === 'details'}
          aria-controls="details-panel"
          id="details-tab"
          onClick={() => onTabChange('details')}
          className={`flex-1 px-4 py-3 font-display text-sm uppercase tracking-wider transition-colors transition-shadow relative ${
            activeTab === 'details'
              ? 'bg-slate-800 text-cyan-300 border-b-2 border-cyan-400 shadow-[0_0_10px_rgba(6,182,212,0.3)]'
              : 'text-slate-400 hover:text-cyan-300 hover:bg-slate-800/50'
          }`}
        >
          Details
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'narrative'}
          aria-controls="narrative-panel"
          id="narrative-tab"
          onClick={() => hasSelection && onTabChange('narrative')}
          disabled={!hasSelection}
          className={`flex-1 px-4 py-3 font-display text-sm uppercase tracking-wider transition-colors transition-shadow relative ${
            activeTab === 'narrative'
              ? 'bg-slate-800 text-cyan-300 border-b-2 border-cyan-400 shadow-[0_0_10px_rgba(6,182,212,0.3)]'
              : hasSelection
              ? 'text-slate-400 hover:text-cyan-300 hover:bg-slate-800/50'
              : 'text-slate-600 cursor-not-allowed'
          }`}
        >
          Narrative
        </button>

        {/* Collapse button - integrated into tab bar */}
        <button
          onClick={onToggleCollapse}
          aria-label="Collapse sidebar"
          className="w-12 flex items-center justify-center text-cyan-400/60 hover:text-cyan-300 hover:bg-cyan-500/10 transition-colors transition-transform duration-200 border-l border-cyan-500/20 group"
          title="Collapse Panel"
        >
          <svg
            className="w-4 h-4 transition-transform group-hover:-translate-x-0.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>
      </div>

      {/* ACCESSIBILITY: Tab Panels with ARIA attributes */}
      <div className="flex-1 overflow-y-auto">
        <div
          role="tabpanel"
          id="details-panel"
          aria-labelledby="details-tab"
          hidden={activeTab !== 'details'}
        >
          {activeTab === 'details' && (
            <DossierPanel
              node={selectedNode}
              graphData={graphData}
              onGenerateNarrative={handleGenerateNarrative}
            />
          )}
        </div>
        <div
          role="tabpanel"
          id="narrative-panel"
          aria-labelledby="narrative-tab"
          hidden={activeTab !== 'narrative'}
        >
          {activeTab === 'narrative' && (
            <NarrativePanel
              narrative={narrative}
              loading={loading}
              error={error?.message || null}
            />
          )}
        </div>
      </div>
    </div>
  );
}
