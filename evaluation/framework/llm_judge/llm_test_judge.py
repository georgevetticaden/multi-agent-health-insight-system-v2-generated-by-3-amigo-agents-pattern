"""
LLM Test Judge for Evaluation Framework

This module provides a comprehensive LLM-based judge for evaluating agent performance
in the multi-agent health insight system. It consolidates all LLM evaluation logic,
handling both component scoring and failure analysis.

Key Features:
- Unified interface for all LLM evaluation operations
- Component scoring for quality assessment
- Detailed failure analysis with actionable recommendations
- Prompt management with caching for efficiency
- Support for both CMO and specialist agent evaluation

Usage:
    from evaluation.framework.llm_judge import LLMTestJudge
    
    judge = LLMTestJudge(anthropic_client, model="claude-3-sonnet-20240229")
    
    # Score a component
    result = await judge.score_context_awareness(analysis, query)
    
    # Analyze a failure
    analysis = await judge.analyze_complexity_mismatch(...)
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from functools import lru_cache

from anthropic import Anthropic
from typing import Union

# Import tracing support
try:
    from services.tracing import TRACING_ENABLED
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    TRACING_ENABLED = False

logger = logging.getLogger(__name__)


@dataclass
class ScoringResult:
    """
    Result from an LLM scoring operation.
    
    Attributes:
        score: Numeric score between 0.0 and 1.0
        reasoning: Human-readable explanation of the score
        details: Optional additional details (e.g., breakdown, metadata)
    """
    score: float
    reasoning: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class FailureAnalysis:
    """
    Detailed failure analysis from LLM Judge.
    
    Attributes:
        dimension: Evaluation dimension that failed (e.g., 'complexity_classification')
        root_cause: Primary reason for the failure
        specific_issues: List of specific problems identified
        recommendations: Actionable recommendations for improvement
        priority: Priority level ('high', 'medium', 'low')
        prompt_file: Specific prompt file that needs improvement (optional)
        expected_impact: Expected impact of implementing recommendations (optional)
    """
    dimension: str
    root_cause: str
    specific_issues: List[str]
    recommendations: List[str]
    priority: str  # high, medium, low
    prompt_file: Optional[str] = None
    expected_impact: Optional[str] = None


class LLMTestJudge:
    """
    LLM Test Judge for comprehensive agent evaluation.
    
    This class serves as the central hub for all LLM-based evaluation operations
    in the multi-agent health insight system. It provides both scoring capabilities
    for quality assessment and detailed failure analysis for improvement insights.
    
    The judge supports evaluation of:
    - CMO (Chief Medical Officer) agents
    - Specialist agents (Cardiology, Endocrinology, etc.)
    
    Architecture:
    - Scoring methods: Evaluate specific quality components (0.0-1.0 scale)
    - Failure analysis: Provide detailed insights when dimensions fail
    - Prompt management: Efficient loading and caching of evaluation prompts
    - Generic interfaces: Extensible design for new evaluation types
    
    Example:
        # Initialize the judge
        judge = LLMTestJudge(anthropic_client)
        
        # Score context awareness
        score_result = await judge.score_context_awareness(
            analysis="The patient shows signs of...",
            query="What are my recent health trends?"
        )
        print(f"Score: {score_result.score}, Reason: {score_result.reasoning}")
        
        # Analyze a failure
        failure = await judge.analyze_complexity_mismatch(
            agent_type="cmo",
            test_case={"query": "..."},
            actual_complexity="SIMPLE",
            expected_complexity="COMPLEX",
            approach_text="..."
        )
        print(f"Root cause: {failure.root_cause}")
        print(f"Recommendations: {failure.recommendations}")
    """
    
    def __init__(self, anthropic_client: Anthropic, model: str = "claude-3-5-sonnet-20241022"):
        self.client = anthropic_client
        self.model = model
        self._prompt_cache = {}
        
        # Set metadata for tracing if available
        if hasattr(self.client, 'set_metadata'):
            self.client.set_metadata(
                agent_type="llm_judge",
                stage="evaluation"
            )
    
    # ==================== Prompt Management ====================
    
    def _make_traced_call(self, messages: list, dimension: str, operation: str, max_tokens: int = 500):
        """Make an LLM call with tracing metadata if available."""
        # Set metadata for this specific call if tracing is available
        if hasattr(self.client, 'set_metadata'):
            self.client.set_metadata(
                agent_type="llm_judge",
                stage=f"{dimension}_{operation}",
                dimension=dimension,
                operation=operation
            )
        
        return self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=messages
        )
    
    @lru_cache(maxsize=32)
    def _load_prompt(self, agent_type: str, prompt_category: str, prompt_name: str) -> str:
        """
        Load a prompt file with caching.
        
        Args:
            agent_type: Agent type (e.g., 'cmo', 'specialist')
            prompt_category: Category ('scoring' or 'failure_analysis')
            prompt_name: Name of the prompt file (without .txt)
        
        Returns:
            Prompt template content
        """
        prompt_path = (
            Path(__file__).parent.parent.parent / 
            "agents" / agent_type / "judge_prompts" / 
            prompt_category / f"{prompt_name}.txt"
        )
        
        try:
            return prompt_path.read_text()
        except Exception as e:
            logger.error(f"Failed to load prompt {prompt_path}: {e}")
            raise ValueError(f"Could not load prompt: {prompt_name}")
    
    def _load_agent_prompt(self, agent_type: str, prompt_file: str) -> Optional[str]:
        """Load an actual agent prompt file for analysis"""
        # Navigate to project root
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent
        
        # Construct path based on agent type
        if agent_type == "cmo":
            prompt_path = project_root / "backend" / "services" / "agents" / "cmo" / "prompts" / prompt_file
        elif agent_type == "specialist":
            prompt_path = project_root / "backend" / "services" / "agents" / "specialist" / "prompts" / prompt_file
        else:
            logger.warning(f"Unknown agent type: {agent_type}")
            return None
        
        try:
            return prompt_path.read_text()
        except Exception as e:
            logger.error(f"Failed to load agent prompt {prompt_path}: {e}")
            return None
    
    # ==================== CMO Scoring Methods ====================
    
    async def score_context_awareness(self, analysis: str, query: str) -> ScoringResult:
        """
        Score context awareness in CMO analysis.
        
        Evaluates how well the analysis considers temporal context, patient history,
        and relevant background information when addressing the query.
        
        Args:
            analysis: The CMO agent's analysis text
            query: The original patient query
            
        Returns:
            ScoringResult with score (0.0-1.0) and reasoning
        """
        prompt_template = self._load_prompt("cmo", "scoring", "context_awareness")
        
        prompt = prompt_template.format(
            analysis=analysis,
            query=query
        )
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            response_text = response.content[0].text.strip()
            logger.debug(f"LLM Judge response for context awareness: {response_text[:200]}...")
            
            # Parse score and reasoning from response
            import re
            score_match = re.search(r'<score>([\d.]+)</score>', response_text)
            reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>', response_text, re.DOTALL)
            
            if not score_match:
                logger.warning(f"No score found in response: {response_text[:100]}...")
                return ScoringResult(score=0.5, reasoning="Failed to parse score from response")
            
            score = float(score_match.group(1))
            score = max(0.0, min(1.0, score))  # Clamp to valid range
            
            reasoning = reasoning_match.group(1).strip() if reasoning_match else "No reasoning provided"
            
            logger.debug(f"Parsed context awareness - Score: {score}, Reasoning: {reasoning[:50]}...")
            return ScoringResult(score=score, reasoning=reasoning)
        except Exception as e:
            logger.error(f"Failed to parse context awareness score: {e}")
            logger.error(f"Response was: {response.content[0].text[:200] if response.content else 'No content'}")
            return ScoringResult(score=0.5, reasoning=f"Parsing error: {str(e)}")
    
    async def score_specialist_rationale(self, approach: str, specialists: List[str], query: str) -> ScoringResult:
        """
        Score the rationale for specialist selection.
        
        Evaluates whether the CMO agent provides clear, medical reasoning for
        choosing specific specialists to address the patient's query.
        
        Args:
            approach: The analysis approach text containing rationale
            specialists: List of selected specialist names
            query: The original patient query
            
        Returns:
            ScoringResult with score (0.0-1.0) and reasoning
        """
        prompt_template = self._load_prompt("cmo", "scoring", "specialist_rationale")
        
        prompt = prompt_template.format(
            analysis=approach,
            specialists=", ".join(specialists),
            query=query
        )
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            response_text = response.content[0].text.strip()
            logger.info(f"          📄 LLM Judge specialist rationale response: {response_text[:300]}...")
            
            import re
            score_match = re.search(r'<score>([\d.]+)</score>', response_text)
            reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>', response_text, re.DOTALL)
            
            if not score_match:
                logger.warning(f"          ❌ XML parsing failed: No <score> tag found in response")
                logger.warning(f"          📄 Full response: {response_text}")
                return ScoringResult(score=0.5, reasoning="Failed to parse score from response - no <score> tag found")
            
            score_text = score_match.group(1)
            logger.info(f"          ✅ Found score in XML: '{score_text}'")
            
            try:
                score = float(score_text)
                original_score = score
                score = max(0.0, min(1.0, score))  # Clamp to valid range
                
                if original_score != score:
                    logger.warning(f"          ⚠️  Score {original_score} was clamped to {score}")
                    
            except ValueError as ve:
                logger.error(f"          ❌ Could not convert score '{score_text}' to float: {ve}")
                return ScoringResult(score=0.5, reasoning=f"Invalid score format: '{score_text}'")
            
            if not reasoning_match:
                logger.warning(f"          ⚠️  No <reasoning> tag found, using default")
                reasoning = "No reasoning provided in response"
            else:
                reasoning = reasoning_match.group(1).strip()
                logger.info(f"          ✅ Found reasoning: {reasoning[:100]}...")
            
            logger.info(f"          🎯 Final specialist rationale result: score={score:.3f}")
            return ScoringResult(score=score, reasoning=reasoning)
            
        except Exception as e:
            logger.error(f"          ❌ Exception during specialist rationale XML parsing: {e}")
            logger.error(f"          📄 Response was: {response.content[0].text[:500] if response.content else 'No content'}")
            return ScoringResult(score=0.5, reasoning=f"Parsing error: {str(e)}")
    
    async def score_comprehensive_approach(self, analysis: str, query: str, key_areas: List[str]) -> ScoringResult:
        """Score comprehensiveness of the analysis approach"""
        prompt_template = self._load_prompt("cmo", "scoring", "comprehensive_approach")
        
        prompt = prompt_template.format(
            analysis=analysis,
            query=query,
            key_concepts_str=", ".join(key_areas)
        )
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            response_text = response.content[0].text.strip()
            logger.debug(f"LLM Judge response for comprehensive approach: {response_text[:200]}...")
            
            import re
            score_match = re.search(r'<score>([\d.]+)</score>', response_text)
            reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>', response_text, re.DOTALL)
            
            if not score_match:
                logger.warning(f"No score found in response: {response_text[:100]}...")
                return ScoringResult(score=0.5, reasoning="Failed to parse score from response")
            
            score = float(score_match.group(1))
            score = max(0.0, min(1.0, score))  # Clamp to valid range
            
            reasoning = reasoning_match.group(1).strip() if reasoning_match else "No reasoning provided"
            
            logger.debug(f"Parsed comprehensive approach - Score: {score}, Reasoning: {reasoning[:50]}...")
            return ScoringResult(score=score, reasoning=reasoning)
        except Exception as e:
            logger.error(f"Failed to parse comprehensive approach score: {e}")
            logger.error(f"Response was: {response.content[0].text[:200] if response.content else 'No content'}")
            return ScoringResult(score=0.5, reasoning=f"Parsing error: {str(e)}")
    
    async def score_concern_identification(self, analysis: str, query: str) -> ScoringResult:
        """Score identification of health concerns"""
        prompt_template = self._load_prompt("cmo", "scoring", "concern_identification")
        
        prompt = prompt_template.format(
            analysis=analysis,
            query=query
        )
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            response_text = response.content[0].text.strip()
            logger.debug(f"LLM Judge response for concern identification: {response_text[:200]}...")
            
            import re
            score_match = re.search(r'<score>([\d.]+)</score>', response_text)
            reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>', response_text, re.DOTALL)
            
            if not score_match:
                logger.warning(f"No score found in response: {response_text[:100]}...")
                return ScoringResult(score=0.5, reasoning="Failed to parse score from response")
            
            score = float(score_match.group(1))
            score = max(0.0, min(1.0, score))  # Clamp to valid range
            
            reasoning = reasoning_match.group(1).strip() if reasoning_match else "No reasoning provided"
            
            logger.debug(f"Parsed concern identification - Score: {score}, Reasoning: {reasoning[:50]}...")
            return ScoringResult(score=score, reasoning=reasoning)
        except Exception as e:
            logger.error(f"Failed to parse concern identification score: {e}")
            logger.error(f"Response was: {response.content[0].text[:200] if response.content else 'No content'}")
            return ScoringResult(score=0.5, reasoning=f"Parsing error: {str(e)}")
    
    async def score_specialist_similarity(
        self, 
        predicted_specialists: List[str], 
        actual_specialists: List[str],
        query: str,
        medical_context: Optional[str] = None
    ) -> ScoringResult:
        """Score similarity between predicted and actual specialists using LLM"""
        prompt_template = self._load_prompt("cmo", "scoring", "specialist_similarity")
        
        prompt = prompt_template.format(
            query=query,
            medical_context=f'Medical Context: {medical_context}' if medical_context else '',
            predicted_specialists=', '.join(sorted(predicted_specialists)),
            actual_specialists=', '.join(sorted(actual_specialists))
        )
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            response_text = response.content[0].text.strip()
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)
            
            return ScoringResult(
                score=result.get('similarity_score', 0.5),
                reasoning=result.get('reasoning', 'No reasoning provided'),
                details={
                    'is_similar': result.get('is_similar', False),
                    'missing_critical': result.get('missing_critical', []),
                    'acceptable_substitutions': result.get('acceptable_substitutions', {})
                }
            )
        except Exception as e:
            logger.error(f"Failed to parse specialist similarity score: {e}")
            # Fallback to deterministic scoring
            from evaluation.framework.llm_judge import SpecialistSimilarityScorer
            score, details = SpecialistSimilarityScorer.calculate_similarity(
                predicted_specialists, actual_specialists
            )
            return ScoringResult(
                score=score,
                reasoning="Fallback to deterministic similarity calculation",
                details=details
            )
    
    # ==================== Specialist Scoring Methods ====================
    
    async def score_data_identification(self, analysis: str, query: str, expected_data: List[str]) -> ScoringResult:
        """Score data identification quality for specialist agents"""
        prompt_template = self._load_prompt("specialist", "scoring", "data_identification")
        
        prompt = prompt_template.format(
            analysis=analysis,
            query=query,
            expected_data=", ".join(expected_data)
        )
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            response_text = response.content[0].text.strip()
            logger.debug(f"LLM Judge response for data identification: {response_text[:200]}...")
            
            import re
            score_match = re.search(r'<score>([\d.]+)</score>', response_text)
            reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>', response_text, re.DOTALL)
            
            if not score_match:
                logger.warning(f"No score found in response: {response_text[:100]}...")
                return ScoringResult(score=0.5, reasoning="Failed to parse score from response")
            
            score = float(score_match.group(1))
            score = max(0.0, min(1.0, score))  # Clamp to valid range
            
            reasoning = reasoning_match.group(1).strip() if reasoning_match else "No reasoning provided"
            
            logger.debug(f"Parsed data identification - Score: {score}, Reasoning: {reasoning[:50]}...")
            return ScoringResult(score=score, reasoning=reasoning)
        except Exception as e:
            logger.error(f"Failed to parse data identification score: {e}")
            logger.error(f"Response was: {response.content[0].text[:200] if response.content else 'No content'}")
            return ScoringResult(score=0.5, reasoning=f"Parsing error: {str(e)}")
    
    async def score_clinical_accuracy(self, analysis: str, specialty: str, query: str) -> ScoringResult:
        """Score clinical accuracy for specialist agents"""
        prompt_template = self._load_prompt("specialist", "scoring", "clinical_accuracy")
        
        prompt = prompt_template.format(
            analysis=analysis,
            specialty=specialty,
            query=query
        )
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            response_text = response.content[0].text.strip()
            logger.debug(f"LLM Judge response for clinical accuracy: {response_text[:200]}...")
            
            import re
            score_match = re.search(r'<score>([\d.]+)</score>', response_text)
            reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>', response_text, re.DOTALL)
            
            if not score_match:
                logger.warning(f"No score found in response: {response_text[:100]}...")
                return ScoringResult(score=0.5, reasoning="Failed to parse score from response")
            
            score = float(score_match.group(1))
            score = max(0.0, min(1.0, score))  # Clamp to valid range
            
            reasoning = reasoning_match.group(1).strip() if reasoning_match else "No reasoning provided"
            
            logger.debug(f"Parsed clinical accuracy - Score: {score}, Reasoning: {reasoning[:50]}...")
            return ScoringResult(score=score, reasoning=reasoning)
        except Exception as e:
            logger.error(f"Failed to parse clinical accuracy score: {e}")
            logger.error(f"Response was: {response.content[0].text[:200] if response.content else 'No content'}")
            return ScoringResult(score=0.5, reasoning=f"Parsing error: {str(e)}")
    
    # ==================== CMO Failure Analysis Methods ====================
    
    async def analyze_complexity_mismatch(
        self,
        agent_type: str,
        test_case: Dict[str, Any],
        actual_complexity: str,
        expected_complexity: str,
        approach_text: str
    ) -> FailureAnalysis:
        """
        Analyze why complexity classification was wrong.
        
        Provides detailed analysis of complexity misclassification, identifying
        root causes and suggesting prompt improvements to better distinguish
        between complexity levels.
        
        Args:
            agent_type: Type of agent ('cmo' or 'specialist')
            test_case: Test case data including the query
            actual_complexity: Complexity level the agent predicted
            expected_complexity: Correct complexity level
            approach_text: Agent's analysis approach text
            
        Returns:
            FailureAnalysis with root cause, issues, and recommendations
        """
        prompt_template = self._load_prompt(agent_type, "failure_analysis", "complexity_mismatch")
        
        # Load the actual agent prompt
        actual_prompt_content = self._load_agent_prompt(
            agent_type, 
            "1_gather_data_assess_complexity.txt"
        ) or "[Could not load actual prompt content]"
        
        prompt = prompt_template.format(
            query=test_case.get('query', ''),
            expected_complexity=expected_complexity,
            actual_complexity=actual_complexity,
            approach_text=approach_text,
            actual_prompt_content=actual_prompt_content
        )
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            response_text = response.content[0].text.strip()
            logger.info(f"Raw LLM response for complexity mismatch (first 1000 chars): {response_text[:1000]}...")
            if len(response_text) > 1000:
                logger.info(f"Raw LLM response (chars 1000-2000): {response_text[1000:2000]}...")
            if len(response_text) > 2000:
                logger.info(f"Raw LLM response (last 500 chars): ...{response_text[-500:]}")
            
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)
            
            logger.info(f"Parsed JSON keys: {list(result.keys())}")
            logger.info(f"Full parsed result: {json.dumps(result, indent=2)}")
            
            # Extract recommendations from new format
            recommendations = []
            if result.get('recommendations'):
                for rec in result['recommendations']:
                    if isinstance(rec, dict):
                        # New structured format
                        recommendations.append(rec.get('recommendation', str(rec)))
                    else:
                        # Simple string format
                        recommendations.append(str(rec))
            
            failure_analysis = FailureAnalysis(
                dimension="complexity_classification",
                root_cause=result.get('root_cause', result.get('issue_description', '')),
                specific_issues=result.get('complexity_indicators', []),
                recommendations=recommendations,
                priority=result.get('priority', 'medium'),
                prompt_file=result.get('prompt_file'),
                expected_impact=result.get('expected_impact')
            )
            
            logger.info(f"✅ COMPLEXITY CLASSIFICATION ANALYSIS CREATED:")
            logger.info(f"   root_cause: '{failure_analysis.root_cause[:50]}...' (length: {len(failure_analysis.root_cause)})")
            logger.info(f"   specific_issues: {len(failure_analysis.specific_issues)} items")
            logger.info(f"   recommendations: {len(failure_analysis.recommendations)} items")
            
            return failure_analysis
        except Exception as e:
            logger.error(f"Failed to parse complexity mismatch analysis: {e}")
            return FailureAnalysis(
                dimension="complexity_classification",
                root_cause="Failed to analyze complexity mismatch",
                specific_issues=["Review complexity classification criteria"],
                recommendations=["Review complexity classification criteria"],
                priority="medium"
            )
    
    async def analyze_specialist_mismatch(
        self,
        agent_type: str,
        test_case: Dict[str, Any],
        actual_specialists: List[str],
        expected_specialists: List[str],
        approach_text: str,
        f1_score: float,
        missing_critical: List[str]
    ) -> FailureAnalysis:
        """Analyze why specialist selection was wrong"""
        prompt_template = self._load_prompt(agent_type, "failure_analysis", "specialist_mismatch")
        
        # Load the actual agent prompt
        prompt_file = "3_assign_specialist_tasks.txt" if agent_type == "cmo" else "system_prompt.txt"
        actual_prompt_content = self._load_agent_prompt(
            agent_type, 
            prompt_file
        ) or "[Could not load actual prompt content]"
        
        prompt = prompt_template.format(
            query=test_case.get('query', ''),
            expected_specialists=', '.join(sorted(expected_specialists)),
            actual_specialists=', '.join(sorted(actual_specialists)),
            f1_score=f1_score,
            missing_critical=', '.join(missing_critical) if missing_critical else 'None',
            approach_text=approach_text,
            actual_prompt_content=actual_prompt_content
        )
        
        logger.info(f"=== LLM JUDGE SPECIALTY_SELECTION PROMPT ===")
        logger.info(f"Prompt length: {len(prompt)} characters")
        logger.info(f"First 1000 chars: {prompt[:1000]}")
        if len(prompt) > 1000:
            logger.info(f"Next 1000 chars: {prompt[1000:2000]}")
        if len(prompt) > 2000:
            logger.info(f"Final 500 chars: {prompt[-500:]}")
        logger.info(f"=== END SPECIALTY_SELECTION PROMPT ===")
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            response_text = response.content[0].text.strip()
            logger.info(f"Raw LLM response for specialist mismatch (first 1000 chars): {response_text[:1000]}...")
            if len(response_text) > 1000:
                logger.info(f"Raw LLM response (chars 1000-2000): {response_text[1000:2000]}...")
            if len(response_text) > 2000:
                logger.info(f"Raw LLM response (last 500 chars): ...{response_text[-500:]}")
            
            import re
            
            # Method 1: Try to extract from markdown code blocks (most reliable)
            markdown_match = re.search(r'```(?:json)?\s*\n?(.*?)```', response_text, re.DOTALL)
            result = None
            
            if markdown_match:
                logger.info("Found markdown code block")
                json_content = markdown_match.group(1).strip()
                
                # Method 1a: Direct parse
                try:
                    result = json.loads(json_content)
                    logger.info(f"Successfully parsed JSON from markdown block")
                    logger.info(f"Parsed JSON keys: {list(result.keys())}")
                except json.JSONDecodeError as e:
                    logger.warning(f"Direct parse failed: {e}")
                    
                    # Method 1b: Find the outermost JSON object by tracking braces
                    if result is None:
                        brace_count = 0
                        json_start = None
                        json_end = None
                        
                        for i, char in enumerate(json_content):
                            if char == '{':
                                if brace_count == 0:
                                    json_start = i
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0 and json_start is not None:
                                    json_end = i + 1
                                    break
                        
                        if json_start is not None and json_end is not None:
                            try:
                                json_substring = json_content[json_start:json_end]
                                result = json.loads(json_substring)
                                logger.info(f"Successfully parsed JSON using brace matching (start: {json_start}, end: {json_end})")
                                logger.info(f"Parsed JSON keys: {list(result.keys())}")
                            except json.JSONDecodeError as e:
                                logger.warning(f"Brace matching parse failed: {e}")
            
            # Method 2: If markdown extraction failed, try to find JSON in the entire response
            if result is None:
                logger.info("Markdown extraction failed, trying to find JSON in entire response")
                
                # Method 2a: Look for JSON that starts with expected structure
                json_pattern = r'\{\s*"prompt_file"\s*:.*?"priority"\s*:\s*"[^"]+"\s*\}'
                json_match = re.search(json_pattern, response_text, re.DOTALL)
                
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        logger.info("Successfully parsed JSON using structure pattern")
                        logger.info(f"Parsed JSON keys: {list(result.keys())}")
                    except json.JSONDecodeError:
                        logger.warning("Structure pattern parse failed")
                
                # Method 2b: Track braces in entire response
                if result is None:
                    brace_count = 0
                    json_start = None
                    json_end = None
                    
                    for i, char in enumerate(response_text):
                        if char == '{':
                            if brace_count == 0:
                                json_start = i
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0 and json_start is not None:
                                json_end = i + 1
                                # Try to parse this potential JSON object
                                try:
                                    json_substring = response_text[json_start:json_end]
                                    candidate = json.loads(json_substring)
                                    # Check if this looks like our expected response
                                    if isinstance(candidate, dict) and ('issue_description' in candidate or 'prompt_file' in candidate):
                                        result = candidate
                                        logger.info(f"Found valid JSON response at position {json_start}-{json_end}")
                                        logger.info(f"Parsed JSON keys: {list(result.keys())}")
                                        break
                                except json.JSONDecodeError:
                                    # Continue looking for next potential JSON object
                                    json_start = None
                
                # Method 2c: Last resort - try direct parse
                if result is None:
                    try:
                        result = json.loads(response_text)
                        logger.info("Successfully parsed entire response as JSON")
                    except json.JSONDecodeError:
                        logger.error("All JSON parsing methods failed")
            
            if result:
                logger.info(f"Parsed JSON keys: {list(result.keys())}")
                logger.info(f"Full parsed result: {json.dumps(result, indent=2)}")
                logger.info(f"issue_description: '{result.get('issue_description', 'NOT FOUND')}'")
                logger.info(f"missing_specialists_reason type: {type(result.get('missing_specialists_reason'))}")
                logger.info(f"recommendations length: {len(result.get('recommendations', []))}")
            else:
                logger.error("Failed to parse any valid JSON from response")
                # Try to extract what we can from the raw response text
                # This is a fallback for when JSON parsing completely fails
                raise ValueError("No valid JSON could be parsed from LLM response")
            
            # Extract specific issues from the new format
            specific_issues = []
            if result.get('missing_specialists_reason') and isinstance(result['missing_specialists_reason'], dict):
                for spec, reason in result['missing_specialists_reason'].items():
                    if reason:  # Only add if reason is not empty
                        specific_issues.append(f"Missing {spec}: {reason}")
            if result.get('unnecessary_specialists') and isinstance(result['unnecessary_specialists'], list):
                if result['unnecessary_specialists']:  # Only add if list is not empty
                    specific_issues.append(f"Unnecessary: {', '.join(result['unnecessary_specialists'])}")
            
            # Extract recommendations from new format
            recommendations = []
            if result.get('recommendations') and isinstance(result['recommendations'], list):
                for rec in result['recommendations']:
                    if isinstance(rec, dict):
                        # New structured format
                        rec_text = rec.get('recommendation', str(rec))
                        if rec_text and rec_text.strip():  # Only add non-empty recommendations
                            recommendations.append(rec_text)
                    elif isinstance(rec, str) and rec.strip():
                        # Simple string format
                        recommendations.append(rec)
            
            # Get root cause - ensure it's not empty
            root_cause = result.get('issue_description', '')
            if not root_cause or not root_cause.strip():
                # Fallback to a generic message if empty
                root_cause = f"Failed to select correct specialists: expected {', '.join(expected_specialists)}, got {', '.join(actual_specialists)}"
                logger.warning(f"Empty issue_description, using fallback root cause")
            
            failure_analysis = FailureAnalysis(
                dimension="specialty_selection",
                root_cause=root_cause,
                specific_issues=specific_issues,
                recommendations=recommendations,
                priority=result.get('priority', 'medium'),
                prompt_file=result.get('prompt_file')
            )
            
            logger.info(f"✅ SPECIALTY SELECTION ANALYSIS CREATED:")
            logger.info(f"   root_cause: '{failure_analysis.root_cause[:50]}...' (length: {len(failure_analysis.root_cause)})")
            logger.info(f"   specific_issues: {len(failure_analysis.specific_issues)} items")
            logger.info(f"   recommendations: {len(failure_analysis.recommendations)} items")
            
            return failure_analysis
        except Exception as e:
            logger.error(f"Failed to parse specialist mismatch analysis: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Response content available: {response.content[0].text[:200] if response.content else 'No content'}")
            
            # Create a meaningful fallback based on the actual test data
            specific_issues = []
            if missing_critical:
                specific_issues.append(f"Missing critical specialists: {', '.join(missing_critical)}")
            specific_issues.append(f"Expected {len(expected_specialists)} specialists, got {len(actual_specialists)}")
            
            return FailureAnalysis(
                dimension="specialty_selection",
                root_cause=f"Specialist selection failed with F1 score {f1_score:.2f}. Expected: {', '.join(sorted(expected_specialists))}, Actual: {', '.join(sorted(actual_specialists))}",
                specific_issues=specific_issues,
                recommendations=[
                    "Review specialist selection criteria in prompts",
                    f"Add explicit rules for including {', '.join(missing_critical)}" if missing_critical else "Improve specialist matching logic"
                ],
                priority="high" if f1_score < 0.5 else "medium"
            )
    
    async def analyze_quality_issues(
        self,
        agent_type: str,
        query: str,
        approach_text: str,
        quality_breakdown: Dict[str, float],
        key_data_points: List[str],
        quality_score: float,
        target_score: float = 0.80
    ) -> FailureAnalysis:
        """Analyze analysis quality issues"""
        logger.info(f"analyze_quality_issues called - quality_score: {quality_score}, target_score: {target_score}")
        logger.debug(f"Quality breakdown: {quality_breakdown}")
        
        # Check if this is a near-miss (within 30% of target)
        is_near_miss = quality_score >= (target_score * 0.7)
        logger.debug(f"Is near-miss: {is_near_miss} (threshold: {target_score * 0.7})")
        
        # For near-misses, focus on the weakest components
        if is_near_miss:
            # Sort components by score to identify weakest areas
            sorted_components = sorted(quality_breakdown.items(), key=lambda x: x[1])
            weakest_components = dict(sorted_components[:2])  # Focus on 2 weakest
            
            # Build focused analysis
            specific_issues = []
            recommendations = []
            
            for component, score in weakest_components.items():
                if component == "specialist_rationale" and score < 0.5:
                    specific_issues.append(f"Specialist rationale score ({score:.2f}): Missing clear medical reasoning for specialist selection")
                    recommendations.append("Add explicit medical rationale for each specialist chosen (e.g., 'Endocrinology for glucose/diabetes concerns')")
                
                elif component == "context_awareness" and score < 0.9:
                    specific_issues.append(f"Context awareness score ({score:.2f}): Could better incorporate temporal context and patient history")
                    recommendations.append("Emphasize timeline considerations and historical data patterns in analysis approach")
                
                elif component == "comprehensive_approach" and score < 0.95:
                    specific_issues.append(f"Comprehensive approach score ({score:.2f}): Minor gaps in coverage of medical concepts")
                    recommendations.append("Ensure all relevant medical domains are explicitly addressed in the approach")
                
                elif component == "concern_identification" and score < 0.9:
                    specific_issues.append(f"Concern identification score ({score:.2f}): Could be more proactive in identifying potential risks")
                    recommendations.append("Explicitly mention potential health risks or areas needing monitoring")
                
                elif component == "data_gathering" and score < 1.0:
                    specific_issues.append(f"Data gathering score ({score:.2f}): Tool usage could be optimized")
                    recommendations.append("Ensure tool queries are precisely targeted to the patient's question")
            
            # Calculate how close we are to passing
            gap = target_score - quality_score
            percentage_short = (gap / target_score) * 100
            
            return FailureAnalysis(
                dimension="analysis_quality",
                root_cause=f"Near-miss: Quality score {quality_score:.2f} is {percentage_short:.1f}% short of target {target_score}",
                specific_issues=specific_issues if specific_issues else [f"Overall quality {quality_score:.2f} slightly below target {target_score}"],
                recommendations=recommendations if recommendations else ["Minor improvements needed in weakest components"],
                priority="low",  # Near-misses are lower priority
                expected_impact=f"Addressing these specific areas would likely push the score above the {target_score} threshold"
            )
        
        # For significant failures, use the full LLM analysis
        prompt_template = self._load_prompt(agent_type, "failure_analysis", "quality_issues")
        
        # Load relevant agent prompts
        relevant_prompts = {}
        if agent_type == "cmo":
            prompt_files = [
                "1_gather_data_assess_complexity.txt",
                "2_define_analytical_approach.txt", 
                "3_assign_specialist_tasks.txt",
                "4_synthesis.txt"
            ]
        else:
            prompt_files = ["system_prompt.txt"]
        
        for pf in prompt_files:
            content = self._load_agent_prompt(agent_type, pf)
            if content:
                relevant_prompts[pf] = content
        
        # Identify weak components
        weak_components = {k: v for k, v in quality_breakdown.items() if v < 0.5}
        
        prompt = prompt_template.format(
            query=query,
            quality_score=quality_score,
            quality_breakdown=json.dumps(quality_breakdown, indent=2),
            key_data_points=', '.join(key_data_points),
            approach_text=approach_text,
            weak_components=json.dumps(weak_components, indent=2),
            relevant_prompts=json.dumps(relevant_prompts, indent=2)
        )
        
        logger.info(f"=== LLM JUDGE ANALYSIS_QUALITY PROMPT ===")
        logger.info(f"Prompt length: {len(prompt)} characters")
        logger.info(f"First 1000 chars: {prompt[:1000]}")
        if len(prompt) > 1000:
            logger.info(f"Next 1000 chars: {prompt[1000:2000]}")
        if len(prompt) > 2000:
            logger.info(f"Next 1000 chars: {prompt[2000:3000]}")
        if len(prompt) > 3000:
            logger.info(f"Final 500 chars: {prompt[-500:]}")
        logger.info(f"=== END ANALYSIS_QUALITY PROMPT ===")
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            response_text = response.content[0].text.strip()
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)
            
            # Extract specific issues from weak components
            specific_issues = []
            for component, analysis in result.get('weak_components', {}).items():
                specific_issues.append(f"{component}: {analysis}")
            
            # Extract recommendations from new format
            recommendations = []
            for prompt_file, improvements in result.get('prompt_improvements', {}).items():
                if improvements.get('needs_update'):
                    # Check if recommendations are in new format
                    if improvements.get('recommendations'):
                        for rec in improvements['recommendations']:
                            if isinstance(rec, dict):
                                recommendations.append(f"{prompt_file}: {rec.get('recommendation', str(rec))}")
                            else:
                                recommendations.append(f"{prompt_file}: {rec}")
                    # Fallback to old format
                    elif improvements.get('specific_changes'):
                        for change in improvements['specific_changes']:
                            recommendations.append(f"{prompt_file}: {change}")
            
            return FailureAnalysis(
                dimension="analysis_quality",
                root_cause=result.get('root_cause', ''),
                specific_issues=specific_issues,
                recommendations=recommendations,
                priority=result.get('overall_priority', 'medium'),
                expected_impact=result.get('expected_impact')
            )
        except Exception as e:
            logger.error(f"Failed to parse quality analysis: {e}")
            return FailureAnalysis(
                dimension="analysis_quality",
                root_cause=f"Analysis quality below threshold ({quality_score:.2f} < {target_score})",
                specific_issues=[f"{k}: {v:.2f}" for k, v in weak_components.items()],
                recommendations=["Review analysis comprehensiveness"],
                priority="high" if quality_score < 0.7 else "medium",
                prompt_file="backend/services/agents/cmo/prompts/2_define_analytical_approach.txt"
            )
    
    async def analyze_tool_usage_issues(
        self,
        agent_type: str,
        query: str,
        tool_calls_made: int,
        tool_success_rate: float,
        tool_relevance_score: float,
        initial_data_gathered: Dict[str, Any]
    ) -> FailureAnalysis:
        """Analyze tool usage issues"""
        prompt_template = self._load_prompt(agent_type, "failure_analysis", "tool_usage_issues")
        
        prompt = prompt_template.format(
            query=query,
            tool_calls_made=tool_calls_made,
            tool_success_rate=tool_success_rate,
            tool_relevance_score=tool_relevance_score,
            initial_data_gathered=json.dumps(initial_data_gathered, indent=2)
        )
        
        logger.info(f"LLM Judge tool_usage prompt (first 300 chars): {prompt[:300]}...")
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            response_text = response.content[0].text.strip()
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)
            
            # Extract recommendations from new format
            recommendations = []
            if result.get('recommendations'):
                for rec in result['recommendations']:
                    if isinstance(rec, dict):
                        recommendations.append(rec.get('recommendation', str(rec)))
                    else:
                        recommendations.append(str(rec))
            # Fallback to old format
            elif result.get('specific_improvements'):
                recommendations = result['specific_improvements']
            
            return FailureAnalysis(
                dimension="tool_usage",
                root_cause=result.get('root_cause', result.get('issue_description', '')),
                specific_issues=[result.get('issue_description', '')],
                recommendations=recommendations,
                priority=result.get('priority', 'medium')
            )
        except Exception as e:
            logger.error(f"Failed to parse tool usage analysis: {e}")
            return FailureAnalysis(
                dimension="tool_usage",
                root_cause="Insufficient or ineffective tool usage",
                specific_issues=[f"Tool success rate: {tool_success_rate:.2f}"],
                recommendations=["Ensure appropriate tools are called for data gathering"],
                priority="high" if tool_success_rate < 0.8 else "medium"
            )
    
    async def analyze_response_structure_issues(
        self,
        agent_type: str,
        query: str,
        structure_errors: List[str],
        approach_text: str
    ) -> FailureAnalysis:
        """Analyze response structure issues"""
        prompt_template = self._load_prompt(agent_type, "failure_analysis", "response_structure_issues")
        
        prompt = prompt_template.format(
            query=query,
            structure_errors=json.dumps(structure_errors, indent=2),
            response_content_sample=approach_text[:500] + "..."
        )
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            response_text = response.content[0].text.strip()
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)
            
            # Extract recommendations from new format
            recommendations = []
            if result.get('recommendations'):
                for rec in result['recommendations']:
                    if isinstance(rec, dict):
                        recommendations.append(rec.get('recommendation', str(rec)))
                    else:
                        recommendations.append(str(rec))
            # Fallback to old format
            elif result.get('specific_improvements'):
                recommendations = result['specific_improvements']
            
            return FailureAnalysis(
                dimension="response_structure",
                root_cause=result.get('issue_description', ''),
                specific_issues=result.get('structure_errors', structure_errors),
                recommendations=recommendations,
                priority=result.get('priority', 'high')
            )
        except Exception as e:
            logger.error(f"Failed to parse structure analysis: {e}")
            return FailureAnalysis(
                dimension="response_structure",
                root_cause="Response structure validation failed",
                specific_issues=structure_errors if structure_errors else ["Invalid format"],
                recommendations=["Ensure response follows required format"],
                priority="high"
            )
    
    # ==================== Generic Interfaces ====================
    
    async def score_component(
        self,
        agent_type: str,
        component_name: str,
        **kwargs
    ) -> ScoringResult:
        """
        Generic interface for scoring any component.
        
        This method routes to the appropriate scoring method based on
        agent type and component name.
        """
        # Map component names to scoring methods
        scoring_methods = {
            "cmo": {
                "context_awareness": self.score_context_awareness,
                "specialist_rationale": self.score_specialist_rationale,
                "comprehensive_approach": self.score_comprehensive_approach,
                "concern_identification": self.score_concern_identification,
                "specialist_similarity": self.score_specialist_similarity,
            },
            "specialist": {
                "data_identification": self.score_data_identification,
                "clinical_accuracy": self.score_clinical_accuracy,
            }
        }
        
        if agent_type not in scoring_methods:
            logger.error(f"Unknown agent type: {agent_type}")
            return ScoringResult(score=0.5, reasoning=f"Unknown agent type: {agent_type}")
        
        if component_name not in scoring_methods[agent_type]:
            logger.error(f"Unknown component for {agent_type}: {component_name}")
            return ScoringResult(score=0.5, reasoning=f"Unknown component: {component_name}")
        
        # Call the appropriate scoring method
        method = scoring_methods[agent_type][component_name]
        return await method(**kwargs)
    
    async def analyze_failure(
        self,
        agent_type: str,
        dimension: str,
        **kwargs
    ) -> FailureAnalysis:
        """
        Generic interface for analyzing any dimension failure.
        
        This method routes to the appropriate analysis method based on
        agent type and dimension.
        """
        # Map dimensions to analysis methods
        analysis_methods = {
            "complexity_classification": self.analyze_complexity_mismatch,
            "specialty_selection": self.analyze_specialist_mismatch,
            "analysis_quality": self.analyze_quality_issues,
            "tool_usage": self.analyze_tool_usage_issues,
            "response_structure": self.analyze_response_structure_issues,
        }
        
        if dimension not in analysis_methods:
            logger.error(f"Unknown dimension: {dimension}")
            return FailureAnalysis(
                dimension=dimension,
                root_cause=f"Unknown dimension: {dimension}",
                specific_issues=["Dimension not supported"],
                recommendations=[],
                priority="low"
            )
        
        # Add agent_type to kwargs
        kwargs['agent_type'] = agent_type
        
        # Call the appropriate analysis method
        method = analysis_methods[dimension]
        return await method(**kwargs)
    
    async def analyze_dimension_patterns(
        self,
        agent_type: str,
        dimension_name: str, 
        dimension_data: Dict[str, Any]
    ) -> Optional[Dict]:
        """
        Analyze failure patterns across all tests for a dimension.
        
        This method performs macro-level analysis by examining all test failures
        for a specific dimension, identifying patterns, and providing consolidated
        recommendations.
        
        Args:
            agent_type: Type of agent being evaluated (e.g., 'cmo')
            dimension_name: Name of the dimension being analyzed
            dimension_data: Aggregated data including all test failures
            
        Returns:
            Consolidated analysis with patterns and recommendations, or None if analysis fails
        """
        logger.info(f"🔍 Analyzing patterns for dimension: {dimension_name}")
        
        # Load macro analysis prompt
        prompt_template = self._load_prompt(
            agent_type, 
            "macro_analysis", 
            "dimension_pattern_analysis"
        )
        
        # Collect all unique prompt files mentioned in failures
        unique_prompt_files = set()
        for test_failure in dimension_data['failed_tests']:
            prompt_files = test_failure.get('prompt_files', [])
            for pf in prompt_files:
                if isinstance(pf, dict):
                    unique_prompt_files.add(pf.get('name', pf.get('filename', '')))
                else:
                    unique_prompt_files.add(str(pf))
        
        # Load actual prompt content
        prompt_contents = {}
        for prompt_file in unique_prompt_files:
            # Clean filename (remove path if included)
            clean_filename = prompt_file.split('/')[-1] if '/' in prompt_file else prompt_file
            
            # Load the actual prompt content
            actual_content = self._load_agent_prompt(agent_type, clean_filename)
            if actual_content:
                prompt_contents[clean_filename] = actual_content
            else:
                prompt_contents[clean_filename] = f"[Could not load {clean_filename}]"
                logger.warning(f"Could not load prompt file: {clean_filename}")
        
        # Format individual test analyses
        test_analyses_text = []
        for test_failure in dimension_data['failed_tests']:
            test_text = f"""Test Case: {test_failure['test_id']}
Query: {test_failure['query'][:100]}...
Score: {test_failure['score']:.2%} (Target: {test_failure['target']:.2%})

Individual LLM Judge Analysis:
- Root Cause: {test_failure.get('root_cause', 'Not analyzed')}
- Recommendations:"""
            
            for rec in test_failure.get('recommendations', []):
                test_text += f"\n  • {rec}"
                
            test_text += f"""
- Priority: {test_failure.get('priority', 'medium')}
- Prompt Files: {', '.join(str(pf) for pf in test_failure.get('prompt_files', []))}
--------------------------------------------------------------------------------"""
            test_analyses_text.append(test_text)
        
        # Format prompt contents
        prompt_contents_text = []
        for filename, content in sorted(prompt_contents.items()):
            prompt_contents_text.append(f"""File: {filename}
```
{content}
```
================================================================================""")
        
        # Format the complete prompt
        prompt = prompt_template.format(
            dimension_name=dimension_name,
            failed_count=len(dimension_data['failed_tests']),
            total_count=dimension_data['total_tests'],
            avg_score=dimension_data['avg_score'],
            target_score=dimension_data['target_score'],
            failure_rate=dimension_data['failure_rate'],
            test_analyses='\n'.join(test_analyses_text),
            prompt_contents='\n'.join(prompt_contents_text)
        )
        
        # Call LLM with more tokens for larger context
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,  # Increased for comprehensive analysis
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse response
            response_text = response.content[0].text.strip()
            logger.debug(f"Raw macro analysis response: {response_text[:500]}...")
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)
                
            logger.info(f"✅ Macro analysis complete for {dimension_name}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze dimension patterns: {e}")
            return None