import os
import re
import json
import time
import logging
from typing import Dict, Any, List, Tuple, Optional, TYPE_CHECKING, Union
from anthropic import Anthropic

from services.agents.models import QueryComplexity, SpecialistTask, MedicalSpecialty
from services.agents.cmo.cmo_prompts import CMOPrompts
from utils.anthropic_client import AnthropicStreamingClient
from tools.tool_registry import ToolRegistry
from config.model_config import get_safe_max_tokens, validate_model_config

# Import tracing components
try:
    from services.tracing import get_trace_collector, TraceEventType
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False

# Avoid circular import
if TYPE_CHECKING:
    from services.agents.metadata.core import AgentMetadata
    from evaluation.core import AgentEvaluationMetadata

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
        max_tokens_synthesis: int = 16384,
        default_max_tool_calls: int = 5,
        enable_tracing: bool = True
    ):
        # Initialize base client
        self.client = anthropic_client
        if self.client is None:
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            
        self.tool_registry = tool_registry or ToolRegistry()
        self.model = model or os.getenv("CMO_MODEL", "claude-3-5-sonnet-20241022")
        
        # Validate model and adjust token limits
        validate_model_config(self.model)
        self.max_tokens_analysis = get_safe_max_tokens(self.model, max_tokens_analysis)
        self.max_tokens_planning = get_safe_max_tokens(self.model, max_tokens_planning)
        self.max_tokens_synthesis = get_safe_max_tokens(self.model, max_tokens_synthesis)
        self.default_max_tool_calls = default_max_tool_calls
        self.prompts = CMOPrompts()
        
        # Log the adjusted token limits
        logger.info(f"CMO Agent initialized with model: {self.model}")
        logger.info(f"Adjusted max_tokens - analysis: {self.max_tokens_analysis}, planning: {self.max_tokens_planning}, synthesis: {self.max_tokens_synthesis}")
        
        # Use the same client for streaming (traced or not)
        self.streaming_client = AnthropicStreamingClient(self.client)
        
        # Set up tracing collector if available
        self.trace_collector = get_trace_collector() if TRACING_AVAILABLE else None
        
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
        
        # Debug: Check if we have a trace context
        if TRACING_AVAILABLE:
            from services.tracing import TraceContextManager
            context = TraceContextManager.get_context()
            if context:
                logger.debug(f"CMO: Trace context available: {context.trace_id}")
            else:
                logger.warning("CMO: No trace context found when making LLM call")
        
        # Set tracing metadata for this call
        self.streaming_client.set_metadata(
            agent_type="cmo",
            stage="query_analysis",
            prompt_file="1_gather_data_assess_complexity.txt"
        )
        
        # Also update the trace context if available
        if TRACING_AVAILABLE and self.trace_collector:
            self.trace_collector.update_context(
                current_agent="cmo",
                current_stage="query_analysis",
                current_prompt_file="1_gather_data_assess_complexity.txt"
            )
        
        try:
            response = await self.streaming_client.create_message_with_retry_async(
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
                    # Track start time for duration
                    tool_start_time = time.time()
                    
                    # Execute the tool (tool invocation will be auto-traced by streaming client)
                    result = await self.tool_registry.execute_tool(tool_name, tool_input)
                    
                    # Calculate duration
                    tool_duration_ms = (time.time() - tool_start_time) * 1000
                    
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
                    
                    # Trace tool result if tracing is enabled
                    if TRACING_AVAILABLE and self.trace_collector:
                        # Prepare result data - include actual results but limit size
                        result_data_for_trace = {}
                        if isinstance(result, dict):
                            # Include key fields from result
                            result_data_for_trace = {
                                "query_successful": result.get("query_successful", False),
                                "result_count": result.get("result_count", 0),
                                "results": result.get("results", [])[:5],  # Limit to first 5 results
                                "query": result.get("query", ""),
                                "error": result.get("error")
                            }
                        
                        await self.trace_collector.add_event(
                            event_type=TraceEventType.TOOL_RESULT,
                            agent_type="cmo",
                            stage="query_analysis",
                            data={
                                "tool_name": tool_name,
                                "tool_id": tool_id,
                                "success": True,
                                "result_summary": initial_data.get("summary", ""),
                                "result_data": result_data_for_trace,
                                "duration_ms": tool_duration_ms,
                                "linked_tool_invocation_id": tool_id  # Link to invocation
                            },
                            duration_ms=tool_duration_ms,
                            metadata={
                                "tool_input": tool_input,
                                "tool_output": result  # Store complete output
                            }
                        )
                    
                    tool_results.append({
                        "tool_id": tool_id,
                        "tool": tool_name,
                        "input": tool_input,
                        "output": result
                    })
                    
                except Exception as e:
                    logger.error(f"Tool execution failed: {str(e)}")
                    initial_data["summary"] = f"Tool execution failed: {str(e)}"
                    
                    # Trace tool error if tracing is enabled
                    if TRACING_AVAILABLE and self.trace_collector:
                        await self.trace_collector.add_event(
                            event_type=TraceEventType.TOOL_RESULT,
                            agent_type="cmo",
                            stage="query_analysis",
                            data={
                                "tool_name": tool_name,
                                "tool_id": tool_id,
                                "success": False,
                                "error": str(e),
                                "error_type": type(e).__name__
                            },
                            metadata={"tool_input": tool_input}
                        )
                    
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
            
            # Update metadata for assessment response (still part of initial gathering)
            self.streaming_client.set_metadata(
                agent_type="cmo",
                stage="query_analysis",
                prompt_file="1_gather_data_assess_complexity.txt",
                prompt_phase="assessment_after_tool"
            )
            
            # Get the final response with initial assessment
            assessment_response = await self.streaming_client.create_message_with_retry_async(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.0
            )
            
            # Extract complexity from initial assessment
            assessment_text = assessment_response.content[0].text
            complexity = self._extract_complexity(assessment_text)
            # Update initial_data with key findings (don't overwrite)
            key_findings_data = self._extract_key_findings(assessment_text)
            initial_data.update(key_findings_data)
            
            # Add the assessment to messages
            messages.append({
                "role": "assistant",
                "content": assessment_text
            })
        else:
            # No tool calls, just add the assistant response
            messages.append({
                "role": "assistant",
                "content": response.content[0].text if response.content else ""
            })
            # Extract complexity from the response
            complexity = self._extract_complexity(response.content[0].text)
            # Update initial_data with key findings (don't overwrite)
            key_findings_data = self._extract_key_findings(response.content[0].text)
            initial_data.update(key_findings_data)
        
        # Now ask for the analysis summary with the complexity already determined
        summary_prompt = self.prompts.get_analysis_summary_prompt().replace("{{COMPLEXITY}}", complexity.value)
        messages.append({
            "role": "user",
            "content": summary_prompt
        })
        
        # Update metadata for analytical approach
        self.streaming_client.set_metadata(
            agent_type="cmo",
            stage="query_analysis",
            prompt_file="2_define_analytical_approach.txt"
        )
        
        summary_response = await self.streaming_client.create_message_with_retry_async(
            model=self.model,
            messages=messages,
            max_tokens=1000,
            temperature=0.0
        )
        
        # Parse approach from response (complexity already extracted from step 1)
        response_text = summary_response.content[0].text
        approach = self._extract_approach(response_text)
        
        logger.info(f"Query analysis complete - Complexity: {complexity.value}, Tool calls: {initial_data['tool_calls_made']}")
        
        # Add stage end marker
        if TRACING_AVAILABLE and self.trace_collector:
            await self.trace_collector.add_event(
                event_type=TraceEventType.STAGE_END,
                agent_type="cmo",
                stage="query_analysis",
                data={
                    "complexity": complexity.value,
                    "approach": approach,
                    "tool_calls_made": initial_data['tool_calls_made']
                }
            )
        
        return complexity, approach, initial_data
    
    async def create_specialist_tasks(
        self,
        query: str,
        complexity: QueryComplexity,
        approach: str,
        initial_data: Dict[str, Any]
    ) -> List[SpecialistTask]:
        """Create specific tasks for specialists based on analysis"""
        
        # Add stage start marker
        if TRACING_AVAILABLE and self.trace_collector:
            await self.trace_collector.add_event(
                event_type=TraceEventType.STAGE_START,
                agent_type="cmo",
                stage="task_creation",
                data={
                    "complexity": complexity.value,
                    "initial_data_summary": initial_data.get("summary", "")
                }
            )
        
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
        
        # Set tracing metadata for task creation
        self.streaming_client.set_metadata(
            agent_type="cmo",
            stage="task_creation",
            prompt_file="3_assign_specialist_tasks.txt"
        )
        
        # Also update the trace context if available
        if TRACING_AVAILABLE and self.trace_collector:
            self.trace_collector.update_context(
                current_agent="cmo",
                current_stage="task_creation",
                current_prompt_file="3_assign_specialist_tasks.txt"
            )
        
        response = await self.streaming_client.create_message_with_retry_async(
            model=self.model,
            messages=[{"role": "user", "content": task_prompt}],
            max_tokens=self.max_tokens_planning,
            temperature=0.0
        )
        
        tasks_text = response.content[0].text
        
        # Parse tasks from XML
        tasks = self._parse_tasks_from_xml(tasks_text, complexity)
        
        logger.info(f"Created {len(tasks)} specialist tasks")
        
        # Add stage end marker
        if TRACING_AVAILABLE and self.trace_collector:
            await self.trace_collector.add_event(
                event_type=TraceEventType.STAGE_END,
                agent_type="cmo",
                stage="task_creation",
                data={
                    "task_count": len(tasks),
                    "specialists": [task.specialist.value for task in tasks]
                }
            )
        
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
    
    def _extract_key_findings(self, text: str) -> Dict[str, Any]:
        """Extract key findings from initial assessment"""
        match = re.search(r'<key_findings>(.*?)</key_findings>', text, re.IGNORECASE | re.DOTALL)
        key_findings = match.group(1).strip() if match else ""
        
        return {
            "summary": key_findings
        }
    
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
            "cardiology": MedicalSpecialty.CARDIOLOGY,
            "endocrinology": MedicalSpecialty.ENDOCRINOLOGY,
            "laboratory_medicine": MedicalSpecialty.LABORATORY_MEDICINE,
            "lab_medicine": MedicalSpecialty.LABORATORY_MEDICINE,    # Common mistake
            "pharmacy": MedicalSpecialty.PHARMACY,
            "nutrition": MedicalSpecialty.NUTRITION,
            "preventive_medicine": MedicalSpecialty.PREVENTIVE_MEDICINE
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
    
    async def synthesize_findings(
        self, 
        query: str, 
        specialist_findings: str,
        stream: bool = False
    ) -> Any:
        """
        Synthesize specialist findings into a comprehensive response
        
        Args:
            query: Original patient query
            specialist_findings: Formatted findings from all specialists
            stream: Whether to stream the response
            
        Returns:
            Either a complete synthesis string or a streaming response
        """
        # Get synthesis prompt
        synthesis_prompt = self.prompts.get_synthesis_prompt(query, specialist_findings)
        
        # Create message
        messages = [{"role": "user", "content": synthesis_prompt}]
        
        # Set tracing metadata for synthesis
        self.streaming_client.set_metadata(
            agent_type="cmo",
            stage="synthesis",
            prompt_file="4_synthesis.txt"
        )
        
        # Also update the trace context if available
        if TRACING_AVAILABLE and self.trace_collector:
            self.trace_collector.update_context(
                current_agent="cmo",
                current_stage="synthesis",
                current_prompt_file="4_synthesis.txt"
            )
        
        if stream:
            # Return streaming response for the orchestrator to handle
            return await self.streaming_client.create_message_with_retry_async(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens_synthesis,
                temperature=0.3,
                stream=True
            )
        else:
            # Return complete synthesis
            response = await self.streaming_client.create_message_with_retry_async(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens_synthesis,
                temperature=0.3,
                stream=False
            )
            return response.content[0].text
    
    @classmethod
    def get_metadata(cls) -> 'AgentMetadata':
        """
        Get core metadata for this agent.
        
        Returns basic agent information without evaluation-specific concepts.
        """
        from services.agents.metadata.core import AgentMetadata, PromptMetadata
        
        # Get prompt metadata from CMOPrompts class
        prompts_metadata = CMOPrompts.get_prompt_metadata()
        
        # Convert to basic PromptMetadata (without evaluation dimensions)
        basic_prompts = [
            PromptMetadata(
                filename=p.filename,
                description=p.description,
                purpose=p.purpose,
                version=p.version
            )
            for p in prompts_metadata
        ]
        
        return AgentMetadata(
            agent_type="cmo",
            agent_class="services.agents.cmo.CMOAgent",
            description="Chief Medical Officer agent orchestrating multi-agent health analysis",
            prompts=basic_prompts,
            capabilities=["orchestration", "complexity_assessment", "task_delegation"],
            supported_tools=["execute_health_query_v2"],
            config={
                "max_specialists": 8,
                "complexity_levels": ["SIMPLE", "STANDARD", "COMPLEX", "COMPREHENSIVE"],
                "tool_limit_per_task": 5,
                "supported_specialists": [s.value for s in MedicalSpecialty]
            }
        )
    
    @classmethod
    def get_evaluation_metadata(cls) -> 'AgentEvaluationMetadata':
        """
        Get evaluation metadata for this agent.
        
        This method defines the evaluation criteria, dimensions, and prompts
        that are used to evaluate the CMO agent's performance.
        """
        # Import here to avoid circular dependency
        from evaluation.core import (
            AgentEvaluationMetadata,
            EvaluationCriteria,
            QualityComponent,
            dimension_registry
        )
        from evaluation.core.dimensions import EvaluationMethod
        from evaluation.agents import CMO_DIMENSIONS
        
        # Get core agent metadata
        agent_metadata = cls.get_metadata()
        
        # Define evaluation criteria
        evaluation_criteria = [
            EvaluationCriteria(
                dimension=CMO_DIMENSIONS["complexity_classification"],
                description="Accuracy in classifying query complexity (SIMPLE/STANDARD/COMPLEX/COMPREHENSIVE)",
                target_score=0.90,
                weight=0.20,  # 20% of total evaluation
                evaluation_method=EvaluationMethod.DETERMINISTIC,
                evaluation_description="Binary accuracy against expert-labeled complexity"
            ),
            EvaluationCriteria(
                dimension=CMO_DIMENSIONS["specialty_selection"],
                description="Precision in selecting appropriate medical specialists",
                target_score=0.85,
                weight=0.25,  # 25% of total evaluation
                evaluation_method=EvaluationMethod.HYBRID,
                evaluation_description="Weighted combination of deterministic precision and LLM judge rationale"
            ),
            EvaluationCriteria(
                dimension=dimension_registry.get("analysis_quality"),  # Common dimension
                description="Comprehensiveness and quality of medical analysis orchestration",
                target_score=0.80,
                weight=0.25,  # 25% of total evaluation
                evaluation_method=EvaluationMethod.HYBRID,
                evaluation_description="Weighted score across deterministic and LLM judge components"
            ),
            EvaluationCriteria(
                dimension=dimension_registry.get("tool_usage"),  # Common dimension
                description="Effectiveness of health data tool usage",
                target_score=0.90,
                weight=0.15,  # 15% of total evaluation
                evaluation_method=EvaluationMethod.HYBRID,
                evaluation_description="Combination of success rate and relevance scoring"
            ),
            EvaluationCriteria(
                dimension=dimension_registry.get("response_structure"),  # Common dimension
                description="Compliance with expected XML response format",
                target_score=0.95,
                weight=0.15,  # 15% of total evaluation
                evaluation_method=EvaluationMethod.HYBRID,
                evaluation_description="XML validation and required field presence"
            )
        ]
        
        # Define quality components for complex dimensions
        quality_components = {
            dimension_registry.get("analysis_quality"): [
                QualityComponent(
                    name="data_gathering",
                    description="Appropriate tool calls to gather health data",
                    weight=0.20,
                    evaluation_method=EvaluationMethod.DETERMINISTIC
                ),
                QualityComponent(
                    name="context_awareness",
                    description="Consideration of temporal context and patient history",
                    weight=0.15,
                    evaluation_method=EvaluationMethod.LLM_JUDGE
                ),
                QualityComponent(
                    name="comprehensive_approach",
                    description="Coverage of all relevant medical concepts",
                    weight=0.25,
                    evaluation_method=EvaluationMethod.LLM_JUDGE
                ),
                QualityComponent(
                    name="concern_identification",
                    description="Identification of health concerns and risks",
                    weight=0.20,
                    evaluation_method=EvaluationMethod.LLM_JUDGE
                )
            ],
            # Complexity classification is deterministic - no components needed
            CMO_DIMENSIONS["specialty_selection"]: [
                QualityComponent(
                    name="specialist_precision",
                    description="Selected specialists match expected set",
                    weight=0.6,
                    evaluation_method=EvaluationMethod.DETERMINISTIC
                ),
                QualityComponent(
                    name="specialist_rationale",
                    description="Clear reasoning for specialist choices",
                    weight=0.4,
                    evaluation_method=EvaluationMethod.LLM_JUDGE
                )
            ],
            dimension_registry.get("tool_usage"): [
                QualityComponent(
                    name="tool_success_rate",
                    description="Percentage of successful tool calls",
                    weight=0.5,
                    evaluation_method=EvaluationMethod.DETERMINISTIC
                )
            ],
            dimension_registry.get("response_structure"): [
                QualityComponent(
                    name="xml_validity",
                    description="Valid XML structure in responses",
                    weight=0.7,
                    evaluation_method=EvaluationMethod.DETERMINISTIC
                ),
                QualityComponent(
                    name="required_fields",
                    description="Presence of all required XML fields",
                    weight=0.3,
                    evaluation_method=EvaluationMethod.DETERMINISTIC
                )
            ]
        }
        
        # Get core agent metadata
        agent_metadata = cls.get_metadata()
        
        # Create the complete evaluation metadata
        return AgentEvaluationMetadata(
            agent_metadata=agent_metadata,
            evaluation_criteria=evaluation_criteria,
            quality_components=quality_components
        )