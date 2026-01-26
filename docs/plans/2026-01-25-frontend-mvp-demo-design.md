# Frontend MVP Demo - Design Document

> **Document Classification:** Implementation Design
> **Version:** 1.0.0
> **Created:** 2026-01-25
> **Status:** Approved for Implementation

---

## Overview

Build a working Next.js 14 demo frontend to visualize the TEST-CERESA knowledge graph with integrated narrative generation. Focus: graph-centric interface with contextual narratives, no authentication/database (local development only).

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
3. **User clicks "Generate Narrative"** → switches to Narrative tab → `POST /api/cases/TEST-CERESA/narrative`
4. **Narrative displays** with inline citations and highlighted events

### Technology Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS (dark theme)
- **Graph:** react-force-graph-2d
- **State:** React hooks (no external state management)

---

## Component Design

### 1. Dashboard Layout (app/case/[caseId]/page.tsx)

Two-column responsive layout:

```typescript
const CaseDashboard = ({ params }: { params: { caseId: string } }) => {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'details' | 'narrative'>('details');
  const { data: graphData, isLoading, error } = useGraph(params.caseId);

  if (error) return <ErrorState error={error} />;
  if (isLoading) return <LoadingState />;

  return (
    <div className="h-screen flex flex-col bg-slate-900">
      <Header graphData={graphData} caseId={params.caseId} />

      <div className="flex-1 flex overflow-hidden">
        {/* Left: Graph (flexible width) */}
        <div className="flex-1">
          <KnowledgeGraph
            data={graphData}
            selectedNodeId={selectedNodeId}
            onNodeClick={(node) => {
              setSelectedNodeId(node.id);
              setActiveTab('details'); // Reset to details
            }}
          />
        </div>

        {/* Right: Tabbed Sidebar (500px fixed) */}
        <EntitySidebar
          selectedNode={graphData.nodes.find(n => n.id === selectedNodeId)}
          graphData={graphData}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          caseId={params.caseId}
        />
      </div>
    </div>
  );
};
```

### 2. KnowledgeGraph Component

Force-directed graph with custom node rendering:

```typescript
interface KnowledgeGraphProps {
  data: GraphData;
  selectedNodeId: string | null;
  onNodeClick: (node: Node) => void;
}

const KnowledgeGraph = ({ data, selectedNodeId, onNodeClick }: KnowledgeGraphProps) => {
  const graphRef = useRef();

  const getNodeColor = (node: Node): string => ({
    'TIER_3_AI': '#6B7280',         // Gray
    'TIER_2_ANALYST': '#F59E0B',    // Amber
    'TIER_2_INSTITUTIONAL': '#D97706', // Dark amber
    'TIER_1_CERTIFIED': '#3B82F6',  // Blue
  }[node.verification.tier]);

  const getNodeSize = (node: Node): number => ({
    'PROPERTY': 8,
    'PERSON': 6,
    'ORGANIZATION': 6,
    'DOCUMENT': 4,
    'LOCATION': 5,
  }[node.entity_type] || 5);

  return (
    <ForceGraph2D
      ref={graphRef}
      graphData={data}
      nodeColor={getNodeColor}
      nodeRelSize={getNodeSize}
      nodeLabel={node => `${node.name} (${node.entity_type})`}
      linkColor={() => '#475569'}
      backgroundColor="#0F172A"
      onNodeClick={onNodeClick}
      nodeCanvasObjectMode={() => 'after'}
      nodeCanvasObject={(node, ctx) => {
        if (node.id === selectedNodeId) {
          // Glow effect
          ctx.beginPath();
          ctx.arc(node.x, node.y, getNodeSize(node) + 3, 0, 2 * Math.PI);
          ctx.fillStyle = `${getNodeColor(node)}40`;
          ctx.fill();
        }
      }}
    />
  );
};
```

### 3. EntitySidebar Component

Tabbed interface switching between Details and Narrative:

```typescript
interface EntitySidebarProps {
  selectedNode: Node | null;
  graphData: GraphData;
  activeTab: 'details' | 'narrative';
  onTabChange: (tab: 'details' | 'narrative') => void;
  caseId: string;
}

const EntitySidebar = ({
  selectedNode,
  graphData,
  activeTab,
  onTabChange,
  caseId
}: EntitySidebarProps) => {
  return (
    <div className="w-[500px] border-l border-slate-800 flex flex-col">
      {/* Tab Headers */}
      <div className="border-b border-slate-800 flex">
        <TabButton
          active={activeTab === 'details'}
          onClick={() => onTabChange('details')}
        >
          Details
        </TabButton>
        <TabButton
          active={activeTab === 'narrative'}
          onClick={() => onTabChange('narrative')}
        >
          Narrative
        </TabButton>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'details' ? (
          <DossierPanel
            node={selectedNode}
            graphData={graphData}
            onGenerateNarrative={() => onTabChange('narrative')}
          />
        ) : (
          <NarrativePanel
            caseId={caseId}
            nodeId={selectedNode?.id}
          />
        )}
      </div>
    </div>
  );
};
```

### 4. DossierPanel Component

Entity details with narrative generation trigger:

```typescript
const DossierPanel = ({
  node,
  graphData,
  onGenerateNarrative
}: DossierPanelProps) => {
  if (!node) {
    return (
      <div className="p-6 text-center text-slate-500">
        Click a node to view details
      </div>
    );
  }

  const relatedLinks = graphData.links.filter(
    l => l.source === node.id || l.target === node.id
  );

  const sourceDocIds = node.extracted_from?.split(',').map(s => s.trim()) || [];

  return (
    <div className="p-4 space-y-4">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-start justify-between">
          <h2 className="text-xl font-semibold">{node.name}</h2>
          <NodeBadge tier={node.verification.tier} />
        </div>
        <p className="text-sm text-slate-400 font-mono">
          {node.entity_type} • {node.id}
        </p>
      </div>

      {/* Generate Narrative Button */}
      <button
        onClick={onGenerateNarrative}
        className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded font-medium transition-colors"
      >
        📖 Generate Narrative
      </button>

      {/* Verification Info */}
      <section className="bg-slate-800 rounded p-3 space-y-2">
        <h3 className="text-sm font-semibold">Verification</h3>
        <p className="text-sm text-slate-400">
          Confidence: <span className="font-mono">{(node.verification.confidence * 100).toFixed(0)}%</span>
        </p>
        {node.verification.tier === 'TIER_3_AI' && (
          <p className="text-xs text-amber-400 mt-2">
            ⚠️ AI-extracted. Not verified by analyst.
          </p>
        )}
      </section>

      {/* Entity-specific Details */}
      <EntityDetails node={node} />

      {/* Related Entities */}
      {relatedLinks.length > 0 && (
        <section className="bg-slate-800 rounded p-3">
          <h3 className="text-sm font-semibold mb-2">
            Related Entities ({relatedLinks.length})
          </h3>
          <RelationsList links={relatedLinks} graphData={graphData} />
        </section>
      )}

      {/* Source Documents */}
      {sourceDocIds.length > 0 && (
        <section className="bg-slate-800 rounded p-3">
          <h3 className="text-sm font-semibold mb-2">
            Sources ({sourceDocIds.length})
          </h3>
          <SourceList docIds={sourceDocIds} />
        </section>
      )}
    </div>
  );
};
```

### 5. NarrativePanel Integration

Adapt existing component for tab context:

```typescript
const NarrativePanel = ({ caseId, nodeId }: NarrativePanelProps) => {
  const { narrative, loading, error, generateNarrative } = useNarrative();

  // Auto-generate when tab opened with selected node
  useEffect(() => {
    if (nodeId && !narrative) {
      generateNarrative(caseId, nodeId);
    }
  }, [nodeId]);

  // Reuse existing NarrativePanel component
  return (
    <NarrativePanelComponent
      narrative={narrative}
      loading={loading}
      error={error ? { type: 'unknown', message: error } : null}
      onClose={() => {/* no-op in tab context */}}
    />
  );
};
```

---

## API Routes

### Graph Data Route (app/api/cases/[caseId]/graph/route.ts)

Reads graph from Factory output directory:

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { readFile } from 'fs/promises';
import { join } from 'path';

export async function GET(
  request: NextRequest,
  { params }: { params: { caseId: string } }
) {
  try {
    const { caseId } = params;

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
    const parsed = JSON.parse(graphData);

    return NextResponse.json(parsed);
  } catch (error: any) {
    if (error.code === 'ENOENT') {
      return NextResponse.json(
        { error: 'Case not found' },
        { status: 404 }
      );
    }

    console.error('Graph load error:', error);
    return NextResponse.json(
      { error: 'Failed to load graph data' },
      { status: 500 }
    );
  }
}
```

### Narrative Route (app/api/cases/[caseId]/narrative/route.ts)

Migrate existing Pages Router route to App Router structure. Functionality unchanged - spawns Python subprocess to call narrative generator.

---

## Styling & Theme

### Dark Theme (globals.css)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --font-mono: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
  }

  body {
    @apply bg-slate-900 text-slate-100;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }

  code, .font-mono {
    font-family: var(--font-mono);
  }
}
```

### Tailwind Config (tailwind.config.ts)

```typescript
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['var(--font-mono)'],
      },
      colors: {
        'tier-3': '#6B7280',  // Gray
        'tier-2': '#F59E0B',  // Amber
        'tier-1': '#3B82F6',  // Blue
      },
    },
  },
  plugins: [],
};

export default config;
```

### Color Scheme

```
Backgrounds:
  Primary:   #0F172A (slate-900)
  Secondary: #1E293B (slate-800)
  Tertiary:  #334155 (slate-700)

Text:
  Primary:   #F8FAFC (slate-50)
  Secondary: #94A3B8 (slate-400)
  Muted:     #64748B (slate-500)

Verification Tiers:
  TIER_3_AI:            #6B7280 (gray-500)
  TIER_2_ANALYST:       #F59E0B (amber-500)
  TIER_2_INSTITUTIONAL: #D97706 (amber-600)
  TIER_1_CERTIFIED:     #3B82F6 (blue-500)

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
6. Create `/api/cases/[caseId]/graph` route (read from Factory)
7. Migrate `/api/cases/[caseId]/narrative` to App Router
8. Test both routes with TEST-CERESA case

### Phase 3: Core Components
9. Build `types.ts` from SCHEMA.md (Node, Link, GraphData interfaces)
10. Create `useGraph` hook
11. Build `KnowledgeGraph` component with react-force-graph-2d
12. Create `Header` component
13. Build dashboard layout

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
- [ ] Narrative generates with inline citations
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
