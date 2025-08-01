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

# No longer need to import evaluation modules - using subprocess approach

# Report service availability will be checked when needed
REPORT_SERVICE_AVAILABLE = True


class EvaluationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EventType(Enum):
    STATUS = "status"
    RESULT = "result"
    ERROR = "error"


class EvaluationService:
    """Service for running evaluations from test cases"""
    
    def __init__(self):
        # Import evaluation data config
        try:
            from evaluation.data.config import EvaluationDataConfig
            self.config = EvaluationDataConfig
            self.config.init_directories()
            self.use_unified_storage = True
        except ImportError:
            self.config = None
            self.use_unified_storage = False
            
        self.evaluations: Dict[str, Dict[str, Any]] = {}  # Still maintain in-memory cache
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
        
        # For subprocess evaluation, we work directly with dictionary data
        logger.info("Processing test case data...")
        logger.info(f"  - Query: {test_case_data.get('query', '')[:100]}...")
        logger.info(f"  - Expected complexity: {test_case_data.get('expected_complexity')}")
        logger.info(f"  - Expected specialties: {test_case_data.get('expected_specialties')}")
        logger.info(f"  - Category: {test_case_data.get('category')}")
        
        # Store evaluation info
        self.evaluations[evaluation_id] = {
            "id": evaluation_id,
            "test_case_data": test_case_data,
            "agent_type": agent_type,
            "status": EvaluationStatus.PENDING,
            "started_at": datetime.now(),
            "events": []  # Store evaluation lifecycle events
        }
        logger.info(f"Stored evaluation info in memory")
        
        # If using unified storage, create metadata file
        if self.use_unified_storage:
            run_dir = self.config.get_run_dir(evaluation_id)
            metadata = {
                "evaluation_id": evaluation_id,
                "test_case_id": test_case_data.get("id"),
                "trace_id": test_case_data.get("trace_id"),
                "agent_type": agent_type,
                "started_at": datetime.now().isoformat(),
                "status": EvaluationStatus.PENDING.value
            }
            (run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
            logger.info(f"Created metadata file at: {run_dir / 'metadata.json'}")
        
        # Start evaluation in background
        logger.info(f"Starting background evaluation task...")
        asyncio.create_task(self._run_evaluation_async(
            evaluation_id, test_case_data, agent_type
        ))
        
        return evaluation_id
    
    async def get_evaluation_result(self, evaluation_id: str) -> Optional[Dict[str, Any]]:
        """Get evaluation result if completed"""
        if evaluation_id not in self.evaluations:
            return None
        
        evaluation = self.evaluations[evaluation_id]
        if evaluation["status"] == EvaluationStatus.COMPLETED:
            return evaluation.get("result")
        
        return None
    
    def get_evaluation_events(self, evaluation_id: str, start_index: int = 0) -> Dict[str, Any]:
        """Get evaluation events since the given index"""
        logger.info(f"Getting events for evaluation {evaluation_id} from start_index {start_index}")
        logger.info(f"Using unified storage: {self.use_unified_storage}")
        
        # If using unified storage, read from file system
        if self.use_unified_storage:
            logger.info(f"Looking for run directory for evaluation {evaluation_id}")
            run_dir = self.config.find_run_dir(evaluation_id)
            logger.info(f"Found run directory: {run_dir}")
            if not run_dir:
                logger.error(f"Evaluation {evaluation_id} not found in file system")
                return {"error": "Evaluation not found", "events": []}
            
            # Read ALL event files and sort them
            events_dir = run_dir / "events"
            logger.info(f"Looking for events in: {events_dir}")
            logger.info(f"Events directory exists: {events_dir.exists()}")
            
            if events_dir.exists():
                event_files = sorted(events_dir.glob("*.json"))
                logger.info(f"Found {len(event_files)} total event files")
                if event_files:
                    logger.info(f"First few event files: {[f.name for f in event_files[:3]]}")
                    logger.info(f"Last few event files: {[f.name for f in event_files[-3:]]}")
            else:
                event_files = []
                logger.warning(f"Events directory does not exist: {events_dir}")
            
            # Load ALL events first to get correct ordering
            all_events = []
            for i, event_file in enumerate(event_files):
                try:
                    with open(event_file) as f:
                        event = json.load(f)
                        # Add an index to maintain order
                        event['_index'] = i
                        all_events.append(event)
                except Exception as e:
                    logger.error(f"Error reading event file {event_file}: {e}")
            
            # Now slice from start_index to get only NEW events
            new_events = all_events[start_index:] if start_index < len(all_events) else []
            logger.info(f"Total events loaded: {len(all_events)}")
            logger.info(f"Returning {len(new_events)} new events (from index {start_index})")
            if new_events:
                logger.info(f"First new event: {new_events[0].get('type', 'unknown')} - {new_events[0].get('message', '')}")
            else:
                logger.info(f"No new events to return")
            
            # Read metadata for status
            metadata_path = run_dir / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path) as f:
                    metadata = json.load(f)
                status = metadata.get("status", "unknown")
            else:
                status = "unknown"
            
            return {
                "evaluation_id": evaluation_id,
                "status": status,
                "events": new_events,
                "total_events": len(all_events),
                "has_more": False
            }
        else:
            # Fallback to in-memory storage
            logger.info(f"Available evaluations: {list(self.evaluations.keys())}")
            
            if evaluation_id not in self.evaluations:
                logger.error(f"Evaluation {evaluation_id} not found in evaluations dict")
                return {"error": "Evaluation not found", "events": []}
            
            evaluation = self.evaluations[evaluation_id]
            all_events = evaluation.get("events", [])
            logger.info(f"Total events stored: {len(all_events)}")
            
            events = all_events[start_index:]
            logger.info(f"Returning {len(events)} events starting from index {start_index}")
            
            return {
                "evaluation_id": evaluation_id,
                "status": evaluation["status"].value,
                "events": events,
                "total_events": len(all_events),
                "has_more": len(events) < len(all_events)
            }
    
    async def save_test_case(
        self,
        test_case_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> str:
        """Save a test case to disk"""
        if self.use_unified_storage:
            # Save using TestLoader to unified storage
            try:
                from evaluation.data.test_loader import TestLoader
                
                # Ensure test case has required fields
                if 'id' not in test_case_data:
                    test_case_data['id'] = str(uuid.uuid4())
                if 'agent_type' not in test_case_data:
                    test_case_data['agent_type'] = 'cmo'  # Default to CMO
                if 'created_at' not in test_case_data:
                    test_case_data['created_at'] = datetime.now().isoformat()
                if 'created_by' not in test_case_data:
                    test_case_data['created_by'] = 'studio'
                
                # Save test case
                if TestLoader.save_test_case(test_case_data, source='studio'):
                    test_path = self.config.get_test_case_path(
                        test_case_data['id'], 
                        test_case_data['agent_type']
                    )
                    logger.info(f"Saved test case to unified storage: {test_path}")
                    return str(test_path)
                else:
                    logger.error("Failed to save test case to unified storage")
            except Exception as e:
                logger.error(f"Error saving to unified storage: {e}")
        
        # Fallback to old storage method
        today = datetime.now().strftime("%Y-%m-%d")
        if session_id:
            save_dir = Path("test_cases") / today / session_id
        else:
            save_dir = Path("test_cases") / today
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Save test case
        test_case_id = test_case_data.get('id', str(uuid.uuid4()))
        filename = f"{test_case_id}.json"
        filepath = save_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(test_case_data, f, indent=2)
        
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
    
    async def _evaluate_with_cli_evaluator(
        self,
        test_case_data: Dict[str, Any],
        agent_type: str,
        evaluation_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate using CLI evaluator with trace data.
        
        This method uses the comprehensive CLI evaluator which includes
        LLM judge and detailed failure analysis.
        """
        # Import from backend's evaluation module - adjust path
        import sys
        import os
        backend_eval_path = os.path.join(os.path.dirname(__file__), "../..")
        if backend_eval_path not in sys.path:
            sys.path.insert(0, backend_eval_path)
        
        from eval_integration.cli_evaluator_adapter import TraceEvaluationService
        from anthropic import Anthropic
        
        # Load trace
        trace_id = test_case_data.get('trace_id')
        if not trace_id:
            raise ValueError("Test case must have a trace_id")
            
        trace_path = self._find_trace_file(trace_id)
        if not trace_path:
            raise ValueError(f"Trace file not found for trace_id: {trace_id}")
        
        logger.info(f"Loading trace from: {trace_path}")
        
        # Create evaluation service with Anthropic client
        anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        eval_service = TraceEvaluationService(anthropic_client=anthropic_client)
        
        # Run evaluation
        logger.info("Running CLI evaluator on trace...")
        result_dict = await eval_service.evaluate_test_case_from_trace(
            test_case_data,
            trace_path,
            evaluation_id,
            self.evaluations  # Pass evaluations dict to store events
        )
        
        # Return the result dictionary directly
        return result_dict
    
    def _find_trace_file(self, trace_id: str) -> Optional[str]:
        """Find trace file by ID."""
        # Try unified storage first
        if self.use_unified_storage:
            trace_path = self.config.find_trace(trace_id)
            if trace_path:
                logger.info(f"Found trace in unified storage: {trace_path}")
                return str(trace_path)
            else:
                logger.warning(f"Trace not found via config.find_trace for ID: {trace_id}")
        
        # If unified storage available, also check the traces directory directly
        if self.use_unified_storage and self.config.TRACES_DIR.exists():
            logger.info(f"Searching in unified traces directory: {self.config.TRACES_DIR}")
            # Search in date directories
            for date_dir in self.config.TRACES_DIR.iterdir():
                if date_dir.is_dir():
                    # Try new naming pattern (HHMMSS_trace_id.json)
                    for trace_file in date_dir.glob(f"*_{trace_id}.json"):
                        if trace_file.exists():
                            logger.info(f"Found trace with new naming pattern: {trace_file}")
                            return str(trace_file)
                    # Try old naming pattern
                    trace_file = date_dir / f"{trace_id}.json"
                    if trace_file.exists():
                        logger.info(f"Found trace with old naming pattern: {trace_file}")
                        return str(trace_file)
        
        # Fallback to old trace directories
        logger.info("Falling back to old trace directories")
        trace_dirs = [
            Path("traces"),
            Path(".")
        ]
        
        for base_dir in trace_dirs:
            if not base_dir.exists():
                continue
                
            # Search for trace file
            for trace_file in base_dir.rglob(f"*{trace_id}*.json"):
                if trace_file.is_file() and not trace_file.name.endswith('.hierarchical.json'):
                    logger.info(f"Found trace in fallback directory: {trace_file}")
                    return str(trace_file)
        
        logger.error(f"Trace file not found for ID: {trace_id}")
        return None
    
    async def _run_evaluation_async(
        self,
        evaluation_id: str,
        test_case_data: Dict[str, Any],
        agent_type: str
    ):
        """Run evaluation asynchronously"""
        logger.info(f"=== ASYNC EVALUATION START: {evaluation_id} ===")
        logger.info(f"Test case: {test_case_data.get('id', 'unknown')}")
        logger.info(f"Agent type: {agent_type}")
        
        evaluation = self.evaluations[evaluation_id]
        
        try:
            # Update status
            logger.info(f"Updating evaluation status to RUNNING...")
            evaluation["status"] = EvaluationStatus.RUNNING
            
            # Update metadata file if using unified storage
            if self.use_unified_storage:
                run_dir = self.config.find_run_dir(evaluation_id)
                if run_dir:
                    metadata_path = run_dir / "metadata.json"
                    if metadata_path.exists():
                        with open(metadata_path) as f:
                            metadata = json.load(f)
                        metadata["status"] = EvaluationStatus.RUNNING.value
                        metadata_path.write_text(json.dumps(metadata, indent=2))
            
            # Use CLI evaluator with subprocess
            trace_id = test_case_data.get('trace_id')
            if not trace_id:
                raise ValueError("Test case must have a trace_id for evaluation")
            
            logger.info(f"Using CLI evaluator with trace: {trace_id}")
            result = await self._evaluate_with_cli_evaluator(
                test_case_data,
                agent_type,
                evaluation_id  # Pass evaluation_id to store events
            )
            
            logger.info(f"Evaluation completed with overall score: {result.get('overall_score', 0):.2%}")
            logger.info(f"Dimension results:")
            for dim, dim_result in result.get('dimension_results', {}).items():
                logger.info(f"  - {dim}: {dim_result.get('score', 0):.2%}")
            
            # Store result first
            evaluation["result"] = result
            
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
                    logger.info(f"Test case keys: {list(test_case_data.keys())}")
                    logger.info(f"Result keys: {list(result.keys())}")
                    logger.info(f"Agent type: {agent_type}")
                    
                    report_path = report_service.generate_report_from_evaluation(
                        evaluation_id=evaluation_id,
                        test_case=test_case_data,
                        evaluation_result=result,
                        agent_type=agent_type
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
            
            # Update metadata file if using unified storage
            if self.use_unified_storage:
                run_dir = self.config.find_run_dir(evaluation_id)
                if run_dir:
                    metadata_path = run_dir / "metadata.json"
                    if metadata_path.exists():
                        with open(metadata_path) as f:
                            metadata = json.load(f)
                        metadata["status"] = EvaluationStatus.COMPLETED.value
                        metadata["completed_at"] = datetime.now().isoformat()
                        metadata_path.write_text(json.dumps(metadata, indent=2))
            
            logger.info(f"Evaluation {evaluation_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Evaluation {evaluation_id} failed: {e}", exc_info=True)
            evaluation["status"] = EvaluationStatus.FAILED
            evaluation["error"] = str(e)
            
            # Update metadata file if using unified storage
            if self.use_unified_storage:
                run_dir = self.config.find_run_dir(evaluation_id)
                if run_dir:
                    metadata_path = run_dir / "metadata.json"
                    if metadata_path.exists():
                        with open(metadata_path) as f:
                            metadata = json.load(f)
                        metadata["status"] = EvaluationStatus.FAILED.value
                        metadata["error"] = str(e)
                        metadata["failed_at"] = datetime.now().isoformat()
                        metadata_path.write_text(json.dumps(metadata, indent=2))
    
    async def _save_result(self, evaluation_id: str, result: Dict[str, Any]):
        """Save evaluation result to file"""
        if self.use_unified_storage:
            # Save to unified storage location
            run_dir = self.config.find_run_dir(evaluation_id)
            if run_dir:
                filepath = run_dir / "result.json"
                logger.info(f"Saving evaluation result to unified storage: {filepath}")
                
                with open(filepath, 'w') as f:
                    json.dump(result, f, indent=2)
                
                logger.info(f"Successfully saved evaluation result ({os.path.getsize(filepath)} bytes)")
                
                # Store filepath in evaluation
                self.evaluations[evaluation_id]["result_file"] = str(filepath)
                return
        
        # Fallback to old storage method
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_case_id = result.get('test_case_id', evaluation_id[:8])
        filename = f"{test_case_id}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        logger.info(f"Saving evaluation result to: {filepath}")
        
        with open(filepath, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Successfully saved evaluation result ({os.path.getsize(filepath)} bytes)")
        
        # Store filepath in evaluation
        self.evaluations[evaluation_id]["result_file"] = str(filepath)