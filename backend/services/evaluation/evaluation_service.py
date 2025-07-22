import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, AsyncIterator
from enum import Enum
import sys

# Set up logging first
logger = logging.getLogger(__name__)

# Add backend to path for imports
backend_path = os.path.join(os.path.dirname(__file__), "../..")
sys.path.append(backend_path)

# Store project root for later use with report generation
project_root = os.path.join(backend_path, "..")

from dotenv import load_dotenv

# Load environment variables from multiple locations
current_dir = Path(__file__).parent.parent.parent.parent  # Project root
load_dotenv(current_dir / '.env')  # Project root
load_dotenv(current_dir / 'backend' / '.env')  # Backend directory
load_dotenv(current_dir / 'evaluation' / '.env')  # Evaluation directory

# Import evaluation modules from backend's evaluation module
try:
    from evaluation.core.models import TestCase, EvaluationResult
    from evaluation.core.runner import EvaluationRunner, EvaluationProgress
    from evaluation.core import AgentEvaluationMetadata
    EVALUATION_AVAILABLE = True
    logger.info("Successfully imported evaluation modules")
except ImportError as e:
    logger.warning(f"Evaluation modules not available: {e}")
    logger.warning(f"Current working directory: {os.getcwd()}")
    logger.warning(f"Python path: {sys.path[:3]}")
    EVALUATION_AVAILABLE = False
    # Define dummy classes to prevent import errors
    class TestCase:
        pass
    class EvaluationResult:
        pass
    class EvaluationRunner:
        pass
    class EvaluationProgress:
        pass
    class AgentEvaluationMetadata:
        pass

from services.agents.cmo import CMOAgent

# Don't import report service at module level - defer until needed
REPORT_SERVICE_AVAILABLE = EVALUATION_AVAILABLE


class EvaluationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EventType(Enum):
    STATUS = "status"
    PROGRESS = "progress"
    RESULT = "result"
    ERROR = "error"


class EvaluationService:
    """Service for running evaluations from test cases"""
    
    def __init__(self):
        self.runner = EvaluationRunner()
        self.evaluations: Dict[str, Dict[str, Any]] = {}
        self.results_dir = Path("evaluation_results")
        self.results_dir.mkdir(exist_ok=True)
    
    async def run_evaluation(
        self,
        test_case_data: Dict[str, Any],
        agent_type: str = "cmo"
    ) -> str:
        """
        Start an evaluation for a test case
        
        Args:
            test_case_data: Test case data from QE Agent
            agent_type: Type of agent to evaluate (default: cmo)
            
        Returns:
            evaluation_id: ID to track the evaluation
        """
        logger.info("=== EVALUATION SERVICE: Starting new evaluation ===")
        
        # Generate evaluation ID
        evaluation_id = str(uuid.uuid4())
        logger.info(f"Generated evaluation ID: {evaluation_id}")
        
        # Parse test case
        try:
            logger.info("Parsing test case data...")
            test_case = self._parse_test_case(test_case_data)
            logger.info(f"Successfully parsed test case: {test_case.id}")
            logger.info(f"  - Query: {test_case.query[:100]}...")
            logger.info(f"  - Expected complexity: {test_case.expected_complexity}")
            logger.info(f"  - Expected specialties: {test_case.expected_specialties}")
            logger.info(f"  - Category: {test_case.category}")
        except Exception as e:
            logger.error(f"Failed to parse test case: {e}")
            raise ValueError(f"Invalid test case format: {str(e)}")
        
        # Get agent metadata
        logger.info(f"Looking up metadata for agent type: {agent_type}")
        agent_metadata = self._get_agent_metadata(agent_type)
        if not agent_metadata:
            raise ValueError(f"Unknown agent type: {agent_type}")
        logger.info(f"Found agent metadata with {len(agent_metadata.evaluation_criteria)} evaluation criteria")
        
        # Store evaluation info
        self.evaluations[evaluation_id] = {
            "id": evaluation_id,
            "test_case": test_case,
            "agent_type": agent_type,
            "status": EvaluationStatus.PENDING,
            "started_at": datetime.now(),
            "progress": []
        }
        logger.info(f"Stored evaluation info in memory")
        
        # Start evaluation in background
        logger.info(f"Starting background evaluation task...")
        asyncio.create_task(self._run_evaluation_async(
            evaluation_id, test_case, agent_metadata
        ))
        
        return evaluation_id
    
    async def stream_evaluation_progress(
        self,
        evaluation_id: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream evaluation progress updates"""
        if evaluation_id not in self.evaluations:
            yield {
                "type": EventType.ERROR.value,
                "content": f"Evaluation {evaluation_id} not found"
            }
            return
        
        evaluation = self.evaluations[evaluation_id]
        
        # Send initial status
        yield {
            "type": EventType.STATUS.value,
            "content": evaluation["status"].value,
            "data": {
                "test_case_id": evaluation["test_case"].id,
                "agent_type": evaluation["agent_type"]
            }
        }
        
        # Stream progress updates
        last_progress_idx = 0
        while True:
            # Check for new progress
            if len(evaluation["progress"]) > last_progress_idx:
                for progress in evaluation["progress"][last_progress_idx:]:
                    yield {
                        "type": EventType.PROGRESS.value,
                        "content": progress["message"],
                        "data": progress
                    }
                last_progress_idx = len(evaluation["progress"])
            
            # Check if completed
            if evaluation["status"] in [EvaluationStatus.COMPLETED, EvaluationStatus.FAILED]:
                if evaluation["status"] == EvaluationStatus.COMPLETED:
                    # Include report URL in result
                    result_data = evaluation.get("result", {}).copy()  # Make a copy to avoid modifying original
                    result_data["report_url"] = evaluation.get("report_url")
                    
                    logger.info(f"Sending evaluation result with report_url: {result_data.get('report_url')}")
                    
                    yield {
                        "type": EventType.RESULT.value,
                        "content": "Evaluation completed",
                        "data": result_data
                    }
                else:
                    yield {
                        "type": EventType.ERROR.value,
                        "content": evaluation.get("error", "Evaluation failed")
                    }
                break
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(0.1)
    
    async def get_evaluation_result(self, evaluation_id: str) -> Optional[Dict[str, Any]]:
        """Get evaluation result if completed"""
        if evaluation_id not in self.evaluations:
            return None
        
        evaluation = self.evaluations[evaluation_id]
        if evaluation["status"] == EvaluationStatus.COMPLETED:
            return evaluation.get("result")
        
        return None
    
    async def save_test_case(
        self,
        test_case_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> str:
        """Save a test case to disk"""
        test_case = self._parse_test_case(test_case_data)
        
        # Create directory structure
        today = datetime.now().strftime("%Y-%m-%d")
        if session_id:
            save_dir = Path("test_cases") / today / session_id
        else:
            save_dir = Path("test_cases") / today
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Save test case
        filename = f"{test_case.id}.json"
        filepath = save_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(test_case.to_dict(), f, indent=2)
        
        logger.info(f"Saved test case to {filepath}")
        return str(filepath)
    
    async def list_saved_test_cases(
        self,
        session_id: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """List saved test cases"""
        test_cases = []
        
        # Determine search path
        if session_id:
            today = datetime.now().strftime("%Y-%m-%d")
            search_path = Path("test_cases") / today / session_id
        else:
            search_path = Path("test_cases")
        
        if not search_path.exists():
            return test_cases
        
        # Find all test case files
        for filepath in search_path.rglob("*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    test_cases.append({
                        "filepath": str(filepath),
                        "test_case": data
                    })
            except Exception as e:
                logger.error(f"Failed to load test case from {filepath}: {e}")
        
        return test_cases
    
    def _parse_test_case(self, test_case_data: Dict[str, Any]) -> TestCase:
        """Parse test case from QE Agent format"""
        logger.info("Parsing test case from QE Agent format...")
        
        # Handle the raw test case string if provided
        if "raw" in test_case_data:
            logger.info("Found 'raw' field in test case data, extracting fields...")
            # Extract fields from the raw TestCase(...) string
            raw = test_case_data["raw"]
            logger.info(f"Raw test case string length: {len(raw)} chars")
            # This is a simplified parser - in production, use AST parsing
            fields = self._extract_fields_from_raw(raw)
            logger.info(f"Extracted {len(fields)} fields from raw string")
            # Create new dict with only the extracted fields
            test_case_data = fields
        else:
            logger.info("No 'raw' field found, filtering valid fields...")
            # Remove any non-TestCase fields
            valid_fields = {"id", "query", "expected_complexity", "actual_complexity",
                          "expected_specialties", "actual_specialties", "key_data_points",
                          "category", "notes", "based_on_real_query", "trace_id"}
            original_count = len(test_case_data)
            test_case_data = {k: v for k, v in test_case_data.items() if k in valid_fields}
            logger.info(f"Filtered from {original_count} to {len(test_case_data)} valid fields")
        
        # Ensure required fields
        required_fields = ["id", "query", "expected_complexity"]
        for field in required_fields:
            if field not in test_case_data:
                logger.error(f"Missing required field: {field}")
                logger.error(f"Available fields: {list(test_case_data.keys())}")
                raise ValueError(f"Missing required field: {field}")
        
        logger.info("All required fields present, creating TestCase object...")
        return TestCase(**test_case_data)
    
    def _extract_fields_from_raw(self, raw: str) -> Dict[str, Any]:
        """Extract fields from raw TestCase string using AST parsing"""
        import ast
        import re
        
        logger.info("Extracting fields from raw TestCase string...")
        logger.info(f"Raw string (first 200 chars): {raw[:200]}...")
        
        # Clean up the raw string to make it valid Python
        # Remove TestCase( prefix and ) suffix
        raw = raw.strip()
        if raw.startswith('TestCase('):
            raw = raw[9:]
        if raw.endswith(')'):
            raw = raw[:-1]
        
        # Parse as keyword arguments
        fields = {}
        
        # Use AST to parse the TestCase arguments
        try:
            # Create a dummy function call to parse
            dummy_code = f"dict({raw})"
            tree = ast.parse(dummy_code, mode='eval')
            
            # Extract the arguments
            if isinstance(tree.body, ast.Call):
                for keyword in tree.body.keywords:
                    key = keyword.arg
                    value = ast.literal_eval(keyword.value)
                    fields[key] = value
                    logger.info(f"  Extracted field '{key}': {value}")
            
            logger.info(f"Successfully extracted {len(fields)} fields using AST")
        except Exception as e:
            logger.warning(f"AST parsing failed, falling back to regex: {e}")
            
            # Fallback to regex parsing
            # Extract id
            id_match = re.search(r'id="([^"]+)"', raw)
            if id_match:
                fields["id"] = id_match.group(1)
            
            # Extract query (handle multiline)
            query_match = re.search(r'query="([^"]+)"', raw, re.DOTALL)
            if query_match:
                fields["query"] = query_match.group(1)
            
            # Extract complexities
            expected_match = re.search(r'expected_complexity="([^"]+)"', raw)
            if expected_match:
                fields["expected_complexity"] = expected_match.group(1)
            
            actual_match = re.search(r'actual_complexity="([^"]+)"', raw)
            if actual_match:
                fields["actual_complexity"] = actual_match.group(1)
            
            # Extract specialties (handle set format)
            expected_spec_match = re.search(r'expected_specialties=\{([^}]+)\}', raw)
            if expected_spec_match:
                specialties = [s.strip().strip('"\'\'') for s in expected_spec_match.group(1).split(',')]
                fields["expected_specialties"] = set(specialties)
            
            actual_spec_match = re.search(r'actual_specialties=\{([^}]+)\}', raw)
            if actual_spec_match:
                specialties = [s.strip().strip('"\'\'') for s in actual_spec_match.group(1).split(',')]
                fields["actual_specialties"] = set(specialties)
            
            # Extract key_data_points
            key_data_match = re.search(r'key_data_points=\[([^\]]+)\]', raw)
            if key_data_match:
                data_points = [s.strip().strip('"\'\'') for s in key_data_match.group(1).split(',')]
                fields["key_data_points"] = data_points
            
            # Extract other fields
            category_match = re.search(r'category="([^"]+)"', raw)
            if category_match:
                fields["category"] = category_match.group(1)
            
            notes_match = re.search(r'notes="([^"]+)"', raw, re.DOTALL)
            if notes_match:
                fields["notes"] = notes_match.group(1)
        
        return fields
    
    def _get_agent_metadata(self, agent_type: str) -> Optional[AgentEvaluationMetadata]:
        """Get evaluation metadata for agent type"""
        if agent_type == "cmo":
            return CMOAgent.get_evaluation_metadata()
        # Add other agents as needed
        return None
    
    async def _evaluate_with_cli_evaluator(
        self,
        test_case: TestCase,
        agent_type: str,
        progress_callback: Optional[Any] = None
    ) -> EvaluationResult:
        """
        Evaluate using CLI evaluator with trace data.
        
        This method uses the comprehensive CLI evaluator which includes
        LLM judge and detailed failure analysis.
        """
        # Import from backend's evaluation module
        from evaluation.cli_evaluator_adapter import TraceEvaluationService
        from anthropic import Anthropic
        import os
        
        # Load trace
        trace_path = self._find_trace_file(test_case.trace_id)
        if not trace_path:
            raise ValueError(f"Trace file not found for trace_id: {test_case.trace_id}")
        
        logger.info(f"Loading trace from: {trace_path}")
        
        # Convert test case to dict format
        test_case_dict = test_case.to_dict()
        
        # Create evaluation service with Anthropic client
        anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        eval_service = TraceEvaluationService(anthropic_client=anthropic_client)
        
        # Progress updates
        if progress_callback:
            await progress_callback(EvaluationProgress(
                stage="loading_trace",
                progress=10.0,
                message="Loading trace data..."
            ))
        
        # Run evaluation
        logger.info("Running CLI evaluator on trace...")
        result_dict = await eval_service.evaluate_test_case_from_trace(
            test_case_dict,
            trace_path
        )
        
        # Convert back to EvaluationResult
        dimension_results = {}
        for dim_name, dim_data in result_dict["dimension_results"].items():
            from evaluation.core.models import DimensionResult
            dimension_results[dim_name] = DimensionResult(
                dimension_name=dim_name,
                score=dim_data["score"],
                normalized_score=dim_data.get("normalized_score", dim_data["score"]),
                components=dim_data.get("components", {}),
                details=dim_data.get("details", {}),
                evaluation_method="cli_evaluator"
            )
        
        # Create evaluation result
        result = EvaluationResult(
            test_case_id=test_case.id,
            agent_type=agent_type,
            overall_score=result_dict["overall_score"],
            dimension_results=dimension_results,
            execution_time_ms=result_dict.get("execution_time_ms", 0),
            metadata=result_dict.get("metadata", {})
        )
        
        return result
    
    def _find_trace_file(self, trace_id: str) -> Optional[str]:
        """Find trace file by ID."""
        # Look in standard trace directories
        trace_dirs = [
            Path("backend/traces"),
            Path("traces"),
            Path(".")
        ]
        
        for base_dir in trace_dirs:
            if not base_dir.exists():
                continue
                
            # Search for trace file
            for trace_file in base_dir.rglob(f"*{trace_id}*.json"):
                if trace_file.is_file():
                    return str(trace_file)
        
        return None
    
    async def _run_evaluation_async(
        self,
        evaluation_id: str,
        test_case: TestCase,
        agent_metadata: AgentEvaluationMetadata
    ):
        """Run evaluation asynchronously"""
        logger.info(f"=== ASYNC EVALUATION START: {evaluation_id} ===")
        logger.info(f"Test case: {test_case.id}")
        logger.info(f"Agent type: {agent_metadata.agent_metadata.agent_type}")
        
        evaluation = self.evaluations[evaluation_id]
        
        try:
            # Update status
            logger.info(f"Updating evaluation status to RUNNING...")
            evaluation["status"] = EvaluationStatus.RUNNING
            
            # Define progress callback
            async def progress_callback(progress: EvaluationProgress):
                logger.info(f"Progress update: {progress.stage} - {progress.dimension} - {progress.message}")
                evaluation["progress"].append({
                    "stage": progress.stage,
                    "dimension": progress.dimension,
                    "progress": progress.progress,
                    "message": progress.message,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Check if we have a trace_id to use CLI evaluator
            if hasattr(test_case, 'trace_id') and test_case.trace_id:
                logger.info(f"Using CLI evaluator with trace: {test_case.trace_id}")
                result = await self._evaluate_with_cli_evaluator(
                    test_case,
                    agent_metadata.agent_metadata.agent_type,
                    progress_callback
                )
            else:
                # Fallback to original evaluation runner
                logger.info(f"Using standard evaluation runner (no trace available)")
                result = await self.runner.evaluate_test_case(
                    test_case,
                    agent_metadata,
                    progress_callback
                )
            
            logger.info(f"Evaluation completed with overall score: {result.overall_score:.2%}")
            logger.info(f"Dimension results:")
            for dim, dim_result in result.dimension_results.items():
                logger.info(f"  - {dim}: {dim_result.normalized_score:.2%} ({dim_result.evaluation_method})")
            
            # Store result first
            evaluation["result"] = result.to_dict()
            
            # Save result to file
            await self._save_result(evaluation_id, result)
            
            # Generate comprehensive HTML report BEFORE marking as completed
            if REPORT_SERVICE_AVAILABLE:
                try:
                    logger.info(f"Starting report generation for evaluation {evaluation_id}...")
                    
                    # Temporarily add project root to path for report service import
                    if project_root not in sys.path:
                        sys.path.insert(0, project_root)
                    
                    try:
                        # Import report service here when paths are properly set up
                        from services.evaluation.report_service import ReportService
                        report_service = ReportService()
                        logger.info("Successfully created ReportService instance")
                    finally:
                        # Remove project root from path to avoid conflicts
                        if project_root in sys.path:
                            sys.path.remove(project_root)
                    
                    logger.info(f"Generating HTML report for evaluation {evaluation_id}...")
                    logger.info(f"Test case keys: {list(test_case.to_dict().keys())}")
                    logger.info(f"Result keys: {list(result.to_dict().keys())}")
                    logger.info(f"Agent type: {agent_metadata.agent_metadata.agent_type}")
                    
                    report_path = report_service.generate_report_from_evaluation(
                        evaluation_id=evaluation_id,
                        test_case=test_case.to_dict(),
                        evaluation_result=result.to_dict(),
                        agent_type=agent_metadata.agent_metadata.agent_type
                    )
                    
                    # Store report path in evaluation
                    evaluation["report_path"] = report_path
                    evaluation["report_url"] = report_service.get_report_url(report_path)
                    logger.info(f"✅ Report generated at: {report_path}")
                    logger.info(f"✅ Report URL: {evaluation['report_url']}")
                    logger.info(f"✅ Full evaluation object has report_url: {'report_url' in evaluation}")
                    
                except Exception as e:
                    logger.error(f"Failed to generate report: {e}", exc_info=True)
                    logger.error(f"Report generation error type: {type(e).__name__}")
                    logger.error(f"Report generation error details: {str(e)}")
                    # Don't fail the evaluation if report generation fails
                    evaluation["report_path"] = None
                    evaluation["report_url"] = None
            else:
                logger.warning("Report service not available - skipping report generation")
                evaluation["report_path"] = None
                evaluation["report_url"] = None
            
            # NOW mark as completed after report is generated
            evaluation["status"] = EvaluationStatus.COMPLETED
            evaluation["completed_at"] = datetime.now()
            
            logger.info(f"Evaluation {evaluation_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Evaluation {evaluation_id} failed: {e}", exc_info=True)
            evaluation["status"] = EvaluationStatus.FAILED
            evaluation["error"] = str(e)
    
    async def _save_result(self, evaluation_id: str, result: EvaluationResult):
        """Save evaluation result to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{result.test_case_id}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        logger.info(f"Saving evaluation result to: {filepath}")
        
        with open(filepath, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        logger.info(f"Successfully saved evaluation result ({os.path.getsize(filepath)} bytes)")
        
        # Store filepath in evaluation
        self.evaluations[evaluation_id]["result_file"] = str(filepath)