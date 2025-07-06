import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Code } from 'lucide-react';

interface ToolCallSectionProps {
  content: string;
}

const ToolCallSection: React.FC<ToolCallSectionProps> = ({ content }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Parse the content to extract tool call information
  const lines = content.split('\n');
  let mainMessage = '';
  let toolCallInfo = '';
  let inToolCall = false;
  
  for (const line of lines) {
    if (line.includes('🔧 **Tool Call:') || line.includes('🔧 **') && line.includes('calling')) {
      inToolCall = true;
      toolCallInfo += line + '\n';
    } else if (inToolCall) {
      toolCallInfo += line + '\n';
    } else {
      mainMessage += line + '\n';
    }
  }
  
  // If no tool call found, just return the content as-is
  if (!toolCallInfo) {
    return <div className="whitespace-pre-wrap">{content}</div>;
  }
  
  // Extract parameters from tool call info
  const paramMatch = toolCallInfo.match(/```json\n([\s\S]*?)```/);
  const parameters = paramMatch ? paramMatch[1].trim() : '';
  
  return (
    <div>
      {/* Main message */}
      <div className="whitespace-pre-wrap mb-2">{mainMessage.trim()}</div>
      
      {/* Collapsible tool call section */}
      <div className="border border-blue-200 rounded-lg bg-blue-50 overflow-hidden">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full px-4 py-2 flex items-center justify-between hover:bg-blue-100 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Code className="w-4 h-4 text-blue-600" />
            <span className="font-medium text-blue-700">Tool Call: execute_health_query_v2</span>
          </div>
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-blue-600" />
          ) : (
            <ChevronRight className="w-4 h-4 text-blue-600" />
          )}
        </button>
        
        {isExpanded && parameters && (
          <div className="px-4 py-3 border-t border-blue-200 bg-white">
            <div className="text-sm font-medium text-gray-600 mb-2">Parameters:</div>
            <pre className="bg-gray-50 p-3 rounded text-xs overflow-x-auto">
              <code>{parameters}</code>
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default ToolCallSection;