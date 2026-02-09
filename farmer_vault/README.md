# Farmer Vault

Next.js interface for exploring Civic Table case outputs.

## Quick Start

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

If local case data exists, Vault redirects to an available case (prefers `DEMO-SYNTHETIC`).

## What Vault Does

- renders document, entity, narrative, and graph views
- reads case artifacts from local `../cases/<CASE_ID>/`
- exposes case APIs under `/api/cases/[caseId]/...`
- supports grouped documents via `document_groups.yaml`

## Key Routes

```text
/case/[caseId]
/case/[caseId]/documents
/case/[caseId]/document/[docId]
/case/[caseId]/entities
/case/[caseId]/entity/[entityId]
/case/[caseId]/narrative
/case/[caseId]/graph
```

## Auth Model

Current auth is a shared-password gate:

- login route: `/login`
- auth API: `/api/auth/login`
- logout API: `/api/auth/logout`
- edge gate: `proxy.ts`
- session token: signed `vault_session` cookie (`lib/auth.ts`)

Environment variables:

- `VAULT_PASSWORD`
- `VAULT_SESSION_SECRET` (used to sign session cookies)

Current cookie behavior: `secure` is set automatically when `NODE_ENV=production`.

## Development Commands

```bash
npm run dev
npm test
npm run lint
npm run type-check
```

## Related Docs

- `../docs/architecture/FRONTEND.md`
- `../docs/architecture/ARCHITECTURE.md`
- `../docs/architecture/SECURITY.md`
