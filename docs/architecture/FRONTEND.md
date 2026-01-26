# Farmer House Forensic Intelligence Platform — Frontend Specification (The Vault)

> **Document Classification:** Internal Engineering Reference
> **Version:** 1.1.0
> **Last Updated:** 2025-01-21
> **Status:** MVP1 Implementation Guide (with performance optimizations)

---

## Overview

Zone B (The Vault) is the client-facing read-only interface for viewing forensic dossiers. It renders the `graph_data.json` output from Zone A (The Factory) as an interactive knowledge graph with document viewer.

**Core Principles:**
- **Read-Only**: No uploads, edits, or deletions
- **Static**: Data is pre-generated; no backend processing
- **Obsidian-Style**: Force-directed graph with node detail panel
- **Palantir Aesthetic**: Dark mode, monospace, high-stakes professional
- **Performance-First**: Optimized for graphs with 1,000+ nodes

**Graph Data Contract (Aligned to `graph_data.json`):**
- **Nodes** use `entity_type` and `name` (not `type`/`label`).
- **Links** use `relation_type` (not `label`) and are the primary driver for view filters.
- **Provenance** lives on `extracted_from` (comma-delimited string of document IDs; split + trim).
- **Verification tiers** are `TIER_1_CERTIFIED`, `TIER_2_INSTITUTIONAL`, `TIER_2_ANALYST`, `TIER_3_AI`.

---

## Graph Performance Strategy

### Expected Scale
Based on 300 documents × ~5 entities/doc:
- **Nodes**: ~1,500 entities
- **Edges**: ~3,000-4,500 relations
- **Challenge**: Force-directed graphs degrade significantly above ~500 nodes

### Three-Tier Rendering Strategy

**Tier 1: Filtered View (Default)**
- Show only high-importance nodes initially
- Importance = betweenness centrality + connection count
- Render ~200-300 "core" nodes
- User can expand to see full graph

**Tier 2: Clustered View**
- Group entities by property or family
- Each cluster shown as single meta-node
- Click to expand cluster
- Reduces visual complexity

**Tier 3: Focus Mode**
- Show selected node + N-hop neighbors only
- N=2 by default (direct and secondary connections)
- Dramatically improves performance
- Maintains context without overwhelming

### Implementation Plan

```typescript
// lib/graph-optimizer.ts

interface GraphOptimization {
  mode: 'filtered' | 'clustered' | 'focus';
  nodeLimit: number;
  clusteringKey?: 'property' | 'person' | 'entity_type';
  focusNodeId?: string;
  hopDistance?: number;
}

export function optimizeGraph(
  fullGraph: GraphData,
  options: GraphOptimization
): GraphData {
  switch (options.mode) {
    case 'filtered':
      return filterByImportance(fullGraph, options.nodeLimit);

    case 'clustered':
      return clusterByKey(fullGraph, options.clusteringKey);

    case 'focus':
      return extractNHopNeighborhood(
        fullGraph,
        options.focusNodeId,
        options.hopDistance || 2
      );

    default:
      return fullGraph;
  }
}

function filterByImportance(graph: GraphData, limit: number): GraphData {
  // Calculate node importance scores
  const scores = graph.nodes.map(node => ({
    node,
    score: calculateImportance(node, graph.links)
  }));

  // Sort by importance and take top N
  const topNodes = scores
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map(s => s.node);

  const topNodeIds = new Set(topNodes.map(n => n.id));

  // Filter links to only include those between top nodes
  const filteredLinks = graph.links.filter(
    link => topNodeIds.has(link.source) && topNodeIds.has(link.target)
  );

  return {
    ...graph,
    nodes: topNodes,
    links: filteredLinks
  };
}

function calculateImportance(node: Node, links: Link[]): number {
  // Factors:
  // 1. Connection count (degree centrality)
  const degree = links.filter(
    l => l.source === node.id || l.target === node.id
  ).length;

  // 2. Entity type priority
  const typePriority = {
    'PERSON': 1.5,
    'PROPERTY': 2.0,      // Properties are most important
    'ORGANIZATION': 1.2,
    'DOCUMENT': 0.5,      // Documents are numerous, lower priority
    'LOCATION': 0.8
  };

  // 3. Verification tier bonus
  const tierBonus = {
    'TIER_1_CERTIFIED': 2.0,
    'TIER_2_INSTITUTIONAL': 1.7,
    'TIER_2_ANALYST': 1.5,
    'TIER_3_AI': 1.0
  };

  return (
    degree *
    (typePriority[node.entity_type] || 1.0) *
    (tierBonus[node.verification.tier] || 1.0)
  );
}

function extractNHopNeighborhood(
  graph: GraphData,
  startNodeId: string,
  hops: number
): GraphData {
  const visited = new Set<string>([startNodeId]);
  let frontier = new Set<string>([startNodeId]);

  // BFS to find all nodes within N hops
  for (let i = 0; i < hops; i++) {
    const nextFrontier = new Set<string>();

    for (const nodeId of frontier) {
      const neighbors = graph.links
        .filter(l => l.source === nodeId || l.target === nodeId)
        .map(l => l.source === nodeId ? l.target : l.source);

      neighbors.forEach(n => {
        if (!visited.has(n)) {
          nextFrontier.add(n);
          visited.add(n);
        }
      });
    }

    frontier = nextFrontier;
  }

  // Filter to neighborhood
  const neighborhoodNodes = graph.nodes.filter(n => visited.has(n.id));
  const neighborhoodLinks = graph.links.filter(
    l => visited.has(l.source) && visited.has(l.target)
  );

  return {
    ...graph,
    nodes: neighborhoodNodes,
    links: neighborhoodLinks
  };
}
```

### UI Controls: Tabbed Filter Views (Default)

**Primary Interface:** Horizontal tabs above graph for quick view switching

```typescript
// components/GraphFilterTabs.tsx

type FilterView =
  | 'overview'      // Core entities (properties + key people)
  | 'families'      // Group by family clusters
  | 'properties'    // Property-centric view
  | 'timeline'      // Temporal view (chronological)
  | 'legal'         // Legal acts & government actions
  | 'full';         // Complete unfiltered graph

interface GraphFilterTabsProps {
  currentView: FilterView;
  onViewChange: (view: FilterView) => void;
  data: GraphData;
}

export function GraphFilterTabs({ currentView, onViewChange, data }: GraphFilterTabsProps) {
  const viewStats = calculateViewStats(data);

  return (
    <div className="border-b border-slate-800 bg-slate-900/50">
      <div className="flex items-center gap-1 px-4 overflow-x-auto">
        <Tab
          active={currentView === 'overview'}
          onClick={() => onViewChange('overview')}
          icon="🏠"
          label="Overview"
          count={viewStats.overview}
          description="Key entities and relationships"
        />
        <Tab
          active={currentView === 'families'}
          onClick={() => onViewChange('families')}
          icon="👥"
          label="Families"
          count={viewStats.families}
          description="Group by family lineage"
        />
        <Tab
          active={currentView === 'properties'}
          onClick={() => onViewChange('properties')}
          icon="🏛️"
          label="Properties"
          count={viewStats.properties}
          description="Property-centric view"
        />
        <Tab
          active={currentView === 'timeline'}
          onClick={() => onViewChange('timeline')}
          icon="📅"
          label="Timeline"
          count={viewStats.events}
          description="Chronological events"
        />
        <Tab
          active={currentView === 'legal'}
          onClick={() => onViewChange('legal')}
          icon="⚖️"
          label="Legal"
          count={viewStats.legalActs}
          description="Legal actions & decrees"
        />
        <Tab
          active={currentView === 'full'}
          onClick={() => onViewChange('full')}
          icon="🔍"
          label="Full Graph"
          count={data.nodes.length}
          description="Complete unfiltered view"
        />
      </div>
    </div>
  );
}

function Tab({
  active,
  onClick,
  icon,
  label,
  count,
  description
}: {
  active: boolean;
  onClick: () => void;
  icon: string;
  label: string;
  count: number;
  description: string;
}) {
  return (
    <button
      onClick={onClick}
      title={description}
      className={`
        px-4 py-3 border-b-2 transition-colors whitespace-nowrap
        ${active
          ? 'border-blue-500 text-blue-400 bg-slate-800/50'
          : 'border-transparent text-slate-400 hover:text-slate-300 hover:border-slate-700'
        }
      `}
    >
      <div className="flex items-center gap-2">
        <span className="text-lg">{icon}</span>
        <span className="text-sm font-medium">{label}</span>
        <span className="text-xs font-mono bg-slate-800 px-1.5 py-0.5 rounded">
          {count}
        </span>
      </div>
    </button>
  );
}
```

### Filter View Logic

```typescript
// lib/graph-filters.ts

export function applyFilterView(data: GraphData, view: FilterView): GraphData {
  const temporalRelationTypes = new Set([
    'SOLD',
    'BOUGHT',
    'INHERITED',
    'CONFISCATED',
    'WITNESSED',
    'NOTARIZED'
  ]);

  switch (view) {
    case 'overview':
      return {
        ...data,
        nodes: data.nodes.filter(n =>
          n.entity_type === 'PROPERTY' ||
          (n.entity_type === 'PERSON' && calculateImportance(n, data.links) > 5)
        ),
        links: data.links.filter(l =>
          ['OWNS', 'CONFISCATED', 'INHERITED', 'SOLD', 'BOUGHT'].includes(l.relation_type)
        )
      };

    case 'families':
      return clusterByFamily(data);

    case 'properties':
      return {
        ...data,
        nodes: data.nodes.filter(n =>
          n.entity_type === 'PROPERTY' ||
          (n.entity_type === 'PERSON' && isConnectedToProperty(n, data.links)) ||
          n.entity_type === 'DOCUMENT'
        )
      };

    case 'timeline':
      // Show entities that have temporal data
      return {
        ...data,
        nodes: data.nodes.filter(n => hasTemporalData(n)),
        links: data.links.filter(l => l.date && temporalRelationTypes.has(l.relation_type))
      };

    case 'legal':
      return {
        ...data,
        nodes: data.nodes.filter(n =>
          n.entity_type === 'ORGANIZATION' ||
          n.entity_type === 'DOCUMENT'
        ),
        links: data.links.filter(l =>
          ['CONFISCATED', 'REGISTERED_IN', 'NOTARIZED', 'ISSUED_BY'].includes(l.relation_type)
        )
      };

    case 'full':
    default:
      return data;
  }
}

function clusterByFamily(data: GraphData): GraphData {
  // Group PERSON nodes by family name
  const families = new Map<string, Node[]>();

  data.nodes.filter(n => n.entity_type === 'PERSON').forEach(person => {
    const familyName = extractFamilyName(person.name);
    if (!families.has(familyName)) {
      families.set(familyName, []);
    }
    families.get(familyName)!.push(person);
  });

  // Create cluster nodes for each family
  const clusterNodes: Node[] = [];
  const clusterMap = new Map<string, string>();

  families.forEach((members, familyName) => {
    if (members.length > 1) {
      // Create cluster node
      const clusterId = `FAMILY-${familyName}`;
      clusterNodes.push({
        id: clusterId,
        name: `${familyName} Family`,
        entity_type: 'PERSON',
        verification: {
          tier: 'TIER_3_AI',
          confidence: 0.9
        },
        member_count: members.length,
        extracted_from: ''
      });

      // Map members to cluster
      members.forEach(m => clusterMap.set(m.id, clusterId));
    }
  });

  // Replace person nodes with clusters, keep other entities
  const filteredNodes = [
    ...clusterNodes,
    ...data.nodes.filter(n => n.entity_type !== 'PERSON' || !clusterMap.has(n.id))
  ];

  // Remap links to clusters
  const remappedLinks = data.links.map(link => ({
    ...link,
    source: clusterMap.get(link.source) || link.source,
    target: clusterMap.get(link.target) || link.target
  }));

  return {
    ...data,
    nodes: filteredNodes,
    links: remappedLinks
  };
}

function extractFamilyName(fullName: string): string {
  // Simple extraction: last word is family name
  // "Mario Ceresa" → "Ceresa"
  // "Don Mario Ceresa" → "Ceresa"
  const parts = fullName.split(' ');
  return parts[parts.length - 1];
}
```

### Secondary Controls (Gear Menu)

For advanced options, add a gear menu in the corner:

```typescript
// components/GraphAdvancedControls.tsx

export function GraphAdvancedControls() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="absolute top-4 right-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 bg-slate-800 border border-slate-700 rounded hover:bg-slate-700"
        title="Advanced controls"
      >
        ⚙️
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-slate-800 border border-slate-700 rounded shadow-lg p-3 space-y-3">
          <div>
            <label className="text-xs text-slate-400">Verification Tier</label>
            <select className="w-full mt-1 bg-slate-700 text-slate-200 text-sm rounded px-2 py-1">
              <option value="all">All Tiers</option>
              <option value="TIER_1_CERTIFIED">Certified Only</option>
              <option value="TIER_2_INSTITUTIONAL">Institutional + Certified</option>
              <option value="TIER_2_ANALYST">Analyst + Certified</option>
            </select>
          </div>

          <div>
            <label className="text-xs text-slate-400">Node Limit</label>
            <input
              type="range"
              min="50"
              max="1000"
              step="50"
              defaultValue="300"
              className="w-full"
            />
            <div className="text-xs text-slate-500 text-center">300 nodes</div>
          </div>

          <div>
            <label className="text-xs text-slate-400">Physics Strength</label>
            <input
              type="range"
              min="0"
              max="100"
              defaultValue="50"
              className="w-full"
            />
          </div>
        </div>
      )}
    </div>
  );
}
```

### Performance Benchmarks

Target performance on M1 Mac:

| Graph Size | Mode | Render Time | FPS | Acceptable? |
|------------|------|-------------|-----|-------------|
| 100 nodes | Full | <100ms | 60 | ✓ Excellent |
| 300 nodes | Filtered | <200ms | 50-60 | ✓ Good |
| 500 nodes | Filtered | <500ms | 40-50 | ✓ Acceptable |
| 1,000 nodes | Focus | <300ms | 50-60 | ✓ Good |
| 1,500 nodes | Full | 2-5s | 20-30 | ✗ Poor (use filtered) |

**Optimization Triggers:**
- If graph >500 nodes, default to filtered mode
- If graph >1,000 nodes, disable full mode
- If FPS drops below 30, suggest focus mode

---

## Design System

### Color Palette

```css
/* Vault Theme Colors */
:root {
  /* Background */
  --vault-bg-primary: #0F172A;     /* Slate-900 */
  --vault-bg-secondary: #1E293B;   /* Slate-800 */
  --vault-bg-tertiary: #334155;    /* Slate-700 */
  
  /* Text */
  --vault-text-primary: #F8FAFC;   /* Slate-50 */
  --vault-text-secondary: #94A3B8; /* Slate-400 */
  --vault-text-muted: #64748B;     /* Slate-500 */
  
  /* Borders */
  --vault-border: #475569;         /* Slate-600 */
  --vault-border-strong: #64748B;  /* Slate-500 */
  
  /* Verification Tiers */
  --tier-3-ai: #6B7280;            /* Grey-500 */
  --tier-3-ai-glow: rgba(107, 114, 128, 0.3);
  --tier-2-verified: #F59E0B;      /* Amber-500 */
  --tier-2-verified-glow: rgba(245, 158, 11, 0.3);
  --tier-1-certified: #3B82F6;     /* Blue-500 */
  --tier-1-certified-glow: rgba(59, 130, 246, 0.3);
  
  /* Entity Types */
  --entity-person: #6366F1;        /* Indigo-500 */
  --entity-property: #10B981;      /* Emerald-500 */
  --entity-document: #F59E0B;      /* Amber-500 */
  --entity-organization: #8B5CF6;  /* Violet-500 */
  --entity-legal-act: #EF4444;     /* Red-500 */
  --entity-location: #84CC16;      /* Lime-500 */
  
  /* Accents */
  --vault-accent: #3B82F6;         /* Blue-500 */
  --vault-warning: #F59E0B;        /* Amber-500 */
  --vault-danger: #EF4444;         /* Red-500 */
  --vault-success: #10B981;        /* Emerald-500 */
}
```

### Typography

```css
/* Font Stack */
:root {
  --font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', monospace;
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Type Scale */
.text-xs    { font-size: 0.75rem; }   /* 12px */
.text-sm    { font-size: 0.875rem; }  /* 14px */
.text-base  { font-size: 1rem; }      /* 16px */
.text-lg    { font-size: 1.125rem; }  /* 18px */
.text-xl    { font-size: 1.25rem; }   /* 20px */
.text-2xl   { font-size: 1.5rem; }    /* 24px */
.text-3xl   { font-size: 1.875rem; }  /* 30px */

/* Usage */
body { font-family: var(--font-sans); }
code, .data-field, .node-label { font-family: var(--font-mono); }
```

### Component Patterns

```css
/* Card */
.vault-card {
  background: var(--vault-bg-secondary);
  border: 1px solid var(--vault-border);
  border-radius: 0.5rem;
  padding: 1rem;
}

/* Panel */
.vault-panel {
  background: var(--vault-bg-primary);
  border-left: 1px solid var(--vault-border);
}

/* Badge */
.vault-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-family: var(--font-mono);
  text-transform: uppercase;
}

.vault-badge--tier-3 {
  background: var(--tier-3-ai-glow);
  color: var(--tier-3-ai);
  border: 1px solid var(--tier-3-ai);
}

.vault-badge--tier-2 {
  background: var(--tier-2-verified-glow);
  color: var(--tier-2-verified);
  border: 1px solid var(--tier-2-verified);
}

.vault-badge--tier-1 {
  background: var(--tier-1-certified-glow);
  color: var(--tier-1-certified);
  border: 1px solid var(--tier-1-certified);
}
```

---

## Page Structure

### Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  HEADER: Case Title | Status | Legal Disclaimer Toggle             │
├──────────────────────────────────────────┬──────────────────────────┤
│                                          │                          │
│                                          │      DOSSIER PANEL       │
│            KNOWLEDGE GRAPH               │                          │
│            (Force-Directed)              │  - Entity Details        │
│                                          │  - Source Documents      │
│                                          │  - Timeline Events       │
│                                          │  - Related Entities      │
│                                          │                          │
├──────────────────────────────────────────┴──────────────────────────┤
│  FOOTER: Verification Legend | Processing Date | Disclaimer         │
└─────────────────────────────────────────────────────────────────────┘
```

### Responsive Breakpoints

```css
/* Mobile: Stack panels */
@media (max-width: 768px) {
  .vault-layout {
    flex-direction: column;
  }
  .dossier-panel {
    width: 100%;
    height: 50vh;
  }
}

/* Desktop: Side-by-side */
@media (min-width: 769px) {
  .vault-layout {
    flex-direction: row;
  }
  .knowledge-graph {
    flex: 1;
  }
  .dossier-panel {
    width: 400px;
  }
}
```

---

## Component Specifications

### 1. Knowledge Graph

The centerpiece visualization using `react-force-graph-2d`.

```typescript
// components/KnowledgeGraph.tsx

import ForceGraph2D from 'react-force-graph-2d';
import { useCallback, useRef } from 'react';
import { GraphData, Node, Link } from '@/lib/types';

interface KnowledgeGraphProps {
  data: GraphData;
  onNodeClick: (node: Node) => void;
  selectedNodeId: string | null;
  viewMode?: 'filtered' | 'clustered' | 'focus' | 'full';
  filterEntityType?: EntityType | 'all';
}

export function KnowledgeGraph({
  data,
  onNodeClick,
  selectedNodeId,
  viewMode = 'filtered',
  filterEntityType = 'all'
}: KnowledgeGraphProps) {
  const graphRef = useRef<any>();
  const [optimizedData, setOptimizedData] = useState<GraphData>(data);

  // Apply optimizations based on view mode
  useEffect(() => {
    let optimized = data;

    // Filter by entity type first
    if (filterEntityType !== 'all') {
      optimized = {
        ...optimized,
        nodes: optimized.nodes.filter(n => n.entity_type === filterEntityType),
        links: optimized.links.filter(l => {
          const sourceNode = optimized.nodes.find(n => n.id === l.source);
          const targetNode = optimized.nodes.find(n => n.id === l.target);
          return sourceNode?.entity_type === filterEntityType || targetNode?.entity_type === filterEntityType;
        })
      };
    }

    // Apply view mode optimization
    switch (viewMode) {
      case 'filtered':
        optimized = optimizeGraph(optimized, { mode: 'filtered', nodeLimit: 300 });
        break;
      case 'focus':
        if (selectedNodeId) {
          optimized = optimizeGraph(optimized, {
            mode: 'focus',
            focusNodeId: selectedNodeId,
            hopDistance: 2
          });
        }
        break;
      case 'full':
        // No optimization, show all
        break;
    }

    setOptimizedData(optimized);
  }, [data, viewMode, filterEntityType, selectedNodeId]);
  
  // Node color based on verification tier
  const getNodeColor = useCallback((node: Node) => {
    const tierColors = {
      'TIER_3_AI': '#6B7280',        // Grey
      'TIER_2_ANALYST': '#F59E0B',   // Amber/Gold
      'TIER_2_INSTITUTIONAL': '#D97706', // Darker amber (for distinction)
      'TIER_1_CERTIFIED': '#3B82F6', // Blue
    };
    return tierColors[node.verification.tier] || '#6B7280';
  }, []);
  
  // Node size based on connection count
  const getNodeSize = useCallback((node: Node) => {
    const connections = data.links.filter(
      l => l.source === node.id || l.target === node.id
    ).length;
    return Math.max(6, Math.min(20, 6 + connections * 2));
  }, [data.links]);
  
  // Custom node rendering
  const nodeCanvasObject = useCallback((node: any, ctx: CanvasRenderingContext2D) => {
    const size = getNodeSize(node);
    const color = getNodeColor(node);
    const isSelected = node.id === selectedNodeId;
    
    // Glow effect for selected node
    if (isSelected) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, size + 4, 0, 2 * Math.PI);
      ctx.fillStyle = `${color}40`;
      ctx.fill();
    }
    
    // Node circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
    
    // Border
    ctx.strokeStyle = isSelected ? '#FFFFFF' : `${color}80`;
    ctx.lineWidth = isSelected ? 2 : 1;
    ctx.stroke();
    
    // Label
    ctx.font = '10px JetBrains Mono';
    ctx.fillStyle = '#F8FAFC';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText(node.name, node.x, node.y + size + 4);
  }, [getNodeColor, getNodeSize, selectedNodeId]);
  
  // Link styling
  const linkColor = useCallback((link: Link) => {
    const tierColors = {
      'TIER_3_AI': '#6B728040',
      'TIER_2_ANALYST': '#F59E0B60',
      'TIER_2_INSTITUTIONAL': '#D9770660',
      'TIER_1_CERTIFIED': '#3B82F680',
    };
    return tierColors[link.verification.tier] || '#6B728040';
  }, []);
  
  return (
    <div className="h-full w-full bg-slate-900">
      <ForceGraph2D
        ref={graphRef}
        graphData={{
          nodes: data.nodes,
          links: data.links.map(l => ({
            ...l,
            source: l.source,
            target: l.target,
          })),
        }}
        nodeCanvasObject={nodeCanvasObject}
        linkColor={linkColor}
        linkWidth={1.5}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
        onNodeClick={(node) => onNodeClick(node as Node)}
        backgroundColor="#0F172A"
        // Physics settings for Obsidian-like feel
        d3VelocityDecay={0.3}
        d3AlphaDecay={0.02}
        warmupTicks={100}
        cooldownTicks={200}
      />
    </div>
  );
}
```

**Graph Configuration:**

```typescript
// lib/graph-config.ts

export const GRAPH_CONFIG = {
  // Force simulation
  d3Force: {
    charge: -300,        // Node repulsion
    link: {
      distance: 100,     // Preferred link length
    },
    center: true,
    collision: {
      radius: 30,        // Prevent overlap
    },
  },
  
  // Visual
  nodeRelSize: 6,        // Base node size
  linkWidth: 1.5,
  linkDirectionalArrowLength: 4,
  
  // Interaction
  enableZoom: true,
  enablePan: true,
  enableNodeDrag: true,
  
  // Performance
  warmupTicks: 100,
  cooldownTicks: 200,
};
```

### 2. Dossier Panel

Right-side detail panel shown when a node is selected.

```typescript
// components/DossierPanel.tsx

import { Node, Link, GraphData } from '@/lib/types';
import { NodeBadge } from './NodeBadge';
import { SourceList } from './SourceList';
import { RelatedEntities } from './RelatedEntities';

interface DossierPanelProps {
  node: Node | null;
  graphData: GraphData;
  onNodeSelect: (nodeId: string) => void;
}

export function DossierPanel({ node, graphData, onNodeSelect }: DossierPanelProps) {
  if (!node) {
    return (
      <div className="vault-panel h-full flex items-center justify-center text-slate-500">
        <p className="text-center">
          Select a node in the graph<br />
          to view details
        </p>
      </div>
    );
  }
  
  // Find related links and entities
  const relatedLinks = graphData.links.filter(
    l => l.source === node.id || l.target === node.id
  );
  
  const relatedNodeIds = new Set(
    relatedLinks.flatMap(l => [l.source, l.target]).filter(id => id !== node.id)
  );
  
  const relatedNodes = graphData.nodes.filter(n => relatedNodeIds.has(n.id));
  
  // Find source documents
  const extractedFromIds = (node.extracted_from || '')
    .split(',')
    .map(id => id.trim())
    .filter(Boolean);
  const extractedFromSet = new Set(extractedFromIds);
  const sourceDocuments = graphData.nodes.filter(
    n => n.entity_type === 'DOCUMENT' && extractedFromSet.has(n.id)
  );
  
  return (
    <div className="vault-panel h-full overflow-y-auto p-4 space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-start justify-between">
          <h2 className="text-xl font-semibold text-slate-50">
            {node.name}
          </h2>
          <NodeBadge tier={node.verification.tier} />
        </div>
        <p className="text-sm text-slate-400 font-mono">
          {node.entity_type} • {node.id}
        </p>
      </div>
      
      {/* Verification Info */}
      <section className="vault-card">
        <h3 className="text-sm font-semibold text-slate-300 mb-2">
          Verification
        </h3>
        <div className="space-y-1 text-sm">
          <p className="text-slate-400">
            Confidence: <span className="text-slate-200 font-mono">
              {(node.verification.confidence * 100).toFixed(0)}%
            </span>
          </p>
          {node.verification.notes && (
            <p className="text-slate-500 italic">
              {node.verification.notes}
            </p>
          )}
        </div>
        
        {/* TIER_3 Disclaimer */}
        {node.verification.tier === 'TIER_3_AI' && (
          <div className="mt-3 p-2 bg-slate-800 rounded border border-slate-700">
            <p className="text-xs text-slate-500">
              ⚠️ AI-extracted data. Not verified by human analyst.
              Confidence scores indicate extraction reliability, not factual accuracy.
            </p>
          </div>
        )}
      </section>
      
      {/* Entity Data */}
      <section className="vault-card">
        <h3 className="text-sm font-semibold text-slate-300 mb-2">
          Details
        </h3>
        <EntityDataDisplay data={node} type={node.entity_type} />
      </section>
      
      {/* Aliases */}
      {node.alternate_names && node.alternate_names.length > 0 && (
        <section className="vault-card">
          <h3 className="text-sm font-semibold text-slate-300 mb-2">
            Also Known As
          </h3>
          <div className="flex flex-wrap gap-2">
            {node.alternate_names.map((alias, i) => (
              <span key={i} className="px-2 py-1 bg-slate-800 rounded text-sm text-slate-400 font-mono">
                {alias}
              </span>
            ))}
          </div>
        </section>
      )}
      
      {/* Source Documents */}
      {sourceDocuments.length > 0 && (
        <section className="vault-card">
          <h3 className="text-sm font-semibold text-slate-300 mb-2">
            Source Documents ({sourceDocuments.length})
          </h3>
          <SourceList 
            documents={sourceDocuments} 
            onDocumentClick={(docId) => onNodeSelect(docId)}
          />
        </section>
      )}
      
      {/* Related Entities */}
      {relatedNodes.length > 0 && (
        <section className="vault-card">
          <h3 className="text-sm font-semibold text-slate-300 mb-2">
            Related Entities ({relatedNodes.length})
          </h3>
          <RelatedEntities 
            nodes={relatedNodes}
            links={relatedLinks}
            currentNodeId={node.id}
            onNodeClick={onNodeSelect}
          />
        </section>
      )}
    </div>
  );
}
```

### 3. Node Badge

Verification tier indicator.

```typescript
// components/NodeBadge.tsx

import { VerificationTier } from '@/lib/types';

const TIER_CONFIG = {
  'TIER_3_AI': {
    label: 'AI',
    className: 'bg-gray-500/20 text-gray-400 border-gray-500',
    icon: null
  },
  'TIER_2_ANALYST': {
    label: 'VERIFIED',
    className: 'bg-amber-500/20 text-amber-400 border-amber-500',
    icon: null
  },
  'TIER_2_INSTITUTIONAL': {
    label: 'FH VERIFIED',
    className: 'bg-amber-600/20 text-amber-500 border-amber-600',
    icon: '🏛️'  // Building/institution emoji
  },
  'TIER_1_CERTIFIED': {
    label: 'CERTIFIED',
    className: 'bg-blue-500/20 text-blue-400 border-blue-500',
    icon: '✓'
  },
};

interface NodeBadgeProps {
  tier: VerificationTier;
  size?: 'sm' | 'md';
}

export function NodeBadge({ tier, size = 'sm' }: NodeBadgeProps) {
  const config = TIER_CONFIG[tier];

  return (
    <span className={`
      inline-flex items-center gap-1
      px-2 py-0.5
      rounded
      border
      font-mono 
      uppercase
      ${size === 'sm' ? 'text-xs' : 'text-sm'}
      ${config.className}
    `}>
      {config.icon && <span className="text-sm">{config.icon}</span>}
      {config.label}
    </span>
  );
}
```

### 4. Source Viewer

Document image viewer with OCR text overlay.

```typescript
// components/SourceViewer.tsx

import { useState } from 'react';
import { Node } from '@/lib/types';

interface SourceViewerProps {
  document: Node;
}

export function SourceViewer({ document }: SourceViewerProps) {
  const [showOcr, setShowOcr] = useState(false);
  const [zoom, setZoom] = useState(1);
  
  const docData = document as {
    file_path?: string;
    ocr_text?: string;
    summary?: string;
  };
  
  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-2 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <button 
            onClick={() => setZoom(z => Math.max(0.5, z - 0.25))}
            className="px-2 py-1 bg-slate-800 rounded hover:bg-slate-700"
          >
            -
          </button>
          <span className="text-sm font-mono">{Math.round(zoom * 100)}%</span>
          <button 
            onClick={() => setZoom(z => Math.min(3, z + 0.25))}
            className="px-2 py-1 bg-slate-800 rounded hover:bg-slate-700"
          >
            +
          </button>
        </div>
        
        <button
          onClick={() => setShowOcr(!showOcr)}
          className={`px-3 py-1 rounded text-sm ${
            showOcr ? 'bg-blue-600' : 'bg-slate-800 hover:bg-slate-700'
          }`}
        >
          {showOcr ? 'Hide OCR' : 'Show OCR'}
        </button>
      </div>
      
      {/* Document View */}
      <div className="flex-1 overflow-auto p-4">
        {showOcr ? (
          <div className="bg-slate-800 p-4 rounded">
            <pre className="text-sm text-slate-300 whitespace-pre-wrap font-mono">
              {docData.ocr_text || 'No OCR text available'}
            </pre>
          </div>
        ) : (
          <div className="flex justify-center">
            <img
              src={`/data/images/${docData.file_path}`}
              alt={document.name}
              style={{ transform: `scale(${zoom})`, transformOrigin: 'top center' }}
              className="max-w-full shadow-lg"
            />
          </div>
        )}
      </div>
      
      {/* Summary */}
      {docData.summary && (
        <div className="p-3 border-t border-slate-700 bg-slate-800/50">
          <p className="text-sm text-slate-400">
            <span className="font-semibold text-slate-300">Summary: </span>
            {docData.summary}
          </p>
        </div>
      )}
    </div>
  );
}
```

### 5. OCR Text Display

**Purpose:** Display extracted OCR text from documents for transparency and analyst verification.

**Location:** Extend SourceViewer component to show OCR data from extraction JSONs.

**Data Source:**
- OCR data stored in extraction JSONs (not in graph nodes)
- Path: `cases/{case_id}/extractions/{document_id}.json`
- Structure: `extraction.ocr_result.{text, confidence, blocks, metadata}`

**Implementation Notes:**

Update SourceViewer to fetch and display OCR data:

```typescript
// Add OCR confidence display with color coding
function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.9) return 'text-green-400';   // High confidence
  if (confidence >= 0.7) return 'text-yellow-400';  // Medium confidence
  return 'text-red-400';                            // Low confidence - warn user
}

// In SourceViewer, show OCR metadata above text:
<div className="flex items-center gap-3 text-sm pb-2 border-b border-slate-700">
  <span className={`font-mono ${getConfidenceColor(ocrData.confidence)}`}>
    OCR Confidence: {(ocrData.confidence * 100).toFixed(0)}%
  </span>
  {ocrData.metadata.language && (
    <span className="text-slate-400">
      Language: {ocrData.metadata.language.toUpperCase()}
    </span>
  )}
</div>

<pre className="text-sm text-slate-300 whitespace-pre-wrap font-mono leading-relaxed">
  {ocrData.text}
</pre>
```

**Display Rules:**
- Color-code confidence: Green ≥90%, Yellow 70-89%, Red <70%
- Show detected language from `metadata.language`
- Preserve whitespace/formatting from original
- TIER_3_AI disclaimer required for unverified OCR text
- Load extraction JSON on-demand (when user clicks "Show OCR")

**Access Control:**
- OCR text follows case-based permissions (same as entities)
- If user can view case, they can view OCR text

**Future Enhancement (Out of Scope for MVP1):**
- OCR Block Viewer showing per-block confidence and bounding boxes
- Click entity → highlight source text in document (requires mapping)
- OCR text search within document

### 6. Timeline View

Chronological event display.

```typescript
// components/TimelineView.tsx

import { TimelineEvent } from '@/lib/types';
import { NodeBadge } from './NodeBadge';

interface TimelineViewProps {
  events: TimelineEvent[];
  onEntityClick: (entityId: string) => void;
}

export function TimelineView({ events, onEntityClick }: TimelineViewProps) {
  // Sort events by date
  const sortedEvents = [...events].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );
  
  return (
    <div className="relative pl-4">
      {/* Timeline line */}
      <div className="absolute left-0 top-0 bottom-0 w-px bg-slate-700" />
      
      {sortedEvents.map((event, index) => (
        <div key={index} className="relative pb-6 last:pb-0">
          {/* Timeline dot */}
          <div className={`
            absolute -left-1.5 w-3 h-3 rounded-full border-2
            ${event.verification === 'TIER_1_CERTIFIED' ? 'bg-blue-500 border-blue-400' :
              event.verification === 'TIER_2_INSTITUTIONAL' ? 'bg-amber-600 border-amber-500' :
              event.verification === 'TIER_2_ANALYST' ? 'bg-amber-500 border-amber-400' :
              'bg-gray-500 border-gray-400'}
          `} />
          
          {/* Event content */}
          <div className="ml-4">
            <div className="flex items-center gap-2 mb-1">
              <time className="text-sm font-mono text-slate-400">
                {formatDate(event.date, event.date_precision)}
              </time>
              <NodeBadge tier={event.verification} size="sm" />
            </div>
            
            <p className="text-slate-200">{event.event}</p>
            
            {/* Related entities */}
            <div className="flex flex-wrap gap-1 mt-2">
              {event.entities.map(entityId => (
                <button
                  key={entityId}
                  onClick={() => onEntityClick(entityId)}
                  className="px-2 py-0.5 text-xs bg-slate-800 hover:bg-slate-700 rounded font-mono"
                >
                  {entityId}
                </button>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function formatDate(date: string, precision?: string): string {
  const d = new Date(date);
  switch (precision) {
    case 'year':
      return d.getFullYear().toString();
    case 'month':
      return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
    case 'decade':
      return `${Math.floor(d.getFullYear() / 10) * 10}s`;
    default:
      return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  }
}
```

### 7. Gap Alert

Display missing evidence warnings.

```typescript
// components/GapAlert.tsx

import { Gap } from '@/lib/types';

const PRIORITY_STYLES = {
  CRITICAL: 'border-red-500 bg-red-500/10',
  HIGH: 'border-amber-500 bg-amber-500/10',
  MEDIUM: 'border-yellow-500 bg-yellow-500/10',
  LOW: 'border-slate-500 bg-slate-500/10',
};

interface GapAlertProps {
  gap: Gap;
  onEntityClick: (entityId: string) => void;
}

export function GapAlert({ gap, onEntityClick }: GapAlertProps) {
  return (
    <div className={`border rounded p-3 ${PRIORITY_STYLES[gap.priority]}`}>
      <div className="flex items-center gap-2 mb-2">
        <span className={`
          px-2 py-0.5 rounded text-xs font-mono uppercase
          ${gap.priority === 'CRITICAL' ? 'bg-red-500 text-white' :
            gap.priority === 'HIGH' ? 'bg-amber-500 text-black' :
            gap.priority === 'MEDIUM' ? 'bg-yellow-500 text-black' :
            'bg-slate-500 text-white'}
        `}>
          {gap.priority}
        </span>
        <span className="text-sm text-slate-400 font-mono">
          {gap.gap_type?.replace(/_/g, ' ')}
        </span>
      </div>
      
      <p className="text-sm text-slate-300 mb-2">
        {gap.description}
      </p>
      
      {/* Related entities */}
      {gap.related_entities.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {gap.related_entities.map(entityId => (
            <button
              key={entityId}
              onClick={() => onEntityClick(entityId)}
              className="px-2 py-0.5 text-xs bg-slate-800 hover:bg-slate-700 rounded font-mono"
            >
              {entityId}
            </button>
          ))}
        </div>
      )}
      
      {/* Suggested sources */}
      {gap.suggested_sources && gap.suggested_sources.length > 0 && (
        <div className="mt-2 pt-2 border-t border-slate-700">
          <p className="text-xs text-slate-500 mb-1">Suggested sources:</p>
          <ul className="text-xs text-slate-400 list-disc list-inside">
            {gap.suggested_sources.map((source, i) => (
              <li key={i}>{source}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

---

## Page Components

### Dashboard Page

```typescript
// app/case/[id]/page.tsx

import { GraphData } from '@/lib/types';
import { KnowledgeGraph } from '@/components/KnowledgeGraph';
import { DossierPanel } from '@/components/DossierPanel';
import { useState } from 'react';

export default function CaseDashboard({ params }: { params: { id: string } }) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  
  // Load graph data (static import for MVP)
  const graphData: GraphData = require(`@/public/data/${params.id}/graph_data.json`);
  
  const selectedNode = selectedNodeId 
    ? graphData.nodes.find(n => n.id === selectedNodeId) 
    : null;
  
  return (
    <div className="h-screen flex flex-col bg-slate-900">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-semibold text-slate-50">
            {graphData.metadata.case_id}
          </h1>
          <p className="text-sm text-slate-400 font-mono">
            {graphData.metadata.case_id}
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          <span className="text-sm text-slate-500">
            {graphData.metadata.entity_count} entities • {graphData.metadata.relation_count} relations
          </span>
        </div>
      </header>
      
      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Graph */}
        <div className="flex-1">
          <KnowledgeGraph
            data={graphData}
            onNodeClick={(node) => setSelectedNodeId(node.id)}
            selectedNodeId={selectedNodeId}
          />
        </div>
        
        {/* Dossier Panel */}
        <div className="w-[400px] border-l border-slate-800">
          <DossierPanel
            node={selectedNode}
            graphData={graphData}
            onNodeSelect={setSelectedNodeId}
          />
        </div>
      </div>
      
      {/* Footer */}
      <footer className="px-6 py-3 border-t border-slate-800 bg-slate-900/50">
        <div className="flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-gray-500" /> AI Inference
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-amber-500" /> Verified
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-blue-500" /> Certified
            </span>
          </div>
          
          <p>
            Processed: {new Date(graphData.metadata.updated_at).toLocaleDateString()}
          </p>
        </div>
      </footer>
    </div>
  );
}
```

---

## Legal Disclaimer Component

Required on all pages.

```typescript
// components/LegalDisclaimer.tsx

interface LegalDisclaimerProps {
  disclaimer: string;
  expanded?: boolean;
}

export function LegalDisclaimer({ disclaimer, expanded = false }: LegalDisclaimerProps) {
  const [isExpanded, setIsExpanded] = useState(expanded);
  
  return (
    <div className="bg-slate-800 border border-slate-700 rounded p-3">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full text-left"
      >
        <span className="text-sm font-semibold text-slate-300">
          ⚖️ Legal Disclaimer
        </span>
        <span className="text-slate-500">
          {isExpanded ? '▼' : '▶'}
        </span>
      </button>
      
      {isExpanded && (
        <p className="mt-2 text-xs text-slate-400 leading-relaxed">
          {disclaimer}
        </p>
      )}
    </div>
  );
}
```

---

## Project Setup

### Dependencies

```json
// package.json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-force-graph-2d": "^1.24.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.2.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.3.0",
    "typescript": "^5.0.0"
  }
}
```

### Tailwind Configuration

```javascript
// tailwind.config.js
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        sans: ['Inter', '-apple-system', 'sans-serif'],
      },
      colors: {
        'tier-3': '#6B7280',
        'tier-2': '#F59E0B',
        'tier-1': '#3B82F6',
      },
    },
  },
  plugins: [],
};
```

---

## Accessibility

- All interactive elements have focus states
- Color is not the only indicator (badges have text labels)
- Keyboard navigation for graph (arrow keys, enter to select)
- Screen reader labels on all controls
- Sufficient color contrast (WCAG AA)

---

*This specification defines the MVP1 Vault interface. Advanced features (authentication, multi-case, real-time updates) are deferred to MVP2.*
