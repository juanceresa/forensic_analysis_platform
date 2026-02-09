# Domain Configuration Architecture

> **Document Classification:** Technical Design
> **Version:** 1.0.0
> **Created:** 2026-01-27
> **Status:** Implementation Ready

---

## Overview

This document defines the domain configuration system that enables Civic Table to serve multiple documentary recovery domains (genealogy, academic research, investigative journalism, parallel restitution) from a shared technical core.

**Strategic Context:** Maintained in local strategy docs under `.claude/local_docs/strategy/`.

**Key Insight:** 70% of the platform is domain-agnostic. Only entity types, relation types, extraction prompts, and success criteria are domain-specific.

---

## Current State: Hardcoded Elements

### 1. Entity Types (`structure/schema.py`)

```python
class EntityType(str, Enum):
    PERSON = "PERSON"
    PROPERTY = "PROPERTY"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    DOCUMENT = "DOCUMENT"
```

**Domain-specific fields:**
- `Person`: mother, father, spouse, children, siblings (genealogical)
- `Property`: registry_number, cadastral_info, folio_number (Cuban registry)
- `Location`: country defaults to "Cuba"

### 2. Relation Types (`structure/schema.py`)

```python
class RelationType(str, Enum):
    # Property Ownership (26+ types)
    OWNS, OWNED, INHERITED, SOLD, SOLD_TO, BOUGHT, PURCHASED_FROM, CONFISCATED
    # Family Relations
    SPOUSE_OF, CHILD_OF, HEIR_OF, RELATED_TO
    # Property Boundaries
    BORDERS_NORTH, BORDERS_SOUTH, BORDERS_EAST, BORDERS_WEST
    # Document Relations
    MENTIONED_IN, WITNESSED, WITNESSED_BY, NOTARIZED, NOTARIZED_BY, ISSUED_BY
    # ... etc
```

**Temporal classification** (`extract/llm.py`):
```python
TEMPORAL_RELATIONS = {"SOLD", "BOUGHT", "INHERITED", "CONFISCATED", "WITNESSED", "NOTARIZED"}
STATE_RELATIONS = {"OWNS", "LOCATED_IN", "EMPLOYED_BY", "RELATED_TO", "REGISTERED_IN"}
```

### 3. Extraction Prompts (`extract/llm.py`)

Cuban-specific context embedded in prompts:
- "historical Cuban property documents"
- "pre-revolutionary Cuba (pre-1959)"
- Spanish family phrases: "hijo de", "casado con", "esposa de"
- Document types: "deeds, titles, wills, confiscation decrees"
- Geographic focus: "Camagüey province"
- Time period: "1940s-1960s"

### 4. Narrative Prompts (`narrative/prompts.py`)

- "property restitution research"
- CONFISCATED as highlighted event type
- "🚨 EXPROPRIATION EVENT" formatting
- INRA (Instituto Nacional de Reforma Agraria) references

### 5. Dossier Templates (`dossier/templates/`)

- Section names assume property restitution
- Spanish legal terminology in glossary
- Cuban historical context

---

## Target Architecture

### Directory Structure

```
farmer_factory/
├── core/                      # Domain-agnostic engine
│   ├── config/
│   │   ├── domain_loader.py   # Load and validate domain configs
│   │   └── domain_registry.py # Registry of available domains
│   └── ... (existing modules refactored)
│
├── domains/                   # Domain-specific configurations
│   ├── __init__.py
│   ├── cuban_property/
│   │   ├── __init__.py
│   │   ├── domain.yaml        # Main domain configuration
│   │   ├── entities.yaml      # Entity type definitions
│   │   ├── relations.yaml     # Relation type definitions
│   │   ├── prompts/
│   │   │   ├── system_context.txt
│   │   │   ├── entity_extraction.txt
│   │   │   ├── relation_extraction.txt
│   │   │   └── narrative.txt
│   │   ├── taxonomies/
│   │   │   ├── document_types.yaml
│   │   │   ├── property_types.yaml
│   │   │   └── locations.yaml
│   │   └── templates/         # Domain-specific dossier templates
│   │       └── glossary.yaml
│   │
│   ├── genealogy/             # Future domain
│   │   ├── domain.yaml
│   │   ├── entities.yaml
│   │   ├── relations.yaml
│   │   └── prompts/
│   │
│   └── base/                  # Shared base configurations
│       ├── verification.yaml  # Verification tier definitions
│       └── common_entities.yaml
```

---

## Configuration Schema

### Domain Manifest (`domain.yaml`)

```yaml
# domains/cuban_property/domain.yaml
domain:
  name: "Cuban Property Restitution"
  code: "cuban_property"
  version: "1.0.0"
  description: "Documentary recovery for Cuban exile property claims"

  # Primary characteristics
  primary_language: "es"
  supported_languages: ["es", "en"]
  temporal_range:
    start: "1940"
    end: "1970"
    focus_period: "1959-1965"  # Revolution and aftermath

  geographic_focus:
    countries: ["Cuba"]
    primary_regions: ["Camagüey", "La Habana", "Oriente"]

  # What this domain is for
  use_cases:
    - "FCSC claim preparation"
    - "Lawyer negotiation leverage"
    - "Family historical record"

  # Success definition
  success_criteria:
    primary_goal: "FCSC claim preparation"
    verification_target: "TIER_2_ANALYST"  # Minimum tier for primary goal
    completeness_indicators:
      - "Chain of title documented"
      - "Confiscation event documented"
      - "Current claimant lineage established"

# Include other config files
includes:
  entities: "entities.yaml"
  relations: "relations.yaml"
  verification: "../base/verification.yaml"
```

### Entity Configuration (`entities.yaml`)

```yaml
# domains/cuban_property/entities.yaml
entity_types:

  PERSON:
    description: "Individual person (owner, heir, witness, notary, official)"
    icon: "👤"
    color: "#3B82F6"  # Blue

    # Core fields (always present)
    core_fields:
      - name: name
        type: string
        required: true
        description: "Full name as written in documents"

      - name: alternate_names
        type: list[string]
        required: false
        description: "Titles, abbreviations, nicknames"

    # Domain-specific fields
    domain_fields:
      # Demographics
      - name: birth_date
        type: date
        required: false
        extraction_hints: ["nacido", "nació", "fecha de nacimiento"]

      - name: death_date
        type: date
        required: false
        extraction_hints: ["fallecido", "murió", "fecha de defunción"]

      - name: nationality
        type: string
        required: false
        default: "Cuban"

      - name: residence
        type: string
        required: false
        extraction_hints: ["domiciliado en", "vecino de", "residente de"]

      - name: profession
        type: string
        required: false
        extraction_hints: ["profesión", "ocupación", "oficio"]

      - name: marital_status
        type: enum
        values: ["soltero", "casado", "viudo", "divorciado", "unknown"]
        required: false
        extraction_hints: ["casado con", "soltero", "viuda de"]

      # Family relationships (critical for genealogy)
      - name: mother
        type: string
        required: false
        extraction_hints: ["hija de", "hijo de ... y"]

      - name: father
        type: string
        required: false
        extraction_hints: ["hijo de", "hija de"]

      - name: spouse
        type: string
        required: false
        extraction_hints: ["casado con", "esposa de", "esposo de", "casada con"]

      - name: children
        type: list[string]
        required: false
        extraction_hints: ["sus hijos", "herederos"]

      - name: siblings
        type: list[string]
        required: false
        extraction_hints: ["hermano de", "hermana de"]

      # Roles in documents
      - name: roles
        type: list[string]
        required: false
        values: ["owner", "seller", "buyer", "heir", "witness", "notary", "official"]

  PROPERTY:
    description: "Real property (finca, hacienda, urban property)"
    icon: "🏠"
    color: "#10B981"  # Green

    core_fields:
      - name: name
        type: string
        required: false
        description: "Property name if named (e.g., 'Central Santa Maria')"

    domain_fields:
      - name: property_type
        type: enum
        values: ["finca", "hacienda", "ingenio", "central", "colonia", "sitio", "urban", "commercial"]
        required: false
        extraction_hints: ["finca", "hacienda", "ingenio", "propiedad"]

      - name: address
        type: string
        required: false

      - name: description
        type: string
        required: false

      - name: area
        type: float
        required: false

      - name: area_unit
        type: enum
        values: ["hectares", "caballerías", "acres", "square_meters"]
        required: false

      # Cuban registry fields
      - name: registry_number
        type: string
        required: false
        extraction_hints: ["inscrita al", "folio", "tomo"]

      - name: cadastral_info
        type: string
        required: false
        extraction_hints: ["finca número", "cadastral"]

      - name: folio_number
        type: string
        required: false
        extraction_hints: ["folio"]

  ORGANIZATION:
    description: "Organization (bank, court, government agency)"
    icon: "🏛️"
    color: "#F59E0B"  # Amber

    core_fields:
      - name: name
        type: string
        required: true

    domain_fields:
      - name: org_type
        type: enum
        values: ["bank", "court", "notary_office", "registry", "government_agency", "company"]
        required: false

      - name: address
        type: string
        required: false

    # Known organizations for this domain
    known_entities:
      - name: "Instituto Nacional de Reforma Agraria"
        aliases: ["INRA"]
        org_type: "government_agency"
      - name: "Ministerio de Recuperación de Bienes Malversados"
        aliases: ["MRBM"]
        org_type: "government_agency"

  LOCATION:
    description: "Geographic location (city, province, municipality)"
    icon: "📍"
    color: "#8B5CF6"  # Purple

    core_fields:
      - name: name
        type: string
        required: true

    domain_fields:
      - name: location_type
        type: enum
        values: ["country", "province", "municipality", "city", "barrio", "neighborhood"]
        required: false

      - name: parent_location
        type: string
        required: false

      - name: country
        type: string
        required: false
        default: "Cuba"

    # Known locations for this domain
    known_entities:
      - name: "La Habana"
        aliases: ["Havana"]
        location_type: "province"
      - name: "Camagüey"
        location_type: "province"
      - name: "Florida"
        parent_location: "Camagüey"
        location_type: "municipality"

  DOCUMENT:
    description: "Source document (deed, certificate, decree)"
    icon: "📄"
    color: "#6B7280"  # Gray

    core_fields:
      - name: title
        type: string
        required: false

      - name: document_type
        type: string
        required: true

      - name: file_path
        type: string
        required: true

      - name: page_count
        type: integer
        required: true

    domain_fields:
      - name: document_number
        type: string
        required: false

      - name: date
        type: date
        required: false

      - name: issuer
        type: string
        required: false

      - name: language
        type: string
        required: false
        default: "es"
```

### Relation Configuration (`relations.yaml`)

```yaml
# domains/cuban_property/relations.yaml
relation_types:

  # Property Ownership Relations
  OWNS:
    description: "Person/Organization owns Property"
    category: "ownership"
    source_types: [PERSON, ORGANIZATION]
    target_types: [PROPERTY]
    temporal: state  # Ongoing condition, date optional
    color: "#10B981"
    extraction_hints: ["propietario de", "dueño de", "pertenece a"]

  SOLD:
    description: "Person sold Property (transaction event)"
    category: "transaction"
    source_types: [PERSON]
    target_types: [PROPERTY]
    temporal: event  # Needs date
    color: "#F59E0B"
    creates_inverse: BOUGHT
    extraction_hints: ["vendió", "venta de", "enajenó"]

  BOUGHT:
    description: "Person bought Property"
    category: "transaction"
    source_types: [PERSON]
    target_types: [PROPERTY]
    temporal: event
    color: "#F59E0B"
    extraction_hints: ["compró", "adquirió", "compra de"]

  INHERITED:
    description: "Person inherited Property"
    category: "succession"
    source_types: [PERSON]
    target_types: [PROPERTY]
    temporal: event
    color: "#8B5CF6"
    extraction_hints: ["heredó", "herencia de", "heredero de"]

  CONFISCATED:
    description: "Government/Organization confiscated Property"
    category: "expropriation"
    source_types: [ORGANIZATION]
    target_types: [PROPERTY]
    temporal: event
    color: "#EF4444"  # Red - highlight this
    high_priority: true  # Special handling in narratives
    extraction_hints: ["confiscó", "expropiación", "intervención", "nacionalización"]
    narrative_template: "🚨 EXPROPRIATION EVENT"

  # Family Relations
  CHILD_OF:
    description: "Person is child of another Person"
    category: "family"
    source_types: [PERSON]
    target_types: [PERSON]
    temporal: state
    symmetric: false
    color: "#3B82F6"
    extraction_hints: ["hijo de", "hija de"]

  SPOUSE_OF:
    description: "Person is spouse of another Person"
    category: "family"
    source_types: [PERSON]
    target_types: [PERSON]
    temporal: state
    symmetric: true  # If A spouse of B, then B spouse of A
    color: "#EC4899"
    extraction_hints: ["casado con", "esposa de", "esposo de", "casada con"]

  HEIR_OF:
    description: "Person is heir of another Person"
    category: "succession"
    source_types: [PERSON]
    target_types: [PERSON]
    temporal: state
    color: "#8B5CF6"
    extraction_hints: ["heredero de", "heredera de"]

  RELATED_TO:
    description: "Generic family relation (when specific type unclear)"
    category: "family"
    source_types: [PERSON]
    target_types: [PERSON]
    temporal: state
    symmetric: true
    color: "#6B7280"
    fallback: true  # Use when specific relation type unclear

  # Document Relations
  WITNESSED:
    description: "Person witnessed transaction/document"
    category: "document"
    source_types: [PERSON]
    target_types: [DOCUMENT]
    temporal: event
    color: "#6B7280"
    extraction_hints: ["testigo", "presente"]

  NOTARIZED:
    description: "Notary certified document"
    category: "document"
    source_types: [PERSON]
    target_types: [DOCUMENT]
    temporal: event
    color: "#6B7280"
    extraction_hints: ["notario", "ante mí", "certifico"]

  ISSUED_BY:
    description: "Document issued by Organization"
    category: "document"
    source_types: [DOCUMENT]
    target_types: [ORGANIZATION]
    temporal: state
    color: "#6B7280"

  # Geographic Relations
  LOCATED_IN:
    description: "Property/Organization located in Location"
    category: "geographic"
    source_types: [PROPERTY, ORGANIZATION]
    target_types: [LOCATION]
    temporal: state
    color: "#8B5CF6"
    extraction_hints: ["ubicado en", "sito en", "situado en"]

  REGISTERED_IN:
    description: "Property registered in Registry"
    category: "administrative"
    source_types: [PROPERTY]
    target_types: [ORGANIZATION]
    temporal: state
    color: "#6B7280"
    extraction_hints: ["inscrita en", "registrada en"]

  # Property Boundary Relations (domain-specific)
  BORDERS_NORTH:
    description: "Property borders to the north"
    category: "boundary"
    source_types: [PROPERTY]
    target_types: [PROPERTY, LOCATION, PERSON]
    temporal: state
    color: "#6B7280"
    extraction_hints: ["norte", "al norte", "lindando al norte"]

  BORDERS_SOUTH:
    description: "Property borders to the south"
    category: "boundary"
    source_types: [PROPERTY]
    target_types: [PROPERTY, LOCATION, PERSON]
    temporal: state
    color: "#6B7280"
    extraction_hints: ["sur", "al sur", "lindando al sur"]

  BORDERS_EAST:
    description: "Property borders to the east"
    category: "boundary"
    source_types: [PROPERTY]
    target_types: [PROPERTY, LOCATION, PERSON]
    temporal: state
    color: "#6B7280"
    extraction_hints: ["este", "al este", "lindando al este"]

  BORDERS_WEST:
    description: "Property borders to the west"
    category: "boundary"
    source_types: [PROPERTY]
    target_types: [PROPERTY, LOCATION, PERSON]
    temporal: state
    color: "#6B7280"
    extraction_hints: ["oeste", "al oeste", "lindando al oeste"]

# Relation categories for filtering/display
categories:
  ownership:
    label: "Ownership"
    description: "Property ownership relations"
  transaction:
    label: "Transactions"
    description: "Sales, purchases"
  succession:
    label: "Succession"
    description: "Inheritance and heirs"
  expropriation:
    label: "Expropriation"
    description: "Government confiscation"
    high_priority: true
  family:
    label: "Family"
    description: "Family relationships"
  document:
    label: "Document"
    description: "Document-related relations"
  geographic:
    label: "Geographic"
    description: "Location relations"
  boundary:
    label: "Boundaries"
    description: "Property boundaries"
  administrative:
    label: "Administrative"
    description: "Registry and administrative"

# Temporal classification
temporal_types:
  event:
    description: "Events that occurred at specific times (need dates)"
    examples: ["SOLD", "BOUGHT", "INHERITED", "CONFISCATED", "WITNESSED"]
    date_required: preferred
  state:
    description: "Ongoing conditions (dates optional)"
    examples: ["OWNS", "LOCATED_IN", "EMPLOYED_BY", "SPOUSE_OF"]
    date_required: optional
```

### Prompt Templates (`prompts/`)

```text
# domains/cuban_property/prompts/system_context.txt

You are a forensic document analyst working on historical property records from pre-revolutionary Cuba (pre-1959). Your task is to extract factual information from OCR-processed documents.

CRITICAL CONSTRAINTS:
1. Extract only what the document explicitly states or directly implies
2. Never make legal conclusions (e.g., "this proves ownership")
3. Never assess claim strength or litigation potential
4. Flag uncertain extractions with confidence scores
5. Preserve original Spanish names and terms
6. Note OCR quality issues that affect reliability

DOCUMENT CONTEXT:
- Most documents are in Spanish
- Many are handwritten (variable OCR quality)
- Document types include: deeds, titles, wills, confiscation decrees, registry certificates, notarial acts, correspondence
- Time period: primarily 1940s-1960s
- Geographic focus: Cuba, with emphasis on Camagüey province

SPANISH FAMILY RELATIONSHIP PATTERNS:
- "hijo de [father] y [mother]" - son of
- "hija de [father] y [mother]" - daughter of
- "casado/a con [spouse]" - married to
- "esposa de [husband]" / "esposo de [wife]" - spouse of
- "viuda de [late husband]" - widow of
- "hermano/a de [sibling]" - brother/sister of
- "heredero/a de [decedent]" - heir of

COMMON CUBAN PROPERTY TERMS:
- finca: farm/estate
- hacienda: large estate
- ingenio/central: sugar mill
- caballería: Cuban land unit (~13.4 hectares)
- colonia: sugar cane farm
- sitio: small plot
- folio/tomo: registry reference
```

```text
# domains/cuban_property/prompts/entity_extraction.txt.j2

{# Jinja2 template for entity extraction prompt #}
{{ system_context }}

Analyze the following OCR text and extract all entities with their detailed attributes.

ENTITY TYPES TO EXTRACT:
{% for entity_type, config in entity_types.items() %}
{{ loop.index }}. {{ entity_type }} - {{ config.description }}
{% endfor %}

{% for entity_type, config in entity_types.items() %}
{{ entity_type }} ENTITY SCHEMA:
{
  "entity_type": "{{ entity_type }}",
{% for field in config.core_fields + config.domain_fields %}
  "{{ field.name }}": {{ field.type_example | default('null') }},{% if field.extraction_hints %}  // Hints: {{ field.extraction_hints | join(', ') }}{% endif %}
{% endfor %}
  "confidence": 0.90,
  "context": "...quote from document...",
  "notes": null
}

{% endfor %}

DOCUMENT METADATA:
Document ID: {{ document_id }}
Document Type: {{ document_type }}
OCR Quality: {{ ocr_quality_desc }} ({{ ocr_quality }})
Language: {{ language }}

OCR TEXT:
{{ ocr_text }}

Respond with JSON in this format:
{
  "entities": [
    // Array of extracted entities
  ],
  "dates": [],
  "monetary_values": [],
  "registry_refs": [],
  "document_date": null,
  "extraction_notes": ""
}
```

---

## Implementation Plan

### Phase 1: Domain Loader Infrastructure

**Files to create:**
```
farmer_factory/
├── domains/
│   ├── __init__.py
│   ├── loader.py           # DomainLoader class
│   ├── registry.py         # DomainRegistry singleton
│   ├── models.py           # Pydantic models for domain configs
│   └── cuban_property/     # First domain
│       ├── __init__.py
│       ├── domain.yaml
│       ├── entities.yaml
│       ├── relations.yaml
│       └── prompts/
```

**Key classes:**

```python
# domains/models.py
from pydantic import BaseModel
from typing import Dict, List, Optional, Literal

class FieldDefinition(BaseModel):
    name: str
    type: str
    required: bool = False
    default: Optional[Any] = None
    description: Optional[str] = None
    extraction_hints: List[str] = []
    values: Optional[List[str]] = None  # For enums

class EntityTypeConfig(BaseModel):
    description: str
    icon: str
    color: str
    core_fields: List[FieldDefinition]
    domain_fields: List[FieldDefinition]
    known_entities: List[Dict[str, Any]] = []

class RelationTypeConfig(BaseModel):
    description: str
    category: str
    source_types: List[str]
    target_types: List[str]
    temporal: Literal["event", "state"]
    color: str
    symmetric: bool = False
    high_priority: bool = False
    extraction_hints: List[str] = []
    narrative_template: Optional[str] = None

class DomainConfig(BaseModel):
    name: str
    code: str
    version: str
    description: str
    primary_language: str
    supported_languages: List[str]
    temporal_range: Dict[str, str]
    geographic_focus: Dict[str, Any]
    use_cases: List[str]
    success_criteria: Dict[str, Any]
    entity_types: Dict[str, EntityTypeConfig]
    relation_types: Dict[str, RelationTypeConfig]
```

```python
# domains/loader.py
from pathlib import Path
import yaml
from .models import DomainConfig

class DomainLoader:
    """Load and validate domain configurations."""

    def __init__(self, domains_dir: Path = None):
        self.domains_dir = domains_dir or Path(__file__).parent
        self._cache: Dict[str, DomainConfig] = {}

    def load(self, domain_code: str) -> DomainConfig:
        """Load a domain configuration by code."""
        if domain_code in self._cache:
            return self._cache[domain_code]

        domain_path = self.domains_dir / domain_code
        if not domain_path.exists():
            raise ValueError(f"Domain '{domain_code}' not found")

        # Load and merge YAML files
        config = self._load_yaml_files(domain_path)

        # Validate with Pydantic
        domain_config = DomainConfig(**config)

        self._cache[domain_code] = domain_config
        return domain_config

    def list_domains(self) -> List[str]:
        """List available domain codes."""
        return [
            d.name for d in self.domains_dir.iterdir()
            if d.is_dir() and (d / "domain.yaml").exists()
        ]
```

```python
# domains/registry.py
from typing import Optional
from .loader import DomainLoader
from .models import DomainConfig

class DomainRegistry:
    """Singleton registry for active domain."""

    _instance: Optional["DomainRegistry"] = None
    _active_domain: Optional[DomainConfig] = None
    _loader: DomainLoader = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._loader = DomainLoader()
        return cls._instance

    def set_active(self, domain_code: str) -> DomainConfig:
        """Set the active domain for processing."""
        self._active_domain = self._loader.load(domain_code)
        return self._active_domain

    @property
    def active(self) -> DomainConfig:
        """Get the active domain configuration."""
        if self._active_domain is None:
            raise RuntimeError("No active domain set. Call set_active() first.")
        return self._active_domain

    def get_entity_types(self) -> List[str]:
        """Get entity types for active domain."""
        return list(self.active.entity_types.keys())

    def get_relation_types(self) -> List[str]:
        """Get relation types for active domain."""
        return list(self.active.relation_types.keys())

# Global instance
domain_registry = DomainRegistry()
```

### Phase 2: Refactor Schema Module

**Changes to `structure/schema.py`:**

1. Make `EntityType` and `RelationType` dynamic based on domain config
2. Generate Pydantic models dynamically from domain entity definitions
3. Keep backward compatibility with existing code

```python
# structure/schema.py (refactored)
from farmer_factory.domains.registry import domain_registry

def get_entity_type_enum():
    """Get EntityType enum for active domain."""
    from enum import Enum
    types = domain_registry.get_entity_types()
    return Enum("EntityType", {t: t for t in types})

def get_relation_type_enum():
    """Get RelationType enum for active domain."""
    from enum import Enum
    types = domain_registry.get_relation_types()
    return Enum("RelationType", {t: t for t in types})

# For backward compatibility during migration
EntityType = get_entity_type_enum()  # Will error until domain is set
RelationType = get_relation_type_enum()
```

### Phase 3: Refactor Extraction Prompts

**Changes to `extract/llm.py`:**

1. Load system context from domain prompts
2. Build entity/relation prompts from domain config
3. Use extraction hints from domain config

```python
# extract/llm.py (refactored)
from farmer_factory.domains.registry import domain_registry
from jinja2 import Environment, FileSystemLoader

class LLMExtractionService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.api_client = ClaudeAPIClient(api_key=api_key)
        self._jinja_env = None

    @property
    def jinja_env(self) -> Environment:
        if self._jinja_env is None:
            domain = domain_registry.active
            prompts_dir = Path(__file__).parent.parent / "domains" / domain.code / "prompts"
            self._jinja_env = Environment(loader=FileSystemLoader(prompts_dir))
        return self._jinja_env

    def _build_entity_prompt(self, text: str, document_id: str, ...) -> str:
        domain = domain_registry.active

        # Load system context
        system_context = (self.jinja_env.get_template("system_context.txt")
                         .render())

        # Build prompt from template
        template = self.jinja_env.get_template("entity_extraction.txt.j2")
        return template.render(
            system_context=system_context,
            entity_types=domain.entity_types,
            document_id=document_id,
            ocr_text=text,
            # ... other variables
        )
```

### Phase 4: Create Cuban Property Domain

Extract all Cuban-specific content into `domains/cuban_property/`:

1. `domain.yaml` - Domain manifest
2. `entities.yaml` - Entity type definitions
3. `relations.yaml` - Relation type definitions
4. `prompts/system_context.txt` - Cuban context
5. `prompts/entity_extraction.txt.j2` - Entity extraction template
6. `prompts/relation_extraction.txt.j2` - Relation extraction template
7. `taxonomies/document_types.yaml` - Document type vocabulary
8. `taxonomies/property_types.yaml` - Property type vocabulary

### Phase 5: CLI Domain Selection

**Changes to `cli.py`:**

```python
@click.option(
    "--domain", "-d",
    default="cuban_property",
    help="Domain configuration to use"
)
def process(case_id: str, domain: str, ...):
    """Process documents for a case."""
    from farmer_factory.domains.registry import domain_registry

    # Set active domain
    domain_config = domain_registry.set_active(domain)
    click.echo(f"Using domain: {domain_config.name} (v{domain_config.version})")

    # ... rest of processing
```

---

## Migration Strategy

### Backward Compatibility

During migration, maintain backward compatibility:

1. **Default domain**: If no domain specified, use `cuban_property`
2. **Existing code**: Keep existing enums working until refactor complete
3. **Tests**: All existing tests should pass with `cuban_property` domain

### Migration Steps

1. **Create domain infrastructure** (no changes to existing code)
2. **Create `cuban_property` domain** (extract from existing code)
3. **Verify equivalence** (domain config produces same behavior)
4. **Refactor extraction** (use domain prompts)
5. **Refactor schema** (dynamic entity/relation types)
6. **Update CLI** (add `--domain` flag)
7. **Update tests** (parameterize by domain)

---

## Example: Genealogy Domain (Future)

```yaml
# domains/genealogy/domain.yaml
domain:
  name: "Genealogical Research"
  code: "genealogy"
  version: "0.1.0"
  description: "Documentary recovery for family history and lineage research"

  primary_language: "en"
  supported_languages: ["en", "de", "it", "es", "fr"]

  temporal_range:
    start: "1700"
    end: "2000"

  use_cases:
    - "DAR/SAR applications"
    - "Citizenship claims (EU passport)"
    - "Family tree completion"
    - "Medical genealogy"

  success_criteria:
    primary_goal: "Verified lineage documentation"
    verification_target: "TIER_2_ANALYST"
    completeness_indicators:
      - "Birth-marriage-death chain complete"
      - "Vital records matched"
      - "Geographic migration documented"
```

```yaml
# domains/genealogy/entities.yaml
entity_types:
  PERSON:
    # Similar to cuban_property but with genealogy focus
    domain_fields:
      - name: birth_place
        type: string
        required: false
      - name: death_place
        type: string
        required: false
      - name: baptism_date
        type: date
        required: false
      - name: immigration_date
        type: date
        required: false
      - name: immigration_port
        type: string
        required: false

  VITAL_RECORD:
    description: "Birth, marriage, or death record"
    domain_fields:
      - name: record_type
        type: enum
        values: ["birth", "marriage", "death", "baptism", "burial"]
      - name: registry_location
        type: string
      - name: certificate_number
        type: string
```

---

## Acceptance Criteria

### Phase 1: Infrastructure
- [ ] `DomainLoader` loads and validates YAML configs
- [ ] `DomainRegistry` provides active domain access
- [ ] Domain models validate correctly with Pydantic

### Phase 2: Cuban Property Domain
- [ ] All Cuban-specific content extracted to config files
- [ ] Extraction produces identical results to current code
- [ ] All existing tests pass

### Phase 3: Dynamic Schema
- [ ] `EntityType` and `RelationType` generated from domain
- [ ] Entity models built dynamically from config
- [ ] Backward compatibility maintained

### Phase 4: CLI Integration
- [ ] `--domain` flag works on all commands
- [ ] Default domain is `cuban_property`
- [ ] Domain info displayed during processing

### Phase 5: Documentation
- [ ] Domain creation guide written
- [ ] API documentation updated
- [ ] Example genealogy domain sketched

---

*This document provides the technical specification for domain configuration. Implementation should proceed in phases to minimize disruption to existing functionality.*
