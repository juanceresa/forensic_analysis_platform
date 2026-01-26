import type { BaseNode, VerificationTier, EntityType } from './types';

export function getNodeColor(node: BaseNode): string {
  const entityColors: Record<EntityType, string> = {
    PERSON: '#7c3aed',       // Purple/Violet
    LOCATION: '#0891b2',     // Cyan
    PROPERTY: '#059669',     // Green
    ORGANIZATION: '#dc2626', // Red
    DOCUMENT: '#64748b',     // Slate/Gray
  };
  return entityColors[node.entity_type] || '#64748b';
}

export function getNodeSize(node: BaseNode): number {
  const sizeMap: Record<EntityType, number> = {
    PROPERTY: 6,
    PERSON: 5,
    ORGANIZATION: 5,
    LOCATION: 4,
    DOCUMENT: 3,
  };
  return sizeMap[node.entity_type] || 4;
}
