# Farmer Vault - The Vault Frontend

Next.js 16 forensic intelligence interface for Civic Table platform.

## Quick Start

```bash
npm install
npm run dev
```

Navigate to http://localhost:3000 (redirects to TEST-CERESA case).

## Architecture

The Vault implements a **document-first navigation architecture** with multiple complementary views for case data:

```
/case/[caseId]/              → Dashboard (case overview)
/case/[caseId]/documents     → Document Browser
/case/[caseId]/entities      → Entity Browser (grouped by type)
/case/[caseId]/narrative     → Timeline View (grouped by decade)
/case/[caseId]/graph         → Knowledge Graph (interactive)
/case/[caseId]/entity/[id]   → Entity Detail
/case/[caseId]/document/[id] → Document Viewer
```

## API Routes

| Endpoint | Description |
|----------|-------------|
| `/api/cases/[caseId]/dashboard` | Aggregated metrics, verification distribution, workflow status |
| `/api/cases/[caseId]/entities` | All entities grouped by type (PERSON, PROPERTY, etc.) |
| `/api/cases/[caseId]/timeline` | Documents grouped by decade with contextual titles |
| `/api/cases/[caseId]/graph` | Full graph_data.json for visualization |

## Key Components

### Navigation
- `CaseLayout` - Sidebar navigation with case context
- `Sidebar` - Navigation links for all views

### Views
- `EntityBrowser` - Type-grouped entity display with verification badges
- `TimelinePeriod` - Expandable timeline periods with document cards
- `GraphView` - Wrapper for knowledge graph with navigation

### Graph
- `KnowledgeGraph` - Force-directed visualization (react-force-graph-2d)
- `GraphSettingsPanel` - Real-time graph customization (layout, colors, filters)
- `DossierPanel` - Entity details and relations

### Shared
- `Card` - Styled container component
- `Badge` - Verification tier badges
- `shared/index.ts` - Common UI components

## Data Flow

```
Factory Output                 API Routes                    Components
─────────────                 ──────────                    ──────────
graph_data.json    →    /api/cases/[caseId]/*    →    Page Components
    │                         │                              │
    ├── nodes[]              ├── /dashboard                 ├── Dashboard
    │   └── entities         │   └── metrics,workflow       │
    │   └── documents        ├── /entities                  ├── EntityBrowser
    │                        │   └── grouped by type        │
    ├── links[]              ├── /timeline                  ├── TimelinePeriod
    │   └── relationships    │   └── grouped by decade      │
    │                        └── /graph                     └── KnowledgeGraph
    └── metadata                 └── full graph data
```

## Verification Tiers

| Tier | Description | Color |
|------|-------------|-------|
| `TIER_3_AI` | AI-extracted, not verified | Grey |
| `TIER_2_ANALYST` | Analyst verified | Amber |
| `TIER_2_INSTITUTIONAL` | Farmer House verified | Gold with FH badge |
| `TIER_1_CERTIFIED` | Legally certified | Blue |

**Note:** `TIER_4_SOURCE` is a frontend-only display tier used for source document entities in the UI.

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript 5.7
- **Styling**: Tailwind CSS 3.4
- **Graph**: react-force-graph-2d
- **Testing**: Vitest

## Development

```bash
# Run development server
npm run dev

# Run tests
npm test

# Type check
npm run type-check

# Lint
npm run lint
```

## Current Limitations

- **Local development only** (authentication not configured)
- **File-based data** (reads from ../cases directory)
- **Single case support** (multi-case navigation planned)

## Documentation

- `/docs/architecture/FRONTEND.md` - Full frontend specification
- `/docs/architecture/ARCHITECTURE.md` - System architecture
- `/.claude/ROADMAP.md` - Project roadmap
