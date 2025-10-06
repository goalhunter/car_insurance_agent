// Customer types
export interface Customer {
  customer_id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  age?: number;
  driving_experience_years?: number;
  previous_claims_count?: number;
}

// Policy types
export interface Policy {
  policy_id: string;
  policy_number: string;
  policy_type: string;
  policy_status: string;
  coverage_amount: number;
  deductible_amount: number;
  premium_amount: number;
  customer_id: string;
  policy_start_date: string;
  policy_end_date: string;
}

// Vehicle types
export interface Vehicle {
  vehicle_id: string;
  make: string;
  model: string;
  year_of_manufacture: number;
  color: string;
  registration_number: string;
  vin: string;
}

// Damage Analysis types
export interface DamageAnalysis {
  vehicle_match: boolean;
  analysis: {
    vehicle_matches_policy: boolean;
    damaged_parts: string[];
    damage_summary: string;
    estimated_repair_cost_usd: number;
    likely_crash_reason: string;
    severity: 'minor' | 'moderate' | 'severe';
    suspicious_indicators?: string[];
  };
}

// Document Analysis types
export interface DocumentAnalysis {
  incident_date: string;
  incident_location: string;
  police_case_number: string;
  fault_determination: string;
  estimated_repair_cost: number;
  repair_items: string[];
  inconsistencies?: string[];
  red_flags?: string[];
}

// Settlement Decision types
export interface SettlementDecision {
  claim_id: string;
  recommendation: 'APPROVE' | 'MANUAL_REVIEW' | 'DENY';
  approved_amount: number;
  deductible_applies: boolean;
  customer_pays: number;
  insurance_pays: number;
  genuine_factors: string[];
  suspicious_factors: string[];
  risk_assessment: 'low' | 'medium' | 'high';
  detailed_reasoning: string;
  supporting_evidence: string[];
  next_steps: string[];
  pdf_url?: string;
  pdf_s3_key?: string;
}

// Claim steps
export const ClaimStep = {
  CUSTOMER_VERIFICATION: 1,
  POLICY_VERIFICATION: 2,
  DAMAGE_ANALYSIS: 3,
  DOCUMENT_ANALYSIS: 4,
  SETTLEMENT_DECISION: 5,
} as const;

export type ClaimStep = typeof ClaimStep[keyof typeof ClaimStep];

// Claim state
export interface ClaimState {
  currentStep: ClaimStep;
  customer?: Customer;
  policy?: Policy;
  vehicle?: Vehicle;
  damageImages?: string[]; // S3 URIs
  damageAnalysis?: DamageAnalysis;
  policeReport?: string; // S3 URI
  repairEstimate?: string; // S3 URI
  documentAnalysis?: DocumentAnalysis;
  settlement?: SettlementDecision;
}

// Chat message types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: {
    step?: ClaimStep;
    action?: string;
  };
}

// API Response types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}
