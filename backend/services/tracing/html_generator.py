"""
HTML generator for trace viewer.

Provides standalone HTML generation for trace viewing without requiring
a backend server. The generated HTML is self-contained with all styling
and JavaScript inline.
"""

import json
from typing import Dict, Any, List
from .trace_models import CompleteTrace, TraceEventType
from .trace_formatters import (
    format_duration, format_token_count, estimate_api_cost, 
    format_cost, truncate_text, extract_prompt_components,
    format_tool_result_summary, calculate_performance_metrics
)


def format_conversation_history(messages: List[Dict[str, Any]]) -> str:
    """Format conversation history for better readability"""
    if not messages:
        return "<p>No conversation history</p>"
    
    html_parts = []
    for i, msg in enumerate(messages):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        
        # Format role with color
        role_colors = {
            'user': '#2ecc71',
            'assistant': '#3498db',
            'system': '#e74c3c'
        }
        role_color = role_colors.get(role, '#95a5a6')
        
        html_parts.append(f'<div class="conversation-message">')
        html_parts.append(f'<div class="message-header" style="color: {role_color}"><strong>{role.upper()}</strong></div>')
        
        # Format content based on type
        if isinstance(content, str):
            # Simple text content
            html_parts.append(f'<div class="message-content"><pre>{truncate_text(content, 500)}</pre></div>')
        elif isinstance(content, list):
            # Complex content (tool results, etc.)
            for item in content:
                if isinstance(item, dict):
                    if item.get('type') == 'text':
                        html_parts.append(f'<div class="message-content"><pre>{item.get("text", "")}</pre></div>')
                    elif item.get('type') == 'tool_result':
                        # Format tool result nicely
                        tool_content = item.get('content', '')
                        try:
                            # Try to parse as JSON for better formatting
                            tool_data = json.loads(tool_content) if isinstance(tool_content, str) else tool_content
                            if isinstance(tool_data, dict):
                                # Extract key information
                                query = tool_data.get('query', 'N/A')
                                results = tool_data.get('results', [])
                                result_count = tool_data.get('result_count', 0)
                                
                                html_parts.append('<div class="tool-result-content">')
                                html_parts.append(f'<strong>Tool Result:</strong> Query "{query}"<br>')
                                html_parts.append(f'<strong>Found:</strong> {result_count} results<br>')
                                
                                if results and len(results) > 0:
                                    # Show first result as preview
                                    first_result = results[0]
                                    if 'GLUCOSE_VALUE' in first_result or 'VALUE_NUMERIC' in first_result:
                                        value = first_result.get('GLUCOSE_VALUE') or first_result.get('VALUE_NUMERIC', 'N/A')
                                        unit = first_result.get('UNIT') or first_result.get('MEASUREMENT_DIMENSION', '')
                                        date = first_result.get('RECORD_DATE', 'N/A')
                                        html_parts.append(f'<strong>Latest Result:</strong> {value} {unit} on {date}')
                                    else:
                                        html_parts.append(f'<details><summary>View Result</summary><pre>{json.dumps(first_result, indent=2)}</pre></details>')
                                
                                html_parts.append('</div>')
                            else:
                                html_parts.append(f'<div class="message-content"><pre>{json.dumps(tool_data, indent=2)}</pre></div>')
                        except:
                            html_parts.append(f'<div class="message-content"><pre>{tool_content}</pre></div>')
                    elif item.get('type') == 'tool_use':
                        html_parts.append(f'<div class="tool-use-content"><strong>Tool Call:</strong> {item.get("name", "unknown")}</div>')
        else:
            # Fallback
            html_parts.append(f'<div class="message-content"><pre>{json.dumps(content, indent=2)}</pre></div>')
        
        html_parts.append('</div>')
    
    return '\n'.join(html_parts)


def format_event_data(event) -> str:
    """Format event data based on event type for better display"""
    if event.event_type == TraceEventType.LLM_PROMPT:
        # Extract prompt components
        data = event.data or {}
        components = extract_prompt_components(
            data.get('messages', []),
            data.get('system_prompt')
        )
        
        html = f'''
        <div class="prompt-sections">
            <div class="prompt-section">
                <h4>Active Prompt</h4>
                <div class="prompt-content">
                    <div class="prompt-meta">
                        <span>Model: {data.get('model', 'unknown')}</span>
                        <span>Temperature: {data.get('temperature', 0)}</span>
                        <span>Max Tokens: {data.get('max_tokens', 0)}</span>
                        {f"<span>Prompt File: {data.get('prompt_file', 'none')}</span>" if data.get('prompt_file') else ""}
                    </div>
                    <pre>{components['current_prompt']}</pre>
                </div>
            </div>
            {"<div class='prompt-section'><h4>System Prompt</h4><pre>" + components['system_prompt'] + "</pre></div>" if components['system_prompt'] else ""}
            {f"<div class='prompt-section collapsible-section'><h4 onclick='toggleSection(this)'>Conversation History ({components['history_size']} messages)</h4><div class='section-content hidden'>{format_conversation_history(components['conversation_history'])}</div></div>" if components['history_size'] > 0 else ""}
        </div>
        '''
        return html
        
    elif event.event_type == TraceEventType.LLM_RESPONSE:
        data = event.data or {}
        response_text = data.get('response_text', '')
        
        # Format response with markdown support (basic)
        formatted_response = response_text.replace('\n\n', '</p><p>').replace('\n', '<br>')
        
        html = f'''
        <div class="response-content">
            <div class="response-meta">
                <span>Stop Reason: {data.get('stop_reason', 'unknown')}</span>
                <span>Model: {data.get('model', 'unknown')}</span>
                {f"<span>Tool Calls: {', '.join(data.get('tool_calls', []))}</span>" if data.get('tool_calls') else ""}
            </div>
            <div class="response-text">
                <p>{formatted_response}</p>
            </div>
        </div>
        '''
        return html
        
    elif event.event_type == TraceEventType.TOOL_INVOCATION:
        data = event.data or {}
        tool_id = data.get('tool_id', '')
        html = f'''
        <div class="tool-invocation" data-tool-id="{tool_id}">
            <h4>Tool: {data.get('tool_name', 'unknown')}</h4>
            <div class="tool-id">Tool ID: {tool_id}</div>
            <div class="tool-params">
                <pre>{json.dumps(data.get('tool_input', {}), indent=2)}</pre>
            </div>
        </div>
        '''
        return html
        
    elif event.event_type == TraceEventType.TOOL_RESULT:
        data = event.data or {}
        success = data.get('success', False)
        result_data = data.get('result_data', {})
        linked_id = data.get('linked_tool_invocation_id', '')
        
        # Get the full tool output from metadata if available
        full_output = event.metadata.get('tool_output') if event.metadata else None
        
        # Format actual results if available
        results_html = ""
        if result_data and result_data.get('results'):
            results = result_data['results']
            result_count = result_data.get('result_count', len(results))
            
            if results and len(results) > 0:
                # Show summary of results
                results_summary = f'''
                <div class="results-summary">
                    <strong>Query:</strong> {result_data.get('query', 'N/A')}<br>
                    <strong>Results Found:</strong> {result_count}<br>
                    <strong>Success:</strong> {'Yes' if result_data.get('query_successful', False) else 'No'}
                </div>
                '''
                
                # Show first few results as preview
                preview_results = results[:3]
                preview_html = ""
                for i, result in enumerate(preview_results):
                    # Format each result based on common health data fields
                    if 'GLUCOSE_VALUE' in result or 'VALUE_NUMERIC' in result:
                        # Lab result formatting
                        value = result.get('GLUCOSE_VALUE') or result.get('VALUE_NUMERIC', 'N/A')
                        unit = result.get('UNIT') or result.get('MEASUREMENT_DIMENSION', '')
                        date = result.get('RECORD_DATE', 'N/A')
                        provider = result.get('PROVIDER', 'N/A')
                        preview_html += f'''
                        <div class="result-item">
                            <strong>Result #{i+1}:</strong> {value} {unit}<br>
                            <span class="result-meta">Date: {date} | Provider: {provider}</span>
                        </div>
                        '''
                    else:
                        # Generic result formatting
                        preview_html += f'<div class="result-item"><pre>{json.dumps(result, indent=2)}</pre></div>'
                
                # Full results in collapsible section
                full_results_html = ""
                if len(results) > 3 or full_output:
                    results_to_show = full_output if full_output else {"results": results, "count": result_count}
                    full_results_html = f'''
                    <div class="collapsible-results">
                        <h5 onclick="toggleSection(this)" class="collapsible-header">
                            📊 View Complete Results ({result_count} total) ▼
                        </h5>
                        <div class="section-content hidden">
                            <pre>{json.dumps(results_to_show, indent=2)}</pre>
                        </div>
                    </div>
                    '''
                
                results_html = f'''
                <div class="actual-results">
                    {results_summary}
                    <div class="results-preview">
                        <h5>Preview:</h5>
                        {preview_html}
                    </div>
                    {full_results_html}
                </div>
                '''
        
        html = f'''
        <div class="tool-result {'' if success else 'error'}" data-linked-tool-id="{linked_id}">
            <h4>Result: {'✅ Success' if success else '❌ Failed'}</h4>
            {f'<div class="tool-id">Linked to Tool ID: {linked_id}</div>' if linked_id else ''}
            <div class="result-summary">
                {data.get('result_summary', '') or data.get('error', 'No summary available')}
            </div>
            {f"<div class='result-meta'><span>Duration: {format_duration(data.get('duration_ms'))}</span><span>Records: {data.get('result_count', 0)}</span></div>" if success else ""}
            {results_html}
        </div>
        '''
        return html
        
    else:
        # Default formatting
        return f'<pre>{json.dumps(event.data, indent=2)}</pre>'


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
    tool_results = len([e for e in trace.events if e.event_type == TraceEventType.TOOL_RESULT])
    errors = len([e for e in trace.events if e.event_type == TraceEventType.ERROR])
    
    # Calculate costs
    models_used = {}
    for event in trace.events:
        if event.event_type == TraceEventType.LLM_PROMPT and event.data:
            model = event.data.get('model', 'unknown')
            models_used[model] = models_used.get(model, 0) + (event.tokens_used or 0)
    
    total_cost = sum(estimate_api_cost(tokens, model) for model, tokens in models_used.items())
    
    # Calculate performance metrics
    perf_metrics = calculate_performance_metrics(trace.events)
    
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
        tokens_str = f'<span class="tokens">{format_token_count(event.tokens_used)} tokens</span>' if event.tokens_used else ''
        duration_str = f'<span class="duration">{format_duration(event.duration_ms)}</span>' if event.duration_ms else ''
        
        # Special formatting for different event types
        event_data_html = format_event_data(event)
        
        # Add copy button
        copy_button = f'<button class="copy-btn" onclick="copyEvent(\'event-{i}\')" title="Copy event data">📋</button>'
        
        # Check if this event is connected to another
        connected_class = ""
        connection_indicator = ""
        
        if event.event_type == TraceEventType.TOOL_INVOCATION:
            connected_class = "tool-invocation-event"
            connection_indicator = '<div class="connection-line down"></div>'
        elif event.event_type == TraceEventType.TOOL_RESULT:
            connected_class = "tool-result-event"
            # Look back to see if previous event was tool invocation
            if i > 0 and trace.events[i-1].event_type == TraceEventType.TOOL_INVOCATION:
                connection_indicator = '<div class="connection-line up"></div>'
        elif event.event_type == TraceEventType.LLM_RESPONSE and event.data and event.data.get('tool_calls'):
            connected_class = "has-tool-calls"
            connection_indicator = '<div class="connection-line down"></div>'
        
        events_html.append(f'''
            <div class="event {event_class} {connected_class}">
                {connection_indicator}
                <div class="event-header collapsible" onclick="toggleContent('event-{i}')")
                    <span class="event-type">{event.event_type.value}</span>
                    <span class="event-timestamp">{event.timestamp}</span>
                    <span class="event-agent">{event.agent_type}</span>
                    <span class="event-agent">{event.stage}</span>
                    {tokens_str}
                    {duration_str}
                    {copy_button}
                </div>
                <div class="event-content {'hidden' if is_large and event.event_type not in [TraceEventType.LLM_PROMPT, TraceEventType.LLM_RESPONSE] else ''}" id="event-{i}">
                    <div class="event-data" data-raw='{json.dumps(event.data).replace("'", "&apos;")}'>
                        {event_data_html}
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
        .tooltip {{
            font-size: 11px;
            color: #7f8c8d;
            font-style: italic;
        }}
        .copy-btn {{
            background: none;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 2px 6px;
            margin-left: 10px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s;
        }}
        .copy-btn:hover {{
            background: #3498db;
            color: white;
            border-color: #3498db;
        }}
        .prompt-sections {{
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}
        .prompt-section {{
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 10px;
        }}
        .prompt-section h4 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
            font-size: 14px;
            cursor: pointer;
        }}
        .prompt-meta {{
            display: flex;
            gap: 15px;
            margin-bottom: 10px;
            font-size: 11px;
            color: #7f8c8d;
        }}
        .prompt-meta span {{
            background: #ecf0f1;
            padding: 2px 8px;
            border-radius: 3px;
        }}
        .response-content {{
            padding: 10px;
        }}
        .response-meta {{
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            font-size: 11px;
        }}
        .response-meta span {{
            background: #f39c12;
            color: white;
            padding: 2px 8px;
            border-radius: 3px;
        }}
        .response-text {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            line-height: 1.6;
        }}
        .tool-invocation, .tool-result {{
            padding: 10px;
        }}
        .tool-result.error {{
            background: #ffe6e6;
            border: 1px solid #ffcccc;
            border-radius: 4px;
        }}
        .tool-params {{
            background: #f0f0f0;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
        }}
        .result-summary {{
            font-size: 14px;
            margin: 10px 0;
        }}
        .result-meta {{
            display: flex;
            gap: 15px;
            font-size: 12px;
            color: #666;
        }}
        .actual-results {{
            margin-top: 15px;
            border-top: 1px solid #e0e0e0;
            padding-top: 10px;
        }}
        .actual-results h5 {{
            margin: 0 0 10px 0;
            color: #34495e;
            font-size: 13px;
        }}
        .actual-results pre {{
            background: #f5f5f5;
            padding: 10px;
            border-radius: 4px;
            font-size: 11px;
            max-height: 200px;
            overflow-y: auto;
        }}
        .more-results {{
            font-size: 11px;
            color: #7f8c8d;
            font-style: italic;
            margin: 5px 0 0 0;
        }}
        .tool-id {{
            font-size: 10px;
            color: #95a5a6;
            font-family: 'Courier New', monospace;
            margin: 5px 0;
        }}
        .results-summary {{
            background: #e8f4f8;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 10px;
            font-size: 12px;
        }}
        .results-preview {{
            margin-top: 10px;
        }}
        .result-item {{
            background: #f9f9f9;
            padding: 8px;
            margin: 5px 0;
            border-left: 3px solid #3498db;
            font-size: 12px;
        }}
        .result-item .result-meta {{
            color: #7f8c8d;
            font-size: 11px;
        }}
        .collapsible-results {{
            margin-top: 15px;
            border-top: 1px solid #e0e0e0;
            padding-top: 10px;
        }}
        .collapsible-header {{
            cursor: pointer;
            color: #2980b9;
            font-size: 13px;
            user-select: none;
            margin: 0;
        }}
        .collapsible-header:hover {{
            text-decoration: underline;
        }}
        .conversation-message {{
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
            background: #fafafa;
        }}
        .message-header {{
            font-size: 12px;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .message-content {{
            font-size: 12px;
            background: white;
            padding: 8px;
            border-radius: 4px;
            margin: 5px 0;
        }}
        .message-content pre {{
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .tool-result-content {{
            background: #e8f4f8;
            padding: 10px;
            border-radius: 4px;
            margin: 5px 0;
            font-size: 12px;
            border-left: 3px solid #3498db;
        }}
        .tool-use-content {{
            background: #fff3cd;
            padding: 8px;
            border-radius: 4px;
            margin: 5px 0;
            font-size: 12px;
            border-left: 3px solid #f39c12;
        }}
        .collapsible-section .section-content {{
            margin-top: 10px;
        }}
        .toast {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #27ae60;
            color: white;
            padding: 10px 20px;
            border-radius: 4px;
            opacity: 0;
            transition: opacity 0.3s;
            z-index: 1000;
        }}
        .toast.show {{
            opacity: 1;
        }}
        .event.tool_result {{
            border-left-color: #8e44ad;
        }}
        .event.tool_result .event-type {{
            background: #8e44ad;
        }}
        .connection-line {{
            position: absolute;
            width: 2px;
            height: 20px;
            background: #3498db;
            left: -8px;
        }}
        .connection-line.down {{
            bottom: -20px;
        }}
        .connection-line.up {{
            top: -20px;
        }}
        .tool-invocation-event {{
            position: relative;
            margin-bottom: 20px;
        }}
        .tool-result-event {{
            position: relative;
            margin-top: -10px;
        }}
        .has-tool-calls {{
            position: relative;
            margin-bottom: 20px;
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
                <span class="value">{format_duration(trace.total_duration_ms)} <span class="tooltip">({trace.total_duration_ms or 0:.0f}ms)</span></span>
            </div>
            <div class="row">
                <span class="label">Initial Input:</span>
                <span class="value">{truncate_text(trace.initial_input, 100)}</span>
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
                <span class="number">{format_token_count(total_tokens)}</span>
                <span class="label">Total Tokens</span>
            </div>
            <div class="stat">
                <span class="number">{format_cost(total_cost)}</span>
                <span class="label">Est. Cost</span>
            </div>
            <div class="stat">
                <span class="number">{errors}</span>
                <span class="label">Errors</span>
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
        
        function toggleSection(header) {{
            const content = header.nextElementSibling;
            content.classList.toggle('hidden');
        }}
        
        function copyEvent(eventId) {{
            event.stopPropagation();
            const eventEl = document.getElementById(eventId);
            const dataEl = eventEl.querySelector('.event-data');
            const rawData = dataEl.getAttribute('data-raw');
            
            // Parse and format the data
            try {{
                const data = JSON.parse(rawData);
                const formatted = JSON.stringify(data, null, 2);
                
                // Copy to clipboard
                navigator.clipboard.writeText(formatted).then(() => {{
                    showToast('Event data copied to clipboard!');
                }}).catch(err => {{
                    console.error('Failed to copy:', err);
                    // Fallback method
                    const textarea = document.createElement('textarea');
                    textarea.value = formatted;
                    document.body.appendChild(textarea);
                    textarea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textarea);
                    showToast('Event data copied to clipboard!');
                }});
            }} catch (e) {{
                console.error('Failed to parse event data:', e);
            }}
        }}
        
        function showToast(message) {{
            const toast = document.createElement('div');
            toast.className = 'toast';
            toast.textContent = message;
            document.body.appendChild(toast);
            
            setTimeout(() => toast.classList.add('show'), 10);
            setTimeout(() => {{
                toast.classList.remove('show');
                setTimeout(() => document.body.removeChild(toast), 300);
            }}, 2000);
        }}
        
        // Auto-expand LLM prompts and responses by default
        document.addEventListener('DOMContentLoaded', function() {{
            const llmEvents = document.querySelectorAll('.event.llm_prompt .event-content, .event.llm_response .event-content');
            llmEvents.forEach(content => {{
                content.classList.remove('hidden');
            }});
        }});
        
        // Add keyboard shortcuts
        document.addEventListener('keydown', function(e) {{
            // Ctrl/Cmd + F to focus search (if implemented)
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {{
                e.preventDefault();
                // Future: Focus search input
            }}
            
            // Escape to close all expanded sections
            if (e.key === 'Escape') {{
                document.querySelectorAll('.event-content:not(.hidden)').forEach(el => {{
                    el.classList.add('hidden');
                }});
            }}
        }});
    </script>
</body>
</html>
    """
    
    return html