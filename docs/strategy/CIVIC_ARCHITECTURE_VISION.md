# Civic Table as Civic Architecture: Strategic Vision Document

> **Document Classification:** Strategic Foundation
> **Version:** 1.0.0
> **Created:** 2026-01-27
> **Status:** Living Document — Core Strategic Reference

---

## Executive Summary

This document captures the strategic insight that **Civic Table is civic architecture**—an institution deliberately designed to translate degraded archives into structured evidence that dispossessed communities can deploy for their own purposes.

The platform, currently focused on Cuban property restitution, generalizes to **any domain where people have legitimate claims but cannot make their documentary evidence legible to institutions that matter**.

**Key insight:** 70% of what we've built is domain-agnostic. The path to expansion requires:
1. Abstracting domain-specific elements into configuration
2. Documenting the methodology at a general level (not Cuba-specific)
3. Identifying parallel markets (genealogy, academic research, investigative journalism)

---

## Part I: The Civic Architecture Framework

### Source

Dr. Robert Ceresa's working paper "Civic Architecture: Designing Institutions for Democratic Capacity" (Huston-Tillotson University) provides the theoretical framework for understanding what Civic Table is and what it could become.

### Core Argument

American democracy suffers from **structural civic exhaustion**: institutions still function but no longer enable people to *author* their world. The answer isn't more participation—it's **better design**.

> "Democracy cannot survive on energy alone. It requires form."

### The Four Benchmarks of Democratic Design

| Benchmark | Definition | Test |
|-----------|------------|------|
| **Translation** | Turn private frustration into public action | Does the institution provide channels through which individual experience becomes collective meaning? |
| **Authorship** | Distribute power to shape frameworks, not just outcomes | Can people define agendas, craft language, and steward decisions—not just participate? |
| **Durability** | Carry civic agency across time | Can the institution survive turnover, shifting moods, and generational change? |
| **Scalability** | Travel without losing integrity | Can the design be rebuilt with local materials in new contexts? |

### Key Distinction

The paper distinguishes between **programs** (time-limited initiatives) and **civic infrastructure** (durable institutions that form citizens through design).

> "The Farmer House operates not as a program but as civic infrastructure."

---

## Part II: Civic Table Through the Four Benchmarks

### Benchmark 1: Translation

**The frustration:** Cuban exile families have documents that exist but can't be made legible to institutions:
- Decaying in shoebox archives
- OCR technology doesn't understand their context
- Legal pathways require evidence they can't produce
- Lawyers exist but families approach from positions of weakness

**The translation:** Civic Table converts "my family lost everything" into structured forensic facts:
- "Document X states Y owned Z in 1958"
- "Corroborated by three sources"
- "Verified at TIER_2_ANALYST"

**Civic Table is institutional translation:** converting private pain into public evidence.

### Benchmark 2: Authorship

**The design choice:** Families own their dossiers but don't manipulate the evidence.

- Verification tiers are **transparent**—families see what's AI-extracted vs. verified
- The output enables families to **author their own next steps**: negotiate with lawyers, decide on litigation, present evidence on their terms
- "Forensic facts, not legal conclusions" gives families information without dependency

**The paper's insight:** "Authorship does not mean unanimity... It means structured co-creation."

Civic Table gives families co-authorship of their historical record without corrupting forensic integrity.

### Benchmark 3: Durability

**POSTURING.md is a durability document.** Critical moves:
- Publish methodology while Robert is at Farmer House
- Make Farmer House verification optional, not required
- Build platform so Civic Table survives any institutional relationship ending

**The paper warns:** "When the forms that hold civic agency are thin, every generation must start again from scratch."

**Our response:** Published methodology + working platform = durable civic infrastructure for documentary recovery. Other families, other regions can inherit this work.

### Benchmark 4: Scalability

**Methodology-as-publication** directly addresses this.

> "True scalability is not replication by template. It is translation across context."

Civic Table's design allows:
- The methodology to be adopted elsewhere (it's published)
- But implementation requires local expertise (our moat)
- Other practitioners rebuild civic forms with local materials using the same verification tier framework

---

## Part III: What Civic Table Is (and Isn't)

### What We Are

**Civic infrastructure for documentary recovery**—an institution designed to:
- **Learn** (AI extraction + human verification improves over time)
- **Remember** (audit trails, graph databases, verification histories)
- **Redesign itself** (methodology publication invites iteration by others)

### What We Are Not

| Not This | Because |
|----------|---------|
| Legal aid program | We don't provide legal strategy |
| Technology service | We provide forensic facts, not software |
| Advocacy organization | We don't argue for outcomes |
| SaaS product | We're a service bureau; clients view, not manipulate |

### The Larger Vision

> **Civic Table builds infrastructure for making degraded archives legible to power structures—enabling dispossessed families, marginalized communities, and individual researchers to author their own evidentiary records.**

---

## Part IV: Generalization Analysis

### What's Domain-Specific vs. Domain-Agnostic

| Layer | Current (Cuban Property) | Generalizability |
|-------|-------------------------|------------------|
| **Technical** | OCR → LLM extraction → graph construction | ~95% reusable |
| **Methodological** | Verification tiers, forensic facts posture, audit trails | 100% reusable |
| **Domain** | Spanish-language deeds, Cuban property law, FCSC claims | 0% reusable—requires new config per domain |

**Key insight:** 70% of what we've built is domain-agnostic.

### Domain-Specific Elements to Abstract

1. **Entity taxonomy** — What kinds of things exist?
   - Cuban: PERSON, PROPERTY, ORGANIZATION, LOCATION, DOCUMENT
   - Genealogy: PERSON, BIRTH_EVENT, DEATH_EVENT, MARRIAGE_EVENT
   - Holocaust: PERSON, PROPERTY, BANK_ACCOUNT, BUSINESS

2. **Relation taxonomy** — What relationships matter?
   - Cuban: OWNS, CONFISCATED, WITNESSED, NOTARIZED
   - Genealogy: PARENT_OF, CHILD_OF, MARRIED_TO, BORN_AT
   - Investigative: PAID_TO, DIRECTOR_OF, SHAREHOLDER_OF

3. **Extraction prompts** — Domain-specific LLM instructions
   - Language, historical context, document types, entities to extract

4. **Verification criteria** — What does "verified" mean?
   - Cuban: Chain of title complete, FCSC-ready
   - Genealogy: Vital records match, DAR-acceptable
   - Holocaust: Claims Conference standards

5. **Success definition** — What outcome are we enabling?
   - Cuban: FCSC claim, lawyer negotiation
   - Genealogy: DAR application, citizenship claim
   - Investigative: Publication, legal filing

6. **Language/script** — Spanish, German, Hebrew, Cyrillic, handwriting variants

7. **Temporal context** — 1950s Cuba vs. 1930s-40s Europe vs. contemporary

8. **Geographic context** — Cuban provinces vs. other regional hierarchies

---

## Part V: Market Analysis

### The Civic Architecture Test for Market Selection

Use the four benchmarks to identify where this infrastructure creates value:

#### Translation Test
> "Where are there frustrated archives?"

Communities with documents that *exist* but can't be made *legible* to institutions:

| Domain | The Frustration | The Translation Gap |
|--------|----------------|---------------------|
| **Genealogical research** | "I have family records but can't prove lineage" | Degraded documents → verified family graphs |
| **Holocaust/WWII restitution** | "Records scattered across archives" | Multi-archive synthesis → ownership chains |
| **Indigenous land claims** | "Oral history + fragments but courts want paper" | Mixed evidence → structured evidentiary base |
| **Slavery descendant research** | "Records in census margins, ship logs, ledgers" | Hostile archives → person-centered graphs |
| **Immigration family reunification** | "Can prove relationship but documents in foreign formats" | Foreign archives → USCIS-legible evidence |
| **Investigative journalism** | "10,000 FOIA pages but can't find the story" | Document dumps → entity relationship maps |
| **Academic historical research** | "Primary sources but manual extraction takes years" | Archival research → structured datasets |

#### Authorship Test
> "Who gains agency from structured evidence?"

**Strong authorship cases:**
- Families negotiating with lawyers (come with evidence, not dependency)
- Descendants approaching reparations processes (own their lineage documentation)
- Researchers building their own databases (control the evidence base)
- Journalists investigating power (map relationships themselves)

**Weak authorship cases:**
- Pure service to institutions (archives digitizing for their own use)
- Research assistance without ownership transfer

#### Durability Test
> "What problems persist across generations?"

**Strong (multi-generational):**
- Property restitution (Cuban, Jewish, Indigenous, colonial)
- Genealogical research (inherently generational)
- Descendant claims (slavery reparations, historical injustice)

**Weaker:**
- One-time investigative projects
- Research that ends with publication

#### Scalability Test
> "Are there parallel communities with similar problems?"

Post-revolutionary property dispossession pattern:
- Cuba (1959) — current focus
- Nicaragua (1979) — Sandinista confiscations
- Haiti (1804) — colonial property claims
- Zimbabwe (2000s) — land reform disputes
- South Africa — post-apartheid restitution
- Eastern Europe (1945-89) — Communist-era seizures

Each requires domain-specific knowledge, but methodology transfers.

---

## Part VI: Competitive Landscape

### The Market is Fragmented by Layer

| Layer | Tools | What They Do | What They Don't Do |
|-------|-------|--------------|-------------------|
| **OCR/HTR** | Transkribus, eScriptorium, Kraken | Transcribe historical documents | Extract entities, build graphs, produce dossiers |
| **Document Organization** | DocumentCloud, Google Pinpoint | Search, annotate, organize | Build relationship graphs, verification tiers |
| **Investigative Platforms** | ICIJ Datashare, OCCRP Aleph | Cross-reference entities across leaks | Process your documents, verification workflow |
| **Knowledge Graphs** | Neo4j, KGGen | Store and query relationships | End-to-end from documents, client-facing output |
| **Genealogy** | FamilySearch, Ancestry, MyHeritage | Search institutional archives | Process personal/family archives |

### The Gap: No Integrated Pipeline

**What doesn't exist:**

```
Your degraded documents
        ↓
   OCR with confidence scoring
        ↓
   Entity + relationship extraction
        ↓
   Knowledge graph construction
        ↓
   Verification tiers
        ↓
   Client-ready dossier with citations
        ↓
   Audit trail for evidentiary use
```

### Closest Competitors

| Platform | Proximity | Why It's Not the Same |
|----------|-----------|----------------------|
| **ICIJ Datashare** | High | Built for massive leaked archives (Panama Papers scale), not personal document recovery. Uses Neo4j. No verification tiers. Not for individuals. |
| **Google Pinpoint** | Medium | Entity extraction + search, but no relationship graphs, no dossier output, no verification workflow. For newsrooms, not families. |
| **Transkribus** | Medium | Best-in-class HTR, but stops at transcription. No entity extraction, no graphs, no dossiers. |
| **Palantir** | Conceptually close | Does everything, costs millions, enterprise-only, no civic mission. |

### Academic Validation (Not Competition)

Research community building one-off pipelines that validate our approach:
- Chilean Dictatorship Archives — LLM entity extraction + resolution
- 19th-Century Land Registry — End-to-end pipeline for property graphs
- Oral Historical Archives (LLM-RAG) — Knowledge graph from oral history

These are academic projects, not products. They validate the approach without competing in the market.

### Feature Comparison Matrix

| Capability | Transkribus | Pinpoint | Datashare | **Civic Table** |
|------------|-------------|----------|-----------|-----------------|
| Historical HTR/OCR | ✅ | ✅ | ❌ | ✅ |
| Entity extraction | ❌ | ✅ | ✅ | ✅ |
| Relationship extraction | ❌ | ❌ | Partial | ✅ |
| Knowledge graph | ❌ | ❌ | ✅ | ✅ |
| Verification tiers | ❌ | ❌ | ❌ | ✅ |
| Dossier generation | ❌ | ❌ | ❌ | ✅ |
| Audit trail | ❌ | ❌ | Partial | ✅ |
| Domain configurable | N/A | ❌ | ❌ | ✅ (planned) |
| Designed for individuals | ❌ | ❌ | ❌ | ✅ |

---

## Part VII: Market Sizing and Prioritization

### Market Assessment

| Market | Size | Civic Mission | Technical Fit | Business Model |
|--------|------|---------------|---------------|----------------|
| **Genealogy** | Massive ($4.7B Ancestry) | Medium | High | Consumer subscription |
| **Academic/DH** | Medium, grant-funded | High | High | Per-project or institutional |
| **Investigative Journalism** | Small but influential | High | High | Difficult (expect free tools) |
| **Parallel Restitution** | Niche per geography | Very High | Very High | Service bureau |

### Strategic Positioning

```
                    Market Size
                         ▲
                         │
         Genealogy ●     │
         (massive)       │
                         │
                         │     ● Academic/DH
                         │       (medium, grant-funded)
                         │
         ● Investigative │
           Journalism    │
           (small but    │
            influential) │
                         │
                         └────────────────────────▶ Civic Mission Alignment
                              Low              High
```

### Recommended Priority

1. **Vertical expansion** (same problem, different geographies) — Highest mission alignment
   - Nicaraguan exile claims (Spanish-language, similar structure)
   - Eastern European restitution (active processes, aging archives)

2. **Genealogy** — Largest market opportunity
   - White space is "process your personal archives"
   - FamilySearch/Ancestry focus on institutional archives
   - Would need consumer-friendly UX layer

3. **Academic/Digital Humanities** — Strong technical fit
   - Grant-funded projects have budgets
   - Need customization and transparency
   - Longer sales cycles

4. **Investigative Journalism** — Influential but difficult
   - Real need, but newsrooms expect free tools
   - Best path: open-source core, paid hosted service

---

## Part VIII: Strategic Priorities

### Priority 1: Abstract Domain Configuration (Technical)

Pull Cuban-specific elements into a configuration layer:

```
civic_table/
├── core/                      # Domain-agnostic
│   ├── intake/                # Document loading
│   ├── prepare/               # Preprocessing
│   ├── extract/               # OCR + LLM engine
│   ├── structure/             # Graph construction
│   ├── verify/                # Verification framework
│   ├── export/                # Dossier generation
│   └── vault/                 # Client-facing viewer
│
├── domains/                   # Domain-specific configs
│   ├── cuban_property/
│   │   ├── schema.yaml        # Entity types, relation types
│   │   ├── prompts/           # Extraction prompts
│   │   ├── taxonomies/        # Domain vocabulary
│   │   └── success.yaml       # What "verified" means
│   │
│   ├── genealogy/             # Future
│   ├── holocaust_restitution/ # Future
│   └── investigative/         # Future
```

### Priority 2: Document Methodology at General Level (Publication)

The publication should be:

**Title:** "Documentary Recovery as Civic Infrastructure: A Methodology for Archival Intelligence"

**Structure:**
1. The problem: degraded archives, frustrated translation
2. The framework: civic architecture for evidentiary authorship
3. The methodology: OCR → extraction → graph → verification → dossier
4. The verification tier system (domain-agnostic)
5. Case study: Cuban property restitution (worked example)
6. Applicability: genealogy, restitution claims, investigative research, digital humanities

**Key positioning:** Foundational methodology with Cuban property as illustration, not "Cuban property tool that might generalize."

### Priority 3: Identify Domain #2 Partner

Options:
- **Genealogical society** — Large market, clear success criteria
- **Holocaust memorial organization** — Active restitution processes
- **Academic archive project** — Grant-funded, methodology-aligned
- **Parallel dispossession community** — Nicaraguan, Eastern European

Partner brings domain expertise; we bring methodology and platform.

---

## Part IX: The Moat

### What Protects Civic Table Long-Term

1. **Published Methodology** — Permanent, citable, can't be taken away
2. **Platform Ownership** — Code, infrastructure, client data
3. **First-Mover Advantage** — Operating when competitors read the paper
4. **Client Relationships** — Direct pipeline to communities
5. **Founding Case** — Ceresa archive as proprietary training/validation data
6. **Implementation Expertise** — Knowing ≠ Doing

### The Croissant Analogy

> Published methodology = Recipe for croissants
> Civic Table platform = The bakery with trained bakers, equipment, supplier relationships, and happy customers

Anyone can read the croissant recipe. Most won't try to bake. Those who try won't do it well. Those who do it well won't scale it.

---

## Part X: Design Tensions to Acknowledge

### The Paternalism Tradeoff

The paper emphasizes **distributed power** and **co-creation**. Civic Table's model is deliberately paternalistic in one dimension: **families cannot modify their own data**.

This is intentional (evidence integrity), but worth naming as a design choice.

**Possible expansions of authorship (without compromising forensic integrity):**
- Families flag gaps they know about ("we know there's a third deed")
- Families prioritize which entities to verify first
- Families contribute oral history context for disambiguation
- Families annotate (but not edit) their dossiers

### The Commercial vs. Civic Tension

Genealogy is the largest market but has medium civic mission alignment. Investigative journalism has high alignment but difficult business model.

**Resolution:** The technical core is the same. Domain configuration allows serving multiple markets from shared infrastructure. Commercial success (genealogy) can fund civic mission (restitution, journalism).

---

## Part XI: Key Quotes for Reference

### From the Civic Architecture Paper

> "Democracy cannot survive on energy alone. It requires form."

> "Civic architecture names the work of rebuilding society's civic capacity... the deliberate design of institutions that embed democratic agency, distribute responsibility, and sustain public life across generations."

> "Authorship does not mean unanimity or endless consensus. It means structured co-creation: defined roles, transparent rules, and shared custody of meaning."

> "True scalability is not replication by template. It is translation across context."

> "The Farmer House operates not as a program but as civic infrastructure."

### From This Analysis

> "Civic Table is institutional translation: converting private pain into public evidence."

> "70% of what we've built is domain-agnostic."

> "No one has built the end-to-end pipeline from degraded documents to verified, client-ready evidence with audit trails—designed for individuals and families rather than enterprises or newsrooms."

> "The gap is real."

---

## Appendix A: Domain Configuration Schema (To Be Developed)

See separate document: `docs/architecture/DOMAIN_CONFIGURATION.md` (planned)

Key elements to parameterize:
- Entity types and their fields
- Relation types and their constraints
- Extraction prompts (per entity type, per document type)
- Verification criteria (what does each tier mean in this domain)
- Success definition (what outcome are we enabling)
- Language and script configuration
- Temporal and geographic context
- Confidence thresholds

## Appendix B: Methodology Publication Outline (To Be Developed)

See separate document: `docs/strategy/METHODOLOGY_PUBLICATION_OUTLINE.md` (planned)

## Appendix C: Competitive Intelligence Sources

- [GIJN Top Investigative Tools 2025](https://gijn.org/stories/gijn-top-investigative-tools-2025/)
- [Google Pinpoint vs DocumentCloud](https://mediacopilot.ai/google-pinpoint-vs-documentcloud-investigative-journalism/)
- [ICIJ Datashare](https://gijn.org/stories/gijns-data-journalism-top-10-datashare-document-analysis-visualization-talkies-and-kyrgyzstans-labor-imbalance/)
- [Transkribus and Digital Humanities](https://www.pdnob.com/ocr/transkribus.html)
- [FamilySearch AI Developments](https://www.familysearch.org/en/blog/ai-developments-genealogy)
- [Knowledge Graph Extraction Challenges (Neo4j)](https://neo4j.com/blog/developer/knowledge-graph-extraction-challenges/)
- [Chilean Dictatorship Archives KG (arXiv)](https://arxiv.org/html/2408.11975v1)

---

*This document captures strategic insights from the civic architecture analysis session of 2026-01-27. It should be referenced for all decisions about platform generalization, market expansion, and methodology publication.*
