import React from 'react';
import { Brain } from 'lucide-react';

interface ThinkingIndicatorProps {
  content?: string;
}

const ThinkingIndicator: React.FC<ThinkingIndicatorProps> = ({ content }) => {
  return (
    <div className="flex gap-3 justify-start">
      <div className="flex-shrink-0 w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
        <Brain className="w-5 h-5 text-purple-600 animate-pulse" />
      </div>
      
      <div className="bg-purple-50 border border-purple-200 rounded-lg px-4 py-3 max-w-3xl">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-sm font-medium text-purple-700">Extended Thinking</span>
          <div className="flex gap-1">
            <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse" />
            <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
            <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
          </div>
        </div>
        
        {content && (
          <div className="text-sm text-purple-600 italic max-h-32 overflow-y-auto">
            {content}
          </div>
        )}
      </div>
    </div>
  );
};

export default ThinkingIndicator;