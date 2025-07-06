# Simplified Architecture Brief

## Core Architecture Principles

This system follows a **simple, direct implementation** approach:

### Technology Stack (Required)
- **Backend**: FastAPI (Python)
- **Frontend**: React with Vite
- **AI**: Anthropic Claude API
- **Streaming**: Server-Sent Events (SSE)
- **Data Access**: Pre-built tools (provided)

### What We're NOT Using
- ❌ Next.js (neither for backend nor frontend)
- ❌ Redis or any caching layer
- ❌ Databases (tools handle data)
- ❌ Message queues or task workers
- ❌ Authentication systems
- ❌ Complex state management (Redux, Zustand)

## Implementation Approach

### 1. Direct Tool Integration
```python
# Tools are pre-built and provided
from tools.tool_registry import ToolRegistry

# Simply use them in agents
tools = ToolRegistry()
result = await tools.execute_tool("execute_health_query_v2", {"query": "..."})
```

### 2. Simple Agent Pattern
```python
class SpecialistAgent:
    def __init__(self, name, specialty):
        self.client = Anthropic()
        self.tools = ToolRegistry()
        self.prompts = self._load_prompts()  # From .txt files
    
    async def analyze(self, task):
        # Direct API call with tools
        return await self.client.messages.create(...)
```

### 3. Direct SSE Streaming
```python
# FastAPI endpoint
@router.post("/api/chat/message")
async def chat_message(request):
    async def generate():
        async for update in orchestrator.process(request):
            yield f"data: {json.dumps(update)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### 4. React Frontend
```bash
# Setup
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install

# Simple component structure
src/
├── App.tsx
├── components/
├── services/api.ts
└── types/
```

## Why This Architecture?

1. **Simplicity**: Easy to understand, modify, and debug
2. **Direct**: No unnecessary abstraction layers
3. **Fast Development**: Can be built quickly
4. **Clear Boundaries**: Each component has one job
5. **Tool-Focused**: Leverages pre-built capabilities

## Data Flow

```
User Query → React UI → FastAPI → CMO Agent → Specialist Agents
                ↓                      ↓              ↓
              SSE Updates         Tool Calls     Tool Calls
                ↓                      ↓              ↓
            Real-time UI          Health Data    Health Data
```

## Key Implementation Notes

1. **Agents are thin orchestrators** - Most logic is in prompts
2. **Tools handle all data access** - No database code needed
3. **SSE provides real-time updates** - No polling or WebSockets
4. **React state is sufficient** - No complex state management
5. **FastAPI handles everything** - Simple, fast, async

## Getting Started

1. Backend: `cd backend && python main.py`
2. Frontend: `cd frontend && npm run dev`
3. That's it - no complex setup required