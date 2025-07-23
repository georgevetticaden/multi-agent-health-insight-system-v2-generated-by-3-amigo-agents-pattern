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
        print(f"Migrated {len(tests)} CMO {category} tests to {path}")

    # Also save all tests in one file for convenience
    all_tests_path = EvaluationDataConfig.TEST_SUITES_DIR / "framework" / "cmo" / "all_tests.json"
    all_tests_path.write_text(json.dumps(cmo_tests, indent=2))
    print(f"Saved all {len(cmo_tests)} CMO tests to {all_tests_path}")

def migrate_specialist_tests():
    """Migrate specialist tests to new format"""
    # Check if specialist tests exist
    try:
        from evaluation.agents.specialist.test_cases import TEST_CASES as SPECIALIST_TESTS
        
        specialist_tests = []
        for test in SPECIALIST_TESTS:
            # Adapt to specialist schema
            test_dict = {
                "id": test.id,
                "agent_type": "specialist",
                "specialist_type": getattr(test, 'specialist_type', 'GENERAL'),
                "task": {
                    "objective": test.query,
                    "context": getattr(test, 'context', ''),
                    "expected_output": getattr(test, 'expected_output', ''),
                    "priority": "high",
                    "max_tool_calls": 5
                },
                "expected_tools": getattr(test, 'expected_tools', []),
                "expected_data_points": getattr(test, 'expected_data_points', test.key_data_points),
                "validation_criteria": {},
                "created_by": "framework",
                "created_at": "2025-01-01T00:00:00Z"
            }
            specialist_tests.append(test_dict)
        
        # Save by specialist type
        types = {}
        for test in specialist_tests:
            spec_type = test.get("specialist_type", "general")
            if spec_type not in types:
                types[spec_type] = []
            types[spec_type].append(test)
        
        for spec_type, tests in types.items():
            path = EvaluationDataConfig.TEST_SUITES_DIR / "framework" / "specialist" / f"{spec_type.lower()}_tests.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(tests, indent=2))
            print(f"Migrated {len(tests)} specialist {spec_type} tests to {path}")
            
    except ImportError:
        print("No specialist test cases found to migrate")

def migrate_visualization_tests():
    """Create sample visualization tests"""
    # Create sample visualization tests since they likely don't exist yet
    viz_tests = [
        {
            "id": "viz_test_001",
            "agent_type": "visualization",
            "query": "Create a chart showing blood pressure trends over the last 6 months",
            "input_data": {
                "type": "time_series",
                "metrics": ["systolic_bp", "diastolic_bp"],
                "time_range": "6_months"
            },
            "expected_chart_type": "LineChart",
            "expected_features": ["dual_y_axis", "trend_line", "date_axis"],
            "expected_libraries": ["recharts"],
            "created_by": "framework",
            "created_at": "2025-01-01T00:00:00Z"
        },
        {
            "id": "viz_test_002",
            "agent_type": "visualization",
            "query": "Show distribution of cholesterol levels by age group",
            "input_data": {
                "type": "distribution",
                "metrics": ["cholesterol_total", "cholesterol_ldl", "cholesterol_hdl"],
                "grouping": "age_group"
            },
            "expected_chart_type": "BarChart",
            "expected_features": ["grouped_bars", "legend", "tooltips"],
            "expected_libraries": ["recharts"],
            "created_by": "framework",
            "created_at": "2025-01-01T00:00:00Z"
        }
    ]
    
    path = EvaluationDataConfig.TEST_SUITES_DIR / "framework" / "visualization" / "sample_tests.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(viz_tests, indent=2))
    print(f"Created {len(viz_tests)} sample visualization tests at {path}")

def migrate_test_cases():
    """Run all migrations"""
    print("Starting test case migration...")
    print("-" * 50)
    
    migrate_cmo_tests()
    print()
    
    migrate_specialist_tests()
    print()
    
    migrate_visualization_tests()
    print()
    
    print("-" * 50)
    print("Migration complete!")
    print("\nYou can now:")
    print("1. Remove old Python test case files")
    print("2. Update imports to use TestLoader")
    print("3. Test the new loading system")

if __name__ == "__main__":
    migrate_test_cases()