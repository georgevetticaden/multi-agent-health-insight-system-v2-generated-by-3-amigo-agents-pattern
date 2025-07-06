"""
Visualization Agent Prompts Module

Manages all prompts for the medical visualization agent.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json


class VisualizationPrompts:
    """Manages visualization agent prompts loaded from external files"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self._cache: Dict[str, str] = {}
    
    def _load_prompt(self, filename: str) -> str:
        """Load and cache prompt from file"""
        if filename not in self._cache:
            file_path = self.base_path / filename
            with open(file_path, 'r', encoding='utf-8') as f:
                self._cache[filename] = f.read()
        return self._cache[filename]
    
    def get_generation_prompt(
        self,
        query: str,
        query_type: str,
        synthesis_text: str,
        key_data_points: Dict[str, Any],
        result_count: int
    ) -> str:
        """Get the main visualization generation prompt"""
        base_template = self._load_prompt("generation_base.txt")
        
        # Load query type examples
        example = self.get_query_type_example(query_type)
        
        # Load instructions
        instructions = self._load_prompt("instructions_general.txt")
        
        # Use safe string replacement to avoid issues with curly braces in JavaScript code
        prompt = base_template
        prompt = prompt.replace("{query}", query)
        prompt = prompt.replace("{query_type}", query_type)
        prompt = prompt.replace("{synthesis_summary}", synthesis_text[:2000] + ("..." if len(synthesis_text) > 2000 else ""))
        prompt = prompt.replace("{key_data_points}", json.dumps(key_data_points, indent=2)[:1500] + ("..." if len(json.dumps(key_data_points)) > 1500 else ""))
        prompt = prompt.replace("{result_count}", str(result_count))
        prompt = prompt.replace("{examples}", example)
        prompt = prompt.replace("{instructions}", instructions)
        
        return prompt
    
    def get_query_type_example(self, query_type: str) -> str:
        """Get visualization example for specific query type"""
        example_map = {
            "time_series": "example_time_series.txt",
            "abnormal_results": "example_abnormal_results.txt",
            "medication_adherence": "example_medication_adherence.txt",
            "correlation": "example_correlation.txt",
            "before_after": "example_before_after.txt",
            "general": "example_time_series.txt"  # Default to time series
        }
        
        filename = example_map.get(query_type, "example_time_series.txt")
        return self._load_prompt(filename)