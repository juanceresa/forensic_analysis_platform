# Farmer House Forensic Intelligence Platform — Security Architecture

> **Document Classification:** Internal Security Reference
> **Version:** 1.0.0
> **Last Updated:** 2026-01-22
> **Status:** PLANNING PHASE — Security-First Design

---

## Executive Summary

The Farmer House platform handles **highly sensitive historical property documents** for Cuban exile families seeking restitution. These families are justifiably concerned about:

- **Privacy**: Their claims may be politically sensitive
- **Confidentiality**: Documents contain personal and financial information
- **Integrity**: Evidence must be tamper-proof for legal proceedings
- **Access Control**: Only authorized family members should view their cases

This document defines the security architecture to address these concerns.

---

## Threat Model

### Assets to Protect

| Asset | Sensitivity | Impact if Compromised |
|-------|-------------|----------------------|
| Source PDFs (property deeds, confiscation orders) | **CRITICAL** | Legal case destroyed, family privacy violated |
| Extracted entity graph | **HIGH** | Family relationships exposed, claims undermined |
| User identity/contact info | **HIGH** | Harassment, identity theft |
| Processing audit logs | **MEDIUM** | Evidence chain broken |
| AI inference metadata | **LOW** | Minimal direct harm |

### Threat Actors

| Actor | Motivation | Capabilities |
|-------|-----------|--------------|
| **Opportunistic attackers** | Data theft for resale | Automated scanning, credential stuffing |
| **Political adversaries** | Sabotage claims, identify families | Sophisticated social engineering, targeted attacks |
| **Curious insiders** | Unauthorized case viewing | Legitimate system access, credential abuse |
| **Legal opponents** | Undermine evidence integrity | Discovery requests, forensic analysis |

### Attack Vectors

1. **Unauthorized access to Zone B (Vault)** — No authentication in MVP1
2. **Cross-case data leakage** — User A sees User B's documents
3. **Man-in-the-middle attacks** — Unencrypted data in transit
4. **Session hijacking** — Token theft, session fixation
5. **Credential compromise** — Weak passwords, phishing
6. **Insider threats** — Analyst accesses unauthorized cases
7. **Evidence tampering** — Modified documents, altered timestamps

---

## Security Architecture

### Defense in Depth Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 1: IDENTITY & ACCESS                                      │
│ • OAuth 2.0 with Auth0/Clerk                                    │
│ • Multi-factor authentication (TOTP required)                   │
│ • Role-based access control (RBAC)                              │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 2: TRANSPORT SECURITY                                     │
│ • TLS 1.3 only (no downgrades)                                  │
│ • HSTS with preload                                             │
│ • Certificate pinning for API calls                             │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 3: APPLICATION SECURITY                                   │
│ • Case isolation (row-level security in DB)                     │
│ • Content Security Policy (CSP)                                 │
│ • Rate limiting, request signing                                │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 4: DATA SECURITY                                          │
│ • Encryption at rest (AES-256)                                  │
│ • Field-level encryption for PII                                │
│ • Immutable audit logs                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 5: INFRASTRUCTURE SECURITY                                │
│ • Private VPC, no public egress from Zone A                     │
│ • Database backups encrypted with separate keys                 │
│ • SOC 2 Type II compliant hosting (Vercel Enterprise)           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Authentication & Authorization

### OAuth 2.0 Implementation

**Primary Provider:** [Clerk](https://clerk.com)

**Why Clerk:**
- **Free tier:** 10,000 monthly active users (years of runway)
- **MFA included:** TOTP, SMS, backup codes at no cost
- **Next.js native:** Purpose-built for Next.js App Router
- **Production-ready UI:** Professional login/signup screens out of the box
- **Social logins:** Google, Apple, GitHub included
- **Session management:** Automatic token refresh, secure storage
- **User management:** Built-in admin dashboard

**Why OAuth 2.0:**
- Industry-standard, battle-tested protocol
- Reduces attack surface (no password storage)
- Enables MFA without custom implementation
- Audit logging built-in

### Authentication Flow (Clerk)

```
┌──────────┐                                       ┌──────────┐
│  User    │                                       │  Clerk   │
└────┬─────┘                                       └────┬─────┘
     │                                                  │
     │ 1. Visit protected route                        │
     │────────────────────────────────────────────────>│
     │                                                  │
     │ 2. Redirect to Clerk sign-in (with PKCE)        │
     │<────────────────────────────────────────────────│
     │                                                  │
     │ 3. User authenticates (password + MFA)          │
     │────────────────────────────────────────────────>│
     │                                                  │
     │ 4. Clerk sets session cookie (HttpOnly)         │
     │<────────────────────────────────────────────────│
     │                                                  │
┌────▼─────┐                                      ┌────▼─────┐
│ Vault    │ 5. Every request includes session    │  Clerk   │
│ (Next.js)│    Middleware validates with Clerk   │  API     │
│ Middleware──────────────────────────────────────>│          │
└────┬─────┘                                      └────┬─────┘
     │                                                  │
     │ 6. User object with JWT claims                  │
     │<────────────────────────────────────────────────│
     │                                                  │
┌────▼─────┐                                      ┌────▼─────┐
│ Vault    │ 7. API call with userId in JWT       │ Supabase │
│ Frontend │─────────────────────────────────────>│ (Postgres│
└──────────┘    RLS validates userId              │ + RLS)   │
                                                  └──────────┘
```

**Security Features:**
- **PKCE (Proof Key for Code Exchange)**: Prevents authorization code interception
- **Short-lived access tokens**: 15 minutes expiry
- **Refresh token rotation**: New refresh token on each use, old one invalidated
- **HttpOnly cookies**: Tokens stored in secure cookies, not localStorage
- **CSRF protection**: State parameter validation

### User Roles

| Role | Access | Use Case |
|------|--------|----------|
| `family_member` | Read own case only | Default role for family clients |
| `case_admin` | Read/write own case, invite family | Primary contact for a family |
| `analyst` | Read/write multiple cases (assigned) | Internal staff processing documents |
| `supervisor` | Read all cases, manage users | Quality assurance, oversight |
| `system_admin` | Full access, user management | Platform administration |

### Case Access Control

**Row-Level Security (RLS) in PostgreSQL:**

```sql
-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  auth0_id TEXT UNIQUE NOT NULL,
  email TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('family_member', 'case_admin', 'analyst', 'supervisor', 'system_admin')),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Cases table
CREATE TABLE cases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  family_name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Case access table (many-to-many)
CREATE TABLE case_access (
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
  permission TEXT NOT NULL CHECK (permission IN ('read', 'write', 'admin')),
  granted_by UUID REFERENCES users(id),
  granted_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (user_id, case_id)
);

-- RLS Policy: Users can only see cases they have access to
ALTER TABLE cases ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their assigned cases"
  ON cases FOR SELECT
  USING (
    id IN (
      SELECT case_id FROM case_access WHERE user_id = auth.uid()
    )
    OR
    EXISTS (
      SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('supervisor', 'system_admin')
    )
  );
```

**No Cross-Case Leakage:**
- Database enforces isolation at query level
- Impossible to fetch data from unassigned cases
- Even if frontend has bugs, backend rejects unauthorized queries

---

## Transport Security

### TLS Configuration

**Minimum Standard:** TLS 1.3 only

**Next.js config:**
```typescript
// next.config.js
module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          // Strict Transport Security (force HTTPS)
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          // Prevent MIME sniffing
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          // Prevent clickjacking
          {
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          // Content Security Policy
          {
            key: 'Content-Security-Policy',
            value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' https://*.supabase.co https://*.auth0.com"
          }
        ]
      }
    ]
  }
}
```

### API Request Signing

All API calls to Supabase include:
1. **JWT signature** (issued by Auth0)
2. **Request timestamp** (prevents replay attacks)
3. **HMAC signature** (prevents tampering)

**Example:**
```typescript
const apiCall = async (endpoint: string, data: any) => {
  const timestamp = Date.now();
  const signature = await hmac(
    `${endpoint}:${timestamp}:${JSON.stringify(data)}`,
    process.env.API_SECRET_KEY
  );

  return fetch(endpoint, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'X-Timestamp': timestamp.toString(),
      'X-Signature': signature
    },
    body: JSON.stringify(data)
  });
};
```

---

## Data Security

### Encryption at Rest

**Supabase (PostgreSQL):**
- Database-level encryption: AES-256
- Encrypted backups: Separate encryption keys rotated quarterly
- Point-in-time recovery: Encrypted WAL logs

**Field-Level Encryption (Sensitive PII):**

```typescript
// Encrypt before storing in database
const encryptedSSN = await encrypt(ssn, userKey);

// Decrypt only when authorized user requests
const decryptedSSN = await decrypt(encryptedSSN, userKey);
```

**Which fields to encrypt:**
- Social Security Numbers (if collected)
- Exact street addresses (beyond city/province)
- Bank account numbers (from historical documents)
- Personal notes from analysts

**Key Management:**
- Master key stored in AWS KMS or Google Secret Manager
- User-specific keys derived from master key + user ID
- Keys rotated annually
- Old keys retained for decryption but not encryption

### Document Storage Security

**Zone A (Factory - Internal):**
- Stored on encrypted local disks or private S3 bucket
- No public access
- Access logged with IP, timestamp, user

**Zone B (Vault - Client-Facing):**
- Documents served through Supabase Storage
- Signed URLs with 1-hour expiry
- Watermarked with user ID (forensic tracking)
- No direct URL access (requires authentication)

**Redaction:**
```typescript
// Before serving document to client
const redactedDocument = await redact(document, {
  livingPersons: true,  // Names of people born after 1960
  exactAddresses: true, // Replace "123 Main St" with "Main St, Havana"
  financials: false     // Keep amounts for context
});
```

### Audit Logging

**What to log:**
- All authentication events (login, logout, failed attempts)
- Document access (who viewed what, when)
- Data modifications (edits to entities, tier promotions)
- Administrative actions (user creation, role changes)
- Export/download events (PDF generation, data exports)

**Log format (JSON Lines):**
```json
{
  "timestamp": "2025-01-22T14:30:00Z",
  "event_type": "DOCUMENT_VIEWED",
  "user_id": "auth0|abc123",
  "user_email": "maria@example.com",
  "user_role": "family_member",
  "case_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_id": "DOC-001",
  "ip_address": "192.0.2.1",
  "user_agent": "Mozilla/5.0...",
  "result": "SUCCESS"
}
```

**Log storage:**
- Append-only (immutable)
- Stored separately from application database
- Retained for 7 years (legal requirement)
- Monitored for suspicious patterns (e.g., bulk downloads)

### Tamper Evidence

**Hash Chain:**
```
Log Entry 1 → hash(entry1) → Entry 2 → hash(entry2 + hash1) → Entry 3 → ...
```

**Cryptographic Signing:**
- Each case dossier signed with platform private key
- Signature includes all entity data + timestamps
- Clients can verify authenticity with public key
- Supports legal discovery requirements

---

## Session Management

### Token Lifecycle

| Token Type | Lifetime | Storage | Renewal |
|------------|----------|---------|---------|
| **Access Token (JWT)** | 15 minutes | HttpOnly cookie | Automatically via refresh token |
| **Refresh Token** | 30 days | HttpOnly cookie (rotated) | Manual re-authentication after expiry |
| **CSRF Token** | Session | HTTP header | Regenerated on each request |

### Session Security

**Session fixation prevention:**
- Regenerate session ID on login
- Invalidate old session on password change
- Single active session per user (logout on new login)

**Session termination:**
- Automatic logout after 30 minutes inactivity
- Manual "logout all devices" option
- Admin can revoke user sessions

---

## Multi-Factor Authentication (MFA)

### MFA Requirement

**Mandatory for:**
- All `case_admin`, `analyst`, `supervisor`, `system_admin` roles
- Any user accessing >1 case
- Optional for single-case `family_member` (encouraged)

**MFA Methods (in order of preference):**
1. **TOTP (Time-based One-Time Password)** — Google Authenticator, Authy
2. **SMS** — Fallback only (less secure due to SIM swapping)
3. **Email OTP** — Fallback for users without smartphones
4. **Hardware token** — YubiKey for high-security users

**Recovery codes:**
- 10 single-use backup codes generated at MFA enrollment
- Stored encrypted, can be regenerated once

### MFA Flow

```
User enters password → Auth0 validates → Prompt for TOTP code → Validate code → Issue tokens
```

**Bypass prevention:**
- MFA status checked on every login
- Cannot disable MFA without current TOTP code
- Admin-forced MFA re-enrollment if suspicious activity

---

## Privacy Enhancements

### Data Minimization

**Collect only what's necessary:**
- ❌ Don't collect: SSN, passport numbers, exact birth dates
- ✅ Collect: Name, email, approximate age ("born ~1950")
- ✅ Infer: Relationships from documents, not surveys

### Anonymization Options

**For politically sensitive cases:**
- Pseudonymize family names in UI ("Family A", "Family B")
- Hash document IDs (not sequential)
- Redact living persons' names by default
- Allow case-level privacy settings

### GDPR/CCPA Compliance (Future)

Even though clients are primarily US-based, best practices:
- **Right to access**: Export all user data as JSON
- **Right to deletion**: Soft-delete user account, anonymize logs
- **Right to portability**: Download case data as structured JSON
- **Consent management**: Explicit opt-in for analytics

---

## Infrastructure Security

### Zone A (Factory)

**Isolation:**
- No public internet access
- No SSH from public IP (bastion host only)
- Private VPC with firewall rules

**Access control:**
- Analysts use VPN + MFA to access
- All commands logged (bash history, process accounting)
- Separate service accounts for each analyst

**Document storage:**
- Encrypted local disk or private S3 bucket
- Backups encrypted with different key than production
- 3-2-1 backup rule: 3 copies, 2 media types, 1 offsite

### Zone B (Vault)

**Hosting:** Vercel Enterprise (SOC 2 Type II compliant)

**Database:** Supabase (Postgres with built-in RLS)

**CDN:** Cloudflare (DDoS protection, WAF)

**Secrets management:**
- Never commit secrets to git
- Use Vercel environment variables (encrypted at rest)
- Rotate API keys quarterly
- Separate keys for dev/staging/production

---

## Incident Response Plan

### Detection

**Monitoring for:**
- Failed login attempts (>5 in 10 minutes)
- Bulk document downloads (>10 documents in 1 hour)
- Access from new locations/devices
- Changes to user roles
- Database query anomalies (e.g., full table scans)

**Alerting:**
- Real-time alerts to security team via PagerDuty/Slack
- Weekly security digest to stakeholders

### Response Procedures

| Severity | Incident Type | Response Time | Actions |
|----------|---------------|---------------|---------|
| **CRITICAL** | Data breach, unauthorized access | 1 hour | Revoke all sessions, disable affected accounts, notify users |
| **HIGH** | Suspicious activity, privilege escalation | 4 hours | Investigate, reset passwords, review logs |
| **MEDIUM** | Unusual access patterns | 24 hours | Monitor, contact user to verify |
| **LOW** | Failed login attempts | 7 days | Log, no immediate action |

### Breach Notification

**Legal requirements:**
- Notify affected users within 72 hours (GDPR)
- Notify regulatory bodies if required
- Document timeline, scope, remediation

**Communication plan:**
- Email to affected users (encrypted)
- Public statement on website (if widespread)
- Offer credit monitoring if PII exposed

---

## Development & Deployment Security

### Secure Development Lifecycle

**Code review:**
- All code reviewed by 2+ developers
- Security-focused review for auth/encryption code
- Automated security scanning (Snyk, Dependabot)

**Dependency management:**
- Pin exact versions in package.json/requirements.txt
- Audit dependencies monthly for vulnerabilities
- Avoid unmaintained packages

**Secrets in code:**
- Pre-commit hook blocks API keys in git
- Use environment variables, never hardcode
- Scan git history for leaked secrets (gitleaks)

### CI/CD Pipeline

**Security gates:**
1. **Lint + type check** → Fail if errors
2. **Dependency scan** → Fail if critical vulnerabilities
3. **Unit tests** → Fail if <80% coverage
4. **Integration tests** → Fail if auth bypass possible
5. **Deploy to staging** → Manual QA
6. **Deploy to production** → Require approval from 2 admins

**Deployment:**
- Zero-downtime deployments (blue-green)
- Automatic rollback if health checks fail
- Immutable infrastructure (no SSH to production)

---

## Compliance & Certifications

### Current Status (MVP1)

- [x] HTTPS/TLS 1.3
- [x] Password hashing (bcrypt)
- [ ] OAuth 2.0 with MFA
- [ ] Encryption at rest
- [ ] Audit logging
- [ ] SOC 2 Type II hosting

### Roadmap (MVP2+)

- [ ] **SOC 2 Type II** certification for platform (18 months)
- [ ] **ISO 27001** compliance (24 months)
- [ ] **HIPAA** compliance if expanding to medical records
- [ ] **Legal hold** capability for litigation

---

## Security Checklist for Launch

### Pre-Production

- [ ] All API keys rotated, production keys separate from dev
- [ ] Auth0 production tenant configured with MFA enforced
- [ ] Database RLS policies tested (cannot access other cases)
- [ ] TLS certificate valid, HSTS enabled
- [ ] CSP headers prevent XSS
- [ ] Rate limiting configured (100 req/min per user)
- [ ] Audit logging tested, logs flowing to monitoring
- [ ] Backup/restore tested, encrypted backups verified
- [ ] Incident response plan documented, team trained

### Post-Production (First 30 Days)

- [ ] Monitor failed login attempts, investigate anomalies
- [ ] Review audit logs weekly
- [ ] User feedback on security/privacy concerns
- [ ] Penetration test by third party (recommended)
- [ ] Bug bounty program (HackerOne) if budget allows

---

## Implementation Guide: Clerk + Next.js + Supabase

### Step-by-Step Setup (MVP1.5)

**Timeline:** 2-3 weeks before launch

#### 1. Set Up Clerk (2 days)

**1.1 Create Clerk account and application**
```bash
# Visit https://clerk.com and create account
# Create new application: "Farmer House Vault"
# Choose: Email, Google, Apple as authentication methods
# Enable MFA in settings → Authentication → Multi-factor
```

**1.2 Install Clerk in Next.js**
```bash
cd farmer_vault
npm install @clerk/nextjs
```

**1.3 Configure environment variables**
```bash
# .env.local
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/onboarding
```

**1.4 Add middleware (protects all routes by default)**
```typescript
// middleware.ts
import { authMiddleware } from "@clerk/nextjs";

export default authMiddleware({
  publicRoutes: ["/", "/sign-in", "/sign-up"],
  ignoredRoutes: ["/api/webhook"]
});

export const config = {
  matcher: ["/((?!.+\\.[\\w]+$|_next).*)", "/", "/(api|trpc)(.*)"],
};
```

**1.5 Wrap app with ClerkProvider**
```typescript
// app/layout.tsx
import { ClerkProvider } from '@clerk/nextjs'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body>{children}</body>
      </html>
    </ClerkProvider>
  )
}
```

**1.6 Add sign-in page**
```typescript
// app/sign-in/[[...sign-in]]/page.tsx
import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-900">
      <SignIn />
    </div>
  );
}
```

**Acceptance Criteria:**
- ✅ Visiting /case/123 redirects to sign-in
- ✅ Sign up flow works (email verification)
- ✅ MFA enrollment prompt after first login
- ✅ Session persists across page refreshes

---

#### 2. Integrate Clerk with Supabase RLS (3 days)

**2.1 Sync Clerk users to Supabase**

Create webhook endpoint to sync user creation:

```typescript
// app/api/webhook/clerk/route.ts
import { Webhook } from 'svix'
import { headers } from 'next/headers'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY! // Admin key, bypasses RLS
)

export async function POST(req: Request) {
  const WEBHOOK_SECRET = process.env.CLERK_WEBHOOK_SECRET

  const headerPayload = headers()
  const svix_id = headerPayload.get("svix-id")
  const svix_timestamp = headerPayload.get("svix-timestamp")
  const svix_signature = headerPayload.get("svix-signature")

  const payload = await req.json()
  const body = JSON.stringify(payload)

  const wh = new Webhook(WEBHOOK_SECRET!)
  let evt: any

  try {
    evt = wh.verify(body, {
      "svix-id": svix_id!,
      "svix-timestamp": svix_timestamp!,
      "svix-signature": svix_signature!,
    })
  } catch (err) {
    return new Response('Webhook verification failed', { status: 400 })
  }

  // Handle user.created event
  if (evt.type === 'user.created') {
    const { id, email_addresses, first_name, last_name } = evt.data

    await supabase.from('users').insert({
      clerk_id: id,
      email: email_addresses[0].email_address,
      first_name,
      last_name,
      role: 'family_member' // Default role
    })
  }

  return new Response('Webhook processed', { status: 200 })
}
```

**2.2 Configure webhook in Clerk dashboard**
- Go to Clerk Dashboard → Webhooks
- Add endpoint: `https://yourdomain.com/api/webhook/clerk`
- Subscribe to: `user.created`, `user.updated`, `user.deleted`

**2.3 Create Supabase schema with RLS**

```sql
-- Users table (synced from Clerk)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_id TEXT UNIQUE NOT NULL,
  email TEXT NOT NULL,
  first_name TEXT,
  last_name TEXT,
  role TEXT NOT NULL DEFAULT 'family_member' CHECK (role IN ('family_member', 'case_admin', 'analyst', 'supervisor', 'system_admin')),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Cases table
CREATE TABLE cases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  family_name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Case access (who can see which cases)
CREATE TABLE case_access (
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
  permission TEXT NOT NULL CHECK (permission IN ('read', 'write', 'admin')),
  granted_by UUID REFERENCES users(id),
  granted_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (user_id, case_id)
);

-- Enable RLS on cases
ALTER TABLE cases ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see cases they have access to
CREATE POLICY "Users can view their assigned cases"
  ON cases FOR SELECT
  USING (
    -- User has explicit access
    id IN (
      SELECT case_id FROM case_access
      WHERE user_id = (SELECT id FROM users WHERE clerk_id = auth.jwt() ->> 'sub')
    )
    OR
    -- User is supervisor/admin (can see all)
    EXISTS (
      SELECT 1 FROM users
      WHERE clerk_id = auth.jwt() ->> 'sub'
      AND role IN ('supervisor', 'system_admin')
    )
  );
```

**2.4 Get Clerk user ID in API routes**

```typescript
// app/api/cases/route.ts
import { auth } from '@clerk/nextjs'
import { createClient } from '@supabase/supabase-js'

export async function GET() {
  const { userId } = auth() // Clerk user ID

  if (!userId) {
    return new Response('Unauthorized', { status: 401 })
  }

  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  )

  // RLS will automatically filter to only cases this user can access
  const { data, error } = await supabase
    .from('cases')
    .select('*')
    .eq('user_clerk_id', userId) // Or use the RLS policy

  return Response.json(data)
}
```

**2.5 Map Python endpoint errors to HTTP status codes**

When a Python endpoint returns a payload with `status_code`, map it to the
HTTP response status in your Next.js route.

```typescript
// Example: app/api/cases/[id]/dossier/route.ts
import { NextRequest } from 'next/server'

export async function POST(req: NextRequest, { params }: { params: { id: string } }) {
  const body = await req.json()
  const result = await callFactory(params.id, body)

  if (result?.status_code) {
    return Response.json(result, { status: result.status_code })
  }

  return Response.json(result, { status: 200 })
}
```

> **Note:** Narrative generation no longer uses an API endpoint. It runs as a
> batch step during Factory processing, producing `case_narrative.json` which
> the Vault reads as a static file.

**Acceptance Criteria:**
- ✅ New Clerk users auto-sync to Supabase
- ✅ User A cannot query user B's cases (tested with SQL)
- ✅ Roles properly restrict access
- ✅ Webhook processes within 5 seconds

---

#### 3. Enable HTTPS/TLS (1 day)

**On Vercel (automatic):**
- TLS 1.3 enabled by default
- Free SSL certificate from Let's Encrypt

**Add security headers:**
```typescript
// next.config.js
module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          {
            key: 'Content-Security-Policy',
            value: "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://clerk.com https://*.clerk.accounts.dev; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://*.supabase.co https://clerk.com https://*.clerk.accounts.dev"
          }
        ]
      }
    ]
  }
}
```

**Acceptance Criteria:**
- ✅ Site loads over HTTPS
- ✅ Security headers present (check with securityheaders.com)
- ✅ No mixed content warnings

---

#### 4. Implement Audit Logging (2 days)

**4.1 Create audit log table**

```sql
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  timestamp TIMESTAMPTZ DEFAULT now(),
  event_type TEXT NOT NULL,
  user_id UUID REFERENCES users(id),
  clerk_id TEXT,
  case_id UUID REFERENCES cases(id),
  document_id TEXT,
  ip_address INET,
  user_agent TEXT,
  result TEXT NOT NULL CHECK (result IN ('SUCCESS', 'FAILURE')),
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Index for fast lookups
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_case_id ON audit_logs(case_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);

-- RLS: Users can only see their own audit logs
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own audit logs"
  ON audit_logs FOR SELECT
  USING (
    clerk_id = auth.jwt() ->> 'sub'
    OR
    EXISTS (
      SELECT 1 FROM users
      WHERE clerk_id = auth.jwt() ->> 'sub'
      AND role IN ('supervisor', 'system_admin')
    )
  );
```

**4.2 Create logging utility**

```typescript
// lib/audit.ts
import { createClient } from '@supabase/supabase-js'
import { headers } from 'next/headers'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function logAudit({
  eventType,
  clerkId,
  caseId,
  documentId,
  result,
  metadata
}: {
  eventType: string
  clerkId: string
  caseId?: string
  documentId?: string
  result: 'SUCCESS' | 'FAILURE'
  metadata?: any
}) {
  const headersList = headers()
  const ip = headersList.get('x-forwarded-for') || headersList.get('x-real-ip')
  const userAgent = headersList.get('user-agent')

  await supabase.from('audit_logs').insert({
    event_type: eventType,
    clerk_id: clerkId,
    case_id: caseId,
    document_id: documentId,
    ip_address: ip,
    user_agent: userAgent,
    result,
    metadata
  })
}
```

**4.3 Use in API routes**

```typescript
// app/api/cases/[id]/documents/[docId]/route.ts
import { auth } from '@clerk/nextjs'
import { logAudit } from '@/lib/audit'

export async function GET(
  req: Request,
  { params }: { params: { id: string; docId: string } }
) {
  const { userId } = auth()

  if (!userId) {
    await logAudit({
      eventType: 'DOCUMENT_VIEW_FAILED',
      clerkId: 'anonymous',
      caseId: params.id,
      documentId: params.docId,
      result: 'FAILURE',
      metadata: { reason: 'Not authenticated' }
    })
    return new Response('Unauthorized', { status: 401 })
  }

  // Fetch document...

  await logAudit({
    eventType: 'DOCUMENT_VIEWED',
    clerkId: userId,
    caseId: params.id,
    documentId: params.docId,
    result: 'SUCCESS'
  })

  return Response.json(document)
}
```

**Acceptance Criteria:**
- ✅ All document views logged
- ✅ Failed login attempts logged
- ✅ Logs queryable by admin
- ✅ Logs include IP and user agent

---

#### 5. Verify Encryption at Rest (1 day)

**Supabase:**
- Database encryption: ✅ Enabled by default (AES-256)
- Backups: ✅ Encrypted automatically

**Verify:**
```bash
# Check Supabase dashboard → Settings → General
# Look for "Encryption at rest: Enabled"
```

**Acceptance Criteria:**
- ✅ Database shows encryption enabled
- ✅ Backups are encrypted
- ✅ API keys stored in Vercel env vars (encrypted)

---

**Total Implementation Time:** ~10 days

**Cost:** $0/month (all free tiers)

---

## Cost Estimates

### MVP1 (Free Tier)

| Service | Plan | Monthly Cost | Limits |
|---------|------|--------------|--------|
| **Clerk** | Free | $0 | 10,000 MAU, MFA included |
| **Supabase** | Free | $0 | 500 MB database, 1 GB storage, 2 GB bandwidth |
| **Vercel** | Hobby | $0 | 100 GB bandwidth, serverless functions |
| **Cloudflare** | Free | $0 | WAF, CDN, basic DDoS |
| **Total** | | **$0/month** | Sufficient for MVP1 testing |

**Note:** Free tier sufficient for:
- Initial family testing (10-50 users)
- 300 documents processed
- Development and staging environments

### Production Scale (~100 users)

| Service | Plan | Monthly Cost | Notes |
|---------|------|--------------|-------|
| **Clerk** | Free | $0 | Still within 10k MAU limit |
| **Supabase** | Pro | $25 | 8 GB database, 100 GB storage |
| **Vercel** | Pro | $20 | DDoS protection, analytics, priority support |
| **Cloudflare** | Free | $0 | WAF, CDN sufficient for this scale |
| **Total** | | **$45/month** | For <100 active families |

### Enterprise Scale (1,000+ users)

| Service | Plan | Monthly Cost |
|---------|------|--------------|
| **Clerk** | Pro (10k+ MAU) | $25/month + $0.02/MAU |
| **Supabase** | Pro (larger) | $100 |
| **Vercel** | Pro | $20 |
| **Total** | | **~$165/month** (1,000 users) |

**Much cheaper than Auth0 at scale due to Clerk's generous free tier and linear pricing.**

---

## Alternative Approaches Considered

### Option A: Supabase Auth (DIY)

**Pros:**
- Fully free
- Integrated with database
- MFA available (TOTP)

**Cons:**
- More implementation work (UI, session management)
- Less polished user experience
- Manual webhook setup for user sync

**Verdict:** Not worth the saved $0 given Clerk is also free

### Option B: NextAuth.js (Open source)

**Pros:**
- Open source, no vendor lock-in
- Flexible, supports many providers
- Free forever

**Cons:**
- Must build MFA yourself
- Session management complexity
- No built-in user management UI

**Verdict:** Too much work for MVP1

### Option C: Auth0

**Pros:**
- Enterprise-grade
- Very mature ecosystem

**Cons:**
- MFA requires paid plan ($228/month minimum)
- Overkill for initial scale
- More expensive at scale

**Verdict:** Great for enterprise, but Clerk better for startups

### Final Decision: Clerk

**Reasoning:**
- ✅ Free tier is generous (10k MAU)
- ✅ MFA included at no cost
- ✅ Purpose-built for Next.js
- ✅ Professional UI out of the box
- ✅ Less implementation work = faster to market
- ✅ Easy migration to paid tier when needed

---

*This document defines the security posture for the Farmer House Forensic Intelligence Platform. All implementation must adhere to these guidelines. Security is not optional.*

---

## Security Review Findings (2026-01-28)

This section documents findings from the comprehensive security review conducted on the codebase.

### Vulnerabilities Identified and Fixed

#### 1. Path Traversal Vulnerability in Python Backend (FIXED)

**Severity:** HIGH

**Description:**
Multiple Python modules constructed file paths by directly interpolating user-supplied `case_id` values without validation. This could allow an attacker to access files outside the intended `cases/` directory by supplying malicious case IDs like `../etc/passwd`.

**Affected Files:**
- `farmer_factory/api/narrative.py` (removed — narrative is now batch-generated)
- `farmer_factory/scripts/generate_narrative.py` (removed — replaced by CLI command)
- `farmer_factory/dossier/__init__.py`
- `farmer_factory/dossier/preparer.py`

**Fix Applied:**
Created `farmer_factory/utils/__init__.py` with validation functions:
- `validate_case_id(case_id)` - Returns True/False for valid alphanumeric case IDs
- `get_safe_case_path(case_id, base_dir)` - Returns validated Path or raises ValueError
- `CASE_ID_PATTERN` - Regex pattern `^[A-Za-z0-9_-]+$` for validation

All affected modules now validate case_id before constructing paths:

```python
from farmer_factory.utils import validate_case_id

if not validate_case_id(case_id):
    raise ValueError(f"Invalid case_id: {case_id}")
```

**Note:** The TypeScript API routes in `farmer_vault/` already had this protection via `CASE_ID_PATTERN` regex validation and `path.resolve()` checks. The Python backend now has equivalent defense-in-depth protection.

#### 2. DOM-based XSS Vulnerability in viewer.html (FIXED)

**Severity:** MEDIUM

**Description:**
The `viewer.html` file used `innerHTML` to render entity data from `graph_data.json` without HTML escaping. If an attacker could inject malicious content into the graph data (e.g., through a compromised LLM extraction), it could execute arbitrary JavaScript.

**Location:** `viewer.html` - `showPanel()` function

**Fix Applied:**
- Added `escapeHtml()` function using DOM-based encoding
- All user-controlled values are now escaped before rendering
- Entity types and verification tiers are validated against allowlists
- CSS class names are sanitized to only allow alphanumeric characters

```javascript
function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    const str = String(text);
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
```

### Security Patterns Already Present

The codebase already implements several security best practices:

1. **TypeScript API Route Input Validation:**
   - All routes validate `caseId`, `docId`, `entityId` with regex patterns
   - Path resolution checks prevent directory traversal
   - Example from `farmer_vault/app/api/cases/[caseId]/graph/route.ts`

2. **Parameterized Claude API Calls:**
   - The `ClaudeAPIClient` uses the official Anthropic SDK
   - No string interpolation in API parameters

3. **Subprocess Safety:**
   - `compiler.py` validates LaTeX engine against a fixed allowlist
   - No shell=True or user-controlled command arguments

4. **No SQL Injection Vectors:**
   - No raw SQL with string interpolation found
   - Future Supabase integration should use parameterized queries

5. **Secrets Management:**
   - API keys loaded from environment variables
   - `.env.example` documents required secrets without values
   - No hardcoded credentials in codebase

### Recommendations for Future Development

#### Immediate (Before Production)

1. **Implement Authentication:** Deploy Clerk authentication as documented in this file
2. **Add Rate Limiting:** Implement rate limiting on all API endpoints
3. **Enable Security Headers:** Add CSP, HSTS, X-Frame-Options headers to Next.js config
4. **Audit Logging:** Implement audit logs for document access

#### Short-term

1. **Input Validation Schema:** Consider using Zod for runtime validation of API inputs
2. **Dependency Auditing:** Set up automated dependency scanning (Dependabot/Snyk)
3. **Penetration Testing:** Conduct third-party security assessment before launch

#### Long-term

1. **SOC 2 Compliance:** Document and implement controls for certification
2. **Bug Bounty Program:** Consider HackerOne program post-launch
3. **Security Training:** Ensure all developers complete secure coding training
