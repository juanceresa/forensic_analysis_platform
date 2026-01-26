'use client';

import { useState } from 'react';
import type { GraphData, BaseNode } from '@/lib/types';
import { Header } from '@/components/Header';
import { KnowledgeGraph } from '@/components/KnowledgeGraph';
import { EntitySidebar } from '@/components/EntitySidebar';
import { ErrorBoundary } from '@/components/ErrorBoundary';

type TabType = 'details' | 'narrative';

interface DashboardClientProps {
  initialData: GraphData;
  caseId: string;
}

export function DashboardClient({ initialData, caseId }: DashboardClientProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('details');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  const selectedNode = initialData.nodes.find((n) => n.id === selectedNodeId) || null;

  // DEBUG: Log node selection
  console.log('DashboardClient render:', {
    selectedNodeId,
    selectedNode: selectedNode ? selectedNode.id : 'null',
    totalNodes: initialData.nodes.length,
  });

  return (
    <ErrorBoundary>
      <div className="h-screen flex flex-col bg-slate-950">
        <Header graphData={initialData} caseId={caseId} />

        <div className="flex-1 flex overflow-hidden">
          {/* Left: Graph (flexible width) */}
          <div className="flex-1 min-w-0 relative z-0">
            <KnowledgeGraph
              data={initialData}
              selectedNodeId={selectedNodeId}
              onNodeClick={(node: BaseNode) => {
                console.log('Node clicked:', node.id, node.name || node.id);
                setSelectedNodeId(node.id);
                setActiveTab('details'); // Reset to details on new selection
              }}
            />
          </div>

          {/* Right: Tabbed Sidebar (500px fixed) */}
          <EntitySidebar
            selectedNode={selectedNode}
            graphData={initialData}
            activeTab={activeTab}
            onTabChange={setActiveTab}
            caseId={caseId}
            isCollapsed={isSidebarCollapsed}
            onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
          />
        </div>
      </div>
    </ErrorBoundary>
  );
}
