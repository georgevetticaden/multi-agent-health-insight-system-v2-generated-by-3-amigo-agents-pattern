import os
from datetime import datetime
from pathlib import Path
from typing import Dict

class SpecialistPrompts:
    """Manages prompts for specialist agents"""
    
    def __init__(self):
        self.prompt_dir = Path(__file__).parent / "prompts"
        self.specialty_file_map = {
            "general_practice": "system_general_practice.txt",
            "endocrinology": "system_endocrinology.txt",
            "cardiology": "system_cardiology.txt",
            "nutrition": "system_nutrition.txt",
            "preventive_medicine": "system_preventive_medicine.txt",
            "laboratory_medicine": "system_laboratory_medicine.txt",
            "pharmacy": "system_pharmacy.txt",
            "data_analysis": "system_data_analysis.txt"
        }
        self._load_prompts()
    
    def _load_prompts(self):
        """Load all prompt templates from files"""
        self.prompts = {}
        
        # Load system prompts for each specialty
        for specialty, filename in self.specialty_file_map.items():
            filepath = self.prompt_dir / filename
            if filepath.exists():
                with open(filepath, 'r') as f:
                    self.prompts[f"system_{specialty}"] = f.read()
        
        # Load task execution and analysis prompts
        for prompt_file in ["1_task_execution.txt", "2_final_analysis.txt"]:
            filepath = self.prompt_dir / prompt_file
            if filepath.exists():
                with open(filepath, 'r') as f:
                    self.prompts[prompt_file.replace('.txt', '')] = f.read()
    
    def get_system_prompt(self, specialty: str) -> str:
        """Get system prompt for a specific specialty"""
        current_date = datetime.now()
        prompt_key = f"system_{specialty}"
        
        if prompt_key not in self.prompts:
            raise ValueError(f"No system prompt found for specialty: {specialty}")
        
        return self.prompts[prompt_key].format(
            current_date=current_date.strftime("%Y-%m-%d"),
            current_year=current_date.year
        )
    
    def get_task_execution_prompt(
        self,
        objective: str,
        context: str,
        expected_output: str,
        max_tool_calls: int
    ) -> str:
        """Get task execution prompt with parameters"""
        return self.prompts["1_task_execution"].format(
            objective=objective,
            context=context,
            expected_output=expected_output,
            max_tool_calls=max_tool_calls
        )
    
    def get_final_analysis_prompt(self) -> str:
        """Get final analysis prompt"""
        return self.prompts["2_final_analysis"]