import os
import re
import time
import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING, Union
from anthropic import Anthropic

from services.agents.models import MedicalSpecialty, SpecialistTask, SpecialistResult
from services.agents.specialist.specialist_prompts import SpecialistPrompts
from utils.anthropic_client import AnthropicStreamingClient
from tools.tool_registry import ToolRegistry

# Import tracing components
try:
    from services.tracing import get_trace_collector, TraceEventType
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False

# Avoid circular import
if TYPE_CHECKING:
    from services.agents.metadata.core import AgentMetadata

logger = logging.getLogger(__name__)

class SpecialistAgent:
    """Medical specialist agent that performs focused analysis"""
    
    def __init__(
        self,
        anthropic_client: Optional[Anthropic] = None,
        tool_registry: Optional[ToolRegistry] = None,
        model: Optional[str] = None,
        max_tokens: int = 4000,
        enable_tracing: bool = True
    ):
        # Initialize base client
        self.client = anthropic_client
        if self.client is None:
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            
        self.tool_registry = tool_registry or ToolRegistry()
        self.model = model or os.getenv("SPECIALIST_MODEL", "claude-3-5-sonnet-20241022")
        self.max_tokens = max_tokens
        self.prompts = SpecialistPrompts()
        
        # Use the same client for streaming (traced or not)
        self.streaming_client = AnthropicStreamingClient(self.client)
        
        # Set up tracing collector if available
        self.trace_collector = get_trace_collector() if TRACING_AVAILABLE else None
    
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
        
        # Set tracing metadata for this specialist execution
        if hasattr(self.client, 'set_metadata'):
            self.client.set_metadata(
                agent_type=task.specialist.value,
                stage="specialist_execution",
                prompt_file=f"system_{task.specialist.value}.txt"
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
            # Set tracing metadata for this call
            self.streaming_client.set_metadata(
                agent_type=task.specialist.value,
                stage="analysis",
                prompt_file="specialist_analysis.txt"
            )
            
            # Also update the trace context if available
            if TRACING_AVAILABLE and self.trace_collector:
                self.trace_collector.update_context(
                    current_agent=task.specialist.value,
                    current_stage="analysis",
                    current_prompt_file="specialist_analysis.txt"
                )
            
            response = await self.streaming_client.create_message_with_retry_async(
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
                        # Track start time for duration
                        tool_start_time = time.time()
                        
                        # Execute the tool (tool invocation will be auto-traced by streaming client)
                        result = await self.tool_registry.execute_tool(tool_name, tool_input)
                        
                        # Calculate duration
                        tool_duration_ms = (time.time() - tool_start_time) * 1000
                        
                        # Store findings data (keep top 10 results)
                        result_count = 0
                        if isinstance(result, dict) and "results" in result:
                            query_key = f"query_{tool_calls_made}"
                            result_count = result.get("result_count", 0)
                            findings_data[query_key] = {
                                "query": tool_input.get("query", ""),
                                "result_count": result_count,
                                "results": result.get("results", [])[:10]  # Keep top 10
                            }
                        
                        # Trace tool result if tracing is enabled
                        if TRACING_AVAILABLE and self.trace_collector:
                            # Create result summary
                            if isinstance(result, dict):
                                if result.get("query_successful", False):
                                    result_summary = f"Found {result_count} results for: {tool_input.get('query', '')}"
                                else:
                                    result_summary = "No data found for the query"
                            else:
                                result_summary = f"Tool returned {type(result).__name__}"
                            
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
                                agent_type=task.specialist.value.lower(),
                                stage="analysis",
                                data={
                                    "tool_name": tool_name,
                                    "tool_id": content.id,
                                    "success": True,
                                    "result_summary": result_summary,
                                    "result_data": result_data_for_trace,
                                    "duration_ms": tool_duration_ms,
                                    "linked_tool_invocation_id": content.id  # Link to invocation
                                },
                                duration_ms=tool_duration_ms,
                                metadata={
                                    "tool_input": tool_input,
                                    "specialist": task.specialist.value,
                                    "tool_output": result  # Store complete output
                                }
                            )
                        
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
                        
                        # Trace tool error if tracing is enabled
                        if TRACING_AVAILABLE and self.trace_collector:
                            await self.trace_collector.add_event(
                                event_type=TraceEventType.TOOL_RESULT,
                                agent_type=task.specialist.value.lower(),
                                stage="analysis",
                                data={
                                    "tool_name": tool_name,
                                    "tool_id": content.id,
                                    "success": False,
                                    "error": str(e),
                                    "error_type": type(e).__name__
                                },
                                metadata={
                                    "tool_input": tool_input,
                                    "specialist": task.specialist.value
                                }
                            )
                        
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
        
        # Set tracing metadata for final synthesis
        self.streaming_client.set_metadata(
            agent_type=task.specialist.value,
            stage="synthesis",
            prompt_file="specialist_synthesis.txt"
        )
        
        # Also update the trace context if available
        if TRACING_AVAILABLE and self.trace_collector:
            self.trace_collector.update_context(
                current_agent=task.specialist.value,
                current_stage="synthesis",
                current_prompt_file="specialist_synthesis.txt"
            )
        
        final_response = await self.streaming_client.create_message_with_retry_async(
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
    
    @classmethod
    def get_evaluation_metadata(cls, specialty: MedicalSpecialty) -> 'AgentMetadata':
        """
        Get evaluation metadata for a specific specialist type.
        
        Args:
            specialty: The medical specialty to get metadata for
            
        Returns:
            AgentMetadata configured for the specific specialty
        """
        # Import here to avoid circular dependency
        from services.agents.metadata.core import (
            AgentMetadata, 
            PromptMetadata
        )
        from evaluation.core.dimensions import (
            EvaluationCriteria,
            QualityComponent,
            dimension_registry
        )
        from evaluation.agents.specialist.dimensions import MEDICAL_DIMENSIONS
        
        # Get prompt metadata from SpecialistPrompts class
        prompts_metadata = SpecialistPrompts.get_prompt_metadata(specialty.value)
        
        # Define common evaluation criteria for all specialists
        evaluation_criteria = [
            EvaluationCriteria(
                dimension=MEDICAL_DIMENSIONS["medical_accuracy"],
                description=f"Medical accuracy of {specialty.value} specialist analysis",
                target_score=0.85,
                weight=0.30,
                measurement_method="llm_judge",
                measurement_description="LLM Judge evaluation of medical correctness"
            ),
            EvaluationCriteria(
                dimension=MEDICAL_DIMENSIONS["evidence_quality"],
                description=f"Quality of evidence provided by {specialty.value} specialist",
                target_score=0.80,
                weight=0.25,
                measurement_method="hybrid",
                measurement_description="Quality and appropriateness of evidence cited"
            ),
            EvaluationCriteria(
                dimension=MEDICAL_DIMENSIONS["clinical_reasoning"],
                description=f"Clinical reasoning quality of {specialty.value} specialist",
                target_score=0.85,
                weight=0.15,
                measurement_method="llm_judge",
                measurement_description="Sound clinical reasoning and decision-making"
            ),
            EvaluationCriteria(
                dimension=MEDICAL_DIMENSIONS["specialty_expertise"],
                description=f"Demonstration of {specialty.value} expertise",
                target_score=0.80,
                weight=0.15,
                measurement_method="hybrid",
                measurement_description="Specialty-specific knowledge and skills"
            ),
            EvaluationCriteria(
                dimension=MEDICAL_DIMENSIONS["patient_safety"],
                description=f"Patient safety considerations in {specialty.value} analysis",
                target_score=0.90,
                weight=0.15,
                measurement_method="llm_judge",
                measurement_description="Appropriate safety considerations and warnings"
            )
        ]
        
        # Add specialty-specific dimensions based on the specialty type
        specialty_specific_config = cls._get_specialty_specific_config(specialty)
        
        # Create the complete metadata
        # Define quality components for complex dimensions
        quality_components = {
            MEDICAL_DIMENSIONS["medical_accuracy"]: [
                QualityComponent(
                    name="factual_accuracy",
                    description="Correctness of medical facts and interpretations",
                    weight=0.6,
                    evaluation_method="llm_judge"
                ),
                QualityComponent(
                    name="clinical_relevance",
                    description="Relevance to the clinical question",
                    weight=0.4,
                    evaluation_method="llm_judge"
                )
            ],
            MEDICAL_DIMENSIONS["evidence_quality"]: [
                QualityComponent(
                    name="evidence_strength",
                    description="Quality and reliability of evidence sources",
                    weight=0.5,
                    evaluation_method="hybrid"
                ),
                QualityComponent(
                    name="evidence_relevance",
                    description="Appropriateness of evidence for the clinical question",
                    weight=0.5,
                    evaluation_method="llm_judge"
                )
            ],
            MEDICAL_DIMENSIONS["clinical_reasoning"]: [
                QualityComponent(
                    name="logical_flow",
                    description="Logical progression of clinical reasoning",
                    weight=0.6,
                    evaluation_method="llm_judge"
                ),
                QualityComponent(
                    name="differential_diagnosis",
                    description="Consideration of alternative diagnoses",
                    weight=0.4,
                    evaluation_method="llm_judge"
                )
            ],
            MEDICAL_DIMENSIONS["specialty_expertise"]: [
                QualityComponent(
                    name="domain_knowledge",
                    description="Demonstration of specialty-specific knowledge",
                    weight=0.7,
                    evaluation_method="hybrid"
                ),
                QualityComponent(
                    name="technical_accuracy",
                    description="Accuracy of technical/clinical details",
                    weight=0.3,
                    evaluation_method="llm_judge"
                )
            ],
            MEDICAL_DIMENSIONS["patient_safety"]: [
                QualityComponent(
                    name="risk_identification",
                    description="Identification of potential risks",
                    weight=0.6,
                    evaluation_method="llm_judge"
                ),
                QualityComponent(
                    name="safety_recommendations",
                    description="Appropriate safety precautions and warnings",
                    weight=0.4,
                    evaluation_method="llm_judge"
                )
            ]
        }
        
        # Create basic agent metadata
        agent_metadata = AgentMetadata(
            agent_type=specialty.value,
            agent_class="services.agents.specialist.SpecialistAgent",
            description=f"{specialty.value.replace('_', ' ').title()} specialist agent for focused medical analysis",
            prompts=prompts_metadata,
            capabilities=["medical_analysis", "clinical_reasoning", "evidence_synthesis"],
            supported_tools=["execute_health_query_v2"],
            config=specialty_specific_config
        )
        
        # Import and create evaluation metadata
        from evaluation.core.agent_evaluation_metadata import AgentEvaluationMetadata
        
        evaluation_metadata = AgentEvaluationMetadata(
            agent_metadata=agent_metadata,
            evaluation_criteria=evaluation_criteria,
            quality_components=quality_components
        )
        
        return evaluation_metadata
    
    @staticmethod
    def _get_specialty_specific_config(specialty: MedicalSpecialty) -> Dict[str, Any]:
        """Get specialty-specific configuration"""
        configs = {
            MedicalSpecialty.CARDIOLOGY: {
                "focus_areas": ["cardiovascular risk", "lipid management", "hypertension"],
                "key_metrics": ["cholesterol", "blood pressure", "ASCVD risk"],
                "guidelines": ["ACC/AHA 2018", "ESC 2021"]
            },
            MedicalSpecialty.ENDOCRINOLOGY: {
                "focus_areas": ["diabetes", "thyroid", "metabolic syndrome"],
                "key_metrics": ["HbA1c", "glucose", "thyroid hormones"],
                "guidelines": ["ADA Standards", "AACE Guidelines"]
            },
            MedicalSpecialty.LABORATORY_MEDICINE: {
                "focus_areas": ["lab interpretation", "reference ranges", "trends"],
                "key_metrics": ["all lab values"],
                "guidelines": ["CAP", "CLSI"]
            },
            # Add more specialties as needed
        }
        
        return configs.get(specialty, {
            "focus_areas": [],
            "key_metrics": [],
            "guidelines": []
        })