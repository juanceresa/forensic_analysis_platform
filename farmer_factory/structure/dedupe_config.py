"""Dedupe field configurations for entity types (dedupe 3.0 API)."""

import dedupe.variables

# Person fields - multi-attribute matching
PERSON_FIELDS = [
    dedupe.variables.String('name'),
    dedupe.variables.String('birth_date', has_missing=True),
    dedupe.variables.String('death_date', has_missing=True),
    dedupe.variables.String('residence', has_missing=True),
    dedupe.variables.String('profession', has_missing=True),
    dedupe.variables.String('nationality', has_missing=True),
]

# Location fields
LOCATION_FIELDS = [
    dedupe.variables.String('name'),
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
    dedupe.variables.String('name'),
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
