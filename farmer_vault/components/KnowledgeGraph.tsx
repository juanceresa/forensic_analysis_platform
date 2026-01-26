'use client';

import { useRef, useCallback, useMemo, useState, useLayoutEffect, useEffect } from 'react';
import dynamic from 'next/dynamic';
import type { GraphData, BaseNode } from '@/lib/types';
import { getNodeColor, getNodeSize } from '@/lib/graph-utils';
import type { GraphSettings } from '@/lib/graph-settings';
import { DEFAULT_SETTINGS } from '@/lib/graph-settings';
import { forceManyBody, forceX, forceY } from 'd3-force';

// PERFORMANCE: Dynamic import reduces initial bundle by ~200KB
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-slate-950">
      <div className="text-center">
        <div className="animate-spin motion-reduce:animate-none rounded-full h-12 w-12 border-b-2 border-cyan-400 shadow-[0_0_20px_rgba(6,182,212,0.5)] mx-auto mb-4" />
        <p className="text-cyan-400 font-mono text-sm">Loading graph visualization…</p>
      </div>
    </div>
  ),
});

interface KnowledgeGraphProps {
  data: GraphData;
  selectedNodeId: string | null;
  onNodeClick: (node: BaseNode) => void;
  onBackgroundClick?: () => void;
  settings?: GraphSettings;
}

export function KnowledgeGraph({
  data,
  selectedNodeId,
  onNodeClick,
  onBackgroundClick,
  settings: userSettings,
}: KnowledgeGraphProps) {
  const defaultGraphTheme = useMemo(
    () => ({
      background: '#0b0e12',
      line: '#2b323a',
      lineHighlight: 'rgba(110, 219, 227, 0.4)',
      nodeFocus: '#6edbe3',
      text: '#d6dee6',
    }),
    []
  );
  const graphRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [hoverAlpha, setHoverAlpha] = useState(0);
  const [selectedAlpha, setSelectedAlpha] = useState(0);
  const selectedAnimRef = useRef<number | null>(null);
  const hoverAnimRef = useRef<number | null>(null);
  const hoverAlphaRef = useRef(0);
  const selectedAlphaRef = useRef(0);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  const [graphTheme, setGraphTheme] = useState(defaultGraphTheme);

  // Merge user settings with defaults
  const settings = useMemo(
    () => ({ ...DEFAULT_SETTINGS, ...userSettings }),
    [userSettings]
  );

  // Calculate node degrees (number of connections) for sizing
  const nodeDegrees = useMemo(() => {
    const degrees = new Map<string, number>();
    data.nodes.forEach(node => degrees.set(node.id, 0));
    data.links.forEach(link => {
      const sourceId = typeof link.source === 'string' ? link.source : (link.source as any).id;
      const targetId = typeof link.target === 'string' ? link.target : (link.target as any).id;
      degrees.set(sourceId, (degrees.get(sourceId) || 0) + 1);
      degrees.set(targetId, (degrees.get(targetId) || 0) + 1);
    });
    return degrees;
  }, [data.nodes, data.links]);

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

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const updatePreference = () => setPrefersReducedMotion(mediaQuery.matches);
    updatePreference();
    mediaQuery.addEventListener('change', updatePreference);
    return () => mediaQuery.removeEventListener('change', updatePreference);
  }, []);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    const styles = getComputedStyle(containerRef.current);
    const readVar = (name: string, fallback: string) =>
      styles.getPropertyValue(name).trim() || fallback;

    setGraphTheme({
      background: readVar('--graph-background', defaultGraphTheme.background),
      line: readVar('--graph-line', defaultGraphTheme.line),
      lineHighlight: readVar('--graph-line-highlight', defaultGraphTheme.lineHighlight),
      nodeFocus: readVar('--graph-node-focused', defaultGraphTheme.nodeFocus),
      text: readVar('--graph-text', defaultGraphTheme.text),
    });
  }, [defaultGraphTheme]);

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

  const hoveredNodeSet = useMemo(() => {
    if (!hoveredNodeId) {
      return null;
    }

    const connected = new Set<string>([hoveredNodeId]);
    data.links.forEach((link) => {
      const sourceId = typeof link.source === 'string' ? link.source : link.source?.id;
      const targetId = typeof link.target === 'string' ? link.target : link.target?.id;
      if (sourceId === hoveredNodeId && targetId) {
        connected.add(targetId);
      }
      if (targetId === hoveredNodeId && sourceId) {
        connected.add(sourceId);
      }
    });

    return connected;
  }, [hoveredNodeId, data.links]);

  const selectedNodeSet = useMemo(() => {
    if (!selectedNodeId) {
      return null;
    }

    const connected = new Set<string>([selectedNodeId]);
    data.links.forEach((link) => {
      const sourceId = typeof link.source === 'string' ? link.source : link.source?.id;
      const targetId = typeof link.target === 'string' ? link.target : link.target?.id;
      if (sourceId === selectedNodeId && targetId) {
        connected.add(targetId);
      }
      if (targetId === selectedNodeId && sourceId) {
        connected.add(sourceId);
      }
    });

    return connected;
  }, [selectedNodeId, data.links]);

  const activeNodeSet = selectedNodeSet ?? hoveredNodeSet;
  const activeAlpha = selectedNodeId ? selectedAlpha : hoverAlpha;
  const hasActiveHighlight = Boolean(activeNodeSet);
  const baseHighlightAlpha = 0.28;

  // PERFORMANCE: Memoize callback to prevent re-renders
  const handleNodeClick = useCallback(
    (node: any) => {
      onNodeClick(node as BaseNode);
    },
    [onNodeClick]
  );

  const applyForces = useCallback(() => {
    if (!graphRef.current) {
      return;
    }
    if (dimensions.width === 0 || dimensions.height === 0) {
      return;
    }

    const maxDistance = Math.max(dimensions.width, dimensions.height, 600);

    graphRef.current.d3Force(
      'charge',
      forceManyBody()
        .strength(-settings.repelForce)
        .distanceMax(maxDistance)
    );

    graphRef.current.d3Force('link')?.distance(settings.linkForce).strength(0.7);

    graphRef.current.d3Force('x', forceX(0).strength(settings.centerForce));
    graphRef.current.d3Force('y', forceY(0).strength(settings.centerForce));

    graphRef.current.d3ReheatSimulation();
  }, [settings.repelForce, settings.linkForce, settings.centerForce, dimensions.width, dimensions.height]);

  useEffect(() => {
    let rafId: number | null = null;

    const tryApply = () => {
      if (graphRef.current && dimensions.width > 0 && dimensions.height > 0) {
        applyForces();
        return;
      }
      rafId = requestAnimationFrame(tryApply);
    };

    tryApply();

    return () => {
      if (rafId !== null) {
        cancelAnimationFrame(rafId);
      }
    };
  }, [applyForces, dimensions.width, dimensions.height]);

  const previousSettingsRef = useRef(settings);
  useEffect(() => {
    const previous = previousSettingsRef.current;
    previousSettingsRef.current = settings;

    const resetToDefaults =
      previous !== settings &&
      settings.centerForce === DEFAULT_SETTINGS.centerForce &&
      settings.repelForce === DEFAULT_SETTINGS.repelForce &&
      settings.linkForce === DEFAULT_SETTINGS.linkForce &&
      settings.nodeSizeBase === DEFAULT_SETTINGS.nodeSizeBase &&
      settings.nodeSizeMultiplier === DEFAULT_SETTINGS.nodeSizeMultiplier &&
      settings.linkWidth === DEFAULT_SETTINGS.linkWidth &&
      settings.constellationLinkWidth === DEFAULT_SETTINGS.constellationLinkWidth;

    if (resetToDefaults && graphRef.current) {
      graphRef.current.zoomToFit(400, 60);
    }
  }, [settings]);

  useEffect(() => {
    const targetAlpha = hoveredNodeId ? 1 : 0;

    if (prefersReducedMotion) {
      hoverAlphaRef.current = targetAlpha;
      setHoverAlpha(targetAlpha);
      return;
    }

    const durationMs = 180;
    const start = performance.now();
    const startAlpha = hoverAlphaRef.current;

    if (hoverAnimRef.current) {
      cancelAnimationFrame(hoverAnimRef.current);
    }

    const tick = (now: number) => {
      const elapsed = Math.min(1, (now - start) / durationMs);
      const nextAlpha = startAlpha + (targetAlpha - startAlpha) * elapsed;
      hoverAlphaRef.current = nextAlpha;
      setHoverAlpha(nextAlpha);
      if (elapsed < 1) {
        hoverAnimRef.current = requestAnimationFrame(tick);
      }
    };

    hoverAnimRef.current = requestAnimationFrame(tick);

    return () => {
      if (hoverAnimRef.current) {
        cancelAnimationFrame(hoverAnimRef.current);
      }
    };
  }, [hoveredNodeId, prefersReducedMotion]);

  useEffect(() => {
    const targetAlpha = selectedNodeId ? 1 : 0;

    if (prefersReducedMotion) {
      selectedAlphaRef.current = targetAlpha;
      setSelectedAlpha(targetAlpha);
      return;
    }

    const durationMs = 220;
    const start = performance.now();
    let startAlpha = selectedAlphaRef.current;
    if (selectedNodeId && hoveredNodeId === selectedNodeId) {
      startAlpha = Math.max(startAlpha, hoverAlphaRef.current);
    }

    if (selectedAnimRef.current) {
      cancelAnimationFrame(selectedAnimRef.current);
    }

    const tick = (now: number) => {
      const elapsed = Math.min(1, (now - start) / durationMs);
      const nextAlpha = startAlpha + (targetAlpha - startAlpha) * elapsed;
      selectedAlphaRef.current = nextAlpha;
      setSelectedAlpha(nextAlpha);
      if (elapsed < 1) {
        selectedAnimRef.current = requestAnimationFrame(tick);
      }
    };

    selectedAnimRef.current = requestAnimationFrame(tick);

    return () => {
      if (selectedAnimRef.current) {
        cancelAnimationFrame(selectedAnimRef.current);
      }
    };
  }, [selectedNodeId, hoveredNodeId, prefersReducedMotion]);

  // Custom node renderer - simple flat circles with size based on connections
  const nodeCanvasObject = useMemo(
    () => (node: any, ctx: CanvasRenderingContext2D, globalScale?: number) => {
      // Skip rendering if node position not yet calculated
      if (typeof node.x !== 'number' || typeof node.y !== 'number') {
        return;
      }

      const nodeId = node.id;
      const isHovered = nodeId === hoveredNodeId;
      const isSelected = nodeId === selectedNodeId;
      const isDimmed = activeNodeSet ? !activeNodeSet.has(nodeId) : false;
      const color = getNodeColor(node, settings.entityColors);

      // Calculate size based on number of connections (hub nodes are larger)
      const degree = nodeDegrees.get(nodeId) || 0;
      // Obsidian-style sizing: all nodes clearly visible at any zoom level
      const size = settings.nodeSizeBase + Math.pow(degree, 0.5) * settings.nodeSizeMultiplier;

      ctx.save();

      ctx.shadowBlur = 0;

      // Simple flat circle
      ctx.beginPath();
      ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
      if (isDimmed) {
        const dimAlpha = hasActiveHighlight ? 1 - 0.2 * activeAlpha : 1;
        ctx.fillStyle = `rgba(${hexToRgb(color)}, ${dimAlpha})`;
      } else {
        ctx.fillStyle = color;
      }
      ctx.fill();

      const ringAlpha = isHovered ? hoverAlpha : isSelected ? selectedAlpha : 0;
      if (ringAlpha > 0) {
        const borderAlpha = Math.max(ringAlpha, 0.55);
        ctx.shadowBlur = 14 * ringAlpha;
        ctx.shadowColor = withAlpha(graphTheme.nodeFocus, 0.45 * ringAlpha);

        // Cyan hover ring outside the node
        ctx.beginPath();
        ctx.arc(node.x, node.y, size + 3, 0, 2 * Math.PI);
        ctx.strokeStyle = withAlpha(graphTheme.nodeFocus, ringAlpha);
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // White border on the node itself
        ctx.beginPath();
        ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
        ctx.strokeStyle = `rgba(255, 255, 255, ${borderAlpha})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      if (typeof globalScale === 'number' && globalScale > 1.05) {
        const labelAlpha = Math.min(1, (globalScale - 1.05) / 0.9);
        const fontSize = Math.max(8, Math.min(13, 12 / globalScale));
        ctx.font = `${fontSize}px "Space Grotesk", "Helvetica Neue", Arial, sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillStyle = withAlpha(graphTheme.text, 0.65 * labelAlpha);
        ctx.fillText(node.name || node.id, node.x, node.y + size + 4);
      }

      ctx.restore();
    },
    [
      hoveredNodeId,
      hoveredNodeSet,
      selectedNodeId,
      selectedNodeSet,
      hasActiveHighlight,
      activeAlpha,
      nodeDegrees,
      settings.nodeSizeBase,
      settings.nodeSizeMultiplier,
      settings.entityColors,
      graphTheme.nodeFocus,
      graphTheme.text
    ]
  );

  // Custom link color - highlight constellation links
  const getLinkColor = useCallback(
    (link: any) => {
      const sourceId = typeof link.source === 'string' ? link.source : link.source?.id;
      const targetId = typeof link.target === 'string' ? link.target : link.target?.id;

      if (selectedNodeId && (sourceId === selectedNodeId || targetId === selectedNodeId)) {
        return withAlpha(graphTheme.lineHighlight, baseHighlightAlpha * selectedAlpha);
      }

      const isHoveredLink = hoveredNodeId && (sourceId === hoveredNodeId || targetId === hoveredNodeId);

      if (isHoveredLink) {
        return withAlpha(graphTheme.lineHighlight, baseHighlightAlpha * hoverAlpha);
      }

      return graphTheme.line;
    },
    [
      hoveredNodeId,
      hoverAlpha,
      selectedNodeId,
      selectedAlpha,
      graphTheme.lineHighlight,
      graphTheme.line,
      baseHighlightAlpha
    ]
  );

  // Custom link width - make constellation links thicker
  const getLinkWidth = useCallback(
    (link: any) => {
      const sourceId = typeof link.source === 'string' ? link.source : link.source?.id;
      const targetId = typeof link.target === 'string' ? link.target : link.target?.id;

      if (selectedNodeId && (sourceId === selectedNodeId || targetId === selectedNodeId)) {
        return settings.linkWidth + settings.constellationLinkWidth * selectedAlpha;
      }

      if (hoveredNodeId && hoverAlpha > 0 && (sourceId === hoveredNodeId || targetId === hoveredNodeId)) {
        return settings.linkWidth + settings.constellationLinkWidth * hoverAlpha;
      }

      return settings.linkWidth; // Thin but visible
    },
    [
      hoveredNodeId,
      hoverAlpha,
      selectedNodeId,
      selectedAlpha,
      settings.linkWidth,
      settings.constellationLinkWidth
    ]
  );

  return (
    <div
      ref={containerRef}
      className="graph-view w-full h-full relative overflow-hidden"
      role="application"
      aria-label="Knowledge graph visualization of entities and relationships"
      style={{ zIndex: 0 }}
    >
      <ForceGraph2D
        ref={graphRef}
        graphData={data as any}
        width={dimensions.width || undefined}
        height={dimensions.height || undefined}
        nodeColor={((node: any) => getNodeColor(node, settings.entityColors)) as any}
        nodeLabel={(node: any) => `${node.name || node.id} (${node.entity_type})`}
        linkColor={getLinkColor as any}
        linkWidth={getLinkWidth as any}
        backgroundColor="rgba(0,0,0,0)"
        onNodeClick={handleNodeClick as any}
        onBackgroundClick={onBackgroundClick}
        onNodeHover={(node: any) => setHoveredNodeId(node ? node.id : null)}
        nodeCanvasObjectMode={() => 'replace'}
        nodeCanvasObject={nodeCanvasObject}
        warmupTicks={30}
        cooldownTicks={300}
        d3AlphaDecay={0.03}
        d3VelocityDecay={0.4}
      />
    </div>
  );
}

function hexToRgb(hex: string): string {
  const normalized = hex.replace('#', '');
  const value = normalized.length === 3
    ? normalized.split('').map((c) => c + c).join('')
    : normalized;
  const intValue = parseInt(value, 16);
  const r = (intValue >> 16) & 255;
  const g = (intValue >> 8) & 255;
  const b = intValue & 255;
  return `${r}, ${g}, ${b}`;
}

function withAlpha(color: string, alpha: number): string {
  const trimmed = color.trim();
  const rgbaMatch = trimmed.match(/^rgba\(([^,]+),([^,]+),([^,]+),([^)]+)\)$/);
  if (rgbaMatch) {
    return `rgba(${rgbaMatch[1].trim()}, ${rgbaMatch[2].trim()}, ${rgbaMatch[3].trim()}, ${alpha})`;
  }
  const rgbMatch = trimmed.match(/^rgb\(([^,]+),([^,]+),([^)]+)\)$/);
  if (rgbMatch) {
    return `rgba(${rgbMatch[1].trim()}, ${rgbMatch[2].trim()}, ${rgbMatch[3].trim()}, ${alpha})`;
  }
  if (trimmed.startsWith('#')) {
    return `rgba(${hexToRgb(trimmed)}, ${alpha})`;
  }
  return trimmed;
}
