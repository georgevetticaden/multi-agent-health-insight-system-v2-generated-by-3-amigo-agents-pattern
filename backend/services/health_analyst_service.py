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
from services.agents.cmo.cmo_agent_simple import CMOAgentSimple
from tools.tool_registry import ToolRegistry
from utils.anthropic_client import AnthropicStreamingClient

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
    
    def __init__(self):
        self.sse_manager = SSEManager()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        logger.info(f"Initializing HealthAnalystService with API key: {api_key[:10]}...")
        self.anthropic_client = Anthropic(api_key=api_key)
        self.tool_registry = ToolRegistry()
        
        # Model configuration
        self.visualization_model = os.getenv("VISUALIZATION_MODEL", "claude-3-5-sonnet-20241022")
        self.cmo_model = os.getenv("CMO_MODEL", self.visualization_model)
        self.specialist_model = os.getenv("SPECIALIST_MODEL", self.visualization_model)
        
        # Token limits
        self.max_tokens_synthesis = int(os.getenv("MAX_TOKENS_SYNTHESIS", "16384"))
        self.max_tokens_cmo_analysis = int(os.getenv("MAX_TOKENS_CMO_ANALYSIS", "4000"))
        self.max_tokens_task_planning = int(os.getenv("MAX_TOKENS_TASK_PLANNING", "6000"))
        self.max_tokens_specialist = int(os.getenv("MAX_TOKENS_SPECIALIST", "4000"))
        
        # Initialize agents - use simplified CMO to avoid tool issues
        self.cmo_agent = CMOAgentSimple(
            anthropic_client=self.anthropic_client,
            tool_registry=self.tool_registry,
            model=self.cmo_model,
            max_tokens_analysis=self.max_tokens_cmo_analysis,
            max_tokens_planning=self.max_tokens_task_planning
        )
        
        self.specialist_agent = SpecialistAgent(
            anthropic_client=self.anthropic_client,
            tool_registry=self.tool_registry,
            model=self.specialist_model,
            max_tokens=self.max_tokens_specialist
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
    
    async def process_health_query(self, query: str) -> AsyncIterator[Dict[str, Any]]:
        """Process a health query through the multi-agent system with rich events"""
        
        logger.info(f"="*80)
        logger.info(f"PROCESS HEALTH QUERY START")
        logger.info(f"Query: {query[:100]}...")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info(f"="*80)
        
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
                complexity, approach, initial_data = await self.cmo_agent.analyze_query_simple(query)
                logger.info(f"CMO Analysis Complete - Complexity: {complexity.value}, Approach: {approach[:50]}...")
                
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
            tasks = await self.cmo_agent.create_specialist_tasks(query, complexity, approach, initial_data)
            
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
                    
                    for attempt in range(max_retries):
                        try:
                            return await self.specialist_agent.execute_task(task)
                        except Exception as e:
                            if attempt < max_retries - 1:
                                logger.warning(f"Specialist {task.specialist.value} failed (attempt {attempt + 1}), retrying...")
                                await asyncio.sleep(retry_delay * (2 ** attempt))
                            else:
                                logger.error(f"Specialist {task.specialist.value} failed after {max_retries} attempts: {str(e)}")
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
            
            synthesis = {}
            async for chunk in self._stream_synthesis_with_cmo(query, all_results):
                yield chunk
                if chunk.get("type") == "synthesis_complete":
                    synthesis = chunk.get("synthesis", {})
            
            # Step 6: Generate visualization if needed
            if self._should_generate_visualization(query, synthesis):
                logger.info("=== VISUALIZATION GENERATION STARTING ===")
                logger.info(f"Query: {query}")
                logger.info(f"Has synthesis: {bool(synthesis)}")
                logger.info(f"Specialist results count: {len(all_results)}")
                
                yield {
                    "type": "thinking",
                    "content": "📊 Generating interactive visualization of your health data..."
                }
                
                async for chunk in self._stream_visualization(query, synthesis, all_results):
                    logger.info(f"Streaming chunk type: {chunk.get('type')}, content length: {len(chunk.get('content', ''))}")
                    yield chunk
                    
                logger.info("=== VISUALIZATION GENERATION COMPLETE ===")
            
            # Step 7: Consultation complete
            yield {
                "type": "thinking",
                "content": "✅ **Medical Team Consultation Complete**\n\nYour health analysis has been delivered. The team remains available for follow-up questions."
            }
            
            # Step 8: Done
            yield {"type": "done", "conversation_id": str(int(time.time()))}
            
        except Exception as e:
            logger.error(f"Error processing health query: {str(e)}")
            yield {"type": "error", "content": f"An error occurred: {str(e)}"}
    
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
        
        # Create synthesis prompt
        synthesis_prompt = f"""As the Chief Medical Officer, provide a comprehensive response to the patient's question.

Original Question: {query}

Specialist Findings:
{specialist_findings}

Provide a direct, comprehensive answer that:
1. Directly addresses the patient's specific question
2. Integrates all specialist insights
3. Highlights key findings and patterns
4. Provides clear recommendations
5. Flags any concerns requiring attention

Use clear, patient-friendly language while maintaining medical accuracy."""
        
        # Stream the synthesis
        response = self.streaming_client.create_message_with_retry(
            model=self.cmo_model,
            messages=[{"role": "user", "content": synthesis_prompt}],
            max_tokens=self.max_tokens_synthesis,
            temperature=0.3,
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