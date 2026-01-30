# Farmer House Forensic Intelligence Platform — Frontend Specification (The Vault)

> **Document Classification:** Internal Engineering Reference
> **Version:** 4.0.0
> **Last Updated:** 2026-01-29
> **Status:** MVP1 Active Implementation (Document-First + Document Grouping)

---

## Overview

Zone B (The Vault) is the client-facing read-only interface for viewing forensic dossiers. It implements a **document-first navigation architecture** that presents case data through multiple complementary views: Documents, Entities, Narrative Timeline, and Knowledge Graph.

**Core Principles:**
- **Read-Only**: No uploads, edits, or deletions
- **Document-First**: Primary navigation through documents, not the graph
- **Multi-View**: Same data accessible through different lenses (documents, entities, timeline, graph)
- **Intelligence Aesthetic**: Dark mode, monospace, high-stakes professional
- **Performance-First**: Server-side rendering with client-side interactivity

**Data Sources:**
- `graph_data.json` from Zone A — entities, relationships, verification tiers
- `document_groups.yaml` — multi-part document grouping (maps extraction files to logical documents)
- `extractions/*.json` — per-page extraction data (OCR text, entities, confidence)
- `case_narrative.json` — optional narrative periods with highlighted events

All accessed through case-specific API routes. A shared utility module (`lib/document-groups.ts`) provides document group resolution across all routes.

**Graph Data Contract (Aligned to `graph_data.json`):**
- **Nodes** use `entity_type` and `name` (not `type`/`label`).
- **Links** use `relation_type` (not `label`) and are the primary driver for view filters.
- **Provenance** lives on `extracted_from` (comma-delimited string of document IDs; split + trim).
- **Verification tiers** are `TIER_1_CERTIFIED`, `TIER_2_ANALYST`, `TIER_3_AI`, `TIER_4_SOURCE`.

---

## Navigation Architecture

### Route Structure

```
/case/[caseId]/                    → Dashboard (case overview)
/case/[caseId]/documents           → Document Browser
/case/[caseId]/entities            → Entity Browser (grouped by type)
/case/[caseId]/narrative           → Timeline View (grouped by decade)
/case/[caseId]/graph               → Knowledge Graph (interactive visualization)
/case/[caseId]/entity/[entityId]   → Entity Detail Page
/case/[caseId]/document/[docId]    → Document Viewer
```

### Sidebar Navigation

The case layout includes a persistent sidebar with navigation:

```
┌─────────────────────────────────────────────────────────────────────┐
│  HEADER: Case Title | Status                                        │
├─────────────┬───────────────────────────────────────────────────────┤
│             │                                                        │
│  SIDEBAR    │                    MAIN CONTENT                        │
│             │                                                        │
│  Dashboard  │  (Varies by route)                                     │
│  Documents  │                                                        │
│  Entities   │                                                        │
│  Narrative  │                                                        │
│  Graph      │                                                        │
│             │                                                        │
├─────────────┴───────────────────────────────────────────────────────┤
│  FOOTER: Verification Legend | Legal Disclaimer                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

All API routes follow Next.js App Router conventions with async params.

### GET `/api/cases/[caseId]/dashboard`

Returns aggregated metrics for the case dashboard.

**Response:**
```typescript
interface DashboardData {
  metrics: {
    documents: number;
    entities: number;
    relationships: number;
    stage: string;           // Current workflow stage
    stageProgress: number;   // 0-100 percentage
  };
  verificationDistribution: {
    TIER_3_AI: number;
    TIER_2_ANALYST: number;
    TIER_1_CERTIFIED: number;
    TIER_4_SOURCE: number;
  };
  entityTypeSummary: Record<string, number>;
  dateRange: {
    earliest: string | null;  // ISO date
    latest: string | null;
  };
  workflowStages: WorkflowStages;
}
```

### GET `/api/cases/[caseId]/entities`

Returns all entities grouped by type.

**Response:**
```typescript
interface EntitiesResponse {
  entities: {
    PERSON: EntityInfo[];
    PROPERTY: EntityInfo[];
    ORGANIZATION: EntityInfo[];
    LOCATION: EntityInfo[];
  };
  totalCount: number;
  documentCount: number;
  metadata: GraphMetadata;
}

interface EntityInfo {
  id: string;
  name: string;
  entity_type: EntityType;
  verification: Verification;
  extracted_from: string;
  // Type-specific fields (dates, addresses, etc.)
}
```

### GET `/api/cases/[caseId]/timeline`

Returns documents grouped by time period for narrative view.

**Response:**
```typescript
interface TimelineResponse {
  periods: TimePeriod[];
  totalDocuments: number;
  dateRange: {
    earliest_document: string | null;
    latest_document: string | null;
  };
}

interface TimePeriod {
  id: string;
  title: string;        // Contextual title (e.g., "Expropriation Period")
  startYear: number;
  endYear: number;
  documents: DocumentInfo[];
  entities: EntityInfo[];
}
```

**Period Titles (Contextual to Cuban History):**
| Year Range | Title |
|------------|-------|
| 1959-1961 | "Expropriation Period" |
| 1962-1969 | "Early Revolutionary Period" |
| 1950-1958 | "Pre-Revolutionary Period" |
| Default | "[Decade] - [Decade+9]" |

### GET `/api/cases/[caseId]/documents`

Returns all documents for a case, with multi-part documents aggregated into single entries.

**Response:**
```typescript
interface DocumentsResponse {
  documents: {
    id: string;           // "doc_<groupId>" for grouped, stem for standalone
    filename: string;     // Group name or original filename
    date: string | null;
    type: string | null;  // Inferred from filename heuristics
    entityCount: number;
    confidence: number;   // Max OCR confidence across pages
    partCount: number;    // Number of pages/parts
    imagePath: string;
  }[];
}
```

### GET `/api/cases/[caseId]/document/[docId]`

Returns document detail with per-page data for grouped documents.

**Response:**
```typescript
interface DocumentDetailResponse {
  id: string;
  filename: string;
  date: string | null;
  type: string | null;
  entityCount: number;
  confidence: number;
  imagePath: string;
  ocrText: string;            // First page OCR text
  translatedText: string | null;
  entities: Entity[];         // All entities across pages
  detectedLanguage: string;
  pages?: {                   // Present for grouped documents
    ocrText: string;
    translatedText: string | null;
    imagePath: string;        // Includes ?page=N param
    entities: Entity[];
  }[];
}
```

### GET `/api/cases/[caseId]/document/[docId]/image`

Serves the intake file (PDF/JPG/PNG) for a document. Supports `?page=N` for grouped documents.

### GET `/api/cases/[caseId]/entity/[entityId]`

Returns entity detail with source documents resolved to document groups.

**Response:**
```typescript
interface EntityDetailResponse {
  entity: BaseNode;
  sourceDocuments: {
    id: string;       // "doc_<groupId>" or extraction stem
    filename: string; // Group name or "<stem>.pdf"
  }[];
  connections: {
    relation_type: string;
    targetEntity: EntityInfo | null;
  }[];
}
```

### GET `/api/cases/[caseId]/graph`

Returns the full graph data for visualization.

**Response:** Complete `GraphData` object as defined in `/lib/types.ts`.

---

## Shared Modules

### `lib/document-groups.ts`

Single source of truth for document group operations, used by all 5 API routes that deal with documents.

**Exports:**
| Function | Purpose |
|----------|---------|
| `loadDocumentGroups(caseDir)` | Load and validate `document_groups.yaml` (returns null if missing or not CONFIRMED) |
| `buildFileToGroupMap(groups)` | Map file stems + full filenames → `DocumentGroup` |
| `matchExtractionToGroup(baseName, map)` | Match extraction basename (strips `_page_N`) to group |
| `findGroupForDocId(caseDir, docId)` | Resolve `doc_`-prefixed ID directly to its group |
| `findGroupExtractionFiles(extractionsDir, group)` | Find and sort extraction JSONs matching a group's files |
| `inferType(name)` | Heuristic document type inference from filename |

**Consumers:**
- `/api/cases/[caseId]/documents/` — document list aggregation
- `/api/cases/[caseId]/document/[docId]/` — grouped document detail + pages
- `/api/cases/[caseId]/document/[docId]/image/` — page-aware image serving
- `/api/cases/[caseId]/timeline/` — timeline period grouping
- `/api/cases/[caseId]/entity/[entityId]/` — source document name resolution

---

## Page Components

### Dashboard Page (`/case/[caseId]/page.tsx`)

The case overview page with key metrics and workflow progress.

**Features:**
- Metrics grid (stage, documents, entities, relationships)
- Verification status bar (stacked progress by tier)
- Workflow checklist (intake, processing, analysis, certification)
- Click-through links to detail views

**Key Components:**
- `WorkflowChecklist` - Expandable checklist with completion status

### Entity Browser (`/case/[caseId]/entities/page.tsx`)

Displays all entities grouped by type with verification badges.

**Features:**
- Type-based grouping (PERSON, PROPERTY, ORGANIZATION, LOCATION)
- Expandable sections per entity type
- Entity count badges
- Verification tier indicators
- Click-through to entity detail pages

**Component:** `components/Entities/EntityBrowser.tsx`

```typescript
interface EntityBrowserProps {
  entities: GroupedEntities;
  caseId: string;
}
```

### Narrative Timeline (`/case/[caseId]/narrative/page.tsx`)

Documents organized chronologically by decade with contextual Cuban history titles.

**Features:**
- Time period grouping (decade-based)
- Contextual period titles
- AI disclaimer banner (TIER_3_AI warning)
- Expandable period sections
- Document cards with extracted entities

**Component:** `components/Narrative/TimelinePeriod.tsx`

```typescript
interface TimelinePeriodProps {
  period: TimePeriodData;
  caseId: string;
  index: number;
  defaultOpen?: boolean;
}
```

**Visual Design:**
- Timeline track with period markers
- Period cards with document count
- Entity chips showing extracted entities per document
- Alternating layout for visual interest

### Graph View (`/case/[caseId]/graph/page.tsx`)

Interactive knowledge graph visualization.

**Features:**
- Full-page graph canvas
- Navigation bar with back button
- Node click → entity detail navigation
- Settings panel integration

**Component:** `components/Graph/GraphView.tsx`

```typescript
interface GraphViewProps {
  caseId: string;
}
```

---

## Graph Visualization System

### Current Implementation

The graph visualization uses `react-force-graph-2d` with a comprehensive settings system that allows real-time customization of layout, appearance, and filtering.

### Graph Settings Panel

**Location:** Top-left corner, gear icon toggle
**Type:** Floating panel with three tabs: Layout, Colors, Filters
**Persistence:** Settings saved to localStorage for user preferences

#### Settings Architecture

```typescript
// lib/graph-settings.ts

export interface GraphSettings {
  // Display Settings
  nodeSizeMultiplier: number;    // Scale factor for degree-based sizing
  linkWidth: number;             // Link thickness
  showArrows: boolean;           // Show directional arrows on links

  // Force Simulation Settings
  centerForce: number;           // Gravity toward center (0-2)
  repelForce: number;            // Repulsion between nodes
  linkForce: number;             // Target distance between connected nodes

  // Color Settings
  entityColors: EntityColorMap;  // Custom colors per entity type
  linkColor: string;            // Base link color

  // Filter Settings
  entityTypeFilters: Record<EntityType, boolean>; // true = visible
  hideOrphans: boolean;         // Hide nodes with no connections
}

export const DEFAULT_SETTINGS: GraphSettings = {
  // Display
  nodeSizeMultiplier: 2,
  linkWidth: 2,
  showArrows: false,

  // Forces
  centerForce: 0.1,
  repelForce: 140,
  linkForce: 60,

  // Colors
  entityColors: {
    PERSON: '#7c3aed',
    LOCATION: '#0891b2',
    PROPERTY: '#059669',
    ORGANIZATION: '#dc2626',
    DOCUMENT: '#64748b',
  },
  linkColor: '#ffffff',

  // Filters
  entityTypeFilters: {
    PERSON: true,
    LOCATION: true,
    PROPERTY: true,
    ORGANIZATION: true,
    DOCUMENT: true,
  },
  hideOrphans: false,
};
```

#### Tab 1: Layout

Controls for graph physics and display:

**Display Section:**
- **Node Scale** (0.5-5.0): Multiplier for degree-based node sizing
- **Link Width** (0.2-4.0): Thickness of connection lines
- **Show Arrows** (toggle): Display directional arrows on links

**Forces Section:**
- **Center Force** (0-1.2): Pull toward center of view
- **Repel Force** (40-200): Push nodes apart
- **Link Distance** (30-140): Target distance between connected nodes

#### Tab 2: Colors

Color customization for entity types and links:

- **Link Color**: Base color for all connection lines
- **PERSON**: Color for person nodes
- **LOCATION**: Color for location nodes
- **PROPERTY**: Color for property nodes
- **ORGANIZATION**: Color for organization nodes
- **DOCUMENT**: Color for document nodes

Each entity type has a color picker for custom hex colors.

#### Tab 3: Filters (NEW)

Data visibility controls:

**Entity Types Section:**
- Toggle for each entity type (PERSON, LOCATION, PROPERTY, ORGANIZATION, DOCUMENT)
- When toggled off, nodes of that type are hidden
- Links between hidden nodes are also filtered out

**Visibility Section:**
- **Hide Orphans** (toggle): Hide nodes with no connections (degree === 0)

**Implementation:**
```typescript
// components/Graph/KnowledgeGraph.tsx

// Filter data based on settings
const filteredData: GraphData = useMemo(() => {
  // Filter nodes by entity type and orphan status
  const visibleNodes = data.nodes.filter(node => {
    // Check entity type filter
    if (!settings.entityTypeFilters[node.entity_type]) {
      return false;
    }

    // Check orphan filter
    if (settings.hideOrphans) {
      const degree = nodeDegrees.get(node.id) || 0;
      if (degree === 0) {
        return false;
      }
    }

    return true;
  });

  // Create set of visible node IDs for quick lookup
  const visibleNodeIds = new Set(visibleNodes.map(node => node.id));

  // Filter links where both source and target are visible
  const visibleLinks = data.links.filter(link => {
    const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
    const targetId = typeof link.target === 'string' ? link.target : link.target.id;
    return visibleNodeIds.has(sourceId) && visibleNodeIds.has(targetId);
  });

  return {
    metadata: data.metadata,
    nodes: visibleNodes,
    links: visibleLinks,
  };
}, [data, settings.entityTypeFilters, settings.hideOrphans, nodeDegrees]);
```

### Graph Rendering Features

**Node Rendering:**
- Size based on connection count (degree centrality)
- Color based on entity type
- Glow effect for selected/hovered nodes
- Smooth animations with reduced-motion support
- Labels visible at zoom > 1.05x

**Link Rendering:**
- Custom canvas rendering for smooth lines
- Optional directional arrows
- Highlight on node selection/hover
- Proper termination at node boundaries (avoiding overlap)

**Interaction:**
- Click node to view details in dossier panel
- Hover for preview highlight
- Drag nodes to reposition
- Zoom and pan controls
- Click background to deselect

**Performance Optimizations:**
- Dynamic bundle loading (ForceGraph2D loaded on demand)
- Memoized calculations for colors, sizes, and filtered data
- Efficient force simulation with configurable parameters
- Canvas-based rendering for smooth 60fps at 300+ nodes

---

## Future Enhancements (Out of Scope for MVP1)

### Graph Performance Strategy

**Status:** Planned for large-scale implementations

For cases with 1,000+ nodes, implement advanced filtering and optimization:

**Three-Tier Rendering Strategy:**

1. **Filtered View** - Show high-importance nodes only (~200-300)
2. **Clustered View** - Group entities by family/property
3. **Focus Mode** - Show selected node + N-hop neighbors

**Implementation:**
```typescript
// lib/graph-optimizer.ts (FUTURE)

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
  // Implementation for large-scale graph optimization
}
```

**Performance Benchmarks** (Target):
| Graph Size | Mode | Render Time | FPS | Status |
|------------|------|-------------|-----|--------|
| 100 nodes | Full | <100ms | 60 | ✓ Implemented |
| 300 nodes | Full | <200ms | 50-60 | ✓ Implemented |
| 500 nodes | Filtered | <500ms | 40-50 | ⏳ Future |
| 1,000 nodes | Focus | <300ms | 50-60 | ⏳ Future |
| 1,500 nodes | Clustered | 2-5s | 20-30 | ⏳ Future |

### Advanced Filter Views

**Status:** Planned for Phase 2

Horizontal tab system for pre-configured view modes:
- **Overview** - Core entities (properties + key people)
- **Families** - Group by family clusters
- **Properties** - Property-centric view
- **Timeline** - Temporal view (chronological)
- **Legal** - Legal acts & government actions
- **Full** - Complete unfiltered graph

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

  /* Entity Types (Current Implementation) */
  --entity-person: #7c3aed;        /* Violet-600 */
  --entity-location: #0891b2;      /* Cyan-600 */
  --entity-property: #059669;      /* Emerald-600 */
  --entity-organization: #dc2626;  /* Red-600 */
  --entity-document: #64748b;      /* Slate-500 */

  /* Graph Theme */
  --graph-background: #0b0e12;     /* Near-black */
  --graph-line: #2b323a;           /* Dark grey */
  --graph-line-highlight: rgba(110, 219, 227, 0.4); /* Cyan highlight */
  --graph-node-focused: #6edbe3;   /* Cyan-400 */
  --graph-text: #d6dee6;           /* Light grey */

  /* Accents */
  --vault-accent: #06B6D4;         /* Cyan-500 */
  --vault-warning: #F59E0B;        /* Amber-500 */
  --vault-danger: #EF4444;         /* Red-500 */
  --vault-success: #10B981;        /* Emerald-500 */
}
```

### Typography

```css
/* Font Stack */
:root {
  --font-mono: 'Space Grotesk', 'JetBrains Mono', 'SF Mono', monospace;
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

### Case Layout (Sidebar Navigation)

```
┌─────────────────────────────────────────────────────────────────────┐
│  HEADER: Logo | Case Title | User Menu                              │
├─────────────┬───────────────────────────────────────────────────────┤
│             │                                                        │
│  SIDEBAR    │                    MAIN CONTENT                        │
│  ─────────  │                                                        │
│  Dashboard  │  Content varies by route:                              │
│  Documents  │  - Dashboard: Metrics, workflow, verification          │
│  Entities   │  - Entities: Grouped entity browser                    │
│  Narrative  │  - Narrative: Timeline periods                         │
│  Graph      │  - Graph: Force-directed visualization                 │
│             │                                                        │
├─────────────┴───────────────────────────────────────────────────────┤
│  FOOTER: Legal Disclaimer | Verification Legend                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Graph Page Layout (Full-Screen)

```
┌─────────────────────────────────────────────────────────────────────┐
│  HEADER: ← Back to Case | Case Title                                │
├──────────────────────────────────────────┬──────────────────────────┤
│                                          │                          │
│                                          │      DOSSIER PANEL       │
│            KNOWLEDGE GRAPH               │                          │
│            (Force-Directed)              │  - Entity Details        │
│                                          │  - Source Documents      │
│  ⚙️ Settings Panel (Floating)           │  - Related Entities      │
│                                          │                          │
├──────────────────────────────────────────┴──────────────────────────┤
│  FOOTER: Verification Legend | Node Count                            │
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
// components/Graph/KnowledgeGraph.tsx

import ForceGraph2D from 'react-force-graph-2d';
import { useCallback, useRef, useMemo } from 'react';
import { GraphData, BaseNode } from '@/lib/types';
import { GraphSettings, DEFAULT_SETTINGS } from '@/lib/graph-settings';

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
  const graphRef = useRef<any>(null);

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
      const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
      const targetId = typeof link.target === 'string' ? link.target : link.target.id;
      degrees.set(sourceId, (degrees.get(sourceId) || 0) + 1);
      degrees.set(targetId, (degrees.get(targetId) || 0) + 1);
    });
    return degrees;
  }, [data.nodes, data.links]);

  // Filter data based on settings
  const filteredData: GraphData = useMemo(() => {
    const visibleNodes = data.nodes.filter(node => {
      if (!settings.entityTypeFilters[node.entity_type]) {
        return false;
      }
      if (settings.hideOrphans) {
        const degree = nodeDegrees.get(node.id) || 0;
        if (degree === 0) return false;
      }
      return true;
    });

    const visibleNodeIds = new Set(visibleNodes.map(node => node.id));
    const visibleLinks = data.links.filter(link => {
      const sourceId = typeof link.source === 'string' ? link.source : link.source.id;
      const targetId = typeof link.target === 'string' ? link.target : link.target.id;
      return visibleNodeIds.has(sourceId) && visibleNodeIds.has(targetId);
    });

    return {
      metadata: data.metadata,
      nodes: visibleNodes,
      links: visibleLinks,
    };
  }, [data, settings.entityTypeFilters, settings.hideOrphans, nodeDegrees]);

  // Node rendering with size based on degree
  const nodeCanvasObject = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale?: number) => {
    const degree = nodeDegrees.get(node.id) || 0;
    const size = BASE_NODE_SIZE + Math.pow(degree, 0.5) * settings.nodeSizeMultiplier;
    const color = settings.entityColors[node.entity_type];
    const isSelected = node.id === selectedNodeId;

    // Draw node with glow effect if selected
    if (isSelected) {
      ctx.shadowBlur = 24;
      ctx.shadowColor = `${color}80`;
    }

    ctx.beginPath();
    ctx.arc(node.x, node.y, size, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();

    // Border and label rendering...
  }, [nodeDegrees, settings, selectedNodeId]);

  // Custom link rendering with optional arrows
  const linkCanvasObject = useCallback((link: any, ctx: CanvasRenderingContext2D, globalScale?: number) => {
    // Draw line from source to target
    // If settings.showArrows, draw arrow at target end
    // Terminate line at node boundary, not center
  }, [settings.showArrows, settings.linkWidth]);

  return (
    <div className="h-full w-full bg-slate-900">
      <ForceGraph2D
        ref={graphRef}
        graphData={filteredData as any}
        nodeCanvasObject={nodeCanvasObject}
        linkCanvasObject={linkCanvasObject}
        linkColor={() => settings.linkColor}
        onNodeClick={onNodeClick}
        onBackgroundClick={onBackgroundClick}
        backgroundColor="#0F172A"
        d3VelocityDecay={0.35}
        d3AlphaDecay={0.025}
        warmupTicks={40}
        cooldownTicks={400}
      />
    </div>
  );
}
```

### 2. Graph Settings Panel

**Implementation:** `components/Graph/GraphSettingsPanel.tsx`

Three-tab floating panel with gear icon toggle:

```typescript
export function GraphSettingsPanel({
  settings,
  onUpdateSetting,
  onReset,
}: GraphSettingsPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'layout' | 'colors' | 'filters'>('layout');

  return (
    <div className="absolute top-4 left-4">
      {/* Gear Icon Toggle */}
      <button onClick={() => setIsOpen(!isOpen)}>
        {/* Animated gear icon with cyan glow when open */}
      </button>

      {/* Settings Panel */}
      {isOpen && (
        <div className="mt-3 rounded-xl bg-slate-900">
          {/* Header with Reset button */}

          {/* Tab Bar */}
          <div className="flex border-b border-slate-800">
            <button>Layout</button>
            <button>Colors</button>
            <button>Filters</button>
          </div>

          {/* Tab Content */}
          {activeTab === 'layout' && (
            <>
              <DisplaySection />
              <ForcesSection />
            </>
          )}

          {activeTab === 'colors' && (
            <ColorsSection />
          )}

          {activeTab === 'filters' && (
            <>
              <EntityTypeFilters />
              <VisibilityToggles />
            </>
          )}
        </div>
      )}
    </div>
  );
}
```

**Features:**
- Click-outside-to-close behavior
- Smooth slide-in animation
- Cyan accent colors matching graph theme
- Sliders with live value display
- Toggle switches for boolean settings
- Color pickers for entity colors
- Reset button to restore defaults

### 3. Entity Sidebar

Right-side slide-in panel shown when a graph node is selected. Fetches entity data from the API and renders the `EntityDetail` component inline.

```
┌────────────────────────────────────┬──────────────┐
│ KnowledgeGraph (flex-1)            │ EntitySidebar│
│                                    │ (500px)      │
│  Click node → fetch entity data    │ Entity header│
│  Click bg   → clear selection      │ Metadata     │
│                                    │ Source docs  │
│                                    │ Connections  │
└────────────────────────────────────┴──────────────┘
```

**Location:** `components/Graph/EntitySidebar.tsx`

**Props:**
- `selectedNodeId: string | null` — which node is selected
- `caseId: string` — case context for API fetch
- `isCollapsed: boolean` — sidebar width toggle
- `onToggleCollapse: () => void` — collapse/expand callback

**Behavior:**
- When `selectedNodeId` changes, fetches `/api/cases/{caseId}/entity/{entityId}`
- Renders `EntityDetail` with the fetched entity, source documents, and connections
- Collapsible to 48px rail with expand button
- Shows loading spinner during fetch, error state on failure
- Empty state prompts user to select a node

### 4. Node Badge

Verification tier indicator.

```typescript
// components/Graph/NodeBadge.tsx

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
    icon: '🏛️'
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

---

## Project Setup

### Dependencies

```json
// package.json
{
  "dependencies": {
    "next": "^16.1.4",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-force-graph-2d": "^1.24.0",
    "@clerk/nextjs": "^6.12.0",
    "@supabase/supabase-js": "^2.49.1"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^19",
    "@types/d3-force": "^3.0.10",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.7.3",
    "vitest": "^4.0.18"
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
        mono: ['Space Grotesk', 'JetBrains Mono', 'monospace'],
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

- All interactive elements have focus states with cyan ring
- Color is not the only indicator (badges have text labels)
- Keyboard navigation supported (Tab, Enter, Escape)
- Screen reader labels on all controls (aria-label, aria-pressed)
- Sufficient color contrast (WCAG AA minimum)
- Reduced motion support (prefers-reduced-motion respected)
- Click-outside-to-close for modal panels

---

## Testing

### Unit Tests

```typescript
// hooks/useGraph.test.ts
- ✓ Initializes with default settings
- ✓ Updates individual settings
- ✓ Resets to defaults
- ✓ Persists settings to localStorage
```

### Integration Tests

```typescript
// components/KnowledgeGraph.test.tsx
- ✓ Renders graph with filtered data
- ✓ Hides nodes based on entity type filters
- ✓ Hides orphan nodes when enabled
- ✓ Updates on settings change
```

---

## Performance Considerations

**Current Performance:**
- 100-300 nodes: 60 FPS consistently
- Real-time settings updates without lag
- Smooth animations and transitions
- Bundle size optimized with dynamic imports

**Optimization Techniques:**
1. **Memoization**: Expensive calculations cached with useMemo
2. **Dynamic Imports**: ForceGraph2D loaded on demand (~200KB saved)
3. **Canvas Rendering**: Direct canvas manipulation for custom nodes/links
4. **Efficient Filtering**: Set-based lookups for node visibility
5. **Debounced Updates**: Settings changes batched for performance

---

## Changelog

### Version 4.0.0 (2026-01-29)
- **Document Grouping**: All API routes support `document_groups.yaml` for multi-part documents
- **Shared `lib/document-groups.ts`**: Consolidated YAML loading, file-to-group mapping, extraction matching, and type inference into a single module used by 5 API routes
- New API endpoints: `/documents`, `/document/[docId]`, `/document/[docId]/image`
- Entity source documents resolve to group names (not raw extraction stems)
- Multi-page document viewer with prev/next page navigation
- `?page=N` support on image endpoint for grouped documents
- Iframe-based PDF viewer (replaced manual zoom controls)
- `js-yaml` dependency for server-side YAML parsing

### Version 3.0.0 (2026-01-26)
- **Document-First Architecture**: Complete navigation redesign
- Added sidebar navigation with Dashboard, Documents, Entities, Narrative, Graph views
- New API endpoints: `/dashboard`, `/entities`, `/timeline`, `/graph`
- New components: EntityBrowser, TimelinePeriod, GraphView
- Dashboard with real-time metrics and workflow tracking
- Timeline view with decade-based grouping and contextual Cuban history titles
- Entity browser with type-based grouping
- Updated page structure documentation
- Added TIER_4_SOURCE verification tier for source documents

### Version 2.0.0 (2026-01-26)
- Added Filters tab with entity type toggles and orphan hiding
- Implemented real-time graph filtering based on settings
- Updated documentation to reflect current implementation
- Marked future enhancements as out of scope for MVP1
- Added comprehensive testing section

### Version 1.1.0 (2025-01-21)
- Added graph settings panel with Layout and Colors tabs
- Implemented custom arrow rendering
- Added performance optimizations

### Version 1.0.0 (2025-01-20)
- Initial MVP1 implementation
- Basic knowledge graph with force-directed layout
- Dossier panel with entity details

---

*This specification reflects the current MVP1 implementation of The Vault interface with document-first navigation. For backend integration details, see `/docs/architecture/ARCHITECTURE.md`. For data schemas, see `/farmer_factory/structure/SCHEMA.md`.*
