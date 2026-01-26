'use client';

import { useRef, useCallback, useMemo, useState, useLayoutEffect } from 'react';
import dynamic from 'next/dynamic';
import type { GraphData, BaseNode } from '@/lib/types';
import { getNodeColor, getNodeSize } from '@/lib/graph-utils';

// PERFORMANCE: Dynamic import reduces initial bundle by ~200KB
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-slate-950">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400 shadow-[0_0_20px_rgba(6,182,212,0.5)] mx-auto mb-4" />
        <p className="text-cyan-400 font-mono text-sm">Loading graph visualization...</p>
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
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useLayoutEffect(() => {
    if (!containerRef.current) {
      return;
    }

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) {
        return;
      }
      const { width, height } = entry.contentRect;
      setDimensions({
        width: Math.floor(width),
        height: Math.floor(height),
      });
    });

    observer.observe(containerRef.current);

    return () => observer.disconnect();
  }, []);

  // Calculate constellation (connected nodes) when selection changes
  const constellationNodes = useMemo(() => {
    if (!selectedNodeId) return new Set<string>();

    const constellation = new Set<string>([selectedNodeId]);
    const toProcess = [selectedNodeId];
    const processed = new Set<string>();

    // BFS to find all connected nodes
    while (toProcess.length > 0) {
      const currentId = toProcess.shift()!;
      if (processed.has(currentId)) continue;
      processed.add(currentId);

      data.links.forEach((link) => {
        if (link.source === currentId || (typeof link.source === 'object' && (link.source as any).id === currentId)) {
          const targetId = typeof link.target === 'string' ? link.target : (link.target as any).id;
          if (!constellation.has(targetId)) {
            constellation.add(targetId);
            toProcess.push(targetId);
          }
        }
        if (link.target === currentId || (typeof link.target === 'object' && (link.target as any).id === currentId)) {
          const sourceId = typeof link.source === 'string' ? link.source : (link.source as any).id;
          if (!constellation.has(sourceId)) {
            constellation.add(sourceId);
            toProcess.push(sourceId);
          }
        }
      });
    }

    return constellation;
  }, [selectedNodeId, data.links]);

  // PERFORMANCE: Memoize callback to prevent re-renders
  const handleNodeClick = useCallback(
    (node: any) => {
      onNodeClick(node as BaseNode);
    },
    [onNodeClick]
  );

  // Custom node renderer with constellation highlighting
  const nodeCanvasObject = useMemo(
    () => (node: any, ctx: CanvasRenderingContext2D) => {
      const nodeId = node.id;
      const isSelected = nodeId === selectedNodeId;
      const isInConstellation = constellationNodes.has(nodeId);

      if (isSelected || isInConstellation) {
        const time = Date.now() / 1000;
        const size = getNodeSize(node);
        const color = getNodeColor(node);

        if (isSelected) {
          // Selected node: Large pulsing cyan glow
          const pulse = Math.sin(time * 3) * 0.4 + 0.6;

          ctx.save();
          // Outer glow ring
          ctx.shadowBlur = 30 * pulse;
          ctx.shadowColor = '#06B6D4';
          ctx.beginPath();
          ctx.arc(node.x, node.y, size + 4, 0, 2 * Math.PI);
          ctx.fillStyle = `rgba(6, 182, 212, ${0.3 * pulse})`;
          ctx.fill();

          // Inner highlight
          ctx.shadowBlur = 15;
          ctx.beginPath();
          ctx.arc(node.x, node.y, size + 2, 0, 2 * Math.PI);
          ctx.fillStyle = `rgba(6, 182, 212, ${0.5 * pulse})`;
          ctx.fill();
          ctx.restore();
        } else if (isInConstellation) {
          // Constellation nodes: Subtle glow in original color
          const pulse = Math.sin(time * 2 + nodeId.length) * 0.2 + 0.8;

          ctx.save();
          ctx.shadowBlur = 15 * pulse;
          ctx.shadowColor = color;
          ctx.beginPath();
          ctx.arc(node.x, node.y, size + 1.5, 0, 2 * Math.PI);
          ctx.fillStyle = `${color}30`;
          ctx.fill();
          ctx.restore();
        }
      }
    },
    [selectedNodeId, constellationNodes]
  );

  // Custom link color - highlight constellation links
  const getLinkColor = useCallback(
    (link: any) => {
      if (!selectedNodeId) return '#475569';

      const sourceId = typeof link.source === 'string' ? link.source : link.source?.id;
      const targetId = typeof link.target === 'string' ? link.target : link.target?.id;

      if (constellationNodes.has(sourceId) && constellationNodes.has(targetId)) {
        return '#06B6D4'; // Cyan for constellation links
      }

      return '#475569'; // Default slate
    },
    [selectedNodeId, constellationNodes]
  );

  // Custom link width - make constellation links thicker
  const getLinkWidth = useCallback(
    (link: any) => {
      if (!selectedNodeId) return 1;

      const sourceId = typeof link.source === 'string' ? link.source : link.source?.id;
      const targetId = typeof link.target === 'string' ? link.target : link.target?.id;

      if (constellationNodes.has(sourceId) && constellationNodes.has(targetId)) {
        return 2; // Thicker for constellation
      }

      return 1; // Default
    },
    [selectedNodeId, constellationNodes]
  );

  return (
    <div
      ref={containerRef}
      className="w-full h-full relative overflow-hidden"
      role="application"
      aria-label="Knowledge graph visualization of entities and relationships"
    >
      <ForceGraph2D
        ref={graphRef}
        graphData={data as any}
        width={dimensions.width || undefined}
        height={dimensions.height || undefined}
        nodeColor={getNodeColor as any}
        nodeVal={getNodeSize as any}
        nodeLabel={(node: any) => `${node.name || node.id} (${node.entity_type})`}
        linkColor={getLinkColor as any}
        linkWidth={getLinkWidth as any}
        backgroundColor="#020617"
        onNodeClick={handleNodeClick as any}
        nodeCanvasObjectMode={() => 'after'}
        nodeCanvasObject={nodeCanvasObject}
        warmupTicks={0}
        cooldownTicks={Infinity}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.3}
      />
    </div>
  );
}
