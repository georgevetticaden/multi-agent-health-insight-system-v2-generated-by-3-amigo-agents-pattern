# Evaluation Data Architecture

## Overview

The `evaluation/data/` directory contains all evaluation-related data artifacts, providing a unified storage system for traces, test cases, and evaluation results. This architecture supports multiple agent types with agent-specific test schemas while maintaining a consistent storage structure.

## Directory Structure

```
evaluation/data/
├── config.py                 # Central configuration module
├── test_loader.py           # Multi-agent test case loader
├── migrate_tests.py         # One-time migration script
│
├── schemas/                 # Agent-specific test schemas
│   ├── cmo_schema.json     # CMO agent test schema
│   ├── specialist_schema.json  # Specialist test schema
│   └── visualization_schema.json # Visualization test schema
│
├── traces/                  # Health query execution traces
│   └── [date]/
│       └── trace_[id].json
│
├── test-suites/            # Test case definitions
│   ├── framework/          # Framework-provided tests
│   │   ├── cmo/           # CMO agent tests
│   │   │   ├── basic_tests.json
│   │   │   ├── complex_tests.json
│   │   │   └── edge_cases.json
│   │   ├── specialist/    # Specialist agent tests
│   │   │   ├── cardiology_tests.json
│   │   │   └── endocrinology_tests.json
│   │   └── visualization/ # Visualization tests
│   │       └── chart_tests.json
│   │
│   └── studio-generated/   # User-created tests
│       ├── cmo/           # CMO tests by date
│       │   └── [date]/
│       │       └── test_[id].json
│       ├── specialist/    # Specialist tests by date
│       │   └── [date]/
│       │       └── test_[id].json
│       └── visualization/ # Visualization tests by date
│           └── [date]/
│               └── test_[id].json
│
└── runs/                   # Evaluation execution results
    └── [date]/
        └── eval_[id]/
            ├── metadata.json      # Run metadata (includes agent_type)
            ├── events/           # Lifecycle events
            │   ├── 001_trace_load.json
            │   ├── 002_dimension_start.json
            │   └── ...
            ├── result.json       # Evaluation result
            └── report/
                └── index.html    # HTML report
```

## Key Components

### 1. Configuration (`config.py`)

Central configuration for all storage operations:

```python
from evaluation.data.config import EvaluationDataConfig

# Get paths
trace_path = EvaluationDataConfig.get_trace_path(trace_id)
run_dir = EvaluationDataConfig.get_run_dir(evaluation_id)
test_path = EvaluationDataConfig.get_test_case_path(test_id)

# Initialize directories
EvaluationDataConfig.init_directories()
```

### 2. Test Loader (`test_loader.py`)

Unified loader for all test cases:

```python
from evaluation.data.test_loader import TestLoader

# Load all tests (framework + studio)
all_tests = TestLoader.load_all_tests()

# Load specific test
test = TestLoader.load_test_by_id("test_001")
```

### 3. Test Case Schemas

Each agent type has its own test case schema:

#### CMO Test Schema
```json
{
  "id": "cmo_test_001",
  "agent_type": "cmo",
  "query": "Show me my blood pressure trends",
  "expected_complexity": "STANDARD",
  "expected_specialties": ["CARDIOLOGY", "DATA_ANALYSIS"],
  "key_data_points": ["blood_pressure", "trends"],
  "category": "cardiac",
  "notes": "Tests basic cardiac data analysis",
  "trace_id": "abc123",
  "created_at": "2025-01-23T10:30:00Z",
  "created_by": "studio"
}
```

#### Specialist Test Schema
```json
{
  "id": "specialist_test_001",
  "agent_type": "specialist",
  "specialist_type": "CARDIOLOGY",
  "task": {
    "objective": "Analyze blood pressure trends",
    "context": "Patient history context",
    "expected_output": "Trend analysis",
    "priority": "high",
    "max_tool_calls": 5
  },
  "expected_tools": ["execute_health_query_v2"],
  "expected_data_points": ["systolic_bp", "diastolic_bp"],
  "validation_criteria": {},
  "created_at": "2025-01-23T10:30:00Z",
  "created_by": "framework"
}
```

#### Visualization Test Schema
```json
{
  "id": "viz_test_001",
  "agent_type": "visualization",
  "query": "Create blood pressure chart",
  "input_data": {
    "type": "time_series",
    "metrics": ["systolic_bp", "diastolic_bp"]
  },
  "expected_chart_type": "LineChart",
  "expected_features": ["dual_y_axis", "trend_line"],
  "created_at": "2025-01-23T10:30:00Z",
  "created_by": "studio"
}
```

## Data Flow

### Creating a Test Case
1. Health Query → Creates trace in `traces/`
2. QE Agent → Generates test case
3. Save → Stores in `test-suites/studio-generated/`

### Running an Evaluation
1. Load test case from `test-suites/`
2. Create run directory in `runs/[date]/eval_[id]/`
3. Stream events to `events/` directory
4. Save final result to `result.json`
5. Generate report in `report/index.html`

### Event Storage
Events are stored as numbered JSON files for chronological ordering:
- `001_trace_load.json`
- `002_dimension_start.json`
- `003_complexity_eval.json`
- etc.

## Environment Variables

Configure storage locations via environment:

```bash
# Redirect traces to temp storage
EVAL_TRACES_DIR=/tmp/evaluation/traces

# Redirect runs to larger disk
EVAL_RUNS_DIR=/mnt/storage/evaluation/runs
```

## Usage Examples

### Backend Service
```python
# Save a trace
trace_path = EvaluationDataConfig.get_trace_path(trace_id)
trace_path.write_text(json.dumps(trace_data))

# Save a test case with agent type
test_path = EvaluationDataConfig.get_test_case_path(
    test_id="test_001",
    agent_type="cmo"
)
test_path.parent.mkdir(parents=True, exist_ok=True)
test_path.write_text(json.dumps(test_data))

# Start evaluation
run_dir = EvaluationDataConfig.get_run_dir(evaluation_id)
metadata = {
    "evaluation_id": evaluation_id,
    "agent_type": "cmo",  # Important!
    "test_case_id": "test_001"
}
(run_dir / "metadata.json").write_text(json.dumps(metadata))

# Store event
event_file = run_dir / "events" / f"{num:03d}_{event_type}.json"
event_file.write_text(json.dumps(event_data))
```

### CLI Framework
```python
# Load all tests
from evaluation.data.test_loader import TestLoader
all_tests = TestLoader.load_all_tests()

# Load only CMO tests
cmo_tests = TestLoader.load_all_tests(agent_type="cmo")

# Load specialist tests
specialist_tests = TestLoader.load_all_tests(agent_type="specialist")

# Run evaluations by type
for test in cmo_tests:
    cmo_evaluator.evaluate(test)

for test in specialist_tests:
    specialist_evaluator.evaluate(test)
```

### Schema Validation
```python
# Validate a test case
test_case = {
    "id": "test_001",
    "agent_type": "cmo",
    "query": "Show me my labs",
    # ... other fields
}

if EvaluationDataConfig.validate_test_case(test_case):
    print("Valid test case")
else:
    print("Invalid test case")
```

## Migration from Old Structure

Run the migration script to convert Python test cases to JSON:

```bash
python evaluation/data/migrate_tests.py
```

This will:
1. Load existing Python test cases
2. Convert to JSON format
3. Save in `test-suites/framework/`
4. Preserve all test metadata

## Benefits

1. **Unified Storage**: All evaluation data in one place
2. **Persistent Events**: Survive server reloads
3. **Single Test Format**: JSON for all test cases
4. **No Duplication**: One result file per evaluation
5. **Configurable**: Redirect storage as needed
6. **Clean Separation**: Framework code vs data

## Maintenance

### Cleanup Old Data
```bash
# Remove traces older than 90 days
find evaluation/data/traces -mtime +90 -delete

# Archive old runs
tar -czf runs_2024.tar.gz evaluation/data/runs/2024-*
rm -rf evaluation/data/runs/2024-*
```

### Backup
```bash
# Backup test suites (small, important)
cp -r evaluation/data/test-suites /backup/

# Backup recent runs
rsync -av evaluation/data/runs/ /backup/runs/
```