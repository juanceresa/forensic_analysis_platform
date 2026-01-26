// Verification System
export type VerificationTier =
  | 'TIER_3_AI'
  | 'TIER_2_ANALYST'
  | 'TIER_2_INSTITUTIONAL'
  | 'TIER_1_CERTIFIED';

export interface Verification {
  tier: VerificationTier;
  confidence: number;
  verified_by?: string | null;
  verified_at?: string | null;
  notes?: string | null;
}

// Entity Types
export type EntityType =
  | 'PERSON'
  | 'PROPERTY'
  | 'ORGANIZATION'
  | 'LOCATION'
  | 'DOCUMENT';

// Base Node (all entity types extend this)
export interface BaseNode {
  id: string;
  entity_type: EntityType;
  name?: string;
  verification: Verification;
  extracted_from: string;  // Comma-delimited doc IDs
  created_at?: string;
  updated_at?: string;
  notes?: string | null;
  // Allow additional entity-specific fields
  [key: string]: unknown;
}

// Link (relation between entities)
export interface Link {
  relation_id?: string;
  source: string;
  target: string;
  relation_type: string;
  verification: Verification;
  date?: string | null;
  amount?: number | null;
  currency?: string | null;
  property_id?: string | null;
  document_id?: string | null;
  evidence?: string | null;
  notes?: string | null;
}

// Graph Metadata
export interface GraphMetadata {
  case_id: string;
  created_at: string;
  updated_at: string;
  factory_version: string;
  entity_count: number;
  relation_count: number;
  document_count: number;
  verification_distribution?: Record<string, number>;
  entity_type_summary?: Record<string, number>;
  date_range?: {
    earliest_document?: string | null;
    latest_document?: string | null;
    earliest_event?: string | null;
    latest_event?: string | null;
  };
}

// Complete Graph Structure
export interface GraphData {
  metadata: GraphMetadata;
  nodes: BaseNode[];
  links: Link[];
}

// Narrative Types
export interface EvidenceCitation {
  doc_id: string;
  page?: number | null;
  quote: string;
  confidence: number;
  verification_tier: string;
  ocr_confidence?: number | null;
}

export interface FactualClaim {
  claim_text: string;
  citation_number: number;
  evidence: EvidenceCitation[];
  temporal_context?: string | null;
  fact_type?: string | null;
}

export interface EventHighlight {
  event_type: 'CONFISCATED' | 'SOLD' | 'INHERITED';
  summary: string;
  date: string | null;
  citation_number: number;
  evidence: EvidenceCitation[];
  parties_involved: string[];
}

export interface NarrativeResult {
  focal_entity_id: string;
  focal_entity_name: string;
  focal_entity_type: string;
  constellation_size: number;
  model_used: string;
  main_narrative: string;
  facts: FactualClaim[];
  highlighted_events: EventHighlight[];
  total_documents: number;
  total_citations: number;
  date_range?: string | null;
  generation_cost: number;
  from_cache: boolean;
  is_simple_entity?: boolean;
  quality_warning?: string | null;
  session_total_cost?: number;
}

export interface NarrativeError {
  type: 'validation' | 'cost_limit' | 'insufficient_data' | 'network' | 'unknown';
  message: string;
}
