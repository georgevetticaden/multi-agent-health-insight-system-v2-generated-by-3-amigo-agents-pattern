import json
import asyncio
from typing import AsyncIterator, Dict, Any
from sse_starlette.sse import EventSourceResponse

class SSEManager:
    @staticmethod
    def create_event(event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "event": event_type,
            "data": json.dumps(data)
        }
    
    @staticmethod
    async def generate_sse_events(event_generator: AsyncIterator[Dict[str, Any]]) -> AsyncIterator[str]:
        await asyncio.sleep(0.001)
        
        async for event in event_generator:
            if isinstance(event, dict) and "event" in event and "data" in event:
                yield f"event: {event['event']}\ndata: {event['data']}\n\n"
            else:
                yield f"data: {json.dumps(event)}\n\n"
            
            await asyncio.sleep(0.001)
    
    @staticmethod
    def create_sse_response(event_generator: AsyncIterator[Dict[str, Any]]) -> EventSourceResponse:
        return EventSourceResponse(
            SSEManager.generate_sse_events(event_generator),
            headers={
                'X-Accel-Buffering': 'no',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Connection': 'keep-alive',
                'Transfer-Encoding': 'chunked',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )