# Technical Architecture Document: Multi-Agent Health Insight System

## System Overview

The Multi-Agent Health Insight System implements a sophisticated orchestrator-worker pattern using a simple, direct technology stack. The architecture prioritizes clarity, maintainability, and real-time user feedback while avoiding unnecessary complexity.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)                       │
│  ┌─────────────┐  ┌──────────────────┐  ┌────────────────────┐    │
│  │   Welcome   │  │   3-Panel Chat   │  │  Code Artifact     │    │
│  │   Screen    │  │    Interface     │  │  Renderer          │    │
│  └─────────────┘  └──────────────────┘  └────────────────────┘    │
│                              │                                       │
│                       EventSource (SSE)                             │
└──────────────────────────────┼─────────────────────────────────────┘
                               │ GET /api/chat/stream
┌──────────────────────────────┼─────────────────────────────────────┐
│                        Backend (FastAPI)                            │
│                              │                                      │
│  ┌───────────────────────────┴──────────────────────────────┐     │
│  │                   API Routes (SSE endpoints)               │     │
│  └───────────────────────────┬──────────────────────────────┘     │
│                              │                                      │
│  ┌───────────────────────────┴──────────────────────────────┐     │
│  │              Health Analyst Service (Orchestrator)         │     │
│  └───────────────────────────┬──────────────────────────────┘     │
│         ┌────────────────────┼────────────────────┐                │
│         │                    │                    │                 │
│  ┌──────┴──────┐  ┌─────────┴─────────┐  ┌──────┴──────┐         │
│  │ CMO Agent   │  │ Specialist Agent  │  │ Viz Agent   │         │
│  │(Orchestrator)│  │   (Workers x8)    │  │ (Generator) │         │
│  └──────┬──────┘  └─────────┬─────────┘  └─────────────┘         │
│         │                    │                                      │
│  ┌──────┴───────────────────┴──────────────────────────────┐      │
│  │              Pre-built Tools (Tool Registry)              │      │
│  │  • execute_health_query_v2                               │      │
│  │  • snowflake_import_analyze_health_records_v2            │      │
│  └──────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Backend Services Structure

```
backend/
├── main.py                          # FastAPI app entry point
├── api/
│   └── chat.py                     # SSE chat endpoints
├── services/
│   ├── health_analyst_service.py   # Main orchestration service
│   └── agents/
│       ├── cmo/
│       │   ├── cmo_agent.py       # Chief Medical Officer
│       │   └── prompts/           # CMO prompts
│       │       ├── 1_initial_analysis.txt
│       │       ├── 2_initial_analysis_summarize.txt
│       │       ├── 3_task_creation.txt
│       │       └── 4_synthesis.txt
│       ├── specialist/
│       │   ├── specialist_agent.py # Single specialist class
│       │   └── prompts/           # All specialist prompts
│       │       ├── system_cardiology.txt
│       │       ├── system_endocrinology.txt
│       │       ├── system_laboratory_medicine.txt
│       │       ├── system_data_analysis.txt
│       │       ├── system_preventive_medicine.txt
│       │       ├── system_pharmacy.txt
│       │       ├── system_nutrition.txt
│       │       ├── system_general_practice.txt
│       │       ├── 1_task_execution.txt
│       │       └── 2_final_analysis.txt
│       └── visualization/
│           ├── visualization_agent_v2.py
│           └── prompts/
│               └── visualization_examples.txt
├── models/
│   ├── agents.py                  # Agent data models
│   └── health.py                  # Health domain models
├── tools/                         # PRE-BUILT - DO NOT MODIFY
│   ├── tool_registry.py
│   └── health_query_tool.py
└── utils/
    └── streaming.py              # SSE utilities
```

### Frontend Architecture

```
frontend/
├── src/
│   ├── App.tsx                   # Main app component
│   ├── pages/
│   │   ├── Welcome.tsx          # Welcome screen
│   │   └── Chat.tsx             # 3-panel chat interface
│   ├── components/
│   │   ├── ChatPanel/           # Center chat panel
│   │   ├── ConversationList/    # Left conversation panel
│   │   ├── MedicalTeam/         # Right panel - team view
│   │   ├── Visualization/       # Right panel - viz view
│   │   └── CodeArtifact/        # Dynamic code renderer
│   ├── services/
│   │   └── api.ts               # API client with EventSource
│   ├── hooks/
│   │   ├── useSSE.ts           # SSE connection management
│   │   └── useChat.ts          # Chat state management
│   └── types/
│       ├── agents.ts            # Agent type definitions
│       └── health.ts            # Health data types
└── public/
    └── assets/                  # Static assets
```

## Multi-Agent Orchestration Pattern

### 1. CMO Agent (Orchestrator)

The Chief Medical Officer serves as the orchestrator:

```python
class CMOAgent:
    def __init__(self, anthropic_client, tool_registry, model):
        self.client = anthropic_client
        self.tool_registry = tool_registry
        self.model = model
        self.prompts = CMOPrompts()  # Loads externalized prompts
    
    async def analyze_query_with_tools(self, query: str):
        # 1. Initial assessment using tools
        # 2. Determine complexity level
        # 3. Return initial insights and approach
    
    async def create_specialist_tasks(self, query, complexity, approach):
        # Create specific tasks for each specialist
        # Returns list of SpecialistTask objects
    
    async def synthesize_findings(self, specialist_results):
        # Combine all specialist insights
        # Create comprehensive summary
```

### 2. Specialist Agent (Workers)

A single class handles all specialties through prompts:

```python
class SpecialistAgent:
    def __init__(self, anthropic_client, tool_registry, model):
        self.client = anthropic_client
        self.tool_registry = tool_registry
        self.model = model
        self.prompts = SpecialistPrompts()
    
    async def execute_task_with_tools(self, task: SpecialistTask):
        # Get specialty-specific system prompt
        system_prompt = self._get_specialist_system_prompt(task.specialist)
        
        # Execute task with appropriate tools
        # Return SpecialistResult
```

### 3. Medical Specialties

```python
class MedicalSpecialty(Enum):
    GENERAL_PRACTICE = "general_practice"      # Dr. Primary
    ENDOCRINOLOGY = "endocrinology"           # Dr. Hormone
    CARDIOLOGY = "cardiology"                 # Dr. Heart
    NUTRITION = "nutrition"                   # Dr. Nutrition
    PREVENTIVE_MEDICINE = "preventive_medicine" # Dr. Prevention
    LABORATORY_MEDICINE = "laboratory_medicine" # Dr. Lab
    PHARMACY = "pharmacy"                     # Dr. Pharma
    DATA_ANALYSIS = "data_analysis"           # Dr. Analytics
```

## Data Flow

### 1. Query Submission Flow

```
User Input → Frontend Validation → API Call
    ↓
POST /api/chat/message
    ↓
EventSource Connection Established
    ↓
SSE Events Begin Streaming
```

### 2. Agent Orchestration Flow

```
Query Received
    ↓
CMO Initial Analysis (with tools)
    ↓
Complexity Assessment (Simple/Standard/Complex/Critical)
    ↓
Specialist Task Creation
    ↓
Parallel Specialist Execution
    ↓
CMO Synthesis
    ↓
Visualization Generation
    ↓
Stream Results to Frontend
```

### 3. SSE Event Flow

```python
# Event Types
{
    "event": "connected",
    "data": {"message": "Connection established"}
}

{
    "event": "message", 
    "data": {
        "type": "thinking|text|tool_call|specialist_update",
        "content": "..."
    }
}

{
    "event": "visualization",
    "data": {
        "code": "```javascript\n// React component code\n```"
    }
}

{
    "event": "done",
    "data": {"message": "Analysis complete"}
}
```

## Tool Integration Architecture

### Tool Registry Pattern

```python
# Tools are PRE-BUILT and imported
from tools.tool_registry import ToolRegistry
from tools.health_query_tool import execute_health_query_v2

class HealthAnalystService:
    def __init__(self):
        self.tool_registry = ToolRegistry()
        
        # Agents receive tool registry
        self.cmo_agent = CMOAgent(
            self.client,
            self.tool_registry,
            model="claude-3-sonnet-20240229"
        )
```

### Tool Usage in Agents

```python
# Direct tool usage
result = await self.tool_registry.execute_tool(
    "execute_health_query_v2",
    {"query": "Show cholesterol trends"}
)

# Or via Anthropic's native tool calling
response = await self.client.messages.create(
    model=self.model,
    messages=messages,
    tools=self.tool_registry.get_tool_definitions(),
    max_tokens=4000
)
```

## Streaming Architecture (SSE)

### Backend SSE Implementation

```python
@router.get("/api/chat/stream")
async def stream_chat(message: str = Query(...)):
    async def generate():
        # Anti-buffering headers
        yield f"data: {json.dumps({'type': 'connected'})}\n\n"
        await asyncio.sleep(0.001)  # Force flush
        
        # Process query
        async for update in health_analyst_service.process_query(message):
            yield f"data: {json.dumps(update)}\n\n"
            await asyncio.sleep(0.001)  # Force flush
            
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return EventSourceResponse(
        generate(),
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )
```

### Frontend SSE Consumption

```typescript
const eventSource = new EventSource(
    `/api/chat/stream?message=${encodeURIComponent(message)}`
);

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleStreamUpdate(data);
};

eventSource.onerror = () => {
    // Automatic reconnection
};
```

## State Management

### Frontend State Structure

```typescript
interface AppState {
    conversations: Conversation[];
    activeConversation: string;
    messages: Message[];
    agents: AgentStatus[];
    visualizations: Visualization[];
    activeQuery: number;
    streamingStatus: StreamingStatus;
}

interface AgentStatus {
    id: string;
    name: string;
    specialty: string;
    status: 'waiting' | 'active' | 'complete' | 'error';
    progress: number;
    result?: SpecialistResult;
}
```

### Backend State Management

- Stateless service design
- All state in frontend or passed via API
- No session management required
- Tools handle data persistence

## Security Architecture

### API Security
- HTTPS only in production
- Input validation and sanitization
- Rate limiting per IP
- No PII in logs

### Data Security
- Health data never stored in backend
- Tools handle secure data access
- No caching of sensitive data
- Encrypted transmission

## Performance Optimization

### Backend Optimizations
- Parallel specialist execution
- Streaming results as available
- Efficient prompt management
- Token budget controls

### Frontend Optimizations
- Code splitting for visualizations
- Lazy loading of components
- Virtual scrolling for long chats
- Debounced API calls

## Error Handling Strategy

### Backend Error Handling
```python
try:
    result = await specialist.execute_task(task)
except Exception as e:
    # Log error, continue with other specialists
    # Include partial results in synthesis
```

### Frontend Error Recovery
- Automatic SSE reconnection
- Graceful degradation
- User-friendly error messages
- Retry mechanisms

## Deployment Architecture

### Development
```bash
# Backend
cd backend && uvicorn main:app --reload

# Frontend  
cd frontend && npm run dev
```

### Production
- Backend: FastAPI with Uvicorn workers
- Frontend: Static build served via CDN
- No external services required
- Environment-based configuration

## Monitoring and Observability

### Key Metrics
- Query completion rates
- Agent execution times
- Token usage per query
- SSE connection stability
- Error rates by specialist

### Logging Strategy
- Structured JSON logging
- Correlation IDs for request tracking
- No PII in logs
- Performance timing logs

## Scalability Considerations

### Horizontal Scaling
- Stateless backend enables easy scaling
- Load balancer with sticky sessions for SSE
- Tool layer handles data scaling

### Vertical Scaling
- Async processing for all I/O
- Efficient memory usage
- Controlled concurrency

This architecture provides a robust foundation for multi-agent orchestration while maintaining simplicity and extensibility for adaptation to other domains.