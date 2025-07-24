# CLAUDE.md

Multi-Agent Health Insight System - Powered by Anthropic Claude + Snowflake Cortex.

## Development Mode: Enhancement & Feature Development

The Multi-Agent Health Insight System has been successfully implemented based on the PM outputs, UX prototypes, and technical patterns. This document now serves two purposes:

1. **Part 1: System Creation Guide (Historical Reference)** - How the system was built
2. **Part 2: Enhancement & Feature Development Guide (Active)** - How to extend and improve the system

## System Architecture Highlights

### Multi-Agent Health System
- **Orchestrator-Worker Pattern**: CMO agent orchestrates 8 medical specialists
- **SSE Streaming**: Real-time updates with proper event handling
- **Visualization Engine**: Generates self-contained React components with embedded data
- **Tool Integration**: Pre-built Snowflake Cortex tools for health data queries

### Evaluation Framework
- **Metadata-Driven Architecture**: BaseEvaluator provides generic, extensible foundation
- **Hybrid Evaluation Methods**: Combines deterministic rules with LLM Judge evaluation
- **Unified Data Storage**: All evaluation data in centralized `/evaluation/data/` directory
- **Multi-Agent Support**: Separate test schemas and evaluators for CMO, Specialist, and Visualization agents
- **Subprocess Execution**: Clean separation between web UI and evaluation framework

### Trace Viewer Features
- **Hierarchical Event Display**: Clear visualization of multi-agent execution flow
- **Smart Content Formatting**: Automatic detection and formatting of LLM responses, tool calls, and data
- **Timeline Navigation**: Click on execution stages to jump to corresponding agent analysis
- **Standalone HTML Viewer**: View traces without backend server running

---

# Part 1: System Creation Guide (Historical Reference)

## Pre-Implementation Checklist

Before starting, ensure you understand:
□ All PM outputs (PRD, architecture, APIs, data models)

□ UX prototypes (open the HTML files!)

□ Pre-built tools (what's provided, how to use them)

□ Technical patterns (implementation guide is the master doc)

□ Visualization agent requirement (generates React components)

□ No Redis, no Next.js, no databases

□ FastAPI + React/Vite only

## Technology Stack (REQUIRED)

**Backend**: FastAPI (Python) - NOT Next.js, NOT Django, NOT Flask
- fastapi==0.104.1
- anthropic==0.39.0
- sse-starlette==1.8.2

**Frontend**: React with Vite - NOT Next.js, NOT Create React App
- react@^18.2.0
- tailwindcss@^3.3.0 (NOT v4)
- recharts@^2.10.0
- @babel/standalone@^7.23.0

**Streaming**: Direct SSE from FastAPI - NO Redis, NO queues
- Use GET endpoints with EventSource
- Add X-Accel-Buffering: no header
- Include 0.001s delays for proper flushing

**Data Access**: Import pre-built tools from `backend/tools/` - DO NOT reimplement

## Implementation Process

### Phase 1: Analysis & Planning

**IMPORTANT**: Thoroughly review ALL documents in the `requirements/` directory:

1. **PM-Generated Outputs** (`requirements/pm-outputs/`)
   - Read PRD.md for overall vision and requirements
   - Study system-architecture.md for technical design
   - Review api-specification.md for endpoint details
   - Examine data-models.md for entity structures
   - Check tool-interface.md for pre-built tool usage
   - Review user-stories.md for feature requirements

2. **UX-Generated Outputs** (`requirements/ux-outputs/`)
   - **CRITICAL**: Review `prototypes/` folder for HTML mockups
   - Study design-system.md for styling guidelines
   - Check component-specs.md for UI components
   - Review visualization-specs.md for chart requirements

3. **PO-Provided Inputs** (`requirements/po-inputs/`)
   - Review domain-specific requirements
   - Check brand guidelines if provided
   - Study any mockups or wireframes
   - **CRITICAL**: Review multi-agent-implementation-architecture.md for backend structure

4. **Technical Patterns** (`requirements/technical-patterns/`)
   - **MASTER GUIDE**: `implementation-guide.md` - Follow this exactly
   - Review `visualization-agent-pattern.md` for visualization requirements
   - Check `multi-agent-patterns.md` for orchestration patterns
   - Study `streaming-patterns.md` for SSE implementation

5. **Pre-built Tools** (`backend/tools/`)
   - Identify ALL provided tools
   - Understand their interfaces
   - Plan to IMPORT and use them directly

### Phase 2: Present Implementation Plan

After thoroughly reviewing ALL documents:

1. **DRAFT** (do not use todo system yet) an implementation plan that includes:
   - Backend setup with FastAPI
   - All agents from architecture (CMO, specialists, visualization)
   - Frontend setup with React + Vite
   - CodeArtifact component for visualizations
   - SSE streaming implementation
   - Integration of pre-built tools

2. Your plan MUST match the architecture in PM outputs:
   - Orchestrator agent (CMO)
   - All specialist agents listed
   - Visualization agent (generates React components)
   - Exact API endpoints specified
   - UI components from UX prototypes

3. **Present the plan as TEXT** (not as todos) showing:
   - All phases in order
   - Which agents you'll implement
   - How you'll use the pre-built tools
   - Frontend components matching UX prototypes

4. **Ask for approval**: "I've reviewed all requirements including PM outputs, UX prototypes, and technical patterns. Here's my implementation plan based on the architecture. Should I proceed with this plan?"

5. **ONLY AFTER USER APPROVES**: Create the actual todos using the todo system and begin Phase 1.

### Phase 3: Execute Plan

Only after user approval:

1. **Match UX Prototypes Exactly**
   - Open and study the HTML files in `requirements/ux-outputs/prototypes/`
   - Implement the EXACT layout and components shown
   - Use the same class names and styling patterns
   - Include all interactive elements demonstrated

2. **Follow Implementation Order**
   - Backend setup first (FastAPI, agents, tools)
   - Frontend setup next (React + Vite)
   - Integration last (SSE connection, visualization rendering)

3. **Update Todo Status**
   - Mark each task as you complete it
   - Complete each phase before moving to next
   - Test as you go

## Quick Links
- PM Outputs: `requirements/pm-outputs/` (PRD, architecture, APIs)
- UX Prototypes: `requirements/ux-outputs/prototypes/` (HTML mockups)
- Implementation Guide: `requirements/technical-patterns/implementation-guide.md`
- Visualization Pattern: `requirements/technical-patterns/visualization-agent-pattern.md`
- Pre-built Tools: `backend/tools/` (DO NOT MODIFY)

## Expected Project Structure

```
backend/
├── main.py              # FastAPI app with CORS and SSE endpoints
├── requirements.txt     # anthropic, fastapi, uvicorn, etc.
├── api/                 # API route handlers
│   └── chat.py         # SSE endpoint for streaming
├── services/           
│   ├── health_analyst_service.py  # Main orchestration service
│   ├── agents/         # Agent implementations
│   │   ├── cmo/        # Orchestrator with prompts/
│   │   ├── specialist/ # Single class with prompts/ for all
│   │   └── visualization/ # Visualization agent (REQUIRED)
│   └── streaming/      # SSE utilities
└── tools/              # PRE-BUILT tools (DO NOT MODIFY)
    ├── tool_registry.py
    └── [other provided tools]

frontend/
├── package.json         # React, Vite, Tailwind, Recharts, @babel/standalone
├── vite.config.ts      
├── src/
│   ├── App.tsx         # Main app component
│   ├── components/     # React components
│   │   ├── ChatInterface.tsx    # Main chat UI with SSE
│   │   ├── CodeArtifact.tsx     # Renders visualization code
│   │   ├── MedicalTeamDisplay.tsx # Shows agent status
│   │   └── [other UX components]
│   ├── services/       # API client with SSE
│   └── types/          # TypeScript types
└── index.html
```

## Critical Implementation Rules

### ALWAYS:
- Use FastAPI for backend (with `uvicorn main:app --reload`)
- Use React + Vite for frontend (with `npm run dev`)
- Import tools from `backend/tools/` using:
  ```python
  from tools.tool_registry import ToolRegistry
  from tools.health_query_tool import execute_health_query_v2
  ```
- Implement direct SSE streaming without queues
- Keep agents simple - thin wrappers around Anthropic calls
- Use externalized prompts in `.txt` files
- **Include Visualization Agent** that:
  - Generates self-contained React components
  - Embeds data directly in the component
  - Streams as ```javascript code blocks
  - Is called AFTER synthesis is complete

### NEVER:
- Use Next.js (backend or frontend)
- Add Redis, databases, or message queues  
- Reimplement tools that exist in `backend/tools/`
- Create complex agent inheritance hierarchies
- Add authentication systems
- Use state management libraries (Redux, Zustand)

## Key Implementation Patterns

### Agent Implementation Pattern
```python
# Every agent follows this pattern
class SpecialistAgent:
    def __init__(self, name, specialty):
        self.client = Anthropic()
        self.tools = ToolRegistry()  # Import pre-built tools
        self.prompts = self._load_prompts()  # From .txt files
```

### Visualization Flow
1. CMO completes synthesis
2. Visualization agent generates React component
3. Component streamed as ```javascript code block
4. Frontend CodeArtifact renders it dynamically

### SSE Streaming Pattern (CRITICAL)
```python
# Correct GET endpoint for EventSource
@router.get("/api/chat/stream")
async def chat_stream(message: str):
    async def generate():
        # Critical delay to prevent buffering
        await asyncio.sleep(0.001)
        
        async for update in orchestrator.process(message):
            yield {
                "event": "message",
                "data": json.dumps(update)
            }
            await asyncio.sleep(0.001)  # Force flush
    
    return EventSourceResponse(
        generate(),
        headers={
            'X-Accel-Buffering': 'no',  # Critical header
            'Cache-Control': 'no-cache'
        }
    )

# Frontend usage
const eventSource = new EventSource(`/api/chat/stream?message=${encodeURIComponent(message)}`);
```

## Common Issues & Solutions

### TypeScript Import Errors
```typescript
// Wrong - causes "does not provide export" errors
import { SpecialistStatus, COLORS } from './types';

// Correct - use type imports
import type { SpecialistStatus } from './types';
import { COLORS } from './types';
```

### Tailwind CSS Version Issues
```json
// package.json - Use v3, NOT v4
"tailwindcss": "^3.3.0"  // ✅ Correct
"tailwindcss": "^4.0.0"  // ❌ Wrong - breaking changes
```

### SSE Connection Issues
```typescript
// Wrong - POST with EventSource
new EventSource('/api/chat/message', { method: 'POST' }); // ❌

// Correct - GET with query params
new EventSource(`/api/chat/stream?message=${encodeURIComponent(msg)}`); // ✅
```

## Important Notes
- Present plan as TEXT first, get approval, THEN create todos
- No duplicate presentation (todos ARE the plan once approved)
- Tools are PRE-BUILT - import and use them directly
- Match UI components to UX prototypes exactly
- Follow dependency versions EXACTLY
- Test SSE streaming before marking complete
- Final deliverable must include:
  ```bash
  # Backend
  cd backend && pip install -r requirements.txt && python main.py
  
  # Frontend
  cd frontend && npm install && npm run dev
  ```

---

# Part 2: Enhancement & Feature Development Guide (Active)

## Current System Overview

The Multi-Agent Health Insight System is now fully operational with:

### **Core Architecture (DO NOT MODIFY)**
- **Orchestrator-Worker Pattern**: CMO agent orchestrates 8 medical specialists
- **SSE Streaming**: Real-time updates with proper event handling
- **Visualization Engine**: Generates self-contained React components with embedded data
- **Tool Integration**: Pre-built Snowflake Cortex tools for health data queries

### **Current Capabilities**
- Health data analysis across multiple domains (labs, medications, vitals)
- Multi-agent orchestration with real-time progress tracking
- Dynamic visualization generation based on query context
- Complexity-based team assembly (Simple/Standard/Complex/Critical)
- Persistent conversation history with thread management

## Adding New Features

### **Feature Development Checklist**
Before adding any new feature:
- [ ] Review existing patterns in the codebase
- [ ] Check if similar functionality already exists
- [ ] Ensure backward compatibility
- [ ] Plan for testing (unit, integration, SSE streaming)
- [ ] Document the feature in appropriate location

### **Safe Enhancement Areas**

#### 1. **Adding New Specialist Agents**
```python
# Location: backend/services/agents/specialist/
# Steps:
1. Add new specialty to MedicalSpecialty enum
2. Create system prompt in prompts/system_[specialty].txt
3. Update CMO task creation logic
4. Add specialist color/icon in frontend
5. Test with relevant queries
```

#### 2. **Extending Visualization Types**
```python
# Location: backend/services/agents/visualization/prompts/
# Steps:
1. Add new example in prompts/example_[type].txt
2. Update query type detection in visualization_agent.py
3. Test with sample data
4. Ensure CodeArtifact component can render it
```

#### 3. **Adding New Health Metrics**
```python
# Location: backend/tools/
# Steps:
1. DO NOT modify existing tools
2. Create new tool following ToolRegistry pattern
3. Register in tool_registry.py
4. Update relevant specialist prompts
```

#### 4. **UI/UX Enhancements**
```typescript
// Location: frontend/src/components/
// Safe to modify:
- Color schemes and animations
- Additional information displays
- New interaction patterns
// DO NOT modify:
- Core SSE handling logic
- Three-panel layout structure
- Message parsing logic
```

### **Feature Categories & Patterns**

#### **Analytics Features**
- Predictive health trends
- Risk scoring algorithms
- Comparative analysis (peer groups)
- Pattern: Implement as new specialist agent or enhance existing ones

#### **Data Integration**
- Wearable device data
- External lab imports
- Insurance claim data
- Pattern: Create new tools, don't modify existing ones

#### **Reporting & Export**
- PDF report generation
- Data export (CSV, JSON)
- Shareable visualizations
- Pattern: Add new endpoints, maintain existing API structure

#### **Collaboration Features**
- Share with healthcare providers
- Family member access
- Care team coordination
- Pattern: Extend conversation model, don't break existing flow

## Testing New Features

### **Required Test Coverage**
1. **Unit Tests**: Each new agent/component
2. **Integration Tests**: Full workflow with new feature
3. **SSE Streaming Tests**: Ensure real-time updates work
4. **Visualization Tests**: Verify chart rendering
5. **Performance Tests**: Check impact on response time

### **Testing Patterns**
```python
# Agent testing template
async def test_new_specialist():
    # 1. Test prompt loading
    # 2. Test tool calling
    # 3. Test response format
    # 4. Test error handling
    # 5. Test streaming output
```

## Performance Considerations

### **When Adding Features**
- Maintain parallel specialist execution
- Use streaming for long operations
- Cache expensive computations
- Monitor token usage
- Profile database queries

### **Red Flags**
- Sequential agent execution
- Blocking API calls
- Large context windows
- Uncached file reads
- Synchronous processing

## Common Enhancement Scenarios

### **Scenario 1: Adding Medication Interaction Checker**
```python
# Approach:
1. Create MedicationInteractionSpecialist
2. Add drug interaction database tool
3. Enhance Pharmacy specialist prompts
4. Add interaction visualization
```

### **Scenario 2: Implementing Health Score Dashboard**
```python
# Approach:
1. Create HealthScoreAgent
2. Define scoring algorithm
3. Add dashboard component
4. Integrate with existing specialists
```

### **Scenario 3: Adding Voice Input**
```typescript
// Approach:
1. Add speech-to-text service
2. Integrate with ChatInterface
3. Handle streaming transcription
4. Maintain text-based fallback
```

## Code Standards for Enhancements

### **Python Standards**
- Type hints required
- Async/await for I/O operations
- Comprehensive error handling
- Logging at appropriate levels
- Docstrings for public methods

### **TypeScript Standards**
- Strict mode enabled
- Interfaces over types
- Proper error boundaries
- Component composition
- Accessibility (ARIA labels)

### **PR Requirements**
- [ ] Tests pass (unit, integration)
- [ ] No regression in existing features
- [ ] Documentation updated
- [ ] Performance impact assessed
- [ ] Security review if handling new data

## Migration & Upgrade Patterns

### **Database Schema Changes**
- Always backward compatible
- Migration scripts provided
- Rollback plan documented

### **API Version Changes**
- Maintain v1 endpoints
- Version new endpoints
- Deprecation notices
- Client compatibility

### **Frontend Updates**
- Progressive enhancement
- Feature flags for rollout
- Browser compatibility
- Mobile responsiveness

## Debugging Enhanced Features

### **SSE Streaming Issues**
```typescript
// Check points:
1. Browser console for event logs
2. Network tab for SSE connection
3. Backend logs for streaming errors
4. Event type consistency
```

### **Agent Communication**
```python
# Debug locations:
1. health_analyst_service.py - orchestration
2. specialist_agent.py - individual agents
3. anthropic_streaming.py - API calls
4. SSE response formatting
```

### **Visualization Rendering**
```typescript
// Common issues:
1. Data format mismatch
2. Missing chart dependencies
3. CodeArtifact parsing errors
4. Recharts context issues
```

## Feature Rollout Strategy

### **Development → Staging → Production**
1. Feature flag implementation
2. Gradual rollout percentage
3. A/B testing framework
4. Rollback procedures
5. Performance monitoring

### **User Communication**
- In-app feature announcements
- Documentation updates
- Training materials
- Feedback collection

## Security Considerations for New Features

### **Data Handling**
- PHI/PII compliance
- Encryption at rest/transit
- Access control
- Audit logging
- Data retention policies

### **API Security**
- Rate limiting
- Input validation
- SQL injection prevention
- XSS protection
- CORS configuration

## Recent Updates

### **Trace Viewer Improvements (Completed)**
- Fixed text overflow issue in hierarchical trace viewer
- Added proper text wrapping to event detail displays
- Improved readability of long responses and data fields
- Enhanced CSS with `white-space: pre-wrap` and `word-wrap: break-word`

### **Smart Content Formatter (Completed)**
- Implemented intelligent formatting for trace event data
- Added specialized formatters for:
  - LLM responses with task XML parsing and card display
  - Tool invocations with highlighted queries
  - Query results with tabular data display
  - JSON data with syntax highlighting
- Toggle between formatted and raw views for debugging
- Automatic detection of content type for appropriate formatting
- Enhanced visual hierarchy with task cards, priority badges, and emojis
- Made formatted view the default display mode (raw view available via toggle)
- Added support for non-XML task format parsing (handles both XML and plain text task formats)

## Future Enhancement Ideas

### **Near-term (Next Sprint)**
- Health trend notifications
- Medication reminder integration
- Lab result explanations
- Wellness recommendations

### **Medium-term (Next Quarter)**
- Predictive health insights
- Integration with wearables
- Family health tracking
- Telemedicine integration

### **Long-term (Next Year)**
- AI health coach
- Genomic data analysis
- Clinical trial matching
- Population health insights

## Getting Help

### **For Enhancement Questions**
1. Review this guide
2. Check existing patterns in codebase
3. Look for similar features
4. Test in isolation first

### **For Bug Reports**
- GitHub Issues: Include reproduction steps
- Logs: Include relevant backend/frontend logs
- Environment: Specify versions and configuration

### **For Feature Requests**
- Use GitHub Discussions
- Provide use cases
- Consider implementation impact
- Suggest testing approach

---

# Part 3: Evaluation System Architecture

## System Overview

The evaluation system provides comprehensive testing capabilities for the multi-agent health insight system:

### Core Features
- **QE Agent**: Fully operational with "run" and "details" commands for test case management
- **Evaluation Engine**: Comprehensive scoring across 5 dimensions with metadata-driven architecture
- **HTML Reports**: Beautiful reports with CLI-style drill-downs and LLM Judge analysis
- **Eval Dev Studio**: Three-panel UI for test case management and evaluation
- **Unified Storage**: All evaluation data in centralized `/evaluation/data/` directory

### Evaluation Data Architecture

```
evaluation/
├── agents/                       # Agent-specific evaluation code
├── cli/                          # Command-line interface
├── core/                         # Core types and interfaces
├── framework/                    # Evaluation framework components
└── data/                         # All evaluation data artifacts
    ├── config.py                 # Central configuration
    ├── test_loader.py            # Multi-agent test loader
    ├── schemas/                  # Agent-specific test schemas
    │   ├── cmo_schema.json
    │   ├── specialist_schema.json
    │   └── visualization_schema.json
    ├── traces/                   # Health query traces
    ├── test-suites/              # All test cases in JSON
    │   ├── framework/            # Organized by agent type
    │   └── studio-generated/     # User-created tests
    └── runs/                     # Evaluation results
        └── [date]/eval_[id]/
            ├── metadata.json     # Run metadata
            ├── events/*.json     # Persistent lifecycle events
            ├── result.json       # Evaluation result
            └── report/index.html # HTML report
```

### Key Architecture Benefits
1. **Multi-Agent Support**: Each agent type has its own JSON schema and test organization
2. **Persistent Events**: Evaluation lifecycle events survive server reloads
3. **Unified Format**: All test cases use JSON format (framework and studio-generated)
4. **No Duplication**: Single result file per evaluation
5. **Configurable Storage**: Redirect paths via environment variables
6. **Clean Separation**: Framework code vs data storage

## Eval Dev Studio UI

### Three-Panel Layout

#### **Left Panel: QE/Evaluation Agent Interface**
- QE Agent chat interface for test case creation and evaluation commands
- Real-time status of running evaluations
- Agent conversation history and context
- Quick actions (run evaluation, view details, reset)

#### **Middle Panel: Test Case & Trace Viewer**
- **Test Case List**: Grid view with ID, query preview, complexity, status
- **Detail View**: Full test case parameters, trace viewer integration
- **Quick Actions**: Run, view report, edit, duplicate
- **Evaluation History**: Timeline of all evaluations for a test case

#### **Right Panel: Multi-Tab Information**
- **📊 Evaluation Reports** - Interactive HTML reports with drill-downs
- **📈 Performance Analytics** - Charts and metrics across test cases
- **🔍 Test Case Details** - Detailed breakdown of selected test case
- **📋 Evaluation History** - Timeline of all evaluations
- **⚙️ Test Management** - Bulk operations, import/export

### Test Case Lifecycle
1. **Creation**: Generate via QE Agent or manual input
2. **Organization**: Categories, tags, complexity grouping
3. **Execution**: Run single or batch evaluations
4. **Analysis**: View results, compare runs, identify patterns
5. **Iteration**: Edit, refine, and re-run test cases

# Part 4: Evaluation Framework Integration

## Architecture Overview

The evaluation framework consists of two integrated systems:

### 1. Main Evaluation Framework (`/evaluation`)
- **Purpose**: Comprehensive evaluation system implementing Anthropic's best practices
- **Components**: CMOEvaluator, SpecialistEvaluator, test cases, dimensions, LLM Judge
- **Access**: CLI (`python -m evaluation.cli.run_evaluation`) or direct import
- **Features**: Metadata-driven architecture, hybrid evaluation methods, component-based scoring

### 2. Backend Integration Layer (`/backend/eval_integration`)
- **Purpose**: Bridges web UI with main evaluation framework
- **Components**: subprocess_evaluator.py, cli_evaluator_adapter.py, trace_parser.py
- **Access**: Called by backend services for Studio evaluations
- **Features**: Subprocess execution, event streaming, mock agents for trace replay

## Subprocess Execution Pattern

The framework uses subprocess execution to maintain clean separation:

```python
# Avoids module conflicts between backend and evaluation paths
result = run_evaluation_subprocess(test_case, trace_data, api_key, event_callback)
```

Benefits:
- Clean separation between systems
- No import path conflicts
- Independent dependencies
- Real-time event streaming

## Evaluation Lifecycle Events

The ~30 second evaluation process reports these lifecycle events:

1. **trace_load** - "🔍 Loading execution trace"
2. **test_case_ready** - "📋 Test case prepared"
3. **dimension_start** - "📏 Evaluating [Dimension Name]"
4. **dimension_evaluation** - "📊 Evaluating all dimensions"
5. **llm_judge_eval** - "🤖 LLM-as-Judge evaluating..."
6. **dimension_result** - "✅/❌ [dimension]: [score]"
7. **diagnostic** - "🔍 LLM-as-Judge diagnosing..."
8. **diagnostic_complete** - "💡 LLM-as-Judge generated N recommendations"
9. **overall_score** - "📊 Evaluation complete: Overall Score X.XXX"
10. **evaluation_complete** - "✅ Evaluation analysis finished"

### Event API
```python
GET /api/evaluation/events/{evaluation_id}?start_index=0

# Response format
{
    "evaluation_id": "...",
    "status": "running",
    "events": [{"type": "...", "message": "...", "timestamp": "..."}],
    "total_events": 15,
    "has_more": false
}
```

## Integration Points

- **Test Case Flow**: QE Agent → JSON → Backend → Subprocess → Evaluator
- **Trace Processing**: Health Query → Trace → Extractor → MockAgent → Evaluation
- **Event Streaming**: Subprocess → Parser → Storage → API → Frontend

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.

## Update Guidelines
When making updates to the codebase:
- NO BACKWARD COMPATIBILITY REQUIRED - Feel free to make breaking changes when they improve the system
- UPDATE README.md - When making significant changes, update the README to reflect the CURRENT STATE
- MAINTAIN EXISTING STRUCTURE - Keep the existing outline/structure of documentation
- DOCUMENT CURRENT STATE - Don't track incremental updates or maintain change logs
- FOCUS ON "WHAT IS" - Documentation should describe how the system works NOW, not its history