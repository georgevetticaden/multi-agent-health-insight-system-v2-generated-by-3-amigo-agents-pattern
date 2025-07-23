import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse
import asyncio

from services.qe_analyst_service import QEAnalystService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize QE service
qe_service = QEAnalystService()

def format_sse_message(data: Dict[str, Any]) -> dict:
    """Format message for SSE transmission"""
    return {
        "event": "message",
        "data": json.dumps(data)
    }

@router.get("/api/qe/chat/stream")
async def qe_chat_stream(
    trace_id: str = Query(..., description="Trace ID to analyze"),
    message: str = Query(..., description="User message"),
    stage_name: Optional[str] = Query(None, description="Stage name if discussing specific stage"),
    stage_id: Optional[str] = Query(None, description="Stage ID if discussing specific stage")
):
    """Stream QE agent responses for trace analysis
    
    This endpoint follows the same SSE pattern as the main chat endpoint.
    """
    
    # Build stage context if provided
    stage_context = None
    if stage_name or stage_id:
        stage_context = {
            "stage_name": stage_name,
            "stage_id": stage_id
        }
    
    async def generate():
        try:
            logger.info(f"Starting QE chat stream for trace {trace_id}, message: {message[:50]}...")
            event_count = 0
            
            # Add initial delay to prevent buffering
            await asyncio.sleep(0.001)
            
            # Process through QE service
            async for event in qe_service.process_qe_request(
                trace_id=trace_id,
                message=message,
                stage_context=stage_context
            ):
                event_count += 1
                logger.debug(f"QE stream event #{event_count}: type={event.get('type')}, content_length={len(str(event.get('content', '')))}")
                yield format_sse_message(event)
                await asyncio.sleep(0.001)  # Force flush
            
            # Send done event to properly close the stream
            yield format_sse_message({"type": "done"})
            await asyncio.sleep(0.001)
            
            logger.info(f"QE chat stream completed successfully after {event_count} events")
                
        except Exception as e:
            logger.error(f"Error in QE chat stream: {e}", exc_info=True)
            yield format_sse_message({
                "type": "error",
                "content": f"Stream error: {str(e)}"
            })
    
    return EventSourceResponse(
        generate(),
        headers={
            'X-Accel-Buffering': 'no',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
    )

@router.get("/api/qe/trace-context/{trace_id}")
async def get_trace_context(trace_id: str):
    """Get the current trace context loaded in QE agent"""
    
    agent = qe_service.agents.get(trace_id)
    if not agent or not agent.current_trace_context:
        raise HTTPException(
            status_code=404,
            detail="Trace context not found. Start a chat first."
        )
    
    return {
        "trace_id": trace_id,
        "context": agent.current_trace_context,
        "identified_issues": agent.identified_issues
    }

@router.get("/api/qe/conversation-summary/{trace_id}")
async def get_conversation_summary(trace_id: str):
    """Get summary of QE conversation for a trace"""
    
    summary = qe_service.get_agent_summary(trace_id)
    if not summary:
        raise HTTPException(
            status_code=404,
            detail="No conversation found for this trace"
        )
    
    return summary

@router.post("/api/qe/reset/{trace_id}")
async def reset_conversation(trace_id: str):
    """Reset the QE conversation for a trace"""
    
    qe_service.reset_agent(trace_id)
    return {"status": "success", "message": "Conversation reset"}

@router.post("/api/qe/evaluation-result/{trace_id}")
async def update_evaluation_result(trace_id: str, result: Dict[str, Any]):
    """Update QE Agent with evaluation results from frontend
    
    This endpoint is called by the frontend after evaluation completes
    to pass the results back to the QE Agent so the 'details' command works.
    """
    logger.info(f"Updating QE Agent with evaluation result for trace {trace_id}")
    logger.info(f"Result overall score: {result.get('overall_score', 'N/A')}")
    
    success = qe_service.set_evaluation_result(trace_id, result)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"No QE Agent found for trace {trace_id}. Start a chat first."
        )
    
    return {
        "status": "success",
        "message": "Evaluation result updated",
        "trace_id": trace_id
    }

@router.get("/api/qe/report/{report_name}/{filename:path}")
async def serve_evaluation_report(report_name: str, filename: str):
    """Serve evaluation report HTML and asset files
    
    This endpoint serves the evaluation report files to avoid file:// URL security issues.
    The report_name is the directory name in evaluation_results/qe_reports/
    Supports nested paths like report/report.html or report/dimension_scores.png
    """
    # Construct the file path safely using absolute path
    backend_dir = Path(__file__).parent.parent
    base_path = backend_dir / "evaluation_results" / "qe_reports"
    report_path = base_path / report_name / filename
    
    # Security check - ensure the resolved path is within the base directory
    try:
        report_path = report_path.resolve()
        base_path = base_path.resolve()
        if not str(report_path).startswith(str(base_path)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check if file exists
    if not report_path.exists():
        raise HTTPException(status_code=404, detail=f"Report file not found: {filename}")
    
    # Determine media type
    media_type = "application/octet-stream"
    if filename.endswith(".html"):
        media_type = "text/html"
    elif filename.endswith(".png"):
        media_type = "image/png"
    elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
        media_type = "image/jpeg"
    elif filename.endswith(".json"):
        media_type = "application/json"
    elif filename.endswith(".css"):
        media_type = "text/css"
    elif filename.endswith(".js"):
        media_type = "application/javascript"
    
    # Serve the file
    return FileResponse(
        path=report_path,
        media_type=media_type,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )