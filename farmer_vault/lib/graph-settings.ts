/**
 * Graph Settings Configuration
 *
 * Defines types and defaults for customizable graph visualization parameters.
 * Settings persist to localStorage for user preferences.
 */

import type { EntityType } from './types';

export type EntityColorMap = Record<EntityType, string>;

export interface GraphSettings {
  // Display Settings
  nodeSizeMultiplier: number;    // Scale factor for degree-based sizing
  linkWidth: number;             // Link thickness
  showArrows: boolean;           // Show directional arrows on links

  // Force Simulation Settings
  centerForce: number;           // Gravity toward center (0-2)
  repelForce: number;            // Repulsion between nodes (positive value, applied as negative)
  linkForce: number;             // Target distance between connected nodes

  // Color Settings
  entityColors: EntityColorMap;
  linkColor: string;            // Base link color

  // Filter Settings
  entityTypeFilters: Record<EntityType, boolean>; // true = visible
  hideOrphans: boolean;         // Hide nodes with no connections
}

export const DEFAULT_SETTINGS: GraphSettings = {
  // Display
  nodeSizeMultiplier: 2,
  linkWidth: 2,
  showArrows: false,

  // Forces
  centerForce: 0.1,
  repelForce: 140,
  linkForce: 60,

  // Colors
  entityColors: {
    PERSON: '#7c3aed',
    LOCATION: '#0891b2',
    PROPERTY: '#059669',
    ORGANIZATION: '#dc2626',
    DOCUMENT: '#64748b',
  },
  linkColor: '#ffffff',

  // Filters
  entityTypeFilters: {
    PERSON: true,
    LOCATION: true,
    PROPERTY: true,
    ORGANIZATION: true,
    DOCUMENT: true,
  },
  hideOrphans: false,
};

export interface SettingRange {
  min: number;
  max: number;
  step: number;
}

export const SETTINGS_RANGES: Record<keyof GraphSettings, SettingRange> = {
  // Display
  nodeSizeMultiplier: { min: 0.5, max: 5, step: 0.5 },
  linkWidth: { min: 0.2, max: 4, step: 0.1 },
  showArrows: { min: 0, max: 1, step: 1 }, // Boolean toggle (not used by sliders)

  // Forces
  centerForce: { min: 0, max: 1.2, step: 0.05 },
  repelForce: { min: 40, max: 200, step: 5 },
  linkForce: { min: 30, max: 140, step: 5 },

  // Colors (not used by sliders)
  entityColors: { min: 0, max: 0, step: 0 },
  linkColor: { min: 0, max: 0, step: 0 },

  // Filters (not used by sliders)
  entityTypeFilters: { min: 0, max: 0, step: 0 },
  hideOrphans: { min: 0, max: 1, step: 1 }, // Boolean toggle
};

export const SETTING_LABELS: Record<keyof GraphSettings, string> = {
  nodeSizeMultiplier: 'Node Scale',
  linkWidth: 'Link Width',
  showArrows: 'Show Arrows',
  centerForce: 'Center Force',
  repelForce: 'Repel Force',
  linkForce: 'Link Distance',
  entityColors: 'Entity Colors',
  linkColor: 'Link Color',
  entityTypeFilters: 'Entity Type Filters',
  hideOrphans: 'Hide Orphans',
};

export const SETTING_DESCRIPTIONS: Record<keyof GraphSettings, string> = {
  nodeSizeMultiplier: 'Size scaling for connected nodes',
  linkWidth: 'Thickness of connection lines',
  showArrows: 'Show directional arrows on links',
  centerForce: 'Pull toward center',
  repelForce: 'Push nodes apart',
  linkForce: 'Target distance between connected nodes',
  entityColors: 'Custom colors for entity types',
  linkColor: 'Base color for connection lines',
  entityTypeFilters: 'Control visibility of entity types',
  hideOrphans: 'Hide nodes with no connections',
};
