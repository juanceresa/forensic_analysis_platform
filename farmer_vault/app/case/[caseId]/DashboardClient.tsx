'use client';

import { useState } from 'react';
import type { GraphData, BaseNode } from '@/lib/types';
import { Header } from '@/components/Dashboard/Header';
import { KnowledgeGraph } from '@/components/Graph/KnowledgeGraph';
import { EntitySidebar } from '@/components/Graph/EntitySidebar';
import { ErrorBoundary } from '@/components/shared/ErrorBoundary';
import { useGraphSettings } from '@/hooks/useGraphSettings';

interface DashboardClientProps {
  initialData: GraphData;
  caseId: string;
}

export function DashboardClient({ initialData, caseId }: DashboardClientProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const { settings } = useGraphSettings();

  return (
    <ErrorBoundary>
      <div className="h-screen flex flex-col bg-slate-950">
        <Header graphData={initialData} caseId={caseId} />

        <div className="flex-1 flex overflow-hidden">
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
          </div>

          <EntitySidebar
            selectedNodeId={selectedNodeId}
            caseId={caseId}
          />
        </div>
      </div>
    </ErrorBoundary>
  );
}
