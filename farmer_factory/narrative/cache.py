"""Session-scoped caching for narrative generation with graph-state invalidation."""

import hashlib
import time
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Set

from farmer_factory.structure.graph import KnowledgeGraph

logger = logging.getLogger(__name__)


class NarrativeCache(ABC):
    """Abstract base class for narrative caching."""

    @abstractmethod
    def get(
        self,
        session_id: str,
        focal_entity_id: str,
        graph_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached narrative."""
        pass

    @abstractmethod
    def set(
        self,
        session_id: str,
        focal_entity_id: str,
        graph_hash: str,
        data: Dict[str, Any],
        ttl: int
    ) -> bool:
        """Store narrative in cache."""
        pass

    @abstractmethod
    def invalidate_session(self, session_id: str) -> int:
        """Invalidate all cached narratives for a session."""
        pass

    def generate_cache_key(
        self,
        session_id: str,
        focal_entity_id: str,
        graph_hash: str
    ) -> str:
        """Generate cache key."""
        return f"narrative:{session_id}:{focal_entity_id}:{graph_hash}"

    def calculate_graph_hash(
        self,
        constellation: Set[str],
        graph: KnowledgeGraph
    ) -> str:
        """
        Calculate hash of graph state for constellation.

        Hash includes:
        - Entity verification tiers
        - Constellation membership
        - Relation count and types

        Args:
            constellation: Set of entity IDs
            graph: Knowledge graph

        Returns:
            Hash string
        """
        hash_components = []

        # Sort entities for consistent hashing
        sorted_entities = sorted(constellation)

        for entity_id in sorted_entities:
            entity = graph.get_entity(entity_id)
            if entity:
                # Include verification tier (changes when analyst verifies)
                verification = entity.get("verification", {})
                tier = verification.get("tier", "UNKNOWN")
                confidence = verification.get("confidence", 0.0)

                hash_components.append(f"{entity_id}:{tier}:{confidence:.2f}")

        # Include relation count
        relation_count = 0
        for entity_id in constellation:
            relations = graph.get_relations(entity_id, direction="both")
            relation_count += len(relations)

        hash_components.append(f"relations:{relation_count}")

        # Calculate hash
        hash_input = "|".join(hash_components)
        graph_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

        return graph_hash


class InMemoryCache(NarrativeCache):
    """In-memory cache implementation for MVP1 (single server)."""

    def __init__(self, default_ttl: int = 3600):
        """
        Initialize in-memory cache.

        Args:
            default_ttl: Default TTL in seconds (1 hour)
        """
        self.cache: Dict[str, Any] = {}
        self.timestamps: Dict[str, float] = {}
        self.default_ttl = default_ttl

    def get(
        self,
        session_id: str,
        focal_entity_id: str,
        graph_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached narrative."""
        key = self.generate_cache_key(session_id, focal_entity_id, graph_hash)

        # Check if exists
        if key not in self.cache:
            logger.info(f"Cache miss: {key}")
            return None

        # Check TTL
        timestamp = self.timestamps.get(key, 0)
        if time.time() >= timestamp:
            # Expired
            del self.cache[key]
            del self.timestamps[key]
            logger.info(f"Cache expired: {key}")
            return None

        logger.info(f"Cache hit: {key}")
        return self.cache[key]

    def set(
        self,
        session_id: str,
        focal_entity_id: str,
        graph_hash: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Store narrative in cache."""
        key = self.generate_cache_key(session_id, focal_entity_id, graph_hash)
        if ttl is None:
            ttl = self.default_ttl

        self.cache[key] = data
        self.timestamps[key] = time.time() + ttl

        logger.info(f"Cached narrative: {key} (TTL={ttl}s)")
        return True

    def invalidate_session(self, session_id: str) -> int:
        """Invalidate all cached narratives for a session."""
        prefix = f"narrative:{session_id}:"
        keys_to_delete = [k for k in self.cache.keys() if k.startswith(prefix)]

        for key in keys_to_delete:
            del self.cache[key]
            if key in self.timestamps:
                del self.timestamps[key]

        logger.info(f"Invalidated {len(keys_to_delete)} narratives for session {session_id}")
        return len(keys_to_delete)


# Future: Redis implementation for MVP2
# class RedisCache(NarrativeCache):
#     """Redis cache implementation for production (horizontal scaling)."""
#
#     def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
#         import redis
#         self.client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
#
#     def get(self, session_id, focal_entity_id, graph_hash):
#         key = self.generate_cache_key(session_id, focal_entity_id, graph_hash)
#         cached = self.client.get(key)
#         return json.loads(cached) if cached else None
#
#     def set(self, session_id, focal_entity_id, graph_hash, data, ttl):
#         key = self.generate_cache_key(session_id, focal_entity_id, graph_hash)
#         self.client.setex(key, ttl, json.dumps(data))
#         return True
#
#     def invalidate_session(self, session_id):
#         pattern = f"narrative:{session_id}:*"
#         keys = self.client.keys(pattern)
#         if keys:
#             return self.client.delete(*keys)
#         return 0
