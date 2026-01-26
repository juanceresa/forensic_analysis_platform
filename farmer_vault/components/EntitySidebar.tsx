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

  return (
    <div
      className={`shrink-0 border-l border-cyan-500/20 flex flex-col bg-slate-900 z-10 ${
        isCollapsed ? 'w-12' : 'w-[500px]'
      }`}
    >
      <div className="border-b border-cyan-500/20 flex items-center justify-between">
        <div className="px-3 py-2 text-xs font-display uppercase tracking-wider text-slate-400">
          Panel
        </div>
        <button
          onClick={onToggleCollapse}
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className="min-h-[44px] px-3 text-cyan-300 hover:text-cyan-200 transition-colors"
          title={isCollapsed ? 'Expand' : 'Collapse'}
        >
          {isCollapsed ? '›' : '‹'}
        </button>
      </div>

      {isCollapsed ? (
        <button
          onClick={onToggleCollapse}
          className="flex-1 flex items-center justify-center text-slate-400 hover:text-cyan-200 transition-colors"
          aria-label="Expand sidebar"
        >
          ◂
        </button>
      ) : (
        <>
      {/* ACCESSIBILITY: Tab Headers with ARIA attributes */}
      <div role="tablist" className="border-b border-cyan-500/20 flex">
        <button
          role="tab"
          aria-selected={activeTab === 'details'}
          aria-controls="details-panel"
          id="details-tab"
          onClick={() => onTabChange('details')}
          className={`flex-1 px-4 py-3 font-display text-sm uppercase tracking-wider transition-all ${
            activeTab === 'details'
              ? 'bg-slate-800 text-cyan-300 border-b-2 border-cyan-400 shadow-[0_0_10px_rgba(6,182,212,0.3)]'
              : 'text-slate-400 hover:text-cyan-300'
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
          className={`flex-1 px-4 py-3 font-display text-sm uppercase tracking-wider transition-all ${
            activeTab === 'narrative'
              ? 'bg-slate-800 text-cyan-300 border-b-2 border-cyan-400 shadow-[0_0_10px_rgba(6,182,212,0.3)]'
              : hasSelection
              ? 'text-slate-400 hover:text-cyan-300'
              : 'text-slate-600 cursor-not-allowed'
          }`}
        >
          Narrative
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
        </>
      )}
    </div>
  );
}
