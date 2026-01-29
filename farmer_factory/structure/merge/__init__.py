"""Entity merge authority components."""

from .models import EntityGroupFile, MergeGroup, CrossTypeRelationsFile
from .reader import get_all_entity_groups, get_confirmed_merges, read_cross_type_relations
from .writer import write_entity_groups, write_cross_type_relations, add_analyst_merge
from .engine import apply_merges

__all__ = [
    "EntityGroupFile",
    "MergeGroup",
    "CrossTypeRelationsFile",
    "get_all_entity_groups",
    "get_confirmed_merges",
    "read_cross_type_relations",
    "write_entity_groups",
    "write_cross_type_relations",
    "add_analyst_merge",
    "apply_merges",
]
