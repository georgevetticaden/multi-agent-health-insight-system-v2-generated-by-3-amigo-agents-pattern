#!/usr/bin/env python3
"""Simple migration to manually create JSON test cases from CMO test structure"""

import json
from pathlib import Path
from datetime import datetime

# Get the base directory
BASE_DIR = Path(__file__).parent
TEST_SUITES_DIR = BASE_DIR / "test-suites"

def create_sample_cmo_tests():
    """Create sample CMO test cases based on the test_cases.py structure"""
    
    # Sample test cases based on the CMO test structure
    cmo_tests = [
        # Simple queries
        {
            "id": "simple_001",
            "agent_type": "cmo",
            "query": "What is my current blood sugar level?",
            "expected_complexity": "SIMPLE",
            "expected_specialties": ["ENDOCRINOLOGY"],
            "key_data_points": ["glucose", "latest_labs"],
            "category": "diabetes",
            "notes": "Simple single data point query",
            "created_by": "framework",
            "created_at": "2025-01-01T00:00:00Z"
        },
        {
            "id": "simple_002",
            "agent_type": "cmo",
            "query": "Show me my latest blood pressure reading",
            "expected_complexity": "SIMPLE",
            "expected_specialties": ["CARDIOLOGY"],
            "key_data_points": ["blood_pressure", "latest_vitals"],
            "category": "cardiac",
            "notes": "Simple vital sign query",
            "created_by": "framework",
            "created_at": "2025-01-01T00:00:00Z"
        },
        # Standard queries
        {
            "id": "standard_001",
            "agent_type": "cmo",
            "query": "Show me my blood pressure trends over the last 3 months",
            "expected_complexity": "STANDARD",
            "expected_specialties": ["CARDIOLOGY", "DATA_ANALYSIS"],
            "key_data_points": ["blood_pressure", "trends", "3_months"],
            "category": "cardiac",
            "notes": "Standard trend analysis",
            "created_by": "framework",
            "created_at": "2025-01-01T00:00:00Z"
        },
        {
            "id": "standard_002",
            "agent_type": "cmo",
            "query": "Compare my cholesterol levels before and after starting statins",
            "expected_complexity": "STANDARD",
            "expected_specialties": ["CARDIOLOGY", "PHARMACY"],
            "key_data_points": ["cholesterol", "statins", "medication_timeline"],
            "category": "cardiac",
            "notes": "Medication effectiveness analysis",
            "created_by": "framework",
            "created_at": "2025-01-01T00:00:00Z"
        },
        # Complex queries
        {
            "id": "complex_001",
            "agent_type": "cmo",
            "query": "How has my diabetes management changed since starting the new medication regimen, including A1C trends, glucose variability, and any side effects?",
            "expected_complexity": "COMPLEX",
            "expected_specialties": ["ENDOCRINOLOGY", "PHARMACY", "DATA_ANALYSIS"],
            "key_data_points": ["a1c", "glucose_variability", "medications", "side_effects", "trends"],
            "category": "diabetes",
            "notes": "Complex multi-dimensional analysis",
            "created_by": "framework",
            "created_at": "2025-01-01T00:00:00Z"
        },
        {
            "id": "complex_002",
            "agent_type": "cmo",
            "query": "Analyze my heart health including blood pressure trends, cholesterol levels, exercise data, and medication adherence over the past year",
            "expected_complexity": "COMPLEX",
            "expected_specialties": ["CARDIOLOGY", "PHARMACY", "LIFESTYLE", "DATA_ANALYSIS"],
            "key_data_points": ["blood_pressure", "cholesterol", "exercise", "medication_adherence", "yearly_trends"],
            "category": "cardiac",
            "notes": "Comprehensive cardiac health analysis",
            "created_by": "framework",
            "created_at": "2025-01-01T00:00:00Z"
        },
        # Critical queries
        {
            "id": "critical_001",
            "agent_type": "cmo",
            "query": "I've been experiencing chest pain and shortness of breath. Analyze my recent cardiac markers, ECG results, blood pressure trends, and any relevant risk factors",
            "expected_complexity": "CRITICAL",
            "expected_specialties": ["CARDIOLOGY", "EMERGENCY", "DIAGNOSTICS", "RISK_ANALYSIS"],
            "key_data_points": ["cardiac_markers", "ecg", "blood_pressure", "symptoms", "risk_factors"],
            "category": "emergency",
            "notes": "Critical symptom analysis requiring urgent attention",
            "created_by": "framework",
            "created_at": "2025-01-01T00:00:00Z"
        }
    ]
    
    # Save by category
    categories = {}
    for test in cmo_tests:
        cat = test.get("category", "general")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(test)
    
    # Create framework test directory
    framework_dir = TEST_SUITES_DIR / "framework" / "cmo"
    framework_dir.mkdir(parents=True, exist_ok=True)
    
    # Save each category
    for category, tests in categories.items():
        path = framework_dir / f"{category}_tests.json"
        with open(path, 'w') as f:
            json.dump(tests, f, indent=2)
        print(f"Created {len(tests)} CMO {category} tests at {path}")
    
    # Save all tests
    all_path = framework_dir / "all_tests.json"
    with open(all_path, 'w') as f:
        json.dump(cmo_tests, f, indent=2)
    print(f"Created all {len(cmo_tests)} CMO tests at {all_path}")

def create_sample_specialist_tests():
    """Create sample specialist test cases"""
    
    specialist_tests = [
        {
            "id": "specialist_001",
            "agent_type": "specialist",
            "specialist_type": "CARDIOLOGY",
            "task": {
                "objective": "Analyze blood pressure trends",
                "context": "Patient on lisinopril for 6 months",
                "expected_output": "Trend analysis with medication correlation",
                "priority": "high",
                "max_tool_calls": 5
            },
            "expected_tools": ["execute_health_query_v2"],
            "expected_data_points": ["systolic_bp", "diastolic_bp", "medication_dates"],
            "validation_criteria": {
                "must_identify_trend": True,
                "must_correlate_medication": True
            },
            "created_by": "framework",
            "created_at": "2025-01-01T00:00:00Z"
        },
        {
            "id": "specialist_002",
            "agent_type": "specialist",
            "specialist_type": "ENDOCRINOLOGY",
            "task": {
                "objective": "Evaluate diabetes control",
                "context": "Type 2 diabetes patient with recent medication change",
                "expected_output": "A1C trend analysis and glucose variability assessment",
                "priority": "high",
                "max_tool_calls": 5
            },
            "expected_tools": ["execute_health_query_v2"],
            "expected_data_points": ["a1c", "glucose_readings", "medication_changes"],
            "validation_criteria": {
                "must_analyze_a1c": True,
                "must_assess_variability": True
            },
            "created_by": "framework",
            "created_at": "2025-01-01T00:00:00Z"
        }
    ]
    
    # Save specialist tests
    specialist_dir = TEST_SUITES_DIR / "framework" / "specialist"
    specialist_dir.mkdir(parents=True, exist_ok=True)
    
    path = specialist_dir / "general_tests.json"
    with open(path, 'w') as f:
        json.dump(specialist_tests, f, indent=2)
    print(f"Created {len(specialist_tests)} specialist tests at {path}")

def create_sample_visualization_tests():
    """Create sample visualization test cases"""
    
    viz_tests = [
        {
            "id": "viz_001",
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
            "id": "viz_002",
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
    
    # Save visualization tests
    viz_dir = TEST_SUITES_DIR / "framework" / "visualization"
    viz_dir.mkdir(parents=True, exist_ok=True)
    
    path = viz_dir / "chart_tests.json"
    with open(path, 'w') as f:
        json.dump(viz_tests, f, indent=2)
    print(f"Created {len(viz_tests)} visualization tests at {path}")

def main():
    """Run the migration"""
    print("Creating sample test cases in JSON format...")
    print("-" * 50)
    
    create_sample_cmo_tests()
    print()
    
    create_sample_specialist_tests()
    print()
    
    create_sample_visualization_tests()
    print()
    
    print("-" * 50)
    print("Sample test creation complete!")
    print("\nThe test cases are now available in:")
    print(f"  {TEST_SUITES_DIR}/framework/")

if __name__ == "__main__":
    main()