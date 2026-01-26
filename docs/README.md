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
- **`architecture/TESTING.md`** - Testing strategy and quality assurance

---

## Operational Guides

User-facing documentation for platform operators:
- **`guides/ADMIN_GUIDE.md`** - System administration and case management
- **`guides/ANALYST_GUIDE.md`** - Analyst verification workflow

---

## Module Documentation

Implementation-level documentation:

### Extract Module (`farmer_factory/extract/`)
- **`README.md`** - Module overview, usage examples
- **`PROMPTS.md`** - LLM extraction prompts (canonical reference)

### Structure Module (`farmer_factory/structure/`)
- **`README.md`** - Graph construction and entity deduplication
- **`SCHEMA.md`** - Complete JSON/Pydantic schema specification
- **`DATA_DICTIONARY.md`** - Field-level reference
- **`INTEGRATION.md`** - Integration guide

### Prepare Module (`farmer_factory/prepare/`)
- **`README.md`** - Module overview
- **`PREPROCESSING.md`** - Image processing pipeline details

---

## Recent Changes

Context for recent updates in this session:
- Narrative API now loads `graph_data.json`, and relation counting/model selection uses unique edges.
- Knowledge graph supports multiple relations between the same nodes (multi-edge) and cache invalidation hashes full graph state.
- Extraction now passes document dates into relation temporal fallbacks and skips invalid relation types without dropping valid ones.
- Graph export format is unified on `nodes` + `links`, with metadata carrying verification distribution, entity type summary, and date range.

---

## Implementation Plans

Dated design and implementation documents:
- **`plans/`** - All implementation plans (YYYY-MM-DD-feature-name.md)

Recent plans:
- `2026-01-25-documentation-reorganization.md`
- `2026-01-25-extract-module-refactor.md`
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
- **Admin operations?** → `guides/ADMIN_GUIDE.md`
- **Analyst workflow?** → `guides/ANALYST_GUIDE.md`

---

*All documentation is now organized by domain. `.claude/` contains only Claude-specific instructions.*
