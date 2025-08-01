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
        
        # Load studio-generated tests
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
    
    @staticmethod
    def save_test_case(test_case: Dict[str, Any], source: str = "studio") -> bool:
        """Save a test case to the appropriate location"""
        if not EvaluationDataConfig.validate_test_case(test_case):
            print("Invalid test case format")
            return False
        
        agent_type = test_case.get("agent_type", "cmo")
        test_id = test_case.get("id")
        
        if source == "studio":
            # Save to studio-generated directory
            test_path = EvaluationDataConfig.get_test_case_path(test_id, agent_type)
            test_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Save to framework directory
            category = test_case.get("category", "general")
            test_path = (EvaluationDataConfig.TEST_SUITES_DIR / "framework" / 
                        agent_type / f"{category}_tests.json")
            test_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing tests if file exists
            existing_tests = []
            if test_path.exists():
                with open(test_path) as f:
                    existing_tests = json.load(f)
            
            # Add new test and save
            existing_tests.append(test_case)
            test_case = existing_tests
        
        # Write test case(s)
        with open(test_path, 'w') as f:
            json.dump(test_case, f, indent=2)
        
        return True
    
    @staticmethod
    def get_test_categories(agent_type: str = None) -> Dict[str, int]:
        """Get all test categories with counts"""
        categories = {}
        tests = TestLoader.load_all_tests(agent_type)
        
        for test in tests:
            cat = test.get("category", "general")
            categories[cat] = categories.get(cat, 0) + 1
        
        return categories