import json
import logging
from typing import Dict, Any, Optional, AsyncGenerator, List
from anthropic import Anthropic
from utils.anthropic_client import AnthropicStreamingClient
from .qe_prompts import QEPrompts

logger = logging.getLogger(__name__)

class QEAgent:
    """Quality Evaluation Agent for analyzing traces and generating test cases"""
    
    def __init__(self, trace_id: Optional[str] = None):
        """Initialize QE Agent
        
        Args:
            trace_id: Optional trace ID for context
        """
        self.trace_id = trace_id
        self.client = Anthropic()
        self.streaming_client = AnthropicStreamingClient(self.client)
        self.prompts = QEPrompts()
        self.conversation_history: List[Dict[str, str]] = []
        self.current_trace_context: Optional[Dict[str, Any]] = None
        self.identified_issues: List[Dict[str, Any]] = []
        
        # Test case state management
        self.current_test_case: Optional[Dict[str, Any]] = None
        self.saved_test_cases: List[Dict[str, Any]] = []
        self.test_case_iteration: int = 0
        
        # Evaluation results storage
        self.last_evaluation_result: Optional[Dict[str, Any]] = None
        
    def set_trace_context(self, trace_context: Dict[str, Any]):
        """Set the trace context for analysis"""
        self.current_trace_context = trace_context
        logger.info(f"QE Agent initialized with trace context for query: {trace_context.get('query', 'Unknown')}")
    
    def _extract_test_case_from_response(self, response: str) -> Optional[str]:
        """Extract TestCase code block from agent response"""
        # Look for ```python blocks
        if "```python" in response:
            start = response.find("```python") + 9
            end = response.find("```", start)
            if end > start:
                return response[start:end].strip()
        
        # Look for TestCase( pattern
        if "TestCase(" in response:
            start = response.find("TestCase(")
            # Find the matching closing parenthesis
            depth = 1
            i = start + 9
            while i < len(response) and depth > 0:
                if response[i] == '(':
                    depth += 1
                elif response[i] == ')':
                    depth -= 1
                i += 1
            if depth == 0:
                return response[start:i]
        
        return None
    
    def update_test_case(self, updates: Dict[str, Any]):
        """Update the current test case with new values"""
        if not self.current_test_case:
            self.current_test_case = {}
        
        self.current_test_case.update(updates)
        self.test_case_iteration += 1
        
    def save_current_test_case(self):
        """Save the current test case to the saved list"""
        if self.current_test_case:
            self.saved_test_cases.append(self.current_test_case.copy())
            return True
        return False
    
    def start_new_test_case(self):
        """Start a new test case"""
        if self.current_test_case:
            self.save_current_test_case()
        
        self.current_test_case = {}
        self.test_case_iteration = 0
        
    def get_test_case_summary(self) -> Dict[str, Any]:
        """Get summary of current test case session"""
        return {
            "current_test_case": self.current_test_case,
            "saved_test_cases": len(self.saved_test_cases),
            "iterations": self.test_case_iteration,
            "trace_id": self.trace_id
        }
    
    async def analyze_user_feedback(
        self,
        user_message: str,
        stage_context: Optional[Dict[str, Any]] = None,
        stream_handler: Optional[Any] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Analyze user feedback about the trace and generate appropriate response
        
        Args:
            user_message: User's feedback or question
            stage_context: Optional context about specific stage being discussed
            stream_handler: Optional handler for streaming responses
        """
        # Build conversation context
        messages = []
        
        # System prompt - use collaborative mode
        system_prompt = self.prompts.build_system_prompt(include_examples=True, collaborative=True)
        logger.debug(f"System prompt length: {len(system_prompt)}")
        logger.debug(f"System prompt preview: {system_prompt[:200]}...")
        
        # Add trace context as first user message if not already in conversation
        if not self.conversation_history and self.current_trace_context:
            context_message = f"""
Here is the trace context for analysis:

Query: {self.current_trace_context.get('query', 'N/A')}
Complexity Classification: {self.current_trace_context.get('complexity', 'N/A')}
Assigned Specialists: {', '.join(self.current_trace_context.get('specialists', []))}
Trace ID: {self.trace_id}

Key Stages Executed:
{json.dumps(self.current_trace_context.get('stages', {}), indent=2)}
"""
            messages.append({"role": "user", "content": context_message})
            messages.append({"role": "assistant", "content": "I have the trace context loaded. I can see the query, actual complexity classification, specialists used, and execution details. Tell me what issues you've observed and I'll help create a test case with the correct expected values."})
            
            # Store in history
            self.conversation_history.append({"role": "user", "content": context_message})
            self.conversation_history.append({"role": "assistant", "content": messages[-1]["content"]})
        
        # Add conversation history
        messages.extend(self.conversation_history)
        
        # Check for action commands first
        command_response = await self._handle_action_command(user_message)
        if command_response:
            # Handle command responses
            async for event in command_response:
                yield event
            return
        
        # Add current message with explicit reminder about action menu
        current_message = user_message
        if stage_context:
            current_message = f"{user_message}\n\nContext: User is looking at stage '{stage_context.get('stage_name', 'unknown')}'"
        
        # Add explicit instruction in the user message
        current_message += "\n\nIMPORTANT: After creating the test case, you MUST show the action menu with options (refine, run, save, new, list)."
        
        messages.append({"role": "user", "content": current_message})
        
        # Stream response
        response_text = ""
        test_case_generated = False
        
        logger.info(f"Starting QE agent response generation for message: {user_message}...")
        
        try:
            # Set metadata for tracing
            self.streaming_client.set_metadata(
                agent_type="qe",
                stage="test_case_generation",
                prompt_file="2_build_test_case.txt"
            )
            
            # Use the streaming client like CMO does with create_message_with_retry_async
            stream = await self.streaming_client.create_message_with_retry_async(
                model="claude-3-opus-20240229",
                messages=messages,
                system=system_prompt,
                max_tokens=4000,
                temperature=0.3,
                stream=True
            )
            
            # Process the streaming response
            chunk_count = 0
            stop_streaming_text = False
            for chunk in stream:
                chunk_count += 1
                
                # Handle text delta
                if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                    content = chunk.delta.text
                    response_text += content
                    
                    # Check if we should stop streaming text (when we hit the Python code block)
                    if "```python" in response_text and not stop_streaming_text:
                        # Find where the code block starts
                        pre_code_text = response_text[:response_text.find("```python")]
                        # Calculate how much of current chunk is before the code block
                        already_sent = len(response_text) - len(content)
                        if already_sent < len(pre_code_text):
                            # Send the remaining text before the code block
                            remaining = pre_code_text[already_sent:]
                            if remaining:
                                yield {
                                    "type": "text",
                                    "content": remaining
                                }
                        stop_streaming_text = True
                        logger.info(f"Stopped streaming text at code block in chunk {chunk_count}")
                    
                    # Stream content only if we haven't hit the code block
                    if not stop_streaming_text:
                        yield {
                            "type": "text",
                            "content": content
                        }
                    
                    # Check if we're generating a test case
                    if "TestCase(" in response_text and not test_case_generated:
                        logger.debug(f"Detected TestCase in response at chunk {chunk_count}")
                        test_case_generated = True
                
                # Handle message stop
                elif hasattr(chunk, 'type') and chunk.type == 'message_stop':
                    logger.debug("Received message_stop event")
            
            # Store in conversation history
            self.conversation_history.append({"role": "user", "content": current_message})
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            # Log the response for debugging
            logger.info(f"QE Agent streaming completed. Chunks: {chunk_count}, Response length: {len(response_text)}")
            if "What would you like to do" in response_text:
                logger.info("Action menu was included in response")
            else:
                logger.warning("Action menu was NOT included in response")
                logger.info(f"Response ends with: ...{response_text[-100:]}")
            
            # Extract and yield test case after streaming is complete
            if test_case_generated and "TestCase(" in response_text:
                test_case = self._extract_test_case_from_response(response_text)
                if test_case:
                    # Parse and save the test case
                    try:
                        self.current_test_case = {
                            "raw": test_case,
                            "iteration": self.test_case_iteration
                        }
                        self.test_case_iteration += 1
                        
                        # Yield the test case event
                        yield {
                            "type": "test_case",
                            "content": test_case
                        }
                        
                        # Extract and yield the action menu if present
                        action_menu_start = response_text.find("What would you like to do")
                        if action_menu_start != -1:
                            action_menu = response_text[action_menu_start:]
                            yield {
                                "type": "action_menu",
                                "content": action_menu
                            }
                        else:
                            logger.warning("Action menu not found in response after test case")
                    except Exception as e:
                        logger.error(f"Error parsing test case: {e}")
            
            # Identify any issues mentioned
            self._identify_issues_from_response(response_text)
            
        except Exception as e:
            logger.error(f"Error in QE agent analysis: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": f"Error analyzing feedback: {str(e)}"
            }
        finally:
            logger.info(f"QE agent analyze_user_feedback completed. Final response length: {len(response_text)}")
    
    async def _handle_action_command(self, command: str) -> Optional[AsyncGenerator[Dict[str, Any], None]]:
        """Handle action commands like 'run', 'save', 'new', etc."""
        command_lower = command.lower().strip()
        
        async def generate_response():
            if command_lower in ["run", "execute"]:
                if not self.current_test_case:
                    yield {
                        "type": "text",
                        "content": "❌ No test case to run. Please create a test case first."
                    }
                    return
                
                yield {
                    "type": "text",
                    "content": "🚀 Starting evaluation..."
                }
                
                # Trigger evaluation
                yield {
                    "type": "start_evaluation",
                    "content": self.current_test_case
                }
                
            elif command_lower == "save":
                if self.current_test_case:
                    yield {
                        "type": "save_test_case",
                        "content": self.current_test_case
                    }
                    
                    if self.save_current_test_case():
                        yield {
                            "type": "text", 
                            "content": f"✅ Test case saved! Total saved test cases: {len(self.saved_test_cases)}\n\nYou can continue refining this test case or type 'new' to create another one."
                        }
                else:
                    yield {
                        "type": "text",
                        "content": "❌ No test case to save. Please create a test case first."
                    }
                    
            elif command_lower == "save and run":
                if self.save_current_test_case():
                    yield {
                        "type": "text",
                        "content": f"✅ Test case saved! Total saved test cases: {len(self.saved_test_cases)}\n\n🚀 Execution feature coming soon!"
                    }
                else:
                    yield {
                        "type": "text",
                        "content": "❌ No test case to save."
                    }
                    
            elif command_lower == "new":
                self.start_new_test_case()
                yield {
                    "type": "text",
                    "content": "📝 Starting a new test case. What issue have you observed in this trace?"
                }
                
            elif command_lower == "list":
                if self.saved_test_cases:
                    cases_list = "\n".join([f"{i+1}. {tc.get('id', 'unnamed')}" for i, tc in enumerate(self.saved_test_cases)])
                    yield {
                        "type": "text",
                        "content": f"📋 Saved test cases in this session:\n{cases_list}\n\nCurrent test case iterations: {self.test_case_iteration}"
                    }
                else:
                    yield {
                        "type": "text",
                        "content": "No saved test cases yet in this session."
                    }
            
            elif command_lower == "details":
                # Show evaluation report details
                if self.last_evaluation_result:
                    report_url = self.last_evaluation_result.get('report_url')
                    overall_score = self.last_evaluation_result.get('overall_score', 0)
                    dimension_results = self.last_evaluation_result.get('dimension_results', {})
                    
                    if report_url:
                        # Build a comprehensive response with both summary and link
                        content = f"📊 **Full Evaluation Report**\n\n"
                        content += f"**Overall Score:** {overall_score:.1%}\n\n"
                        
                        # Show dimension scores
                        if dimension_results:
                            content += "**Dimension Scores:**\n"
                            for dim_name, dim_data in dimension_results.items():
                                score = dim_data.get('normalized_score', 0)
                                content += f"- {dim_name.replace('_', ' ').title()}: {score:.1%}\n"
                            content += "\n"
                        
                        content += f"**Detailed Report:** \n\n"
                        
                        yield {
                            "type": "text",
                            "content": content
                        }
                        
                        # Yield the report URL as a special type that can be rendered as a link
                        yield {
                            "type": "report_link",
                            "url": report_url,
                            "text": "View Full Report"
                        }
                        
                        # Continue with the description
                        description = "\n\nThe full report includes:\n"
                        description += "- Executive summary with overall scores\n"
                        description += "- Detailed dimension breakdowns\n"
                        description += "- Component-level scoring\n"
                        description += "- Visualizations and charts\n"
                        description += "- Failure analysis and recommendations\n"
                        description += "- Complete test case details"
                        
                        yield {
                            "type": "text",
                            "content": description
                        }
                    else:
                        # No report URL but we have results
                        content = f"📊 **Evaluation Results Summary**\n\n"
                        content += f"**Overall Score:** {overall_score:.1%}\n\n"
                        
                        if dimension_results:
                            content += "**Dimension Scores:**\n"
                            for dim_name, dim_data in dimension_results.items():
                                score = dim_data.get('normalized_score', 0)
                                content += f"- {dim_name.replace('_', ' ').title()}: {score:.1%}\n"
                        
                        content += "\n*Note: Full HTML report generation may be in progress or disabled.*"
                        
                        yield {
                            "type": "text",
                            "content": content
                        }
                else:
                    yield {
                        "type": "text",
                        "content": "No evaluation results available. Please run an evaluation first using the 'run' command."
                    }
                
        if command_lower in ["run", "execute", "save", "save and run", "new", "list", "details"]:
            return generate_response()
        return None
    
    def _identify_issues_from_response(self, response: str):
        """Extract identified issues from the response"""
        issue_keywords = {
            "complexity": ["misclassified", "wrong complexity", "should be SIMPLE", "should be STANDARD", "should be COMPLEX", "should be COMPREHENSIVE"],
            "specialist": ["missing specialist", "wrong specialist", "should include", "forgot to assign"],
            "analysis": ["incomplete analysis", "missed correlation", "insufficient depth"],
            "tool": ["inefficient query", "wrong tool", "missing data"],
            "structure": ["malformed", "missing section", "format error"]
        }
        
        for issue_type, keywords in issue_keywords.items():
            if any(keyword.lower() in response.lower() for keyword in keywords):
                self.identified_issues.append({
                    "type": issue_type,
                    "trace_id": self.trace_id,
                    "description": response[:200]  # First 200 chars as summary
                })
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation and identified issues"""
        return {
            "trace_id": self.trace_id,
            "query": self.current_trace_context.get('query') if self.current_trace_context else None,
            "identified_issues": self.identified_issues,
            "conversation_length": len(self.conversation_history)
        }
    
    def set_evaluation_result(self, result: Dict[str, Any]):
        """Set the evaluation result from frontend"""
        self.last_evaluation_result = result
        logger.info(f"QE Agent received evaluation result for trace {self.trace_id}")
        logger.info(f"Overall score: {result.get('overall_score', 'N/A')}")
        logger.info(f"Report URL: {result.get('report_url', 'N/A')}")
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = []
        self.identified_issues = []
        logger.info(f"QE Agent conversation reset for trace {self.trace_id}")