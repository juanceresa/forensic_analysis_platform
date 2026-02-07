/**
 * Graph Settings Configuration
 *
 * Simplified settings for graph visualization.
 * Removed: force tuning, color pickers, size sliders (use smart defaults).
 * Kept: toggle controls that belong in the toolbar.
 */

import type { EntityType } from './types';
import { RELATION_CATEGORIES } from './relation-categories';

export interface GraphSettings {
  showArrows: boolean;
  hideOrphans: boolean;
  entityTypeFilters: Record<EntityType, boolean>;
  relationCategoryVisibility: Record<string, boolean>;
}

// Build default relation visibility from categories
const defaultRelationVisibility: Record<string, boolean> = {};
for (const key of Object.keys(RELATION_CATEGORIES)) {
  defaultRelationVisibility[key] = true;
}

export const DEFAULT_SETTINGS: GraphSettings = {
  showArrows: true,
  hideOrphans: false,
  entityTypeFilters: {
    PERSON: true,
    LOCATION: true,
    PROPERTY: true,
    ORGANIZATION: true,
    DOCUMENT: true,
  },
  relationCategoryVisibility: defaultRelationVisibility,
};

/** Hardcoded entity colors — single source of truth */
export const ENTITY_COLORS: Record<EntityType, string> = {
  PERSON: '#7c3aed',
  LOCATION: '#0891b2',
  PROPERTY: '#059669',
  ORGANIZATION: '#dc2626',
  DOCUMENT: '#64748b',
};

export const ENTITY_LABELS: Record<EntityType, string> = {
  PERSON: 'Person',
  PROPERTY: 'Property',
  ORGANIZATION: 'Organization',
  LOCATION: 'Location',
  DOCUMENT: 'Document',
};
