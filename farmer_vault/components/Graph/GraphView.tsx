'use client';

import { useEffect, useState } from 'react';
import { KnowledgeGraph } from './KnowledgeGraph';
import { EntitySidebar } from './EntitySidebar';
import { GraphSettingsPanel } from './GraphSettingsPanel';
import { useGraphSettings } from '@/hooks/useGraphSettings';
import type { GraphData, BaseNode } from '@/lib/types';

interface GraphViewProps {
  caseId: string;
}

const ENTITY_TYPE_COLORS: Record<string, { color: string; label: string }> = {
  PERSON: { color: '#38bdf8', label: 'Person' },
  PROPERTY: { color: '#a78bfa', label: 'Property' },
  ORGANIZATION: { color: '#fb923c', label: 'Organization' },
  LOCATION: { color: '#4ade80', label: 'Location' },
  DOCUMENT: { color: '#f472b6', label: 'Document' },
};

export function GraphView({ caseId }: GraphViewProps) {
  const { settings, updateSetting, resetSettings, isLoaded } = useGraphSettings();
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  useEffect(() => {
    async function fetchGraphData() {
      try {
        const res = await fetch(`/api/cases/${caseId}/graph`);
        if (!res.ok) throw new Error('Failed to fetch graph data');
        const data = await res.json();
        setGraphData(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load graph');
      } finally {
        setLoading(false);
      }
    }

    fetchGraphData();
  }, [caseId]);

  const handleNodeClick = (node: BaseNode) => {
    setSelectedNodeId(node.id);
  };

  const handleBackgroundClick = () => {
    setSelectedNodeId(null);
  };

  if (loading || !isLoaded) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-950">
        <div className="text-center">
          <div className="animate-spin motion-reduce:animate-none rounded-full h-12 w-12 border-b-2 border-blue-400 mx-auto mb-4" />
          <p className="text-slate-400 font-mono text-sm">Loading graph...</p>
        </div>
      </div>
    );
  }

  if (error || !graphData) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-950">
        <div className="text-center p-8 bg-slate-900 border border-red-800/50 rounded">
          <p className="text-red-400 font-mono text-sm">{error || 'Failed to load graph data'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-slate-950">
      {/* Graph Header */}
      <header className="shrink-0 px-6 py-4 border-b border-slate-800 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-mono">Knowledge Graph</h1>
          <p className="text-sm text-slate-500 mt-1">
            {graphData.nodes.length} entities &middot; {graphData.links.length} relationships
          </p>
        </div>
        <div className="text-xs text-slate-500">
          Click a node to view entity details
        </div>
      </header>

      {/* Graph + Sidebar */}
      <div className="flex-1 flex overflow-hidden">
        {/* Graph Canvas */}
        <div className="flex-1 min-w-0 relative flex flex-col">
          <div className="flex-1 relative overflow-hidden">
            <KnowledgeGraph
              data={graphData}
              selectedNodeId={selectedNodeId}
              onNodeClick={handleNodeClick}
              onBackgroundClick={handleBackgroundClick}
              settings={settings}
            />

            {/* Settings Panel (overlaid) */}
            <GraphSettingsPanel
              settings={settings}
              onUpdateSetting={updateSetting}
              onReset={resetSettings}
            />
          </div>

          {/* Legend Footer */}
          <footer className="shrink-0 px-6 py-3 border-t border-slate-800 bg-slate-900/50">
            <div className="flex items-center gap-6 justify-center">
              {Object.entries(ENTITY_TYPE_COLORS).map(([type, config]) => (
                <div key={type} className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: config.color }}
                  />
                  <span className="text-xs text-slate-400 font-mono">{config.label}</span>
                </div>
              ))}
            </div>
          </footer>
        </div>

        {/* Entity Sidebar */}
        <EntitySidebar
          selectedNodeId={selectedNodeId}
          caseId={caseId}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
        />
      </div>
    </div>
  );
}
