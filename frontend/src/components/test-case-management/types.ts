export interface TestCase {
  id: string;
  trace_id: string;
  query: string;
  expected_complexity: string;
  actual_complexity: string;
  expected_specialties: string[];
  actual_specialties: string[];
  key_data_points: string[];
  actual_key_data_points: string[];
  notes: string;
  created_at: string;
  updated_at: string;
  based_on_real_query: boolean;
  category: string;
  modified_fields: string[];
}

export interface DimensionResult {
  dimension_name: string;
  score: number;
  max_score: number;
  normalized_score: number;
  components: Record<string, number>;
  details: Record<string, any>;
  evaluation_method: string;
}

export interface EvaluationReport {
  test_case_id: string;
  evaluation_id: string;
  overall_score: number;
  dimension_results: Record<string, DimensionResult>;
  execution_time_ms: number;
  timestamp?: string;
  metadata?: Record<string, any>;
  report_url?: string;
  report_dir?: string;
}

export interface QEMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface TraceEvent {
  id: string;
  event_type: string;
  stage: string;
  agent: string;
  timestamp: string;
  data: Record<string, any>;
}