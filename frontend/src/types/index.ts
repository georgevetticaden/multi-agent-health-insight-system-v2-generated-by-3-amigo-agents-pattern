// Chat types
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: Record<string, any>;
}

export interface ChatRequest {
  message: string;
  conversationId?: string;
  context?: Record<string, any>;
  enableExtendedThinking?: boolean;
}

export interface StreamChunk {
  type: 'text' | 'tool_call' | 'tool_result' | 'visualization' | 'thinking' | 'error' | 'done';
  content?: string;
  data?: any;
}

// Health data types
export interface ImportRequest {
  fileDirectory: string;
  patientName?: string;
}

export interface ImportResponse {
  success: boolean;
  message?: string;
  error?: string;
  patientId?: string;
  importId?: string;
  totalRecords?: number;
  statistics?: ImportStatistics;
}

export interface ImportStatistics {
  totalRecords: number;
  recordsByCategory: Record<string, number>;
  timelineCoverage: Record<string, number>;
  dataQuality: DataQualityMetrics;
  keyInsights: string[];
}

export interface DataQualityMetrics {
  labResultsWithRanges: QualityMetric;
  medicationsWithStatus: QualityMetric;
  recordsWithDates: QualityMetric;
}

export interface QualityMetric {
  count: number;
  total: number;
  percentage: number;
}

export interface QueryRequest {
  query: string;
  patientId?: string;
}

export interface QueryResponse {
  query: string;
  querySuccessful: boolean;
  interpretation?: string;
  sql?: string;
  results?: any[];
  resultCount?: number;
  dataMetrics?: Record<string, any>;
  error?: string;
  warnings: string[];
}

// Visualization types
export interface Visualization {
  type: 'line_chart' | 'bar_chart' | 'pie_chart' | 'table' | 'import_dashboard' | 'auto';
  data: any;
  title?: string;
  metrics?: Record<string, any>;
}

export interface HealthMetric {
  name: string;
  value: number | string;
  unit?: string;
  normalRange?: {
    min: number;
    max: number;
  };
  status?: 'normal' | 'warning' | 'danger';
  trend?: 'up' | 'down' | 'stable';
}