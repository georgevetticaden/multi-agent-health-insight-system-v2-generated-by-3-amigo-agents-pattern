"""
Test Case Converter

Converts JSON test cases to the expected test case objects for CLI evaluation.
"""

from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass


@dataclass
class CMOTestCase:
    """Simple test case class for CMO evaluation"""
    id: str
    query: str
    expected_complexity: str
    expected_specialties: Set[str]
    key_data_points: List[str]
    description: str = ""
    category: str = "general"
    notes: Optional[str] = None
    based_on_real_query: bool = False


def convert_json_to_cmo_test_case(test_dict: Dict[str, Any]) -> CMOTestCase:
    """Convert JSON test case to CMOTestCase object"""
    # expected_complexity is a string in TestCase, not an enum
    expected_complexity = test_dict.get("expected_complexity", "STANDARD")
    
    # expected_specialties is a Set[str], not enum
    expected_specialties = set(test_dict.get("expected_specialties", []))
    
    return CMOTestCase(
        id=test_dict["id"],
        query=test_dict["query"],
        expected_complexity=expected_complexity,
        expected_specialties=expected_specialties,
        key_data_points=test_dict.get("key_data_points", []),
        description=test_dict.get("notes", ""),
        category=test_dict.get("category", "general"),
        notes=test_dict.get("notes"),
        based_on_real_query=test_dict.get("based_on_real_query", False)
    )


def convert_json_test_cases(test_dicts: List[Dict[str, Any]], agent_type: str) -> List[Any]:
    """Convert list of JSON test cases to appropriate objects based on agent type"""
    if agent_type == "cmo":
        return [convert_json_to_cmo_test_case(td) for td in test_dicts]
    elif agent_type == "specialist":
        # For now, specialist tests can remain as dicts
        # Future: implement proper specialist test case conversion
        return test_dicts
    else:
        # Unknown agent type, return as is
        return test_dicts