"""LLM prompts for batch case narrative generation."""

from typing import Dict, List, Any


PERIOD_NARRATIVE_TEMPLATE = """You are a forensic analyst writing a historical narrative for property restitution research.

**CRITICAL CONSTRAINTS:**
1. Write in past tense with engaging narrative voice (not a mechanical data dump)
2. Present events in chronological order within this period
3. NEVER make legal conclusions or assess ownership validity
4. NEVER infer beyond what the documents explicitly state
5. Highlight expropriations, sales, and inheritances prominently
6. Ground every claim in the documents provided — do not fabricate

**Time Period:** {period_label} ({period_range})

**Documents in this period:**
{documents_context}

**Entities referenced in this period:**
{entities_context}

**Relations between entities in this period:**
{relations_context}

**Special Events to Highlight:**
{special_events}
{domain_knowledge}
**Instructions:**
First, write a short evocative title (3-6 words) for this period — something a family would recognize,
like "The Confiscation" or "Building The Family Empire" or "A Legacy Divided". Not a date range.

Then write a narrative (3-6 paragraphs) that does THREE things:

1. TELL THE STORY — what happened in this period, grounded in the documents.
   Use engaging language. Keep it accessible for families, not lawyers.

2. EXPLAIN THE SIGNIFICANCE — use your knowledge of the domain (see Domain
   Knowledge above) to explain WHY document details matter. Example: if a tax
   record lists 24 caballerías but other records show 60, explain what that
   discrepancy means in context of Cuban fiscal practices.

3. FLAG FORENSIC OBSERVATIONS — note discrepancies between documents, missing
   records one would expect, patterns that suggest something, or connections
   across documents the family might not see.

Weave all three naturally into the prose — do not use headers, bullets, or
separate sections. The narrative should read as one cohesive analytical story.

After the narrative, on a new line starting with "OBSERVATIONS:", list 1-3
brief forensic observations as pipe-separated entries:
  observation text | severity (HIGH/MEDIUM/LOW)

Output format:
<title>
---
<narrative prose>
---
OBSERVATIONS:
<observation> | <severity>"""


CASE_SUMMARY_TEMPLATE = """You are a forensic analyst writing an executive summary for a property restitution case.

**CRITICAL CONSTRAINTS:**
1. Write in past tense with engaging narrative voice
2. Summarize the full arc of the family's documentary record
3. NEVER make legal conclusions or assess ownership validity
4. NEVER infer beyond what the documents state
5. This is AI-generated research analysis, not a legal document

**Case:** {case_id}
**Date Range:** {date_range}
**Total Documents:** {total_documents}
**Total Entities:** {total_entities}

**Period Summaries (chronological):**
{period_summaries}

**Instructions:**
Write a 2-3 paragraph executive summary of this case. Describe the arc of the family's
documentary record — what the documents reveal about property ownership, transfers,
and any state actions over time. Be specific about key events and dates.

Output ONLY the summary prose. No headers, no bullet points, no metadata."""


def build_period_prompt(
    period_label: str,
    period_range: str,
    documents: List[Dict[str, Any]],
    entities: List[Dict[str, Any]],
    relations: List[Dict[str, Any]],
    domain_context: str = "",
) -> str:
    """Build prompt for a single period's narrative generation."""
    docs_lines = []
    for doc in documents:
        line = f"- {doc.get('name', doc.get('id', 'Unknown'))}"
        if doc.get("date"):
            line += f" (dated {doc['date']})"
        if doc.get("document_type"):
            line += f" [{doc['document_type']}]"
        docs_lines.append(line)
    docs_str = "\n".join(docs_lines) if docs_lines else "No documents with dates in this period."

    entity_lines = []
    for ent in entities:
        line = f"- {ent.get('name', ent.get('id', 'Unknown'))} ({ent.get('entity_type', 'UNKNOWN')})"
        entity_lines.append(line)
    entities_str = "\n".join(entity_lines) if entity_lines else "No entities identified."

    relation_lines = []
    has_confiscation = False
    has_sale = False
    has_inheritance = False
    for rel in relations:
        rel_type = rel.get("relation_type", "UNKNOWN")
        line = f"- {rel_type}: {rel.get('source_name', '?')} -> {rel.get('target_name', '?')}"
        if rel.get("date"):
            line += f" (date: {rel['date']})"
        relation_lines.append(line)

        if rel_type == "CONFISCATED":
            has_confiscation = True
        elif rel_type == "SOLD":
            has_sale = True
        elif rel_type == "INHERITED":
            has_inheritance = True

    relations_str = "\n".join(relation_lines) if relation_lines else "No relations identified."

    special = []
    if has_confiscation:
        special.append("CONFISCATION (highlight prominently)")
    if has_sale:
        special.append("SALE (note clearly)")
    if has_inheritance:
        special.append("INHERITANCE (note clearly)")
    special_str = ", ".join(special) if special else "None"

    # Domain knowledge section (bound to 3000 chars)
    domain_section = ""
    if domain_context:
        truncated = domain_context[:3000]
        if len(domain_context) > 3000:
            truncated += "\n[truncated]"
        domain_section = f"\n**Domain Knowledge:**\n{truncated}\n"

    return PERIOD_NARRATIVE_TEMPLATE.format(
        period_label=period_label,
        period_range=period_range,
        documents_context=docs_str,
        entities_context=entities_str,
        relations_context=relations_str,
        special_events=special_str,
        domain_knowledge=domain_section,
    )


def build_summary_prompt(
    case_id: str,
    date_range: str,
    total_documents: int,
    total_entities: int,
    period_summaries: List[Dict[str, str]],
) -> str:
    """Build prompt for the overall case summary."""
    summaries_lines = []
    for ps in period_summaries:
        summaries_lines.append(f"**{ps['label']} ({ps['range']}):**\n{ps['narrative']}\n")
    summaries_str = "\n".join(summaries_lines)

    return CASE_SUMMARY_TEMPLATE.format(
        case_id=case_id,
        date_range=date_range,
        total_documents=total_documents,
        total_entities=total_entities,
        period_summaries=summaries_str,
    )
