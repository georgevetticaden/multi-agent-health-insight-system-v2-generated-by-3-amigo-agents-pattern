# Multi-Agent System Implementation Guide

## Overview

You are implementing a Multi-Agent System following Anthropic's orchestrator-worker pattern as described in ["How we built our multi-agent research system"](https://www.anthropic.com/engineering/built-multi-agent-research-system). This guide provides the exact implementation approach using FastAPI and React with direct tool integration.

**CRITICAL**: Review these companion guides:
- `technology-requirements.md` - Exact technology stack and what NOT to use
- `dependency-management-guide.md` - Exact versions to prevent library conflicts
- `sse-implementation-guide.md` - Correct SSE patterns for streaming

## Project Structure

Your workspace should follow this structure:

```
workspace/
├── CLAUDE.md                    # This implementation guide
├── backend/
│   ├── tools/                   # Pre-built tool integrations (if provided)
│   │   └── [domain-specific tools provided by PO]
│   └── [you will create all other backend files]
├── frontend/
│   └── [you will create all frontend files]
└── requirements/               # Domain-specific requirements
    ├── technical-patterns/    # Reusable technical patterns
    ├── pm-outputs/            # Product Manager outputs
    │   └── architecture/      # Technical architecture
    ├── ux-outputs/           # UX Designer outputs
    └── po-inputs/            # Product Owner inputs (includes customization guides)
```

## Implementation Phases

### Phase 1: Understand Domain Requirements

Before writing any code:
1. Review ALL files in `requirements/` directory thoroughly
2. Understand the domain model from `requirements/pm-outputs/architecture/data-models.md`
3. Study the API contracts in `requirements/pm-outputs/architecture/api-specification.md`
4. Review UX prototypes in `requirements/ux-outputs/prototypes/`
5. Identify any pre-built tools in `backend/tools/`
6. **CRITICAL**: Check for domain-specific customization guides in `requirements/po-inputs/`:
   - Look for `*-technical-customization-guide.md` - Domain-specific agent configs, data models, API endpoints
   - Look for `*-ui-customization-guide.md` - Domain-specific colors, icons, UI components

### Phase 2: Backend Foundation

#### Step 1: Core Setup
```
backend/
├── main.py                     # FastAPI application
├── requirements.txt            # Dependencies
├── api/                       # API endpoints  
│   └── chat.py               # SSE streaming endpoint
├── models/                     # Pydantic models
├── services/                   # Business logic
│   ├── agents/               # Agent implementations
│   └── streaming/            # SSE utilities
└── tools/                     # Pre-built tools (DO NOT MODIFY)
```

Create main.py with FastAPI:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables BEFORE imports
load_dotenv()

from api import chat

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

#### Step 2: Multi-Agent Architecture

Follow this pattern for ANY domain:

```
services/
├── health_analyst_service.py    # Main orchestration service
├── agents/
│   ├── cmo/                    # Orchestrator agent
│   │   ├── cmo_agent.py
│   │   └── prompts/           # Externalized prompts
│   ├── specialist/            # Single specialist implementation
│   │   ├── specialist_agent.py
│   │   └── prompts/           # All specialist system prompts
│   └── visualization/         # Visualization generator
│       ├── visualization_agent.py
│       └── prompts/           # Visualization examples
└── streaming/
    └── sse_handler.py         # Real-time updates

**IMPORTANT**: See `requirements/po-inputs/multi-agent-implementation-architecture.md` for detailed backend structure.
```

**Generic Orchestrator Pattern**:
```python
class OrchestratorAgent:
    async def process_request(self, request: Any) -> AsyncGenerator:
        # 1. Analyze request complexity
        complexity = await self.assess_complexity(request)
        
        # 2. Create specialist tasks based on domain logic
        tasks = await self.create_tasks(request, complexity)
        
        # 3. Execute specialists (parallel when possible)
        results = await self.execute_specialists(tasks)
        
        # 4. Synthesize results
        synthesis = await self.synthesize(results)
        
        # 5. Generate visualizations if needed
        visualizations = await self.create_visualizations(synthesis)
```

**Domain Customization**: 
- The orchestrator name, specialist types, and complexity rules come from technical customization guide in `requirements/po-inputs/`
- For example, a health system might have "CMO" as orchestrator with 8 medical specialists
- A finance system might have "CFO" as orchestrator with financial analysts

#### Step 3: Specialist Implementation

**CRITICAL**: Create ONE SpecialistAgent class that handles ALL specialties:
```python
from anthropic import Anthropic
from tools.tool_registry import ToolRegistry

class SpecialistAgent:
    def __init__(self, anthropic_client, tool_registry, model):
        self.client = anthropic_client
        self.tool_registry = tool_registry
        self.prompts = SpecialistPrompts()
    
    async def execute_task_with_tools(self, task: SpecialistTask) -> SpecialistResult:
        # Get specialty-specific system prompt
        system_prompt = self._get_specialist_system_prompt(task.specialist)
        
        # Execute with Anthropic + tools
        response = await self.client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=[{"role": "user", "content": task_prompt}],
            tools=self.tools.get_tool_definitions(),
            max_tokens=4000
        )
        return self._process_response(response)
```

Specialties are defined as an enum, NOT separate classes. See the implementation architecture document for details.

#### Step 4: Visualization Agent Implementation

**CRITICAL**: For data analysis systems, implement a Visualization Agent:

```python
class VisualizationAgent:
    def __init__(self, anthropic_client):
        self.client = anthropic_client
        self.prompts = self._load_prompts()
    
    async def stream_visualization(self, query: str, results: list, synthesis: str):
        # Extract key data points from synthesis
        key_data = self._extract_data_points(results, synthesis)
        
        # Generate prompt with embedded data
        prompt = f'''
        Create a self-contained React component for this query: {query}
        
        Key data from analysis: {key_data}
        
        CRITICAL: 
        - Start with: const HealthVisualization = () => {{
        - Embed data as const rawData = [...]
        - Use Recharts components
        - DO NOT include imports
        '''
        
        # Stream the code artifact
        async for chunk in self._stream_code(prompt):
            yield {
                "type": "text",
                "content": chunk
            }
```

The visualization agent creates self-contained React components that are streamed as code artifacts and rendered in the frontend.

### Phase 3: API Implementation

Implement endpoints defined in `requirements/pm-outputs/architecture/api-specification.md`:

1. **Main Processing Endpoint** (usually with SSE)
2. **Resource Management Endpoints** (CRUD operations)
3. **Configuration Endpoints** (if needed)

### Phase 4: Frontend Implementation

#### Setup with Vite
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install -D tailwindcss@^3.3.0 postcss autoprefixer
npm install recharts@^2.10.0 lucide-react@^0.294.0 @babel/standalone@^7.23.0
npx tailwindcss init -p
```

**CRITICAL**: See `dependency-management-guide.md` for exact versions

#### Core Components Structure
```
frontend/
├── package.json         # React, Vite, Tailwind
├── vite.config.ts      # Vite configuration
├── index.html          # Entry point
├── src/
│   ├── App.tsx         # Main component
│   ├── main.tsx        # React DOM render
│   ├── index.css       # Tailwind imports
│   ├── components/
│   │   ├── ChatInterface.tsx    # Main chat UI
│   │   ├── MessageList.tsx      # Message display
│   │   ├── SpecialistPanel.tsx  # Agent status
│   │   └── Visualization.tsx    # Charts
│   ├── services/
│   │   └── api.ts              # SSE client
│   └── types/
│       └── index.ts            # TypeScript types
```

**Domain-Specific UI Customization**:
Check for UI customization guide in `requirements/po-inputs/` for:
- Color palette for agents and semantic states
- Agent icons and imagery
- Domain-specific UI components
- Animation patterns appropriate to the domain
- Trust-building elements specific to the industry

#### Key Implementation Points

1. **Simple State**: Use React useState/useEffect
2. **SSE Integration**: Native EventSource API
3. **No Complex Libraries**: No Redux, Zustand, etc.
4. **Direct API Calls**: Simple fetch/SSE to backend

#### CodeArtifact Component for Visualizations

```typescript
// components/CodeArtifact.tsx
const CodeArtifact = ({ code, isStreaming }) => {
  const [viewMode, setViewMode] = useState('code');
  
  // Execute code to render component
  const renderedComponent = useMemo(() => {
    if (isStreaming) return null;
    
    try {
      // Transform JSX with Babel
      const transformed = Babel.transform(code, {
        presets: ['react']
      });
      
      // Make Recharts available
      window.Recharts = Recharts;
      
      // Execute and render
      const Component = eval(transformed.code);
      return <Component />;
    } catch (error) {
      return <div>Error: {error.message}</div>;
    }
  }, [code, isStreaming]);
  
  return (
    <div>
      {viewMode === 'code' && <pre>{code}</pre>}
      {viewMode === 'preview' && renderedComponent}
    </div>
  );
};
```

### Phase 5: Integration

1. Connect frontend to backend APIs
2. Implement proper error handling
3. Add loading states
4. Test edge cases

## Universal Best Practices

### 1. Multi-Agent Patterns

**Orchestration**:
- Orchestrator should understand domain complexity
- Create focused tasks for specialists
- Handle parallel vs sequential execution
- Gracefully handle specialist failures

**Communication**:
- Use structured formats for inter-agent communication
- Maintain clear task boundaries
- Include confidence scores when relevant

**Tool Usage**:
- If tools are provided, understand their interfaces first
- Use Anthropic's native tool calling
- Handle tool failures gracefully
- Respect rate limits

### 2. Streaming & Real-time Updates

**FastAPI SSE Endpoint**:
```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.post("/api/chat/message")
async def chat_message(request: ChatRequest):
    async def generate():
        # Format SSE messages
        yield f"data: {json.dumps({'type': 'status', 'message': 'Processing...'})}\n\n"
        
        # Stream from orchestrator
        async for update in orchestrator.process(request.message):
            yield f"data: {json.dumps(update)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )
```

**Frontend SSE Client**:
```typescript
const eventSource = new EventSource('/api/chat/message');
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Update React state
    setMessages(prev => [...prev, data]);
};
```

### 3. Error Handling

- Implement retry logic with exponential backoff
- Provide meaningful error messages
- Log errors appropriately
- Degrade gracefully

### 4. Performance Considerations

- Use parallel processing where possible
- Implement appropriate caching
- Monitor token usage
- Optimize for user-perceived performance

## Implementation Checklist

Before starting, ensure you have:
- [ ] Read all files in requirements/
- [ ] Understood the domain model
- [ ] Reviewed API specifications
- [ ] Examined UX prototypes
- [ ] Identified pre-built tools
- [ ] Reviewed domain-specific customization guides (if provided)

During implementation:
- [ ] Follow the phased approach
- [ ] Manually verify each component works
- [ ] Implement proper error handling
- [ ] Add comprehensive logging
- [ ] Ensure type safety

Before completion:
- [ ] All APIs match specifications
- [ ] UI matches UX designs exactly
- [ ] Real-time updates work smoothly
- [ ] Error scenarios handled gracefully
- [ ] Performance meets requirements

## Simplified Architecture

The system uses a straightforward architecture:
- **No Authentication**: Focus on core functionality
- **No External Services**: No Redis, databases, or message queues
- **Direct Tool Usage**: Import pre-built tools from `backend/tools/`
- **Simple Streaming**: Direct SSE without queuing infrastructure

## Working with Pre-built Tools

When `backend/tools/` contains pre-built tools:
1. **Import them** in your services, don't recreate functionality
2. **Use their interfaces** as documented in tool-interface.md
3. **Example**:
   ```python
   from tools.health_query_tool import execute_health_query_v2
   from tools.snowflake_tool import snowflake_import_analyze_health_records_v2
   
   # In your specialist agent:
   result = await execute_health_query_v2(query_params)
   ```

## Common Pitfalls to Avoid

1. **Don't use Next.js** - Use FastAPI + React/Vite as specified
2. **Don't add Redis or databases** - Tools handle all data access
3. **Don't recreate provided tools** - Import from `backend/tools/`
4. **Don't over-engineer agents** - Keep them simple with externalized prompts
5. **Don't add authentication** - Focus on core functionality
6. **Don't use complex state management** - React state is sufficient

## Demo Setup & Running Instructions

### Backend Setup

1. **Install Dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Environment Configuration** (if needed):
   ```bash
   cp .env.example .env
   # Edit .env with any required API keys
   ```

3. **Start Backend Server**:
   ```bash
   python main.py
   # Or if using uvicorn directly:
   uvicorn main:app --reload --port 8000
   ```
   
   Backend will be available at: `http://localhost:8000`
   
   API documentation available at: `http://localhost:8000/docs`

### Frontend Setup

1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install
   # or: yarn install
   ```

2. **Start Frontend Development Server**:
   ```bash
   npm run dev
   # or: yarn dev
   ```
   
   Frontend will be available at: `http://localhost:5173` (Vite default)
   
   Or if using Create React App: `http://localhost:3000`

### Verifying the Demo

1. **Check Backend Health**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Open Frontend**:
   - Navigate to `http://localhost:5173` in your browser
   - You should see the welcome screen as designed in UX prototypes

3. **Test Core Functionality**:
   - Try the example queries provided on the welcome screen
   - Verify real-time updates are streaming
   - Check that visualizations render correctly

### Common Demo Issues

- **CORS Errors**: Ensure backend has proper CORS configuration for frontend URL
- **Port Conflicts**: Change ports in startup commands if defaults are in use
- **Missing Environment Variables**: Check console for any missing API keys
- **Connection Refused**: Verify both backend and frontend are running

### Manual Testing Checklist

- [ ] Backend starts without errors
- [ ] Frontend connects to backend successfully
- [ ] Main user flow works end-to-end
- [ ] Real-time updates display properly
- [ ] Error states show user-friendly messages
- [ ] UI matches the UX prototypes

## Success Criteria

Your implementation succeeds when:
- ✅ All requirements from PM are met
- ✅ UI matches UX specifications exactly
- ✅ Multi-agent orchestration works smoothly
- ✅ Real-time updates provide good UX
- ✅ System handles errors gracefully
- ✅ Performance meets defined SLAs

## Getting Started

1. Start by reading `requirements/pm-outputs/PRD.md`
2. Review `requirements/pm-outputs/architecture/system-architecture.md`
3. Examine `requirements/ux-outputs/prototypes/`
4. Check for any provided tools in `backend/tools/`
5. **Review technology stack**: Read `technology-requirements.md` for exact versions and constraints
6. Review `visualization-agent-pattern.md` for visualization requirements
7. **Check for customization guides**: Look for domain-specific technical and UI customization guides in `requirements/po-inputs/`
8. Begin with Phase 1 and progress systematically

Remember: The domain-specific details are in the requirements directory. This guide provides the technical patterns that work across all domains. Domain customization guides in po-inputs bridge the gap between generic patterns and specific implementations.

## Related Patterns

- [Technology Requirements](technology-requirements.md) - Exact stack and version requirements
- [Visualization Agent Pattern](visualization-agent-pattern.md) - REQUIRED for data analysis systems
- [Multi-Agent Patterns](multi-agent-patterns.md) - Orchestrator-worker architecture
- [Streaming Patterns](streaming-patterns.md) - SSE implementation details