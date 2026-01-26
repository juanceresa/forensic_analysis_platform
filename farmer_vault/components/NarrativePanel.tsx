'use client';

import { useState, useEffect } from 'react';
import type { NarrativeResult } from '@/lib/types';

interface NarrativePanelProps {
  narrative: NarrativeResult | null;
  loading: boolean;
  error: string | null;
}

export function NarrativePanel({
  narrative,
  loading,
  error,
}: NarrativePanelProps) {
  const [expandedCitations, setExpandedCitations] = useState<Set<number>>(new Set());
  const [displayedText, setDisplayedText] = useState('');

  // FEATURE: Typewriter effect for narrative generation
  useEffect(() => {
    if (!narrative?.main_narrative) {
      setDisplayedText('');
      return;
    }

    let index = 0;
    const text = narrative.main_narrative;
    const interval = setInterval(() => {
      if (index < text.length) {
        setDisplayedText(text.slice(0, index + 1));
        index++;
      } else {
        clearInterval(interval);
      }
    }, 20); // Typewriter speed

    return () => clearInterval(interval);
  }, [narrative?.main_narrative]);

  const toggleCitation = (citationNum: number) => {
    setExpandedCitations((prev) => {
      const next = new Set(prev);
      if (next.has(citationNum)) {
        next.delete(citationNum);
      } else {
        next.add(citationNum);
      }
      return next;
    });
  };

  const getVerificationColor = (tier: string): string => {
    const colors: Record<string, string> = {
      TIER_1_CERTIFIED: 'text-tier-1',
      TIER_2_INSTITUTIONAL: 'text-tier-2-inst',
      TIER_2_ANALYST: 'text-tier-2',
      TIER_3_AI: 'text-tier-3',
    };
    return colors[tier] || 'text-tier-3';
  };

  const getEventIcon = (eventType: string): string => {
    const icons: Record<string, string> = {
      CONFISCATED: '🚨',
      SOLD: '💰',
      INHERITED: '📜',
    };
    return icons[eventType] || '📋';
  };

  const renderNarrative = (text: string) => {
    const paragraphs = text.split('\n\n').filter((p) => p.trim());
    return paragraphs.map((paragraph, idx) => (
      <p key={idx} className="mb-4 text-slate-200 leading-relaxed font-body">
        {paragraph}
      </p>
    ));
  };

  // ACCESSIBILITY: Loading state with aria-live
  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div
          className="text-center"
          role="status"
          aria-live="polite"
          aria-label="Generating narrative"
        >
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4" />
          <p className="text-slate-400 font-mono text-sm">
            Analyzing evidence constellation...
          </p>
        </div>
      </div>
    );
  }

  // ACCESSIBILITY: Error state with role="alert"
  if (error) {
    return (
      <div className="p-6">
        <div
          className="bg-red-950/50 border border-red-500 rounded p-4"
          role="alert"
          aria-live="assertive"
        >
          <h3 className="text-red-400 font-display text-sm uppercase tracking-wider mb-2">
            Generation Failed
          </h3>
          <p className="text-slate-300 font-mono text-xs">{error}</p>
        </div>
      </div>
    );
  }

  if (!narrative) {
    return (
      <div className="p-6 text-center text-slate-500 font-mono text-sm">
        <div className="mb-2 text-slate-600">◇</div>
        Click "Generate Intelligence Briefing" to begin
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4 overflow-y-auto">
      {/* Header */}
      <div className="border-b border-cyan-500/20 pb-3">
        <h2 className="text-xl font-display uppercase tracking-wide text-cyan-100">
          {narrative.focal_entity_name}
        </h2>
        <p className="text-xs text-slate-400 font-mono uppercase tracking-wider mt-1">
          {narrative.focal_entity_type} • Intelligence Briefing
        </p>
      </div>

      {/* Metadata Tags - Holographic Data Chips */}
      <div className="flex gap-2 flex-wrap text-xs font-mono">
        <span className="px-3 py-1.5 bg-gradient-to-br from-cyan-950/50 to-slate-900 border border-cyan-500/30 rounded shadow-[0_0_8px_rgba(6,182,212,0.15)] text-cyan-200 backdrop-blur-sm">
          <span className="text-cyan-400 font-bold">{narrative.constellation_size}</span> entities
        </span>
        <span className="px-3 py-1.5 bg-gradient-to-br from-blue-950/50 to-slate-900 border border-blue-500/30 rounded shadow-[0_0_8px_rgba(59,130,246,0.15)] text-blue-200 backdrop-blur-sm">
          <span className="text-blue-400 font-bold">{narrative.total_documents}</span> documents
        </span>
        <span className="px-3 py-1.5 bg-gradient-to-br from-purple-950/50 to-slate-900 border border-purple-500/30 rounded shadow-[0_0_8px_rgba(139,92,246,0.15)] text-purple-200 backdrop-blur-sm">
          {narrative.model_used}
        </span>
        {narrative.from_cache && (
          <span className="px-3 py-1.5 bg-gradient-to-br from-emerald-950/50 to-slate-900 border border-emerald-500/40 rounded shadow-[0_0_10px_rgba(16,185,129,0.2)] text-emerald-300 backdrop-blur-sm animate-pulse">
            ✓ cached
          </span>
        )}
      </div>

      {/* Highlighted Events */}
      {narrative.highlighted_events.length > 0 && (
        <section>
          <h3 className="text-xs font-display uppercase tracking-wider text-slate-300 mb-2">
            Critical Events
          </h3>
          <div className="space-y-2">
            {narrative.highlighted_events.map((event, idx) => (
              <div
                key={idx}
                className="bg-slate-800 border border-cyan-600/50 rounded p-3 border-l-4"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span>{getEventIcon(event.event_type)}</span>
                  <span className="font-display text-xs uppercase tracking-wider text-cyan-400">
                    {event.event_type}
                  </span>
                  {event.date && (
                    <span className="text-xs text-slate-400 font-mono">{event.date}</span>
                  )}
                </div>
                <p className="text-sm text-slate-300 font-body">{event.summary}</p>
                {event.parties_involved.length > 0 && (
                  <p className="text-xs text-slate-400 mt-1 font-mono">
                    Parties: {event.parties_involved.join(', ')}
                  </p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Main Narrative with Typewriter Effect */}
      <section>
        <h3 className="text-xs font-display uppercase tracking-wider text-slate-300 mb-2">
          Intelligence Summary
        </h3>
        <div className="text-sm font-body">{renderNarrative(displayedText)}</div>
      </section>

      {/* Evidence Citations */}
      {narrative.facts.length > 0 && (
        <section>
          <h3 className="text-xs font-display uppercase tracking-wider text-slate-300 mb-2">
            Supporting Evidence ({narrative.total_citations})
          </h3>
          <div className="space-y-2">
            {narrative.facts.map((fact) => (
              <div key={fact.citation_number} className="bg-slate-800 border border-slate-700 rounded">
                <button
                  onClick={() => toggleCitation(fact.citation_number)}
                  className="w-full min-h-[44px] px-3 py-2 flex items-center justify-between hover:bg-slate-700 rounded transition-colors"
                  aria-expanded={expandedCitations.has(fact.citation_number)}
                  aria-label={`Toggle citation ${fact.citation_number}: ${fact.claim_text}`}
                >
                  <span className="font-mono text-sm text-left">
                    [{String.fromCharCode(9311 + fact.citation_number)}] {fact.claim_text}
                  </span>
                  <span className="text-xs text-slate-400 font-display uppercase ml-2">
                    {fact.fact_type || 'FACT'}
                  </span>
                </button>
                {expandedCitations.has(fact.citation_number) && (
                  <div className="px-3 pb-3 space-y-2">
                    {fact.evidence.map((citation, idx) => (
                      <div key={idx} className="border-l-2 border-cyan-600 pl-3">
                        <p className="text-xs text-slate-400 mb-1 font-mono">
                          {citation.doc_id}{citation.page ? ` • p.${citation.page}` : ''}
                        </p>
                        <blockquote className="italic text-sm text-slate-300 font-body">
                          "{citation.quote}"
                        </blockquote>
                        <p className="text-xs text-slate-400 mt-1 font-mono">
                          Confidence: {(citation.confidence * 100).toFixed(0)}% •{' '}
                          <span className={getVerificationColor(citation.verification_tier)}>
                            {citation.verification_tier.replace('TIER_', 'T')}
                          </span>
                        </p>
                      </div>
                    ))}
                    {fact.temporal_context && (
                      <p className="text-xs text-slate-500 font-mono">
                        Temporal context: {fact.temporal_context}
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Footer Disclaimer */}
      <div className="border-t border-cyan-500/20 pt-4 space-y-2">
        <p className="text-xs text-cyan-400 font-mono leading-relaxed">
          <strong className="text-cyan-500">⚠️ FORENSIC INTELLIGENCE ONLY:</strong>{' '}
          This analysis synthesizes documentary evidence and does not constitute legal
          advice or proof of ownership.
        </p>
        <p className="text-xs text-slate-500 font-mono">
          Generation cost: ${narrative.generation_cost.toFixed(4)}
          {narrative.session_total_cost !== undefined && (
            <> | Session total: ${narrative.session_total_cost.toFixed(4)}</>
          )}
        </p>
      </div>
    </div>
  );
}
