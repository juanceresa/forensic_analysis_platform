import type { BaseNode, VerificationTier, EntityType } from './types';

export function getNodeColor(node: BaseNode): string {
  const tierColors: Record<VerificationTier, string> = {
    TIER_1_CERTIFIED: '#3B82F6',     // Blue
    TIER_2_INSTITUTIONAL: '#D97706',  // Dark Amber
    TIER_2_ANALYST: '#F59E0B',        // Amber
    TIER_3_AI: '#6B7280',             // Gray
  };
  return tierColors[node.verification.tier];
}

export function getNodeSize(node: BaseNode): number {
  const sizeMap: Record<EntityType, number> = {
    PROPERTY: 8,
    PERSON: 6,
    ORGANIZATION: 6,
    LOCATION: 5,
    DOCUMENT: 4,
  };
  return sizeMap[node.entity_type] || 5;
}
