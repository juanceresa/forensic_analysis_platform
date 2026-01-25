# Documentation Reorganization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reorganize documentation so `.claude/CLAUDE.md` is the master file with pointers to domain-specific docs in their proper module locations.

**Architecture:** Current `.claude/` directory contains everything (PROMPTS.md, SCHEMA.md, ARCHITECTURE.md, etc.). We'll move domain docs to their modules and keep only Claude-specific instructions in `.claude/`.

**Principles:**
- `.claude/CLAUDE.md` - Master file with project overview and pointers
- Module docs (PROMPTS.md, SCHEMA.md) - Move to relevant modules
- Architecture docs (ARCHITECTURE.md, SECURITY.md) - Move to `docs/architecture/`
- Keep `.claude/ROADMAP.md` (project-level tracking)

---

## Task 1: Audit current documentation structure

**Files:**
- Read: `.claude/` directory contents
- Read: existing module README files

**Step 1: List all .claude files**

Run: `ls -la .claude/`

Expected output showing all doc files

**Step 2: List all module README files**

Run: `find farmer_factory -name "README.md" -o -name "*.md"`

Expected: List of existing module documentation

**Step 3: Create reorganization mapping**

Document where each file should go:

```markdown
# Documentation Reorganization Mapping

## Keep in .claude/
- CLAUDE.md (master instructions for Claude)
- ROADMAP.md (project-level tracking)

## Move to docs/architecture/
- ARCHITECTURE.md → docs/architecture/ARCHITECTURE.md
- SECURITY.md → docs/architecture/SECURITY.md
- POSTURING.md → docs/architecture/POSTURING.md
- FRONTEND.md → docs/architecture/FRONTEND.md

## Move to farmer_factory/extract/
- PROMPTS.md → farmer_factory/extract/PROMPTS.md

## Move to farmer_factory/structure/
- SCHEMA.md → farmer_factory/structure/SCHEMA.md

## Move to farmer_factory/prepare/
- PREPROCESSING.md → farmer_factory/prepare/PREPROCESSING.md
```

**Step 4: Commit planning doc**

```bash
git add docs/plans/2026-01-25-documentation-reorganization-mapping.md
git commit -m "docs: plan documentation reorganization"
```

---

## Task 2: Create docs/architecture/ directory

**Files:**
- Create: `docs/architecture/` directory
- Create: `docs/architecture/README.md`

**Step 1: Create architecture docs directory**

Run: `mkdir -p docs/architecture`

**Step 2: Create architecture README**

```markdown
# Architecture Documentation

> **Last Updated:** 2026-01-25

This directory contains high-level architecture and design documentation for the Civic Table platform.

---

## Documents

### System Architecture
- **ARCHITECTURE.md** - System design, Air Gap architecture, zones A & B
- **SECURITY.md** - Authentication, authorization, audit logging

### Domain Architecture
- **POSTURING.md** - Organizational strategy, Farmer House vs Civic Table
- **FRONTEND.md** - UI components, design system, verification tiers

---

## Quick Links

**For implementation details, see module-specific docs:**
- Entity extraction: `farmer_factory/extract/PROMPTS.md`
- Graph schema: `farmer_factory/structure/SCHEMA.md`
- Image preprocessing: `farmer_factory/prepare/PREPROCESSING.md`

**For Claude Code instructions:**
- Master file: `.claude/CLAUDE.md`
- Project roadmap: `.claude/ROADMAP.md`

---

*These documents are design references. For code-level docs, see module READMEs.*
```

**Step 3: Commit**

```bash
git add docs/architecture/
git commit -m "docs: create architecture documentation directory"
```

---

## Task 3: Move architecture docs from .claude/ to docs/architecture/

**Files:**
- Move: `.claude/ARCHITECTURE.md` → `docs/architecture/ARCHITECTURE.md`
- Move: `.claude/SECURITY.md` → `docs/architecture/SECURITY.md`
- Move: `.claude/POSTURING.md` → `docs/architecture/POSTURING.md`
- Move: `.claude/FRONTEND.md` → `docs/architecture/FRONTEND.md`

**Step 1: Move architecture files**

Run:
```bash
mv .claude/ARCHITECTURE.md docs/architecture/
mv .claude/SECURITY.md docs/architecture/
mv .claude/POSTURING.md docs/architecture/
mv .claude/FRONTEND.md docs/architecture/
```

**Step 2: Verify files moved**

Run: `ls -la docs/architecture/`

Expected: All 4 .md files present

**Step 3: Commit**

```bash
git add docs/architecture/ .claude/
git commit -m "docs: move architecture docs from .claude/ to docs/architecture/

Moved system design docs to proper location:
- ARCHITECTURE.md
- SECURITY.md
- POSTURING.md
- FRONTEND.md

These are reference documents, not Claude-specific instructions.
"
```

---

## Task 4: Move PROMPTS.md to farmer_factory/extract/

**Files:**
- Move: `.claude/PROMPTS.md` → `farmer_factory/extract/PROMPTS.md`

**Step 1: Move PROMPTS.md**

Run: `mv .claude/PROMPTS.md farmer_factory/extract/`

**Step 2: Verify it's in extract module**

Run: `ls farmer_factory/extract/*.md`

Expected: PROMPTS.md and README.md

**Step 3: Update extract/README.md to reference PROMPTS.md**

Add to extract/README.md:

```markdown
## Prompts

All extraction prompts are documented in `PROMPTS.md` in this directory:
- **Prompt 1:** Entity Extraction (Structured Format)
- **Prompt 2:** Relation Extraction

See `PROMPTS.md` for complete prompt templates and design rationale.
```

**Step 4: Commit**

```bash
git add farmer_factory/extract/PROMPTS.md farmer_factory/extract/README.md .claude/
git commit -m "docs: move PROMPTS.md to extract module

Moved LLM prompt specifications from .claude/ to farmer_factory/extract/:
- Entity extraction prompts
- Relation extraction prompts

Updated extract/README.md to reference PROMPTS.md.
"
```

---

## Task 5: Move SCHEMA.md to farmer_factory/structure/

**Files:**
- Move: `.claude/SCHEMA.md` → `farmer_factory/structure/SCHEMA.md`

**Step 1: Move SCHEMA.md**

Run: `mv .claude/SCHEMA.md farmer_factory/structure/`

**Step 2: Verify it's in structure module**

Run: `ls farmer_factory/structure/*.md`

Expected: SCHEMA.md, README.md, INTEGRATION.md

**Step 3: Update structure/README.md to reference SCHEMA.md**

Add to structure/README.md under "## Components":

```markdown
### Complete Schema Specification

See `SCHEMA.md` in this directory for:
- Full JSON schema definitions
- TypeScript type definitions
- Force-graph export format
- Validation rules

`SCHEMA.md` is the canonical schema reference for both Python (Pydantic) and TypeScript implementations.
```

**Step 4: Commit**

```bash
git add farmer_factory/structure/SCHEMA.md farmer_factory/structure/README.md .claude/
git commit -m "docs: move SCHEMA.md to structure module

Moved graph schema specification from .claude/ to farmer_factory/structure/:
- JSON schema definitions
- Pydantic models
- TypeScript types
- Export format

Updated structure/README.md to reference SCHEMA.md.
"
```

---

## Task 6: Move PREPROCESSING.md to farmer_factory/prepare/

**Files:**
- Move: `.claude/PREPROCESSING.md` → `farmer_factory/prepare/PREPROCESSING.md`

**Step 1: Move PREPROCESSING.md**

Run: `mv .claude/PREPROCESSING.md farmer_factory/prepare/`

**Step 2: Check if prepare/README.md exists**

Run: `ls farmer_factory/prepare/README.md 2>/dev/null || echo "No README"`

**Step 3a: If README exists, update it**

Add reference to PREPROCESSING.md:

```markdown
## Image Processing Pipeline

Complete preprocessing pipeline documentation in `PREPROCESSING.md`:
- Deskewing algorithm
- Denoising techniques
- Triage classification (HANDWRITTEN vs TYPED)
- Quality metrics

See `PREPROCESSING.md` for implementation details and design decisions.
```

**Step 3b: If README doesn't exist, create it**

```markdown
# Prepare Module

> **Version:** 1.0.0
> **Last Updated:** 2026-01-25

Image preprocessing pipeline for historical document OCR.

---

## Overview

Converts raw PDF scans into clean, OCR-ready images through:
- Deskewing (rotation correction)
- Denoising (adaptive thresholding)
- Triage (classify as HANDWRITTEN vs TYPED)

---

## Complete Documentation

See `PREPROCESSING.md` for detailed pipeline specification:
- Algorithm descriptions
- Parameter tuning
- Quality metrics
- Design decisions

---

*For implementation, see `pipeline.py` and `steps/`*
```

**Step 4: Commit**

```bash
git add farmer_factory/prepare/ .claude/
git commit -m "docs: move PREPROCESSING.md to prepare module

Moved image preprocessing documentation from .claude/ to farmer_factory/prepare/.

Created/updated prepare/README.md to reference PREPROCESSING.md.
"
```

---

## Task 7: Rewrite .claude/CLAUDE.md as master pointer file

**Files:**
- Modify: `.claude/CLAUDE.md`

**Step 1: Rewrite CLAUDE.md as concise master file**

```markdown
# CLAUDE.md — Instructions for Claude Code

> **Version:** 2.0.0
> **Last Updated:** 2026-01-25
> **Status:** Master instructions file

---

## Project Identity

You are building the **Civic Table** platform — a Forensic Intelligence service for historical property restitution. The platform implements methodology developed at the **Farmer House Democratic Repair Lab** at Huston-Tillotson University.

**Brand Hierarchy:**
- **Civic Table LLC** — Primary brand, client-facing service, platform owner
- **Farmer House** — Methodology developer, optional institutional verifier

Think "Palantir for Cuban exile land deeds" meets "academic rigor meets commercial implementation."

---

## Critical Constraints

### 1. The Air Gap Architecture

The system has TWO ZONES that must remain separate:

**Zone A (The Factory)** — Python backend
- Internal processing only
- OCR, AI inference, entity extraction
- Clients NEVER see this zone

**Zone B (The Vault)** — Next.js frontend
- Read-only static rendering
- Clients can ONLY view, never upload/edit/delete
- Consumes `graph_data.json` from Zone A

**See:** `docs/architecture/ARCHITECTURE.md` for complete system design.

### 2. Legal Posture

We produce **Forensic Facts**, never **Legal Strategy**.

**ALLOWED:**
- "Document X states Y owned Z in 1958"
- "OCR confidence is 72%"
- "Three documents corroborate this claim"

**FORBIDDEN:**
- "This proves ownership"
- "You have a strong case"
- "This is legally valid"

**See:** `docs/architecture/POSTURING.md` for organizational strategy.

### 3. The Verification Tiers

Every data point MUST have a `verification` field with 4-tier system (TIER_3_AI → TIER_1_CERTIFIED).

**See:** `farmer_factory/structure/SCHEMA.md` for complete verification schema.

---

## Tech Stack

### Factory (Python)
- Python 3.10+, Pydantic, NetworkX
- Google Cloud Vision (OCR)
- Anthropic Claude API (extraction)
- dedupe (ML entity resolution)

### Vault (Next.js)
- Next.js 14, TypeScript, Tailwind CSS
- react-force-graph-2d (visualization)
- Clerk (OAuth authentication)
- Supabase (PostgreSQL with RLS)

---

## Documentation Map

### For Claude Code (this directory)
- **CLAUDE.md** (this file) - Master instructions
- **ROADMAP.md** - Project roadmap and phase tracking

### Architecture & Design
- **`docs/architecture/`**
  - `ARCHITECTURE.md` - System design, Air Gap
  - `SECURITY.md` - Authentication, authorization
  - `POSTURING.md` - Organizational strategy
  - `FRONTEND.md` - UI design system

### Module Documentation
- **`farmer_factory/extract/`**
  - `README.md` - Module overview
  - `PROMPTS.md` - LLM extraction prompts

- **`farmer_factory/structure/`**
  - `README.md` - Graph construction & deduplication
  - `SCHEMA.md` - Complete JSON/Pydantic schema
  - `INTEGRATION.md` - Integration guide

- **`farmer_factory/prepare/`**
  - `README.md` - Module overview
  - `PREPROCESSING.md` - Image processing pipeline

### Implementation Plans
- **`docs/plans/`** - Dated design and implementation docs

---

## Implementation Rules

### Python Code
- Use Pydantic for ALL data models
- Type hints on ALL functions
- Docstrings on public functions
- Log all processing steps
- Handle errors gracefully

### LLM Prompts
- Use prompts EXACTLY as specified in `farmer_factory/extract/PROMPTS.md`
- Parse responses into Pydantic models
- Handle malformed responses gracefully
- Never let LLM make legal conclusions

### Frontend
- Dark theme (Slate-900 background)
- Monospace fonts for data
- Verification badges on all nodes
- TIER_3_AI disclaimer wherever unverified data appears

---

## Common Tasks

### Process documents
```bash
python cli.py process CASE-ID --force-typed
```

### Train entity deduplication
```bash
python cli.py train-deduplication CASE-ID --entity-type PERSON
```

### Clean case for re-processing
```bash
python cli.py clean CASE-ID --confirm
```

---

## Current Phase

**See:** `.claude/ROADMAP.md` for current implementation status.

**Active:** Phase 5 - Graph Construction (ML-based deduplication)

---

## What NOT to Do

1. **Never** make legal conclusions in prompts or output
2. **Never** allow Zone B to modify data
3. **Never** display TIER_3_AI data without disclaimer
4. **Never** skip the verification field on any node/link
5. **Never** expose raw AI inference to clients without context

---

*For detailed documentation, see the files referenced above. This is your navigation guide to the codebase.*
```

**Step 2: Verify all referenced files exist**

Run:
```bash
for file in \
  docs/architecture/ARCHITECTURE.md \
  docs/architecture/SECURITY.md \
  docs/architecture/POSTURING.md \
  docs/architecture/FRONTEND.md \
  farmer_factory/extract/PROMPTS.md \
  farmer_factory/structure/SCHEMA.md \
  farmer_factory/prepare/PREPROCESSING.md \
  .claude/ROADMAP.md
do
  if [ -f "$file" ]; then
    echo "✓ $file"
  else
    echo "✗ MISSING: $file"
  fi
done
```

Expected: All files show ✓

**Step 3: Commit**

```bash
git add .claude/CLAUDE.md
git commit -m "docs: rewrite CLAUDE.md as concise master pointer file

Complete rewrite of .claude/CLAUDE.md (v2.0.0):
- Concise project overview
- Critical constraints summary
- Documentation map pointing to domain docs
- Removed verbose content now in module docs

CLAUDE.md is now the navigation hub, not a monolith.
"
```

---

## Task 8: Update .gitignore if needed

**Files:**
- Check: `.gitignore`

**Step 1: Check current .gitignore for .claude**

Run: `grep -n "^.claude" .gitignore`

Expected: Should show `.claude` is ignored (line 75)

**Step 2: Verify docs/ is NOT ignored**

Run: `grep -n "^docs" .gitignore`

Expected: Should show `docs/*` with exceptions (line 76-78)

**Step 3: Ensure docs/architecture/ is not ignored**

Check that `.gitignore` has:
```
docs/*
!docs/plans/
!docs/CLI_USAGE.md
!docs/architecture/
```

If `!docs/architecture/` is missing, add it.

**Step 4: If changed, commit**

```bash
git add .gitignore
git commit -m "build: update .gitignore to allow docs/architecture/"
```

---

## Task 9: Create documentation index

**Files:**
- Create: `docs/README.md`

**Step 1: Create docs/README.md as documentation index**

```markdown
# Documentation Index

> **Last Updated:** 2026-01-25

Complete documentation map for the Civic Table platform.

---

## For Claude Code

Start here if you're using Claude Code:
- **`.claude/CLAUDE.md`** - Master instructions and navigation
- **`.claude/ROADMAP.md`** - Project roadmap and phases

---

## Architecture & Design

High-level system design and strategy:
- **`architecture/ARCHITECTURE.md`** - System design, Air Gap architecture
- **`architecture/SECURITY.md`** - Authentication, authorization, audit logging
- **`architecture/POSTURING.md`** - Organizational strategy (Farmer House vs Civic Table)
- **`architecture/FRONTEND.md`** - UI components and design system

---

## Module Documentation

Implementation-level documentation:

### Extract Module (`farmer_factory/extract/`)
- **`README.md`** - Module overview, usage examples
- **`PROMPTS.md`** - LLM extraction prompts (canonical reference)

### Structure Module (`farmer_factory/structure/`)
- **`README.md`** - Graph construction and entity deduplication
- **`SCHEMA.md`** - Complete JSON/Pydantic schema specification
- **`INTEGRATION.md`** - Integration guide

### Prepare Module (`farmer_factory/prepare/`)
- **`README.md`** - Module overview
- **`PREPROCESSING.md`** - Image processing pipeline details

---

## Implementation Plans

Dated design and implementation documents:
- **`plans/`** - All implementation plans (YYYY-MM-DD-feature-name.md)

Recent plans:
- `2026-01-25-extract-module-refactor.md`
- `2026-01-25-structured-extraction.md`
- `2026-01-24-dedupe-entity-resolution-plan.md`

---

## CLI Usage

- **`CLI_USAGE.md`** - Command-line interface reference

---

## Navigation Tips

**Looking for:**
- **System architecture?** → `architecture/ARCHITECTURE.md`
- **LLM prompts?** → `farmer_factory/extract/PROMPTS.md`
- **Schema definitions?** → `farmer_factory/structure/SCHEMA.md`
- **Image processing?** → `farmer_factory/prepare/PREPROCESSING.md`
- **Project status?** → `.claude/ROADMAP.md`

---

*All documentation is now organized by domain. `.claude/` contains only Claude-specific instructions.*
```

**Step 2: Commit**

```bash
git add docs/README.md
git commit -m "docs: create documentation index

Added docs/README.md as central navigation hub for all documentation:
- Points to Claude Code instructions
- Links to architecture docs
- Links to module docs
- Lists implementation plans

Makes documentation discoverable.
"
```

---

## Task 10: Verify documentation reorganization

**Files:**
- Verify: All files in correct locations

**Step 1: Check .claude/ only has master files**

Run: `ls .claude/`

Expected output:
```
CLAUDE.md
ROADMAP.md
```

**Step 2: Check architecture docs moved**

Run: `ls docs/architecture/`

Expected output:
```
README.md
ARCHITECTURE.md
SECURITY.md
POSTURING.md
FRONTEND.md
```

**Step 3: Check module docs**

Run:
```bash
echo "=== Extract module ==="
ls farmer_factory/extract/*.md

echo "=== Structure module ==="
ls farmer_factory/structure/*.md

echo "=== Prepare module ==="
ls farmer_factory/prepare/*.md
```

Expected: All module docs in place

**Step 4: Verify no broken links**

Manually check key files reference correct paths:
- `.claude/CLAUDE.md` → points to `docs/architecture/`, module docs
- `docs/README.md` → all links valid
- Module READMEs → reference local .md files correctly

**Step 5: Final commit**

```bash
git add -A
git commit -m "docs: complete documentation reorganization

Final verification and cleanup:
- .claude/ contains only CLAUDE.md and ROADMAP.md
- Architecture docs in docs/architecture/
- Domain docs in their modules
- docs/README.md provides navigation

Documentation is now properly organized by concern.
"
```

---

## Verification Checklist

After completing all tasks:

- [ ] `.claude/` contains ONLY `CLAUDE.md` and `ROADMAP.md`
- [ ] `docs/architecture/` contains `ARCHITECTURE.md`, `SECURITY.md`, `POSTURING.md`, `FRONTEND.md`
- [ ] `farmer_factory/extract/` contains `PROMPTS.md`
- [ ] `farmer_factory/structure/` contains `SCHEMA.md`
- [ ] `farmer_factory/prepare/` contains `PREPROCESSING.md`
- [ ] All module READMEs reference local docs
- [ ] `.claude/CLAUDE.md` is concise master pointer file
- [ ] `docs/README.md` provides documentation index
- [ ] No broken documentation links
- [ ] `.gitignore` allows `docs/architecture/`

---

## Benefits

**Before:**
- Everything in `.claude/` (10+ files)
- Hard to find domain-specific docs
- Unclear what's for Claude vs developers

**After:**
- `.claude/` = Claude Code instructions only
- Domain docs live with their code
- Clear separation of concerns
- Easy to find relevant documentation

---

## Rollback Plan

If issues arise:

```bash
# See what was moved
git log --oneline --follow -- .claude/

# Revert moves
git log --oneline | head -20  # Find commits
git revert <commit-range>
```

---

*This reorganization makes documentation discoverable and maintainable.*
