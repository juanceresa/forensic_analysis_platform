# Security Architecture

## Current Posture (As Implemented)

Civic Table currently uses a lightweight, shared-password access model in `farmer_vault/`:

- login endpoint: `app/api/auth/login/route.ts`
- logout endpoint: `app/api/auth/logout/route.ts`
- route gate: `proxy.ts`
- signed auth cookie: `vault_session` (HMAC-signed token)

This is suitable for private demos and controlled sharing, not a full multi-tenant production security model.

## Security Boundaries

1. Data location
- Case data is read from local `cases/` directories.
- Real client data should remain outside git.

2. Input validation
- API routes validate `caseId`, `docId`, and `entityId` patterns.
- Case paths are resolved and checked to prevent traversal.

3. Session gate
- Protected pages require login when `VAULT_PASSWORD` is configured.
- API routes (except auth login/logout) are also gated by `proxy.ts`.
- Cookie is `HttpOnly` and `SameSite=Lax`.
- `secure` cookie flag follows `NODE_ENV === 'production'` in current code.

## Required Environment Variables

For protected deployments:

- `VAULT_PASSWORD`: required to enable access gate
- `VAULT_SESSION_SECRET`: required for strong signed-session auth

Note: keep these values in `.env.local` and never commit them.

Current cookie security behavior: the login route sets `secure` based on
`NODE_ENV === 'production'`.

## Exposure Guidance

If exposing locally-hosted Vault to the internet (for example via cloudflared):

1. Use a strong `VAULT_PASSWORD`.
2. Serve over HTTPS only.
3. Run with `NODE_ENV=production` when publishing beyond localhost.
4. Limit sharing duration.
5. Avoid exposing real sensitive cases without additional controls.
6. Rotate secrets after any public-sharing session.

## Known Gaps vs Enterprise Security

Not yet implemented as a complete production security stack:

- per-user identity and RBAC
- case-level authorization model
- audit log pipeline and immutable security event trail
- hardened session management across all surfaces

## Hardening Roadmap (Recommended)

1. Replace shared password with per-user auth.
2. Add explicit per-route authorization checks in addition to proxy-level gating.
3. Add structured security and access auditing.
4. Add key/secret rotation policy and operational runbooks.
