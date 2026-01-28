# Business Strategy Discussion — 2026-01-26

> **Document Type:** Strategic Planning Session
> **Date:** January 26, 2026
> **Status:** Key insights captured, action items defined

---

## Executive Summary

This document captures a strategic discussion about the Civic Table platform's business model, market positioning, and go-to-market strategy. The conversation evolved from questioning the viability of a $50k/case consulting model to identifying a clearer product-market fit: **helping Cuban exile families understand what they have before engaging lawyers**.

**Key outcome:** The product is not document preparation for legal proceedings — it's the essential research step families need before seeking legal opinion.

---

## The Platform: What We Built

### Technical Stack
- **Factory (Python):** OCR via Google Cloud Vision, AI extraction via Claude API, NetworkX graph construction, entity resolution
- **Vault (Next.js):** Read-only client portal, document browser, entity browser, knowledge graph visualization
- **Architecture:** Air-gapped design — no client uploads, all processing local, clients only see read-only deliverables (avoids SaaS privacy regulations)

### Current State
- Document-first frontend complete
- Entity extraction and relationship mapping working
- Narrative generation implemented
- PDF dossier export planned (LaTeX-based)

---

## Strategic Questions Explored

### 1. "Is this something people would pay big money for?"

**Initial assessment:**
- Real pain point for Cuban exile community
- Smart legal positioning ("forensic facts, not legal strategy")
- No technical moat — OCR + Claude + NetworkX are commodity tools
- Value is in methodology and domain expertise

**Concerns raised:**
- Market size is speculative (depends on Cuban political change)
- $50k pricing triggers "why not just hire lawyers?"
- Current state is prototype, not production

### 2. "What about broader legal tech?"

**Competitive landscape research revealed existing players:**

| Company | Focus |
|---------|-------|
| Affinda | Property deed extraction (99%+ accuracy) |
| V7 Labs | Deed analysis, chain of title tracing |
| Dono | Title industry AI + human verification |
| Parse AI | Property ownership at scale |
| Prophia | Lease abstraction (established 2018) |

**Conclusion:** Broad legal tech = knife to a gunfight. Well-funded competitors with enterprise sales teams, compliance certifications, and integrations.

**Potential gap:** Historical/degraded documents, complex disputes, narrative construction — areas mainstream tools don't handle well.

### 3. "What's the speculative bet on Cuba?"

**Current situation (January 2026):**
- Trump administration actively seeking regime change by end of 2026
- Maduro abduction described as "blueprint and warning" for Cuba
- Cuban economy in worst crisis since Soviet collapse (GDP -11% since 2020)
- 10-20 hour daily blackouts, 10% of population fled
- Sporadic protests now endemic

**Probability assessment:**

| Scenario | Probability |
|----------|-------------|
| Status quo continues | 50-60% |
| Gradual opening (3-5 years) | 20-30% |
| Regime change 2026 | 10-20% |
| Violent collapse / chaos | 5-10% |

**Conclusion:** 15-25% chance of significant change in 2026. Not the base case, but not crazy. Asymmetric bet — limited downside, significant upside if it happens.

---

## The Breakthrough Insight

### What the family's lawyer meeting revealed:

> "They were surprised at how much we had in order."

**Translation:** Most families show up to lawyers with a mess.

> "The question for us was always 'do we have a case'"

**Translation:** Families don't know what they have. They need clarity before spending on lawyers.

> "Research that seems necessary for a family to do before seeking legal opinion"

**This is the product.**

### Reframed Value Proposition

| Old Framing | New Framing |
|-------------|-------------|
| "We prepare documents for legal proceedings" | "We help you understand what you have before you pay a lawyer $500/hr to figure it out" |

### The Position in the Value Chain

```
[Family has boxes of documents]
         ↓
[Civic Table: Organize, extract, analyze]  ← YOU ARE HERE
         ↓
[Family understands what they have]
         ↓
[Informed decision: pursue legal action or not]
         ↓
[Lawyers receive organized client, save 10-20 hours]
```

**You're not replacing lawyers. You're the step before lawyers.**

---

## Revised Business Model

### Pricing Tiers

| Tier | What It Answers | Price Range |
|------|-----------------|-------------|
| **Assessment** | "Do we have anything worth pursuing?" | $1,500-2,500 |
| **Full Dossier** | "Here's everything we have, organized and mapped" | $5,000-8,000 |
| **Legal-Ready** | Above + JD verification and certification | $8,000-12,000 |

### Why This Works

- **Accessible:** Cheaper than 10 hours of lawyer time
- **Clear value:** Not "why not just hire lawyers" — it's "do this FIRST"
- **Referral-friendly:** Lawyers may actually recommend this

### The Referral Loop

Lawyers who've been monitoring Cuban cases for years:
- Don't want to bill 20 hours sorting disorganized papers
- Would prefer clients arrive organized
- When Cuba opens, they'll be overwhelmed — they'll NEED intake help

**Potential script:** "Before we take you on, get your documents organized. Talk to Civic Table."

---

## Architectural Decisions Confirmed

### No Self-Service Tier

The platform intentionally does not support client document uploads. All document processing happens locally on our infrastructure. This avoids:
- GDPR compliance
- Data retention policies
- Breach notification requirements
- SaaS privacy regulations

Clients only access read-only deliverables through the Vault. This is a deliberate compliance/liability decision, not a future feature gap.

### The "Air Gap" Serves the Business Model

- **Zone A (Factory):** Internal processing, never client-facing
- **Zone B (Vault):** Read-only delivery of completed work

This architecture supports a consulting model, not a SaaS model.

---

## Competitive Advantages

1. **Historical document handling** — Optimized for degraded 1950s Spanish-language notarial deeds, not clean modern PDFs
2. **In-house JD** — End-to-end service, verification without external dependency
3. **Narrative construction** — Not just data extraction, but the *story* of ownership
4. **Community trust** — Cuban exile community is tight-knit; reputation matters more than marketing

---

## Risk Assessment

### What Could Go Wrong

| Risk | Mitigation |
|------|------------|
| Cuba never opens | Limited investment, skills transfer to other domains |
| Families won't pay | Price at accessible $3-5k, prove value with first clients |
| Lawyers don't refer | Build relationships, show them the output quality |
| Competitors emerge if Cuba opens | First mover advantage, established workflow |

### What We're NOT Doing

- Quitting day jobs for this
- Spending $50k on marketing
- Building enterprise features for hypothetical scale
- Betting savings on Cuban politics

---

## Action Items

### Immediate (Next 2-4 Weeks)

1. **Complete family dossier** — First case study, proof of concept
2. **Build LaTeX PDF export** — Professional deliverable that justifies the fee
3. **Show dossier to lawyers** — "This is what we deliver"
4. **Ask for referrals** — "Know any families who need this?"

### Short-Term (1-3 Months)

5. **Process 2-3 paying clients** — Validate workflow, refine pricing
6. **Document the methodology** — Reproducible process
7. **Network in Miami** — Cuban exile organizations, law firms

### Positioning (Ongoing)

8. **Watch for signals** — If US takes concrete action beyond rhetoric, accelerate
9. **Keep codebase maintained** — Ready to scale if moment comes
10. **Don't over-invest** — This is an asymmetric bet, not a sure thing

---

## The Bottom Line

**What we're building:** A reputation-based consulting practice that helps Cuban exile families understand their property documentation before engaging lawyers.

**What we're NOT building:** A SaaS platform competing with well-funded legal tech companies.

**The bet:** Limited downside (time invested, skills gained), asymmetric upside (if Cuba opens, first mover in sudden market).

**The next step:** Ship the first dossier. Everything else is theory until then.

---

## Sources Referenced

- [Trump seeking regime change in Cuba - Al Jazeera](https://www.aljazeera.com/news/2026/1/22/trump-seeking-regime-change-in-cuba-by-end-of-the-year-us-media-report)
- [Cuba on the Brink - Foreign Affairs](https://www.foreignaffairs.com/cuba/cuba-brink)
- [Cuban Property Law May Trigger Mass Restitutions - Searcy Law](https://www.searcylaw.com/law-affecting-cuban-property-may-result-in-the-return-of-hundreds-of-thousands-of-stolen-property/)
- [Cubans brace for economic devastation - NBC News](https://www.nbcnews.com/world/latin-america/cubans-brace-even-economic-devastation-threat-no-venezuelan-oil-rcna252430)
- [Affinda Property Title Deed](https://www.affinda.com/documents/property-title-deed)
- [V7 Labs Deed Analysis Agent](https://www.v7labs.com/agents/deed-analysis-agent)
- [Dono Platform](https://www.dono.ai/)

---

*Document generated from strategic planning session, 2026-01-26*
