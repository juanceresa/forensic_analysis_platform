import type { BaseNode, EntityType } from './types';
import { ENTITY_COLORS } from './graph-settings';

export function getNodeColor(node: BaseNode): string {
  return ENTITY_COLORS[node.entity_type] || '#64748b';
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
