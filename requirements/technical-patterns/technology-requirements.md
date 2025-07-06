# Technology Requirements for Multi-Agent System

## Overview
This document defines the exact technology stack and version requirements for implementing the multi-agent system. These requirements are non-negotiable to ensure compatibility and consistent behavior.

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104.1 with Python 3.11+
- **API Design**: RESTful + Server-Sent Events (SSE)
- **AI Integration**: Anthropic API (via anthropic Python SDK)
- **Data Access**: Pre-built tools only (no direct database integration)

### Frontend
- **Framework**: React 18.2.0 with Vite 5.0.8
- **Language**: TypeScript 5.x
- **Styling**: Tailwind CSS 3.3.0 (CRITICAL: NOT v4)
- **Build Tool**: Vite (NOT Next.js, NOT Create React App)

### Streaming Architecture
- **Method**: Server-Sent Events (SSE)
- **Implementation**: GET endpoints with EventSource
- **Headers**: X-Accel-Buffering: no
- **Timing**: 0.001s delays between events for proper flushing

### Data Visualization
- **Charts**: Recharts 2.10.0
- **Dynamic Rendering**: @babel/standalone 7.23.0
- **Pattern**: Self-contained React components streamed as code artifacts

### Icons & UI
- **Icons**: Lucide React 0.294.0
- **Effects**: Glassmorphism via Tailwind CSS utilities
- **Layout**: 3-panel responsive design

## What NOT to Use

### Backend - Avoid These:
- ❌ Next.js API routes
- ❌ Django or Flask
- ❌ GraphQL
- ❌ Direct database connections
- ❌ Redis or message queues
- ❌ External caching services

### Frontend - Avoid These:
- ❌ Next.js
- ❌ Create React App
- ❌ Tailwind CSS v4
- ❌ Redux or complex state management
- ❌ Server-side rendering

### Architecture - Avoid These:
- ❌ Microservices
- ❌ Message queues
- ❌ External databases
- ❌ Authentication systems
- ❌ Complex deployment patterns

## Implementation Notes

### Pre-built Tools
- All data access is through pre-built tools
- Tools are provided in `backend/tools/` directory
- Import and use them directly - do NOT reimplement
- Do NOT design database schemas or persistence layers

### SSE Implementation
```python
# Backend: Use GET endpoint
@app.get("/api/chat/stream")
async def stream_endpoint(message: str):
    # Implementation details in sse-implementation-guide.md
```

```typescript
// Frontend: Use EventSource
const eventSource = new EventSource(
  `/api/chat/stream?message=${encodeURIComponent(message)}`
);
```

### TypeScript Imports
```typescript
// Use type imports for type-only exports
import type { SpecialistStatus } from './types';
import { SPECIALIST_COLORS } from './types';
```

### Visualization Agent
- Generates self-contained React components
- Components include embedded data
- No imports in generated code
- Uses Recharts components available in global scope

## Deployment Requirements

### Development
- Python 3.11 or higher
- Node.js 18 or higher
- npm or yarn

### Production
- FastAPI with Uvicorn
- Static frontend build served separately
- Environment variables for configuration
- No external services required

## Version Compatibility Matrix

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.11+ | Required for latest type hints |
| FastAPI | 0.104.1 | Exact version for compatibility |
| React | 18.2.0 | Concurrent features support |
| Vite | 5.0.8 | Fast HMR and builds |
| Tailwind CSS | 3.3.0 | NOT v4 - breaking changes |
| TypeScript | 5.x | Better type inference |
| Recharts | 2.10.0 | Data visualization |
| @babel/standalone | 7.23.0 | Dynamic code execution |

## Critical Implementation Rules

1. **Use exact versions** specified above
2. **Follow SSE patterns** exactly as documented
3. **Import pre-built tools** - never reimplement
4. **No authentication** - focus on core functionality
5. **Simple state management** - React hooks only
6. **Direct API calls** - no complex abstractions

This technology stack has been proven to work reliably for multi-agent systems across different domains.