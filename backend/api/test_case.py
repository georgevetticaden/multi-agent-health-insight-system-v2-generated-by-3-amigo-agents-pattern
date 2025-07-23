"""
Test Case Management API

Provides endpoints for creating, updating, and evaluating test cases
for the Eval Driven Agent Development Framework.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from services.tracing import get_trace_collector
from services.tracing.trace_models import CompleteTrace, TraceEventType
from services.agents.qe.qe_agent import QEAgent
from services.qe_analyst_service import QEAnalystService
from services.evaluation.evaluation_service import EvaluationService

# Import report service only when needed to avoid startup errors
ReportService = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/test-cases", tags=["test-cases"])


class TestCaseCreate(BaseModel):
    """Request model for creating a test case from a trace"""
    trace_id: str
    user_notes: Optional[str] = None


class TestCaseUpdate(BaseModel):
    """Request model for updating a test case"""
    query: Optional[str] = None
    expected_complexity: Optional[str] = None
    expected_specialties: Optional[list[str]] = None
    key_data_points: Optional[list[str]] = None
    notes: Optional[str] = None


class TestCaseResponse(BaseModel):
    """Response model for test case data"""
    id: str
    trace_id: str
    query: str
    expected_complexity: str
    actual_complexity: str
    expected_specialties: list[str]
    actual_specialties: list[str]
    key_data_points: list[str]
    notes: str
    created_at: datetime
    updated_at: datetime
    based_on_real_query: bool = True
    category: str = "general"
    modified_fields: list[str] = []  # Track which fields have been modified by QE Agent


# In-memory storage for test cases (in production, use a database)
test_cases_db: Dict[str, Dict[str, Any]] = {}


@router.post("/from-trace", response_model=TestCaseResponse)
async def create_test_case_from_trace(request: TestCaseCreate):
    """
    Create a test case from a trace ID.
    
    This endpoint:
    1. Loads the trace
    2. Extracts execution data
    3. Creates an initial test case based on the trace
    """
    try:
        logger.info(f"Creating test case from trace: {request.trace_id}")
        
        # Get trace collector and load trace
        trace_collector = get_trace_collector()
        logger.info(f"Trace collector storage type: {type(trace_collector.storage)}")
        
        # Try to get from active traces first
        trace_data = await trace_collector.get_active_trace(request.trace_id)
        
        # If not active, try stored traces
        if not trace_data:
            logger.info(f"Trace not in active traces, checking storage...")
            trace_data = await trace_collector.storage.get_trace(request.trace_id)
        
        if not trace_data:
            logger.error(f"Trace {request.trace_id} not found in active or stored traces")
            raise HTTPException(status_code=404, detail=f"Trace {request.trace_id} not found")
        
        # Extract data from trace
        trace = trace_data  # Assuming get_trace returns CompleteTrace object
        logger.info(f"Successfully retrieved trace with {len(trace.events)} events")
        
        # Extract query
        query = ""
        for event in trace.events:
            event_type_str = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
            if event_type_str == "user_query":
                query = event.data.get("query", "")
                logger.info(f"Found user query: {query[:50]}...")
                break
        
        if not query:
            raise HTTPException(status_code=400, detail="No query found in trace")
        
        # Extract complexity from trace
        complexity_str = "SIMPLE"
        for event in trace.events:
            event_type_str = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
            if (event_type_str == "stage_end" and 
                event.stage == "query_analysis"):
                complexity_str = event.data.get("complexity", "SIMPLE")
                break
        
        # Extract actual specialties from task creation LLM response
        actual_specialties = []
        for event in trace.events:
            event_type_str = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
            if (event_type_str == "llm_response" and 
                event.stage == "task_creation"):
                response_text = event.data.get("response_text", "")
                logger.info(f"Found task creation response, length: {len(response_text)}")
                
                # Extract specialists from task assignments
                import re
                # Look for <specialist> tags in the response
                specialists = re.findall(r'<specialist>([^<]+)</specialist>', response_text)
                for specialist in specialists:
                    # Clean up and normalize specialist name
                    specialist_clean = specialist.strip().lower().replace(" ", "_")
                    actual_specialties.append(specialist_clean.upper())
                    logger.info(f"Found specialty: {specialist_clean}")
                
                # If no <specialist> tags, try <task> format
                if not specialists:
                    tasks = re.findall(r'<task>.*?<specialty>([^<]+)</specialty>.*?</task>', response_text, re.DOTALL)
                    for specialty in tasks:
                        specialist_clean = specialty.strip().lower().replace(" ", "_")
                        actual_specialties.append(specialist_clean.upper())
                        logger.info(f"Found specialty from task format: {specialist_clean}")
        
        logger.info(f"Total specialties found: {len(actual_specialties)} - {actual_specialties}")
        
        # Create test case
        test_case_id = str(uuid4())
        test_case = {
            "id": test_case_id,
            "trace_id": request.trace_id,
            "query": query,
            "expected_complexity": complexity_str,  # Pre-populate with actual for user to verify/modify
            "actual_complexity": complexity_str,  # Store the actual complexity from trace
            "expected_specialties": actual_specialties.copy(),  # Pre-populate with actual for user to verify/modify
            "actual_specialties": actual_specialties,
            "key_data_points": [],  # To be filled by user
            "notes": request.user_notes or f"Auto-generated from trace {request.trace_id}. Expected values pre-populated from actual execution.",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "based_on_real_query": True,
            "category": "general",
            "modified_fields": []  # No fields modified initially
        }
        
        # Store test case
        test_cases_db[test_case_id] = test_case
        
        logger.info(f"Created test case {test_case_id} from trace {request.trace_id}")
        
        return TestCaseResponse(**test_case)
        
    except Exception as e:
        logger.error(f"Error creating test case from trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{test_case_id}", response_model=TestCaseResponse)
async def get_test_case(test_case_id: str):
    """Get a test case by ID"""
    if test_case_id not in test_cases_db:
        raise HTTPException(status_code=404, detail=f"Test case {test_case_id} not found")
    
    return TestCaseResponse(**test_cases_db[test_case_id])


@router.put("/{test_case_id}", response_model=TestCaseResponse)
async def update_test_case(test_case_id: str, update: TestCaseUpdate):
    """Update a test case"""
    if test_case_id not in test_cases_db:
        raise HTTPException(status_code=404, detail=f"Test case {test_case_id} not found")
    
    test_case = test_cases_db[test_case_id]
    
    # Track modified fields
    if "modified_fields" not in test_case:
        test_case["modified_fields"] = []
    
    # Update fields if provided and track modifications
    update_dict = update.dict(exclude_unset=True)
    
    logger.info(f"Current modified_fields before update: {test_case.get('modified_fields', [])}")
    logger.info(f"Update payload: {update_dict}")
    for key, value in update_dict.items():
        if value is not None:
            # Special handling for list comparisons
            value_changed = False
            old_value = test_case.get(key, "<<NOT_SET>>")
            
            if key in test_case:
                if isinstance(value, list) and isinstance(test_case[key], list):
                    # For lists, normalize and compare sorted values to ignore order
                    # Normalize specialist names for comparison
                    def normalize_list(lst):
                        if key == "expected_specialties":
                            # Normalize specialist names: uppercase, underscores
                            return sorted([s.upper().replace(" ", "_") for s in lst])
                        return sorted(lst)
                    
                    old_normalized = normalize_list(test_case[key])
                    new_normalized = normalize_list(value)
                    value_changed = old_normalized != new_normalized
                    logger.info(f"List comparison for '{key}':")
                    logger.info(f"  Raw old: {test_case[key]}")
                    logger.info(f"  Raw new: {value}")
                    logger.info(f"  Normalized old: {old_normalized}")
                    logger.info(f"  Normalized new: {new_normalized}")
                    logger.info(f"  Changed: {value_changed}")
                else:
                    # For non-lists, direct comparison
                    value_changed = test_case[key] != value
                    logger.info(f"Value comparison for '{key}': old={test_case[key]}, new={value}, changed={value_changed}")
            else:
                # Key doesn't exist, so it's a new value
                value_changed = True
                logger.info(f"New field '{key}' with value: {value}")
            
            # Update the value if it changed
            if value_changed:
                test_case[key] = value
                # Track this field as modified (if it's a user-editable field)
                if key in ["expected_complexity", "expected_specialties", "key_data_points", "notes"]:
                    if key not in test_case["modified_fields"]:
                        test_case["modified_fields"].append(key)
                        logger.info(f"Added '{key}' to modified_fields")
                    else:
                        logger.info(f"'{key}' already in modified_fields")
            else:
                logger.info(f"No change for field '{key}', not marking as modified")
    
    logger.info(f"Final modified_fields after update: {test_case['modified_fields']}")
    
    test_case["updated_at"] = datetime.now()
    
    logger.info(f"Updated test case {test_case_id}")
    
    return TestCaseResponse(**test_case)


@router.post("/{test_case_id}/evaluate")
async def evaluate_test_case(test_case_id: str):
    """
    Run evaluation for a test case.
    
    This triggers the evaluation framework and returns the report URL.
    """
    try:
        if test_case_id not in test_cases_db:
            raise HTTPException(status_code=404, detail=f"Test case {test_case_id} not found")
        
        test_case = test_cases_db[test_case_id]
        logger.info(f"Starting evaluation for test case {test_case_id}")
        
        # Create evaluation service
        eval_service = EvaluationService()
        
        # Prepare test case in evaluation format
        test_case_data = {
            "id": test_case["id"],
            "query": test_case["query"],
            "expected_complexity": test_case["expected_complexity"],
            "expected_specialties": test_case["expected_specialties"],
            "key_data_points": test_case["key_data_points"],
            "notes": test_case["notes"],
            "category": test_case["category"],
            "based_on_real_query": test_case["based_on_real_query"],
            "trace_id": test_case["trace_id"]
        }
        
        # Run evaluation via evaluation service
        evaluation_id = await eval_service.run_evaluation(test_case_data, agent_type="cmo")
        
        # Wait for evaluation to complete (with timeout)
        max_wait_time = 30  # seconds
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < max_wait_time:
            result = await eval_service.get_evaluation_result(evaluation_id)
            if result:
                # Evaluation completed
                evaluation = eval_service.evaluations.get(evaluation_id, {})
                report_url = evaluation.get("report_url")
                
                logger.info(f"Evaluation complete for test case {test_case_id}, report at: {report_url}")
                
                return {
                    "test_case_id": test_case_id,
                    "evaluation_id": evaluation_id,
                    "overall_score": result.get("overall_score", 0),
                    "report_url": report_url,
                    "report_dir": evaluation.get("report_path"),
                    "status": "complete"
                }
            
            # Wait a bit before checking again
            await asyncio.sleep(0.5)
        
        # Timeout
        raise HTTPException(status_code=500, detail="Evaluation timed out")
        
    except Exception as e:
        logger.error(f"Error evaluating test case: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))