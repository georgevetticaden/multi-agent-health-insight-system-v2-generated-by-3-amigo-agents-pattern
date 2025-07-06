import os
import re
import json
import logging
from typing import Dict, Any, List, Tuple, Optional
from anthropic import Anthropic

from services.agents.models import QueryComplexity, SpecialistTask, MedicalSpecialty
from services.agents.cmo.cmo_prompts import CMOPrompts
from utils.anthropic_client import AnthropicStreamingClient
from tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

class CMOAgentSimple:
    """Simplified CMO agent that avoids tool call issues"""
    
    def __init__(
        self,
        anthropic_client: Optional[Anthropic] = None,
        tool_registry: Optional[ToolRegistry] = None,
        model: Optional[str] = None,
        max_tokens_analysis: int = 4000,
        max_tokens_planning: int = 6000,
        default_max_tool_calls: int = 5
    ):
        self.client = anthropic_client or Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.tool_registry = tool_registry or ToolRegistry()
        self.model = model or os.getenv("CMO_MODEL", "claude-3-5-sonnet-20241022")
        self.max_tokens_analysis = max_tokens_analysis
        self.max_tokens_planning = max_tokens_planning
        self.default_max_tool_calls = default_max_tool_calls
        self.prompts = CMOPrompts()
        self.streaming_client = AnthropicStreamingClient(self.client)
        
    async def analyze_query_simple(self, query: str) -> Tuple[QueryComplexity, str, Dict[str, Any]]:
        """
        Simplified analysis without tool calls to avoid API errors
        """
        logger.info("="*60)
        logger.info("CMO SIMPLE ANALYSIS START")
        logger.info(f"Query: {query[:100]}...")
        logger.info("="*60)
        
        # Create a simple analysis prompt without tools
        analysis_prompt = f"""As the Chief Medical Officer, analyze this health query and determine:

1. Query Complexity: Classify as one of:
   - simple: Basic information lookup or single metric
   - standard: Multiple metrics or moderate analysis
   - complex: Correlation analysis or multi-year trends
   - comprehensive: Multiple conditions with deep analysis

2. Analysis Approach: Brief description of how to analyze this query

3. Data Requirements: What types of health data would be needed

Query: {query}

Provide your analysis in this format:
<complexity>simple/standard/complex/comprehensive</complexity>
<approach>Your approach description</approach>
<data_needs>Required data types</data_needs>"""

        messages = [{"role": "user", "content": analysis_prompt}]
        
        # Get analysis without tools
        response = self.streaming_client.create_message_with_retry(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens_analysis,
            temperature=0.0
        )
        
        response_text = response.content[0].text
        logger.info(f"CMO Analysis Response: {response_text[:200]}...")
        
        # Parse complexity
        try:
            complexity_match = re.search(r'<complexity>(.*?)</complexity>', response_text, re.DOTALL)
            if complexity_match:
                complexity_str = complexity_match.group(1).strip().lower()
                complexity = QueryComplexity(complexity_str)
            else:
                logger.warning("No complexity found in response, defaulting to standard")
                complexity = QueryComplexity.STANDARD
        except Exception as e:
            logger.error(f"Error parsing complexity: {e}")
            complexity = QueryComplexity.STANDARD
            
        # Parse approach
        try:
            approach_match = re.search(r'<approach>(.*?)</approach>', response_text, re.DOTALL)
            approach = approach_match.group(1).strip() if approach_match else "Standard health data analysis"
        except Exception as e:
            logger.error(f"Error parsing approach: {e}")
            approach = "Standard health data analysis"
            
        # Create mock initial data
        initial_data = {
            "tool_calls_made": 0,
            "data_available": True,
            "summary": "Health data available for analysis"
        }
        
        logger.info(f"CMO Simple Analysis Complete - Complexity: {complexity.value}")
        
        return complexity, approach, initial_data
        
    async def create_specialist_tasks(
        self, 
        query: str,
        complexity: QueryComplexity,
        approach: str,
        initial_data: Dict[str, Any]
    ) -> List[SpecialistTask]:
        """Create tasks for specialists - same as original"""
        
        # Determine number of specialists based on complexity
        num_specialists_map = {
            QueryComplexity.SIMPLE: 1,
            QueryComplexity.STANDARD: 3,
            QueryComplexity.COMPLEX: 5,
            QueryComplexity.COMPREHENSIVE: 8
        }
        num_specialists = num_specialists_map.get(complexity, 3)
        
        # Get tool call limits based on complexity
        tool_limits = {
            QueryComplexity.SIMPLE: 3,
            QueryComplexity.STANDARD: 5,
            QueryComplexity.COMPLEX: 7,
            QueryComplexity.COMPREHENSIVE: 10
        }
        tool_limit = tool_limits.get(complexity, self.default_max_tool_calls)
        
        # Use the same implementation as CMOAgent
        task_prompt = self.prompts.get_task_creation_prompt(
            query, 
            complexity.value.upper(), 
            approach, 
            initial_data.get("summary", "No initial data gathered"),
            num_specialists,
            tool_limit
        )
        
        messages = [{"role": "user", "content": task_prompt}]
        
        response = self.streaming_client.create_message_with_retry(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens_planning,
            temperature=0.1
        )
        
        response_text = response.content[0].text
        logger.info(f"Task creation response length: {len(response_text)}")
        logger.debug(f"Task creation response preview: {response_text[:500]}...")
        
        # Parse tasks using the same logic as CMOAgent
        tasks = []
        
        # Get tool call limits based on complexity
        tool_limits = {
            QueryComplexity.SIMPLE: 3,
            QueryComplexity.STANDARD: 5,
            QueryComplexity.COMPLEX: 7,
            QueryComplexity.COMPREHENSIVE: 10
        }
        max_tool_calls = tool_limits.get(complexity, self.default_max_tool_calls)
        
        # Check if we have a tasks wrapper
        tasks_match = re.search(r'<tasks>(.*?)</tasks>', response_text, re.IGNORECASE | re.DOTALL)
        if tasks_match:
            # Extract the content within tasks tags
            task_text = tasks_match.group(1)
            logger.info("Found tasks wrapper in XML response")
        else:
            logger.warning("No tasks wrapper found, parsing raw XML")
            task_text = response_text
        
        # Find all task blocks
        task_pattern = re.compile(
            r'<task>(.*?)</task>', 
            re.IGNORECASE | re.DOTALL
        )
        
        task_matches = list(task_pattern.finditer(task_text))
        logger.info(f"Found {len(task_matches)} task blocks in XML")
        
        for i, task_match in enumerate(task_matches):
            task_xml = task_match.group(1)
            
            # Extract task components
            specialist = self._extract_xml_field(task_xml, "specialist")
            objective = self._extract_xml_field(task_xml, "objective")
            context = self._extract_xml_field(task_xml, "context")
            expected_output = self._extract_xml_field(task_xml, "expected_output")
            priority = int(self._extract_xml_field(task_xml, "priority", "1"))
            
            logger.debug(f"Task {i+1}: specialist={specialist}, objective={objective[:50]}...")
            
            # Map specialist names to enum
            specialist_enum = self._map_specialist_to_enum(specialist)
            
            if specialist_enum and objective:
                task = SpecialistTask(
                    specialist=specialist_enum,
                    objective=objective,
                    context=context,
                    expected_output=expected_output,
                    priority=priority,
                    max_tool_calls=max_tool_calls
                )
                tasks.append(task)
                logger.info(f"Successfully parsed task for {specialist_enum.value}")
            else:
                logger.warning(f"Skipping task - invalid specialist ({specialist}) or missing objective")
        
        # Sort by priority
        tasks.sort(key=lambda t: t.priority)
        
        logger.info(f"Created {len(tasks)} specialist tasks")
        return tasks
    
    def _extract_xml_field(self, xml: str, field: str, default: str = "") -> str:
        """Extract a field from XML text"""
        pattern = f'<{field}>(.*?)</{field}>'
        match = re.search(pattern, xml, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else default
    
    def _map_specialist_to_enum(self, specialist_name: str) -> Optional[MedicalSpecialty]:
        """Map specialist name string to enum"""
        mapping = {
            "general_practice": MedicalSpecialty.GENERAL_PRACTICE,
            "internal_medicine": MedicalSpecialty.GENERAL_PRACTICE,  # Common mistake
            "primary_care": MedicalSpecialty.GENERAL_PRACTICE,      # Common mistake
            "cardiology": MedicalSpecialty.CARDIOLOGY,
            "endocrinology": MedicalSpecialty.ENDOCRINOLOGY,
            "laboratory_medicine": MedicalSpecialty.LABORATORY_MEDICINE,
            "lab_medicine": MedicalSpecialty.LABORATORY_MEDICINE,    # Common mistake
            "pharmacy": MedicalSpecialty.PHARMACY,
            "nutrition": MedicalSpecialty.NUTRITION,
            "preventive_medicine": MedicalSpecialty.PREVENTIVE_MEDICINE,
            "data_analysis": MedicalSpecialty.DATA_ANALYSIS
        }
        
        clean_name = specialist_name.lower().strip()
        if clean_name not in mapping:
            logger.warning(f"Unknown specialist: {specialist_name}")
            return None
            
        return mapping[clean_name]