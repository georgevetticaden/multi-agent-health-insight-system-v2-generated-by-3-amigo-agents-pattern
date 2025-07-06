# SSE Streaming Patterns for Multi-Agent Systems

## Overview
Server-Sent Events (SSE) enable real-time communication from server to client, crucial for multi-agent systems where analysis can take time and users need feedback.

**CRITICAL**: Also review `sse-implementation-guide.md` for detailed implementation patterns and common issues.

## Core SSE Implementation

### Backend Pattern (FastAPI)
```python
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

# CORRECT: Use GET endpoint for EventSource
@app.get("/api/chat/stream")
async def stream_endpoint(message: str):
    async def event_generator():
        # CRITICAL: Add delay to prevent buffering
        await asyncio.sleep(0.001)
        
        # Send initial connection event
        yield {
            "event": "connected",
            "data": json.dumps({"status": "connected"})
        }
        
        # Process and stream updates
        async for update in process_request(message):
            yield {
                "event": "message", 
                "data": json.dumps(update)
            }
            await asyncio.sleep(0.001)  # Force flush
        
        # Send completion
        yield {
            "event": "done",
            "data": json.dumps({"status": "complete"})
        }
    
    return EventSourceResponse(
        event_generator(),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
            "Connection": "keep-alive"
        }
    )
```

### Frontend Pattern (React/TypeScript)
```typescript
interface SSEMessage {
    type: string;
    [key: string]: any;
}

const useSSEConnection = (message: string) => {
    const [messages, setMessages] = useState<SSEMessage[]>([]);
    const [status, setStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
    
    useEffect(() => {
        // CORRECT: Use GET with query parameter
        const url = `/api/chat/stream?message=${encodeURIComponent(message)}`;
        const eventSource = new EventSource(url);
        
        eventSource.addEventListener('connected', (event) => {
            setStatus('connected');
        });
        
        eventSource.addEventListener('message', (event) => {
            const data = JSON.parse(event.data);
            setMessages(prev => [...prev, data]);
            handleMessageType(data);
        });
        
        eventSource.addEventListener('done', (event) => {
            eventSource.close();
            setStatus('completed');
        });
        
        eventSource.onerror = () => {
            setStatus('error');
            eventSource.close();
        };
        
        return () => eventSource.close();
    }, [message]);
    
    return { messages, status };
};
```

## Message Type Patterns

### 1. Status Updates
Inform users about system state changes.

```json
{
    "type": "status",
    "status": "analyzing",
    "message": "Analyzing your request complexity..."
}
```

### 2. Specialist Activation
Show which specialists are being engaged.

```json
{
    "type": "specialist_activated",
    "specialist": "DataAnalyst",
    "task": "Analyzing trends in your data",
    "icon": "📊"
}
```

### 3. Progress Updates
Provide granular progress for long-running tasks.

```json
{
    "type": "progress",
    "specialist": "DataAnalyst", 
    "progress": 65,
    "current_action": "Processing historical data"
}
```

### 4. Thinking/Reasoning
Share agent reasoning for transparency.

```json
{
    "type": "thinking",
    "agent": "Orchestrator",
    "thought": "This request requires both financial and risk analysis...",
    "visible": true
}
```

### 5. Tool Calls
Show when agents use tools.

```json
{
    "type": "tool_call",
    "tool": "data_query",
    "parameters": {"query": "SELECT * FROM transactions WHERE..."},
    "specialist": "DataAnalyst"
}
```

### 6. Partial Results
Stream results as they become available.

```json
{
    "type": "partial_result",
    "specialist": "RiskAnalyst",
    "result": {
        "risk_score": 7.2,
        "confidence": 0.85
    }
}
```

### 7. Synthesis Updates
Show orchestrator combining results.

```json
{
    "type": "synthesis",
    "message": "Combining insights from 3 specialists...",
    "specialists_complete": ["DataAnalyst", "RiskAnalyst"],
    "specialists_pending": ["ComplianceExpert"]
}
```

## UI Update Patterns

### Progressive Revelation
```typescript
const MessageHandler = ({ message }: { message: SSEMessage }) => {
    switch (message.type) {
        case 'specialist_activated':
            return <SpecialistCard specialist={message.specialist} status="active" />;
            
        case 'progress':
            return <ProgressBar value={message.progress} label={message.current_action} />;
            
        case 'partial_result':
            return <ResultPreview data={message.result} specialist={message.specialist} />;
            
        default:
            return null;
    }
};
```

### State Management
```typescript
interface SystemState {
    orchestratorStatus: 'idle' | 'thinking' | 'delegating' | 'synthesizing';
    specialists: Map<string, SpecialistState>;
    results: Map<string, any>;
}

const reduceSSEMessage = (state: SystemState, message: SSEMessage): SystemState => {
    switch (message.type) {
        case 'specialist_activated':
            return {
                ...state,
                specialists: new Map(state.specialists).set(
                    message.specialist,
                    { status: 'active', task: message.task }
                )
            };
        // ... other cases
    }
};
```

## Error Handling Patterns

### Graceful Degradation
```typescript
eventSource.onerror = (error) => {
    if (eventSource.readyState === EventSource.CLOSED) {
        // Connection closed cleanly
        setStatus('completed');
    } else {
        // Actual error - attempt reconnection
        setTimeout(() => {
            reconnect();
        }, 5000);
    }
};
```

### Timeout Handling
```python
async def with_timeout(coro, timeout_seconds=30):
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        yield format_sse({
            "type": "timeout",
            "message": "Analysis is taking longer than expected...",
            "action": "continuing"
        })
```

## Performance Optimizations

### 1. Batching Updates
```python
async def batch_updates(updates_queue, batch_size=5, max_wait=0.1):
    batch = []
    while True:
        try:
            update = await asyncio.wait_for(
                updates_queue.get(),
                timeout=max_wait
            )
            batch.append(update)
            
            if len(batch) >= batch_size:
                yield format_sse({"type": "batch", "updates": batch})
                batch = []
        except asyncio.TimeoutError:
            if batch:
                yield format_sse({"type": "batch", "updates": batch})
                batch = []
```

### 2. Compression
```python
# For large data updates
import gzip
import base64

def compress_large_data(data):
    json_str = json.dumps(data)
    if len(json_str) > 1000:  # Compress if large
        compressed = gzip.compress(json_str.encode())
        return {
            "compressed": True,
            "data": base64.b64encode(compressed).decode()
        }
    return data
```

### 3. Selective Updates
```typescript
// Only update UI for relevant changes
const shouldUpdateUI = (message: SSEMessage): boolean => {
    const significantTypes = [
        'specialist_activated',
        'specialist_complete',
        'partial_result',
        'error'
    ];
    return significantTypes.includes(message.type);
};
```

## Testing Patterns

### Mock SSE Server
```python
async def mock_sse_generator():
    """Generate mock SSE events for testing"""
    events = [
        {"type": "status", "message": "Starting analysis"},
        {"type": "specialist_activated", "specialist": "Expert1"},
        {"type": "progress", "progress": 50},
        {"type": "complete", "result": {"answer": "42"}}
    ]
    
    for event in events:
        yield format_sse(event)
        await asyncio.sleep(0.5)  # Simulate processing time
```

### Frontend Testing
```typescript
// Mock EventSource for testing
class MockEventSource {
    onmessage: (event: MessageEvent) => void;
    
    constructor(url: string) {
        setTimeout(() => {
            this.simulateMessages();
        }, 100);
    }
    
    simulateMessages() {
        const messages = [/* test messages */];
        messages.forEach((msg, i) => {
            setTimeout(() => {
                this.onmessage(new MessageEvent('message', { data: JSON.stringify(msg) }));
            }, i * 100);
        });
    }
}
```

## Best Practices

1. **Always Send Heartbeats**
   ```python
   async def heartbeat():
       while True:
           yield format_sse({"type": "heartbeat"})
           await asyncio.sleep(30)
   ```

2. **Include Request IDs**
   ```json
   {
       "type": "status",
       "request_id": "req_123",
       "message": "Processing"
   }
   ```

3. **Implement Reconnection Logic**
   ```typescript
   const reconnectingEventSource = (url: string, maxRetries = 3) => {
       let retries = 0;
       const connect = () => {
           const es = new EventSource(url);
           es.onerror = () => {
               if (retries < maxRetries) {
                   retries++;
                   setTimeout(connect, 1000 * retries);
               }
           };
           return es;
       };
       return connect();
   };
   ```

4. **Clean Up Properly**
   ```python
   async def cleanup_on_disconnect():
       try:
           yield from event_generator()
       finally:
           # Clean up resources
           await cleanup_agents()
   ```

## Conclusion

SSE provides an elegant solution for real-time updates in multi-agent systems. Key takeaways:
- Use typed messages for different update types
- Implement proper error handling and reconnection
- Optimize for performance with batching and compression
- Test thoroughly with mock implementations
- Always provide meaningful progress updates to users