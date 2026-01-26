'use client';

import { useState } from 'react';
import type { GraphData, BaseNode } from '@/lib/types';
import { Header } from '@/components/Header';
import { KnowledgeGraph } from '@/components/KnowledgeGraph';
import { EntitySidebar } from '@/components/EntitySidebar';

type TabType = 'details' | 'narrative';

interface DashboardClientProps {
  initialData: GraphData;
  caseId: string;
}

export function DashboardClient({ initialData, caseId }: DashboardClientProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('details');

  const selectedNode = initialData.nodes.find((n) => n.id === selectedNodeId) || null;

  return (
    <div className="h-screen flex flex-col bg-slate-950">
      <Header graphData={initialData} caseId={caseId} />

      <div className="flex-1 flex overflow-hidden">
        {/* Left: Graph (flexible width) */}
        <div className="flex-1">
          <KnowledgeGraph
            data={initialData}
            selectedNodeId={selectedNodeId}
            onNodeClick={(node: BaseNode) => {
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
        />
      </div>
    </div>
  );
}
