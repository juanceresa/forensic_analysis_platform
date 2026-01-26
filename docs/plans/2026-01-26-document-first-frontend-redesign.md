# Document-First Frontend Redesign

> **Version:** 1.0.0
> **Date:** 2026-01-26
> **Status:** Design Complete - Ready for Implementation

---

## Executive Summary

This design repositions Civic Table from a graph-centric visualization tool to a **document-first forensic intelligence platform**. The core value proposition shifts from "explore this graph" to "verify your documents were processed correctly, examine extracted intelligence, and access supporting analysis tools."

**Key Changes:**
- Documents, entities, and narrative become primary interfaces
- Graph visualization repositioned as supplementary exploration tool
- Enterprise dashboard with workflow stages and verification tracking
- Browser-based navigation for simplicity and shareability
- Forensic/military aesthetic for professional credibility

---

## 1. Product Positioning

### 1.1 Brand Identity

**Civic Table LLC** — Forensic Intelligence service for historical property restitution
**Methodology:** Farmer House Democratic Repair Lab (Huston-Tillotson University)

Think: *"Palantir for Cuban exile land deeds" meets "academic rigor meets commercial implementation"*

### 1.2 Core Value Proposition

**What families need:** Confidence that their documents were processed correctly and proof of forensic findings for legal proceedings.

**What we deliver:**
1. Source verification (OCR extraction quality)
2. Entity intelligence (who/what/where discovered)
3. Relationship mapping (connections between entities)
4. Case narrative (chronological story with evidence)
5. Verification transparency (AI vs Analyst vs Certified tiers)

---

## 2. Overall Architecture

### 2.1 Navigation Structure

**Browser-based navigation** — No custom tab system in Phase 1. Standard URL routing with shareable links.

**URL Structure:**
```
/case/[caseId]                    → Dashboard (landing)
/case/[caseId]/documents          → Document list
/case/[caseId]/document/[docId]   → Document viewer
/case/[caseId]/entities           → Entity browser
/case/[caseId]/entity/[entityId]  → Entity detail
/case/[caseId]/narrative          → Timeline view
/case/[caseId]/graph              → Graph visualization
```

### 2.2 Page Layout

**Standard Layout (all views):**
```
┌──────────────────────────────────────────────────────┐
│ Top Bar (minimal): Logo | Case Name | User Menu     │
├──────────┬───────────────────────────────────────────┤
│          │                                           │
│  Left    │                                           │
│ Sidebar  │         Main Content Area                 │
│  (240px) │                                           │
│          │                                           │
│  Nav:    │                                           │
│  • Dash  │                                           │
│  • Docs  │                                           │
│  • Ents  │                                           │
│  • Narr  │                                           │
│  • Graph │                                           │
│          │                                           │
└──────────┴───────────────────────────────────────────┘
```

**HTML Structure:**
```html
<html class="dark" style="color-scheme: dark">
  <body class="bg-slate-950 text-slate-100">
    <header class="h-14 border-b border-slate-800">
      <!-- Logo + case name + user menu -->
    </header>

    <div class="flex h-[calc(100vh-3.5rem)]">
      <aside class="w-60 border-r border-slate-800">
        <!-- Navigation links as <a> tags -->
      </aside>

      <main class="flex-1 overflow-y-auto">
        <!-- View-specific content -->
      </main>
    </div>
  </body>
</html>
```

### 2.3 Visual Aesthetic: "Intelligence Terminal"

**Design Direction:** Forensic/military-inspired with technical precision.

**Typography:**
- **Display/Headings:** IBM Plex Mono (technical, authoritative)
- **Body Text:** Inter Variable (readable, modern)
- **Data/Metrics:** JetBrains Mono (tabular numbers)

**Color System:**
```css
/* Backgrounds */
--slate-950: #020617;  /* Main background */
--slate-900: #0f172a;  /* Card background */
--slate-800: #1e293b;  /* Borders, hover states */

/* Text */
--slate-100: #f1f5f9;  /* Primary text */
--slate-400: #94a3b8;  /* Muted text */

/* Verification Tiers */
--tier-ai: #f59e0b;      /* Amber - TIER_3_AI */
--tier-analyst: #3b82f6; /* Blue - TIER_2_ANALYST */
--tier-certified: #10b981; /* Green - TIER_1_CERTIFIED */
--tier-source: #a855f7;   /* Purple - TIER_4_SOURCE */
```

**Motion Principles:**
- Honor `prefers-reduced-motion`
- Animate only `transform` and `opacity`
- Staggered reveals on page load using `animation-delay`
- No `transition: all` — list specific properties

---

## 3. Dashboard View

**Route:** `/case/[caseId]`

**Purpose:** First view when accessing a case. Shows case status, progress, and provides quick navigation to analysis tools.

### 3.1 Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│ Top metrics grid (4 cards)                              │
│ [Stage] [Documents] [Entities] [Relationships]          │
├─────────────────────────────────────────────────────────┤
│ Verification Status (full-width card)                   │
│ [████████░░░░] 68% verified                            │
├─────────────────────────────────────────────────────────┤
│ Case Progression Checklist (full-width card)            │
│ Expandable sections for each stage                      │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Card Components

**1. Workflow Stage Card**
```tsx
<Card>
  <div className="text-xs text-slate-400 font-mono uppercase tracking-wider">
    Current Stage
  </div>
  <div className="mt-2 text-3xl font-mono tabular-nums">
    Processing
  </div>
  <div className="mt-1 flex items-center gap-2">
    <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
      <div className="h-full bg-blue-500" style={{width: '68%'}} />
    </div>
    <span className="text-sm text-slate-400 font-mono tabular-nums">68%</span>
  </div>
</Card>
```

**2. Metric Cards** (Documents, Entities, Relationships)
- Large number display (4xl font-mono tabular-nums)
- Small label above
- Link to relevant view below

**3. Verification Status Card** (full-width)
- Horizontal bar chart showing tier distribution
- Color-coded segments (amber/blue/green/purple)
- Legend below with percentages

**4. Case Progression Checklist** (full-width)
- Native `<details>` elements for expandable sections
- Four stages: Intake → Processing → Analysis → Certification
- Visual indicators: ✅ Complete, ⏳ In Progress, ⬜ Pending
- Nested checklist items within each stage

### 3.3 Case Workflow Stages

**Stage 1: Intake**
- Documents uploaded
- Family intake form completed
- Methodology documentation collected

**Stage 2: Processing**
- OCR extraction complete
- Entity extraction complete (TIER_3_AI)
- Graph construction complete

**Stage 3: Analysis**
- Analyst review in progress (TIER_2_ANALYST verification)
- Narrative generation
- Gap identification

**Stage 4: Certification**
- Legal review (TIER_1_CERTIFIED)
- Final report delivery
- Case closure

---

## 4. Documents View

### 4.1 Document List View

**Route:** `/case/[caseId]/documents`

**Layout:**
```tsx
<main className="p-8">
  <header className="mb-6">
    <h1 className="text-2xl font-mono mb-4">Documents</h1>

    {/* Sort controls */}
    <div className="flex gap-2">
      <button data-active={sortBy === 'date'}>By Date</button>
      <button data-active={sortBy === 'type'}>By Type</button>
    </div>
  </header>

  {/* Document grid */}
  <div className="grid gap-3">
    {documents.map((doc) => (
      <Link href={`/case/${caseId}/document/${doc.id}`}>
        <h3>{doc.filename}</h3>
        <time dateTime={doc.date}>{formatDate(doc.date)}</time>
        {doc.type && <span className="badge">{doc.type}</span>}
        <span>{doc.entityCount} entities</span>
      </Link>
    ))}
  </div>
</main>
```

**Features:**
- Default sort: Chronological by document date (oldest to newest)
- Toggle sort: By document type (Contract, Will, Transfer, etc.)
- Each card shows: filename, date, type badge, entity count
- Click → Navigate to document viewer

### 4.2 Document Viewer

**Route:** `/case/[caseId]/document/[docId]`

**Layout:** Two-column split

```
┌────────────────────┬──────────────────────┐
│                    │  Document Header     │
│                    │  [Filename, Date]    │
│   Original Image   ├──────────────────────┤
│                    │  [OCR Text | Entities]│
│   with zoom/pan    │                      │
│                    │  Tab content area    │
│                    │                      │
│                    │                      │
└────────────────────┴──────────────────────┘
     Flex-1                  500px fixed
```

**Left Column: Original Image**
- Full-height image display
- Zoom controls (+/- buttons, reset)
- Pan with drag
- Explicit width/height attributes (prevent CLS)

**Right Column: Tabbed Interface**

**Header Section:**
- Document filename (h1)
- Date with `<time>` element
- OCR confidence score

**Tab 1: OCR Text**
```tsx
<pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed">
  {doc.ocrText}
</pre>
```

**Tab 2: Entities**
- Grouped by entity type (PERSON, PROPERTY, ORGANIZATION, LOCATION)
- Each entity card shows:
  - Entity name
  - Role label (e.g., "Inheritor of Villa Aurelia")
  - Verification badge
- Click entity → Navigate to `/case/[caseId]/entity/[entityId]`

**Accessibility:**
- Tabs use proper ARIA (`role="tablist"`, `aria-selected`)
- Image has descriptive alt text
- Zoom controls have `aria-label`
- All interactive elements keyboard navigable
- Focus states visible with `focus-visible:ring-2`

---

## 5. Entities View

### 5.1 Entity Browser

**Route:** `/case/[caseId]/entities`

**Purpose:** Explore all entities discovered across all documents, grouped by type.

**Layout:**
```tsx
<main className="max-w-4xl mx-auto p-8">
  <header>
    <h1>Entities</h1>
    <p>{totalCount} entities across {documentCount} documents</p>
  </header>

  {/* PERSON Section */}
  <section>
    <h2>Person ({personCount})</h2>
    <div className="space-y-2">
      {personEntities.map((entity) => (
        <Link href={`/case/${caseId}/entity/${entity.id}`}>
          <h3>{entity.name}</h3>
          {entity.roleLabel && <p className="italic">{entity.roleLabel}</p>}
          <VerificationBadge tier={entity.verification.tier} />
        </Link>
      ))}
    </div>
  </section>

  {/* PROPERTY, ORGANIZATION, LOCATION sections follow same pattern */}
</main>
```

**Role Labels:**
AI-generated contextual descriptions that make scanning meaningful for families:
- **Mario Ceresa Rodriguez** — *Inheritor of Villa Aurelia*
- **Francisco Ramiero** — *Patriarch*
- **Villa Aurelia** — *Expropriated Property*
- **María Josefa Font** — *Spouse of Mario Ceresa*

**Implementation Note:**
Role labels generated during relation construction (after deduplication) when full graph context is available. New field: `entity.roleLabel: Optional[str]`

### 5.2 Entity Detail View

**Route:** `/case/[caseId]/entity/[entityId]`

**Layout Structure:**

**1. Entity Header Card**
- Entity type badge
- Entity name (h1)
- Role label (large italic text)
- Metadata grid (varies by entity type):
  - PERSON: birth_date, nationality, profession, residence
  - PROPERTY: address, area, registry_number
  - ORGANIZATION: org_type, address
  - LOCATION: location_type, country
- Verification badge + confidence score (prominent in top-right)

**2. AI-Generated Description** (collapsible `<details>`)
```tsx
<details open>
  <summary>About <Badge>TIER_3_AI</Badge></summary>
  <div>
    <p>{entity.aiDescription}</p>
    <div className="warning">
      ⚠️ AI-generated description. Not verified by human analysts.
    </div>
  </div>
</details>
```

**3. Source Documents Section**
- List of all documents mentioning this entity
- Each shows: filename, date
- Click → Navigate to document viewer

**4. Connections Section**
- Grouped by relationship type (OWNS, MARRIED_TO, INHERITS_FROM, etc.)
- Each connection shows:
  - Target entity name
  - Target entity role label
  - Verification badge
- Click → Navigate to that entity's detail view

**Empty State:**
If no connections: "No connections found" with helpful message

---

## 6. Narrative View

**Route:** `/case/[caseId]/narrative`

**Purpose:** Chronological timeline of the case with expandable periods. Each period shows narrative text, supporting documents, and related entities. Includes PDF export for legal proceedings.

### 6.1 Layout Structure

```
┌──────────────────────────────────────────────────┐
│ Header: "Case Narrative" | [Export to PDF]       │
├──────────────────────────────────────────────────┤
│ ⚠️ AI Disclaimer (yellow banner)                  │
├──────────────────────────────────────────────────┤
│                                                  │
│ Timeline (vertical spine on left)                │
│                                                  │
│ ● 1916-1920 — Property Acquisition               │
│   [Expandable card with narrative + docs]        │
│                                                  │
│ ● 1946-1958 — Inheritance and Transfer           │
│   [Expandable card]                              │
│                                                  │
│ ● 1960-1961 — Expropriation                      │
│   [Expandable card]                              │
│                                                  │
└──────────────────────────────────────────────────┘
```

### 6.2 Timeline Period Component

**Collapsed State:**
```tsx
<details>
  <summary>
    <time>1960-1961</time>
    <h2>Expropriation</h2>
    <div className="metadata">
      {doc.count} documents • {entity.count} entities
    </div>
  </summary>
</details>
```

**Expanded State:**
```tsx
<div className="period-content">
  {/* Narrative text */}
  <div className="prose">
    {period.narrative.split('\n\n').map(p => <p>{p}</p>)}
  </div>

  {/* Supporting documents */}
  <section>
    <h3>Supporting Documents ({count})</h3>
    {period.documents.map(doc => (
      <Link href={`/case/${caseId}/document/${doc.id}`}>
        <DocumentIcon />
        {doc.filename}
        <time>{doc.date}</time>
      </Link>
    ))}
  </section>

  {/* Key entities */}
  <section>
    <h3>Key Entities ({count})</h3>
    {period.entities.map(entity => (
      <Link href={`/case/${caseId}/entity/${entity.id}`}>
        {entity.name}
        <VerificationBadge tier={entity.verification.tier} />
      </Link>
    ))}
  </section>
</div>
```

### 6.3 PDF Export

**Button:** Top-right of page header
**Behavior:** POST to `/api/cases/[caseId]/narrative/export` → Download PDF
**Content:** Full continuous narrative with all supporting citations (not just expandable cards)

**Use Case:** Legal proceedings, attorney consultations, family records

---

## 7. Graph View

**Route:** `/case/[caseId]/graph`

**Purpose:** Supplementary visual exploration tool. Existing graph visualization repositioned as one view among many.

### 7.1 Layout

```
┌─────────────────────────────────────────────────┐
│ Header: "Knowledge Graph" | Settings | Reset    │
├─────────────────────────────────────────────────┤
│                                                 │
│           Graph Canvas (react-force-graph-2d)   │
│                                                 │
├─────────────────────────────────────────────────┤
│ Legend: [●Person] [●Property] [●Org] [●Location]│
└─────────────────────────────────────────────────┘
```

### 7.2 Interaction Changes

**Old Behavior:** Click node → Open right sidebar with entity details

**New Behavior:** Click node → Navigate to `/case/[caseId]/entity/[entityId]`

This maintains browser navigation consistency. Users can:
- View entity detail page
- Use browser back to return to graph
- Open entity in new tab (Ctrl+Click or middle-click)

### 7.3 Integration Notes

- Reuse existing `KnowledgeGraph` component
- Remove old right sidebar (EntitySidebar)
- Keep GraphSettingsPanel as overlay or move to header
- Legend in footer for entity type colors
- Settings persist to localStorage

---

## 8. Design System

### 8.1 Typography

**Font Loading:**
```tsx
// app/layout.tsx
import { IBM_Plex_Mono } from 'next/font/google';
import { Inter } from 'next/font/google';
import { JetBrains_Mono } from 'next/font/google';

const ibmPlexMono = IBM_Plex_Mono({
  weight: ['400', '500', '600'],
  subsets: ['latin'],
  variable: '--font-display',
});

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-body',
});

const jetBrainsMono = JetBrains_Mono({
  weight: ['400', '500'],
  subsets: ['latin'],
  variable: '--font-mono',
});
```

**Usage:**
```css
body { font-family: var(--font-body); }
h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-display);
  text-wrap: balance;
}
.tabular-data {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}
```

### 8.2 Color Tokens

```css
:root {
  /* Backgrounds */
  --slate-950: #020617;
  --slate-900: #0f172a;
  --slate-800: #1e293b;

  /* Text */
  --slate-100: #f1f5f9;
  --slate-300: #cbd5e1;
  --slate-400: #94a3b8;
  --slate-500: #64748b;

  /* Verification Tiers */
  --tier-ai-bg: rgb(245 158 11 / 0.1);
  --tier-ai-border: rgb(245 158 11 / 0.2);
  --tier-ai-text: #fbbf24;

  --tier-analyst-bg: rgb(59 130 246 / 0.1);
  --tier-analyst-border: rgb(59 130 246 / 0.2);
  --tier-analyst-text: #60a5fa;

  --tier-certified-bg: rgb(16 185 129 / 0.1);
  --tier-certified-border: rgb(16 185 129 / 0.2);
  --tier-certified-text: #34d399;

  --tier-source-bg: rgb(168 85 247 / 0.1);
  --tier-source-border: rgb(168 85 247 / 0.2);
  --tier-source-text: #c084fc;

  /* Interactive */
  --blue-600: #2563eb;
  --blue-700: #1d4ed8;
  --blue-400: #60a5fa;
}

html.dark {
  color-scheme: dark;
}
```

### 8.3 Shared Components

**VerificationBadge**
```tsx
interface VerificationBadgeProps {
  tier: 'TIER_1_CERTIFIED' | 'TIER_2_ANALYST' | 'TIER_3_AI' | 'TIER_4_SOURCE';
  size?: 'tiny' | 'small' | 'medium' | 'large';
}

export function VerificationBadge({ tier, size = 'medium' }: VerificationBadgeProps) {
  const config = {
    TIER_3_AI: { label: 'AI', className: 'bg-tier-ai-bg ...' },
    TIER_2_ANALYST: { label: 'Analyst', className: 'bg-tier-analyst-bg ...' },
    TIER_1_CERTIFIED: { label: 'Certified', className: 'bg-tier-certified-bg ...' },
    TIER_4_SOURCE: { label: 'Source', className: 'bg-tier-source-bg ...' },
  }[tier];

  const sizeClasses = {
    tiny: 'px-1.5 py-0.5 text-[10px]',
    small: 'px-2 py-0.5 text-xs',
    medium: 'px-2 py-1 text-xs',
    large: 'px-3 py-1.5 text-sm',
  }[size];

  return (
    <span
      className={`inline-flex items-center rounded font-mono uppercase tracking-wider border ${config.className} ${sizeClasses}`}
      title={tier}
    >
      {config.label}
    </span>
  );
}
```

**Card**
```tsx
interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export function Card({ children, className = '' }: CardProps) {
  return (
    <div className={`bg-slate-900 border border-slate-800 rounded p-6 ${className}`}>
      {children}
    </div>
  );
}
```

### 8.4 Animation System

```css
@media (prefers-reduced-motion: no-preference) {
  @keyframes fadeInUp {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }

  @keyframes fadeInLeft {
    from { opacity: 0; transform: translateX(-16px); }
    to { opacity: 1; transform: translateX(0); }
  }

  .animate-fade-in-up {
    animation: fadeInUp 0.3s ease-out backwards;
  }

  .animate-fade-in-left {
    animation: fadeInLeft 0.4s ease-out backwards;
  }
}
```

**Staggered delays using CSS custom properties:**
```tsx
<div style={{ '--index': index } as React.CSSProperties}>
  {/* CSS: animation-delay: calc(0.05s * var(--index)); */}
</div>
```

---

## 9. Backend Requirements

### 9.1 New API Endpoints

**1. Document Metadata**
```typescript
GET /api/cases/[caseId]/documents
Response: {
  documents: Array<{
    id: string;
    filename: string;
    date: string; // ISO date
    type?: string; // "Contract", "Will", etc.
    entityCount: number;
    confidence: number;
  }>
}
```

**2. Document Detail**
```typescript
GET /api/cases/[caseId]/document/[docId]
Response: {
  id: string;
  filename: string;
  date: string;
  type?: string;
  imagePath: string; // Path to original image in cases/[caseId]/intake/
  ocrText: string;
  confidence: number;
  entities: Array<{
    id: string;
    name: string;
    entity_type: string;
    roleLabel?: string;
    verification: { tier: string; confidence: number };
  }>;
}
```

**3. Narrative PDF Export**
```typescript
POST /api/cases/[caseId]/narrative/export
Response: PDF blob (application/pdf)
```

### 9.2 Data Schema Updates

**Add to Entity Schema:**
```python
class Entity(BaseModel):
    # ... existing fields
    roleLabel: Optional[str] = None  # AI-generated contextual label
```

**Generate Role Labels:**

New backend task after relation construction:

```python
def generate_role_labels(graph_data: GraphData) -> None:
    """
    After deduplication and relation construction,
    generate contextual role labels for each entity.

    Examples:
    - "Mario Ceresa Rodriguez" → "Primary Inheritor"
    - "Villa Aurelia" → "Expropriated Property"
    - "Francisco Ramiero" → "Patriarch"
    """
    for entity in graph_data.nodes:
        relationships = get_entity_relationships(entity, graph_data)
        doc_count = len(entity.source_documents)

        prompt = f"""
        Given this entity and its context:
        Name: {entity.name}
        Type: {entity.entity_type}
        Appears in: {doc_count} documents
        Relationships: {format_relationships(relationships)}

        Generate a concise contextual role label (2-4 words) that describes
        this entity's role in the case. Examples:
        - "Primary Inheritor"
        - "Expropriated Property"
        - "Patriarch"
        - "Spouse of Mario Ceresa"

        Return only the label, no explanation.
        """

        entity.roleLabel = call_llm(prompt).strip()
```

**When to run:** After `structure/build_graph.py` completes, before writing final `graph_data.json`

### 9.3 Document Type Extraction

**Current State:** Documents are named by user (e.g., "3 26 1960 Credit Report.pdf")

**Enhancement:** Extract document type from filename or content:
- Keywords in filename: "Will", "Testament", "Contract", "Transfer", "Deed"
- LLM classification during extraction if not obvious
- Store in document metadata

**Field:** `document.type: Optional[str]` (values: "Contract", "Will", "Transfer", "Deed", "Report", etc.)

---

## 10. File Structure

```
farmer_vault/
├── app/
│   ├── case/
│   │   └── [caseId]/
│   │       ├── page.tsx                # Dashboard
│   │       ├── layout.tsx              # Shared layout with sidebar
│   │       ├── documents/
│   │       │   └── page.tsx            # Document list
│   │       ├── document/
│   │       │   └── [docId]/
│   │       │       └── page.tsx        # Document viewer
│   │       ├── entities/
│   │       │   └── page.tsx            # Entity browser
│   │       ├── entity/
│   │       │   └── [entityId]/
│   │       │       └── page.tsx        # Entity detail
│   │       ├── narrative/
│   │       │   └── page.tsx            # Timeline view
│   │       └── graph/
│   │           └── page.tsx            # Graph visualization
│   ├── layout.tsx                      # Root layout
│   ├── globals.css                     # Global styles
│   └── api/
│       └── cases/
│           └── [caseId]/
│               ├── documents/
│               │   └── route.ts
│               ├── document/
│               │   └── [docId]/
│               │       └── route.ts
│               ├── entities/
│               │   └── route.ts
│               ├── entity/
│               │   └── [entityId]/
│               │       └── route.ts
│               ├── narrative/
│               │   ├── route.ts
│               │   └── export/
│               │       └── route.ts
│               └── graph/
│                   └── route.ts
├── components/
│   ├── Dashboard/
│   │   ├── StageCard.tsx
│   │   ├── MetricCard.tsx
│   │   ├── VerificationStatusCard.tsx
│   │   └── CaseProgressChecklist.tsx
│   ├── Documents/
│   │   ├── DocumentList.tsx
│   │   └── DocumentViewer.tsx
│   ├── Entities/
│   │   ├── EntityBrowser.tsx
│   │   └── EntityDetail.tsx
│   ├── Narrative/
│   │   └── TimelinePeriod.tsx
│   ├── shared/
│   │   ├── VerificationBadge.tsx
│   │   ├── Card.tsx
│   │   ├── Sidebar.tsx
│   │   └── Header.tsx
│   └── KnowledgeGraph.tsx              # Existing graph component (reused)
├── lib/
│   ├── types.ts                        # TypeScript type definitions
│   ├── api.ts                          # API client functions
│   └── utils.ts                        # Utility functions
└── hooks/
    ├── useGraphSettings.ts             # Existing (reused)
    └── useCaseData.ts                  # New: SWR hook for case data
```

---

## 11. Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1-2)

**Deliverables:**
- ✅ New route structure (`/case/[caseId]/*`)
- ✅ Root layout with sidebar navigation
- ✅ Shared components (Sidebar, Header, Card, VerificationBadge)
- ✅ Design system CSS (colors, typography, animations)
- ✅ API endpoints for documents and entities

**Backend Tasks:**
- Build document metadata aggregation
- Create document detail endpoint (image path + OCR + entities)
- Update graph_data.json to include document metadata

**Frontend Tasks:**
- Create shared layout with sidebar
- Build reusable Card and VerificationBadge components
- Set up Tailwind config with custom colors
- Load custom fonts (IBM Plex Mono, Inter, JetBrains Mono)

### Phase 2: Document Workflow (Week 2-3)

**Deliverables:**
- ✅ Dashboard view with metric cards and checklist
- ✅ Document list view with sorting
- ✅ Document viewer (image + OCR + entities tabs)
- ✅ Basic navigation between views

**Backend Tasks:**
- No new backend work required (uses existing data)

**Frontend Tasks:**
- Build Dashboard with StageCard, MetricCard, VerificationStatusCard, CaseProgressChecklist
- Build DocumentList with sort toggle
- Build DocumentViewer with two-column layout and tabs
- Implement image zoom/pan controls
- Wire up navigation links

### Phase 3: Entity System (Week 3-4)

**Deliverables:**
- ✅ Entity role label generation (backend)
- ✅ Entity browser view (grouped by type)
- ✅ Entity detail view (profile + documents + connections)
- ✅ Entity-document-entity navigation flow

**Backend Tasks:**
- Implement `generate_role_labels()` function
- Run after relation construction, before writing graph_data.json
- Test role label quality across multiple cases

**Frontend Tasks:**
- Build EntityBrowser with grouped sections
- Build EntityDetail with collapsible AI description
- Display source documents and connections
- Wire up all navigation links

### Phase 4: Narrative & Polish (Week 4-5)

**Deliverables:**
- ✅ Narrative timeline view with expandable periods
- ✅ PDF export functionality
- ✅ Graph view integration (reuse existing component)
- ✅ Animation polish and performance optimization

**Backend Tasks:**
- Build narrative PDF export endpoint
- Generate PDF from narrative data (use library like ReportLab or WeasyPrint)

**Frontend Tasks:**
- Build Timeline view with expandable details
- Implement PDF export button and download flow
- Integrate existing KnowledgeGraph component
- Update graph click behavior to navigate to entity detail
- Add staggered animations to all views
- Performance audit (lazy loading, code splitting)

---

## 12. Web Interface Guidelines Compliance

This design follows [Vercel Web Interface Guidelines](https://github.com/vercel-labs/web-interface-guidelines):

**Accessibility:**
- ✅ Icon-only buttons have `aria-label`
- ✅ All form inputs have labels or ARIA equivalents
- ✅ Semantic HTML (`<button>`, `<a>`, `<time>`, `<details>`)
- ✅ Keyboard navigation for all interactive elements
- ✅ Images have explicit width/height (prevent CLS)
- ✅ Headings follow hierarchy with proper nesting

**Focus States:**
- ✅ Visible focus via `focus-visible:ring-2`
- ✅ Never `outline-none` without replacement

**Forms:**
- ✅ Inputs have proper `type`, `name`, `autocomplete`
- ✅ Labels clickable via `htmlFor`

**Animation:**
- ✅ Honor `prefers-reduced-motion`
- ✅ Animate only `transform`/`opacity`
- ✅ No `transition: all`

**Typography:**
- ✅ Use `text-wrap: balance` on headings
- ✅ Tabular numbers via `font-variant-numeric: tabular-nums`
- ✅ Loading states end with `…`

**Navigation & State:**
- ✅ URL reflects all view state
- ✅ Use `<Link>` for navigation (not onClick)
- ✅ Deep-linkable URLs

**Dark Mode:**
- ✅ Set `color-scheme: dark` on `<html>`
- ✅ Match `<meta name="theme-color">` to background

---

## 13. Success Metrics

**User Validation:**
- [ ] Families can verify OCR accuracy within 5 minutes
- [ ] Analysts can identify key entities within 10 minutes
- [ ] Case narrative exports to PDF successfully
- [ ] Navigation feels intuitive (< 3 clicks to any entity)

**Technical Validation:**
- [ ] Lighthouse score > 90 (Performance, Accessibility)
- [ ] All interactive elements keyboard accessible
- [ ] Page load time < 2s on 3G connection
- [ ] Zero critical accessibility violations (axe-core)

**Design Validation:**
- [ ] Verification tiers instantly recognizable by color
- [ ] Animations feel professional (not distracting)
- [ ] Typography hierarchy clear and scannable
- [ ] Layout responsive (works on tablets/large phones)

---

## 14. Open Questions & Future Enhancements

**Phase 2 Features (Post-MVP):**
- [ ] Multi-tab workspace (compare two documents side-by-side)
- [ ] Split view (document + entity detail simultaneously)
- [ ] Pinned panels (keep entity card visible while browsing)
- [ ] Search across all documents/entities
- [ ] Advanced filters (by verification tier, date range, entity type)
- [ ] Bulk actions (mark multiple entities for review)
- [ ] Commenting/annotation system (analyst notes on documents)
- [ ] Export options (Excel, JSON, full case archive)

**Integration:**
- [ ] Email notification when case reaches new stage
- [ ] Slack/webhook integration for analyst assignments
- [ ] API for third-party tools (legal software integration)

---

## 15. References

**Related Documentation:**
- `docs/architecture/ARCHITECTURE.md` - System design, Air Gap
- `docs/architecture/SECURITY.md` - Authentication, authorization
- `docs/architecture/FRONTEND.md` - UI design system
- `farmer_factory/structure/SCHEMA.md` - Complete JSON/Pydantic schema
- `farmer_factory/structure/DATA_DICTIONARY.md` - Field-level reference

**External Resources:**
- [Vercel Web Interface Guidelines](https://github.com/vercel-labs/web-interface-guidelines)
- [Web Content Accessibility Guidelines (WCAG) 2.1](https://www.w3.org/WAI/WCAG21/quickref/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

---

**Document Version:** 1.0.0
**Last Updated:** 2026-01-26
**Status:** Design Complete - Ready for Implementation
**Next Step:** Begin Phase 1 implementation (Core Infrastructure)
