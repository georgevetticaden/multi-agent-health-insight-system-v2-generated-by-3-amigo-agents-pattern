"""
HTML generator for trace viewer.

Provides standalone HTML generation for trace viewing without requiring
a backend server. The generated HTML is self-contained with all styling
and JavaScript inline.
"""

import json
from typing import Dict, Any
from .trace_models import CompleteTrace, TraceEventType


def generate_trace_viewer_html(trace: CompleteTrace) -> str:
    """
    Generate standalone HTML content for trace viewer.
    
    Args:
        trace: CompleteTrace object
        
    Returns:
        Self-contained HTML string for trace viewing
    """
    # Organize events by type for better display
    events_by_type = {}
    for event in trace.events:
        event_type = event.event_type.value
        if event_type not in events_by_type:
            events_by_type[event_type] = []
        events_by_type[event_type].append(event)
    
    # Calculate statistics
    total_tokens = sum(event.tokens_used for event in trace.events if event.tokens_used)
    llm_calls = len([e for e in trace.events if e.event_type == TraceEventType.LLM_PROMPT])
    tool_calls = len([e for e in trace.events if e.event_type == TraceEventType.TOOL_INVOCATION])
    
    # Format metadata
    metadata_rows = []
    if trace.test_case_id:
        metadata_rows.append(f'''
            <div class="row">
                <span class="label">Test Case ID:</span>
                <span class="value">{trace.test_case_id}</span>
            </div>
        ''')
    if trace.user_id:
        metadata_rows.append(f'''
            <div class="row">
                <span class="label">User ID:</span>
                <span class="value">{trace.user_id}</span>
            </div>
        ''')
    if trace.session_id:
        metadata_rows.append(f'''
            <div class="row">
                <span class="label">Session ID:</span>
                <span class="value">{trace.session_id}</span>
            </div>
        ''')
    
    metadata_html = '\n'.join(metadata_rows)
    
    # Generate event timeline
    events_html = []
    for i, event in enumerate(trace.events):
        event_class = event.event_type.value.lower()
        
        # Format data for display
        data_str = json.dumps(event.data, indent=2) if event.data else "{}"
        
        # Determine if content should be collapsed
        is_large = len(data_str) > 500
        
        # Format tokens and duration
        tokens_str = f'<span class="tokens">{event.tokens_used} tokens</span>' if event.tokens_used else ''
        duration_str = f'<span class="duration">{event.duration_ms:.1f}ms</span>' if event.duration_ms else ''
        
        events_html.append(f'''
            <div class="event {event_class}">
                <div class="event-header collapsible" onclick="toggleContent('event-{i}')">
                    <span class="event-type">{event.event_type.value}</span>
                    <span class="event-timestamp">{event.timestamp}</span>
                    <span class="event-agent">{event.agent_type}</span>
                    <span class="event-agent">{event.stage}</span>
                    {tokens_str}
                    {duration_str}
                </div>
                <div class="event-content {'hidden' if is_large else ''}" id="event-{i}">
                    <div class="event-data">
                        <pre>{data_str}</pre>
                    </div>
                </div>
            </div>
        ''')
    
    events_timeline = '\n'.join(events_html)
    
    # Generate complete HTML
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trace Viewer - {trace.trace_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: #2c3e50;
            color: white;
            padding: 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .metadata {{
            background: #ecf0f1;
            padding: 15px;
            border-bottom: 1px solid #bdc3c7;
        }}
        .metadata .row {{
            display: flex;
            margin-bottom: 8px;
        }}
        .metadata .label {{
            font-weight: bold;
            width: 150px;
            color: #2c3e50;
        }}
        .metadata .value {{
            flex: 1;
            font-family: 'Courier New', monospace;
        }}
        .stats {{
            display: flex;
            background: #3498db;
            color: white;
        }}
        .stat {{
            flex: 1;
            padding: 15px;
            text-align: center;
            border-right: 1px solid rgba(255,255,255,0.2);
        }}
        .stat:last-child {{
            border-right: none;
        }}
        .stat .number {{
            font-size: 24px;
            font-weight: bold;
            display: block;
        }}
        .stat .label {{
            font-size: 12px;
            opacity: 0.8;
        }}
        .timeline {{
            padding: 20px;
        }}
        .event {{
            margin-bottom: 15px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            position: relative;
        }}
        .event.llm_prompt {{
            border-left-color: #e74c3c;
        }}
        .event.llm_response {{
            border-left-color: #e67e22;
        }}
        .event.tool_call {{
            border-left-color: #f39c12;
        }}
        .event.stage_start {{
            border-left-color: #27ae60;
        }}
        .event.stage_end {{
            border-left-color: #16a085;
        }}
        .event.error {{
            border-left-color: #c0392b;
        }}
        .event-header {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            cursor: pointer;
            padding: 5px;
            border-radius: 4px;
        }}
        .event-header:hover {{
            background: #f8f9fa;
        }}
        .event-type {{
            background: #3498db;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            margin-right: 10px;
        }}
        .event.llm_prompt .event-type {{
            background: #e74c3c;
        }}
        .event.llm_response .event-type {{
            background: #e67e22;
        }}
        .event.tool_call .event-type {{
            background: #f39c12;
        }}
        .event.stage_start .event-type {{
            background: #27ae60;
        }}
        .event.stage_end .event-type {{
            background: #16a085;
        }}
        .event.error .event-type {{
            background: #c0392b;
        }}
        .event-timestamp {{
            color: #7f8c8d;
            font-size: 12px;
            font-family: 'Courier New', monospace;
        }}
        .event-agent {{
            background: #95a5a6;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            margin-left: 10px;
        }}
        .event-content {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            margin-top: 8px;
        }}
        .event-data {{
            font-family: 'Courier New', monospace;
            font-size: 12px;
            max-height: 400px;
            overflow-y: auto;
        }}
        .event-data pre {{
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .tokens {{
            color: #8e44ad;
            font-size: 11px;
            margin-left: 10px;
        }}
        .duration {{
            color: #2980b9;
            font-size: 11px;
            margin-left: 10px;
        }}
        .collapsible {{
            cursor: pointer;
            user-select: none;
        }}
        .hidden {{
            display: none;
        }}
        .trace-source {{
            display: inline-block;
            background: #9b59b6;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            margin-left: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Trace Viewer</h1>
            <p>Trace ID: {trace.trace_id}</p>
        </div>
        
        <div class="metadata">
            <div class="row">
                <span class="label">Source:</span>
                <span class="value">{trace.source} <span class="trace-source">{trace.source.upper()}</span></span>
            </div>
            <div class="row">
                <span class="label">Start Time:</span>
                <span class="value">{trace.start_time}</span>
            </div>
            <div class="row">
                <span class="label">End Time:</span>
                <span class="value">{trace.end_time or 'In Progress'}</span>
            </div>
            <div class="row">
                <span class="label">Duration:</span>
                <span class="value">{trace.total_duration_ms or 0:.0f}ms</span>
            </div>
            <div class="row">
                <span class="label">Initial Input:</span>
                <span class="value">{trace.initial_input[:100]}{'...' if len(trace.initial_input) > 100 else ''}</span>
            </div>
            {metadata_html}
        </div>
        
        <div class="stats">
            <div class="stat">
                <span class="number">{len(trace.events)}</span>
                <span class="label">Total Events</span>
            </div>
            <div class="stat">
                <span class="number">{llm_calls}</span>
                <span class="label">LLM Calls</span>
            </div>
            <div class="stat">
                <span class="number">{tool_calls}</span>
                <span class="label">Tool Calls</span>
            </div>
            <div class="stat">
                <span class="number">{total_tokens}</span>
                <span class="label">Total Tokens</span>
            </div>
        </div>
        
        <div class="timeline">
            <h3>📅 Event Timeline</h3>
            {events_timeline}
        </div>
    </div>
    
    <script>
        function toggleContent(id) {{
            const element = document.getElementById(id);
            element.classList.toggle('hidden');
        }}
        
        // Auto-expand LLM prompts and responses by default
        document.addEventListener('DOMContentLoaded', function() {{
            const llmEvents = document.querySelectorAll('.event.llm_prompt .event-content, .event.llm_response .event-content');
            llmEvents.forEach(content => {{
                content.classList.remove('hidden');
            }});
        }});
    </script>
</body>
</html>
    """
    
    return html