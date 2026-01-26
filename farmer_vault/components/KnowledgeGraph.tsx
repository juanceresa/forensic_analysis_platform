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

  // Custom node renderer with 3D tactile appearance
  const nodeCanvasObject = useMemo(
    () => (node: any, ctx: CanvasRenderingContext2D) => {
      // Skip rendering if node position not yet calculated
      if (typeof node.x !== 'number' || typeof node.y !== 'number') {
        return;
      }

      const nodeId = node.id;
      const isSelected = nodeId === selectedNodeId;
      const isInConstellation = constellationNodes.has(nodeId);
      const time = Date.now() / 1000;
      const size = getNodeSize(node);
      const color = getNodeColor(node);

      ctx.save();

      // Glow effects for selected/constellation nodes
      if (isSelected) {
        const pulse = Math.sin(time * 3) * 0.4 + 0.6;
        ctx.shadowBlur = 30 * pulse;
        ctx.shadowColor = '#06B6D4';
        ctx.beginPath();
        ctx.arc(node.x, node.y, size + 4, 0, 2 * Math.PI);
        ctx.fillStyle = `rgba(6, 182, 212, ${0.3 * pulse})`;
        ctx.fill();
        ctx.shadowBlur = 15;
        ctx.beginPath();
        ctx.arc(node.x, node.y, size + 2, 0, 2 * Math.PI);
        ctx.fillStyle = `rgba(6, 182, 212, ${0.5 * pulse})`;
        ctx.fill();
      } else if (isInConstellation) {
        const pulse = Math.sin(time * 2 + nodeId.length) * 0.2 + 0.8;
        ctx.shadowBlur = 15 * pulse;
        ctx.shadowColor = color;
        ctx.beginPath();
        ctx.arc(node.x, node.y, size + 1.5, 0, 2 * Math.PI);
        ctx.fillStyle = `${color}30`;
        ctx.fill();
      }

      ctx.shadowBlur = 0;

      // Sphere with radial gradient
      const gradient = ctx.createRadialGradient(
        node.x - size * 0.3, node.y - size * 0.3, size * 0.1,
        node.x, node.y, size
      );

      const hexToRgb = (hex: string) => {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
          r: parseInt(result[1], 16),
          g: parseInt(result[2], 16),
          b: parseInt(result[3], 16)
        } : { r: 100, g: 100, b: 100 };
      };

      const rgb = hexToRgb(color);
      gradient.addColorStop(0, `rgba(${rgb.r + 40}, ${rgb.g + 40}, ${rgb.b + 40}, 1)`);
      gradient.addColorStop(0.4, `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 1)`);
      gradient.addColorStop(1, `rgba(${Math.max(0, rgb.r - 40)}, ${Math.max(0, rgb.g - 40)}, ${Math.max(0, rgb.b - 40)}, 1)`);

      ctx.beginPath();
      ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
      ctx.fillStyle = gradient;
      ctx.fill();

      // Glossy highlight
      const highlightGradient = ctx.createRadialGradient(
        node.x - size * 0.35, node.y - size * 0.35, 0,
        node.x - size * 0.35, node.y - size * 0.35, size * 0.6
      );
      highlightGradient.addColorStop(0, 'rgba(255, 255, 255, 0.5)');
      highlightGradient.addColorStop(0.5, 'rgba(255, 255, 255, 0.2)');
      highlightGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');

      ctx.beginPath();
      ctx.arc(node.x - size * 0.25, node.y - size * 0.25, size * 0.5, 0, 2 * Math.PI);
      ctx.fillStyle = highlightGradient;
      ctx.fill();

      // Subtle border
      ctx.beginPath();
      ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
      ctx.strokeStyle = `rgba(${Math.max(0, rgb.r - 60)}, ${Math.max(0, rgb.g - 60)}, ${Math.max(0, rgb.b - 60)}, 0.8)`;
      ctx.lineWidth = 1;
      ctx.stroke();

      ctx.restore();
    },
    [selectedNodeId, constellationNodes]
  );

  // Custom link color - highlight constellation links
  const getLinkColor = useCallback(
    (link: any) => {
      if (!selectedNodeId) return '#1a1a1a';

      const sourceId = typeof link.source === 'string' ? link.source : link.source?.id;
      const targetId = typeof link.target === 'string' ? link.target : link.target?.id;

      if (constellationNodes.has(sourceId) && constellationNodes.has(targetId)) {
        return '#06B6D4'; // Cyan for constellation links
      }

      return '#1a1a1a'; // Very dark gray for non-constellation
    },
    [selectedNodeId, constellationNodes]
  );

  // Custom link width - make constellation links thicker
  const getLinkWidth = useCallback(
    (link: any) => {
      if (!selectedNodeId) return 0.5;

      const sourceId = typeof link.source === 'string' ? link.source : link.source?.id;
      const targetId = typeof link.target === 'string' ? link.target : link.target?.id;

      if (constellationNodes.has(sourceId) && constellationNodes.has(targetId)) {
        return 2; // Thicker for constellation
      }

      return 0.5; // Thin default
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
        backgroundColor="#000000"
        onNodeClick={handleNodeClick as any}
        nodeCanvasObjectMode={() => 'replace'}
        nodeCanvasObject={nodeCanvasObject}
        warmupTicks={0}
        cooldownTicks={Infinity}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.3}
      />
    </div>
  );
}
