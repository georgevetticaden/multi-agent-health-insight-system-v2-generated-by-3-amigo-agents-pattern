# Evaluation Storage Architecture Refactor Plan

## Executive Summary

This document describes a complete refactoring of the evaluation data storage system to fix event persistence, unify test formats, and consolidate storage locations. No backward compatibility is required - this is a clean break refactor.

## Current Problems

1. **Event Loss**: Evaluation lifecycle events stored in-memory, lost on server reload
2. **Data Fragmentation**:
   - Traces: `backend/traces/`
   - Results: `backend/evaluation_results/` (with 3 duplicate JSON files per evaluation)
   - Test cases: Various locations
3. **Format Divergence**: CLI uses Python test cases, Studio generates JSON
4. **Result Duplication**: Same data in multiple files
5. **Path Confusion**: Hardcoded paths throughout codebase
6. **No Configuration**: Cannot redirect storage locations

## Target Architecture

```
evaluation/
├── agents/                       # Framework code (unchanged)
├── cli/                          # CLI interface (unchanged)
├── core/                         # Core logic (unchanged)
├── framework/                    # Framework components (unchanged)
│
└── data/                         # NEW: All evaluation data
    ├── config.py                 # Central configuration
    ├── test_loader.py            # Multi-agent test loader
    ├── migrate_tests.py          # Migration script
    │
    ├── schemas/                  # Agent-specific test schemas
    │   ├── cmo_schema.json      # CMO test schema
    │   ├── specialist_schema.json # Specialist test schema
    │   └── visualization_schema.json # Visualization test schema
    │
    ├── traces/                   # Health query execution traces
    │   └── 2025-01-23/
    │       └── trace_abc123.json
    │
    ├── test-suites/              # ALL test cases in JSON format
    │   ├── framework/            # Framework-provided tests
    │   │   ├── cmo/             # CMO agent tests
    │   │   │   ├── basic_tests.json
    │   │   │   ├── complex_tests.json
    │   │   │   └── edge_cases.json
    │   │   ├── specialist/      # Specialist agent tests
    │   │   │   ├── cardiology_tests.json
    │   │   │   └── endocrinology_tests.json
    │   │   └── visualization/   # Visualization tests
    │   │       └── chart_tests.json
    │   │
    │   └── studio-generated/     # User-created tests via Studio
    │       ├── cmo/             # Organized by agent type
    │       │   └── 2025-01-23/
    │       │       └── test_001.json
    │       ├── specialist/
    │       │   └── 2025-01-23/
    │       │       └── test_002.json
    │       └── visualization/
    │           └── 2025-01-23/
    │               └── test_003.json
    │
    └── runs/                     # Evaluation execution results
        └── 2025-01-23/
            └── eval_9e1197b2/
                ├── metadata.json    # Includes agent_type
                ├── events/         # Real-time progress events
                │   ├── 001_trace_load.json
                │   ├── 002_dimension_start.json
                │   ├── 003_complexity_eval.json
                │   └── ...
                ├── result.json     # Single evaluation result
                └── report/
                    └── index.html  # Generated HTML report
```

## Multi-Agent Test Case Schemas

Each agent type has its own test case schema:

### CMO Test Schema
```json
{
  "id": "cmo_test_001",
  "agent_type": "cmo",
  "query": "Show me my blood pressure trends since starting lisinopril",
  "expected_complexity": "COMPLEX",
  "expected_specialties": ["CARDIOLOGY", "PHARMACY", "DATA_ANALYSIS"],
  "key_data_points": ["blood_pressure", "lisinopril", "trends"],
  "category": "cardiac",
  "notes": "Tests medication impact analysis",
  "trace_id": "abc123",
  "created_at": "2025-01-23T10:30:00Z",
  "created_by": "studio"
}
```

### Specialist Test Schema
```json
{
  "id": "specialist_test_001",
  "agent_type": "specialist",
  "specialist_type": "CARDIOLOGY",
  "task": {
    "objective": "Analyze blood pressure trends",
    "context": "Patient on lisinopril for 6 months",
    "expected_output": "Trend analysis with medication correlation",
    "priority": "high",
    "max_tool_calls": 5
  },
  "expected_tools": ["execute_health_query_v2", "analyze_trends"],
  "expected_data_points": ["systolic_bp", "diastolic_bp", "medication_dates"],
  "validation_criteria": {
    "must_identify_trend": true,
    "must_correlate_medication": true
  },
  "trace_id": "def456",
  "created_at": "2025-01-23T10:35:00Z",
  "created_by": "framework"
}
```

### Visualization Test Schema
```json
{
  "id": "viz_test_001",
  "agent_type": "visualization",
  "query": "Create a chart showing blood pressure trends",
  "input_data": {
    "type": "time_series",
    "metrics": ["systolic_bp", "diastolic_bp"],
    "time_range": "6_months"
  },
  "expected_chart_type": "LineChart",
  "expected_features": ["dual_y_axis", "trend_line", "annotations"],
  "expected_libraries": ["recharts"],
  "created_at": "2025-01-23T10:40:00Z",
  "created_by": "studio"
}
```

## Implementation Phases

### Phase 1: Foundation Setup (2 hours)

#### 1.1 Create Directory Structure
```bash
mkdir -p evaluation/data/{traces,test-suites/{framework/{cmo,specialist},studio-generated},runs}
touch evaluation/data/__init__.py
```

#### 1.2 Create Configuration Module
File: `evaluation/data/config.py`

```python
from pathlib import Path
from datetime import datetime
import os
import json

class EvaluationDataConfig:
    """Central configuration for all evaluation data storage"""
    
    # Base paths
    BASE_DIR = Path(__file__).parent
    TRACES_DIR = Path(os.getenv("EVAL_TRACES_DIR", str(BASE_DIR / "traces")))
    RUNS_DIR = Path(os.getenv("EVAL_RUNS_DIR", str(BASE_DIR / "runs")))
    TEST_SUITES_DIR = BASE_DIR / "test-suites"  # Always relative to framework
    
    # Test case schema for validation
    TEST_CASE_SCHEMA = {
        "type": "object",
        "required": ["id", "query", "expected_complexity", "expected_specialties"],
        "properties": {
            "id": {"type": "string"},
            "query": {"type": "string"},
            "expected_complexity": {"enum": ["SIMPLE", "STANDARD", "COMPLEX", "CRITICAL"]},
            "expected_specialties": {"type": "array", "items": {"type": "string"}},
            "key_data_points": {"type": "array", "items": {"type": "string"}},
            "category": {"type": "string"},
            "notes": {"type": "string"},
            "trace_id": {"type": "string"},
            "created_at": {"type": "string"},
            "created_by": {"enum": ["framework", "studio"]}
        }
    }
    
    @classmethod
    def init_directories(cls):
        """Initialize all required directories"""
        cls.TRACES_DIR.mkdir(parents=True, exist_ok=True)
        cls.RUNS_DIR.mkdir(parents=True, exist_ok=True)
        cls.TEST_SUITES_DIR.mkdir(parents=True, exist_ok=True)
        (cls.TEST_SUITES_DIR / "framework" / "cmo").mkdir(parents=True, exist_ok=True)
        (cls.TEST_SUITES_DIR / "framework" / "specialist").mkdir(parents=True, exist_ok=True)
        (cls.TEST_SUITES_DIR / "studio-generated").mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_trace_path(cls, trace_id: str, date: str = None) -> Path:
        """Get path for a trace file"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        return cls.TRACES_DIR / date / f"trace_{trace_id}.json"
    
    @classmethod
    def get_test_case_path(cls, test_id: str, agent_type: str, date: str = None) -> Path:
        """Get path for a studio-generated test case"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        return cls.TEST_SUITES_DIR / "studio-generated" / agent_type / date / f"{test_id}.json"
    
    @classmethod
    def get_schema_path(cls, agent_type: str) -> Path:
        """Get schema file for agent type"""
        return cls.BASE_DIR / "schemas" / f"{agent_type}_schema.json"
    
    @classmethod
    def get_run_dir(cls, evaluation_id: str, date: str = None) -> Path:
        """Get directory for an evaluation run"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        run_dir = cls.RUNS_DIR / date / f"eval_{evaluation_id}"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "events").mkdir(exist_ok=True)
        (run_dir / "report").mkdir(exist_ok=True)
        return run_dir
    
    @classmethod
    def find_trace(cls, trace_id: str) -> Optional[Path]:
        """Find a trace file by ID"""
        for trace_file in cls.TRACES_DIR.rglob(f"*{trace_id}*.json"):
            if trace_file.is_file():
                return trace_file
        return None
    
    @classmethod
    def validate_test_case(cls, test_case: dict) -> bool:
        """Validate test case against its agent-specific schema"""
        agent_type = test_case.get("agent_type", "cmo")
        schema = cls.load_schema(agent_type)
        
        if not schema:
            # Fallback to basic validation
            return "id" in test_case and "agent_type" in test_case
        
        # Use jsonschema if available
        try:
            import jsonschema
            jsonschema.validate(test_case, schema)
            return True
        except:
            # Basic validation
            required = schema.get("required", [])
            return all(field in test_case for field in required)
```

#### 1.3 Create Test Loader
File: `evaluation/data/test_loader.py`

```python
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from evaluation.data.config import EvaluationDataConfig

class TestLoader:
    """Multi-agent test case loader for framework and studio tests"""
    
    @staticmethod
    def load_all_tests(agent_type: str = None) -> List[Dict[str, Any]]:
        """Load test cases, optionally filtered by agent type"""
        all_tests = []
        
        # Load framework tests
        framework_dir = EvaluationDataConfig.TEST_SUITES_DIR / "framework"
        if agent_type:
            # Load only specific agent type
            agent_dir = framework_dir / agent_type
            if agent_dir.exists():
                for test_file in agent_dir.rglob("*.json"):
                    tests = TestLoader._load_test_file(test_file)
                    all_tests.extend(tests)
        else:
            # Load all agent types
            for agent_dir in framework_dir.iterdir():
                if agent_dir.is_dir():
                    for test_file in agent_dir.rglob("*.json"):
                        tests = TestLoader._load_test_file(test_file)
                        all_tests.extend(tests)
        
        # Similar for studio-generated tests
        studio_dir = EvaluationDataConfig.TEST_SUITES_DIR / "studio-generated"
        if agent_type:
            agent_dir = studio_dir / agent_type
            if agent_dir.exists():
                for test_file in agent_dir.rglob("*.json"):
                    tests = TestLoader._load_test_file(test_file)
                    all_tests.extend(tests)
        else:
            for agent_dir in studio_dir.iterdir():
                if agent_dir.is_dir():
                    for test_file in agent_dir.rglob("*.json"):
                        tests = TestLoader._load_test_file(test_file)
                        all_tests.extend(tests)
        
        return all_tests
    
    @staticmethod
    def _load_test_file(file_path: Path) -> List[Dict[str, Any]]:
        """Load and validate test file"""
        try:
            with open(file_path) as f:
                data = json.load(f)
                if isinstance(data, list):
                    # Validate each test
                    valid_tests = []
                    for test in data:
                        if EvaluationDataConfig.validate_test_case(test):
                            valid_tests.append(test)
                    return valid_tests
                else:
                    # Single test
                    if EvaluationDataConfig.validate_test_case(data):
                        return [data]
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
        return []
    
    @staticmethod
    def load_test_by_id(test_id: str) -> Optional[Dict[str, Any]]:
        """Load a specific test case by ID"""
        all_tests = TestLoader.load_all_tests()
        for test in all_tests:
            if test.get("id") == test_id:
                return test
        return None
```

### Phase 2: Convert Python Tests to JSON (1 hour)

#### 2.1 Migration Script
File: `evaluation/data/migrate_tests.py`

```python
#!/usr/bin/env python3
"""One-time migration script to convert Python test cases to JSON"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add evaluation to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from evaluation.agents.cmo.test_cases import TEST_CASES as CMO_TESTS
from evaluation.data.config import EvaluationDataConfig

def migrate_cmo_tests():
    """Migrate CMO tests to new format"""
    # Initialize directories
    EvaluationDataConfig.init_directories()
    
    # Migrate CMO tests
    cmo_tests = []
    for test in CMO_TESTS:
        test_dict = {
            "id": test.id,
            "agent_type": "cmo",  # Add agent type
            "query": test.query,
            "expected_complexity": test.expected_complexity.value,
            "expected_specialties": [s.value for s in test.expected_specialties],
            "key_data_points": test.key_data_points,
            "category": test.notes.split()[0].lower() if test.notes else "general",
            "notes": test.notes,
            "created_by": "framework",
            "created_at": "2025-01-01T00:00:00Z"
        }
        cmo_tests.append(test_dict)
    
    # Save CMO tests by category
    categories = {}
    for test in cmo_tests:
        cat = test.get("category", "general")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(test)
    
    for category, tests in categories.items():
        path = EvaluationDataConfig.TEST_SUITES_DIR / "framework" / "cmo" / f"{category}_tests.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(tests, indent=2))
        print(f"Migrated {len(tests)} CMO {category} tests")

def migrate_specialist_tests():
    """Migrate specialist tests to new format"""
    # Different schema for specialist tests
    # Implementation depends on existing specialist test structure
    pass

def migrate_test_cases():
    """Run all migrations"""
    migrate_cmo_tests()
    migrate_specialist_tests()

if __name__ == "__main__":
    migrate_test_cases()
```

### Phase 3: Refactor Storage Operations (4 hours)

#### 3.1 Trace Storage Update
File: `backend/services/tracing/trace_service.py`

Add import and update save method:
```python
from evaluation.data.config import EvaluationDataConfig

def save_trace(self, trace: CompleteTrace) -> str:
    """Save trace to new location"""
    EvaluationDataConfig.init_directories()
    
    trace_path = EvaluationDataConfig.get_trace_path(trace.trace_id)
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(trace_path, 'w') as f:
        json.dump(trace.to_dict(), f, indent=2)
    
    logger.info(f"Saved trace to: {trace_path}")
    return str(trace_path)
```

#### 3.2 Evaluation Service Complete Refactor
File: `backend/services/evaluation/evaluation_service.py`

Complete refactor for file-based storage:
```python
from evaluation.data.config import EvaluationDataConfig

class EvaluationService:
    def __init__(self):
        # No more in-memory storage
        EvaluationDataConfig.init_directories()
    
    async def run_evaluation(self, test_case_data: Dict[str, Any], agent_type: str = "cmo") -> str:
        """Start evaluation with new storage"""
        evaluation_id = str(uuid.uuid4())
        run_dir = EvaluationDataConfig.get_run_dir(evaluation_id)
        
        # Write metadata immediately
        metadata = {
            "evaluation_id": evaluation_id,
            "test_case_id": test_case_data.get("id"),
            "trace_id": test_case_data.get("trace_id"),
            "agent_type": agent_type,
            "started_at": datetime.now().isoformat(),
            "status": "running"
        }
        (run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
        
        # Start async evaluation
        asyncio.create_task(self._run_evaluation_async(evaluation_id, test_case_data, agent_type))
        
        return evaluation_id
    
    def get_evaluation_events(self, evaluation_id: str, start_index: int = 0) -> Dict[str, Any]:
        """Read events from file system"""
        # Find run directory
        for run_dir in EvaluationDataConfig.RUNS_DIR.rglob(f"eval_{evaluation_id}"):
            if run_dir.is_dir():
                break
        else:
            return {"error": "Evaluation not found"}
        
        # Read events
        event_files = sorted((run_dir / "events").glob("*.json"))
        events = []
        for event_file in event_files[start_index:]:
            with open(event_file) as f:
                events.append(json.load(f))
        
        # Read metadata for status
        with open(run_dir / "metadata.json") as f:
            metadata = json.load(f)
        
        return {
            "evaluation_id": evaluation_id,
            "events": events,
            "total_events": len(event_files),
            "status": metadata.get("status", "unknown")
        }
```

#### 3.3 Event Storage in CLI Evaluator
File: `backend/eval_integration/cli_evaluator_adapter.py`

Update to store events in files:
```python
def store_event(event: Dict[str, Any]):
    """Store evaluation event in file system"""
    run_dir = EvaluationDataConfig.get_run_dir(evaluation_id)
    event_num = len(list((run_dir / "events").glob("*.json"))) + 1
    event_file = run_dir / "events" / f"{event_num:03d}_{event['type']}.json"
    event["timestamp"] = datetime.now().isoformat()
    event_file.write_text(json.dumps(event, indent=2))
```

### Phase 4: Update CLI Framework (2 hours)

#### 4.1 Update Test Runners
File: `evaluation/cli/run_evaluation.py`

Replace TEST_CASES import with:
```python
from evaluation.data.test_loader import TestLoader

# Load all tests
all_tests = TestLoader.load_all_tests()

# Or load by agent type
cmo_tests = TestLoader.load_all_tests(agent_type="cmo")
specialist_tests = TestLoader.load_all_tests(agent_type="specialist")
```

#### 4.2 Remove Old Test Files
After verifying migration, remove:
- `evaluation/agents/cmo/test_cases.py`
- `evaluation/agents/specialist/test_cases.py`

### Phase 5: Cleanup & Testing (1 hour)

#### 5.1 Delete Old Directories
```bash
rm -rf backend/traces
rm -rf backend/evaluation_results
```

#### 5.2 Update .gitignore
```gitignore
# Evaluation data artifacts
evaluation/data/traces/
evaluation/data/runs/
# Keep test-suites - they're test definitions
```

#### 5.3 End-to-End Testing
- [ ] Health query creates trace in `evaluation/data/traces/`
- [ ] Create test case saves to `evaluation/data/test-suites/studio-generated/`
- [ ] Run evaluation creates organized directory in `evaluation/data/runs/`
- [ ] Events stream to files in real-time
- [ ] Frontend can poll and display events
- [ ] Report generates using single `result.json`
- [ ] CLI can run both framework and studio tests

## Environment Variables

```bash
# Optional - redirect storage locations
EVAL_TRACES_DIR=/tmp/evaluation/traces
EVAL_RUNS_DIR=/tmp/evaluation/runs
```

## Success Metrics

1. **No data loss**: Server reloads don't lose evaluation progress
2. **Unified tests**: Single JSON format for all test cases
3. **Clean storage**: One location for each data type
4. **No duplication**: Single result.json per evaluation
5. **Configurable**: Can redirect storage via environment

## Files to Modify

### Backend
- `backend/services/tracing/trace_service.py`
- `backend/services/evaluation/evaluation_service.py`
- `backend/eval_integration/cli_evaluator_adapter.py`
- `backend/services/evaluation/report_service.py`
- `backend/api/evaluation.py`
- `backend/api/qe_chat.py`

### Evaluation Framework
- `evaluation/cli/run_evaluation.py`
- Remove: `evaluation/agents/*/test_cases.py`

### New Files
- `evaluation/data/config.py`
- `evaluation/data/test_loader.py`
- `evaluation/data/migrate_tests.py`

## No Migration Required

Since backward compatibility is not required:
- Delete all existing traces and results
- Start fresh with new structure
- No data migration scripts needed