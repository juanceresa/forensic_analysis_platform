import { BaseNode, Verification } from './types';

export interface Document {
  id: string; // Document filename without extension + page
  filename: string; // Original filename with extension
  date: string | null; // Extracted date (ISO format)
  type?: string | null; // Contract, Will, Transfer, etc.
  entityCount: number;
  confidence: number; // OCR confidence
  imagePath: string; // Path to original image
  entityIds: string[]; // IDs of entities extracted from this document
}

export interface DocumentPage {
  ocrText: string;
  rawOcrText?: string;
  translatedText?: string | null;
  imagePath: string;
  entities: BaseNode[];
}

export interface DocumentAnalysis {
  document_type: string;
  executive_summary: string;
  claim_relevance: {
    level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
    reasoning: string;
  };
  key_facts: string[];
  cross_references: string[];
  quality_notes: {
    ocr_quality: 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR';
    missing_information: string[];
    verification_needed: string[];
  };
  source_docs: string[];
  _metadata: {
    generated_at: string;
    model: string;
    prompt_version: string;
  };
}

export interface DocumentDetail extends Document {
  ocrText: string;
  rawOcrText?: string;
  translatedText?: string | null;
  detectedLanguage?: string;
  entities: BaseNode[];
  pages?: DocumentPage[];
  analysis?: DocumentAnalysis | null;
}

export interface ExtractionData {
  entities: BaseNode[];
  relations: any[];
  ocr_result: {
    text: string;
    confidence: number;
    page_confidence: number;
    blocks: any[];
    metadata: {
      language: string;
      api_version: string;
      image_dimensions: {
        height: number;
        width: number;
      };
    };
  };
  confidence_scores: {
    ocr_confidence: number;
    llm_confidence: number;
    combined_confidence: number;
  };
  path: string;
  processing_metadata?: any;
}
