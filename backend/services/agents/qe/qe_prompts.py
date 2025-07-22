from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class QEPrompts:
    """Manages prompts for the QE (Quality Evaluation) Agent"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent / "prompts"
        self.examples_path = self.base_path / "examples"
        self._validate_prompts_exist()
    
    def _validate_prompts_exist(self):
        """Ensure all required prompt files exist"""
        required_prompts = [
            "1_collaborative_context.txt",
            "2_build_test_case.txt"
        ]
        
        # Also check for legacy prompts and use them if new ones don't exist
        legacy_prompts = [
            "1_analyze_trace_context.txt",
            "2_identify_issues.txt",
            "3_generate_test_case.txt"
        ]
        
        for prompt in required_prompts:
            if not (self.base_path / prompt).exists():
                raise FileNotFoundError(f"Required prompt file not found: {prompt}")
    
    def _load_prompt(self, filename: str) -> str:
        """Load a prompt from file"""
        try:
            with open(self.base_path / filename, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading prompt {filename}: {e}")
            raise
    
    def _load_example(self, filename: str) -> str:
        """Load an example from the examples directory"""
        try:
            with open(self.examples_path / filename, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading example {filename}: {e}")
            return ""
    
    def get_collaborative_context_prompt(self) -> str:
        """Get the prompt for collaborative test case building"""
        if (self.base_path / "1_collaborative_context.txt").exists():
            return self._load_prompt("1_collaborative_context.txt")
        return self._load_prompt("1_analyze_trace_context.txt")
    
    def get_build_test_case_prompt(self) -> str:
        """Get the prompt for building test cases"""
        if (self.base_path / "2_build_test_case.txt").exists():
            return self._load_prompt("2_build_test_case.txt")
        return self._load_prompt("2_identify_issues.txt")
    
    def get_analyze_context_prompt(self) -> str:
        """Get the prompt for analyzing trace context (legacy)"""
        return self._load_prompt("1_analyze_trace_context.txt")
    
    def get_identify_issues_prompt(self) -> str:
        """Get the prompt for identifying issues (legacy)"""
        return self._load_prompt("2_identify_issues.txt")
    
    def get_generate_test_case_prompt(self) -> str:
        """Get the prompt for generating test cases (legacy)"""
        return self._load_prompt("3_generate_test_case.txt")
    
    def get_example_for_error_type(self, error_type: str) -> Optional[str]:
        """Get an example for a specific error type"""
        example_map = {
            "complexity": "complexity_error_example.txt",
            "specialist": "specialist_selection_example.txt",
            "analysis": "analysis_quality_example.txt",
            "tool": "tool_usage_example.txt",
            "structure": "response_structure_example.txt",
            "refinement": "refinement_count_example.txt"
        }
        
        filename = example_map.get(error_type)
        if filename and (self.examples_path / filename).exists():
            return self._load_example(filename)
        return None
    
    def build_system_prompt(self, include_examples: bool = True, collaborative: bool = True) -> str:
        """Build the complete system prompt for the QE agent"""
        if collaborative:
            parts = [
                self.get_collaborative_context_prompt(),
                "\n\n",
                self.get_build_test_case_prompt()
            ]
        else:
            parts = [
                self.get_analyze_context_prompt(),
                "\n\n",
                self.get_identify_issues_prompt(),
                "\n\n",
                self.get_generate_test_case_prompt()
            ]
        
        if include_examples:
            # Add refinement example first (most important)
            refinement_example = self.get_example_for_error_type("refinement")
            if refinement_example:
                parts.extend(["\n\n", "## CRITICAL: Refinement Example\n\n", refinement_example])
            
            # Add other relevant examples
            for error_type in ["complexity", "specialist"]:
                example = self.get_example_for_error_type(error_type)
                if example:
                    parts.extend(["\n\n", "---\n\n", example])
            
            # Add example with action menu if it exists
            if (self.base_path / "example_test_case_with_menu.txt").exists():
                parts.extend(["\n\n", "## CRITICAL: Example Response with Action Menu\n\n"])
                parts.append(self._load_prompt("example_test_case_with_menu.txt"))
        
        # Always add action menu reminder
        if (self.base_path / "3_test_case_actions.txt").exists():
            parts.extend(["\n\n", "## CRITICAL REMINDER: Always Include Action Menu\n\n"])
            parts.append(self._load_prompt("3_test_case_actions.txt"))
            parts.append("\n\nREMEMBER: You MUST include the action menu after EVERY test case. NEVER end without it!")
        
        return "".join(parts)