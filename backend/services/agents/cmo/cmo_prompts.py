import os
from datetime import datetime
from pathlib import Path

class CMOPrompts:
    """Manages prompts for the CMO agent"""
    
    def __init__(self):
        self.prompt_dir = Path(__file__).parent / "prompts"
        self._load_prompts()
    
    def _load_prompts(self):
        """Load all prompt templates from files"""
        self.prompts = {}
        for prompt_file in self.prompt_dir.glob("*.txt"):
            with open(prompt_file, 'r') as f:
                self.prompts[prompt_file.stem] = f.read()
    
    def get_initial_analysis_prompt(self, query: str) -> str:
        """Get prompt for initial query analysis with tool usage"""
        return self.prompts["1_initial_analysis"].replace(
            "{{CURRENT_DATE}}", datetime.now().strftime("%Y-%m-%d")
        ).replace("{{QUERY}}", query)
    
    def get_analysis_summary_prompt(self) -> str:
        """Get prompt for summarizing initial analysis"""
        return self.prompts["2_initial_analysis_summarize"]
    
    def get_task_creation_prompt(
        self, 
        query: str, 
        complexity: str, 
        approach: str, 
        initial_data: str,
        num_specialists: int,
        tool_limit: int = 5
    ) -> str:
        """Get prompt for creating specialist tasks"""
        return self.prompts["3_task_creation"].replace(
            "{{QUERY}}", query
        ).replace(
            "{{COMPLEXITY}}", complexity
        ).replace(
            "{{APPROACH}}", approach
        ).replace(
            "{{INITIAL_DATA}}", initial_data
        ).replace(
            "{{NUM_SPECIALISTS}}", str(num_specialists)
        ).replace(
            "{{TOOL_LIMIT}}", str(tool_limit)
        )
    
    def get_synthesis_prompt(self, query: str, specialist_findings: str) -> str:
        """Get prompt for final synthesis"""
        return self.prompts["4_synthesis"].replace(
            "{{QUERY}}", query
        ).replace(
            "{{SPECIALIST_FINDINGS}}", specialist_findings
        )