# Evaluation Storage Architecture

## Overview

The evaluation system uses a unified storage architecture under `evaluation/data/` that provides persistent event storage, unified test formats, and consolidated storage locations.

## Directory Structure

```
evaluation/
├── agents/                       # Framework code
├── cli/                          # CLI interface
├── core/                         # Core logic
├── framework/                    # Framework components
│
└── data/                         # All evaluation data
    ├── config.py                 # Central configuration
    ├── test_loader.py            # Multi-agent test loader
    │
    ├── schemas/                  # Agent-specific test schemas
    │   ├── cmo_schema.json
    │   ├── specialist_schema.json
    │   └── visualization_schema.json
    │
    ├── traces/                   # Health query execution traces
    │   └── 2025-01-23/
    │       └── 143219_418f6e26.json  # HHMMSS_trace_id format
    │
    ├── test-suites/              # ALL test cases in JSON format
    │   ├── framework/            # Framework-provided tests
    │   │   ├── cmo/             # CMO agent tests
    │   │   ├── specialist/      # Specialist agent tests
    │   │   └── visualization/   # Visualization tests
    │   │
    │   └── studio-generated/     # User-created tests via Studio
    │       ├── cmo/
    │       ├── specialist/
    │       └── visualization/
    │
    └── runs/                     # Evaluation execution results
        └── 2025-01-23/
            └── eval_9e1197b2_trace_418f6e26/  # Includes trace ID suffix
                ├── metadata.json    # Evaluation metadata
                ├── events/         # Real-time progress events
                │   ├── 001_trace_load.json
                │   ├── 002_dimension_start.json
                │   └── ...
                ├── result.json     # Single evaluation result
                └── report/
                    └── index.html  # Generated HTML report
```

## Key Features

### 1. Unified Storage
- All evaluation data in one location: `evaluation/data/`
- Consistent naming patterns with timestamps and trace IDs
- No more scattered files across different directories

### 2. Persistent Event Storage
- Events stored as numbered JSON files in `events/` directory
- Survives server restarts
- Real-time progress tracking during ~30 second evaluations

### 3. Trace Management
- Traces stored with timestamp prefix: `HHMMSS_trace_id.json`
- Organized by date for easy management
- Unified location for all trace files

### 4. Test Case Organization
- All test cases in JSON format
- Organized by agent type (cmo, specialist, visualization)
- Separate directories for framework vs studio-generated tests

### 5. Configuration Support
- Central `EvaluationDataConfig` class
- Environment variable support for custom paths:
  ```bash
  EVAL_TRACES_DIR=/custom/traces
  EVAL_RUNS_DIR=/custom/runs
  ```

## Test Case Schemas

### CMO Test Schema
```json
{
  "id": "cmo_test_001",
  "agent_type": "cmo",
  "query": "Show me my blood pressure trends",
  "expected_complexity": "COMPLEX",
  "expected_specialties": ["cardiology", "pharmacy", "data_analysis"],
  "key_data_points": ["blood_pressure", "lisinopril", "trends"],
  "category": "cardiac",
  "notes": "Tests medication impact analysis",
  "trace_id": "418f6e26-3f5b-4a1d-b987-abc123def456",
  "created_at": "2025-01-23T10:30:00Z",
  "created_by": "studio"
}
```

### Specialist Test Schema
```json
{
  "id": "specialist_test_001",
  "agent_type": "specialist",
  "specialist_type": "cardiology",
  "task": {
    "objective": "Analyze blood pressure trends",
    "context": "Patient on lisinopril for 6 months",
    "expected_output": "Trend analysis with medication correlation",
    "priority": "high"
  },
  "expected_tools": ["execute_health_query_v2"],
  "trace_id": "def456",
  "created_at": "2025-01-23T10:35:00Z",
  "created_by": "framework"
}
```

## API Integration

### Backend Services
- `TraceCollector`: Saves traces to unified location
- `EvaluationService`: Uses file-based event storage
- `QEAnalystService`: Reads traces from unified location
- `ReportService`: Generates reports in evaluation run directories

### Frontend Components
- Event polling from `/api/evaluation/events/{evaluation_id}`
- Test case management via Eval Dev Studio
- Trace viewer integrated with unified storage

## Benefits

1. **No Data Loss**: Events persist across server restarts
2. **Unified Format**: Single JSON format for all test cases
3. **Clean Organization**: Clear directory structure by data type
4. **Easy Navigation**: Trace IDs included in evaluation folders
5. **Configurable**: Environment variables for custom paths
6. **Performance**: File-based storage scales well