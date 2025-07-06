import os
import re
import logging
from typing import Dict, Any, List, Optional
from anthropic import Anthropic

from services.agents.models import MedicalSpecialty, SpecialistTask, SpecialistResult
from services.agents.specialist.specialist_prompts import SpecialistPrompts
from utils.anthropic_client import AnthropicStreamingClient
from tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

class SpecialistAgent:
    """Medical specialist agent that performs focused analysis"""
    
    def __init__(
        self,
        anthropic_client: Optional[Anthropic] = None,
        tool_registry: Optional[ToolRegistry] = None,
        model: Optional[str] = None,
        max_tokens: int = 4000
    ):
        self.client = anthropic_client or Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.tool_registry = tool_registry or ToolRegistry()
        self.model = model or os.getenv("SPECIALIST_MODEL", "claude-3-5-sonnet-20241022")
        self.max_tokens = max_tokens
        self.prompts = SpecialistPrompts()
        self.streaming_client = AnthropicStreamingClient(self.client)
    
    async def execute_task(self, task: SpecialistTask) -> SpecialistResult:
        """Execute a specialist task and return structured results"""
        
        logger.info(f"Specialist {task.specialist.value} executing task: {task.objective}")
        
        # Get system prompt for this specialty
        system_prompt = self.prompts.get_system_prompt(task.specialist.value)
        
        # Get task execution prompt
        task_prompt = self.prompts.get_task_execution_prompt(
            objective=task.objective,
            context=task.context,
            expected_output=task.expected_output,
            max_tool_calls=task.max_tool_calls
        )
        
        # Get specialist tools (only execute_health_query_v2)
        specialist_tools = [
            tool for tool in self.tool_registry.get_tool_definitions()
            if tool["name"] == "execute_health_query_v2"
        ]
        
        # Initial message
        messages = [{"role": "user", "content": task_prompt}]
        
        # Execute task with tool usage
        tool_calls_made = 0
        findings_data = {}
        conversation_messages = []
        
        while tool_calls_made < task.max_tool_calls:
            response = self.streaming_client.create_message_with_retry(
                model=self.model,
                system=system_prompt,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=0.0,
                tools=specialist_tools,
                tool_choice={"type": "auto"}
            )
            
            # Check if tools were used
            tool_used = False
            response_content = []
            tool_results = []
            
            for content in response.content:
                if hasattr(content, 'type') and content.type == 'tool_use':
                    tool_used = True
                    tool_name = content.name
                    tool_input = content.input
                    
                    logger.info(f"{task.specialist.value} executing tool: {tool_name}")
                    tool_calls_made += 1
                    
                    try:
                        result = await self.tool_registry.execute_tool(tool_name, tool_input)
                        
                        # Store findings data (keep top 10 results)
                        if isinstance(result, dict) and "results" in result:
                            query_key = f"query_{tool_calls_made}"
                            findings_data[query_key] = {
                                "query": tool_input.get("query", ""),
                                "result_count": result.get("result_count", 0),
                                "results": result.get("results", [])[:10]  # Keep top 10
                            }
                        
                        response_content.append({
                            "type": "tool_use",
                            "id": content.id,
                            "name": tool_name,
                            "input": tool_input
                        })
                        
                        # Store tool result for user message
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": str(result)
                        })
                        
                    except Exception as e:
                        logger.error(f"Tool execution failed: {str(e)}")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": f"Error: {str(e)}"
                        })
                else:
                    # Regular text content
                    if hasattr(content, 'text'):
                        response_content.append({
                            "type": "text",
                            "text": content.text
                        })
            
            # Add assistant message
            messages.append({
                "role": "assistant",
                "content": response_content
            })
            
            # If tools were used, add tool results in user message
            if tool_used and tool_results:
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
            
            # If no tools were used, break the loop
            if not tool_used:
                break
            
            # Add user message to continue if we haven't reached the limit
            if tool_calls_made < task.max_tool_calls:
                messages.append({
                    "role": "user",
                    "content": "Continue with your investigation if more data is needed."
                })
        
        # Get final analysis
        messages.append({
            "role": "user",
            "content": self.prompts.get_final_analysis_prompt()
        })
        
        final_response = self.streaming_client.create_message_with_retry(
            model=self.model,
            system=system_prompt,
            messages=messages,
            max_tokens=2000,
            temperature=0.0
        )
        
        # Parse structured response
        response_text = final_response.content[0].text
        
        findings = self._extract_section(response_text, "findings")
        recommendations = self._extract_list_section(response_text, "recommendations")
        concerns = self._extract_list_section(response_text, "concerns")
        confidence = self._extract_confidence(response_text)
        
        # Create result
        result = SpecialistResult(
            specialist=task.specialist,
            findings=findings,
            recommendations=recommendations,
            concerns=concerns,
            data_points=findings_data,
            tool_calls_made=tool_calls_made,
            confidence_level=confidence
        )
        
        logger.info(f"{task.specialist.value} completed analysis - Tool calls: {tool_calls_made}, Confidence: {confidence}")
        
        return result
    
    def _extract_section(self, text: str, section: str) -> str:
        """Extract a section from XML-style tags"""
        pattern = f'<{section}>(.*?)</{section}>'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_list_section(self, text: str, section: str) -> List[str]:
        """Extract a list section from XML-style tags"""
        content = self._extract_section(text, section)
        if not content:
            return []
        
        # Split by lines and clean up
        items = []
        for line in content.split('\n'):
            line = line.strip()
            # Remove bullet points or dashes
            if line.startswith('-'):
                line = line[1:].strip()
            elif line.startswith('•'):
                line = line[1:].strip()
            elif re.match(r'^\d+\.', line):
                # Remove numbering
                line = re.sub(r'^\d+\.\s*', '', line)
            
            if line:
                items.append(line)
        
        return items
    
    def _extract_confidence(self, text: str) -> float:
        """Extract confidence level from response"""
        content = self._extract_section(text, "confidence")
        if content:
            try:
                # Try to extract a float
                import re
                match = re.search(r'(\d*\.?\d+)', content)
                if match:
                    confidence = float(match.group(1))
                    # Ensure it's between 0 and 1
                    return max(0.0, min(1.0, confidence))
            except:
                pass
        
        # Default confidence
        return 0.75