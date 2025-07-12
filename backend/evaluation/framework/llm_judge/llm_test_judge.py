"""
LLM Test Judge for CMO Evaluation

This module provides an AI-powered test judge that analyzes evaluation failures
and provides specific recommendations for prompt improvements.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from anthropic import Anthropic

logger = logging.getLogger(__name__)


class JudgmentType(Enum):
    """Types of judgments the LLM can make"""
    COMPLEXITY_MISMATCH = "complexity_mismatch"
    SPECIALIST_SELECTION = "specialist_selection"
    ANALYSIS_QUALITY = "analysis_quality"
    PROMPT_IMPROVEMENT = "prompt_improvement"


@dataclass
class PromptRecommendation:
    """Recommendation for improving a specific prompt"""
    prompt_file: str
    issue_description: str
    specific_changes: List[str]
    reasoning: str
    priority: str  # high, medium, low


@dataclass
class SpecialistSimilarityJudgment:
    """Judgment on whether specialist selections are similar enough"""
    is_similar: bool
    similarity_score: float
    reasoning: str
    missing_critical: List[str]
    acceptable_substitutions: Dict[str, str]


@dataclass
class QualityAnalysisJudgment:
    """Judgment on analysis quality issues and improvements"""
    prompt_file: str
    issue_description: str
    root_cause: str
    weak_components: Dict[str, str]  # component -> reason for weakness
    specific_improvements: List[str]
    expected_impact: str
    priority: str  # high, medium, low


@dataclass
class ToolUsageAnalysisJudgment:
    """Judgment on tool usage issues"""
    issue_description: str
    root_cause: str
    specific_improvements: List[str]
    priority: str  # high, medium, low


@dataclass  
class ResponseStructureAnalysisJudgment:
    """Judgment on response structure issues"""
    issue_description: str
    structure_errors: List[str]
    specific_improvements: List[str]
    priority: str  # high, medium, low


class LLMTestJudge:
    """AI-powered judge for evaluating test results and suggesting improvements"""
    
    def __init__(self, anthropic_client: Anthropic, model: str = "claude-3-5-sonnet-20241022"):
        self.client = anthropic_client
        self.model = model
    
    async def analyze_complexity_mismatch(
        self,
        test_case: Dict[str, Any],
        actual_complexity: str,
        expected_complexity: str,
        approach_text: str
    ) -> PromptRecommendation:
        """Analyze why complexity classification was wrong and suggest prompt improvements"""
        
        # Load prompt from external file
        prompt_file = Path(__file__).parent / "prompts" / "cmo" / "complexity" / "analyze_mismatch.txt"
        prompt_template = prompt_file.read_text()
        
        # Format the prompt with actual values
        prompt = prompt_template.format(
            query=test_case.get('query', ''),
            expected_complexity=expected_complexity,
            actual_complexity=actual_complexity,
            approach_text=approach_text
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            # Extract JSON from response, handling potential extra text
            response_text = response.content[0].text.strip()
            
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)
                
            return PromptRecommendation(**result)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"Raw response: {response.content[0].text[:500]}...")
            return PromptRecommendation(
                prompt_file="backend/services/agents/cmo/prompts/1_initial_analysis.txt",
                issue_description="Failed to analyze complexity mismatch",
                specific_changes=["Review complexity classification criteria"],
                reasoning="Automated analysis failed",
                priority="medium"
            )
    
    async def judge_specialist_similarity(
        self,
        predicted_specialists: List[str],
        actual_specialists: List[str],
        query: str,
        medical_context: Optional[str] = None
    ) -> SpecialistSimilarityJudgment:
        """Judge if predicted specialists are acceptably similar to actual specialists"""
        
        # Load prompt from external file
        prompt_file = Path(__file__).parent / "prompts" / "cmo" / "specialist" / "judge_similarity.txt"
        prompt_template = prompt_file.read_text()
        
        # Format the prompt with actual values
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
            # Extract JSON from response, handling potential extra text
            response_text = response.content[0].text.strip()
            
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)
                
            return SpecialistSimilarityJudgment(**result)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse specialist similarity response: {e}")
            logger.debug(f"Raw response: {response.content[0].text[:500]}...")
            # Fallback to simple set comparison
            predicted_set = set(predicted_specialists)
            actual_set = set(actual_specialists)
            intersection = predicted_set & actual_set
            union = predicted_set | actual_set
            similarity = len(intersection) / len(union) if union else 0
            
            return SpecialistSimilarityJudgment(
                is_similar=similarity >= 0.6,
                similarity_score=similarity,
                reasoning="Fallback to set similarity calculation",
                missing_critical=list(actual_set - predicted_set),
                acceptable_substitutions={}
            )
    
    async def analyze_specialist_mismatch(
        self,
        test_case: Dict[str, Any],
        actual_specialists: List[str],
        expected_specialists: List[str],
        approach_text: str,
        f1_score: float,
        missing_critical: List[str]
    ) -> Dict[str, Any]:
        """Analyze why specialist selection was wrong and suggest prompt improvements"""
        
        # Load prompt from external file
        prompt_file = Path(__file__).parent / "prompts" / "cmo" / "specialist" / "analyze_mismatch.txt"
        prompt_template = prompt_file.read_text()
        
        # Format the prompt with actual values
        prompt = prompt_template.format(
            query=test_case.get('query', ''),
            expected_specialists=', '.join(sorted(expected_specialists)),
            actual_specialists=', '.join(sorted(actual_specialists)),
            f1_score=f1_score,
            missing_critical=', '.join(missing_critical) if missing_critical else 'None',
            approach_text=approach_text
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            # Extract JSON from response, handling potential extra text
            response_text = response.content[0].text.strip()
            
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)
                
            return result
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse specialist mismatch response: {e}")
            logger.debug(f"Raw response: {response.content[0].text[:500]}...")
            return {
                "prompt_file": "backend/services/agents/cmo/prompts/3_task_creation.txt",
                "issue_description": "Failed to analyze specialist selection mismatch",
                "missing_specialists_reason": {s: "Analysis failed" for s in missing_critical},
                "unnecessary_specialists": [],
                "specific_changes": ["Review specialist selection criteria"],
                "reasoning": "Automated analysis failed",
                "priority": "medium"
            }
    
    async def analyze_quality_issues(
        self,
        query: str,
        approach_text: str,
        quality_breakdown: Dict[str, float],
        key_data_points: List[str],
        quality_score: float
    ) -> QualityAnalysisJudgment:
        """Analyze analysis quality issues and suggest improvements"""
        
        # Identify weak components
        weak_components = {k: v for k, v in quality_breakdown.items() if v < 0.5}
        
        # Load prompt from external file
        prompt_file = Path(__file__).parent / "prompts" / "cmo" / "quality" / "analyze_issues.txt"
        prompt_template = prompt_file.read_text()
        
        # Format the prompt with actual values
        prompt = prompt_template.format(
            query=query,
            quality_score=quality_score,
            quality_breakdown=json.dumps(quality_breakdown, indent=2),
            key_data_points=', '.join(key_data_points),
            approach_text=approach_text,
            weak_components=json.dumps(weak_components, indent=2)
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            # Extract JSON from response
            response_text = response.content[0].text.strip()
            
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)
                
            return QualityAnalysisJudgment(**result)
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse quality analysis response: {e}")
            logger.debug(f"Raw response: {response.content[0].text[:500]}...")
            
            # Fallback analysis
            return QualityAnalysisJudgment(
                prompt_file="backend/services/agents/cmo/prompts/1_initial_analysis.txt",
                issue_description=f"Analysis quality below threshold ({quality_score:.2f} < 0.80)",
                root_cause="Failed to comprehensively address all key data points",
                weak_components=weak_components,
                specific_improvements=[
                    "Add instruction: 'Ensure all key medical concepts mentioned in the query are addressed'",
                    "Add guidance: 'Provide more comprehensive analysis covering all relevant data points'"
                ],
                expected_impact="Improved coverage of medical concepts and data points",
                priority="high" if quality_score < 0.7 else "medium"
            )
    
    async def analyze_tool_usage_issues(
        self,
        query: str,
        tool_calls_made: int,
        tool_success_rate: float,
        tool_relevance_score: float,
        initial_data_gathered: Dict[str, Any]
    ) -> ToolUsageAnalysisJudgment:
        """Analyze tool usage issues and suggest improvements"""
        
        # Load prompt from external file
        prompt_file = Path(__file__).parent / "prompts" / "cmo" / "tool_usage" / "analyze_issues.txt"
        prompt_template = prompt_file.read_text()
        
        # Format the prompt with actual values
        prompt = prompt_template.format(
            query=query,
            tool_calls_made=tool_calls_made,
            tool_success_rate=tool_success_rate,
            tool_relevance_score=tool_relevance_score,
            initial_data_gathered=json.dumps(initial_data_gathered, indent=2)
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
            
            return ToolUsageAnalysisJudgment(**result)
        except Exception as e:
            logger.error(f"Failed to parse tool usage analysis: {e}")
            return ToolUsageAnalysisJudgment(
                issue_description=f"Tool usage below threshold (success rate: {tool_success_rate:.2f})",
                root_cause="Insufficient or ineffective tool usage",
                specific_improvements=["Ensure appropriate tools are called for data gathering"],
                priority="high" if tool_success_rate < 0.8 else "medium"
            )
    
    async def analyze_response_structure_issues(
        self,
        query: str,
        structure_errors: List[str],
        approach_text: str
    ) -> ResponseStructureAnalysisJudgment:
        """Analyze response structure issues and suggest improvements"""
        
        # Load prompt from external file
        prompt_file = Path(__file__).parent / "prompts" / "cmo" / "response_structure" / "analyze_issues.txt"
        prompt_template = prompt_file.read_text()
        
        # Format the prompt with actual values
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
            
            return ResponseStructureAnalysisJudgment(**result)
        except Exception as e:
            logger.error(f"Failed to parse structure analysis: {e}")
            return ResponseStructureAnalysisJudgment(
                issue_description="Response structure validation failed",
                structure_errors=structure_errors if structure_errors else ["Invalid XML format"],
                specific_improvements=["Ensure response follows XML format requirements"],
                priority="high"
            )
    
    async def analyze_test_failure_patterns(
        self,
        test_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze patterns in test failures to identify systemic issues"""
        
        failures = [r for r in test_results if not r.get('success', True) or 
                   not r.get('complexity_correct', True) or 
                   r.get('specialty_f1', 1.0) < 0.8 or
                   r.get('analysis_quality_score', 1.0) < 0.8 or
                   r.get('tool_success_rate', 1.0) < 0.9 or
                   not r.get('response_valid', True)]
        
        if not failures:
            return {
                "patterns": [],
                "recommendations": [],
                "systemic_issues": []
            }
        
        # Analyze patterns
        complexity_failures = [f for f in failures if not f.get('complexity_correct', True)]
        specialist_failures = [f for f in failures if f.get('specialty_f1', 1.0) < 0.8]
        quality_failures = [f for f in failures if f.get('analysis_quality_score', 1.0) < 0.8]
        tool_failures = [f for f in failures if f.get('tool_success_rate', 1.0) < 0.9]
        structure_failures = [f for f in failures if not f.get('response_valid', True)]
        
        patterns = []
        if len(complexity_failures) > len(failures) * 0.3:
            patterns.append({
                "type": "complexity_classification",
                "frequency": len(complexity_failures) / len(test_results),
                "details": "Systematic issues with complexity classification"
            })
        
        if len(specialist_failures) > len(failures) * 0.3:
            patterns.append({
                "type": "specialist_selection",
                "frequency": len(specialist_failures) / len(test_results),
                "details": "Systematic issues with specialist selection"
            })
        
        if len(quality_failures) > len(failures) * 0.3:
            patterns.append({
                "type": "analysis_quality",
                "frequency": len(quality_failures) / len(test_results),
                "details": "Systematic issues with analysis comprehensiveness"
            })
        
        if len(tool_failures) > len(failures) * 0.3:
            patterns.append({
                "type": "tool_usage",
                "frequency": len(tool_failures) / len(test_results),
                "details": "Systematic issues with tool usage effectiveness"
            })
        
        if len(structure_failures) > len(failures) * 0.3:
            patterns.append({
                "type": "response_structure",
                "frequency": len(structure_failures) / len(test_results),
                "details": "Systematic issues with response structure validation"
            })
        
        # Generate recommendations
        recommendations = []
        if patterns:
            for pattern in patterns:
                if pattern["type"] == "complexity_classification":
                    recommendations.append({
                        "area": "Complexity Classification Prompt",
                        "action": "Review and clarify complexity boundaries",
                        "priority": "high",
                        "prompt_file": "backend/services/agents/cmo/prompts/1_initial_analysis.txt"
                    })
                elif pattern["type"] == "specialist_selection":
                    recommendations.append({
                        "area": "Specialist Selection Prompt",
                        "action": "Add more examples of specialist combinations",
                        "priority": "high",
                        "prompt_file": "backend/services/agents/cmo/prompts/3_task_creation.txt"
                    })
                elif pattern["type"] == "analysis_quality":
                    recommendations.append({
                        "area": "Analysis Quality Prompt",
                        "action": "Emphasize comprehensive coverage of all key data points",
                        "priority": "high",
                        "prompt_file": "backend/services/agents/cmo/prompts/1_initial_analysis.txt"
                    })
                elif pattern["type"] == "tool_usage":
                    recommendations.append({
                        "area": "Tool Usage Prompt",
                        "action": "Provide clearer guidance on when and how to use tools",
                        "priority": "medium",
                        "prompt_file": "backend/services/agents/cmo/prompts/1_initial_analysis.txt"
                    })
                elif pattern["type"] == "response_structure":
                    recommendations.append({
                        "area": "Response Format Prompt",
                        "action": "Strengthen XML format requirements and examples",
                        "priority": "high",
                        "prompt_file": "backend/services/agents/cmo/prompts/1_initial_analysis.txt"
                    })
        
        return {
            "patterns": patterns,
            "recommendations": recommendations,
            "systemic_issues": [p["details"] for p in patterns]
        }
    
    async def generate_prompt_improvement_report(
        self,
        evaluation_results: Dict[str, Any]
    ) -> str:
        """Generate a comprehensive report with prompt improvement recommendations"""
        
        report = []
        report.append("# Prompt Improvement Recommendations Report\n")
        report.append(f"Based on evaluation results from {evaluation_results.get('timestamp', 'N/A')}\n")
        
        # Analyze individual failures
        if "individual_results" in evaluation_results:
            complexity_mismatches = []
            specialist_issues = []
            quality_issues = []
            tool_issues = []
            structure_issues = []
            
            for result in evaluation_results["individual_results"]:
                if not result.get("complexity_correct", True):
                    complexity_mismatches.append(result)
                if result.get("specialty_f1", 1.0) < 0.8:
                    specialist_issues.append(result)
                if result.get("analysis_quality_score", 1.0) < 0.8:
                    quality_issues.append(result)
                if result.get("tool_success_rate", 1.0) < 0.9:
                    tool_issues.append(result)
                if not result.get("response_valid", True):
                    structure_issues.append(result)
            
            if complexity_mismatches:
                report.append("\n## Complexity Classification Issues\n")
                for mismatch in complexity_mismatches[:3]:  # Analyze top 3
                    report.append(f"\n### Test Case: {mismatch['test_case_id']}")
                    report.append(f"- Expected: {mismatch['expected_complexity']}")
                    report.append(f"- Actual: {mismatch['actual_complexity']}")
                    report.append(f"- Query: {mismatch['query'][:100]}...")
                    
                    # Use LLM Judge analysis if available
                    if "complexity_analysis" in mismatch:
                        analysis = mismatch["complexity_analysis"]
                        report.append(f"\n**LLM Judge Analysis**:")
                        report.append(f"- Issue: {analysis.get('issue_description', 'N/A')}")
                        report.append(f"- Prompt File: `{analysis.get('prompt_file', 'N/A')}`")
                        report.append("- Specific Changes:")
                        for change in analysis.get('specific_changes', []):
                            report.append(f"  - {change}")
                    else:
                        # Fallback recommendation
                        report.append("\n**Recommendation**: ")
                        if "complex" in mismatch["actual_complexity"].lower() and "standard" in mismatch["expected_complexity"].lower():
                            report.append("The CMO over-classified this query. Consider adjusting the prompt to:")
                            report.append("- Clarify that trend analysis alone doesn't make a query complex")
                            report.append("- Emphasize that 2-3 specialists is typically STANDARD complexity")
                        elif "standard" in mismatch["actual_complexity"].lower() and "complex" in mismatch["expected_complexity"].lower():
                            report.append("The CMO under-classified this query. Consider adjusting the prompt to:")
                            report.append("- Highlight that medication correlation analysis increases complexity")
                            report.append("- Clarify that 4+ specialists typically indicates COMPLEX")
            
            if specialist_issues:
                report.append("\n## Specialist Selection Issues\n")
                for issue in specialist_issues[:3]:
                    report.append(f"\n### Test Case: {issue['test_case_id']}")
                    report.append(f"- F1 Score: {issue.get('specialty_f1', 0):.2f}")
                    report.append(f"- Expected: {issue['expected_specialties']}")
                    report.append(f"- Actual: {issue['actual_specialties']}")
                    
                    # Use LLM Judge analysis if available
                    if "specialist_analysis" in issue:
                        analysis = issue["specialist_analysis"]
                        report.append(f"\n**LLM Judge Analysis**:")
                        report.append(f"- Issue: {analysis.get('issue_description', 'N/A')}")
                        report.append(f"- Prompt File: `{analysis.get('prompt_file', 'N/A')}`")
                        
                        # Missing specialists reasons
                        if analysis.get('missing_specialists_reason'):
                            report.append("- Missing Specialists:")
                            for spec, reason in analysis['missing_specialists_reason'].items():
                                report.append(f"  - {spec}: {reason}")
                        
                        # Specific changes
                        report.append("- Specific Changes:")
                        for change in analysis.get('specific_changes', []):
                            report.append(f"  - {change}")
                    else:
                        report.append("\n**Recommendation**: Review specialist selection criteria in task creation prompt")
            
            if quality_issues:
                report.append("\n## Analysis Quality Issues\n")
                report.append(f"Found {len(quality_issues)} test cases with quality below threshold (0.80)")
                for issue in quality_issues[:3]:
                    report.append(f"\n### Test Case: {issue['test_case_id']}")
                    report.append(f"- Quality Score: {issue.get('analysis_quality_score', 0):.2f}")
                    if 'quality_analysis' in issue:
                        qa = issue['quality_analysis']
                        report.append(f"\n**LLM Judge Analysis**:")
                        report.append(f"- Root Cause: {qa['root_cause']}")
                        report.append(f"- Prompt File: `{qa.get('prompt_file', 'N/A')}`")
                        report.append("- Recommendations:")
                        for rec in qa.get('specific_improvements', []):
                            report.append(f"  - {rec}")
            
            if tool_issues:
                report.append("\n## Tool Usage Issues\n")
                for issue in tool_issues[:3]:
                    report.append(f"\n### Test Case: {issue['test_case_id']}")
                    report.append(f"- Tool Success Rate: {issue.get('tool_success_rate', 0):.2f}")
                    report.append(f"- Tool Calls Made: {issue.get('tool_calls_made', 0)}")
            
            if structure_issues:
                report.append("\n## Response Structure Issues\n")
                for issue in structure_issues[:3]:
                    report.append(f"\n### Test Case: {issue['test_case_id']}")
                    report.append(f"- Structure Valid: False")
                    if issue.get('structure_errors'):
                        report.append(f"- Errors: {', '.join(issue['structure_errors'][:3])}")
        
        # Add pattern analysis
        pattern_analysis = await self.analyze_test_failure_patterns(
            evaluation_results.get("individual_results", [])
        )
        
        if pattern_analysis["patterns"]:
            report.append("\n## Systemic Issues Identified\n")
            for pattern in pattern_analysis["patterns"]:
                report.append(f"- **{pattern['type']}**: {pattern['details']} (affects {pattern['frequency']:.1%} of tests)")
        
        if pattern_analysis["recommendations"]:
            report.append("\n## Priority Actions\n")
            for rec in pattern_analysis["recommendations"]:
                report.append(f"- **{rec['priority'].upper()}**: {rec['action']} in {rec['area']}")
                if rec.get('prompt_file'):
                    report.append(f"  - File: `{rec['prompt_file']}`")
        
        # Collect all mentioned prompt files from individual analyses
        prompt_files_to_review = {}
        
        # Check individual results for prompt file recommendations
        if "individual_results" in evaluation_results:
            for result in evaluation_results["individual_results"]:
                # From complexity analysis
                if "complexity_analysis" in result:
                    pf = result["complexity_analysis"].get("prompt_file")
                    if pf:
                        if pf not in prompt_files_to_review:
                            prompt_files_to_review[pf] = []
                        prompt_files_to_review[pf].append("Complexity classification")
                
                # From specialist analysis
                if "specialist_analysis" in result:
                    pf = result["specialist_analysis"].get("prompt_file")
                    if pf:
                        if pf not in prompt_files_to_review:
                            prompt_files_to_review[pf] = []
                        prompt_files_to_review[pf].append("Specialist selection")
                
                # From quality analysis
                if "quality_analysis" in result:
                    pf = result["quality_analysis"].get("prompt_file")
                    if pf:
                        if pf not in prompt_files_to_review:
                            prompt_files_to_review[pf] = []
                        prompt_files_to_review[pf].append("Analysis quality")
        
        report.append("\n## Prompt Files to Review\n")
        report.append("Based on the evaluation results, consider reviewing these prompts:")
        
        if prompt_files_to_review:
            for i, (pf, issues) in enumerate(prompt_files_to_review.items(), 1):
                unique_issues = list(set(issues))
                report.append(f"{i}. `{pf}` - {', '.join(unique_issues)}")
        else:
            # Fallback to default recommendations
            report.append("1. `backend/services/agents/cmo/prompts/1_initial_analysis.txt` - Complexity classification & analysis quality")
            report.append("2. `backend/services/agents/cmo/prompts/3_task_creation.txt` - Specialist selection & task delegation")
            report.append("3. `backend/services/agents/cmo/prompts/2_initial_analysis_summarize.txt` - Synthesis of findings")
        
        return "\n".join(report)


class SpecialistSimilarityScorer:
    """Enhanced specialist similarity scoring that considers medical domain knowledge"""
    
    # Define specialist equivalence groups
    SPECIALIST_GROUPS = {
        "primary_care": ["general_practice", "family_medicine", "internal_medicine"],
        "metabolic": ["endocrinology", "diabetes_care", "metabolic_medicine"],
        "heart": ["cardiology", "cardiovascular", "cardiac_care"],
        "lab": ["laboratory_medicine", "pathology", "clinical_laboratory"],
        "prevention": ["preventive_medicine", "wellness", "health_screening"]
    }
    
    # Define specialist relationships (can work together or substitute)
    RELATED_SPECIALISTS = {
        "general_practice": ["internal_medicine", "family_medicine"],
        "endocrinology": ["diabetes_care", "metabolic_medicine", "internal_medicine"],
        "cardiology": ["internal_medicine", "preventive_medicine"],
        "nutrition": ["endocrinology", "preventive_medicine", "wellness"],
        "pharmacy": ["clinical_pharmacy", "medication_management"]
    }
    
    @classmethod
    def calculate_similarity(
        cls,
        predicted: List[str],
        actual: List[str]
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate sophisticated similarity score between specialist sets"""
        
        predicted_set = set(predicted)
        actual_set = set(actual)
        
        # Direct matches
        exact_matches = predicted_set & actual_set
        
        # Find equivalent specialists
        equivalent_matches = set()
        substitutions = {}
        
        for pred in predicted_set - exact_matches:
            for act in actual_set - exact_matches:
                # Check if they're in the same group
                for group, members in cls.SPECIALIST_GROUPS.items():
                    if pred in members and act in members:
                        equivalent_matches.add(pred)
                        substitutions[pred] = act
                        break
                
                # Check if they're related
                if pred in cls.RELATED_SPECIALISTS:
                    if act in cls.RELATED_SPECIALISTS[pred]:
                        equivalent_matches.add(pred)
                        substitutions[pred] = act
                        break
        
        # Calculate scores
        total_matches = len(exact_matches) + len(equivalent_matches)
        union_size = len(predicted_set | actual_set)
        
        # Weighted score (exact matches worth more)
        weighted_score = (len(exact_matches) + 0.8 * len(equivalent_matches)) / union_size if union_size > 0 else 0
        
        # Check for critical missing specialists
        missing = actual_set - predicted_set
        missing_critical = [s for s in missing if s not in substitutions.values()]
        
        return weighted_score, {
            "exact_matches": list(exact_matches),
            "equivalent_matches": substitutions,
            "missing_critical": missing_critical,
            "extra_specialists": list(predicted_set - actual_set - set(substitutions.keys())),
            "is_acceptable": weighted_score >= 0.7 and len(missing_critical) <= 1
        }