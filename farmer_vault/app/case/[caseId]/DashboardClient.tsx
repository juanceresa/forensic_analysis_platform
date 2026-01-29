'use client';

import { useState } from 'react';
import type { GraphData, BaseNode } from '@/lib/types';
import { Header } from '@/components/Dashboard/Header';
import { KnowledgeGraph } from '@/components/Graph/KnowledgeGraph';
import { EntitySidebar } from '@/components/Graph/EntitySidebar';
import { ErrorBoundary } from '@/components/shared/ErrorBoundary';
import { GraphSettingsPanel } from '@/components/Graph/GraphSettingsPanel';
import { useGraphSettings } from '@/hooks/useGraphSettings';

interface DashboardClientProps {
  initialData: GraphData;
  caseId: string;
}

export function DashboardClient({ initialData, caseId }: DashboardClientProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const { settings, updateSetting, resetSettings } = useGraphSettings();

  return (
    <ErrorBoundary>
      <div className="h-screen flex flex-col bg-slate-950">
        <Header graphData={initialData} caseId={caseId} />

        <div className="flex-1 flex overflow-hidden">
          {/* Left: Graph (flexible width) */}
          <div className="flex-1 min-w-0 relative">
            <KnowledgeGraph
              data={initialData}
              selectedNodeId={selectedNodeId}
              onNodeClick={(node: BaseNode) => {
                setSelectedNodeId(node.id);
              }}
              onBackgroundClick={() => {
                setSelectedNodeId(null);
              }}
              settings={settings}
            />
            <GraphSettingsPanel
              settings={settings}
              onUpdateSetting={updateSetting}
              onReset={resetSettings}
            />
          </div>

          {/* Right: Entity Sidebar (500px fixed) */}
          <EntitySidebar
            selectedNodeId={selectedNodeId}
            caseId={caseId}
            isCollapsed={isSidebarCollapsed}
            onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
          />
        </div>
      </div>
    </ErrorBoundary>
  );
}
