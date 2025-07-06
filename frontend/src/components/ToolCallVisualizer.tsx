import React, { useState } from 'react';
import { 
  Code, ChevronDown, ChevronRight, Clock, 
  Database, CheckCircle, AlertCircle, Loader2 
} from 'lucide-react';

interface ToolCall {
  id: string;
  toolName: string;
  status: 'pending' | 'executing' | 'complete' | 'error';
  input?: any;
  output?: any;
  duration?: number;
  timestamp: Date;
  specialist?: string;
}

interface ToolCallVisualizerProps {
  toolCall: ToolCall;
  inline?: boolean;
}

const ToolCallVisualizer: React.FC<ToolCallVisualizerProps> = ({ toolCall, inline = false }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getStatusIcon = () => {
    switch (toolCall.status) {
      case 'pending':
        return <Clock className="w-4 h-4 text-gray-400" />;
      case 'executing':
        return <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />;
      case 'complete':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
    }
  };

  const getToolIcon = () => {
    if (toolCall.toolName.includes('query')) {
      return <Database className="w-4 h-4 text-purple-600" />;
    }
    return <Code className="w-4 h-4 text-blue-600" />;
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return '';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  if (inline) {
    return (
      <div className="my-2 bg-blue-50 border border-blue-200 rounded-lg overflow-hidden">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full px-4 py-2 flex items-center justify-between hover:bg-blue-100 transition-colors"
        >
          <div className="flex items-center gap-3">
            {getStatusIcon()}
            {getToolIcon()}
            <span className="text-sm font-medium text-blue-700">
              {toolCall.toolName}
            </span>
            {toolCall.specialist && (
              <span className="text-xs text-gray-600">
                via {toolCall.specialist}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {toolCall.duration && (
              <span className="text-xs text-gray-600">
                {formatDuration(toolCall.duration)}
              </span>
            )}
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-gray-600" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-600" />
            )}
          </div>
        </button>

        {isExpanded && (
          <div className="px-4 py-3 border-t border-blue-200 bg-white space-y-3">
            {toolCall.input && (
              <div>
                <h4 className="text-xs font-semibold text-gray-700 mb-2">Input Parameters</h4>
                <pre className="bg-gray-50 p-3 rounded text-xs overflow-x-auto border border-gray-200">
                  <code className="text-gray-700">
                    {JSON.stringify(toolCall.input, null, 2)}
                  </code>
                </pre>
              </div>
            )}

            {toolCall.output && (
              <div>
                <h4 className="text-xs font-semibold text-gray-700 mb-2">Output</h4>
                <pre className="bg-gray-50 p-3 rounded text-xs overflow-x-auto max-h-40 border border-gray-200">
                  <code className="text-gray-700">
                    {typeof toolCall.output === 'string' 
                      ? toolCall.output 
                      : JSON.stringify(toolCall.output, null, 2)}
                  </code>
                </pre>
              </div>
            )}

            <div className="flex justify-between text-xs text-gray-600">
              <span>Executed at {new Date(toolCall.timestamp).toLocaleTimeString()}</span>
              {toolCall.status === 'complete' && toolCall.duration && (
                <span>Completed in {formatDuration(toolCall.duration)}</span>
              )}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Full card display for tool call section
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {getStatusIcon()}
          <h3 className="font-medium text-gray-900">{toolCall.toolName}</h3>
        </div>
        <span className="text-sm text-gray-600">
          {formatDuration(toolCall.duration)}
        </span>
      </div>

      {/* Add full visualization here */}
    </div>
  );
};

export default ToolCallVisualizer;