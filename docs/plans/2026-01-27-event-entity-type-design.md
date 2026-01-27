# EVENT Entity Type Design Document

> **Status:** DESIGN ONLY - Not yet implemented
> **Date:** 2026-01-27
> **Inspired by:** Chilean dictatorship KG paper (arXiv:2408.11975), Chinese oral history archive research

---

## Motivation

Current schema represents relationships as edges between entities (e.g., PERSON --OWNS--> PROPERTY). While this works for simple relationships, it struggles with complex historical events that involve:

1. **Multiple participants with different roles** - A property sale involves seller, buyer, notary, witnesses
2. **Temporal specificity** - Events have specific dates, not just "a relationship exists"
3. **Contextual details** - Purchase price, payment terms, legal conditions
4. **Causality chains** - Inheritance follows death, confiscation follows nationalization decree

The Chilean KG paper demonstrates that modeling events as first-class entities improves both extraction accuracy and downstream analysis capabilities.

---

## Proposed Design

### EVENT Entity Type

```python
class Event(BaseEntity):
    """
    First-class entity representing a discrete historical occurrence.

    Events capture actions, transactions, and occurrences that involve
    multiple entities and have specific temporal/contextual attributes.
    """

    entity_type: str = "EVENT"

    # Event identity
    event_type: str  # From EventType enum
    name: Optional[str] = None  # Human-readable summary

    # Temporal precision
    date: Optional[str] = None  # ISO date or partial
    date_precision: Optional[str] = None  # "day", "month", "year", "decade"
    end_date: Optional[str] = None  # For duration events

    # Location
    location_id: Optional[str] = None
    location_description: Optional[str] = None

    # Context
    document_id: Optional[str] = None  # Source document
    evidence: Optional[str] = None  # Quoted text
    notes: Optional[str] = None
    # Structured context (esp. for transactions)
    amount: Optional[float] = None
    currency: Optional[str] = None
    payment_terms: Optional[str] = None
    doc_ids: List[str] = Field(default_factory=list)  # All source docs
    evidence_quotes: List[str] = Field(default_factory=list)
    date_sortable: Optional[str] = None  # normalized ISO for ordering
```

### EventType Enum

```python
class EventType(str, Enum):
    """
    Categories of events relevant to property/genealogy research.
    """

    # Property transactions
    SALE = "SALE"
    PURCHASE = "PURCHASE"
    INHERITANCE = "INHERITANCE"
    GIFT = "GIFT"
    MORTGAGE = "MORTGAGE"
    CONFISCATION = "CONFISCATION"

    # Life events
    BIRTH = "BIRTH"
    DEATH = "DEATH"
    MARRIAGE = "MARRIAGE"
    DIVORCE = "DIVORCE"

    # Legal events
    NOTARIZATION = "NOTARIZATION"
    REGISTRATION = "REGISTRATION"
    CERTIFICATION = "CERTIFICATION"

    # Historical events
    NATIONALIZATION = "NATIONALIZATION"
    EXILE = "EXILE"
```

### Event Participation Relations

Rather than direct entity-to-entity relations, events use typed participation:

```python
class EventParticipation(str, Enum):
    """
    Roles entities play in events.
    """

    # Transaction roles
    SELLER = "SELLER"
    BUYER = "BUYER"
    GRANTOR = "GRANTOR"
    GRANTEE = "GRANTEE"

    # Legal roles
    NOTARY = "NOTARY"
    WITNESS = "WITNESS"
    REPRESENTATIVE = "REPRESENTATIVE"

    # Subject roles
    SUBJECT = "SUBJECT"  # The property/person the event is about
    BENEFICIARY = "BENEFICIARY"

    # Context roles
    CREDITOR = "CREDITOR"
    DEBTOR = "DEBTOR"
```

Relations would be: `PERSON --PARTICIPATES_IN[role=SELLER]--> EVENT`
Notes:
- `PARTICIPATES_IN` carries a `role` edge property.
- An entity can have multiple participations on the same event (e.g., NOTARY + WITNESS) if we allow; decide whether to collapse or keep both.
- Event IDs should be deterministic to allow dedup across documents, e.g., `${caseId}-event-${hash(type+date+participants)}`.

---

## Example: Property Sale

### Current Model (Edge-based)

```
Mario Ceresa --SOLD--> Central Santa Maria
Mario Ceresa --SOLD_TO--> Maria Fernandez
Maria Fernandez --BOUGHT--> Central Santa Maria
Jose Rodriguez --NOTARIZED--> (sale document)
```

Problems:
- Date attached to each edge redundantly
- Price/terms duplicated or missing
- Hard to query "all sales in 1958"
- Witness relationships awkward

### Proposed Model (Event-based)

```
EVENT: sale_001
  type: SALE
  date: 1958-03-15
  date_precision: day
  location_id: loc_habana
  evidence: "Escritura Publica 125..."

PARTICIPATES_IN:
  - Mario Ceresa [role=SELLER]
  - Maria Fernandez [role=BUYER]
  - Central Santa Maria [role=SUBJECT]
  - Jose Rodriguez [role=NOTARY]
  - Witness 1 [role=WITNESS]
  - Witness 2 [role=WITNESS]

EVENT_CONTEXT:
  - amount: 50000
  - currency: pesos
  - payment_terms: "cash"
  - document_id: doc_escritura_125
  - doc_ids: [doc_escritura_125, doc_witness_statement]
```

Benefits:
- Single source of truth for date/price
- Easy to query all participants
- Easy to query all events of type
- Natural representation of multi-party transactions

---

## Migration Considerations

### Backward Compatibility

Existing edges should remain valid during transition:

1. **Phase 1:** Add EVENT entity type and PARTICIPATES_IN relation
2. **Phase 2:** Extraction produces both old edges AND events
3. **Phase 3:** Graph builder creates events from edge clusters
4. **Phase 4:** Frontend supports event-centric views
5. **Phase 5:** Deprecate redundant edges (optional)

### Schema Evolution

```python
# New relations to add
class RelationType(str, Enum):
    # ... existing types ...

    # Event relations
    PARTICIPATES_IN = "PARTICIPATES_IN"  # Entity -> Event
    CAUSED_BY = "CAUSED_BY"  # Event -> Event
    ENABLED_BY = "ENABLED_BY"  # Event -> Event
    DOCUMENTED_IN = "DOCUMENTED_IN"  # Event -> Document
```

### Extraction Prompt Changes

The LLM extraction prompts would need to:

1. Identify discrete events in text
2. Extract participants with roles
3. Link contextual details to events
4. Establish temporal ordering
5. Emit deterministic event IDs/slugs so repeated mentions map to the same event
6. Coexist with edge extraction during transition; decide conflict resolution (edges derived from events vs. keep both tagged as derived)

### Per-Event-Type Required Fields (validation)
- **SALE**: roles seller, buyer, subject (property); preferred fields: amount/currency/payment_terms; date or date_precision required.
- **PURCHASE/GIFT/INHERITANCE/CONFISCATION**: roles grantor/grantee or beneficiary/subject as applicable; date/date_precision required.
- **NOTARIZATION/REGISTRATION/CERTIFICATION**: roles notary/subject; doc_id preferred.
- **BIRTH/DEATH/MARRIAGE/DIVORCE**: roles subject (person) plus counterpart for marriage/divorce; date/date_precision required.
- If required participants are missing, skip emitting event or mark as incomplete for review.

---

## Query Benefits

### Current Model Queries

```cypher
// Find all properties Mario sold - requires multiple joins
MATCH (p:Person {name: "Mario Ceresa"})-[:SOLD]->(prop:Property)
RETURN prop

// Find sale price - not possible without document parsing
```

### Event Model Queries

```cypher
// All events where Mario participated
MATCH (p:Person {name: "Mario Ceresa"})-[r:PARTICIPATES_IN]->(e:Event)
RETURN e, r.role

// All sales in 1958 with prices
MATCH (e:Event {type: "SALE"})
WHERE e.date STARTS WITH "1958"
RETURN e.date, e.amount, e.currency

// Chain of title for a property
MATCH (prop:Property)-[:PARTICIPATES_IN {role: "SUBJECT"}]-(e:Event)
WHERE e.type IN ["SALE", "INHERITANCE", "GIFT"]
RETURN e ORDER BY e.date

// Who witnessed most transactions?
MATCH (p:Person)-[r:PARTICIPATES_IN {role: "WITNESS"}]->(e:Event)
RETURN p.name, count(e) ORDER BY count(e) DESC
```

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Increased schema complexity | Phase-based rollout, maintain edge compatibility |
| Extraction accuracy decrease | Keep edge extraction, generate events as secondary |
| Frontend visualization complexity | Start with list views, add event timelines later |
| Storage overhead | Events replace redundant edges, net neutral |
| Duplicate events across docs | Deterministic event ID/slug; merge when type+date+participants match |
| Missing required participants per type | Add per-event-type validation (e.g., SALE: seller, buyer, subject) and skip emission if incomplete |
| No price fields available | Add amount/currency/payment_terms and allow null; don’t block event if missing |
| Role ambiguity | Allow multiple PARTICIPATES_IN with different roles; flag contradictions for review |

---

## Recommendation

**Defer implementation until:**

1. Edge-based extraction is stable and well-tested
2. Frontend MVP is complete
3. Real user feedback indicates need for complex event queries

**When implementing:**

1. Start with SALE events only (most common, best defined)
2. Auto-generate from existing edge clusters
3. Add extraction support incrementally

---

## References

- Chilean dictatorship KG paper (arXiv:2408.11975) - Section 4.2 "Event-Centric Modeling"
- Chinese oral history archive research - Temporal event chains
- Wikidata event modeling patterns
- CIDOC-CRM event ontology (museum domain)
