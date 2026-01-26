# Frontend MVP Demo - Design Document

> **Document Classification:** Implementation Design
> **Version:** 1.0.0
> **Created:** 2026-01-25
> **Status:** Approved for Implementation

---

## Overview

Build a working Next.js 14 demo frontend to visualize the TEST-CERESA knowledge graph with integrated narrative generation. Focus: graph-centric interface with contextual narratives, no authentication/database (local development only). This plan aligns to the current `graph_data.json` export (`metadata`, `nodes`, `links`) and relation-type-driven filters.

**Scope:** MVP Demo (Phase 8A)
- Graph visualization with force-directed layout
- Entity details sidebar
- Narrative generation integration
- Dark theme, professional aesthetic

**Out of Scope (Future Phases):**
- Authentication (Clerk)
- Database (Supabase)
- Analyst verification workflow
- Analytics/monitoring
- Multi-case support

---

## Architecture

### Data Contract (Current Export)

- Graph JSON is `metadata` + `nodes` + `links` (no `edges` or `case_metadata`).
- Nodes use `entity_type` and `name`; provenance is `extracted_from` (comma-delimited).
- Links use `relation_type`; filters and highlighted events should be **relation-type driven**.

### Project Structure

```
farmer_vault/
├── app/
│   ├── layout.tsx              # Root layout (dark theme)
│   ├── page.tsx                # Landing/redirect to case
│   ├── case/[caseId]/
│   │   └── page.tsx            # Main dashboard
│   └── api/
│       └── cases/[caseId]/
│           ├── graph/route.ts  # Serves graph_data.json from Factory
│           └── narrative/route.ts  # Narrative generation (migrate existing)
├── components/
│   ├── KnowledgeGraph.tsx      # Force-directed visualization
│   ├── EntitySidebar.tsx       # Tabbed sidebar (Details/Narrative)
│   ├── DossierPanel.tsx        # Details tab content
│   ├── NarrativePanel.tsx      # Narrative tab (existing, adapt for tabs)
│   ├── NodeBadge.tsx           # Verification tier badges
│   ├── Header.tsx              # Case title, stats
│   └── ui/                     # Shared primitives (Button, Tabs)
├── hooks/
│   ├── useGraph.ts             # Fetch graph data
│   └── useNarrative.ts         # Narrative generation (existing)
├── lib/
│   ├── types.ts                # TypeScript interfaces from SCHEMA.md
│   └── graph-utils.ts          # Helper functions
└── public/
    └── (empty - no static data)
```

### Data Flow

1. **Dashboard loads** → `GET /api/cases/TEST-CERESA/graph` → renders graph
2. **User clicks node** → EntitySidebar shows Details tab
3. **User clicks "Generate Narrative"** → switches to Narrative tab → `POST /api/cases/TEST-CERESA/narrative` with `session_id`
4. **Narrative displays** with inline citations and highlighted events

### Technology Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS (forensic intelligence theme)
- **Graph:** react-force-graph-2d (dynamically imported)
- **State:** React hooks + SWR for data fetching
- **Fonts:** IBM Plex Mono (display), Source Serif 4 (body), Fira Code (mono)

---

## Component Design

### 1. Dashboard Layout (app/case/[caseId]/page.tsx)

Two-column responsive layout with server/client component split:

```typescript
// SERVER COMPONENT - Pre-fetches graph data
import { getGraphData } from '@/lib/graph-api';
import { DashboardClient } from './DashboardClient';
import { ErrorState } from '@/components/ErrorState';

export default async function CaseDashboard({
  params,
}: {
  params: { caseId: string };
}) {
  try {
    // PERFORMANCE: Server-side data fetching eliminates loading state
    const graphData = await getGraphData(params.caseId);

    return <DashboardClient initialData={graphData} caseId={params.caseId} />;
  } catch (error) {
    return <ErrorState error={error as Error} />;
  }
}

// CLIENT COMPONENT (DashboardClient.tsx)
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
```

### 2. KnowledgeGraph Component

Force-directed graph with custom node rendering, dynamic import, and pulsing animation:

```typescript
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
  const graphRef = useRef<any>();

  // PERFORMANCE: Memoize callback to prevent re-renders
  const handleNodeClick = useCallback(
    (node: any) => {
      onNodeClick(node as BaseNode);
    },
    [onNodeClick]
  );

  // PERFORMANCE: Memoize custom node renderer
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
        graphData={data}
        nodeColor={getNodeColor}
        nodeVal={getNodeSize}
        nodeLabel={(node: any) => `${node.name || node.id} (${node.entity_type})`}
        linkColor={() => '#475569'}
        backgroundColor="#020617"
        onNodeClick={handleNodeClick}
        nodeCanvasObjectMode={() => 'after'}
        nodeCanvasObject={nodeCanvasObject}
        warmupTicks={100}
        cooldownTicks={0}
      />
    </div>
  );
}
```

### 3. EntitySidebar Component

Tabbed interface with accessibility improvements:

```typescript
'use client';

import { useMemo } from 'react';
import type { BaseNode, GraphData } from '@/lib/types';
import { DossierPanel } from './DossierPanel';
import { NarrativePanel } from './NarrativePanel';
import { useNarrative } from '@/hooks/useNarrative';

type TabType = 'details' | 'narrative';

interface EntitySidebarProps {
  selectedNode: BaseNode | null;
  graphData: GraphData;
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  caseId: string;
}

export function EntitySidebar({
  selectedNode,
  graphData,
  activeTab,
  onTabChange,
  caseId,
}: EntitySidebarProps) {
  const { narrative, loading, error, generateNarrative } = useNarrative();
  const sessionId = useMemo(() => crypto.randomUUID(), []);

  const hasSelection = Boolean(selectedNode);

  const handleGenerateNarrative = () => {
    if (selectedNode) {
      onTabChange('narrative');
      generateNarrative(caseId, selectedNode.id, sessionId);
    }
  };

  return (
    <div className="w-[500px] border-l border-amber-500/20 flex flex-col bg-slate-900">
      {/* ACCESSIBILITY: Tab Headers with ARIA attributes */}
      <div role="tablist" className="border-b border-amber-500/20 flex">
        <button
          role="tab"
          aria-selected={activeTab === 'details'}
          aria-controls="details-panel"
          id="details-tab"
          onClick={() => onTabChange('details')}
          className={`flex-1 px-4 py-3 font-display text-sm uppercase tracking-wider transition-colors ${
            activeTab === 'details'
              ? 'bg-slate-800 text-amber-400 border-b-2 border-amber-400'
              : 'text-slate-400 hover:text-slate-300'
          }`}
        >
          Details
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'narrative'}
          aria-controls="narrative-panel"
          id="narrative-tab"
          onClick={() => hasSelection && onTabChange('narrative')}
          disabled={!hasSelection}
          className={`flex-1 px-4 py-3 font-display text-sm uppercase tracking-wider transition-colors ${
            activeTab === 'narrative'
              ? 'bg-slate-800 text-amber-400 border-b-2 border-amber-400'
              : hasSelection
              ? 'text-slate-400 hover:text-slate-300'
              : 'text-slate-600 cursor-not-allowed'
          }`}
        >
          Narrative
        </button>
      </div>

      {/* ACCESSIBILITY: Tab Panels with ARIA attributes */}
      <div className="flex-1 overflow-y-auto">
        <div
          role="tabpanel"
          id="details-panel"
          aria-labelledby="details-tab"
          hidden={activeTab !== 'details'}
        >
          {activeTab === 'details' && (
            <DossierPanel
              node={selectedNode}
              graphData={graphData}
              onGenerateNarrative={handleGenerateNarrative}
            />
          )}
        </div>
        <div
          role="tabpanel"
          id="narrative-panel"
          aria-labelledby="narrative-tab"
          hidden={activeTab !== 'narrative'}
        >
          {activeTab === 'narrative' && (
            <NarrativePanel
              narrative={narrative}
              loading={loading}
              error={error?.message || null}
            />
          )}
        </div>
      </div>
    </div>
  );
}
```

### 4. DossierPanel Component

Entity details with forensic intelligence styling:

```typescript
import { useMemo } from 'react';
import type { BaseNode, GraphData } from '@/lib/types';
import { NodeBadge } from './NodeBadge';

interface DossierPanelProps {
  node: BaseNode | null;
  graphData: GraphData;
  onGenerateNarrative: () => void;
}

// PERFORMANCE: Hoist static JSX outside component
const EMPTY_STATE = (
  <div className="p-6 text-center text-slate-500 font-mono text-sm">
    <div className="mb-2 text-slate-600">◇</div>
    Click a node to view details
  </div>
);

export function DossierPanel({
  node,
  graphData,
  onGenerateNarrative,
}: DossierPanelProps) {
  // PERFORMANCE: Memoize expensive filter operation
  const relatedLinks = useMemo(
    () => graphData.links.filter(
      (l) => l.source === node?.id || l.target === node?.id
    ),
    [graphData.links, node?.id]
  );

  // PERFORMANCE: Memoize string split operation
  const sourceDocIds = useMemo(
    () => node?.extracted_from?.split(/\s*,\s*/) || [],
    [node?.extracted_from]
  );

  if (!node) return EMPTY_STATE;

  return (
    <div className="p-4 space-y-4">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-start justify-between">
          <h2 className="text-xl font-display uppercase tracking-wide">
            {node.name || node.id}
          </h2>
          <NodeBadge tier={node.verification.tier} />
        </div>
        <p className="text-xs text-slate-400 font-mono uppercase tracking-wider">
          {node.entity_type} • {node.id}
        </p>
      </div>

      {/* Generate Narrative Button */}
      <button
        onClick={onGenerateNarrative}
        className="w-full min-h-[44px] px-4 py-2 bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-600 rounded font-display text-sm uppercase tracking-wider transition-all shadow-lg hover:shadow-amber-500/50"
        aria-label="Generate narrative for this entity"
      >
        📖 Generate Intelligence Briefing
      </button>

      {/* Verification Info */}
      <section className="bg-slate-800 border border-slate-700 rounded p-3 space-y-2">
        <h3 className="text-xs font-display uppercase tracking-wider text-slate-300">
          Verification Status
        </h3>
        <p className="text-sm text-slate-300">
          Confidence:{' '}
          <span className="font-mono text-amber-400">
            {(node.verification.confidence * 100).toFixed(0)}%
          </span>
        </p>
        {node.verification.tier === 'TIER_3_AI' && (
          <div className="mt-2 p-2 bg-amber-950/50 border border-amber-700/50 rounded">
            <p className="text-xs text-amber-400 font-mono">
              ⚠️ UNVERIFIED: AI-extracted data. Requires analyst review.
            </p>
          </div>
        )}
      </section>

      {/* Related Entities */}
      {relatedLinks.length > 0 && (
        <section className="bg-slate-800 border border-slate-700 rounded p-3">
          <h3 className="text-xs font-display uppercase tracking-wider text-slate-300 mb-2">
            Related Entities ({relatedLinks.length})
          </h3>
          <ul className="space-y-1 text-sm">
            {relatedLinks.slice(0, 5).map((link, idx) => {
              const otherId = link.source === node.id ? link.target : link.source;
              const otherNode = graphData.nodes.find((n) => n.id === otherId);
              return (
                <li key={idx} className="text-slate-300">
                  <span className="font-mono text-xs text-amber-500">
                    {link.relation_type}
                  </span>
                  {' → '}
                  <span className="font-body">{otherNode?.name || otherId}</span>
                </li>
              );
            })}
            {relatedLinks.length > 5 && (
              <li className="text-slate-500 italic text-xs font-mono">
                +{relatedLinks.length - 5} more relations
              </li>
            )}
          </ul>
        </section>
      )}

      {/* Source Documents */}
      {sourceDocIds.length > 0 && (
        <section className="bg-slate-800 border border-slate-700 rounded p-3">
          <h3 className="text-xs font-display uppercase tracking-wider text-slate-300 mb-2">
            Source Documents ({sourceDocIds.length})
          </h3>
          <ul className="space-y-1 text-xs font-mono">
            {sourceDocIds.slice(0, 5).map((docId, idx) => (
              <li key={idx} className="text-slate-400">
                📄 {docId}
              </li>
            ))}
            {sourceDocIds.length > 5 && (
              <li className="text-slate-500 italic">
                +{sourceDocIds.length - 5} more sources
              </li>
            )}
          </ul>
        </section>
      )}
    </div>
  );
}
```

### 5. NarrativePanel Integration

Enhanced with typewriter animation and accessibility:

```typescript
'use client';

import { useState, useEffect } from 'react';
import type { NarrativeResult } from '@/lib/types';

interface NarrativePanelProps {
  narrative: NarrativeResult | null;
  loading: boolean;
  error: string | null;
}

export function NarrativePanel({
  narrative,
  loading,
  error,
}: NarrativePanelProps) {
  const [expandedCitations, setExpandedCitations] = useState<Set<number>>(new Set());
  const [displayedText, setDisplayedText] = useState('');

  // Typewriter effect for narrative generation
  useEffect(() => {
    if (!narrative?.main_narrative) {
      setDisplayedText('');
      return;
    }

    let index = 0;
    const text = narrative.main_narrative;
    const interval = setInterval(() => {
      if (index < text.length) {
        setDisplayedText(text.slice(0, index + 1));
        index++;
      } else {
        clearInterval(interval);
      }
    }, 20); // Typewriter speed

    return () => clearInterval(interval);
  }, [narrative?.main_narrative]);

  const toggleCitation = (citationNum: number) => {
    setExpandedCitations((prev) => {
      const next = new Set(prev);
      if (next.has(citationNum)) {
        next.delete(citationNum);
      } else {
        next.add(citationNum);
      }
      return next;
    });
  };

  const getVerificationColor = (tier: string): string => {
    const colors: Record<string, string> = {
      TIER_1_CERTIFIED: 'text-tier-1',
      TIER_2_INSTITUTIONAL: 'text-tier-2-inst',
      TIER_2_ANALYST: 'text-tier-2',
      TIER_3_AI: 'text-tier-3',
    };
    return colors[tier] || 'text-tier-3';
  };

  const getEventIcon = (eventType: string): string => {
    const icons: Record<string, string> = {
      CONFISCATED: '🚨',
      SOLD: '💰',
      INHERITED: '📜',
    };
    return icons[eventType] || '📋';
  };

  const renderNarrative = (text: string) => {
    const paragraphs = text.split('\n\n').filter((p) => p.trim());
    return paragraphs.map((paragraph, idx) => (
      <p key={idx} className="mb-4 text-slate-200 leading-relaxed font-body">
        {paragraph}
      </p>
    ));
  };

  // ACCESSIBILITY: Loading state with aria-live
  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div
          className="text-center"
          role="status"
          aria-live="polite"
          aria-label="Generating narrative"
        >
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500 mx-auto mb-4" />
          <p className="text-slate-400 font-mono text-sm">
            Analyzing evidence constellation...
          </p>
        </div>
      </div>
    );
  }

  // ACCESSIBILITY: Error state with role="alert"
  if (error) {
    return (
      <div className="p-6">
        <div
          className="bg-red-950/50 border border-red-500 rounded p-4"
          role="alert"
          aria-live="assertive"
        >
          <h3 className="text-red-400 font-display text-sm uppercase tracking-wider mb-2">
            Generation Failed
          </h3>
          <p className="text-slate-300 font-mono text-xs">{error}</p>
        </div>
      </div>
    );
  }

  if (!narrative) {
    return (
      <div className="p-6 text-center text-slate-500 font-mono text-sm">
        <div className="mb-2 text-slate-600">◇</div>
        Click "Generate Intelligence Briefing" to begin
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4 overflow-y-auto">
      {/* Header */}
      <div className="border-b border-amber-500/20 pb-3">
        <h2 className="text-xl font-display uppercase tracking-wide text-amber-100">
          {narrative.focal_entity_name}
        </h2>
        <p className="text-xs text-slate-400 font-mono uppercase tracking-wider mt-1">
          {narrative.focal_entity_type} • Intelligence Briefing
        </p>
      </div>

      {/* Metadata Tags */}
      <div className="flex gap-2 flex-wrap text-xs font-mono">
        <span className="px-2 py-1 bg-slate-800 border border-slate-700 rounded">
          {narrative.constellation_size} entities
        </span>
        <span className="px-2 py-1 bg-slate-800 border border-slate-700 rounded">
          {narrative.total_documents} documents
        </span>
        <span className="px-2 py-1 bg-slate-800 border border-slate-700 rounded">
          {narrative.model_used}
        </span>
        {narrative.from_cache && (
          <span className="px-2 py-1 bg-emerald-900/50 border border-emerald-600 text-emerald-300 rounded">
            ✓ cached
          </span>
        )}
      </div>

      {/* Highlighted Events */}
      {narrative.highlighted_events.length > 0 && (
        <section>
          <h3 className="text-xs font-display uppercase tracking-wider text-slate-300 mb-2">
            Critical Events
          </h3>
          <div className="space-y-2">
            {narrative.highlighted_events.map((event, idx) => (
              <div
                key={idx}
                className="bg-slate-800 border border-amber-600/50 rounded p-3 border-l-4"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span>{getEventIcon(event.event_type)}</span>
                  <span className="font-display text-xs uppercase tracking-wider text-amber-400">
                    {event.event_type}
                  </span>
                  {event.date && (
                    <span className="text-xs text-slate-400 font-mono">{event.date}</span>
                  )}
                </div>
                <p className="text-sm text-slate-300 font-body">{event.summary}</p>
                {event.parties_involved.length > 0 && (
                  <p className="text-xs text-slate-400 mt-1 font-mono">
                    Parties: {event.parties_involved.join(', ')}
                  </p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Main Narrative with Typewriter Effect */}
      <section>
        <h3 className="text-xs font-display uppercase tracking-wider text-slate-300 mb-2">
          Intelligence Summary
        </h3>
        <div className="text-sm font-body">{renderNarrative(displayedText)}</div>
      </section>

      {/* Evidence Citations (rest of component remains similar but with updated styling) */}
      {narrative.facts.length > 0 && (
        <section>
          <h3 className="text-xs font-display uppercase tracking-wider text-slate-300 mb-2">
            Supporting Evidence ({narrative.total_citations})
          </h3>
          {/* ... citation rendering code ... */}
        </section>
      )}

      {/* Footer Disclaimer */}
      <div className="border-t border-amber-500/20 pt-4 space-y-2">
        <p className="text-xs text-amber-400 font-mono leading-relaxed">
          <strong className="text-amber-500">⚠️ FORENSIC INTELLIGENCE ONLY:</strong>{' '}
          This analysis synthesizes documentary evidence and does not constitute legal
          advice or proof of ownership.
        </p>
        <p className="text-xs text-slate-500 font-mono">
          Generation cost: ${narrative.generation_cost.toFixed(4)}
          {narrative.session_total_cost !== undefined && (
            <> | Session total: ${narrative.session_total_cost.toFixed(4)}</>
          )}
        </p>
      </div>
    </div>
  );
}
```

### 6. Header Component (Redesigned)

Classified briefing room aesthetic:

```typescript
import type { GraphData } from '@/lib/types';

interface HeaderProps {
  graphData: GraphData;
  caseId: string;
}

export function Header({ graphData, caseId }: HeaderProps) {
  const { metadata } = graphData;

  return (
    <header className="border-b-2 border-amber-500/20 bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Case ID with Active Indicator */}
        <div>
          <h1 className="text-3xl font-display tracking-wider text-amber-100 flex items-center gap-2">
            {caseId}
            <span className="text-red-500 text-xl animate-pulse" aria-label="Active case">
              ●
            </span>
          </h1>
          <p className="text-xs text-amber-500/70 uppercase tracking-widest font-mono mt-1">
            [ Forensic Intelligence • Tier System Active ]
          </p>
        </div>

        {/* Evidence Counters - Stamp Style */}
        <div className="flex gap-6">
          {[
            { label: 'Entities', count: metadata.entity_count, icon: '👤' },
            { label: 'Relations', count: metadata.relation_count, icon: '🔗' },
            { label: 'Documents', count: metadata.document_count, icon: '📄' },
          ].map(({ label, count, icon }) => (
            <div key={label} className="relative">
              {/* Glow effect */}
              <div className="absolute -inset-1 bg-amber-500/10 blur rounded-lg" />
              {/* Counter card */}
              <div className="relative bg-slate-900 border border-amber-500/30 px-4 py-2 rounded">
                <div className="text-2xl font-mono font-bold text-amber-400">
                  <span className="mr-1">{icon}</span>
                  {count}
                </div>
                <div className="text-[10px] text-amber-600 uppercase tracking-wider font-display">
                  {label}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </header>
  );
}
```

### 7. NodeBadge Component (Evidence Stamps)

Redesigned as evidence classification stamps:

```typescript
import type { VerificationTier } from '@/lib/types';

interface NodeBadgeProps {
  tier: VerificationTier;
  className?: string;
}

export function NodeBadge({ tier, className = '' }: NodeBadgeProps) {
  const styles = {
    TIER_1_CERTIFIED: {
      bg: 'bg-blue-950',
      border: 'border-blue-400',
      text: 'text-blue-300',
      stamp: '✓ CERTIFIED',
      rotate: '-rotate-2',
    },
    TIER_2_INSTITUTIONAL: {
      bg: 'bg-amber-950',
      border: 'border-amber-600',
      text: 'text-amber-400',
      stamp: '⚠ INSTITUTIONAL',
      rotate: 'rotate-1',
    },
    TIER_2_ANALYST: {
      bg: 'bg-amber-950',
      border: 'border-amber-500',
      text: 'text-amber-300',
      stamp: '✓ ANALYST',
      rotate: '-rotate-1',
    },
    TIER_3_AI: {
      bg: 'bg-gray-950',
      border: 'border-gray-600',
      text: 'text-gray-400',
      stamp: '⚠ UNVERIFIED',
      rotate: 'rotate-2',
    },
  };

  const style = styles[tier];

  return (
    <div className={`relative ${className}`}>
      {/* Evidence stamp effect */}
      <div
        className={`
          inline-block px-3 py-1.5
          ${style.bg} ${style.text}
          border-2 ${style.border} ${style.rotate}
          font-mono text-[10px] font-black uppercase tracking-wider
          shadow-lg
        `}
        role="status"
        aria-label={`Verification tier: ${tier}`}
      >
        {style.stamp}
      </div>
    </div>
  );
}
```

---

## API Routes

### Graph Data Route (app/api/cases/[caseId]/graph/route.ts)

PERFORMANCE: Uses React.cache() for per-request deduplication:

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { cache } from 'react';
import { readFile } from 'fs/promises';
import { join } from 'path';
import type { GraphData } from '@/lib/types';

// PERFORMANCE: React.cache() ensures getGraphData is called only once per request
// even if multiple components need it (eliminates waterfalls)
export const getGraphData = cache(async (caseId: string): Promise<GraphData> => {
  // Validate caseId format
  if (!/^[A-Z0-9-]+$/.test(caseId)) {
    throw new Error('Invalid case ID format');
  }

  // Read from Factory output (air gap maintained)
  const graphPath = join(
    process.cwd(),
    '..',
    'cases',
    caseId,
    'output',
    'graph_data.json'
  );

  const graphData = await readFile(graphPath, 'utf-8');
  return JSON.parse(graphData);
});

export async function GET(
  request: NextRequest,
  { params }: { params: { caseId: string } }
) {
  try {
    const data = await getGraphData(params.caseId);
    return NextResponse.json(data);
  } catch (error: any) {
    if (error.code === 'ENOENT') {
      return NextResponse.json(
        { error: 'Case not found' },
        { status: 404 }
      );
    }

    console.error('Graph load error:', error);
    return NextResponse.json(
      { error: error.message || 'Failed to load graph data' },
      { status: 500 }
    );
  }
}
```

**Usage in Server Components:**

```typescript
// lib/graph-api.ts
export { getGraphData } from '@/app/api/cases/[caseId]/graph/route';

// app/case/[caseId]/page.tsx
import { getGraphData } from '@/lib/graph-api';

export default async function CaseDashboard({ params }) {
  const graphData = await getGraphData(params.caseId);
  return <DashboardClient initialData={graphData} caseId={params.caseId} />;
}
```

Note: this assumes the Next.js app runs from `farmer_vault/` and the repo root is one level up. If colocated at repo root, drop the `..` segment.

### Narrative Route (app/api/cases/[caseId]/narrative/route.ts)

Spawn the existing Python script (`farmer_factory/scripts/generate_narrative.py`) and return its JSON output. The script requires `session_id`, so the route must validate request body and pass that through.

Behavior:
- On success: `200` with narrative JSON.
- On error: parse JSON from stderr (script error payload) and map `type` to HTTP status:
  - `cost_limit` → 402
  - `insufficient_data` → 422
  - `unknown` → 500

Pseudo-code (App Router):

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';

const STATUS_BY_TYPE: Record<string, number> = {
  cost_limit: 402,
  insufficient_data: 422,
  unknown: 500
};

export async function POST(
  request: NextRequest,
  { params }: { params: { caseId: string } }
) {
  const { caseId } = params;
  const { clicked_node_id, session_id, max_cost } = await request.json();

  if (!clicked_node_id || !session_id) {
    return NextResponse.json(
      { error: 'Missing clicked_node_id or session_id' },
      { status: 400 }
    );
  }

  return new Promise((resolve) => {
    const proc = spawn('python3', [
      'farmer_factory/scripts/generate_narrative.py',
      '--case-id', caseId,
      '--node-id', clicked_node_id,
      '--session-id', session_id,
      '--max-cost', String(max_cost ?? 1.0),
      '--json'
    ]);

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
    proc.stderr.on('data', (chunk) => { stderr += chunk.toString(); });

    proc.on('close', () => {
      if (stderr) {
        const payload = safeJson(stderr) ?? { error: stderr, type: 'unknown' };
        const status = STATUS_BY_TYPE[payload.type] ?? 500;
        resolve(NextResponse.json(payload, { status }));
        return;
      }
      const payload = safeJson(stdout) ?? { error: 'Invalid narrative response', type: 'unknown' };
      resolve(NextResponse.json(payload, { status: 200 }));
    });
  });
}

function safeJson(data: string) {
  try {
    return JSON.parse(data);
  } catch {
    return null;
  }
}
```

---

## Styling & Theme

### Forensic Intelligence Aesthetic

**Design Concept:** "Intelligence Briefing Room" - classified documents, evidence boards, investigative journalism. This is forensic intelligence, not a SaaS dashboard.

**Key Visual Elements:**
- Typewriter/classified document typography
- Evidence stamp verification badges
- Pulsing amber alerts and highlights
- Subtle grid overlay (war room atmosphere)
- Redacted text reveals for unverified data
- Typewriter animation for narrative generation

### Dark Theme (globals.css)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* Typography - Forensic Intelligence Style */
    --font-display: 'IBM Plex Mono', 'Courier Prime', monospace;
    --font-body: 'Source Serif 4', 'Crimson Pro', Georgia, serif;
    --font-mono: 'Fira Code', 'JetBrains Mono', monospace;
    --font-ui: 'Inter Tight', 'DM Sans', sans-serif;
  }

  body {
    @apply bg-slate-950 text-slate-100;
    font-family: var(--font-body);
    /* War room grid overlay */
    background-image: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 1px,
      rgba(255,255,255,0.02) 1px,
      rgba(255,255,255,0.02) 2px
    );
  }

  h1, h2, h3, h4, h5, h6 {
    font-family: var(--font-display);
    letter-spacing: 0.02em;
    text-transform: uppercase;
  }

  code, .font-mono, pre {
    font-family: var(--font-mono);
  }

  /* Accessibility - Focus indicators */
  *:focus-visible {
    @apply outline-2 outline-offset-2 outline-amber-400 ring-0;
  }
}

@layer components {
  .evidence-stamp {
    @apply inline-block px-3 py-1.5 border-2 font-mono text-[10px] font-black uppercase tracking-wider shadow-lg;
  }

  .redacted {
    @apply bg-slate-800 text-transparent select-none;
    background-image: repeating-linear-gradient(
      90deg,
      #000 0px,
      #000 2px,
      transparent 2px,
      transparent 4px
    );
  }
}
```

### Tailwind Config (tailwind.config.ts)

```typescript
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['var(--font-display)'],
        body: ['var(--font-body)'],
        mono: ['var(--font-mono)'],
        ui: ['var(--font-ui)'],
      },
      colors: {
        // Verification tier colors
        'tier-1': '#3B82F6',      // Blue - TIER_1_CERTIFIED
        'tier-2': '#F59E0B',      // Amber - TIER_2_ANALYST
        'tier-2-inst': '#D97706',  // Dark Amber - TIER_2_INSTITUTIONAL
        'tier-3': '#6B7280',      // Gray - TIER_3_AI
      },
      animation: {
        'flicker': 'flicker 3s linear infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'typewriter': 'typewriter 2s steps(40) forwards',
      },
      keyframes: {
        flicker: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.95' },
        },
        typewriter: {
          '0%': { width: '0' },
          '100%': { width: '100%' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
```

### Color Scheme - Intelligence Briefing Room

```
Backgrounds (Darker, More Atmospheric):
  Primary:   #020617 (slate-950) - Deep navy-black with grid overlay
  Secondary: #0F172A (slate-900) - Layered panels
  Tertiary:  #1E293B (slate-800) - Card backgrounds
  Elevated:  #334155 (slate-700) - Hover states

Text (High Contrast):
  Primary:   #F1F5F9 (slate-100) - Main text
  Secondary: #CBD5E1 (slate-300) - Body text (improved contrast)
  Muted:     #94A3B8 (slate-400) - Labels
  Dimmed:    #64748B (slate-500) - Timestamps

Accent Colors (Warning System):
  Primary:   #FBBF24 (amber-400) - Alerts, highlights
  Critical:  #DC2626 (red-600) - Errors, critical items
  Info:      #60A5FA (blue-400) - Links, informational
  Success:   #10B981 (emerald-500) - Confirmed data

Verification Tiers (Evidence Classification):
  TIER_1_CERTIFIED:     #3B82F6 (blue-500) + stamp effect
  TIER_2_INSTITUTIONAL: #D97706 (amber-600) + stamp effect
  TIER_2_ANALYST:       #F59E0B (amber-500) + stamp effect
  TIER_3_AI:            #6B7280 (gray-500) + warning indicator

Entity Types:
  PERSON:       #6366F1 (indigo-500)
  PROPERTY:     #10B981 (emerald-500)
  DOCUMENT:     #F59E0B (amber-500)
  ORGANIZATION: #8B5CF6 (violet-500)
  LOCATION:     #84CC16 (lime-500)
```

---

## Error Handling

### Loading States

```typescript
// useGraph hook
const useGraph = (caseId: string) => {
  const [data, setData] = useState<GraphData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    setIsLoading(true);
    fetch(`/api/cases/${caseId}/graph`)
      .then(res => {
        if (!res.ok) {
          throw new Error(`Failed to load case: ${res.status}`);
        }
        return res.json();
      })
      .then(setData)
      .catch(setError)
      .finally(() => setIsLoading(false));
  }, [caseId]);

  return { data, isLoading, error };
};
```

### Error Display

```typescript
const ErrorState = ({ error }: { error: Error }) => (
  <div className="h-screen flex items-center justify-center bg-slate-900">
    <div className="text-center max-w-md">
      <h1 className="text-2xl font-bold text-red-400 mb-2">
        Error Loading Case
      </h1>
      <p className="text-slate-400 mb-4">{error.message}</p>
      <button
        onClick={() => window.location.reload()}
        className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded"
      >
        Retry
      </button>
    </div>
  </div>
);

const LoadingState = () => (
  <div className="h-screen flex items-center justify-center bg-slate-900">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4" />
      <p className="text-slate-400">Loading graph data...</p>
    </div>
  </div>
);
```

---

## Implementation Steps

### Phase 1: Project Setup
1. Backup existing `farmer_vault` → `farmer_vault_backup`
2. Run `npx create-next-app@latest farmer_vault --typescript --tailwind --app`
3. Install dependencies: `react-force-graph-2d`
4. Configure Tailwind with dark theme
5. Set up project structure (components/, hooks/, lib/)

### Phase 2: API Routes
6. Create `/api/cases/[caseId]/graph` route (read from Factory, validate `caseId`)
7. Implement `/api/cases/[caseId]/narrative` to call `generate_narrative.py`
8. Test both routes with TEST-CERESA case

### Phase 3: Core Components
9. Build `types.ts` from `farmer_factory/structure/SCHEMA.md` (GraphData uses `metadata`, `nodes`, `links`)
10. Create `useGraph` hook
11. Build `KnowledgeGraph` component with react-force-graph-2d
12. Create `Header` component
13. Build dashboard layout

Minimal `types.ts` scaffold:

```typescript
export type VerificationTier =
  | 'TIER_3_AI'
  | 'TIER_2_ANALYST'
  | 'TIER_2_INSTITUTIONAL'
  | 'TIER_1_CERTIFIED';

export interface Verification {
  tier: VerificationTier;
  confidence: number;
  verified_by?: string | null;
  verified_at?: string | null;
  notes?: string | null;
}

export type EntityType =
  | 'PERSON'
  | 'PROPERTY'
  | 'ORGANIZATION'
  | 'LOCATION'
  | 'DOCUMENT';

export interface BaseNode {
  id: string;
  entity_type: EntityType;
  name?: string;
  verification: Verification;
  extracted_from: string;
  created_at?: string;
  updated_at?: string;
  notes?: string | null;
  [key: string]: unknown;
}

export interface Link {
  relation_id?: string;
  source: string;
  target: string;
  relation_type: string;
  verification: Verification;
  date?: string | null;
  amount?: number | null;
  currency?: string | null;
  property_id?: string | null;
  document_id?: string | null;
  evidence?: string | null;
  notes?: string | null;
}

export interface GraphMetadata {
  case_id: string;
  created_at: string;
  updated_at: string;
  factory_version: string;
  entity_count: number;
  relation_count: number;
  document_count: number;
  verification_distribution?: Record<string, number>;
  entity_type_summary?: Record<string, number>;
  date_range?: {
    earliest_document?: string | null;
    latest_document?: string | null;
    earliest_event?: string | null;
    latest_event?: string | null;
  };
}

export interface GraphData {
  metadata: GraphMetadata;
  nodes: BaseNode[];
  links: Link[];
}
```

### Phase 4: Sidebar & Details
14. Create `EntitySidebar` with tabs
15. Build `DossierPanel` component
16. Create `NodeBadge` component
17. Wire up node selection flow

### Phase 5: Narrative Integration
18. Migrate existing `NarrativePanel.tsx` into new structure
19. Adapt for tab context (auto-generate on tab open)
20. Test narrative generation end-to-end

### Phase 6: Polish
21. Add loading states
22. Add error handling
23. Improve responsive behavior
24. Final styling pass

---

## Testing Checklist

### Functionality
- [ ] Graph loads from `/api/cases/TEST-CERESA/graph`
- [ ] Nodes render with correct colors (verification tiers)
- [ ] Node click selects entity, shows Details tab
- [ ] DossierPanel displays entity info correctly
- [ ] "Generate Narrative" button switches to Narrative tab
- [ ] Narrative generates with inline citations and session cost tracking
- [ ] Session cost tracking works
- [ ] Error states display correctly (case not found, etc.)

### Visual
- [ ] Dark theme throughout (slate-900 background)
- [ ] Monospace fonts on data fields
- [ ] Verification tier badges color-coded
- [ ] Selected node has glow effect
- [ ] Tabs highlight active state
- [ ] Responsive layout (graph resizes, sidebar fixed)

### Performance
- [ ] Graph renders smoothly with 300+ nodes
- [ ] No lag when clicking nodes
- [ ] Narrative generation shows loading state
- [ ] No console errors

---

## Acceptance Criteria

**MVP Demo Complete When:**
1. ✅ Next.js app runs on localhost
2. ✅ TEST-CERESA graph visualizes with force-directed layout
3. ✅ Click node → Details tab shows entity info
4. ✅ Click "Generate Narrative" → Narrative tab shows contextual story
5. ✅ Inline citations [①], [②] display correctly
6. ✅ Highlighted events (CONFISCATED, SOLD, INHERITED) show
7. ✅ Dark theme matches design system
8. ✅ No authentication required (local dev only)

---

## Future Enhancements (Post-MVP)

**Phase 8B: Authentication & Database**
- Clerk OAuth integration
- Supabase database with RLS
- Graph fetched from Supabase Storage
- User-based case access control

**Phase 8C: Advanced Features**
- Graph filter tabs (Overview, Families, Properties, Timeline, Legal)
- Source document viewer with OCR text
- Timeline view with chronological events
- Analyst verification workflow (TIER_3_AI → TIER_2_ANALYST promotion)

**Phase 8D: Observability**
- PostHog analytics
- Sentry error tracking
- Audit logging

---

## Migration Path

When ready to add auth/database:

1. **API Routes:** Swap file read for Supabase fetch
   ```typescript
   // Before: readFile(graphPath)
   // After:  supabase.storage.from('case-graphs').download(path)
   ```

2. **Dashboard:** Add auth check
   ```typescript
   // Wrap with Clerk auth
   <SignedIn>
     <CaseDashboard />
   </SignedIn>
   ```

3. **No frontend changes needed** - API contract stays the same

---

*This design establishes the foundation for the Vault frontend. Authentication and database integration will build on this structure without requiring major refactoring.*
