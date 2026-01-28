# Analyst Verification Guide — Civic Table Platform

> **Document Classification:** Internal Operations Manual
> **Version:** 1.3.0
> **Created:** 2025-01-22
> **Last Updated:** 2026-01-27
> **Audience:** Civic Table Analysts

---

## Overview

This guide covers verification procedures for promoting entities from **TIER_3_AI** (AI-extracted, unverified) to **TIER_2_ANALYST** (human analyst confirmed).

**Your Role:**
- Review AI-extracted entities for accuracy
- Verify against source documents
- Promote verified entities to TIER_2_ANALYST
- Flag problematic extractions for correction
- Maintain verification quality standards

**DO NOT:**
- Make legal conclusions ("This proves ownership")
- Provide legal advice to families
- Promise legal outcomes
- Modify source documents

---

## Verification Tiers Explained

| Tier | Label | Your Responsibility |
|------|-------|---------------------|
| `TIER_3_AI` | AI Extracted | **Review and verify these** |
| `TIER_2_ANALYST` | Analyst Verified | **You create these by verifying TIER_3_AI** |
| `TIER_2_INSTITUTIONAL` | Farmer House Verified | Not your responsibility (external partner) |
| `TIER_1_CERTIFIED` | Legally Certified | Not your responsibility (external legal bodies) |

**Your Goal:** Convert as many TIER_3_AI entities as possible to TIER_2_ANALYST while maintaining high accuracy.

---

## Document Intake Workflow

Before verification can begin, documents must be loaded and processed. This section covers your role in preparing documents for processing.

### Step 1: Load Documents into Intake

1. **Receive documents from client:**
   - Usually via Google Drive or secure file share
   - Documents are scanned PDFs of historical records

2. **Copy PDFs to case intake folder:**
   ```
   cases/CASE-ID/intake/
   ├── escritura_125_1.pdf
   ├── escritura_125_2.pdf
   ├── testamento.pdf
   └── ...all PDFs here...
   ```

3. **Verify all expected documents are present**
   - Check against client's document list
   - Note any missing items

---

### Step 2: Detect Document Groups

**Why this matters:** Clients often scan multi-page documents as separate PDFs (e.g., `deed_1.pdf`, `deed_2.pdf`, `deed_3.pdf`). These need to be treated as ONE logical document for proper evidence tracking.

**Run detection:**
```bash
python3 -m farmer_factory.cli detect-groups CASE-ID
```

**What happens:**
- Scans filenames for patterns like `name_1.pdf`, `name_2.pdf`
- Generates `cases/CASE-ID/document_groups.yaml` with suggested groupings
- Status is set to `DRAFT` (blocks processing until you confirm)

**Example output:**
```
Detected 2 document group(s):

  escritura_125:
    - escritura_125_1.pdf
    - escritura_125_2.pdf
    - escritura_125_3.pdf

  testamento:
    - testamento_a.pdf
    - testamento_b.pdf

4 standalone file(s)

Written to: cases/CASE-ID/document_groups.yaml (DRAFT)
```

---

### Step 3: Review & Confirm Groupings

**Open the generated YAML file:**
```yaml
status: DRAFT  # ← Change to CONFIRMED when done

groups:
  - id: escritura_125
    name: "escritura_125"  # ← Edit to be descriptive
    # document_type:  # ← Optional: notarial_deed, registry_certificate
    # date:  # ← Optional: YYYY-MM-DD
    files:
      - escritura_125_1.pdf
      - escritura_125_2.pdf
      - escritura_125_3.pdf

standalone:
  - random_letter.pdf
```

**Your review tasks:**

| Task | What to Check |
|------|---------------|
| **Verify groupings** | Are these files really parts of ONE document? |
| **Fix wrong groups** | Move files to `standalone` if wrongly grouped |
| **Add missing groups** | Manually add groups the auto-detect missed |
| **Edit names** | Change `"escritura_125"` to `"Escritura Pública No. 125"` |
| **Add metadata** | Add `document_type` and `date` if known |
| **Confirm** | Change `status: DRAFT` to `status: CONFIRMED` |

**Why confirmation is required:**
- Processing will be **blocked** if status is DRAFT
- This prevents accidental wrong groupings from corrupting the graph
- You are the quality gate

---

### Step 4: Process Documents

Once groupings are confirmed (or if no groupings needed):

```bash
python3 -m farmer_factory.cli process CASE-ID --force-typed --domain cuban_property
```

**What happens:**
- Each PDF is OCR'd and extracted separately
- Grouped files become ONE unified DOCUMENT entity
- All entities from grouped files reference the same document ID
- Graph is built with proper provenance

**After processing:**
- Review graph in Vault
- Begin verification workflow (next section)

---

### No Groupings Needed?

If auto-detect finds no groups and all files are standalone:
- You can delete `document_groups.yaml` entirely
- Or change status to `CONFIRMED` with empty groups
- Processing will proceed treating each PDF as separate document

```yaml
status: CONFIRMED
groups: []
standalone:
  - doc1.pdf
  - doc2.pdf
```

---

## Verification Workflow

### Step 1: Access Case for Review

1. **Log in to Civic Table Vault:**
   - Use your analyst credentials
   - MFA required

2. **Select case from dashboard:**
   - You'll see all cases assigned to you
   - Status shows "Awaiting Verification" if newly processed

3. **Open case:**
   - Click case title
   - Graph renders with entities colored by tier
   - Grey nodes = TIER_3_AI (need your review)
   - Gold nodes = Already verified

---

### Step 2: Review Entity

1. **Click on a TIER_3_AI node (grey):**
   - Dossier panel opens on right
   - Shows entity details:
    - Name
     - Type (PERSON, PROPERTY, etc.)
     - Confidence score
     - Source documents
     - Extracted text (OCR)

2. **Review source evidence:**
   - Click "View Source" button
   - Opens document viewer with OCR overlay
   - Verify entity name matches document
   - Check context (is it actually ownership, not just mention?)

3. **Check for hallucinations:**
   - Does entity exist in source document?
   - Is entity type correct? (Not confusing PERSON with ORGANIZATION)
   - Is date accurate?
   - Is location correct?

4. **Review confidence score:**
   - <50%: High risk, verify carefully
   - 50-70%: Medium confidence, cross-reference
   - 70-85%: Good confidence, spot-check
   - >85%: High confidence, quick review

---

### Step 3: Make Verification Decision

**Option A: VERIFY (Promote to TIER_2_ANALYST)**

**When to verify:**
- ✅ Entity clearly visible in source document
- ✅ Entity type is correct
- ✅ Name accurately transcribed
- ✅ Context supports the relation (if applicable)
- ✅ No conflicting information in other documents

**How to verify:**
1. Click "Verify" button in dossier panel
2. Add verification note (required):
   - What you checked
   - Why you're confident
   - Any caveats
3. Click "Confirm Verification"

**Example verification notes:**
- ✅ "Verified against property deed dated 1958-03-15. Name clearly legible."
- ✅ "Cross-referenced with 3 other documents, all confirm ownership."
- ✅ "OCR confidence 92%, manually spot-checked, accurate."

**Example BAD notes:**
- ❌ "Looks good" (too vague)
- ❌ "This proves ownership" (legal conclusion)
- ❌ "" (empty note)

---

**Option B: FLAG FOR REVIEW (Uncertain)**

**When to flag:**
- ⚠️ Confidence score <50%
- ⚠️ Entity partially visible (cut off in scan)
- ⚠️ Handwriting illegible
- ⚠️ Conflicting information in multiple documents
- ⚠️ Entity type ambiguous
- ⚠️ You're not sure

**How to flag:**
1. Click "Flag for Review" button
2. Select reason:
   - Low confidence
   - Illegible text
   - Conflict with other documents
   - Ambiguous entity type
   - Other (specify)
3. Add detailed note explaining issue
4. Click "Submit Flag"

**What happens:**
- Entity stays TIER_3_AI
- Flagged for senior analyst or manual research
- Family sees disclaimer on this node
- Admin notified to review

---

**Option C: REJECT (Incorrect Extraction)**

**When to reject:**
- ❌ Entity does not exist in source document (hallucination)
- ❌ Entity type completely wrong
- ❌ Name severely mis-transcribed
- ❌ Entity is duplicate of existing entity

**How to reject:**
1. Click "Reject" button
2. Select reason:
   - Hallucination (not in document)
   - Wrong entity type
   - Duplicate
   - Severe OCR error
3. Add note explaining why
4. Click "Confirm Rejection"

**What happens:**
- Entity removed from graph
- Logged in audit trail
- May trigger re-processing if systemic issue

---

### Step 4: Verify Relations (Links)

Relations connect entities (e.g., PERSON -[OWNS]-> PROPERTY).

**Review process:**
1. Click on link between nodes
2. Verify:
   - ✅ Relation type correct (OWNS vs INHERITED vs SOLD)
   - ✅ Direction correct (who owns what)
   - ✅ Source documents support relation
   - ✅ Date accurate (when ownership transferred)

3. Verify/Flag/Reject same as entities

**Common relation errors:**
- Wrong direction (PROPERTY -[OWNS]-> PERSON instead of reverse)
- Wrong type (INHERITED confused with PURCHASED)
- Inferred relation not supported by docs

---

## Quality Standards

### Precision > Recall

**Principle:** It's better to leave entities as TIER_3_AI than to incorrectly verify.

**Why:** Families rely on TIER_2_ANALYST for credibility. One incorrect verification undermines trust.

**Target Metrics:**
- **Precision:** ≥95% (95 out of 100 verified entities are correct)
- **Recall:** ≥70% (verify at least 70% of reviewable entities)

**Translation:** Verify confidently. When uncertain, flag for review.

---

### Documentation Requirements

**Every verification MUST have a note.**

**Minimum note quality:**
- Specific (not "looks good")
- References source document
- States what you verified
- Notes any caveats

**Examples:**

✅ **Good:**
> "Verified Mario Ceresa as property owner per deed dated 1958-03-15 (Doc-042, page 2). Signature matches. Cross-referenced with tax record (Doc-103) which corroborates ownership. No conflicts found."

❌ **Bad:**
> "Verified"

✅ **Good (with caveat):**
> "Verified Carlos Ceresa as person mentioned in confiscation decree (Doc-087, page 1). Note: Decree does not specify his role—may be owner, heir, or occupant. Recommend cross-reference with ownership docs."

❌ **Bad (legal conclusion):**
> "This document proves Carlos owned the property and has a valid claim."

---

## Special Cases

### Handwritten Documents

**Challenge:** OCR less reliable, more interpretation needed.

**Approach:**
1. Use document viewer to see original scan
2. Read handwriting yourself
3. Compare with OCR text
4. If you can read it clearly → Verify
5. If illegible → Flag for expert review
6. Add note: "Handwritten document, personally reviewed original scan"

**Never guess.** If you can't read it, flag it.

---

### Spanish Language Documents

**Challenge:** OCR may mis-transcribe Spanish characters (ñ, á, etc.)

**Approach:**
1. Verify special characters correct
2. Check for common OCR errors:
   - ñ → n
   - á/é/í → a/e/i
   - ll → II (double-L vs two I's)
3. Correct in verification note if minor
4. If major error, flag for re-OCR

---

### Conflicting Dates

**Challenge:** Two documents say different dates for same event.

**Approach:**
1. Check both source documents
2. Look for clues:
   - Which is original? (deed vs later correspondence)
   - Which is more legible?
   - Are dates close? (might be filing vs execution date)
3. Flag for review with note:
   - "Doc-042 says 1958-03-15, Doc-087 says 1958-06-20. Recommend legal review."

**Do not choose arbitrarily.**

---

### Duplicate Entities

**Challenge:** AI created multiple nodes for same person/property.

**Example:**
- "Mario Ceresa" (Doc-042)
- "M. Ceresa" (Doc-087)
- "Don Mario" (Doc-103)

**Approach:**
1. Verify these are the same entity
2. Reject duplicates
3. Note in primary entity: "Deduplicated from 'M. Ceresa' and 'Don Mario'"

**Graph deduplicator should handle this, but review output.**

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Making Legal Conclusions

**Wrong:**
> "This deed proves Mario Ceresa owns the property and has a valid legal claim."

**Right:**
> "This deed states Mario Ceresa as owner as of 1958-03-15. OCR confidence 89%, manually verified."

**Why:** You're a fact verifier, not a lawyer. Stick to what documents say, not what they mean legally.

---

### ❌ Mistake 2: Over-Verifying Low-Confidence Data

**Wrong:**
> Verifying entity with 42% confidence because "it looks close enough"

**Right:**
> Flag for review: "OCR confidence 42%, handwriting partially illegible, requires expert review"

**Why:** Families trust TIER_2_ANALYST. Don't dilute that trust.

---

### ❌ Mistake 3: Empty or Vague Notes

**Wrong:**
> "Verified" or "OK" or "Looks good"

**Right:**
> "Verified against source document Doc-042, page 3. Name clearly legible, context supports ownership claim."

**Why:** Audit trail and transparency. Your note may be reviewed months later.

---

### ❌ Mistake 4: Verifying Without Checking Source

**Wrong:**
> Clicking "Verify" based solely on confidence score

**Right:**
> Always open source document and visually confirm

**Why:** AI can hallucinate. You are the quality gate.

---

## Daily Workflow

### Morning Routine

1. **Check assigned cases:**
   - Dashboard shows cases awaiting verification
   - Sort by priority (oldest first)

2. **Review verification targets:**
   - Goal: Verify 50-100 entities per day
   - Focus on high-confidence nodes first (quick wins)

3. **Start with straightforward cases:**
   - Typed documents, high OCR confidence
   - Build momentum

---

### Ongoing

4. **Batch similar entities:**
   - Verify all PERSONs in a document
   - Then verify all PROPERTYs
   - More efficient than jumping around

5. **Take breaks:**
   - Verification requires focus
   - Break every 90 minutes
   - Maintain quality over speed

6. **Ask for help:**
   - Stuck on a tricky entity? Flag for senior analyst
   - Don't guess

---

### End of Day

7. **Review your work:**
   - Click "My Verifications" tab
   - Spot-check 5-10 random verifications
   - Ensure notes are detailed

8. **Update status:**
   - Mark case as "Verification In Progress" or "Verification Complete"

9. **Log any issues:**
   - Systemic OCR problems
   - Patterns of hallucinations
   - Document quality issues

---

## Metrics & Performance

### What We Track

- **Verifications per day:** Target 50-100
- **Precision rate:** Your verified entities later checked, target >95% accurate
- **Flags raised:** Good analysts flag 10-20% (shows careful review)
- **Rejections:** Should be <5% (AI is usually close)

### What Good Looks Like

**High performer:**
- 75 verifications/day
- 97% precision
- 15% flag rate
- Detailed notes on all verifications
- Catches hallucinations

**Needs improvement:**
- 30 verifications/day (too slow)
- 85% precision (too many errors)
- 2% flag rate (not flagging enough uncertainties)
- Generic notes ("verified")

---

## Escalation

### When to Escalate to Senior Analyst

- Multiple conflicting documents on same fact
- Suspected fraud (forged documents)
- Legal language you don't understand
- Pattern of AI errors (all dates wrong in batch)
- Family requests clarification

### When to Escalate to Admin

- Technical issues (can't load documents)
- Suspected data breach
- Inappropriate user behavior
- System bugs

---

## Legal & Ethical Guidelines

### What You Can Say to Families (If Asked)

✅ **Allowed:**
- "I've verified this entity against the source documents."
- "The OCR confidence was low, so I flagged it for further review."
- "This document states your grandfather owned the property in 1958."

❌ **Not Allowed:**
- "You have a strong legal case."
- "This document will win you restitution."
- "I think you should pursue this claim."

### If Family Asks for Legal Advice

**Response:**
> "I can verify what the documents say, but I cannot provide legal advice. I recommend consulting with an attorney who specializes in property restitution."

**Then notify admin** that family needs legal referral.

---

## Quick Reference

### Verification Checklist

Before clicking "Verify":
- [ ] Opened source document
- [ ] Entity visible in document
- [ ] Entity type correct
- [ ] Name accurate
- [ ] Context supports extraction
- [ ] Cross-referenced with other docs (if available)
- [ ] Added detailed verification note
- [ ] No legal conclusions in note

### Keyboard Shortcuts (When Implemented)

- `V` - Verify entity
- `F` - Flag for review
- `R` - Reject entity
- `N` - Next entity
- `S` - Open source document
- `?` - Show help

---

## Future Analyst Tools (Post-MVP1)

The following features are planned for the analyst workflow but not included in MVP1:

### Gap Detection & Research Planning

**Coming Soon:** Internal tools to help analysts identify and address gaps in case documentation.

**Capabilities:**
- **Ownership Chain Analysis** - Detect missing property transfers in ownership sequences
- **Temporal Gap Detection** - Flag suspicious time gaps between events (e.g., owned 1920, then 1960, nothing between)
- **Orphan Entity Detection** - Find entities with no connections (likely extraction errors)
- **Research Target Suggestions** - AI-generated suggestions for which documents to seek in archives

**Use Cases:**
- **Quality Assurance:** Find entities the LLM missed extracting from existing documents
- **Case Scoping:** Assess completeness percentage for pricing/effort estimation
- **Research Planning:** Guide which document types to search for in Cuban/Spanish archives
- **Family Communication:** Translate gap insights into empathetic guidance for families

**Important:** Gap detection is an **analyst-only tool**. DO NOT show raw gap analysis to families. Instead:

✅ **Good:** "If you have any property records from the 1920-1960 period, those would strengthen the ownership chain."

❌ **Bad:** "Your case has 3 critical gaps in the ownership chain from 1920-1960."

**Why:** Families come with what they have - often incomplete documents from exile. Our job is to organize and verify what exists, not highlight what's missing. Gap detection helps **us** do better work, not make families feel deficient.

**Reference:** See `docs/plans/2026-01-23-gap-detection-decision.md` for architectural rationale.

---

## Generating Client Dossiers

Once verification is complete, the primary deliverable is a **Forensic Dossier** — a professional PDF document that presents the case evidence in a format suitable for legal proceedings.

### Understanding the Dossier

**What it is:**
- A polished PDF document assembling all verified evidence
- Contains timeline, family history, property history, and evidence inventory
- Includes verification tier indicators and methodology disclosure
- Professional appearance suitable for attorneys and tribunals

**What it is NOT:**
- A legal brief or argument
- A claim of ownership
- Legal advice

### Analyst Control: Choosing the Focus

**Key concept:** You decide what goes into each dossier by selecting:

1. **The Property** — Which property is this dossier about?
2. **The Family Member** — Who is the claimant/heir?

**Why this matters:**
- A single case may have multiple properties (Villa Aurelia, Hacienda Aguarás, etc.)
- A single case may have multiple family members (different heirs, different branches)
- Each property + claimant combination is a distinct restitution claim
- You generate separate dossiers for separate claims

**Example scenarios:**
| Dossier | Property | Claimant | Use Case |
|---------|----------|----------|----------|
| Dossier A | Villa Aurelia | Mario Ceresa | Primary residence claim |
| Dossier B | Hacienda Aguarás | Elena Rodriguez | Agricultural property claim |
| Dossier C | Villa Aurelia | Giovanni Ceresa | Heir of Mario, different claimant |

### Generating a Dossier

**Prerequisites:**
- Case has been processed (`process` command complete)
- Entities have been verified (ideally most TIER_2_ANALYST)
- LaTeX installed on your system (see Admin Guide)

**Step 1: List available properties**
```bash
cd /path/to/forensic_analysis_platform
python3 farmer_factory/cli.py list-entities CASE-ID --type PROPERTY
```

Review the list and note the ID of the property you want to focus on.

**Step 2: List available family members**
```bash
python3 farmer_factory/cli.py list-entities CASE-ID --type PERSON
```

Review the list and note the ID of the claimant/family member.

**Step 3: Generate the dossier**
```bash
python3 farmer_factory/cli.py generate-dossier CASE-ID \
  --property-id "PROPERTY_ID_HERE" \
  --family-member-id "PERSON_ID_HERE"
```

**Output:**
- LaTeX file: `cases/CASE-ID/output/CASE-ID_dossier.tex`
- PDF file: `cases/CASE-ID/output/CASE-ID_dossier.pdf`

**Step 4: Review before delivery**
- Open the PDF and review all sections
- Verify no legal conclusions appear
- Check timeline accuracy
- Confirm family tree is correct
- Ensure verification tiers are displayed

### Dossier Sections

Each dossier contains:

| Section | Contents | Your Review Focus |
|---------|----------|-------------------|
| **Executive Summary** | 2-paragraph overview | Factual, no legal conclusions |
| **Methodology & Disclaimer** | How evidence was processed | Always included, don't modify |
| **Timeline** | Chronological events | Dates accurate, sources cited |
| **The Family** | Lineage and key figures | Relationships correct |
| **The Property** | Description and location | Address and details accurate |
| **Ownership History** | How family acquired/lost property | Narrative spine is clear |
| **Evidence Inventory** | Document-by-document summary | All docs accounted for |
| **Appendix** | Full citations, glossary | Technical reference |

### Dry Run (No PDF)

To generate just the `.tex` file without compiling to PDF:

```bash
python3 farmer_factory/cli.py generate-dossier CASE-ID \
  --property-id "PROPERTY_ID" \
  --family-member-id "PERSON_ID" \
  --dry-run
```

Useful for:
- Testing on systems without LaTeX
- Reviewing the raw template output
- Debugging template issues

### Client Access

Once generated, the dossier PDF appears in the Vault dashboard:

1. Client logs into Vault
2. Navigates to case dashboard
3. **"Dossier ready"** appears in workflow checklist
4. Client clicks **"Download PDF"**

**Note:** Dossier only appears when you have generated it. Until then, client sees "Dossier in preparation."

### Multiple Dossiers

For cases with multiple claims, generate separate dossiers:

```bash
# Dossier for Villa Aurelia + Mario
python3 farmer_factory/cli.py generate-dossier TEST-CERESA \
  --property-id "villa_aurelia_id" \
  --family-member-id "mario_id"

# Rename output before generating next
mv cases/TEST-CERESA/output/TEST-CERESA_dossier.pdf \
   cases/TEST-CERESA/output/TEST-CERESA_villa_aurelia_mario.pdf

# Dossier for Hacienda Aguaras + Elena
python3 farmer_factory/cli.py generate-dossier TEST-CERESA \
  --property-id "hacienda_aguaras_id" \
  --family-member-id "elena_id"
```

**Future enhancement:** Multiple dossier management in UI (not in MVP).

### Common Issues

**"xelatex not found"**
- LaTeX not installed. See Admin Guide for installation.
- Use `--dry-run` to generate .tex without PDF.

**"Property/Person not found"**
- Double-check the ID from `list-entities` output
- IDs are long strings with underscores, copy exactly

**Empty sections in dossier**
- Missing data in graph (e.g., no family relations extracted)
- Run extraction again or manually review source documents
- Some sections may be empty if data doesn't exist

**Timeline out of order**
- Document dates may be incorrectly extracted
- Review and re-verify date entities

---

## Contact & Support

**Questions about verification:**
- Slack: #analyst-support
- Email: senior-analyst@civictable.com

**Technical issues:**
- Slack: #platform-support
- Email: admin@civictable.com

**Urgent issues:**
- Phone: [TBD]

---

*This guide should be consulted frequently during your first 30 days. Verification quality is our core value proposition.*

**Last updated:** 2026-01-23
