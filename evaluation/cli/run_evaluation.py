"""
Multi-Agent Evaluation Runner

Script to run comprehensive evaluation of different agents in the multi-agent health system.
Supports evaluation of CMO, specialist agents, and full system evaluation.
"""

import asyncio
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import sys
import os

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../../backend"))

from anthropic import Anthropic
from dotenv import load_dotenv

# Import agent implementations
from services.agents.cmo.cmo_agent import CMOAgent
from services.agents.specialist.specialist_agent import SpecialistAgent
from services.agents.models import MedicalSpecialty
from tools.tool_registry import ToolRegistry

# Import evaluators
from evaluation.framework.evaluators import BaseEvaluator
from evaluation.agents.cmo import CMOEvaluator
from evaluation.agents.specialist import SpecialistEvaluator

# Import test cases
from evaluation.agents.cmo.test_cases import CMOTestCases
from evaluation.agents.specialist import SpecialistTestCases

# Import other evaluation components
from evaluation.framework.report_generator import DynamicHTMLReportGenerator
from evaluation.framework.llm_judge import LLMTestJudge, SpecialistSimilarityScorer
from evaluation.utils import setup_evaluation_logging

# Load environment variables
# Try to load from multiple locations with absolute paths
current_dir = Path(__file__).parent.parent.parent
load_dotenv(current_dir / '.env')  # Project root
load_dotenv(current_dir / 'backend' / '.env')  # Backend directory
load_dotenv(current_dir / 'evaluation' / '.env')  # Evaluation directory

# Setup initial logging without file output (will be updated per test run)
log_level = os.getenv("LOG_LEVEL", "INFO")
setup_evaluation_logging(log_level=log_level, log_to_file=False)
logger = logging.getLogger(__name__)


def _print_evaluation_summary(results: Dict[str, Any], test_dir: Path, agent_type: str, test_type: str):
    """Print comprehensive evaluation summary with file tree"""
    summary = results.get("summary", {})
    
    print("\n" + "="*80)
    print(f"EVALUATION SUMMARY - {agent_type.upper()} Agent")
    print(f"Test Type: {test_type}")
    print("="*80)
    
    # Overall result
    overall_result = "PASS" if summary.get("overall_success", False) else "FAIL"
    overall_score = summary.get("success_rate", 0.0) * 100
    print(f"\nOverall Result: {overall_result}")
    print(f"Overall Score: {overall_score:.1f}% (Target: 75.0%)")
    
    # Failed dimensions
    if not summary.get("overall_success", False):
        print("\nFailed Dimensions:")
        # Calculate failed dimensions from results
        dimension_scores = {}
        dimension_targets = {
            'complexity_classification': 0.90,
            'specialty_selection': 0.85,
            'analysis_quality': 0.80,
            'tool_usage': 0.90,
            'response_structure': 0.95
        }
        
        for result in results.get("results", []):
            for dim in dimension_targets:
                if dim not in dimension_scores:
                    dimension_scores[dim] = []
                
                if dim == 'complexity_classification':
                    dimension_scores[dim].append(1.0 if result.get('complexity_correct', False) else 0.0)
                elif dim == 'specialty_selection':
                    dimension_scores[dim].append(result.get('specialty_f1', 0.0))
                elif dim == 'analysis_quality':
                    dimension_scores[dim].append(result.get('analysis_quality_score', 0.0))
                elif dim == 'tool_usage':
                    dimension_scores[dim].append(result.get('tool_success_rate', 0.0))
                elif dim == 'response_structure':
                    dimension_scores[dim].append(1.0 if result.get('response_valid', False) else 0.0)
        
        for dim, scores in dimension_scores.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                target = dimension_targets[dim]
                if avg_score < target:
                    print(f"  - {dim.replace('_', ' ').title()}: {avg_score:.2f} (Target: {target:.2f})")
    
    # Recommendations
    print("\nRecommendations for Improvement:")
    if overall_score < 75.0:
        print("  1. Review failed test cases in the HTML report")
        print("  2. Analyze LLM Judge feedback for quality improvements")
        print("  3. Consider prompt refinements based on failure patterns")
    else:
        print("  ✓ All performance targets met!")
    
    # Test output assets
    print("\n" + "="*80)
    print("TEST OUTPUT ASSETS CREATED")
    print("="*80)
    print(f"\nTest Directory: {test_dir.absolute()}")
    print("\nFile Structure:")
    
    # Build file tree
    def print_tree(path, prefix="", is_last=True):
        """Print directory tree"""
        if path.name.startswith('.'):
            return
            
        # Determine icon
        if path.is_dir():
            icon = "📁"
        elif path.suffix == '.json':
            icon = "📄"
        elif path.suffix == '.html':
            icon = "📊"
        elif path.suffix == '.png':
            icon = "📈"
        elif path.suffix == '.log':
            icon = "📜"
        else:
            icon = "📄"
        
        # Print current item
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{icon} {path.name}", end="")
        
        # Add description for known files
        descriptions = {
            "results.json": "Complete evaluation results with metrics",
            "evaluation.log": "Detailed execution logs",
            "report.html": "Interactive HTML report with visualizations",
            "raw_results.json": "Raw evaluation data for analysis",
            "dimension_scores.png": "Bar chart comparing actual vs target scores",
            "complexity_performance.png": "Performance metrics by query complexity",
            "response_time_distribution.png": "Histogram of response times",
            "specialty_heatmap.png": "Co-occurrence matrix of specialist selections"
        }
        
        if path.name in descriptions:
            print(f" - {descriptions[path.name]}")
        else:
            print()
        
        # Recurse for directories
        if path.is_dir():
            extension = "    " if is_last else "│   "
            children = sorted(list(path.iterdir()))
            for i, child in enumerate(children):
                print_tree(child, prefix + extension, i == len(children) - 1)
    
    print_tree(test_dir)
    
    print("\n" + "="*80)
    print("📊 Full report with visualizations available at:")
    print(f"   {test_dir.absolute()}/report/report.html")
    print("\n📁 Raw results saved to:")
    print(f"   {test_dir.absolute()}/results.json")
    print("="*80 + "\n")


class EvaluationRunner:
    """Manages the evaluation process for different agents with integrated LLM Judge"""
    
    def __init__(self):
        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.anthropic_client = Anthropic(api_key=api_key)
        
        # Initialize tool registry
        self.tool_registry = ToolRegistry()
        
        # Initialize LLM Judge for enhanced analysis
        self.llm_judge = LLMTestJudge(
            anthropic_client=self.anthropic_client,
            model="claude-3-sonnet-20240229"  # Use Sonnet for detailed analysis
        )
        
        # Map of agent types to their evaluators
        self.evaluator_map = {
            "cmo": self._create_cmo_evaluator,
            "specialist": self._create_specialist_evaluator
        }
        
        # Map of agent types to test cases
        self.test_case_map = {
            "cmo": CMOTestCases,
            "specialist": SpecialistTestCases
        }
    
    def _create_cmo_evaluator(self) -> CMOEvaluator:
        """Create CMO evaluator"""
        cmo_agent = CMOAgent(
            anthropic_client=self.anthropic_client,
            tool_registry=self.tool_registry,
            model="claude-3-opus-20240229",  # Use Opus for evaluation
            max_tokens_analysis=3000,  # Reduced for Opus limit
            max_tokens_planning=4000   # Reduced for Opus limit (max 4096)
        )
        return CMOEvaluator(cmo_agent, self.anthropic_client)
    
    def _create_specialist_evaluator(self) -> SpecialistEvaluator:
        """Create generic specialist evaluator"""
        # Initialize specialist agent - specialty will be determined by test cases
        specialist_agent = SpecialistAgent(
            anthropic_client=self.anthropic_client,
            tool_registry=self.tool_registry,
            model="claude-3-opus-20240229",  # Use Opus for evaluation
            max_tokens=3500  # Reduced for Opus limit
        )
        return SpecialistEvaluator(specialist_agent, MedicalSpecialty.CARDIOLOGY, self.anthropic_client)
    
    def _create_specialist_evaluator_for_specialty(self, specialty: str) -> SpecialistEvaluator:
        """Create specialist evaluator for specific specialty"""
        specialist_agent = SpecialistAgent(
            anthropic_client=self.anthropic_client,
            tool_registry=self.tool_registry,
            model="claude-3-opus-20240229",  # Use Opus for evaluation
            max_tokens=3500  # Reduced for Opus limit
        )
        medical_specialty = MedicalSpecialty(specialty)
        return SpecialistEvaluator(specialist_agent, medical_specialty, self.anthropic_client)
    
    def get_test_cases(self, agent_type: str, test_type: str, category: Optional[str] = None, specialty: Optional[str] = None) -> List[Any]:
        """Get test cases for specified agent and test type"""
        
        if agent_type not in self.test_case_map:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        test_cases_class = self.test_case_map[agent_type]
        
        # CMO test cases
        if agent_type == "cmo":
            if test_type == "example":
                return [test_cases_class.get_simple_queries()[0]]
            elif test_type == "complexity":
                return test_cases_class.get_complexity_test_suite()
            elif test_type == "specialty":
                return test_cases_class.get_specialty_test_suite()
            elif test_type == "comprehensive":
                return test_cases_class.get_comprehensive_test_suite()
            elif test_type == "real-world":
                return test_cases_class.get_real_world_test_suite()
            elif test_type == "all":
                return test_cases_class.get_all_test_cases()
            
        # Specialist test cases
        elif agent_type == "specialist":
            # Handle specialty-specific filtering first
            if specialty:
                medical_specialty = MedicalSpecialty(specialty)
                if test_type == "example":
                    specialty_cases = test_cases_class.get_test_cases_by_specialty(medical_specialty)
                    return specialty_cases[:1] if specialty_cases else []
                elif test_type == "comprehensive":
                    return test_cases_class.get_test_cases_by_specialty(medical_specialty)
                elif test_type == "real-world":
                    all_cases = test_cases_class.get_test_cases_by_specialty(medical_specialty)
                    return [case for case in all_cases if case.based_on_real_case]
                elif test_type == "all":
                    return test_cases_class.get_test_cases_by_specialty(medical_specialty)
            else:
                # No specialty specified, use general logic
                if test_type == "example":
                    return test_cases_class.get_cardiology_lipid_trend_cases()[:1]
                elif test_type == "comprehensive":
                    return test_cases_class.get_comprehensive_test_suite()
                elif test_type == "real-world":
                    return test_cases_class.get_real_world_test_suite()
                elif test_type == "all":
                    return test_cases_class.get_all_test_cases()
                # Support for specialty-specific filtering via test_type
                elif test_type in ["cardiology", "endocrinology", "pharmacy", "nutrition", "laboratory_medicine", "preventive_medicine", "data_analysis", "general_practice"]:
                    # Parse specialty from test_type
                    medical_specialty = MedicalSpecialty(test_type)
                    return test_cases_class.get_test_cases_by_specialty(medical_specialty)
                elif test_type == "category" and category:
                    return test_cases_class.get_test_cases_by_category(category)
                elif test_type == "urgency" and category:
                    return test_cases_class.get_test_cases_by_urgency(category)
        
        return []
    
    async def run_evaluation(
        self, 
        agent_type: str,
        test_type: str,
        max_concurrent: int = 5,
        test_ids: Optional[List[str]] = None,
        category: Optional[str] = None,
        specialty: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run evaluation for specified agent type"""
        
        # Create evaluator
        if agent_type not in self.evaluator_map:
            raise ValueError(f"Unknown agent type: {agent_type}. Available: {list(self.evaluator_map.keys())}")
        
        # For specialist agent, use the specialty parameter to create the right evaluator
        if agent_type == "specialist" and specialty:
            evaluator = self._create_specialist_evaluator_for_specialty(specialty)
        else:
            evaluator = self.evaluator_map[agent_type]()
        
        # Get test cases
        test_cases = self.get_test_cases(agent_type, test_type, category, specialty)
        
        if not test_cases:
            logger.warning(f"No test cases found for agent={agent_type}, test={test_type}, category={category}")
            return {"error": "No test cases found"}
        
        # Filter by test IDs if specified
        if test_ids:
            test_ids_set = set(test_ids)
            test_cases = [tc for tc in test_cases if tc.id in test_ids_set]
            logger.info(f"Filtered to {len(test_cases)} test cases by ID")
        
        # Print test case preview for real-world tests
        if test_type == "real-world":
            print(f"\n📋 Real-World Based Test Cases ({len(test_cases)} tests):")
            print("="*80)
            for i, tc in enumerate(test_cases):
                print(f"\n{i+1}. Test ID: {tc.id}")
                print(f"   Query: {tc.query[:100]}..." if len(tc.query) > 100 else f"   Query: {tc.query}")
                print(f"   Expected Complexity: {tc.expected_complexity}")
                print(f"   Expected Specialists: {', '.join(sorted(tc.expected_specialties))}")
                if hasattr(tc, 'notes') and tc.notes:
                    print(f"   Notes: {tc.notes}")
            print("="*80 + "\n")
        
        logger.info(f"Running {len(test_cases)} test cases for {agent_type} agent...")
        
        # Run evaluation
        results = await evaluator.evaluate_test_suite(
            test_cases=test_cases,
            max_concurrent=max_concurrent
        )
        
        # Add metadata
        results["agent_type"] = agent_type
        results["test_type"] = test_type
        results["category"] = category
        
        # Enhance results with LLM Judge analysis for failures
        if results.get("results"):
            results = await self.enhance_with_llm_judge_analysis(results, agent_type)
        
        return results
    
    async def enhance_with_llm_judge_analysis(self, evaluation_result: Dict[str, Any], agent_type: str) -> Dict[str, Any]:
        """Add LLM Judge analysis for failed dimensions"""
        enhanced_results = []
        
        for result in evaluation_result.get("results", []):
            enhanced_result = result.copy()
            
            # Analyze failures based on agent type
            if agent_type == "cmo":
                enhanced_result = await self._enhance_cmo_result(enhanced_result)
            elif agent_type == "specialist":
                enhanced_result = await self._enhance_specialist_result(enhanced_result)
            
            enhanced_results.append(enhanced_result)
        
        evaluation_result["results"] = enhanced_results
        return evaluation_result
    
    async def _enhance_cmo_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance CMO evaluation result with LLM Judge analysis"""
        # Analyze complexity failures
        if not result.get("complexity_correct", True):
            complexity_analysis = await self.llm_judge.analyze_complexity_mismatch(
                test_case=result,  # Pass the full result as test_case
                actual_complexity=result.get("actual_complexity", "Unknown"),
                expected_complexity=result["expected_complexity"],
                approach_text=result.get("approach_text", "")
            )
            if complexity_analysis:
                result["complexity_analysis"] = complexity_analysis if isinstance(complexity_analysis, dict) else complexity_analysis.__dict__
        
        # Analyze specialist selection failures
        if result.get("specialty_f1", 1.0) < 0.8:
            # Get the actual and expected specialists - they may be sets or string representations
            actual_spec = result.get("actual_specialties", set())
            expected_spec = result.get("expected_specialties", set())
            
            # Convert to lists if they're sets
            if isinstance(actual_spec, set):
                actual_specialists = list(actual_spec)
                expected_specialists = list(expected_spec)
            else:
                # They're string representations, parse them
                import ast
                try:
                    actual_specialists = list(ast.literal_eval(actual_spec))
                    expected_specialists = list(ast.literal_eval(expected_spec))
                except:
                    # Fallback parsing if ast.literal_eval fails
                    actual_specialists = actual_spec.strip("{}").replace("'", "").split(", ") if actual_spec else []
                    expected_specialists = expected_spec.strip("{}").replace("'", "").split(", ") if expected_spec else []
            
            # Calculate missing critical specialists
            missing_critical = list(set(expected_specialists) - set(actual_specialists))
            
            specialist_analysis = await self.llm_judge.analyze_specialist_mismatch(
                test_case=result,
                actual_specialists=actual_specialists,
                expected_specialists=expected_specialists,
                approach_text=result.get("approach_text", ""),
                f1_score=result.get("specialty_f1", 0.0),
                missing_critical=missing_critical
            )
            if specialist_analysis:
                result["specialist_analysis"] = specialist_analysis if isinstance(specialist_analysis, dict) else specialist_analysis.__dict__
        
        # Analyze quality failures
        if result.get("analysis_quality_score", 1.0) < 0.8:
            quality_analysis = await self.llm_judge.analyze_quality_issues(
                query=result["query"],
                approach_text=result.get("approach_text", ""),
                quality_breakdown=result.get("quality_breakdown", {}),
                key_data_points=result.get("key_data_points", []),
                quality_score=result.get("analysis_quality_score", 0)
            )
            if quality_analysis:
                result["quality_analysis"] = quality_analysis if isinstance(quality_analysis, dict) else quality_analysis.__dict__
        
        # Add other dimension analyses as needed...
        
        return result
    
    async def _enhance_specialist_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance specialist evaluation result with LLM Judge analysis"""
        # Add specialist-specific LLM Judge analysis
        # This would use the specialist prompts we created
        return result
    
    def create_test_directory(self, agent_type: str, test_type: str) -> Path:
        """Create directory for test run outputs"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_name = f"{agent_type}-{test_type}_{timestamp}"
        test_dir = Path("evaluation/test_runs") / test_name
        test_dir.mkdir(parents=True, exist_ok=True)
        return test_dir


async def main():
    """Main entry point for evaluation runner"""
    parser = argparse.ArgumentParser(description="Run multi-agent evaluation")
    
    # Agent selection
    parser.add_argument(
        "--agent",
        type=str,
        default="cmo",
        choices=["cmo", "specialist"],
        help="Agent type to evaluate"
    )
    
    # Test type selection
    parser.add_argument(
        "--test",
        type=str,
        default="example",
        help="Type of test to run (depends on agent type)"
    )
    
    # Additional options
    parser.add_argument(
        "--specialty",
        type=str,
        help="Medical specialty (for specialist agent)",
        choices=["cardiology", "endocrinology", "pharmacy", "nutrition", "laboratory_medicine", "preventive_medicine", "data_analysis", "general_practice"]
    )
    
    parser.add_argument(
        "--category",
        type=str,
        help="Test category (for category-based tests)"
    )
    
    parser.add_argument(
        "--test-ids",
        type=str,
        help="Comma-separated list of specific test IDs to run"
    )
    
    parser.add_argument(
        "--concurrent",
        type=int,
        default=5,
        help="Maximum concurrent test executions"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for results (default: stdout)"
    )
    
    args = parser.parse_args()
    
    # Parse test IDs if provided
    test_ids = None
    if args.test_ids:
        test_ids = [tid.strip() for tid in args.test_ids.split(",")]
    
    # Initialize runner
    runner = EvaluationRunner()
    
    # Create test directory
    test_dir = runner.create_test_directory(args.agent, args.test)
    
    # Setup logging for this test run
    setup_evaluation_logging(log_level=log_level, log_to_file=True, log_dir=test_dir)
    
    logger.info(f"Starting {args.agent} agent evaluation")
    logger.info(f"Test type: {args.test}")
    logger.info(f"Test directory: {test_dir}")
    
    try:
        # Run evaluation
        results = await runner.run_evaluation(
            agent_type=args.agent,
            test_type=args.test,
            max_concurrent=args.concurrent,
            test_ids=test_ids,
            category=args.category,
            specialty=args.specialty
        )
        
        # Save results
        results_file = test_dir / "results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results saved to: {results_file}")
        
        # Generate report
        if results.get("results"):
            # Add agent type to results for dynamic report generation
            results['agent_type'] = args.agent
            report_generator = DynamicHTMLReportGenerator(test_dir, args.agent)
            report_path = report_generator.generate_html_report(results)
            logger.info(f"Report generated at: {report_path}")
        
        # Generate comprehensive summary
        _print_evaluation_summary(results, test_dir, args.agent, args.test)
        
        # Output summary
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results.get("summary", {}), f, indent=2)
        else:
            print(json.dumps(results.get("summary", {}), indent=2))
        
        # Return appropriate exit code
        return 0 if results.get("overall_success", False) else 1
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)