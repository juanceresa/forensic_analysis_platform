import { useState, useEffect, useCallback } from 'react';
import { GraphSettings, DEFAULT_SETTINGS } from '@/lib/graph-settings';

const STORAGE_KEY = 'graph-settings';

/**
 * Custom hook for managing graph visualization settings with localStorage persistence.
 *
 * @returns Object with current settings, update function, and reset function
 *
 * @example
 * const { settings, updateSetting, resetSettings } = useGraphSettings();
 * updateSetting('nodeSizeMultiplier', 2);
 * resetSettings();
 */
export function useGraphSettings() {
  const [settings, setSettings] = useState<GraphSettings>(DEFAULT_SETTINGS);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load settings from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as GraphSettings;
        // Merge with defaults (deep merge for entityColors)
        setSettings({
          ...DEFAULT_SETTINGS,
          ...parsed,
          entityColors: {
            ...DEFAULT_SETTINGS.entityColors,
            ...(parsed.entityColors || {}),
          },
        });
      }
    } catch (error) {
      console.error('Failed to load graph settings from localStorage:', error);
      // Fall back to defaults on error
    } finally {
      setIsLoaded(true);
    }
  }, []);

  // Save settings to localStorage whenever they change
  useEffect(() => {
    if (!isLoaded) return; // Don't save initial load

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch (error) {
      console.error('Failed to save graph settings to localStorage:', error);
    }
  }, [settings, isLoaded]);

  // Update a single setting
  const updateSetting = useCallback(
    <K extends keyof GraphSettings>(key: K, value: GraphSettings[K]) => {
      setSettings((prev) => ({
        ...prev,
        [key]: value,
      }));
    },
    []
  );

  // Reset all settings to defaults
  const resetSettings = useCallback(() => {
    setSettings(DEFAULT_SETTINGS);
  }, []);

  return {
    settings,
    updateSetting,
    resetSettings,
    isLoaded,
  };
}
