"""Dedupe field configurations for entity types (dedupe 3.0 API).

Updated 2026-01-25 to match v1.2.0 schema with family relationships.

IMPORTANT: Family relationship fields (mother, father, spouse, children, siblings)
are intentionally NOT used for matching. They're for data enrichment, not deduplication.
Matching on family names would create false positives (siblings share parents).
"""

import dedupe.variables

# Person fields - multi-attribute matching
PERSON_FIELDS = [
    # Core identity - PRIMARY matching field
    dedupe.variables.String('name', has_missing=True),

    # Demographics - SECONDARY matching fields (help distinguish people with common names)
    dedupe.variables.String('birth_date', has_missing=True),
    dedupe.variables.String('death_date', has_missing=True),
    dedupe.variables.String('residence', has_missing=True),
    dedupe.variables.String('profession', has_missing=True),
    dedupe.variables.String('nationality', has_missing=True),
    dedupe.variables.String('marital_status', has_missing=True),

    # Note: Family fields (mother, father, spouse, children, siblings) are excluded
    # from matching to avoid false positives. These are stored for genealogical
    # research but don't help distinguish between different people.
    # Example: Two siblings share the same parents - matching on "father" would
    # incorrectly merge them into one person.
]

# Location fields
LOCATION_FIELDS = [
    dedupe.variables.String('name', has_missing=True),
    dedupe.variables.String('location_type', has_missing=True),
    dedupe.variables.String('country', has_missing=True),
    dedupe.variables.String('parent_location_id', has_missing=True),
]

# Property fields
PROPERTY_FIELDS = [
    dedupe.variables.String('name', has_missing=True),
    dedupe.variables.String('property_type', has_missing=True),
    dedupe.variables.String('location_id', has_missing=True),
    dedupe.variables.Price('area', has_missing=True),
]

# Organization fields
ORGANIZATION_FIELDS = [
    dedupe.variables.String('name', has_missing=True),
    dedupe.variables.String('org_type', has_missing=True),
    dedupe.variables.String('location_id', has_missing=True),
]

# Field configuration mapping
FIELD_CONFIG = {
    'PERSON': PERSON_FIELDS,
    'LOCATION': LOCATION_FIELDS,
    'PROPERTY': PROPERTY_FIELDS,
    'ORGANIZATION': ORGANIZATION_FIELDS,
}
