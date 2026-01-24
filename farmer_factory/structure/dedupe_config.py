"""Dedupe field configurations for entity types."""

# Person fields - multi-attribute matching
PERSON_FIELDS = [
    {'field': 'name', 'type': 'String'},
    {'field': 'birth_date', 'type': 'String', 'has missing': True},
    {'field': 'death_date', 'type': 'String', 'has missing': True},
    {'field': 'residence', 'type': 'String', 'has missing': True},
    {'field': 'profession', 'type': 'String', 'has missing': True},
    {'field': 'nationality', 'type': 'String', 'has missing': True},
]

# Location fields
LOCATION_FIELDS = [
    {'field': 'name', 'type': 'String'},
    {'field': 'location_type', 'type': 'String', 'has missing': True},
    {'field': 'country', 'type': 'String', 'has missing': True},
    {'field': 'parent_location_id', 'type': 'String', 'has missing': True},
]

# Property fields
PROPERTY_FIELDS = [
    {'field': 'name', 'type': 'String', 'has missing': True},
    {'field': 'property_type', 'type': 'String', 'has missing': True},
    {'field': 'location_id', 'type': 'String', 'has missing': True},
    {'field': 'area', 'type': 'Price', 'has missing': True},
]

# Organization fields
ORGANIZATION_FIELDS = [
    {'field': 'name', 'type': 'String'},
    {'field': 'org_type', 'type': 'String', 'has missing': True},
    {'field': 'location_id', 'type': 'String', 'has missing': True},
]

# Field configuration mapping
FIELD_CONFIG = {
    'PERSON': PERSON_FIELDS,
    'LOCATION': LOCATION_FIELDS,
    'PROPERTY': PROPERTY_FIELDS,
    'ORGANIZATION': ORGANIZATION_FIELDS,
}
