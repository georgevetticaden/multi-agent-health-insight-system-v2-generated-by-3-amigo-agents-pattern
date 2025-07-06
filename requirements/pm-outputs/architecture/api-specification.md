# API Specification: Multi-Agent Health Insight System

## Overview

This document defines all API endpoints for the Multi-Agent Health Insight System. The API follows RESTful principles with a critical enhancement: Server-Sent Events (SSE) for real-time streaming of agent activities and results.

## Base URL

```
Development: http://localhost:8000
Production: https://api.health-insights.example.com
```

## Authentication

**Note**: For this demo/POC system, authentication is optional and not implemented. In production, all endpoints would require authentication tokens.

## Common Headers

All requests should include:
```
Content-Type: application/json
Accept: application/json
```

SSE endpoints require additional headers (see SSE section).

## Endpoints

### 1. Health Check

#### Endpoint: System Health Status
- **Method**: GET
- **Path**: /api/health
- **Description**: Verifies the API is operational
- **Request Body**: None
- **Response**:
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2025-01-15T10:30:00Z",
    "services": {
      "anthropic_api": "connected",
      "tool_registry": "ready"
    }
  }
  ```
- **Errors**: 
  - 503: Service unavailable
- **Example**:
  ```bash
  curl http://localhost:8000/api/health
  ```

---

### 2. Chat Endpoints

#### Endpoint: Stream Analysis (CRITICAL - PRIMARY ENDPOINT)
- **Method**: GET (for EventSource compatibility)
- **Path**: /api/chat/stream
- **Description**: Streams health analysis with real-time updates via Server-Sent Events
- **Query Parameters**:
  - `message` (required): URL-encoded health query
  - `conversation_id` (optional): UUID for conversation continuity
- **Headers Required**:
  ```
  X-Accel-Buffering: no
  Cache-Control: no-cache
  Connection: keep-alive
  ```
- **Response**: Server-Sent Events stream
  
  **Event Format**:
  ```
  event: {event_type}
  data: {json_payload}
  
  ```
  
  **Event Types**:
  
  1. **connected**
     ```json
     {
       "type": "connected",
       "timestamp": "2025-01-15T10:30:00Z",
       "conversation_id": "uuid"
     }
     ```
  
  2. **message**
     ```json
     {
       "type": "message",
       "subtype": "text|thinking|tool_call|tool_result|specialist_update",
       "content": "string or object",
       "metadata": {
         "agent": "cmo|specialist_name",
         "timestamp": "2025-01-15T10:30:00Z"
       }
     }
     ```
  
  3. **team_assembly**
     ```json
     {
       "type": "team_assembly",
       "complexity": "simple|standard|complex|critical",
       "specialists": [
         {
           "id": "cardiology",
           "name": "Dr. Heart",
           "specialty": "Cardiology",
           "status": "waiting"
         }
       ]
     }
     ```
  
  4. **specialist_progress**
     ```json
     {
       "type": "specialist_progress",
       "specialist_id": "cardiology",
       "progress": 65,
       "status": "active",
       "current_task": "Analyzing cholesterol trends"
     }
     ```
  
  5. **specialist_complete**
     ```json
     {
       "type": "specialist_complete",
       "specialist_id": "cardiology",
       "confidence": 85,
       "key_findings": 2,
       "execution_time": 4.2
     }
     ```
  
  6. **visualization**
     ```json
     {
       "type": "visualization",
       "code": "```javascript\n// Complete React component code\n```",
       "metadata": {
         "chart_type": "time_series",
         "data_points": 150
       }
     }
     ```
  
  7. **error**
     ```json
     {
       "type": "error",
       "error_code": "SPECIALIST_TIMEOUT",
       "message": "Cardiology specialist timed out",
       "recoverable": true
     }
     ```
  
  8. **done**
     ```json
     {
       "type": "done",
       "summary": {
         "total_time": 15.3,
         "specialists_used": 5,
         "tokens_used": 4523
       }
     }
     ```

- **Implementation Notes**:
  - Add 0.001s delays between events for proper flushing
  - Use EventSourceResponse from sse-starlette
  - Frontend uses: `new EventSource(/api/chat/stream?message=${encodeURIComponent(msg)})`
  - Automatic reconnection handled by EventSource API
  - Maximum connection duration: 5 minutes (then reconnect)

- **Error Handling**:
  - Connection errors trigger automatic reconnection
  - Partial results delivered even if some specialists fail
  - Graceful degradation for complex queries

- **Example Frontend Usage**:
  ```javascript
  const eventSource = new EventSource(
    `/api/chat/stream?message=${encodeURIComponent("What's my cholesterol trend?")}`
  );
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
  };
  
  eventSource.onerror = (error) => {
    console.error('SSE Error:', error);
    // EventSource automatically reconnects
  };
  ```

---

#### Endpoint: Save Conversation
- **Method**: POST
- **Path**: /api/chat/conversations
- **Description**: Saves conversation state (client-side state persistence)
- **Request Body**:
  ```json
  {
    "conversation_id": "uuid",
    "title": "Cholesterol Analysis",
    "messages": [
      {
        "id": "msg_uuid",
        "role": "user|assistant",
        "content": "string",
        "timestamp": "2025-01-15T10:30:00Z",
        "metadata": {}
      }
    ],
    "agent_states": [
      {
        "query_index": 0,
        "specialists": [],
        "complexity": "standard"
      }
    ]
  }
  ```
- **Response**:
  ```json
  {
    "conversation_id": "uuid",
    "saved": true,
    "timestamp": "2025-01-15T10:30:00Z"
  }
  ```
- **Errors**:
  - 400: Invalid conversation data
  - 413: Conversation too large
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/chat/conversations \
    -H "Content-Type: application/json" \
    -d '{"conversation_id": "123", "messages": []}'
  ```

---

### 3. Health Data Endpoints

#### Endpoint: Import Health Records
- **Method**: POST
- **Path**: /api/health/import
- **Description**: Triggers import of health records using pre-built tools
- **Request Body**:
  ```json
  {
    "import_type": "full|incremental",
    "file_directory": "/path/to/health/data",
    "options": {
      "validate": true,
      "skip_duplicates": true
    }
  }
  ```
- **Response**:
  ```json
  {
    "import_id": "uuid",
    "status": "processing|complete|failed",
    "summary": {
      "total_records": 1234,
      "imported": 1230,
      "skipped": 4,
      "errors": 0
    },
    "estimated_time": 45
  }
  ```
- **Errors**:
  - 400: Invalid import configuration
  - 404: Directory not found
  - 500: Import tool failure
- **Example**:
  ```bash
  curl -X POST http://localhost:8000/api/health/import \
    -H "Content-Type: application/json" \
    -d '{"import_type": "full", "file_directory": "/data/health"}'
  ```

---

#### Endpoint: Query Health Metrics
- **Method**: GET
- **Path**: /api/health/metrics
- **Description**: Retrieves specific health metrics using natural language
- **Query Parameters**:
  - `query` (required): Natural language query
  - `start_date` (optional): ISO 8601 date
  - `end_date` (optional): ISO 8601 date
  - `metric_types` (optional): Comma-separated list
- **Response**:
  ```json
  {
    "query": "cholesterol levels",
    "results": [
      {
        "date": "2024-06-15",
        "metric": "Total Cholesterol",
        "value": 185,
        "unit": "mg/dL",
        "reference_range": "< 200",
        "status": "normal"
      }
    ],
    "metadata": {
      "total_results": 12,
      "date_range": {
        "start": "2024-01-01",
        "end": "2024-12-31"
      }
    }
  }
  ```
- **Errors**:
  - 400: Invalid query
  - 404: No data found
- **Example**:
  ```bash
  curl "http://localhost:8000/api/health/metrics?query=cholesterol&start_date=2024-01-01"
  ```

---

### 4. Agent Management Endpoints

#### Endpoint: List Available Specialists
- **Method**: GET
- **Path**: /api/agents/specialists
- **Description**: Returns all available medical specialists
- **Response**:
  ```json
  {
    "specialists": [
      {
        "id": "cardiology",
        "name": "Dr. Heart",
        "specialty": "Cardiology",
        "description": "Cardiovascular health expert",
        "capabilities": [
          "Blood pressure analysis",
          "Cholesterol assessment",
          "Heart rate patterns"
        ]
      }
    ]
  }
  ```
- **Errors**: None
- **Example**:
  ```bash
  curl http://localhost:8000/api/agents/specialists
  ```

---

#### Endpoint: Get Agent Status
- **Method**: GET
- **Path**: /api/agents/status
- **Description**: Returns current status of all agents
- **Response**:
  ```json
  {
    "cmo": {
      "status": "ready",
      "active_queries": 0,
      "model": "claude-3-sonnet-20240229"
    },
    "specialists": {
      "available": 8,
      "busy": 0,
      "error": 0
    },
    "system_load": {
      "tokens_per_minute": 1523,
      "average_response_time": 8.2
    }
  }
  ```
- **Errors**: None
- **Example**:
  ```bash
  curl http://localhost:8000/api/agents/status
  ```

---

### 5. Visualization Endpoints

#### Endpoint: Get Visualization Templates
- **Method**: GET
- **Path**: /api/visualizations/templates
- **Description**: Returns available visualization templates
- **Response**:
  ```json
  {
    "templates": [
      {
        "id": "time_series",
        "name": "Time Series Chart",
        "description": "Line chart for trends over time",
        "required_data": ["date", "value"],
        "options": ["multiple_series", "zoom", "export"]
      }
    ]
  }
  ```
- **Errors**: None
- **Example**:
  ```bash
  curl http://localhost:8000/api/visualizations/templates
  ```

---

### 6. System Configuration

#### Endpoint: Get Query Examples
- **Method**: GET
- **Path**: /api/config/examples
- **Description**: Returns example queries for the welcome screen
- **Response**:
  ```json
  {
    "examples": [
      {
        "id": "cholesterol_trend",
        "query": "What's my cholesterol trend over the last 15 years?",
        "complexity": "standard",
        "description": "Analyzes long-term cholesterol patterns",
        "expected_specialists": ["cardiology", "laboratory_medicine", "data_analysis"]
      }
    ]
  }
  ```
- **Errors**: None
- **Example**:
  ```bash
  curl http://localhost:8000/api/config/examples
  ```

---

## Error Response Format

All errors follow this structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional context"
    },
    "timestamp": "2025-01-15T10:30:00Z",
    "request_id": "uuid"
  }
}
```

## Rate Limiting

- **Default limit**: 100 requests per minute per IP
- **SSE connections**: Maximum 5 concurrent per IP
- **Token limit**: 100,000 tokens per hour per IP

Headers returned:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1673784000
```

## CORS Configuration

For development:
```
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
Access-Control-Allow-Credentials: true
```

## WebSocket Alternative (Not Implemented)

While this system uses SSE, a WebSocket alternative could provide bidirectional communication:

```
ws://localhost:8000/ws/chat/{conversation_id}
```

This is noted for future enhancement but not part of the current implementation.