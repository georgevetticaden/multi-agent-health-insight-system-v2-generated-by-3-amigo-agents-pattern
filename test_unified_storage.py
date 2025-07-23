#!/usr/bin/env python3
"""Test script for unified evaluation storage architecture"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

# Test imports
try:
    print("Testing evaluation data config...")
    from evaluation.data.config import EvaluationDataConfig
    config = EvaluationDataConfig()
    config.init_directories()
    print(f"✅ Config loaded, traces dir: {config.TRACES_DIR}")
except Exception as e:
    print(f"❌ Config import failed: {e}")

try:
    print("\nTesting test loader...")
    from evaluation.data.test_loader import TestLoader
    tests = TestLoader.load_all_tests("cmo")
    print(f"✅ Loaded {len(tests)} CMO tests")
    
    # Save a test case
    test_case = {
        "id": "test_storage_001",
        "agent_type": "cmo",
        "query": "Test query for storage",
        "expected_complexity": "SIMPLE",
        "expected_specialties": ["GENERAL_PRACTICE"],
        "created_at": datetime.now().isoformat(),
        "created_by": "studio"
    }
    if TestLoader.save_test_case(test_case, source="studio"):
        print("✅ Test case saved successfully")
except Exception as e:
    print(f"❌ Test loader failed: {e}")

try:
    print("\nTesting evaluation service...")
    from backend.services.evaluation.evaluation_service import EvaluationService
    eval_service = EvaluationService()
    print(f"✅ Evaluation service initialized (unified storage: {eval_service.use_unified_storage})")
    
    # Create a dummy evaluation
    if eval_service.use_unified_storage:
        eval_id = "test_eval_001"
        run_dir = config.get_run_dir(eval_id)
        print(f"✅ Created run directory: {run_dir}")
        
        # Store an event
        event = {"type": "test", "message": "Test event", "timestamp": datetime.now().isoformat()}
        event_file = run_dir / "events" / "001_test.json"
        event_file.write_text(json.dumps(event, indent=2))
        print("✅ Event stored to file")
        
        # Read events back
        events = eval_service.get_evaluation_events(eval_id)
        print(f"✅ Retrieved {len(events.get('events', []))} events")
except Exception as e:
    print(f"❌ Evaluation service test failed: {e}")

print("\n" + "="*50)
print("Unified Storage Test Summary:")
print(f"- Config directory: {config.BASE_DIR}")
print(f"- Traces directory: {config.TRACES_DIR}")
print(f"- Test suites directory: {config.TEST_SUITES_DIR}")
print(f"- Runs directory: {config.RUNS_DIR}")
print("="*50)