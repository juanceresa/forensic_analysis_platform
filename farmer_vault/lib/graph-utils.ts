import type { BaseNode, VerificationTier, EntityType } from './types';

export function getNodeColor(node: BaseNode): string {
  const tierColors: Record<VerificationTier, string> = {
    TIER_1_CERTIFIED: '#06B6D4',     // Cyan - Certified
    TIER_2_ANALYST: '#3B82F6',       // Blue - Analyst Verified
    TIER_2_INSTITUTIONAL: '#8B5CF6', // Purple - Institutional
    TIER_3_AI: '#64748B',            // Slate - AI Generated
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
