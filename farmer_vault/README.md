# Farmer Vault - Frontend Demo

Next.js 14 knowledge graph visualization interface for Civic Table.

## Quick Start

```bash
npm install
npm run dev
```

Navigate to http://localhost:3000 (redirects to TEST-CERESA case).

## Architecture

- **Graph API**: `/api/cases/[caseId]/graph` - Reads from Factory output
- **Narrative API**: `/api/cases/[caseId]/narrative` - Spawns Python script
- **Force-directed graph**: react-force-graph-2d
- **Dark theme**: Tailwind CSS with verification tier colors

## Key Components

- `KnowledgeGraph` - Force-directed visualization
- `EntitySidebar` - Tabbed details/narrative interface
- `DossierPanel` - Entity details and relations
- `NarrativePanel` - Generated narrative with citations

## Current Limitations

- **Local development only** (no authentication)
- **Single case** (TEST-CERESA hardcoded in root redirect)
- **File-based graph data** (no database)

## Next Steps

See `.claude/ROADMAP.md` Phase 8B for authentication and database integration.
