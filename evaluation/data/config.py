from pathlib import Path
from datetime import datetime
import os
import json
from typing import Optional, Dict, Any

class EvaluationDataConfig:
    """Central configuration for all evaluation data storage"""
    
    # Base paths
    BASE_DIR = Path(__file__).parent
    TRACES_DIR = Path(os.getenv("EVAL_TRACES_DIR", str(BASE_DIR / "traces")))
    RUNS_DIR = Path(os.getenv("EVAL_RUNS_DIR", str(BASE_DIR / "runs")))
    TEST_SUITES_DIR = BASE_DIR / "test-suites"  # Always relative to framework
    SCHEMAS_DIR = BASE_DIR / "schemas"
    
    # Test case schemas for validation
    CMO_TEST_SCHEMA = {
        "type": "object",
        "required": ["id", "agent_type", "query", "expected_complexity", "expected_specialties"],
        "properties": {
            "id": {"type": "string"},
            "agent_type": {"type": "string", "enum": ["cmo"]},
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
    
    SPECIALIST_TEST_SCHEMA = {
        "type": "object",
        "required": ["id", "agent_type", "specialist_type", "task"],
        "properties": {
            "id": {"type": "string"},
            "agent_type": {"type": "string", "enum": ["specialist"]},
            "specialist_type": {"type": "string"},
            "task": {
                "type": "object",
                "required": ["objective", "context", "expected_output"],
                "properties": {
                    "objective": {"type": "string"},
                    "context": {"type": "string"},
                    "expected_output": {"type": "string"},
                    "priority": {"type": "string"},
                    "max_tool_calls": {"type": "integer"}
                }
            },
            "expected_tools": {"type": "array", "items": {"type": "string"}},
            "expected_data_points": {"type": "array", "items": {"type": "string"}},
            "validation_criteria": {"type": "object"},
            "trace_id": {"type": "string"},
            "created_at": {"type": "string"},
            "created_by": {"enum": ["framework", "studio"]}
        }
    }
    
    VISUALIZATION_TEST_SCHEMA = {
        "type": "object",
        "required": ["id", "agent_type", "query", "input_data"],
        "properties": {
            "id": {"type": "string"},
            "agent_type": {"type": "string", "enum": ["visualization"]},
            "query": {"type": "string"},
            "input_data": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "metrics": {"type": "array", "items": {"type": "string"}},
                    "time_range": {"type": "string"}
                }
            },
            "expected_chart_type": {"type": "string"},
            "expected_features": {"type": "array", "items": {"type": "string"}},
            "expected_libraries": {"type": "array", "items": {"type": "string"}},
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
        cls.SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        for agent_type in ["cmo", "specialist", "visualization"]:
            (cls.TEST_SUITES_DIR / "framework" / agent_type).mkdir(parents=True, exist_ok=True)
            (cls.TEST_SUITES_DIR / "studio-generated" / agent_type).mkdir(parents=True, exist_ok=True)
    
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
        return cls.SCHEMAS_DIR / f"{agent_type}_schema.json"
    
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
        """Find a trace file by ID across all date directories."""
        for date_dir in cls.TRACES_DIR.iterdir():
            if date_dir.is_dir():
                # Try new naming pattern first (HHMMSS_trace_id.json)
                for trace_file in date_dir.glob(f"*_{trace_id}.json"):
                    return trace_file
                
                # Fallback to old naming pattern (trace_id.json)
                trace_file = date_dir / f"{trace_id}.json"
                if trace_file.exists():
                    return trace_file
        return None
    
    @classmethod
    def find_run_dir(cls, evaluation_id: str) -> Optional[Path]:
        """Find evaluation run directory by ID"""
        for run_dir in cls.RUNS_DIR.rglob(f"eval_{evaluation_id}"):
            if run_dir.is_dir():
                return run_dir
        return None
    
    @classmethod
    def get_schema(cls, agent_type: str) -> Dict[str, Any]:
        """Get test case schema for agent type"""
        if agent_type == "cmo":
            return cls.CMO_TEST_SCHEMA
        elif agent_type == "specialist":
            return cls.SPECIALIST_TEST_SCHEMA
        elif agent_type == "visualization":
            return cls.VISUALIZATION_TEST_SCHEMA
        else:
            # Basic schema for unknown types
            return {
                "type": "object",
                "required": ["id", "agent_type"],
                "properties": {
                    "id": {"type": "string"},
                    "agent_type": {"type": "string"}
                }
            }
    
    @classmethod
    def validate_test_case(cls, test_case: dict) -> bool:
        """Validate test case against its agent-specific schema"""
        agent_type = test_case.get("agent_type", "cmo")
        schema = cls.get_schema(agent_type)
        
        # Use jsonschema if available
        try:
            import jsonschema
            jsonschema.validate(test_case, schema)
            return True
        except ImportError:
            # Basic validation without jsonschema
            required = schema.get("required", [])
            return all(field in test_case for field in required)
        except Exception:
            return False
    
    @classmethod
    def save_schema_files(cls):
        """Save schema definitions to JSON files"""
        cls.SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
        
        schemas = {
            "cmo": cls.CMO_TEST_SCHEMA,
            "specialist": cls.SPECIALIST_TEST_SCHEMA,
            "visualization": cls.VISUALIZATION_TEST_SCHEMA
        }
        
        for agent_type, schema in schemas.items():
            schema_path = cls.get_schema_path(agent_type)
            with open(schema_path, 'w') as f:
                json.dump(schema, f, indent=2)