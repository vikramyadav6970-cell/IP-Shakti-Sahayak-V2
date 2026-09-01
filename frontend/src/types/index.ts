/**
 * Shared TypeScript types for IP-SAKTI Sahayak frontend.
 * Mirrors backend Pydantic and SQLAlchemy models.
 */

export type JurisdictionCode =
  | "INDIA"
  | "INTERNATIONAL"
  | "USA"
  | "EU"
  | "UK"
  | "JAPAN"
  | "AUSTRALIA"
  | "WIPO";

export type Role =
  | "USER"
  | "ADMIN"
  | "IP_FACILITATOR"
  | "CONTENT_MANAGER"
  | "RESEARCHER";

export type ConfidenceLabel = "LOW" | "MEDIUM" | "HIGH";

export type ProductCategory =
  | "CLASSICAL_MEDICINE"
  | "PROPRIETARY_MEDICINE"
  | "NEW_DRUG"
  | "PHYTOPHARMACEUTICAL"
  | "AYURVEDA_AAHARA"
  | "COSMETIC"
  | "UNCLEAR";

export type ClassificationState =
  | "PENDING"
  | "COLLECTING_PRODUCT_INFORMATION"
  | "READY_FOR_CLASSIFICATION"
  | "CLASSIFIED";

export type DeclaredIntent =
  | "PATENT"
  | "RESEARCH"
  | "SELL_BUSINESS"
  | "AYUSH_APPLICATION"
  | "EXPORT"
  | "OTHER";

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  organization?: string;
  language: string;
  is_active?: boolean;
  created_at?: string;
}

export interface Citation {
  id?: string;
  message_id?: string;
  document_title: string;
  section_ref: string;
  source_url: string;
  jurisdiction: string;
  document_type?: string;
  verification_status?: string;
  chunk_id?: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  jurisdiction?: string;
  confidence_score?: number;
  confidence_label?: ConfidenceLabel;
  requires_human_review?: boolean;
  classification?: string;
  citations?: Citation[];
  detected_language?: string;
  is_translated?: boolean;
  created_at?: string;
}

export interface Feedback {
  id?: string;
  message_id: string;
  user_id?: string;
  rating: number;
  comment?: string;
  created_at?: string;
}

export interface ProductContextData {
  product_name?: string;
  description?: string;
  formulation?: string;
  ingredients?: string[];
  dosage_form?: string;
  intended_use?: string;
  therapeutic_claims?: string;
  classical_source?: string;
  other_relevant_info?: string;
  state: ClassificationState;
  category?: string;
  category_name?: string;
  classification_reason?: string;
  regulatory_pathway?: string;
  statutory_authority?: string;
  patent_eligibility?: "EXCLUDED" | "CONDITIONAL" | "HIGH";
  patent_reasoning?: string;
  abs_requirement?: string;
}

export interface ProductClassificationMeta {
  category: ProductCategory;
  category_name: string;
  product_name?: string;
  regulatory_pathway: string;
  statutory_authority: string;
  reasoning: string;
  patent_eligibility: "EXCLUDED" | "CONDITIONAL" | "HIGH";
  patent_reasoning: string;
  abs_requirement: string;
  confidence?: number;
}

export interface ClassificationResult {
  category: ProductCategory;
  category_name?: string;
  regulatory_pathway: string;
  reasoning?: string;
  rules_fired: string[];
  suggested_category?: ProductCategory;
  user_selected_category?: ProductCategory;
  is_reconciled?: boolean;
}

export interface ABSAssessmentResult {
  relevance: "HIGH" | "MEDIUM" | "LOW" | "NOT_APPLICABLE";
  authority: string;
  approval_required: boolean;
  benefit_sharing_applicable: boolean;
  next_steps: string[];
  legal_provisions: string[];
}

export interface ConversationSummary {
  id: string;
  title?: string;
  active_classification_id?: string;
  active_intent?: string;
  product_name?: string;
  category?: string;
  category_name?: string;
  dosage_form?: string;
  ingredients?: string[];
  patent_eligibility?: string;
  regulatory_pathway?: string;
  classification_state?: string;
  message_count?: number;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail {
  id: string;
  user_id: string;
  title?: string;
  active_classification_id?: string;
  active_intent?: string;
  product_context?: ProductContextData;
  product_classification?: ProductClassificationMeta;
  classification_state?: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}
