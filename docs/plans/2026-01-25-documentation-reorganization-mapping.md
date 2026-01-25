# Documentation Reorganization Mapping

> **Created:** 2026-01-25
> **Purpose:** Map where each .claude/ file should move during reorganization

---

## Keep in .claude/
- **CLAUDE.md** - Master instructions for Claude (will be rewritten)
- **ROADMAP.md** - Project-level tracking

## Move to docs/architecture/
- **ARCHITECTURE.md** → `docs/architecture/ARCHITECTURE.md`
- **SECURITY.md** → `docs/architecture/SECURITY.md`
- **POSTURING.md** → `docs/architecture/POSTURING.md`
- **FRONTEND.md** → `docs/architecture/FRONTEND.md`

## Move to farmer_factory/extract/
- **PROMPTS.md** → `farmer_factory/extract/PROMPTS.md`

## Move to farmer_factory/structure/
- **SCHEMA.md** → `farmer_factory/structure/SCHEMA.md`

## Move to farmer_factory/prepare/
- **PREPROCESSING.md** → `farmer_factory/prepare/PREPROCESSING.md`

## Files to Review (Not in Plan)
Additional files found in .claude/ that weren't in original plan:
- **ADMIN_GUIDE.md** - Admin operational guide
- **ANALYST_GUIDE.md** - Analyst workflow guide
- **DATA_DICTIONARY.md** - Data model reference
- **GAP_REMEDIATION_PLAN.md** - Gap remediation planning
- **GAPS_ANALYSIS.md** - Gap analysis
- **README.md** - Current .claude/ README
- **TESTING.md** - Testing documentation
- **settings.local.json** - Local settings (keep)

**Decision needed:** Where should guides (ADMIN_GUIDE, ANALYST_GUIDE) go?
- Option A: `docs/guides/`
- Option B: Keep in `.claude/` temporarily
- Option C: Move to `docs/architecture/` as operational docs

**Decision needed:** Where should DATA_DICTIONARY.md go?
- Relates to SCHEMA.md, could move to `farmer_factory/structure/`

**Decision needed:** Where should TESTING.md go?
- Could move to `docs/architecture/` or stay in `.claude/`

---

## Implementation Priority

**Phase 1 (Current Plan):**
- Architecture docs → `docs/architecture/`
- Module docs → respective modules
- Rewrite CLAUDE.md

**Phase 2 (Follow-up if needed):**
- Organize guides
- Handle DATA_DICTIONARY, TESTING, GAP docs
