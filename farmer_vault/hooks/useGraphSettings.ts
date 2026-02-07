import { useState, useEffect, useCallback } from 'react';
import { type GraphSettings, DEFAULT_SETTINGS } from '@/lib/graph-settings';

const STORAGE_KEY = 'graph-settings-v2';

export function useGraphSettings() {
  const [settings, setSettings] = useState<GraphSettings>(DEFAULT_SETTINGS);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as Partial<GraphSettings>;
        setSettings({
          ...DEFAULT_SETTINGS,
          ...parsed,
          entityTypeFilters: {
            ...DEFAULT_SETTINGS.entityTypeFilters,
            ...(parsed.entityTypeFilters || {}),
          },
          relationCategoryVisibility: {
            ...DEFAULT_SETTINGS.relationCategoryVisibility,
            ...(parsed.relationCategoryVisibility || {}),
          },
        });
      }
    } catch {
      // Fall back to defaults
    } finally {
      setIsLoaded(true);
    }
  }, []);

  useEffect(() => {
    if (!isLoaded) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch {
      // Ignore write failures
    }
  }, [settings, isLoaded]);

  const updateSetting = useCallback(
    <K extends keyof GraphSettings>(key: K, value: GraphSettings[K]) => {
      setSettings((prev) => ({ ...prev, [key]: value }));
    },
    []
  );

  const resetSettings = useCallback(() => {
    setSettings(DEFAULT_SETTINGS);
  }, []);

  return { settings, updateSetting, resetSettings, isLoaded };
}
