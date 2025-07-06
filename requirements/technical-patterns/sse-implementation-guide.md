# SSE (Server-Sent Events) Implementation Guide

## Overview
This guide provides the correct implementation pattern for SSE streaming in the Multi-Agent Health System, addressing common issues found during development.

## Backend SSE Implementation

### FastAPI SSE Endpoint (Correct Pattern)

```python
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import json
import asyncio

router = APIRouter()

@router.get("/api/chat/stream")
async def chat_stream(request: Request, message: str):
    """
    SSE endpoint - MUST use GET method with query parameters
    """
    async def generate():
        try:
            # Critical: Add small delay to prevent buffering
            await asyncio.sleep(0.001)
            
            # Send initial connection event
            yield {
                "event": "connected",
                "data": json.dumps({"status": "connected"})
            }
            
            # Process message
            async for update in health_analyst.process_query(message):
                # Format SSE message
                yield {
                    "event": "message",
                    "data": json.dumps(update)
                }
                # Critical: Small delay for proper flushing
                await asyncio.sleep(0.001)
            
            # Send completion event
            yield {
                "event": "done",
                "data": json.dumps({"status": "complete"})
            }
            
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
    
    # Critical headers to prevent buffering
    return EventSourceResponse(
        generate(),
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )

# Alternative: Using StreamingResponse
@router.post("/api/chat/message")
async def chat_message_post(request: ChatRequest):
    """
    POST endpoint with SSE - requires custom implementation
    """
    async def generate():
        async for update in health_analyst.process_query(request.message):
            # Manual SSE formatting
            yield f"event: message\n"
            yield f"data: {json.dumps(update)}\n\n"
            await asyncio.sleep(0.001)
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )
```

### SSE Message Formatter

```python
class SSEFormatter:
    @staticmethod
    def format_message(event_type: str, data: dict) -> str:
        """Format message for SSE protocol"""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    
    @staticmethod
    def text(content: str) -> dict:
        return {
            "type": "text",
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def tool_call(tool_name: str, args: dict) -> dict:
        return {
            "type": "tool_call",
            "tool": tool_name,
            "arguments": args,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def specialist_update(specialist: str, status: str) -> dict:
        return {
            "type": "specialist_update",
            "specialist": specialist,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
```

## Frontend SSE Implementation

### Correct EventSource Usage

```typescript
// services/sse.ts
export class SSEService {
  private eventSource: EventSource | null = null;
  private reconnectTimeout: number = 3000;
  private reconnectAttempts: number = 0;
  
  connect(message: string, handlers: SSEHandlers): void {
    // For GET endpoint (recommended)
    const url = `/api/chat/stream?message=${encodeURIComponent(message)}`;
    
    this.eventSource = new EventSource(url);
    
    // Handle different event types
    this.eventSource.addEventListener('message', (event) => {
      try {
        const data = JSON.parse(event.data);
        handlers.onMessage?.(data);
      } catch (e) {
        console.error('Failed to parse SSE message:', e);
      }
    });
    
    this.eventSource.addEventListener('connected', (event) => {
      this.reconnectAttempts = 0;
      handlers.onConnect?.();
    });
    
    this.eventSource.addEventListener('done', (event) => {
      handlers.onComplete?.();
      this.disconnect();
    });
    
    this.eventSource.addEventListener('error', (event) => {
      if (event.target.readyState === EventSource.CLOSED) {
        handlers.onError?.('Connection closed');
        this.attemptReconnect(message, handlers);
      }
    });
  }
  
  private attemptReconnect(message: string, handlers: SSEHandlers): void {
    if (this.reconnectAttempts < 3) {
      this.reconnectAttempts++;
      setTimeout(() => {
        this.connect(message, handlers);
      }, this.reconnectTimeout * this.reconnectAttempts);
    }
  }
  
  disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}
```

### POST Endpoint with Fetch + SSE (Alternative)

```typescript
// For POST endpoints that return SSE
async function streamChat(message: string, onUpdate: (data: any) => void) {
  const response = await fetch('/api/chat/message', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message })
  });
  
  if (!response.ok) {
    throw new Error('Failed to start stream');
  }
  
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  
  if (!reader) {
    throw new Error('No response body');
  }
  
  let buffer = '';
  
  while (true) {
    const { done, value } = await reader.read();
    
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    
    // Parse SSE messages from buffer
    const messages = buffer.split('\n\n');
    buffer = messages.pop() || '';
    
    for (const message of messages) {
      if (message.trim()) {
        const lines = message.split('\n');
        let eventType = 'message';
        let eventData = '';
        
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7);
          } else if (line.startsWith('data: ')) {
            eventData = line.slice(6);
          }
        }
        
        if (eventData) {
          try {
            const data = JSON.parse(eventData);
            onUpdate(data);
          } catch (e) {
            console.error('Failed to parse:', e);
          }
        }
      }
    }
  }
}
```

## Common SSE Issues & Solutions

### Issue: Messages Not Streaming (Buffering)
**Solution**: Add critical headers and delays
```python
# Backend
await asyncio.sleep(0.001)  # Force flush
headers = {
    'X-Accel-Buffering': 'no',  # Disable nginx buffering
    'Cache-Control': 'no-cache'
}
```

### Issue: Connection Drops
**Solution**: Implement reconnection logic
```typescript
// Frontend
const MAX_RECONNECT_ATTEMPTS = 3;
const RECONNECT_DELAY = 3000;
```

### Issue: CORS Errors
**Solution**: Configure CORS properly
```python
# Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    expose_headers=["*"]
)
```

### Issue: EventSource Doesn't Support POST
**Solution**: Use GET with query params or fetch API
```typescript
// Option 1: GET with query
const eventSource = new EventSource(`/api/chat/stream?message=${encodeURIComponent(message)}`);

// Option 2: Custom fetch implementation
const response = await fetch('/api/chat/message', { method: 'POST', ... });
```

## Testing SSE Implementation

### Backend Test
```bash
# Test SSE endpoint
curl -N -H "Accept: text/event-stream" \
  "http://localhost:8000/api/chat/stream?message=test"
```

### Frontend Test
```typescript
// Test connection
const sse = new SSEService();
sse.connect('test message', {
  onMessage: (data) => console.log('Received:', data),
  onError: (error) => console.error('Error:', error),
  onComplete: () => console.log('Complete')
});
```

## Best Practices

1. **Always use GET for EventSource** - It's the standard
2. **Add small delays** - Ensures proper flushing
3. **Include reconnection logic** - Network issues happen
4. **Use typed events** - Better error handling
5. **Monitor connection state** - Show UI indicators
6. **Clean up connections** - Prevent memory leaks
7. **Test with real latency** - Use network throttling