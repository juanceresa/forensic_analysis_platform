# Frontend Architecture (Vault)

## Overview

`farmer_vault/` is a Next.js App Router client for reading and reviewing processed case artifacts.

Design goals:

- read-only case exploration
- document-first navigation
- provenance visibility (entities, links, source docs, verification tier)

## Route Surface

Main app routes:

- `/login`
- `/case/[caseId]`
- `/case/[caseId]/documents`
- `/case/[caseId]/document/[docId]`
- `/case/[caseId]/entities`
- `/case/[caseId]/entity/[entityId]`
- `/case/[caseId]/narrative`
- `/case/[caseId]/graph`

Main API routes:

- `/api/cases/[caseId]/dashboard`
- `/api/cases/[caseId]/documents`
- `/api/cases/[caseId]/document/[docId]`
- `/api/cases/[caseId]/document/[docId]/image`
- `/api/cases/[caseId]/entities`
- `/api/cases/[caseId]/entity/[entityId]`
- `/api/cases/[caseId]/timeline`
- `/api/cases/[caseId]/narrative`
- `/api/cases/[caseId]/graph`
- `/api/cases/[caseId]/dossier`

## Data Model

Vault is file-backed by case outputs in `../cases/<CASE_ID>/`.

Core sources:

- `output/graph_data.json`
- `output/entity_descriptions.json` (optional)
- `output/document_analyses.json` (optional)
- `output/case_narrative.json` (optional)
- `extractions/*.json`
- `document_groups.yaml` (optional, when confirmed)

## Document Grouping

Shared document-group logic in `lib/document-groups.ts` is reused across document and entity APIs:

- loads/validates `document_groups.yaml`
- maps extraction files to logical grouped documents
- provides consistent IDs (`doc_<groupId>`) and names across views

## Graph View

Graph components are under `components/Graph/`.

- `KnowledgeGraph.tsx`: force-directed visualization
- `GraphView.tsx`: graph page composition
- `EntitySidebar.tsx`: entity detail panel

Graph behavior is tuned for interactive investigation, with filters and entity inspection rather than raw node dumps.

## Authentication Model

Current model is shared-password gate (`proxy.ts` + `/api/auth/login`).

This should be treated as a controlled-access layer, not full enterprise IAM.

## Operational Notes

- root route auto-selects an available local case (prefers `DEMO-SYNTHETIC`)
- app shows setup guidance if no local case is present
- for local demos: install sample case and run `npm run dev`
