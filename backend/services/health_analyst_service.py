import os
import asyncio
import logging
import time
from typing import AsyncIterator, Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict

from anthropic import Anthropic
from services.streaming import SSEManager
from services.agents import (
    CMOAgent, 
    SpecialistAgent, 
    MedicalVisualizationAgent,
    QueryComplexity,
    SpecialistTask,
    SpecialistResult
)
from tools.tool_registry import ToolRegistry
from utils.anthropic_client import AnthropicStreamingClient

# Import tracing components
try:
    from services.tracing import (
        get_trace_collector, 
        TraceEventType, 
        TraceContextManager,
        TRACING_ENABLED
    )
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    TRACING_ENABLED = False

logger = logging.getLogger(__name__)

# Specialist emoji mapping
SPECIALIST_EMOJIS = {
    "cardiology": "❤️",
    "endocrinology": "🔬",
    "laboratory_medicine": "🧪",
    "data_analysis": "📊",
    "preventive_medicine": "🛡️",
    "pharmacy": "💊",
    "nutrition": "🥗",
    "general_practice": "👨‍⚕️"
}

# Specialist display names
SPECIALIST_NAMES = {
    "cardiology": "Cardiology",
    "endocrinology": "Endocrinology",
    "laboratory_medicine": "Laboratory Medicine",
    "data_analysis": "Data Analysis",
    "preventive_medicine": "Preventive Medicine",
    "pharmacy": "Pharmacy",
    "nutrition": "Nutrition",
    "general_practice": "General Practice"
}

class HealthAnalystService:
    """Orchestrates the multi-agent health analysis system with rich event streaming"""
    
    def __init__(self, enable_tracing: bool = None):
        self.sse_manager = SSEManager()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        logger.info(f"Initializing HealthAnalystService with API key: {api_key[:10]}...")
        self.anthropic_client = Anthropic(api_key=api_key)
        self.tool_registry = ToolRegistry()
        
        # Set up tracing
        if enable_tracing is None:
            enable_tracing = TRACING_ENABLED
        self.tracing_enabled = enable_tracing and TRACING_AVAILABLE
        self.trace_collector = get_trace_collector() if self.tracing_enabled else None
        
        # Model configuration
        self.visualization_model = os.getenv("VISUALIZATION_MODEL", "claude-3-5-sonnet-20241022")
        self.cmo_model = os.getenv("CMO_MODEL", self.visualization_model)
        self.specialist_model = os.getenv("SPECIALIST_MODEL", self.visualization_model)
        
        # Token limits
        self.max_tokens_synthesis = int(os.getenv("MAX_TOKENS_SYNTHESIS", "16384"))
        self.max_tokens_cmo_analysis = int(os.getenv("MAX_TOKENS_CMO_ANALYSIS", "4000"))
        self.max_tokens_task_planning = int(os.getenv("MAX_TOKENS_TASK_PLANNING", "6000"))
        self.max_tokens_specialist = int(os.getenv("MAX_TOKENS_SPECIALIST", "4000"))
        
        # Initialize CMO agent with tool calling capabilities
        self.cmo_agent = CMOAgent(
            anthropic_client=self.anthropic_client,
            tool_registry=self.tool_registry,
            model=self.cmo_model,
            max_tokens_analysis=self.max_tokens_cmo_analysis,
            max_tokens_planning=self.max_tokens_task_planning,
            max_tokens_synthesis=self.max_tokens_synthesis,
            enable_tracing=self.tracing_enabled
        )
        
        self.specialist_agent = SpecialistAgent(
            anthropic_client=self.anthropic_client,
            tool_registry=self.tool_registry,
            model=self.specialist_model,
            max_tokens=self.max_tokens_specialist,
            enable_tracing=self.tracing_enabled
        )
        
        self.visualization_agent = MedicalVisualizationAgent(
            anthropic_client=self.anthropic_client,
            model=self.visualization_model,
            max_tokens=self.max_tokens_synthesis
        )
        
        self.streaming_client = AnthropicStreamingClient(
            self.anthropic_client,
            max_retries=5
        )
        
        logger.info(f"="*60)
        logger.info("Health Analyst Service Initialization Complete")
        logger.info(f"Model Configuration:")
        logger.info(f"  Visualization model: {self.visualization_model}")
        logger.info(f"  CMO model: {self.cmo_model}")
        logger.info(f"  Specialist model: {self.specialist_model}")
        logger.info(f"Token Limits:")
        logger.info(f"  Synthesis: {self.max_tokens_synthesis}")
        logger.info(f"  CMO Analysis: {self.max_tokens_cmo_analysis}")
        logger.info(f"  Task Planning: {self.max_tokens_task_planning}")
        logger.info(f"  Specialist: {self.max_tokens_specialist}")
        logger.info(f"="*60)
    
    async def process_health_query(self, query: str, session_id: Optional[str] = None) -> AsyncIterator[Dict[str, Any]]:
        """Process a health query through the multi-agent system with rich events"""
        
        logger.info(f"="*80)
        logger.info(f"PROCESS HEALTH QUERY START")
        logger.info(f"Query: {query[:100]}...")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info(f"Tracing enabled: {self.tracing_enabled}")
        logger.info(f"="*80)
        
        # Start trace if tracing is enabled
        trace_id = None
        if self.tracing_enabled and self.trace_collector:
            trace_id = await self.trace_collector.start_trace(
                source="production",
                initial_input=query,
                session_id=session_id,
                metadata={"component": "health_analyst_service"}
            )
            logger.info(f"Started trace: {trace_id}")
        
        try:
            # Step 1: CMO initial analysis with rich formatting
            yield {
                "type": "thinking", 
                "content": "🏥 **Medical Team Consultation Starting**\n\nChief Medical Officer is reviewing your query..."
            }
            
            # Simulate tool call for data access
            yield {
                "type": "thinking",
                "content": "🔍 CMO is accessing your health records...\n\n🔧 **Tool Call: execute_health_query_v2**\n```\nSearching health database for relevant records...\n```"
            }
            
            try:
                # Record CMO analysis start
                if self.tracing_enabled and self.trace_collector:
                    self.trace_collector.update_context(
                        current_agent="cmo",
                        current_stage="query_analysis"
                    )
                
                complexity, approach, initial_data = await self.cmo_agent.analyze_query_with_tools(query)
                logger.info(f"CMO Analysis Complete - Complexity: {complexity.value}, Approach: {approach[:50]}...")
                
                # Record CMO analysis completion
                if self.tracing_enabled and self.trace_collector:
                    await self.trace_collector.add_event(
                        event_type=TraceEventType.STAGE_END,
                        agent_type="cmo",
                        stage="query_analysis",
                        data={
                            "complexity": complexity.value,
                            "approach": approach[:100],
                            "tool_calls_made": initial_data.get("tool_calls_made", 0),
                            "data_available": initial_data.get("data_available", False)
                        }
                    )
                
                # Success message
                yield {
                    "type": "thinking",
                    "content": "✅ CMO assessment complete - health data accessed successfully"
                }
                
            except Exception as e:
                logger.error(f"CMO analysis failed: {str(e)}")
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Full error details: {repr(e)}")
                
                # Check for API overload errors
                error_str = str(e).lower()
                error_repr = repr(e).lower()
                
                if any(term in error_str or term in error_repr for term in ["overloaded", "rate_limit", "too_many_requests", "tool_result"]):
                    logger.error("API error detected - providing user-friendly message")
                    yield {
                        "type": "error",
                        "content": "The AI service is experiencing issues. Please wait a moment and try again."
                    }
                    return
                else:
                    raise
            
            # Step 2: Create team strategy with rich formatting
            yield {
                "type": "thinking",
                "content": f"📋 **Creating Medical Team Strategy**\n\nComplexity Assessment: **{complexity.value.upper()}**\nApproach: {approach[:100]}..."
            }
            
            # Create specialist tasks
            if self.tracing_enabled and self.trace_collector:
                self.trace_collector.update_context(
                    current_agent="cmo", 
                    current_stage="task_creation"
                )
            
            tasks = await self.cmo_agent.create_specialist_tasks(query, complexity, approach, initial_data)
            
            # Record task creation
            if self.tracing_enabled and self.trace_collector:
                await self.trace_collector.add_event(
                    event_type=TraceEventType.STAGE_END,
                    agent_type="cmo",
                    stage="task_creation",
                    data={
                        "task_count": len(tasks),
                        "specialists": [task.specialist.value for task in tasks],
                        "complexity": complexity.value
                    }
                )
            
            # Step 3: Announce team assembly with specialist list
            specialist_intro = f"""👥 **Medical Team Assembled**

Your consultation will include:"""
            
            for i, task in enumerate(tasks, 1):
                specialist_type = task.specialist.value
                emoji = SPECIALIST_EMOJIS.get(specialist_type, "⚕️")
                name = SPECIALIST_NAMES.get(specialist_type, specialist_type.replace("_", " ").title())
                specialist_intro += f"\n{i}. {emoji} **{name}** - {task.objective[:100]}..."
            
            yield {"type": "thinking", "content": specialist_intro}
            
            # Step 4: Execute specialists with rich status updates
            all_results = {}
            total_data_points = 0
            
            # Group tasks by priority
            priority_groups = defaultdict(list)
            for task in tasks:
                priority_groups[task.priority].append(task)
            
            # Process each priority group
            for priority in sorted(priority_groups.keys()):
                group_tasks = priority_groups[priority]
                
                # Announce specialists starting
                for task in group_tasks:
                    specialist_type = task.specialist.value
                    emoji = SPECIALIST_EMOJIS.get(specialist_type, "⚕️")
                    name = SPECIALIST_NAMES.get(specialist_type, specialist_type.replace("_", " ").title())
                    
                    yield {
                        "type": "thinking",
                        "content": f"\n{emoji} **{name}** is analyzing your health data..."
                    }
                
                # Execute all specialists in this priority group in parallel
                async def execute_with_retry(task: SpecialistTask) -> Optional[SpecialistResult]:
                    max_retries = 3
                    retry_delay = 2
                    
                    # Record specialist task start
                    if self.tracing_enabled and self.trace_collector:
                        self.trace_collector.update_context(
                            current_agent=task.specialist.value,
                            current_stage="specialist_analysis"
                        )
                        await self.trace_collector.add_event(
                            event_type=TraceEventType.STAGE_START,
                            agent_type=task.specialist.value,
                            stage="specialist_analysis",
                            data={
                                "objective": task.objective,
                                "priority": task.priority,
                                "max_tool_calls": task.max_tool_calls
                            }
                        )
                    
                    for attempt in range(max_retries):
                        try:
                            result = await self.specialist_agent.execute_task(task)
                            
                            # Record successful completion
                            if self.tracing_enabled and self.trace_collector and result:
                                await self.trace_collector.add_event(
                                    event_type=TraceEventType.STAGE_END,
                                    agent_type=task.specialist.value,
                                    stage="specialist_analysis",
                                    data={
                                        "success": True,
                                        "confidence_level": result.confidence_level,
                                        "tool_calls_made": result.tool_calls_made,
                                        "data_points_found": len(result.data_points) if result.data_points else 0,
                                        "findings_length": len(result.findings),
                                        "recommendations_count": len(result.recommendations) if result.recommendations else 0
                                    }
                                )
                            
                            return result
                        except Exception as e:
                            if attempt < max_retries - 1:
                                logger.warning(f"Specialist {task.specialist.value} failed (attempt {attempt + 1}), retrying...")
                                await asyncio.sleep(retry_delay * (2 ** attempt))
                            else:
                                logger.error(f"Specialist {task.specialist.value} failed after {max_retries} attempts: {str(e)}")
                                
                                # Record failure
                                if self.tracing_enabled and self.trace_collector:
                                    await self.trace_collector.add_event(
                                        event_type=TraceEventType.ERROR,
                                        agent_type=task.specialist.value,
                                        stage="specialist_analysis",
                                        data={
                                            "error_type": type(e).__name__,
                                            "error_message": str(e),
                                            "attempts_made": max_retries
                                        }
                                    )
                                
                                return None
                
                # Run all tasks in this priority group
                results = await asyncio.gather(
                    *[execute_with_retry(task) for task in group_tasks],
                    return_exceptions=False
                )
                
                # Send completion updates and store results
                for task, result in zip(group_tasks, results):
                    if result:
                        specialist_type = task.specialist.value
                        name = SPECIALIST_NAMES.get(specialist_type, specialist_type.replace("_", " ").title())
                        
                        # Send completion update
                        yield {
                            "type": "thinking",
                            "content": f"✅ **{name}** completed analysis ({result.tool_calls_made} queries executed, {result.confidence_level:.0%} confidence)"
                        }
                        
                        all_results[task.specialist.value] = result
                        if result.data_points:
                            total_data_points += len(result.data_points)
                    else:
                        # Send error update
                        specialist_type = task.specialist.value
                        name = SPECIALIST_NAMES.get(specialist_type, specialist_type.replace("_", " ").title())
                        
                        yield {
                            "type": "thinking",
                            "content": f"⚠️ **{name}** encountered an issue and could not complete analysis"
                        }
            
            # Step 5: Stream CMO synthesis with rich formatting
            yield {
                "type": "thinking",
                "content": f"""🏥 **Chief Medical Officer Final Review**

📋 Synthesizing findings from {len(all_results)} specialists
📊 Total data points analyzed: {total_data_points}
⏳ Preparing comprehensive report..."""
            }
            
            # Record synthesis start
            if self.tracing_enabled and self.trace_collector:
                self.trace_collector.update_context(
                    current_agent="cmo",
                    current_stage="synthesis"
                )
                await self.trace_collector.add_event(
                    event_type=TraceEventType.STAGE_START,
                    agent_type="cmo",
                    stage="synthesis",
                    data={
                        "specialist_count": len(all_results),
                        "total_data_points": total_data_points,
                        "specialists_included": list(all_results.keys())
                    }
                )
            
            synthesis = {}
            async for chunk in self._stream_synthesis_with_cmo(query, all_results):
                yield chunk
                if chunk.get("type") == "synthesis_complete":
                    synthesis = chunk.get("synthesis", {})
                    
                    # Record synthesis completion
                    if self.tracing_enabled and self.trace_collector:
                        await self.trace_collector.add_event(
                            event_type=TraceEventType.STAGE_END,
                            agent_type="cmo",
                            stage="synthesis",
                            data={
                                "synthesis_length": len(synthesis.get("content", "")),
                                "synthesis_generated": bool(synthesis)
                            }
                        )
            
            # Step 6: Generate visualization if needed
            if self._should_generate_visualization(query, synthesis):
                logger.info("=== VISUALIZATION GENERATION STARTING ===")
                logger.info(f"Query: {query}")
                logger.info(f"Has synthesis: {bool(synthesis)}")
                logger.info(f"Specialist results count: {len(all_results)}")
                
                # Record visualization start
                if self.tracing_enabled and self.trace_collector:
                    self.trace_collector.update_context(
                        current_agent="visualization",
                        current_stage="visualization_generation"
                    )
                    await self.trace_collector.add_event(
                        event_type=TraceEventType.STAGE_START,
                        agent_type="visualization",
                        stage="visualization_generation",
                        data={
                            "query": query,
                            "has_synthesis": bool(synthesis),
                            "specialist_results_count": len(all_results)
                        }
                    )
                
                yield {
                    "type": "thinking",
                    "content": "📊 Generating interactive visualization of your health data..."
                }
                
                async for chunk in self._stream_visualization(query, synthesis, all_results):
                    logger.info(f"Streaming chunk type: {chunk.get('type')}, content length: {len(chunk.get('content', ''))}")
                    yield chunk
                
                # Record visualization completion
                if self.tracing_enabled and self.trace_collector:
                    await self.trace_collector.add_event(
                        event_type=TraceEventType.STAGE_END,
                        agent_type="visualization",
                        stage="visualization_generation",
                        data={"visualization_completed": True}
                    )
                    
                logger.info("=== VISUALIZATION GENERATION COMPLETE ===")
            
            # Step 7: Consultation complete
            yield {
                "type": "thinking",
                "content": "✅ **Medical Team Consultation Complete**\n\nYour health analysis has been delivered. The team remains available for follow-up questions."
            }
            
            # Record final completion
            if self.tracing_enabled and self.trace_collector:
                await self.trace_collector.add_event(
                    event_type=TraceEventType.STAGE_END,
                    agent_type="health_analyst_service",
                    stage="consultation_complete",
                    data={
                        "specialists_executed": len(all_results),
                        "synthesis_generated": bool(synthesis),
                        "visualization_generated": self._should_generate_visualization(query, synthesis),
                        "total_data_points": total_data_points
                    }
                )
            
            # Step 8: Done
            conversation_id = str(int(time.time()))
            yield {"type": "done", "conversation_id": conversation_id, "trace_id": trace_id}
            
        except Exception as e:
            logger.error(f"Error processing health query: {str(e)}")
            
            # Record error in trace
            if self.tracing_enabled and self.trace_collector:
                await self.trace_collector.add_event(
                    event_type=TraceEventType.ERROR,
                    agent_type="health_analyst_service",
                    stage="error_handling",
                    data={
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
            
            yield {"type": "error", "content": f"An error occurred: {str(e)}", "trace_id": trace_id}
        
        finally:
            # Always end the trace
            if self.tracing_enabled and self.trace_collector and trace_id:
                try:
                    completed_trace = await self.trace_collector.end_trace(trace_id)
                    if completed_trace:
                        logger.info(f"Trace completed: {trace_id} (duration: {completed_trace.total_duration_ms}ms)")
                except Exception as trace_error:
                    logger.error(f"Error ending trace {trace_id}: {trace_error}")
    
    async def _stream_synthesis_with_cmo(
        self, 
        query: str, 
        specialist_results: Dict[str, SpecialistResult]
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream the CMO synthesis with special formatting"""
        
        # Prepare specialist findings summary
        findings_text = []
        for specialty, result in specialist_results.items():
            name = SPECIALIST_NAMES.get(specialty, specialty.replace("_", " ").title())
            emoji = SPECIALIST_EMOJIS.get(specialty, "⚕️")
            
            findings_text.append(f"\n### {emoji} {name} Findings:")
            findings_text.append(f"Findings: {result.findings}")
            
            if result.recommendations:
                findings_text.append("\nRecommendations:")
                for rec in result.recommendations:
                    findings_text.append(f"- {rec}")
            
            if result.concerns:
                findings_text.append("\nConcerns:")
                for concern in result.concerns:
                    findings_text.append(f"- {concern}")
            
            findings_text.append(f"\nConfidence: {result.confidence_level:.0%}")
        
        specialist_findings = "\n".join(findings_text)
        
        # Use CMO agent's synthesis method
        response = await self.cmo_agent.synthesize_findings(
            query=query,
            specialist_findings=specialist_findings,
            stream=True
        )
        
        full_synthesis = ""
        paragraph_buffer = ""
        is_first_paragraph = True
        
        for chunk in response:
            if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                text = chunk.delta.text
                full_synthesis += text
                paragraph_buffer += text
                
                # Check for paragraph breaks
                if '\n\n' in paragraph_buffer:
                    paragraphs = paragraph_buffer.split('\n\n')
                    
                    # Process complete paragraphs
                    for i, para in enumerate(paragraphs[:-1]):
                        if is_first_paragraph and para.strip():
                            # Stream first paragraph word by word
                            words = para.strip().split()
                            for word in words:
                                yield {"type": "text", "content": word + " "}
                                await asyncio.sleep(0.03)
                            yield {"type": "text", "content": "\n\n"}
                            is_first_paragraph = False
                        else:
                            # Send complete paragraphs
                            yield {"type": "text", "content": para.strip() + "\n\n"}
                    
                    # Keep the last incomplete paragraph
                    paragraph_buffer = paragraphs[-1]
        
        # Handle any remaining text
        if paragraph_buffer.strip():
            if is_first_paragraph:
                # Stream word by word if it's still the first paragraph
                words = paragraph_buffer.strip().split()
                for word in words:
                    yield {"type": "text", "content": word + " "}
                    await asyncio.sleep(0.03)
            else:
                yield {"type": "text", "content": paragraph_buffer.strip()}
        
        # Return the synthesis for visualization check
        yield {"type": "synthesis_complete", "synthesis": {"content": full_synthesis}}
    
    def _should_generate_visualization(self, query: str, synthesis: Dict[str, Any]) -> bool:
        """Determine if visualization should be generated"""
        
        # Get the synthesis content
        synthesis_content = synthesis.get("content", "") if isinstance(synthesis, dict) else str(synthesis)
        
        # Check for data-related keywords in query or synthesis
        data_keywords = [
            'trend', 'history', 'compare', 'correlation', 
            'over time', 'progression', 'levels', 'values',
            'results', 'measurements', 'abnormal', 'chart'
        ]
        
        query_lower = query.lower()
        
        return any(keyword in query_lower or keyword in synthesis_content.lower() for keyword in data_keywords)
    
    async def _stream_visualization(
        self, 
        query: str, 
        synthesis: Dict[str, Any],
        specialist_results: Dict[str, SpecialistResult]
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream visualization generation"""
        
        # Convert specialist results dict to list format expected by visualization agent
        specialist_results_list = list(specialist_results.values())
        
        # Get synthesis text
        synthesis_text = synthesis.get("content", "") if isinstance(synthesis, dict) else str(synthesis)
        
        try:
            logger.info("=== _stream_visualization START ===")
            logger.info(f"Specialist results list length: {len(specialist_results_list)}")
            logger.info(f"Synthesis text length: {len(synthesis_text)}")
            
            # Notify that visualization is starting with thinking event (shows in separate bubble)
            yield {"type": "thinking", "content": "📊 Generating interactive visualization of your health data..."}
            yield {"type": "thinking", "content": "🎨 **Visualization Agent** is creating an interactive chart..."}
            
            # Stream visualization directly from the agent
            # The visualization agent already wraps code in markdown code blocks
            async for chunk in self.visualization_agent.stream_visualization(
                query, specialist_results_list, synthesis_text
            ):
                # Forward text chunks directly - frontend will parse markdown code blocks
                if chunk.get("type") == "text":
                    yield chunk
            
            logger.info("Visualization generated successfully")
                
        except Exception as e:
            logger.error(f"Visualization generation error: {str(e)}")
            yield {
                "type": "error", 
                "content": "Unable to generate visualization at this time."
            }
    
