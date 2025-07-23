#!/usr/bin/env python3
"""Fix uppercase specialties in test JSON files to match enum values"""

import json
import glob
from pathlib import Path

# Mapping of uppercase to lowercase specialties
SPECIALTY_MAP = {
    "ENDOCRINOLOGY": "endocrinology",
    "CARDIOLOGY": "cardiology", 
    "NUTRITION": "nutrition",
    "PREVENTIVE_MEDICINE": "preventive_medicine",
    "LABORATORY_MEDICINE": "laboratory_medicine",
    "PHARMACY": "pharmacy",
    "DATA_ANALYSIS": "data_analysis",
    "GENERAL_PRACTICE": "general_practice",
    "LIFESTYLE": "lifestyle",
    "EMERGENCY": "emergency",
    "DIAGNOSTICS": "diagnostics",
    "RISK_ANALYSIS": "risk_analysis"
}

def fix_specialties_in_file(file_path):
    """Fix uppercase specialties in a single file"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    modified = False
    
    # Handle list of test cases
    if isinstance(data, list):
        for test in data:
            if 'expected_specialties' in test and isinstance(test['expected_specialties'], list):
                new_specialties = []
                for spec in test['expected_specialties']:
                    if spec in SPECIALTY_MAP:
                        new_specialties.append(SPECIALTY_MAP[spec])
                        modified = True
                    else:
                        new_specialties.append(spec)
                test['expected_specialties'] = new_specialties
    # Handle single test case
    elif isinstance(data, dict) and 'expected_specialties' in data:
        new_specialties = []
        for spec in data['expected_specialties']:
            if spec in SPECIALTY_MAP:
                new_specialties.append(SPECIALTY_MAP[spec])
                modified = True
            else:
                new_specialties.append(spec)
        data['expected_specialties'] = new_specialties
    
    if modified:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Fixed specialties in: {file_path}")
    else:
        print(f"⏭️  No changes needed: {file_path}")

def main():
    """Fix all test files"""
    base_dir = Path(__file__).parent
    test_files = glob.glob(str(base_dir / "test-suites" / "framework" / "**" / "*.json"), recursive=True)
    
    print(f"Found {len(test_files)} test files to check...")
    
    for file_path in test_files:
        fix_specialties_in_file(file_path)
    
    print("\nDone! All test files have been updated to use lowercase specialties.")

if __name__ == "__main__":
    main()