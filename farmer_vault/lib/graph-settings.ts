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
  nodeSizeBase: number;          // Base node radius in pixels
  nodeSizeMultiplier: number;    // Scale factor for degree-based sizing
  linkWidth: number;             // Standard link thickness
  constellationLinkWidth: number; // Highlighted constellation link thickness
  showArrows: boolean;           // Show directional arrows on links

  // Force Simulation Settings
  centerForce: number;           // Gravity toward center (0-2)
  repelForce: number;            // Repulsion between nodes (positive value, applied as negative)
  linkForce: number;             // Target distance between connected nodes

  // Color Settings
  entityColors: EntityColorMap;
}

export const DEFAULT_SETTINGS: GraphSettings = {
  // Display
  nodeSizeBase: 5.5,
  nodeSizeMultiplier: 2,
  linkWidth: 2,
  constellationLinkWidth: 1.5,
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
};

export interface SettingRange {
  min: number;
  max: number;
  step: number;
}

export const SETTINGS_RANGES: Record<keyof GraphSettings, SettingRange> = {
  // Display
  nodeSizeBase: { min: 2, max: 12, step: 0.5 },
  nodeSizeMultiplier: { min: 0.5, max: 5, step: 0.5 },
  linkWidth: { min: 0.2, max: 4, step: 0.1 },
  constellationLinkWidth: { min: 0.5, max: 4, step: 0.5 },
  showArrows: { min: 0, max: 1, step: 1 }, // Boolean toggle (not used by sliders)

  // Forces
  centerForce: { min: 0, max: 1.2, step: 0.05 },
  repelForce: { min: 40, max: 200, step: 5 },
  linkForce: { min: 30, max: 140, step: 5 },

  // Colors (not used by sliders)
  entityColors: { min: 0, max: 0, step: 0 },
};

export const SETTING_LABELS: Record<keyof GraphSettings, string> = {
  nodeSizeBase: 'Node Size',
  nodeSizeMultiplier: 'Node Scale',
  linkWidth: 'Link Width',
  constellationLinkWidth: 'Highlight Width',
  showArrows: 'Show Arrows',
  centerForce: 'Center Force',
  repelForce: 'Repel Force',
  linkForce: 'Link Distance',
  entityColors: 'Entity Colors',
};

export const SETTING_DESCRIPTIONS: Record<keyof GraphSettings, string> = {
  nodeSizeBase: 'Base size of all nodes',
  nodeSizeMultiplier: 'Size scaling for connected nodes',
  linkWidth: 'Thickness of connection lines',
  constellationLinkWidth: 'Thickness of highlighted connections',
  centerForce: 'Pull toward center',
  repelForce: 'Push nodes apart',
  linkForce: 'Target distance between connected nodes',
  entityColors: 'Custom colors for entity types',
};
