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

class CMOAgent:
    """Chief Medical Officer agent that orchestrates health analysis"""
    
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
        
    async def analyze_query_with_tools(self, query: str) -> Tuple[QueryComplexity, str, Dict[str, Any]]:
        """
        Analyze query complexity using tools for initial data gathering
        
        Returns:
            - complexity: QueryComplexity enum
            - approach: String describing the analysis approach
            - initial_data: Dictionary with tool results summary
        """
        logger.info(f"="*60)
        logger.info(f"CMO ANALYSIS START")
        logger.info(f"Query: {query[:100]}...")
        logger.info(f"Max tokens: {self.max_tokens_analysis}")
        logger.info(f"Model: {self.model}")
        logger.info(f"="*60)
        
        # Step 1: Initial analysis with tool usage
        initial_prompt = self.prompts.get_initial_analysis_prompt(query)
        
        messages = [{"role": "user", "content": initial_prompt}]
        
        # Get CMO tools (limited to execute_health_query_v2)
        cmo_tools = [
            tool for tool in self.tool_registry.get_tool_definitions()
            if tool["name"] == "execute_health_query_v2"
        ]
        
        logger.info(f"Calling Anthropic API with {len(cmo_tools)} tools available")
        logger.info(f"Messages in conversation: {len(messages)}")
        
        try:
            response = self.streaming_client.create_message_with_retry(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens_analysis,
                temperature=0.0,
                tools=cmo_tools,
                tool_choice={"type": "auto"}
            )
            logger.info("Initial API call successful")
        except Exception as e:
            logger.error(f"API call failed: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            raise
        
        # Process response and handle tool calls
        tool_results = []
        tool_use_blocks = []
        initial_data = {
            "tool_calls_made": 0,
            "data_available": False,
            "summary": ""
        }
        
        logger.info(f"Processing response with {len(response.content)} content blocks")
        
        for i, content in enumerate(response.content):
            logger.info(f"Content block {i}: type={getattr(content, 'type', 'unknown')}")
            
            if hasattr(content, 'type') and content.type == 'tool_use':
                tool_name = content.name
                tool_input = content.input
                tool_id = content.id
                
                logger.info(f"CMO executing tool: {tool_name}")
                initial_data["tool_calls_made"] += 1
                
                # Store the tool use block
                tool_use_blocks.append({
                    "id": tool_id,
                    "name": tool_name,
                    "input": tool_input
                })
                
                try:
                    result = await self.tool_registry.execute_tool(tool_name, tool_input)
                    
                    # Extract summary information
                    if isinstance(result, dict):
                        initial_data["data_available"] = result.get("query_successful", False)
                        initial_data["result_count"] = result.get("result_count", 0)
                        initial_data["query"] = tool_input.get("query", "")
                        
                        # Create summary for task creation
                        if initial_data["data_available"]:
                            initial_data["summary"] = f"Found {initial_data['result_count']} results for: {initial_data['query']}"
                        else:
                            initial_data["summary"] = "No data found for the query"
                    
                    tool_results.append({
                        "tool_id": tool_id,
                        "tool": tool_name,
                        "input": tool_input,
                        "output": result
                    })
                    
                except Exception as e:
                    logger.error(f"Tool execution failed: {str(e)}")
                    initial_data["summary"] = f"Tool execution failed: {str(e)}"
                    tool_results.append({
                        "tool_id": tool_id,
                        "tool": tool_name,
                        "input": tool_input,
                        "output": {"error": str(e)}
                    })
        
        # Step 2: If we had tool calls, we need to handle them properly
        if tool_results:
            logger.info(f"Processing {len(tool_results)} tool results")
            
            # Build the assistant message content
            assistant_content = []
            
            # Add any text content first
            for content in response.content:
                if hasattr(content, 'type') and content.type == 'text' and content.text:
                    assistant_content.append({"type": "text", "text": content.text})
            
            # Add tool use blocks
            for content in response.content:
                if hasattr(content, 'type') and content.type == 'tool_use':
                    assistant_content.append({
                        "type": "tool_use",
                        "id": content.id,
                        "name": content.name,
                        "input": content.input
                    })
            
            # Add assistant message with tool uses
            messages.append({
                "role": "assistant",
                "content": assistant_content
            })
            
            # Add tool results in a single user message
            tool_result_content = []
            for result in tool_results:
                tool_result_content.append({
                    "type": "tool_result",
                    "tool_use_id": result['tool_id'],
                    "content": json.dumps(result['output'])  # Use JSON for structured data
                })
            
            messages.append({
                "role": "user",
                "content": tool_result_content
            })
            
            logger.info(f"Added tool results to conversation. Total messages: {len(messages)}")
        else:
            # No tool calls, just add the assistant response
            messages.append({
                "role": "assistant",
                "content": response.content[0].text if response.content else ""
            })
        
        # Now ask for the analysis summary
        messages.append({
            "role": "user",
            "content": self.prompts.get_analysis_summary_prompt()
        })
        
        summary_response = self.streaming_client.create_message_with_retry(
            model=self.model,
            messages=messages,
            max_tokens=1000,
            temperature=0.0
        )
        
        # Parse complexity and approach from response
        response_text = summary_response.content[0].text
        
        complexity = self._extract_complexity(response_text)
        approach = self._extract_approach(response_text)
        
        logger.info(f"Query analysis complete - Complexity: {complexity.value}, Tool calls: {initial_data['tool_calls_made']}")
        
        return complexity, approach, initial_data
    
    def create_specialist_tasks(
        self,
        query: str,
        complexity: QueryComplexity,
        approach: str,
        initial_data: Dict[str, Any]
    ) -> List[SpecialistTask]:
        """Create specific tasks for specialists based on analysis"""
        
        num_specialists = self._get_specialist_count(complexity)
        
        # Get tool call limits based on complexity
        tool_limits = {
            QueryComplexity.SIMPLE: 3,
            QueryComplexity.STANDARD: 5,
            QueryComplexity.COMPLEX: 7,
            QueryComplexity.COMPREHENSIVE: 10
        }
        tool_limit = tool_limits.get(complexity, self.default_max_tool_calls)
        
        # Prepare initial data summary
        initial_data_summary = initial_data.get("summary", "No initial data gathered")
        
        task_prompt = self.prompts.get_task_creation_prompt(
            query=query,
            complexity=complexity.value.upper(),
            approach=approach,
            initial_data=initial_data_summary,
            num_specialists=num_specialists,
            tool_limit=tool_limit
        )
        
        response = self.streaming_client.create_message_with_retry(
            model=self.model,
            messages=[{"role": "user", "content": task_prompt}],
            max_tokens=self.max_tokens_planning,
            temperature=0.0
        )
        
        tasks_text = response.content[0].text
        
        # Parse tasks from XML
        tasks = self._parse_tasks_from_xml(tasks_text, complexity)
        
        logger.info(f"Created {len(tasks)} specialist tasks")
        
        return tasks
    
    def _extract_complexity(self, text: str) -> QueryComplexity:
        """Extract complexity from XML response"""
        match = re.search(r'<complexity>(.*?)</complexity>', text, re.IGNORECASE | re.DOTALL)
        if match:
            complexity_str = match.group(1).strip().lower()
            
            # Map to enum
            if complexity_str == "simple":
                return QueryComplexity.SIMPLE
            elif complexity_str == "standard":
                return QueryComplexity.STANDARD
            elif complexity_str == "complex":
                return QueryComplexity.COMPLEX
            elif complexity_str == "comprehensive":
                return QueryComplexity.COMPREHENSIVE
        
        # Default to STANDARD if not found
        logger.warning("Could not extract complexity, defaulting to STANDARD")
        return QueryComplexity.STANDARD
    
    def _extract_approach(self, text: str) -> str:
        """Extract approach from XML response"""
        match = re.search(r'<approach>(.*?)</approach>', text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return "Standard medical analysis approach"
    
    def _parse_tasks_from_xml(self, xml_text: str, complexity: QueryComplexity) -> List[SpecialistTask]:
        """Parse specialist tasks from XML response"""
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
        tasks_match = re.search(r'<tasks>(.*?)</tasks>', xml_text, re.IGNORECASE | re.DOTALL)
        if tasks_match:
            # Extract the content within tasks tags
            xml_text = tasks_match.group(1)
            logger.info("Found tasks wrapper in XML response")
        else:
            logger.warning("No tasks wrapper found, parsing raw XML")
        
        # Find all task blocks
        task_pattern = re.compile(
            r'<task>(.*?)</task>', 
            re.IGNORECASE | re.DOTALL
        )
        
        task_matches = list(task_pattern.finditer(xml_text))
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
        
        logger.info(f"Successfully parsed {len(tasks)} specialist tasks")
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
    
    def _get_specialist_count(self, complexity: QueryComplexity) -> int:
        """Get expected number of specialists based on complexity"""
        counts = {
            QueryComplexity.SIMPLE: 1,
            QueryComplexity.STANDARD: 3,
            QueryComplexity.COMPLEX: 5,
            QueryComplexity.COMPREHENSIVE: 8
        }
        return counts.get(complexity, 3)