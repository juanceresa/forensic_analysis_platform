# Security Policy

## Scope

This repository includes:

- `farmer_factory/` (Python processing pipeline)
- `farmer_vault/` (Next.js read-only viewer)

Real client case data is intentionally excluded from version control.

## Reporting a Vulnerability

Please do not open public issues for security vulnerabilities.

Use one of these channels:

1. Open a private GitHub security advisory for this repository.
2. Contact the maintainer directly and include:
   - affected file/path
   - reproduction steps
   - impact assessment

I will acknowledge receipt and provide a mitigation timeline.

## Hardening Notes

- Keep `.env`/`.env.local` files out of source control.
- Use strong values for:
  - `VAULT_PASSWORD`
  - `VAULT_SESSION_SECRET` (used for signed-session auth)
- If exposing the UI publicly, require HTTPS and run with `NODE_ENV=production`
  so auth cookies are marked `secure`.
- Treat all `TIER_3_AI` outputs as unverified analysis.
- Before opening the repo publicly, run:
  - `bash scripts/check_public_readiness.sh`
