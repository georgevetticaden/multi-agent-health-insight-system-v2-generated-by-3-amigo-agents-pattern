from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List
import json
import asyncio
from datetime import datetime

from services.health_analyst_service import HealthAnalystService

router = APIRouter()
health_service = HealthAnalystService()

# In-memory storage for threads (in production, use a database)
threads_storage: Dict[str, Dict[str, Any]] = {}

@router.get("/api/chat/message")
async def chat_message(message: str = Query(..., description="Health query to analyze")):
    """
    Stream health analysis results using Server-Sent Events
    
    This endpoint returns events in the expected format for the frontend,
    providing real-time updates as the analysis progresses.
    """
    
    async def generate_sse_events():
        try:
            # Send initial connection event
            yield f"event: message\ndata: {json.dumps({'type': 'connected', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Process the health query
            async for event in health_service.process_health_query(message):
                # Format event for SSE with proper event type
                if event.get("type") == "error":
                    yield f"event: error\ndata: {json.dumps(event)}\n\n"
                else:
                    yield f"event: message\ndata: {json.dumps(event)}\n\n"
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.001)
                
        except Exception as e:
            error_event = {
                "type": "error",
                "content": f"An error occurred: {str(e)}"
            }
            yield f"event: error\ndata: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        generate_sse_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Transfer-Encoding": "chunked",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@router.get("/api/threads")
async def get_threads():
    """Get all conversation threads"""
    return {
        "threads": list(threads_storage.values())
    }

@router.post("/api/threads")
async def create_thread(thread_data: Dict[str, Any]):
    """Create a new conversation thread"""
    thread_id = str(int(datetime.now().timestamp()))
    thread = {
        "id": thread_id,
        "title": thread_data.get("title", "New Conversation"),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "messages": [],
        "metadata": thread_data.get("metadata", {})
    }
    threads_storage[thread_id] = thread
    return thread

@router.get("/api/threads/{thread_id}")
async def get_thread(thread_id: str):
    """Get a specific thread by ID"""
    if thread_id not in threads_storage:
        raise HTTPException(status_code=404, detail="Thread not found")
    return threads_storage[thread_id]

@router.put("/api/threads/{thread_id}")
async def update_thread(thread_id: str, update_data: Dict[str, Any]):
    """Update a thread"""
    if thread_id not in threads_storage:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    thread = threads_storage[thread_id]
    thread.update(update_data)
    thread["updated_at"] = datetime.now().isoformat()
    return thread

@router.delete("/api/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """Delete a thread"""
    if thread_id not in threads_storage:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    del threads_storage[thread_id]
    return {"status": "deleted"}

@router.delete("/api/threads/clear")
async def clear_all_threads():
    """Clear all threads"""
    threads_storage.clear()
    return {"status": "cleared", "count": 0}

@router.post("/api/health/import")
async def import_health_data(import_request: Dict[str, Any]):
    """
    Trigger health data import from Snowflake
    
    This would typically call the snowflake_import_analyze_health_records_v2 tool
    """
    try:
        # In a real implementation, this would trigger the import process
        # For now, return a mock response
        return {
            "status": "success",
            "message": "Health data import initiated",
            "records_processed": 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/health/query")
async def execute_health_query(query_request: Dict[str, Any]):
    """
    Execute a direct health query using the tools
    
    This endpoint allows direct querying without the full agent orchestration
    """
    try:
        query = query_request.get("query", "")
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # In a real implementation, this would use the tool registry
        # to execute the query directly
        return {
            "status": "success",
            "query": query,
            "results": [],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))