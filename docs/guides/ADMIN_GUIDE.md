# Admin Operational Guide — Civic Table Platform

> **Document Classification:** Internal Operations Manual
> **Version:** 1.0.0
> **Created:** 2026-01-22
> **Audience:** Platform Administrators

---

## Overview

This guide covers all operational procedures for administering the Civic Table platform. Admins are responsible for case creation, document processing, user management, and system maintenance.

**Prerequisites:**
- Access to Factory CLI (local Python environment)
- Supabase project access (admin credentials)
- Clerk dashboard access
- Vercel deployment access

---

## Case Management

### Create New Case

**When:** Starting a new family's documentary analysis

**Prerequisites:**
- Family has signed service agreement
- Source documents collected (PDFs)

**Steps:**

1. **Create case directory structure:**
   ```bash
   python -m farmer_factory.cli create-case \
     --id CASE-001 \
     --name "Ceresa Family Archive" \
     --family "Ceresa" \
     --domain cuban_property
   ```

   This creates:
   ```
   cases/
   └── CASE-001/
       ├── intake/         # Source PDFs go here
       ├── preprocessed/   # Processed images (auto-generated)
       ├── ocr/            # OCR outputs (auto-generated)
       └── output/         # Final graph_data.json
   ```

2. **Copy source documents:**
   ```bash
   cp ~/family_documents/*.pdf ./cases/CASE-001/intake/
   ```

   **Important:**
   - Keep originals in separate backup location
   - Source PDFs are NEVER modified
   - Verify file count matches manifest

3. **Create case record in Supabase:**
   ```sql
   -- Via Supabase SQL Editor
   INSERT INTO cases (id, title, family_name, status, created_at)
   VALUES (
     'CASE-001',
     'Ceresa Family Archive',
     'Ceresa',
     'INTAKE',
     now()
   );
   ```

**Expected Result:**
- Case directory exists with intake folder populated
- Case record exists in database
- Status = "INTAKE"

---

### Process Case Documents

**When:** After case creation and PDF upload

**Prerequisites:**
- Case exists in system
- PDFs in `cases/CASE-ID/intake/`
- Google Cloud Vision credentials configured (GOOGLE_APPLICATION_CREDENTIALS)
- Anthropic API key configured (ANTHROPIC_API_KEY)

**Steps:**

1. **Detect document groups (if needed):**
   ```bash
   python -m farmer_factory.cli detect-groups CASE-001
   ```

   **What this does:**
   - Scans intake PDFs for multi-part patterns (e.g., deed.pdf, deed.1pdf.pdf)
   - Generates `document_groups.yaml` for review
   - Must be confirmed before processing (see Analyst Guide)

2. **Run full processing pipeline:**
   ```bash
   python -m farmer_factory.cli process CASE-001
   ```

   **What this does:**
   - Converts PDFs to images (300 DPI grayscale)
   - Preprocesses images (deskew, denoise)
   - Runs OCR via Google Cloud Vision
   - Extracts entities and relations via Claude API
   - Builds knowledge graph with deduplication
   - Exports to `graph_data.json`

   **Options:**
   - `--verbose` - Enable debug logging
   - `--force-typed` - Skip handwritten triage (OCR all pages)
   - `--skip-validation` - Skip graph validation
   - `--file document.pdf` - Process single PDF only

   **Expected time:** ~3-5 minutes per document

3. **Validate output:**
   ```bash
   python -m farmer_factory.cli validate CASE-001
   ```

   **What this does:**
   - Validates graph_data.json against schema
   - Checks entity/relation types against domain config
   - Reports validation errors

**Expected Result:**
- `cases/CASE-001/output/graph_data.json` exists
- Validation passes
- Processing stats logged to console

---

### Upload Graph to Supabase

**When:** After successful processing and validation

> **Note:** The `upload` command is planned but not yet implemented. Currently, graphs are served directly from the local file system.

**Future Steps (Once Implemented):**

1. **Upload to Supabase Storage:**
   ```bash
   python -m farmer_factory.cli upload CASE-001
   ```

   **What this does:**
   - Uploads graph_data.json to Supabase Storage bucket `case-graphs`
   - Path: `case-graphs/CASE-001/graph_data.json`
   - Sets proper content-type and permissions

2. **Update case status:**
   ```sql
   UPDATE cases
   SET status = 'READY', updated_at = now()
   WHERE id = 'CASE-001';
   ```

3. **Verify upload:**
   - Visit Supabase Dashboard → Storage → case-graphs
   - Confirm CASE-001/graph_data.json exists
   - Check file size matches local file

**Expected Result:**
- Graph accessible via Vault API
- Case status = "READY"
- Family can now view dossier

---

## User Management

### Invite Family Member (Primary Contact)

**When:** After case is READY

**Prerequisites:**
- Case uploaded to Supabase
- Family contact email verified

**Steps:**

1. **Send Clerk invitation:**
   - Visit https://dashboard.clerk.com
   - Navigate to Users → Invitations
   - Click "New Invitation"
   - Enter email address
   - Set redirect URL: `https://civictable.com/case/CASE-001`
   - Click Send

2. **User signs up:**
   - Family receives email
   - Clicks invitation link
   - Creates account (password + MFA)
   - Clerk webhook syncs user to Supabase

3. **Verify user sync:**
   ```sql
   SELECT * FROM users WHERE email = 'family@example.com';
   ```

   Should return:
   - `clerk_id`: Populated
   - `role`: 'family_member'
   - `created_at`: Recent timestamp

4. **Assign user to case:**
   ```sql
   INSERT INTO case_access (user_id, case_id, permission)
   VALUES (
     (SELECT id FROM users WHERE email = 'family@example.com'),
     'CASE-001',
     'read'
   );
   ```

5. **Test access:**
   - Log in as family member
   - Navigate to /case/CASE-001
   - Verify graph loads
   - Verify RLS prevents access to other cases

**Expected Result:**
- Family member can view their case
- Cannot view other cases
- MFA enforced on login

---

### Invite Additional Family Members

**When:** Primary contact wants to share with family

**Steps:**

1. **Get approval from primary contact**
   - Confirm via email/phone
   - Document approval

2. **Send Clerk invitation** (same as above)

3. **Assign same case access:**
   ```sql
   INSERT INTO case_access (user_id, case_id, permission)
   VALUES (
     (SELECT id FROM users WHERE email = 'relative@example.com'),
     'CASE-001',
     'read'
   );
   ```

**Best Practice:**
- Limit to 5-10 family members per case
- All family members have 'read' permission only
- Primary contact can be upgraded to 'case_admin' if needed

---

### Grant Analyst Access

**When:** Assigning analyst to verify case data

**Prerequisites:**
- Analyst has Clerk account
- Analyst employed by Civic Table

**Steps:**

1. **Update user role:**
   ```sql
   UPDATE users
   SET role = 'analyst'
   WHERE email = 'analyst@civictable.com';
   ```

2. **Assign to case:**
   ```sql
   INSERT INTO case_access (user_id, case_id, permission)
   VALUES (
     (SELECT id FROM users WHERE email = 'analyst@civictable.com'),
     'CASE-001',
     'write'
   );
   ```

3. **Verify analyst can access:**
   - Analyst logs in
   - Sees CASE-001 in dashboard
   - Can view AnalystReviewPanel component
   - Can promote entities to TIER_2_ANALYST

**Expected Result:**
- Analyst can verify entities
- Families see verification badges update in real-time

---

## Troubleshooting

### Problem: Processing Fails on Document

**Symptoms:**
- `python -m farmer_factory.cli process CASE-001` exits with error
- Processing stops mid-pipeline

**Diagnosis:**
```bash
# Check specific document with verbose output
python -m farmer_factory.cli process CASE-001 --file problem_document.pdf --verbose
```

**Common Causes:**

1. **Corrupt PDF:**
   - Try opening PDF manually
   - Re-scan if needed

2. **OCR API Rate Limit:**
   - Wait 60 seconds
   - Re-run processing

3. **Claude API Timeout:**
   - Check Anthropic status page
   - Retry failed relations: `python -m farmer_factory.cli retry-relations CASE-001`

4. **Low Confidence Score:**
   - Review extraction JSONs in `cases/CASE-001/extractions/`
   - Flag for manual review
   - Continue processing other documents

---

### Problem: User Cannot Access Case

**Symptoms:**
- User logs in successfully
- Gets 403 error on /case/CASE-001

**Diagnosis:**
```sql
-- Check user exists
SELECT * FROM users WHERE email = 'user@example.com';

-- Check case access
SELECT * FROM case_access WHERE user_id = (
  SELECT id FROM users WHERE email = 'user@example.com'
);
```

**Fixes:**

1. **User not assigned to case:**
   ```sql
   INSERT INTO case_access (user_id, case_id, permission)
   VALUES (...);
   ```

2. **RLS policy blocking:**
   - Check Supabase RLS policies
   - Verify user's clerk_id matches

3. **Case not uploaded:**
   - Check that graph_data.json exists locally
   - For now, use local file serving (upload not yet implemented)

---

### Problem: Graph Doesn't Load in Vault

**Symptoms:**
- Blank screen or loading spinner
- Console errors

**Diagnosis:**
1. Open browser DevTools → Network tab
2. Check API request to `/api/cases/CASE-001/graph`
3. Look for 404, 403, or 500 errors

**Fixes:**

1. **404 - File not found:**
   - Verify `cases/CASE-001/output/graph_data.json` exists
   - Re-run processing if needed

2. **403 - Permission denied:**
   - Check case_access table
   - Verify RLS policy

3. **500 - Server error:**
   - Check Vercel logs
   - Check for JSON parse errors in graph_data.json
   - Validate with: `python -m farmer_factory.cli validate CASE-001`

---

## Monitoring & Maintenance

### Daily Checks

- [ ] Check Supabase storage usage (alert at 80%)
- [ ] Review audit logs for errors
- [ ] Check API cost (should be <$5/day)
- [ ] Verify backups ran successfully

### Weekly Checks

- [ ] Review failed jobs queue
- [ ] Test user onboarding flow
- [ ] Check Clerk billing (MAU count)
- [ ] Review security alerts (Vercel dashboard)

### Monthly Checks

- [ ] Rotate API keys (if policy requires)
- [ ] Review case processing metrics
- [ ] Test disaster recovery (restore from backup)
- [ ] Update dependencies (security patches)

---

## Backup & Recovery

### Manual Backup

```bash
# Backup all cases
./scripts/backup.sh

# Backup specific case
rsync -av ./cases/CASE-001/ ./backups/$(date +%Y-%m-%d)/CASE-001/
```

### Restore from Backup

```bash
# Restore case from a previous backup
rsync -av ./backups/2026-01-15/CASE-001/ ./cases/CASE-001/
```

---

## Emergency Procedures

### Data Breach Response

1. **Immediately revoke all user sessions:**
   - Clerk Dashboard → Sessions → Revoke All

2. **Disable public access:**
   - Vercel Dashboard → Deployment → Set to Maintenance Mode

3. **Notify users:**
   - Use email template in `templates/breach_notification.md`

4. **Document timeline:**
   - What happened, when, who was affected
   - Report to stakeholders within 24 hours

### System Down Response

1. **Check Vercel status:**
   - https://vercel.com/status

2. **Check Supabase status:**
   - https://status.supabase.com

3. **If Factory down:**
   - Processing can wait, not customer-facing

4. **If Vault down:**
   - Notify families via email
   - Provide ETA if known

---

## Quick Reference Commands

```bash
# Case creation
python -m farmer_factory.cli create-case --id CASE-XXX --name "Name" --family "Family" --domain cuban_property

# Detect document groups
python -m farmer_factory.cli detect-groups CASE-XXX

# Process case
python -m farmer_factory.cli process CASE-XXX

# Process with options
python -m farmer_factory.cli process CASE-XXX --verbose --force-typed

# Validate output
python -m farmer_factory.cli validate CASE-XXX

# Retry failed relations
python -m farmer_factory.cli retry-relations CASE-XXX --verbose

# List cases
python -m farmer_factory.cli list-cases

# List entities in a case
python -m farmer_factory.cli list-entities CASE-XXX --type PERSON

# List available domains
python -m farmer_factory.cli list-domains

# Generate dossier PDF
python -m farmer_factory.cli generate-dossier CASE-XXX --property-id "ID" --family-member-id "ID"

# Clean case outputs
python -m farmer_factory.cli clean CASE-XXX --confirm
```

---

## Contact & Support

**Platform Issues:**
- Email: admin@civictable.com
- Slack: #platform-support

**API Issues:**
- Google Cloud Vision: Check GCP console
- Anthropic: support@anthropic.com
- Clerk: support@clerk.com
- Supabase: support@supabase.com

---

*This guide should be updated as operational procedures evolve. Last reviewed: 2026-01-28*
