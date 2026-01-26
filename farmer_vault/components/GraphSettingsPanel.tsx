'use client';

import { useState, useRef, useEffect, useId } from 'react';
import type { GraphSettings } from '@/lib/graph-settings';
import { SETTINGS_RANGES, SETTING_LABELS, DEFAULT_SETTINGS } from '@/lib/graph-settings';

interface GraphSettingsPanelProps {
  settings: GraphSettings;
  onUpdateSetting: <K extends keyof GraphSettings>(key: K, value: GraphSettings[K]) => void;
  onReset: () => void;
}

/**
 * Floating settings panel for graph visualization controls.
 * Features collapsible sections and styled sliders for real-time adjustments.
 */
export function GraphSettingsPanel({
  settings,
  onUpdateSetting,
  onReset,
}: GraphSettingsPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'layout' | 'colors'>('layout');
  const panelRef = useRef<HTMLDivElement>(null);

  // Click-outside-to-close behavior
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    // Add listener after a brief delay to avoid immediate close on open
    const timer = setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside);
    }, 100);

    return () => {
      clearTimeout(timer);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div ref={panelRef} className="vault-graph-controls absolute top-4 left-4 font-mono" style={{ zIndex: 1000, pointerEvents: 'auto' }}>
      {/* Gear Icon Toggle */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`
          flex items-center justify-center w-11 h-11 rounded-xl
          bg-slate-900/98 border transition-all duration-300 backdrop-blur-md
          ${
            isOpen
              ? 'border-cyan-500/60 shadow-[0_0_24px_rgba(6,182,212,0.35),0_0_4px_rgba(6,182,212,0.2)_inset] scale-105'
              : 'border-slate-700/60 hover:border-cyan-500/40 hover:shadow-[0_0_16px_rgba(6,182,212,0.15)] hover:scale-102'
          }
          focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900
        `}
        aria-label={isOpen ? 'Close graph settings' : 'Open graph settings'}
        aria-expanded={isOpen}
      >
        <svg
          className={`w-5 h-5 transition-all duration-400 ${
            isOpen ? 'text-cyan-400 rotate-180 scale-110' : 'text-slate-400 rotate-0 scale-100'
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
      </button>

      {/* Settings Panel with slide-in animation */}
      {isOpen && (
        <div
          className="mt-3 rounded-xl bg-slate-900/98 backdrop-blur-xl
            animate-slide-in motion-reduce:animate-none flex flex-col"
          role="region"
          aria-label="Graph settings panel"
          style={{
            animation: 'slideIn 250ms cubic-bezier(0.16, 1, 0.3, 1) forwards',
            width: 'var(--graph-controls-width)',
            maxHeight: 'calc(100vh - 120px)',
            border: '1px solid rgba(110, 219, 227, 0.18)',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.45), 0 0 0 1px rgba(110, 219, 227, 0.08) inset, 0 0 32px rgba(6, 182, 212, 0.15)',
            pointerEvents: 'auto'
          }}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-slate-800 shrink-0">
            <h3 className="text-sm font-semibold text-cyan-400 uppercase tracking-wide">
              Graph Settings
            </h3>
            <button
              onClick={onReset}
              className="px-3 py-1 text-xs text-slate-400 hover:text-amber-400
                border border-slate-700 hover:border-amber-500/50 rounded transition-colors transition-shadow duration-200
                hover:shadow-[0_0_8px_rgba(251,191,36,0.3)]"
              aria-label="Reset all settings to defaults"
            >
              Reset
            </button>
          </div>

          {/* Tab Bar */}
          <div className="flex border-b border-slate-800 shrink-0">
            <button
              onClick={() => setActiveTab('layout')}
              className={`flex-1 px-4 py-2 text-xs uppercase tracking-wider transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 ${
                activeTab === 'layout'
                  ? 'text-cyan-300 border-b-2 border-cyan-400'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
              aria-pressed={activeTab === 'layout'}
            >
              Layout
            </button>
            <button
              onClick={() => setActiveTab('colors')}
              className={`flex-1 px-4 py-2 text-xs uppercase tracking-wider transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 ${
                activeTab === 'colors'
                  ? 'text-cyan-300 border-b-2 border-cyan-400'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
              aria-pressed={activeTab === 'colors'}
            >
              Colors
            </button>
          </div>

          {/* Settings Sections - Scrollable */}
          <div className="p-4 space-y-6 overflow-y-auto overflow-x-hidden" style={{ pointerEvents: 'auto' }}>
            {activeTab === 'layout' ? (
              <>
                {/* Display Section */}
                <section className="graph-control-section">
                  <h4 className="graph-control-section-header text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 pb-2 border-b border-slate-800/50">
                    Display
                  </h4>
                  <div className="space-y-3">
                    <SettingsSlider
                      label={SETTING_LABELS.nodeSizeBase}
                      value={settings.nodeSizeBase}
                      onChange={(v) => onUpdateSetting('nodeSizeBase', v)}
                      range={SETTINGS_RANGES.nodeSizeBase}
                    />
                    <SettingsSlider
                      label={SETTING_LABELS.nodeSizeMultiplier}
                      value={settings.nodeSizeMultiplier}
                      onChange={(v) => onUpdateSetting('nodeSizeMultiplier', v)}
                      range={SETTINGS_RANGES.nodeSizeMultiplier}
                    />
                    <SettingsSlider
                      label={SETTING_LABELS.linkWidth}
                      value={settings.linkWidth}
                      onChange={(v) => onUpdateSetting('linkWidth', v)}
                      range={SETTINGS_RANGES.linkWidth}
                    />
                    <SettingsSlider
                      label={SETTING_LABELS.constellationLinkWidth}
                      value={settings.constellationLinkWidth}
                      onChange={(v) => onUpdateSetting('constellationLinkWidth', v)}
                      range={SETTINGS_RANGES.constellationLinkWidth}
                    />
                  </div>
                </section>

                {/* Forces Section */}
                <section className="graph-control-section">
                  <h4 className="graph-control-section-header text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 pb-2 border-b border-slate-800/50">
                    Forces
                  </h4>
                  <div className="space-y-3">
                    <SettingsSlider
                      label={SETTING_LABELS.centerForce}
                      value={settings.centerForce}
                      onChange={(v) => onUpdateSetting('centerForce', v)}
                      range={SETTINGS_RANGES.centerForce}
                    />
                    <SettingsSlider
                      label={SETTING_LABELS.repelForce}
                      value={settings.repelForce}
                      onChange={(v) => onUpdateSetting('repelForce', v)}
                      range={SETTINGS_RANGES.repelForce}
                    />
                    <SettingsSlider
                      label={SETTING_LABELS.linkForce}
                      value={settings.linkForce}
                      onChange={(v) => onUpdateSetting('linkForce', v)}
                      range={SETTINGS_RANGES.linkForce}
                    />
                  </div>
                </section>
              </>
            ) : (
              <section className="graph-control-section">
                <h4 className="graph-control-section-header text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 pb-2 border-b border-slate-800/50">
                  Entity Colors
                </h4>
                <div className="space-y-3">
                  {Object.entries(settings.entityColors).map(([key, value]) => {
                    const inputId = `color-${key.toLowerCase()}`;
                    return (
                    <div key={key} className="graph-color-group flex items-center justify-between">
                      <label htmlFor={inputId} className="text-xs text-slate-400">{key}</label>
                      <input
                        type="color"
                        value={value}
                        id={inputId}
                        onChange={(e) =>
                          onUpdateSetting('entityColors', {
                            ...settings.entityColors,
                            [key]: e.target.value,
                          })
                        }
                        className="h-7 w-12 bg-transparent border border-slate-700 rounded cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
                        aria-label={`${key} color`}
                      />
                    </div>
                  );
                })}
                </div>
              </section>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

interface SettingsSliderProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  range: { min: number; max: number; step: number };
}

function SettingsSlider({ label, value, onChange, range }: SettingsSliderProps) {
  const [isChanging, setIsChanging] = useState(false);
  const sliderId = useId();

  const handleChange = (newValue: number) => {
    setIsChanging(true);
    onChange(newValue);

    // Reset flash after animation
    setTimeout(() => setIsChanging(false), 150);
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label htmlFor={sliderId} className="text-xs text-slate-400">{label}</label>
        <span
          className={`text-xs text-cyan-400 tabular-nums transition-transform transition-colors duration-150 ${
            isChanging ? 'text-cyan-300 scale-110' : ''
          }`}
        >
          {value.toFixed(1)}
        </span>
      </div>
      <input
        type="range"
        id={sliderId}
        min={range.min}
        max={range.max}
        step={range.step}
        value={value}
        onChange={(e) => handleChange(parseFloat(e.target.value))}
        style={{ pointerEvents: 'auto' }}
        className="block w-full h-2 bg-slate-800 rounded-full appearance-none cursor-pointer
          focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/60 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900
          [&::-webkit-slider-runnable-track]:h-2
          [&::-webkit-slider-runnable-track]:bg-slate-800
          [&::-webkit-slider-runnable-track]:rounded-full
          [&::-webkit-slider-thumb]:appearance-none
          [&::-webkit-slider-thumb]:w-4
          [&::-webkit-slider-thumb]:h-4
          [&::-webkit-slider-thumb]:rounded-full
          [&::-webkit-slider-thumb]:bg-gradient-to-br
          [&::-webkit-slider-thumb]:from-cyan-400
          [&::-webkit-slider-thumb]:to-cyan-500
          [&::-webkit-slider-thumb]:shadow-[0_0_12px_rgba(6,182,212,0.7),0_2px_4px_rgba(0,0,0,0.3)]
          [&::-webkit-slider-thumb]:cursor-pointer
          [&::-webkit-slider-thumb]:transition-all
          [&::-webkit-slider-thumb]:duration-200
          [&::-webkit-slider-thumb]:hover:scale-110
          [&::-webkit-slider-thumb]:hover:shadow-[0_0_18px_rgba(6,182,212,0.9),0_3px_6px_rgba(0,0,0,0.4)]
          [&::-webkit-slider-thumb]:active:scale-115
          [&::-webkit-slider-thumb]:active:shadow-[0_0_24px_rgba(6,182,212,1),0_4px_8px_rgba(0,0,0,0.5)]
          [&::-moz-range-track]:h-2
          [&::-moz-range-track]:bg-slate-800
          [&::-moz-range-track]:rounded-full
          [&::-moz-range-track]:border-0
          [&::-moz-range-thumb]:w-4
          [&::-moz-range-thumb]:h-4
          [&::-moz-range-thumb]:rounded-full
          [&::-moz-range-thumb]:bg-gradient-to-br
          [&::-moz-range-thumb]:from-cyan-400
          [&::-moz-range-thumb]:to-cyan-500
          [&::-moz-range-thumb]:border-0
          [&::-moz-range-thumb]:shadow-[0_0_12px_rgba(6,182,212,0.7),0_2px_4px_rgba(0,0,0,0.3)]
          [&::-moz-range-thumb]:cursor-pointer
          [&::-moz-range-thumb]:transition-all
          [&::-moz-range-thumb]:duration-200
          [&::-moz-range-thumb]:hover:scale-110
          [&::-moz-range-thumb]:hover:shadow-[0_0_18px_rgba(6,182,212,0.9),0_3px_6px_rgba(0,0,0,0.4)]
          [&::-moz-range-thumb]:active:scale-115
          [&::-moz-range-thumb]:active:shadow-[0_0_24px_rgba(6,182,212,1),0_4px_8px_rgba(0,0,0,0.5)]
        "
        aria-label={`${label} slider`}
        aria-valuemin={range.min}
        aria-valuemax={range.max}
        aria-valuenow={value}
      />
    </div>
  );
}
