"""
Hierarchical HTML generator for trace viewer.

Creates an intuitive, hierarchical view of trace events organized by
agents and showing clear parent-child relationships.
"""

import json
from typing import Dict, Any, List
from .trace_models import CompleteTrace, TraceEventType, TraceEvent
from .trace_hierarchy import build_trace_hierarchy, HierarchicalEvent, AgentSection, StageInfo
from .trace_formatters import (
    format_duration, format_token_count, estimate_api_cost,
    format_cost, truncate_text, extract_prompt_components
)


def generate_hierarchical_trace_html(trace: CompleteTrace) -> str:
    """
    Generate hierarchical HTML view of trace.
    
    Args:
        trace: Complete trace object
        
    Returns:
        Self-contained HTML string
    """
    # Build hierarchy
    sections, summary = build_trace_hierarchy(trace)
    
    # Generate HTML
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trace Analysis - {trace.trace_id}</title>
    <style>
        {_generate_css()}
    </style>
</head>
<body>
    <div class="container">
        {_generate_header(trace, summary)}
        {_generate_summary_cards(sections, summary)}
        {_generate_timeline(sections)}
        {_generate_agent_sections(sections)}
    </div>
    
    <script>
        {_generate_javascript()}
    </script>
</body>
</html>
    """
    
    return html


def _generate_css() -> str:
    """Generate CSS styles"""
    return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f5f7fa;
            color: #2c3e50;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Header Styles */
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            margin: 0 0 10px 0;
            font-size: 28px;
            font-weight: 600;
        }
        
        .header-meta {
            display: flex;
            gap: 30px;
            margin-top: 15px;
            font-size: 14px;
            opacity: 0.9;
        }
        
        /* Summary Cards */
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            text-align: center;
            transition: transform 0.2s;
        }
        
        .summary-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        
        .summary-card .icon {
            font-size: 32px;
            margin-bottom: 10px;
        }
        
        .summary-card .value {
            font-size: 32px;
            font-weight: 700;
            color: #2c3e50;
            margin: 10px 0;
        }
        
        .summary-card .label {
            font-size: 14px;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Timeline */
        .timeline-section {
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .timeline-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .timeline-header h2 {
            margin: 0;
            color: #2c3e50;
            font-size: 20px;
        }
        
        .timeline {
            display: flex;
            gap: 20px;
            overflow-x: auto;
            padding: 20px 0;
        }
        
        .timeline-agent {
            flex: 0 0 200px;
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            border-left: 4px solid #3498db;
        }
        
        .timeline-agent.cmo {
            border-left-color: #e74c3c;
        }
        
        .timeline-agent.specialist {
            border-left-color: #2ecc71;
        }
        
        /* Agent Sections */
        .agent-section {
            background: white;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            overflow: hidden;
        }
        
        /* Stage Sections */
        .stage-section {
            margin: 15px 0;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            overflow: hidden;
        }
        
        .stage-header {
            background: #f8f9fa;
            padding: 12px 15px;
            cursor: pointer;
            user-select: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .stage-header:hover {
            background: #e9ecef;
        }
        
        .stage-header h4 {
            margin: 0;
            color: #2c3e50;
            font-size: 15px;
            font-weight: 600;
        }
        
        .stage-meta {
            display: flex;
            gap: 15px;
            font-size: 12px;
            color: #7f8c8d;
        }
        
        .stage-content {
            padding: 15px;
            display: none;
        }
        
        .stage-content.show {
            display: block;
        }
        
        .agent-header {
            background: #f8f9fa;
            padding: 20px;
            cursor: pointer;
            user-select: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s;
        }
        
        .agent-header:hover {
            background: #e9ecef;
        }
        
        .agent-header.cmo {
            border-left: 5px solid #e74c3c;
        }
        
        .agent-header.specialist {
            border-left: 5px solid #2ecc71;
        }
        
        .agent-info {
            flex: 1;
        }
        
        .agent-title {
            font-size: 18px;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        
        .agent-meta {
            display: flex;
            gap: 20px;
            font-size: 13px;
            color: #7f8c8d;
        }
        
        .toggle-icon {
            font-size: 20px;
            color: #7f8c8d;
            transition: transform 0.3s;
        }
        
        .agent-header.expanded .toggle-icon {
            transform: rotate(180deg);
        }
        
        .agent-content {
            display: none;
            padding: 20px;
        }
        
        .agent-content.show {
            display: block;
        }
        
        /* Event Hierarchy */
        .event-tree {
            margin: 0;
            padding: 0;
        }
        
        .event-node {
            margin: 10px 0;
            position: relative;
        }
        
        .event-node.level-1 {
            margin-left: 30px;
        }
        
        .event-node.level-2 {
            margin-left: 60px;
        }
        
        .event-node.level-3 {
            margin-left: 90px;
        }
        
        .event-connector {
            position: absolute;
            left: -20px;
            top: 0;
            bottom: 0;
            width: 1px;
            background: #ddd;
        }
        
        .event-connector::before {
            content: '';
            position: absolute;
            left: 0;
            top: 20px;
            width: 15px;
            height: 1px;
            background: #ddd;
        }
        
        .event-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            border: 1px solid #e9ecef;
            position: relative;
            transition: all 0.2s;
        }
        
        .event-card:hover {
            background: #fff;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .event-card.llm-prompt {
            border-left: 3px solid #3498db;
            background: #e8f4fd;
        }
        
        .event-card.llm-response {
            border-left: 3px solid #2ecc71;
            background: #e8f8f5;
        }
        
        .event-card.tool-invocation {
            border-left: 3px solid #f39c12;
            background: #fef5e7;
        }
        
        .event-card.tool-result {
            border-left: 3px solid #9b59b6;
            background: #f4ecf7;
        }
        
        .event-header-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .event-type-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            color: white;
        }
        
        .event-type-badge.llm-prompt {
            background: #3498db;
        }
        
        .event-type-badge.llm-response {
            background: #2ecc71;
        }
        
        .event-type-badge.tool-invocation {
            background: #f39c12;
        }
        
        .event-type-badge.tool-result {
            background: #9b59b6;
        }
        
        .event-metadata {
            display: flex;
            gap: 15px;
            font-size: 12px;
            color: #7f8c8d;
        }
        
        .event-content {
            margin-top: 10px;
        }
        
        .event-summary {
            font-size: 14px;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        
        .event-details {
            display: none;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #e9ecef;
        }
        
        .event-details.show {
            display: block;
        }
        
        .show-details-btn {
            color: #3498db;
            cursor: pointer;
            font-size: 13px;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        
        .show-details-btn:hover {
            text-decoration: underline;
        }
        
        /* Key Findings */
        .key-findings {
            background: #e8f4fd;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
        }
        
        .key-findings h4 {
            margin: 0 0 10px 0;
            color: #2980b9;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .findings-list {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .finding-badge {
            background: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 13px;
            border: 1px solid #3498db;
            color: #2980b9;
        }
        
        /* Utility Classes */
        .hidden {
            display: none;
        }
        
        .copy-btn {
            background: none;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            padding: 4px 8px;
            cursor: pointer;
            font-size: 12px;
            color: #7f8c8d;
            transition: all 0.2s;
        }
        
        .copy-btn:hover {
            background: #3498db;
            color: white;
            border-color: #3498db;
        }
        
        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
    """


def _generate_javascript() -> str:
    """Generate JavaScript for interactivity"""
    return """
        function toggleAgent(agentId) {
            const header = document.getElementById(agentId + '-header');
            const content = document.getElementById(agentId + '-content');
            
            header.classList.toggle('expanded');
            content.classList.toggle('show');
        }
        
        function toggleEventDetails(eventId) {
            const details = document.getElementById(eventId + '-details');
            const btn = document.getElementById(eventId + '-btn');
            
            details.classList.toggle('show');
            
            if (details.classList.contains('show')) {
                btn.innerHTML = '▼ Hide Details';
            } else {
                btn.innerHTML = '▶ Show Details';
            }
        }
        
        function copyEventData(eventId) {
            const eventData = document.getElementById(eventId + '-data').textContent;
            navigator.clipboard.writeText(eventData).then(() => {
                showToast('Event data copied to clipboard!');
            });
        }
        
        function showToast(message) {
            const toast = document.createElement('div');
            toast.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: #27ae60;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                z-index: 1000;
                animation: slideIn 0.3s ease;
            `;
            toast.textContent = message;
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => document.body.removeChild(toast), 300);
            }, 2000);
        }
        
        // Add CSS animations
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
        
        // Auto-expand first agent on load
        document.addEventListener('DOMContentLoaded', () => {
            const firstAgent = document.querySelector('.agent-header');
            if (firstAgent) {
                firstAgent.click();
            }
        });
    """


def _generate_header(trace: CompleteTrace, summary: Dict[str, Any]) -> str:
    """Generate header section"""
    total_cost = estimate_api_cost(summary.get('total_tokens', 0))
    
    return f"""
    <div class="header">
        <h1>🔍 Trace Analysis Report</h1>
        <div class="header-meta">
            <div>
                <strong>Trace ID:</strong> {trace.trace_id}
            </div>
            <div>
                <strong>Duration:</strong> {format_duration(trace.total_duration_ms)}
            </div>
            <div>
                <strong>Start Time:</strong> {trace.start_time}
            </div>
            <div>
                <strong>Cost:</strong> {format_cost(total_cost)}
            </div>
        </div>
        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.2);">
            <strong>Query:</strong> {truncate_text(trace.initial_input, 200)}
        </div>
    </div>
    """


def _generate_summary_cards(sections: List[AgentSection], summary: Dict[str, Any]) -> str:
    """Generate summary cards"""
    return f"""
    <div class="summary-cards">
        <div class="summary-card">
            <div class="icon">👥</div>
            <div class="value">{summary['total_agents']}</div>
            <div class="label">Agents Involved</div>
        </div>
        <div class="summary-card">
            <div class="icon">🔵</div>
            <div class="value">{summary['total_llm_calls']}</div>
            <div class="label">LLM Calls</div>
        </div>
        <div class="summary-card">
            <div class="icon">🔧</div>
            <div class="value">{summary['total_tool_calls']}</div>
            <div class="label">Tool Calls</div>
        </div>
        <div class="summary-card">
            <div class="icon">🎯</div>
            <div class="value">{format_token_count(summary['total_tokens'])}</div>
            <div class="label">Tokens Used</div>
        </div>
    </div>
    """


def _generate_timeline(sections: List[AgentSection]) -> str:
    """Generate timeline visualization showing stages"""
    timeline_items = []
    
    for section in sections:
        agent_class = "cmo" if section.agent_type == "cmo" else "specialist"
        
        # Show each stage as a timeline item
        for stage_name, stage_info in sorted(section.stages.items(), key=lambda x: x[1].start_time or ""):
            timeline_items.append(f"""
            <div class="timeline-agent {agent_class}">
                <div style="font-weight: 600; margin-bottom: 5px;">{section.agent_name}</div>
                <div style="font-size: 11px; color: #34495e; margin-bottom: 3px;">📍 {stage_name}</div>
                <div style="font-size: 12px; color: #7f8c8d;">
                    <div>⏱️ {format_duration(stage_info.duration_ms)}</div>
                    <div>🔵 {stage_info.llm_calls} LLM calls</div>
                    <div>🔧 {stage_info.tool_calls} tool calls</div>
                </div>
            </div>
            """)
    
    return f"""
    <div class="timeline-section">
        <div class="timeline-header">
            <h2>📊 Execution Timeline</h2>
            <span style="font-size: 13px; color: #7f8c8d;">
                Scroll horizontally to see all agents →
            </span>
        </div>
        <div class="timeline">
            {"".join(timeline_items)}
        </div>
    </div>
    """


def _generate_agent_sections(sections: List[AgentSection]) -> str:
    """Generate agent sections with hierarchical events"""
    sections_html = []
    
    for i, section in enumerate(sections):
        agent_id = f"agent-{i}"
        agent_class = "cmo" if section.agent_type == "cmo" else "specialist"
        
        # Generate stage sections
        stages_html = []
        for stage_name, stage_info in sorted(section.stages.items(), key=lambda x: x[1].start_time or ""):
            stage_id = f"{agent_id}-{stage_name.replace(' ', '-')}"
            stage_events_html = _generate_event_tree(stage_info.events, stage_id)
            
            stages_html.append(f"""
            <div class="stage-section">
                <div class="stage-header" onclick="toggleSection(this)">
                    <h4>📍 {stage_name.replace('_', ' ').title()}</h4>
                    <div class="stage-meta">
                        <span>⏱️ {format_duration(stage_info.duration_ms)}</span>
                        <span>🔵 {stage_info.llm_calls} LLM calls</span>
                        <span>🔧 {stage_info.tool_calls} tool calls</span>
                    </div>
                </div>
                <div class="stage-content show">
                    {stage_events_html}
                </div>
            </div>
            """)
        
        # Generate key findings if any
        findings_html = ""
        if section.key_findings:
            findings_items = "".join(
                f'<span class="finding-badge">{finding}</span>'
                for finding in section.key_findings[:5]
            )
            findings_html = f"""
            <div class="key-findings">
                <h4>Key Findings</h4>
                <div class="findings-list">
                    {findings_items}
                </div>
            </div>
            """
        
        # Create stages summary for header
        stages_summary = ", ".join(sorted(section.stages.keys()))
        
        sections_html.append(f"""
        <div class="agent-section">
            <div class="agent-header {agent_class}" id="{agent_id}-header" onclick="toggleAgent('{agent_id}')">
                <div class="agent-info">
                    <div class="agent-title">{section.agent_name}</div>
                    <div class="agent-meta">
                        <span>📋 Stages: {stages_summary}</span>
                        <span>⏱️ {format_duration(section.total_duration_ms)}</span>
                        <span>🔵 {section.llm_calls} LLM calls</span>
                        <span>🔧 {section.tool_calls} tool calls</span>
                        <span>🎯 {format_token_count(section.tokens_used)} tokens</span>
                    </div>
                </div>
                <div class="toggle-icon">▼</div>
            </div>
            <div class="agent-content" id="{agent_id}-content">
                {findings_html}
                <div class="stages-container">
                    {"".join(stages_html)}
                </div>
            </div>
        </div>
        """)
    
    return "\n".join(sections_html)


def _generate_event_tree(events: List[HierarchicalEvent], agent_id: str) -> str:
    """Generate hierarchical event tree"""
    html_parts = []
    
    for event in events:
        html_parts.append(_generate_event_node(event, agent_id))
    
    return "\n".join(html_parts)


def _generate_event_node(event: HierarchicalEvent, agent_id: str) -> str:
    """Generate single event node with children"""
    event_id = f"{agent_id}-event-{event.event_index}"
    event_type = event.event.event_type.value.lower().replace('_', '-')
    
    # Generate event summary based on type
    summary = _generate_event_summary(event.event)
    
    # Generate detailed view
    details = _generate_event_details(event.event)
    
    # Generate children recursively
    children_html = ""
    if event.children:
        children_parts = []
        for child in event.children:
            children_parts.append(_generate_event_node(child, agent_id))
        children_html = "\n".join(children_parts)
    
    # Build the node
    connector = '<div class="event-connector"></div>' if event.level > 0 else ''
    
    return f"""
    <div class="event-node level-{event.level}">
        {connector}
        <div class="event-card {event_type}">
            <div class="event-header-row">
                <span class="event-type-badge {event_type}">
                    {_get_event_icon(event.event.event_type)} {event.event.event_type.value}
                </span>
                <div class="event-metadata">
                    <span>{event.event.timestamp}</span>
                    {f'<span>{format_duration(event.event.duration_ms)}</span>' if event.event.duration_ms else ''}
                    {f'<span>{format_token_count(event.event.tokens_used)} tokens</span>' if event.event.tokens_used else ''}
                    <button class="copy-btn" onclick="copyEventData('{event_id}')">📋</button>
                </div>
            </div>
            <div class="event-content">
                <div class="event-summary">
                    {summary}
                </div>
                <a class="show-details-btn" id="{event_id}-btn" onclick="toggleEventDetails('{event_id}')">
                    ▶ Show Details
                </a>
                <div class="event-details" id="{event_id}-details">
                    {details}
                </div>
                <div class="hidden" id="{event_id}-data">{json.dumps(event.event.data, indent=2)}</div>
            </div>
        </div>
        {children_html}
    </div>
    """


def _get_event_icon(event_type: TraceEventType) -> str:
    """Get icon for event type"""
    icons = {
        TraceEventType.USER_QUERY: "👤",
        TraceEventType.LLM_PROMPT: "📝",
        TraceEventType.LLM_RESPONSE: "💬",
        TraceEventType.TOOL_INVOCATION: "🔧",
        TraceEventType.TOOL_RESULT: "📊",
        TraceEventType.STAGE_START: "▶️",
        TraceEventType.STAGE_END: "⏹️",
        TraceEventType.ERROR: "❌"
    }
    return icons.get(event_type, "📌")


def _generate_event_summary(event: TraceEvent) -> str:
    """Generate human-readable event summary"""
    data = event.data or {}
    
    if event.event_type == TraceEventType.LLM_PROMPT:
        prompt_file = data.get('prompt_file', 'Unknown')
        model = data.get('model', 'Unknown')
        return f"<strong>Prompt:</strong> {prompt_file} | <strong>Model:</strong> {model}"
        
    elif event.event_type == TraceEventType.LLM_RESPONSE:
        response_preview = truncate_text(data.get('response_text', ''), 150)
        tool_calls = data.get('tool_calls', [])
        if tool_calls:
            return f"<strong>Response:</strong> Requesting tools: {', '.join(tool_calls)}"
        else:
            return f"<strong>Response:</strong> {response_preview}"
            
    elif event.event_type == TraceEventType.TOOL_INVOCATION:
        tool_name = data.get('tool_name', 'Unknown')
        tool_input = data.get('tool_input', {})
        query = tool_input.get('query', '') if isinstance(tool_input, dict) else ''
        return f"<strong>Tool:</strong> {tool_name} | <strong>Query:</strong> {query}"
        
    elif event.event_type == TraceEventType.TOOL_RESULT:
        success = data.get('success', False)
        result_data = data.get('result_data', {})
        if success and result_data:
            count = result_data.get('result_count', 0)
            # Extract key value if present
            results = result_data.get('results', [])
            if results and len(results) > 0:
                first_result = results[0]
                if 'GLUCOSE_VALUE' in first_result:
                    value = first_result.get('GLUCOSE_VALUE')
                    unit = first_result.get('UNIT', '')
                    date = first_result.get('RECORD_DATE', '')
                    return f"<strong>✅ Result:</strong> {value} {unit} on {date} ({count} total results)"
            return f"<strong>✅ Success:</strong> {count} results found"
        else:
            error = data.get('error', 'Unknown error')
            return f"<strong>❌ Failed:</strong> {error}"
            
    elif event.event_type == TraceEventType.STAGE_START:
        stage = data.get('stage', 'Unknown')
        return f"<strong>Starting:</strong> {stage}"
        
    elif event.event_type == TraceEventType.STAGE_END:
        stage = data.get('stage', 'Unknown')
        return f"<strong>Completed:</strong> {stage}"
        
    else:
        return f"<strong>{event.event_type.value}:</strong> Event occurred"


def _generate_event_details(event: TraceEvent) -> str:
    """Generate detailed event view"""
    data = event.data or {}
    
    if event.event_type == TraceEventType.LLM_PROMPT:
        # Extract prompt components
        messages = data.get('messages', [])
        system_prompt = data.get('system_prompt', '')
        components = extract_prompt_components(messages, system_prompt)
        
        return f"""
        <div style="margin-top: 10px;">
            <strong>Current Prompt:</strong>
            <pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; font-size: 12px;">
{components['current_prompt']}</pre>
            
            {f'<strong>System Prompt:</strong><pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; font-size: 12px;">{system_prompt}</pre>' if system_prompt else ''}
            
            {f'<details><summary><strong>Conversation History ({components["history_size"]} messages)</strong></summary><pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; font-size: 12px;">{json.dumps(components["conversation_history"], indent=2)}</pre></details>' if components['history_size'] > 0 else ''}
        </div>
        """
        
    elif event.event_type == TraceEventType.TOOL_RESULT:
        # Show full tool results
        result_data = data.get('result_data', {})
        metadata = event.metadata or {}
        full_output = metadata.get('tool_output', result_data)
        
        return f"""
        <div style="margin-top: 10px;">
            <strong>Full Results:</strong>
            <pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; font-size: 12px; max-height: 300px; overflow-y: auto;">
{json.dumps(full_output, indent=2)}</pre>
        </div>
        """
        
    else:
        # Default detailed view
        return f"""
        <div style="margin-top: 10px;">
            <pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin: 5px 0; font-size: 12px;">
{json.dumps(data, indent=2)}</pre>
        </div>
        """