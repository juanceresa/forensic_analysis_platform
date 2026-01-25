# Analyst Verification Guide — Civic Table Platform

> **Document Classification:** Internal Operations Manual
> **Version:** 1.1.0
> **Created:** 2025-01-22
> **Last Updated:** 2026-01-23
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
     - Name/label
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
- ✅ Name/label accurately transcribed
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
- [ ] Name/label accurate
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
