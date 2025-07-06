import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Loader2, CheckCircle, AlertCircle, Code } from 'lucide-react';

interface ToolCallEnvelopeProps {
  toolName: string;
  toolInput?: any;
  toolResult?: any;
  status: 'calling' | 'executing' | 'completed' | 'error';
  error?: string;
}

const ToolCallEnvelope: React.FC<ToolCallEnvelopeProps> = ({
  toolName,
  toolInput,
  toolResult,
  status,
  error
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getStatusIcon = () => {
    switch (status) {
      case 'calling':
      case 'executing':
        return <Loader2 className="w-5 h-5 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5" />;
      case 'error':
        return <AlertCircle className="w-5 h-5" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'calling':
      case 'executing':
        return 'bg-blue-50 border-blue-200 text-blue-700';
      case 'completed':
        return 'bg-green-50 border-green-200 text-green-700';
      case 'error':
        return 'bg-red-50 border-red-200 text-red-700';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'calling':
        return `Calling ${toolName}...`;
      case 'executing':
        return `Executing ${toolName} - querying health database...`;
      case 'completed':
        return `${toolName} completed`;
      case 'error':
        return `${toolName} failed`;
    }
  };

  return (
    <div className={`my-2 rounded-lg border ${getStatusColor()} transition-all duration-200`}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-opacity-70 transition-colors"
      >
        <div className="flex items-center gap-3">
          {getStatusIcon()}
          <span className="font-medium">{getStatusText()}</span>
        </div>
        <div className="flex items-center gap-2">
          <Code className="w-4 h-4 opacity-50" />
          {isExpanded ? (
            <ChevronUp className="w-5 h-5" />
          ) : (
            <ChevronDown className="w-5 h-5" />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="border-t border-current border-opacity-20 p-4 space-y-3">
          {/* Tool Input */}
          {toolInput && (
            <div>
              <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
                <span>📥 Input Parameters</span>
              </h4>
              <pre className="bg-white bg-opacity-50 p-3 rounded text-xs overflow-x-auto">
                {JSON.stringify(toolInput, null, 2)}
              </pre>
            </div>
          )}

          {/* Tool Result */}
          {toolResult && status === 'completed' && (
            <div>
              <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
                <span>📤 Result</span>
              </h4>
              <pre className="bg-white bg-opacity-50 p-3 rounded text-xs overflow-x-auto max-h-60 overflow-y-auto">
                {typeof toolResult === 'object' 
                  ? JSON.stringify(toolResult, null, 2) 
                  : String(toolResult)}
              </pre>
            </div>
          )}

          {/* Error Message */}
          {error && status === 'error' && (
            <div>
              <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
                <span>❌ Error</span>
              </h4>
              <div className="bg-white bg-opacity-50 p-3 rounded text-sm">
                {error}
              </div>
            </div>
          )}

          {/* Status Message */}
          {status === 'executing' && (
            <div className="text-sm opacity-70 italic">
              Querying health database...
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ToolCallEnvelope;