/**
 * NarrativePanel Component
 *
 * Displays contextual narratives for knowledge graph entities with:
 * - Inline citations (unicode markers)
 * - Highlighted events (CONFISCATED, SOLD, INHERITED)
 * - Evidence sidebar with expandable citations
 * - Loading states and error handling
 */

import React, { useState } from 'react';
import styles from './NarrativePanel.module.css';

// Types matching backend models
interface EvidenceCitation {
  citation_number: number;
  doc_id: string;
  quote: string;
  confidence: number;
  verification_tier: string;
}

interface EventHighlight {
  event_type: 'CONFISCATED' | 'SOLD' | 'INHERITED';
  date: string | null;
  summary: string;
  parties_involved: string[];
  location: string | null;
  document_ids: string[];
}

interface NarrativeResult {
  focal_entity_id: string;
  focal_entity_name: string;
  focal_entity_type: string;
  constellation_size: number;
  model_used: string;
  main_narrative: string;
  facts: EvidenceCitation[];
  total_documents: number;
  total_citations: number;
  generation_cost: number;
  from_cache: boolean;
  highlighted_events: EventHighlight[];
  session_total_cost?: number;
}

interface NarrativePanelProps {
  narrative: NarrativeResult | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
}

const NarrativePanel: React.FC<NarrativePanelProps> = ({
  narrative,
  loading,
  error,
  onClose
}) => {
  const [expandedCitations, setExpandedCitations] = useState<Set<number>>(new Set());

  const toggleCitation = (citationNum: number) => {
    setExpandedCitations(prev => {
      const next = new Set(prev);
      if (next.has(citationNum)) {
        next.delete(citationNum);
      } else {
        next.add(citationNum);
      }
      return next;
    });
  };

  // Get verification badge color
  const getVerificationColor = (tier: string): string => {
    switch (tier) {
      case 'TIER_1_CERTIFIED':
        return styles.tier1;
      case 'TIER_2_MANUAL':
        return styles.tier2;
      case 'TIER_3_AI':
        return styles.tier3;
      default:
        return styles.tier3;
    }
  };

  // Get event icon
  const getEventIcon = (eventType: string): string => {
    switch (eventType) {
      case 'CONFISCATED':
        return '🚨';
      case 'SOLD':
        return '💰';
      case 'INHERITED':
        return '📜';
      default:
        return '📋';
    }
  };

  // Parse narrative text into paragraphs
  const renderNarrative = (text: string) => {
    const paragraphs = text.split('\n\n').filter(p => p.trim());
    return paragraphs.map((paragraph, idx) => (
      <p key={idx} className={styles.narrativeParagraph}>
        {paragraph}
      </p>
    ));
  };

  if (loading) {
    return (
      <div className={styles.panel}>
        <div className={styles.loading}>
          <div className={styles.spinner}></div>
          <p>Generating narrative...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.panel}>
        <div className={styles.error}>
          <h3>Error Generating Narrative</h3>
          <p>{error}</p>
          <button onClick={onClose} className={styles.closeButton}>Close</button>
        </div>
      </div>
    );
  }

  if (!narrative) {
    return null;
  }

  return (
    <div className={styles.panel}>
      {/* Header */}
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>{narrative.focal_entity_name}</h2>
          <span className={styles.entityType}>{narrative.focal_entity_type}</span>
        </div>
        <button onClick={onClose} className={styles.closeButton} aria-label="Close">
          ✕
        </button>
      </div>

      {/* Metadata Badges */}
      <div className={styles.metadata}>
        <span className={styles.badge}>
          {narrative.constellation_size} entities
        </span>
        <span className={styles.badge}>
          {narrative.total_documents} documents
        </span>
        <span className={styles.badge}>
          {narrative.model_used}
        </span>
        {narrative.from_cache && (
          <span className={`${styles.badge} ${styles.cached}`}>
            cached
          </span>
        )}
      </div>

      {/* Highlighted Events */}
      {narrative.highlighted_events.length > 0 && (
        <div className={styles.eventsSection}>
          <h3 className={styles.sectionTitle}>Key Events</h3>
          <div className={styles.eventsList}>
            {narrative.highlighted_events.map((event, idx) => (
              <div
                key={idx}
                className={`${styles.eventHighlight} ${styles[event.event_type.toLowerCase()]}`}
              >
                <div className={styles.eventHeader}>
                  <span className={styles.eventIcon}>
                    {getEventIcon(event.event_type)}
                  </span>
                  <span className={styles.eventType}>{event.event_type}</span>
                  {event.date && (
                    <span className={styles.eventDate}>{event.date}</span>
                  )}
                </div>
                <p className={styles.eventSummary}>{event.summary}</p>
                {event.parties_involved.length > 0 && (
                  <div className={styles.eventParties}>
                    Parties: {event.parties_involved.join(', ')}
                  </div>
                )}
                {event.location && (
                  <div className={styles.eventLocation}>
                    Location: {event.location}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className={styles.content}>
        {/* Narrative Text */}
        <div className={styles.narrative}>
          <h3 className={styles.sectionTitle}>Narrative</h3>
          <div className={styles.narrativeText}>
            {renderNarrative(narrative.main_narrative)}
          </div>
        </div>

        {/* Evidence Sidebar */}
        {narrative.facts.length > 0 && (
          <div className={styles.sidebar}>
            <h3 className={styles.sectionTitle}>Evidence ({narrative.total_citations})</h3>
            <div className={styles.citationsList}>
              {narrative.facts.map((citation) => (
                <div key={citation.citation_number} className={styles.citation}>
                  <button
                    onClick={() => toggleCitation(citation.citation_number)}
                    className={styles.citationHeader}
                    aria-expanded={expandedCitations.has(citation.citation_number)}
                  >
                    <span className={styles.citationNumber}>
                      [{String.fromCharCode(9311 + citation.citation_number)}]
                    </span>
                    <span className={styles.citationDoc}>{citation.doc_id}</span>
                    <span className={`${styles.verificationBadge} ${getVerificationColor(citation.verification_tier)}`}>
                      {citation.verification_tier.replace('TIER_', 'T')}
                    </span>
                  </button>
                  {expandedCitations.has(citation.citation_number) && (
                    <div className={styles.citationContent}>
                      <blockquote className={styles.quote}>
                        "{citation.quote}"
                      </blockquote>
                      <div className={styles.confidence}>
                        Confidence: {(citation.confidence * 100).toFixed(0)}%
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className={styles.footer}>
        <div className={styles.disclaimer}>
          <strong>Forensic Intelligence Only:</strong> This narrative synthesizes
          documentary evidence and does not constitute legal advice or proof of ownership.
        </div>
        <div className={styles.costInfo}>
          Generation cost: ${narrative.generation_cost.toFixed(4)}
          {narrative.session_total_cost !== undefined && (
            <> | Session total: ${narrative.session_total_cost.toFixed(4)}</>
          )}
        </div>
      </div>
    </div>
  );
};

export default NarrativePanel;
