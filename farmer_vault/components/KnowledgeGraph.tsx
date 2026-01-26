'use client';

import { useRef, useCallback, useMemo } from 'react';
import dynamic from 'next/dynamic';
import type { GraphData, BaseNode } from '@/lib/types';
import { getNodeColor, getNodeSize } from '@/lib/graph-utils';

// PERFORMANCE: Dynamic import reduces initial bundle by ~200KB
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-slate-950">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500 mx-auto mb-4" />
        <p className="text-slate-400 font-mono text-sm">Loading graph visualization...</p>
      </div>
    </div>
  ),
});

interface KnowledgeGraphProps {
  data: GraphData;
  selectedNodeId: string | null;
  onNodeClick: (node: BaseNode) => void;
}

export function KnowledgeGraph({
  data,
  selectedNodeId,
  onNodeClick,
}: KnowledgeGraphProps) {
  const graphRef = useRef<any>(null);

  // PERFORMANCE: Memoize callback to prevent re-renders
  const handleNodeClick = useCallback(
    (node: any) => {
      onNodeClick(node as BaseNode);
    },
    [onNodeClick]
  );

  // PERFORMANCE: Memoize custom node renderer with pulsing animation
  const nodeCanvasObject = useMemo(
    () => (node: any, ctx: CanvasRenderingContext2D) => {
      if (node.id === selectedNodeId) {
        // Pulsing glow animation for selected node
        const time = Date.now() / 1000;
        const pulse = Math.sin(time * 2) * 0.3 + 0.7;
        const size = getNodeSize(node);
        const color = getNodeColor(node);

        ctx.save();
        ctx.shadowBlur = 20 * pulse;
        ctx.shadowColor = color;
        ctx.beginPath();
        ctx.arc(node.x, node.y, size + 2, 0, 2 * Math.PI);
        ctx.fillStyle = `${color}40`; // 25% opacity
        ctx.fill();
        ctx.restore();
      }
    },
    [selectedNodeId]
  );

  return (
    <div
      className="w-full h-full"
      role="application"
      aria-label="Knowledge graph visualization of entities and relationships"
    >
      <ForceGraph2D
        ref={graphRef}
        graphData={data as any}
        nodeColor={getNodeColor as any}
        nodeVal={getNodeSize as any}
        nodeLabel={(node: any) => `${node.name || node.id} (${node.entity_type})`}
        linkColor={() => '#475569'}
        backgroundColor="#020617"
        onNodeClick={handleNodeClick as any}
        nodeCanvasObjectMode={() => 'after'}
        nodeCanvasObject={nodeCanvasObject}
        warmupTicks={100}
        cooldownTicks={0}
      />
    </div>
  );
}
