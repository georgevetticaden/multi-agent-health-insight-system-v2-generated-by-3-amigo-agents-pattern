from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import json
import logging

from services.evaluation import EvaluationService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize service
evaluation_service = EvaluationService()


class RunEvaluationRequest(BaseModel):
    """Request to run an evaluation"""
    test_case: Dict[str, Any] = Field(..., description="Test case data from QE Agent")
    agent_type: str = Field("cmo", description="Agent type to evaluate")


class SaveTestCaseRequest(BaseModel):
    """Request to save a test case"""
    test_case: Dict[str, Any] = Field(..., description="Test case data")
    session_id: Optional[str] = Field(None, description="Session ID for grouping")


@router.post("/api/evaluation/run")
async def run_evaluation(request: RunEvaluationRequest) -> Dict[str, Any]:
    """
    Start an evaluation for a test case
    
    Returns evaluation ID to track progress
    """
    logger.info(f"=== EVALUATION RUN REQUEST ===")
    logger.info(f"Agent type: {request.agent_type}")
    logger.info(f"Test case data: {json.dumps(request.test_case, indent=2)}")
    
    try:
        evaluation_id = await evaluation_service.run_evaluation(
            request.test_case,
            request.agent_type
        )
        
        logger.info(f"Evaluation started successfully with ID: {evaluation_id}")
        
        return {
            "evaluation_id": evaluation_id,
            "status": "started",
            "message": f"Evaluation started for agent type: {request.agent_type}"
        }
    except ValueError as e:
        logger.error(f"Invalid evaluation request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start evaluation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start evaluation")



@router.get("/api/evaluation/status/{evaluation_id}")
async def get_evaluation_status(evaluation_id: str) -> Dict[str, Any]:
    """
    Get current status of an evaluation
    """
    if evaluation_id not in evaluation_service.evaluations:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    evaluation = evaluation_service.evaluations[evaluation_id]
    
    return {
        "evaluation_id": evaluation_id,
        "status": evaluation["status"].value,
        "test_case_id": evaluation["test_case_data"].get("id", "unknown"),
        "agent_type": evaluation["agent_type"],
        "started_at": evaluation["started_at"].isoformat(),
        "completed_at": evaluation.get("completed_at", "").isoformat() if evaluation.get("completed_at") else None,
        "event_count": len(evaluation.get("events", []))
    }


@router.get("/api/evaluation/results/{evaluation_id}")
async def get_evaluation_results(evaluation_id: str) -> Dict[str, Any]:
    """
    Get evaluation results if completed
    """
    result = await evaluation_service.get_evaluation_result(evaluation_id)
    
    if result is None:
        raise HTTPException(
            status_code=404, 
            detail="Evaluation not found or not yet completed"
        )
    
    return result


@router.post("/api/evaluation/test-case/save")
async def save_test_case(request: SaveTestCaseRequest) -> Dict[str, Any]:
    """
    Save a test case for later use
    """
    try:
        filepath = await evaluation_service.save_test_case(
            request.test_case,
            request.session_id
        )
        
        return {
            "status": "saved",
            "filepath": filepath,
            "message": "Test case saved successfully"
        }
    except Exception as e:
        logger.error(f"Failed to save test case: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save test case: {str(e)}")


@router.get("/api/evaluation/test-cases")
async def list_test_cases(
    session_id: Optional[str] = Query(None, description="Filter by session ID")
) -> List[Dict[str, Any]]:
    """
    List saved test cases
    """
    try:
        test_cases = await evaluation_service.list_saved_test_cases(session_id)
        return test_cases
    except Exception as e:
        logger.error(f"Failed to list test cases: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list test cases")


@router.get("/api/evaluation/events/{evaluation_id}")
async def get_evaluation_events(
    evaluation_id: str,
    start_index: int = Query(0, description="Start index for events")
) -> Dict[str, Any]:
    """
    Get evaluation lifecycle events
    
    Returns events that occurred during the evaluation process,
    allowing the UI to show progress during the ~30 second evaluation.
    """
    logger.info(f"=== GET EVALUATION EVENTS ===")
    logger.info(f"Evaluation ID: {evaluation_id}")
    logger.info(f"Start index: {start_index}")
    logger.info(f"Available evaluations: {list(evaluation_service.evaluations.keys())}")
    
    events_data = evaluation_service.get_evaluation_events(evaluation_id, start_index)
    
    if "error" in events_data:
        logger.error(f"Events not found for evaluation {evaluation_id}")
        raise HTTPException(status_code=404, detail=events_data["error"])
    
    logger.info(f"Returning {len(events_data.get('events', []))} events")
    return events_data