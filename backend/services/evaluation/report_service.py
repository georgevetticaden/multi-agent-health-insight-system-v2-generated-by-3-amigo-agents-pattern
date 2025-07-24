"""
Report Generation Service for QE Agent Evaluations

This service generates the same comprehensive HTML reports as the CLI evaluator,
including visualizations, failure analysis, and detailed dimension breakdowns.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys

logger = logging.getLogger(__name__)

# Set up paths exactly like the CLI evaluation does
import os

# Add project root FIRST to find the correct evaluation module  
# From backend/services/evaluation/report_service.py: ../../../ gets to project root
project_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, project_root)  # Insert at beginning to take priority

# Backend path for other imports
backend_path = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(backend_path)

from dotenv import load_dotenv

# Load environment variables from multiple locations
current_dir = Path(__file__).parent.parent.parent.parent  # Project root
load_dotenv(current_dir / '.env')  # Project root
load_dotenv(current_dir / 'backend' / '.env')  # Backend directory
load_dotenv(current_dir / 'evaluation' / '.env')  # Evaluation directory

# Set matplotlib to use non-interactive backend before importing
import matplotlib
matplotlib.use('Agg')

# Don't import at module level - defer until needed
REPORT_GENERATOR_AVAILABLE = None
DynamicHTMLReportGenerator = None


class ReportService:
    """
    Service to generate comprehensive evaluation reports from QE Agent test cases.
    
    This generates the same detailed HTML reports as the CLI evaluator, including:
    - Executive summary with overall scores
    - Dimension breakdowns with visualizations
    - Component-level scoring details
    - Failure analysis and recommendations
    - Test case details and metadata
    """
    
    def __init__(self):
        self.logger = logger
        # Use absolute path based on backend directory
        backend_dir = Path(__file__).parent.parent.parent
        self.base_report_dir = backend_dir / "evaluation_results" / "qe_reports"
        self.base_report_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"Report base directory: {self.base_report_dir}")
        logger.info(f"Report base directory exists: {self.base_report_dir.exists()}")
    
    def _ensure_report_generator(self):
        """Ensure the report generator is imported"""
        global REPORT_GENERATOR_AVAILABLE, DynamicHTMLReportGenerator
        
        if REPORT_GENERATOR_AVAILABLE is not None:
            return REPORT_GENERATOR_AVAILABLE
            
        # Save current backend paths to temporarily remove them
        backend_paths = [p for p in sys.path if p.endswith('/backend')]
        
        try:
            # Temporarily remove backend paths to avoid conflict
            for path in backend_paths:
                if path in sys.path:
                    sys.path.remove(path)
            
            # Clear evaluation from module cache if it's the wrong one
            if 'evaluation' in sys.modules and hasattr(sys.modules['evaluation'], '__file__'):
                if 'backend/evaluation' in sys.modules['evaluation'].__file__:
                    logger.info("Removing backend evaluation module from cache")
                    # Clear all evaluation submodules
                    to_remove = [k for k in sys.modules.keys() if k.startswith('evaluation.')]
                    for k in to_remove:
                        del sys.modules[k]
                    del sys.modules['evaluation']
            
            from evaluation.framework.report_generator.dynamic_report_generator import DynamicHTMLReportGenerator as DynamicGen
            DynamicHTMLReportGenerator = DynamicGen
            logger.info("Successfully imported DynamicHTMLReportGenerator from evaluation framework")
            REPORT_GENERATOR_AVAILABLE = True
            
        except ImportError as e:
            logger.error(f"Failed to import DynamicHTMLReportGenerator: {e}")
            logger.error(f"Current sys.path: {sys.path[:5]}")
            REPORT_GENERATOR_AVAILABLE = False
            DynamicHTMLReportGenerator = None
        finally:
            # Restore backend paths
            for path in backend_paths:
                if path not in sys.path:
                    sys.path.append(path)
        
        return REPORT_GENERATOR_AVAILABLE
    
    def generate_report_from_evaluation(
        self,
        evaluation_id: str,
        test_case: Dict[str, Any],
        evaluation_result: Dict[str, Any],
        agent_type: str = "cmo"
    ) -> str:
        """
        Generate a comprehensive HTML report from a QE Agent evaluation.
        
        Args:
            evaluation_id: Unique evaluation ID
            test_case: Test case data
            evaluation_result: Evaluation results from the evaluator
            agent_type: Type of agent evaluated
            
        Returns:
            Path to the generated report directory
        """
        logger.info(f"=== REPORT GENERATION START ===")
        logger.info(f"Evaluation ID: {evaluation_id}")
        logger.info(f"Test case ID: {test_case.get('id', 'unknown')}")
        logger.info(f"Agent type: {agent_type}")
        
        # Try to use unified storage if available
        test_run_dir = None
        try:
            from evaluation.data.config import EvaluationDataConfig
            run_dir = EvaluationDataConfig.find_run_dir(evaluation_id)
            if run_dir:
                test_run_dir = run_dir
                logger.info(f"Using unified storage for report: {test_run_dir}")
        except ImportError:
            pass
        
        if not test_run_dir:
            # Fallback to old directory structure
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_name = f"qe_{test_case.get('id', 'unknown')}_{timestamp}"
            test_run_dir = self.base_report_dir / test_name
            test_run_dir.mkdir(exist_ok=True, parents=True)
        
        logger.info(f"Created report directory: {test_run_dir}")
        
        # Save test case
        test_case_path = test_run_dir / "test_case.json"
        with open(test_case_path, 'w') as f:
            json.dump(test_case, f, indent=2)
        logger.info(f"Saved test case to: {test_case_path}")
        
        # Convert evaluation result to CLI format
        logger.info("Converting evaluation result to CLI format...")
        cli_format_results = self._convert_to_cli_format(
            test_case,
            evaluation_result,
            evaluation_id
        )
        logger.info(f"Converted results with {len(cli_format_results.get('results', []))} test case results")
        
        # Save raw results
        raw_results_path = test_run_dir / "evaluation_results.json"
        with open(raw_results_path, 'w') as f:
            json.dump(cli_format_results, f, indent=2, default=str)
        logger.info(f"Saved raw results to: {raw_results_path}")
        
        # Generate HTML report using the same generator as CLI
        try:
            # Ensure report generator is imported
            if not self._ensure_report_generator():
                raise ImportError("DynamicHTMLReportGenerator not available due to import error")
                
            logger.info(f"Initializing DynamicHTMLReportGenerator for agent type: {agent_type}")
            logger.info(f"Test run directory: {test_run_dir}")
            logger.info(f"Test run directory exists: {test_run_dir.exists()}")
            
            report_generator = DynamicHTMLReportGenerator(test_run_dir, agent_type)
            logger.info("✅ Successfully created DynamicHTMLReportGenerator instance")
            
            logger.info("Generating HTML report with full CLI-style features...")
            logger.info(f"CLI format results keys: {list(cli_format_results.keys())}")
            logger.info(f"Number of test results: {len(cli_format_results.get('results', []))}")
            
            # Use the real generator's method
            report_path = report_generator.generate_html_report(cli_format_results)
            logger.info(f"✅ Report generated successfully at: {report_path}")
            logger.info(f"Report path type: {type(report_path)}")
            logger.info(f"Report path exists: {Path(report_path).exists() if report_path else 'N/A'}")
            
            # Check if report subdirectory was created
            report_subdir = test_run_dir / "report"
            logger.info(f"Report subdirectory exists: {report_subdir.exists()}")
            if report_subdir.exists():
                logger.info(f"Report subdirectory contents: {list(report_subdir.iterdir())}")
            
            # Create a link file for easy access with HTTP URL
            link_path = test_run_dir / "report_link.txt"
            http_url = self.get_report_url(str(report_path))
            with open(link_path, 'w') as f:
                f.write(f"{http_url}\n")
            logger.info(f"Created report link file: {link_path} with URL: {http_url}")
            
            logger.info(f"=== REPORT GENERATION COMPLETE ===")
            # The generator returns the report directory, we need the parent test_run_dir
            return str(test_run_dir)
            
        except Exception as e:
            logger.error(f"❌ Failed to generate report: {e}", exc_info=True)
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception args: {e.args}")
            raise
    
    def _convert_to_cli_format(
        self,
        test_case: Dict[str, Any],
        evaluation_result: Dict[str, Any],
        evaluation_id: str
    ) -> Dict[str, Any]:
        """
        Convert QE Agent evaluation results to CLI evaluator format.
        
        The CLI evaluator expects results in a specific format with:
        - results: List of individual test case results
        - summary: Overall summary statistics
        - metadata: Test run metadata
        """
        # Extract dimension results
        dimension_results = evaluation_result.get("dimension_results", {})
        
        # Build individual result in CLI format
        individual_result = {
            "test_case_id": test_case.get("id"),
            "query": test_case.get("query"),
            "success": evaluation_result.get("overall_score", 0) >= 0.75,
            "weighted_score": evaluation_result.get("overall_score", 0),
            
            # Dimension scores
            "complexity_classification_score": dimension_results.get("complexity_classification", {}).get("score", 0),
            "specialty_selection_score": dimension_results.get("specialty_selection", {}).get("score", 0),
            "analysis_quality_score": dimension_results.get("analysis_quality", {}).get("score", 0),
            "tool_usage_score": dimension_results.get("tool_usage", {}).get("score", 0),
            "response_structure_score": dimension_results.get("response_structure", {}).get("score", 0),
            "cost_efficiency_score": dimension_results.get("cost_efficiency", {}).get("score", 0),
            
            # Component breakdowns
            "specialty_component_breakdown": dimension_results.get("specialty_selection", {}).get("components", {}),
            "analysis_quality_breakdown": dimension_results.get("analysis_quality", {}).get("components", {}),
            "tool_component_breakdown": dimension_results.get("tool_usage", {}).get("components", {}),
            "response_component_breakdown": dimension_results.get("response_structure", {}).get("components", {}),
            "cost_efficiency_breakdown": dimension_results.get("cost_efficiency", {}).get("components", {}),
            
            # Details
            "expected_complexity": test_case.get("expected_complexity"),
            "actual_complexity": dimension_results.get("complexity_classification", {}).get("details", {}).get("actual"),
            "complexity_correct": dimension_results.get("complexity_classification", {}).get("details", {}).get("correct", False),
            
            "expected_specialties": test_case.get("expected_specialties", []),
            "actual_specialties": dimension_results.get("specialty_selection", {}).get("details", {}).get("actual_specialties", []),
            "specialty_precision": dimension_results.get("specialty_selection", {}).get("components", {}).get("specialist_precision", 
                                  dimension_results.get("specialty_selection", {}).get("details", {}).get("precision", 0)),
            "specialty_recall": dimension_results.get("specialty_selection", {}).get("details", {}).get("recall", 0),
            "specialty_f1_score": dimension_results.get("specialty_selection", {}).get("score", 0),
            
            "tool_calls_made": dimension_results.get("tool_usage", {}).get("details", {}).get("tool_calls_made", 0),
            "tool_success_count": dimension_results.get("tool_usage", {}).get("details", {}).get("successful_tool_calls", 0),
            "tool_success_rate": dimension_results.get("tool_usage", {}).get("details", {}).get("success_rate", 0),
            
            "response_valid": dimension_results.get("response_structure", {}).get("details", {}).get("response_valid", True),
            "structure_errors": dimension_results.get("response_structure", {}).get("details", {}).get("structure_errors", []),
            
            # Cost efficiency details
            "expected_cost_threshold": test_case.get("expected_cost_threshold"),
            "actual_total_cost": dimension_results.get("cost_efficiency", {}).get("details", {}).get("actual_total_cost"),
            "tokens_used": dimension_results.get("cost_efficiency", {}).get("details", {}).get("tokens_used", 0),
            "cost_within_threshold": dimension_results.get("cost_efficiency", {}).get("details", {}).get("cost_within_threshold", False),
            
            # Metadata
            "response_time_ms": evaluation_result.get("execution_time_ms", 0),
            "approach_text": evaluation_result.get("metadata", {}).get("approach_text", ""),
            
            # Failure analysis (if available)
            "failure_analyses": evaluation_result.get("metadata", {}).get("failure_analyses", [])
        }
        
        # Calculate summary statistics  
        summary = {
            "total_tests": 1,
            "passed_tests": 1 if individual_result["success"] else 0,
            "failed_tests": 0 if individual_result["success"] else 1,
            "overall_success": individual_result["success"],
            "overall_success_rate": individual_result["weighted_score"],  # Use actual score, not pass/fail rate
            "weighted_average_score": individual_result["weighted_score"],
            "weighted_score": individual_result["weighted_score"],  # THIS is what the template looks for!
            "success_rate": individual_result["weighted_score"],  # Alternative field name
            "overall_score": individual_result["weighted_score"],  # Another common field name
            
            # Performance metrics (expected by template)
            "performance_metrics": {
                "avg_response_time_ms": individual_result["response_time_ms"],
                "min_response_time_ms": individual_result["response_time_ms"],
                "max_response_time_ms": individual_result["response_time_ms"],
                "total_execution_time_ms": individual_result["response_time_ms"]
            },
            
            # Dimension success rates
            "dimension_success_rates": {
                "complexity_classification": 1.0 if individual_result["complexity_correct"] else 0.0,
                "specialty_selection": 1.0 if individual_result["specialty_f1_score"] >= 0.85 else 0.0,
                "analysis_quality": 1.0 if individual_result["analysis_quality_score"] >= 0.80 else 0.0,
                "tool_usage": 1.0 if individual_result["tool_usage_score"] >= 0.90 else 0.0,
                "response_structure": 1.0 if individual_result["response_structure_score"] >= 0.95 else 0.0,
                "cost_efficiency": 1.0 if individual_result["cost_efficiency_score"] >= 0.80 else 0.0
            },
            
            # Average dimension scores
            "average_dimension_scores": {
                "complexity_classification": individual_result["complexity_classification_score"],
                "specialty_selection": individual_result["specialty_selection_score"],
                "analysis_quality": individual_result["analysis_quality_score"],
                "tool_usage": individual_result["tool_usage_score"],
                "response_structure": individual_result["response_structure_score"],
                "cost_efficiency": individual_result["cost_efficiency_score"]
            }
        }
        
        # Build the complete results structure
        cli_format_results = {
            "test_type": "qe-generated",
            "agent_type": "cmo",
            "timestamp": datetime.now().isoformat(),
            "evaluation_id": evaluation_id,
            "results": [individual_result],  # List of results
            "summary": summary,
            "metadata": {
                "test_count": 1,
                "test_source": "QE Agent",
                "trace_id": test_case.get("trace_id"),
                "test_case_category": test_case.get("category", "general")
            }
        }
        
        # Debug logging for report data
        logger.info(f"=== CLI FORMAT RESULTS DEBUG ===")
        logger.info(f"Original overall_score: {evaluation_result.get('overall_score', 'NOT_FOUND')}")
        logger.info(f"Individual result weighted_score: {individual_result.get('weighted_score', 'NOT_FOUND')}")
        logger.info(f"Summary weighted_average_score: {summary.get('weighted_average_score', 'NOT_FOUND')}")
        logger.info(f"Summary overall_success: {summary.get('overall_success', 'NOT_FOUND')}")
        logger.info(f"Summary overall_success_rate: {summary.get('overall_success_rate', 'NOT_FOUND')}")
        logger.info(f"Dimension scores:")
        for dim_name in ['complexity_classification', 'specialty_selection', 'analysis_quality', 'tool_usage', 'response_structure', 'cost_efficiency']:
            score = individual_result.get(f"{dim_name}_score", 'NOT_FOUND')
            logger.info(f"  {dim_name}: {score}")
        logger.info(f"=== END CLI FORMAT RESULTS DEBUG ===")
        
        return cli_format_results
    
    def get_report_url(self, report_path: str) -> str:
        """
        Get an HTTP URL for the report that can be served by the API.
        
        Args:
            report_path: Path to the report directory (evaluation run directory)
            
        Returns:
            HTTP URL to the report that will be served by the API
        """
        logger.info(f"Getting report URL for path: {report_path}")
        report_dir = Path(report_path)
        logger.info(f"Report directory exists: {report_dir.exists()}")
        
        # For unified storage, report_path is the evaluation run directory
        # The actual report is in the "report" subdirectory
        if report_dir.name.startswith("eval_"):
            # This is an evaluation run directory
            report_html = report_dir / "report" / "report.html"
            if report_html.exists():
                # Extract evaluation ID from directory name
                eval_id = report_dir.name.replace("eval_", "").split("_trace_")[0]
                url = f"/api/qe/report/{eval_id}/report.html"
                logger.info(f"✅ Generated evaluation report URL: {url}")
                return url
        
        # Check if this is a full report structure with report subdirectory
        full_report_path = report_dir / "report" / "report.html"
        logger.info(f"Checking full report path: {full_report_path}")
        logger.info(f"Full report path exists: {full_report_path.exists()}")
        
        if full_report_path.exists():
            # Full CLI-style report structure
            report_name = report_dir.name
            url = f"/api/qe/report/{report_name}/report/report.html"
            logger.info(f"✅ Generated full report URL: {url}")
            return url
        
        # Try simple structure
        report_file = report_dir / "report.html"
        filename = "report.html"
        if not report_file.exists():
            report_file = report_dir / "index.html"
            filename = "index.html"
        
        logger.info(f"Checking simple report path: {report_file}")
        logger.info(f"Simple report path exists: {report_file.exists()}")
        
        if report_file.exists():
            # Simple report structure
            report_name = report_dir.name
            url = f"/api/qe/report/{report_name}/{filename}"
            logger.info(f"✅ Generated simple report URL: {url}")
            return url
        else:
            logger.error(f"❌ No report file found in {report_path}")
            logger.error(f"Directory contents: {list(report_dir.iterdir()) if report_dir.exists() else 'Directory does not exist'}")
            raise FileNotFoundError(f"Report not found at {report_path}/report/report.html, report.html, or index.html")
    
    def list_reports(self) -> List[Dict[str, Any]]:
        """
        List all available QE-generated reports.
        
        Returns:
            List of report metadata
        """
        reports = []
        
        for report_dir in self.base_report_dir.iterdir():
            if report_dir.is_dir():
                report_html = report_dir / "report" / "report.html"
                if report_html.exists():
                    # Load test case info
                    test_case_path = report_dir / "test_case.json"
                    test_case = {}
                    if test_case_path.exists():
                        with open(test_case_path, 'r') as f:
                            test_case = json.load(f)
                    
                    reports.append({
                        "name": report_dir.name,
                        "path": str(report_dir),
                        "url": self.get_report_url(str(report_dir)),
                        "created": datetime.fromtimestamp(report_html.stat().st_mtime).isoformat(),
                        "test_case_id": test_case.get("id", "unknown"),
                        "query": test_case.get("query", "")[:100] + "..."
                    })
        
        # Sort by creation time (newest first)
        reports.sort(key=lambda x: x["created"], reverse=True)
        
        return reports