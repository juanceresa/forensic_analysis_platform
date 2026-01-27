# Domain Configuration System

> **Version:** 1.0.0
> **Last Updated:** 2026-01-27
> **Status:** Production Ready

---

## Overview

The Domain Configuration System enables Civic Table to serve multiple documentary recovery domains from a shared technical core. Each domain defines its own entity types, relation types, extraction hints, and LLM prompts.

**Key Benefits:**
- Single codebase supports multiple use cases (Cuban property, Holocaust restitution, etc.)
- Domain-specific extraction hints improve LLM accuracy
- Configurable relation semantics (temporal vs. state relations)
- Custom prompt engineering per domain

---

## Architecture

```
farmer_factory/domains/
├── __init__.py          # Public API (domain_registry)
├── registry.py          # Singleton registry for active domain
├── loader.py            # YAML config loader
├── models.py            # Pydantic models for domain config
└── configs/
    └── cuban_property/
        ├── domain.yaml      # Main configuration
        └── prompts/
            └── system_context.txt  # LLM system prompt
```

### Domain Registry (Singleton)

The `domain_registry` singleton provides global access to the active domain configuration:

```python
from farmer_factory.domains import domain_registry

# Set active domain (typically at startup)
domain_registry.set_active("cuban_property")

# Access configuration
config = domain_registry.active
print(config.name)  # "Cuban Property Restitution"

# Get entity/relation types
entity_types = domain_registry.get_entity_types()
relation_types = domain_registry.get_relation_types()

# Get temporal vs state relations (for date handling)
temporal_rels = domain_registry.get_temporal_relations()
state_rels = domain_registry.get_state_relations()
```

---

## Configuration Files

### domain.yaml

The main configuration file defines entity types, relation types, and extraction settings:

```yaml
# Domain identity
code: cuban_property
name: "Cuban Property Restitution"
version: "1.0.0"
description: "Documentary recovery for Cuban property claims"

# Entity types with field configurations
entity_types:
  PERSON:
    description: "Individual with legal standing"
    primary_fields:
      - name
      - birth_date
    optional_fields:
      - death_date
      - nationality
      - residence

  PROPERTY:
    description: "Real estate asset"
    primary_fields:
      - name
      - property_type
    optional_fields:
      - area
      - registry_number

# Relation types with temporal classification
relation_types:
  OWNS:
    description: "Current ownership"
    temporal: false  # State relation (ongoing)
    source_types: [PERSON, ORGANIZATION]
    target_types: [PROPERTY]
    extraction_hints:
      - "propietario de"
      - "dueño de"
      - "owner of"

  CONFISCATED:
    description: "Government expropriation"
    temporal: true  # Event relation (needs date)
    priority: high  # Highlight in narratives
    source_types: [ORGANIZATION]
    target_types: [PROPERTY]
    extraction_hints:
      - "confiscado"
      - "expropiado"
      - "nationalizado"

# Path to prompts directory (relative to domain.yaml)
prompts_dir: "prompts"
```

### system_context.txt

Domain-specific system context injected into LLM prompts:

```text
You are analyzing historical Cuban property documents from 1940-1970.
These documents include deeds, wills, mortgage certificates, and notarial acts.

Key context:
- Cuba nationalized private property in 1959-1960
- Spanish colonial land grants created complex ownership chains
- Common document types: escritura, testamento, hipoteca, certificación
- Currency was Cuban pesos (CUP) before 1959

Focus on extracting:
- Property ownership chains (who owned what, when)
- Family relationships (inheritance, marriage)
- Financial transactions (sales, mortgages)
- Expropriation events (confiscations, nationalizations)
```

---

## Dynamic Type Generation

Entity and relation types are generated dynamically from domain configuration, not hardcoded enums.

### How It Works

1. **At import time:** Default fallback types are used if no domain is active
2. **At runtime:** When `domain_registry.set_active()` is called, types are loaded from config
3. **Schema validation:** Pydantic validators check types against active domain config

```python
# In farmer_factory/structure/schema.py

def get_valid_entity_types() -> Set[str]:
    """Get entity types from domain config, or defaults."""
    if domain_registry.is_active:
        return set(domain_registry.get_entity_types())
    # Fallback defaults
    return {"PERSON", "PROPERTY", "ORGANIZATION", "LOCATION", "DOCUMENT"}

class BaseEntity(BaseModel):
    entity_type: str  # Validated against domain config

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        valid_types = get_valid_entity_types()
        if v not in valid_types:
            raise ValueError(f"Invalid entity type '{v}'")
        return v
```

### Refreshing Types

After setting the active domain, call `refresh_type_enums()` to update dynamic enums:

```python
from farmer_factory.domains import domain_registry
from farmer_factory.structure.schema import refresh_type_enums

domain_registry.set_active("cuban_property")
refresh_type_enums()  # Updates EntityType and RelationType enums
```

---

## CLI Integration

All CLI commands support the `--domain` flag:

```bash
# Create case with specific domain
python -m farmer_factory.cli create-case \
    --id CASE-001 \
    --name "Ceresa Archive" \
    --family "Ceresa" \
    --domain cuban_property

# Process with domain
python -m farmer_factory.cli process CASE-001 --domain cuban_property

# Validate with domain
python -m farmer_factory.cli validate CASE-001 --domain cuban_property

# List available domains
python -m farmer_factory.cli list-domains
```

Default domain is `cuban_property` if not specified.

---

## Domain-Aware Extraction

The LLM extraction service uses domain configuration for:

1. **System Context:** Loaded from `prompts/system_context.txt`
2. **Extraction Hints:** Injected into relation extraction prompts
3. **Temporal Logic:** Different handling for events vs. states

```python
# In farmer_factory/extract/llm.py

def load_system_context() -> str:
    """Load system context from active domain."""
    if not domain_registry.is_active:
        return ""
    prompts_dir = domain_registry.active.prompts_dir
    context_file = Path(prompts_dir) / "system_context.txt"
    return context_file.read_text() if context_file.exists() else ""

def get_relation_extraction_hints() -> Dict[str, List[str]]:
    """Get extraction hints from domain config."""
    hints = {}
    for rel_type, config in domain_registry.active.relation_types.items():
        if config.extraction_hints:
            hints[rel_type] = config.extraction_hints
    return hints
```

---

## Creating a New Domain

1. Create directory: `farmer_factory/domains/configs/my_domain/`

2. Create `domain.yaml`:
```yaml
code: my_domain
name: "My Domain Name"
version: "1.0.0"
description: "Description of the domain"

entity_types:
  # Define entity types...

relation_types:
  # Define relation types...

prompts_dir: "prompts"
```

3. Create `prompts/system_context.txt` with domain-specific context

4. Use the domain:
```bash
python -m farmer_factory.cli process CASE-001 --domain my_domain
```

---

## API Reference

### DomainRegistry

| Method | Description |
|--------|-------------|
| `set_active(code)` | Set the active domain by code |
| `active` | Get active DomainConfig (raises if none) |
| `is_active` | Check if a domain is active |
| `active_code` | Get active domain code or None |
| `get_entity_types()` | List entity type names |
| `get_relation_types()` | List relation type names |
| `get_temporal_relations()` | List event/temporal relations |
| `get_state_relations()` | List state/ongoing relations |
| `get_high_priority_relations()` | List relations to highlight |
| `list_available_domains()` | List all loadable domain codes |
| `reload_active()` | Reload config from disk |

### DomainConfig

| Property | Type | Description |
|----------|------|-------------|
| `code` | str | Domain identifier |
| `name` | str | Display name |
| `version` | str | Config version |
| `description` | str | Domain description |
| `entity_types` | Dict[str, EntityTypeConfig] | Entity configurations |
| `relation_types` | Dict[str, RelationTypeConfig] | Relation configurations |
| `prompts_dir` | Path | Path to prompts directory |

---

## Testing with Domains

Tests use a session-scoped fixture to set up the domain:

```python
# tests/conftest.py

@pytest.fixture(scope="session", autouse=True)
def setup_domain():
    """Set up domain for all tests."""
    from farmer_factory.domains import domain_registry
    from farmer_factory.structure.schema import refresh_type_enums

    domain_registry.set_active("cuban_property")
    refresh_type_enums()
    yield
```

For domain-specific tests:

```python
def test_with_specific_domain():
    domain_registry.set_active("my_domain")
    refresh_type_enums()
    # Run domain-specific tests
```

---

## Troubleshooting

### "No active domain set"

```python
RuntimeError: No active domain set. Call domain_registry.set_active('domain_code') first.
```

**Solution:** Set the domain before using domain-dependent code:
```python
from farmer_factory.domains import domain_registry
domain_registry.set_active("cuban_property")
```

### "Unknown domain"

```
ClickException: Unknown domain 'foo'. Available: cuban_property
```

**Solution:** Check available domains with `list-domains` command or ensure your domain config exists in `farmer_factory/domains/configs/`.

### Types not updating after domain change

**Solution:** Call `refresh_type_enums()` after `set_active()`:
```python
from farmer_factory.structure.schema import refresh_type_enums
refresh_type_enums()
```
