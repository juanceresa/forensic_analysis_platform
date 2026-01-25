"""LLM prompts for single-stage narrative generation."""

from typing import Dict, Any


class NarrativePrompts:
    """Prompt templates for narrative generation."""

    NARRATIVE_TEMPLATE = """You are a forensic analyst writing a historical narrative for property restitution research.

**CRITICAL CONSTRAINTS:**
1. Write in past tense with engaging narrative voice (not mechanical data dump)
2. EVERY claim must have inline citation: [①], [②], etc.
3. Present events in chronological order
4. NEVER make legal conclusions or assess ownership validity
5. NEVER infer beyond what documents explicitly state
6. Highlight expropriations, sales, and inheritances prominently

**Focal Entity:** {focal_entity_name} ({focal_entity_type})

**Graph Context:**
{graph_context}

**Special Instructions:**
- If CONFISCATED relations exist, dedicate a prominent paragraph starting with "🚨 EXPROPRIATION EVENT"
- For SOLD or INHERITED events, note them clearly with dates and parties
- Use engaging language: "Villa Aurelia first appears..." not "Villa Aurelia was mentioned..."
- Keep it accessible for families, not just lawyers

**Output Format:**
Write a chronological narrative (3-8 paragraphs) with inline citations [①], [②], etc.

For each citation number, the evidence will be:
- Document ID and page
- Exact quote from document
- Date if available

Example style:
"Villa Aurelia, a 59.28 caballería estate in Maniabón [①], passed to the Rodríguez Pérez heirs in 1960 [②]. That same year, the Instituto Nacional de Reforma Agraria confiscated 12.99 caballerías under the Agrarian Reform Law [③]."
"""

    SIMPLE_NARRATIVE_TEMPLATE = """You are a forensic analyst providing context for an entity with limited data.

**Entity:** {entity_name} ({entity_type})

**Available Information:**
{context}

**Task:**
Write 1-2 sentences explaining this entity's role in the documents, even though we have limited context.

Example:
"Juan Mir Perez appears as Jefe del Departamento Legal del Instituto Nacional de Reforma Agraria (INRA) in a 1960 co-heir document. Role: INRA legal official involved in Villa Aurelia estate proceedings."

Focus on: who they are, what role they played, how they connect to the case.
"""

    HIGHLIGHTED_EVENT_TEMPLATE = """**🚨 {event_type} EVENT**
{summary}

{details}
"""

    def build_narrative_prompt(self, graph_context: Dict[str, Any]) -> str:
        """
        Build prompt for full narrative generation.

        Args:
            graph_context: Dict with focal entity, entities, relations, documents

        Returns:
            Formatted prompt string
        """
        focal = graph_context.get("focal_entity", {})
        entities = graph_context.get("entities", [])
        relations = graph_context.get("relations", [])
        documents = graph_context.get("documents", [])

        # Format graph context
        entities_str = "\n".join([f"- {e}" for e in entities])

        relations_str = "\n".join([
            f"- {r.get('type', 'UNKNOWN')}: {r.get('source', '?')} → {r.get('target', '?')}"
            f"{' (date: ' + r['date'] + ')' if r.get('date') else ''}"
            for r in relations
        ])

        docs_str = "\n".join([f"- {d}" for d in documents])

        # Check for special events
        has_confiscation = any(r.get("type") == "CONFISCATED" for r in relations)
        has_sale = any(r.get("type") == "SOLD" for r in relations)
        has_inheritance = any(r.get("type") == "INHERITED" for r in relations)

        special_events = []
        if has_confiscation:
            special_events.append("CONFISCATION (highlight prominently)")
        if has_sale:
            special_events.append("SALE (note clearly)")
        if has_inheritance:
            special_events.append("INHERITANCE (note clearly)")

        context_str = f"""
**Entities in Context:**
{entities_str}

**Relations:**
{relations_str}

**Source Documents:**
{docs_str}

**Special Events to Highlight:**
{', '.join(special_events) if special_events else 'None'}
"""

        return self.NARRATIVE_TEMPLATE.format(
            focal_entity_name=focal.get("name", "Unknown"),
            focal_entity_type=focal.get("type", "UNKNOWN"),
            graph_context=context_str
        )

    def build_simple_narrative_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build prompt for simple entities (insufficient data).

        Args:
            context: Dict with entity name, type, role, document

        Returns:
            Formatted prompt string
        """
        context_lines = []
        if context.get("role"):
            context_lines.append(f"Role: {context['role']}")
        if context.get("document"):
            context_lines.append(f"Appears in: {context['document']}")
        if context.get("connections"):
            context_lines.append(f"Connected to: {', '.join(context['connections'])}")

        context_str = "\n".join(context_lines)

        return self.SIMPLE_NARRATIVE_TEMPLATE.format(
            entity_name=context.get("name", "Unknown"),
            entity_type=context.get("type", "UNKNOWN"),
            context=context_str
        )

    def format_highlighted_event(
        self,
        event_type: str,
        summary: str,
        details: str
    ) -> str:
        """
        Format highlighted event (expropriation, sale, inheritance).

        Args:
            event_type: "CONFISCATION", "SALE", or "INHERITANCE"
            summary: Brief event summary
            details: Detailed description with citations

        Returns:
            Formatted event block
        """
        return self.HIGHLIGHTED_EVENT_TEMPLATE.format(
            event_type=event_type,
            summary=summary,
            details=details
        )
