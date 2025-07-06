import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, CheckCircle, Loader2, ChevronDown } from 'lucide-react';

export interface Query {
  id: string;
  question: string;
  timestamp: Date;
  status: 'analyzing' | 'complete';
  teamSize?: number;
}

interface CompactQuerySelectorProps {
  queries: Query[];
  activeQueryId: string;
  onQuerySelect: (queryId: string) => void;
}

const CompactQuerySelector: React.FC<CompactQuerySelectorProps> = ({
  queries,
  activeQueryId,
  onQuerySelect
}) => {
  const [showDropdown, setShowDropdown] = useState(false);
  
  // Show even for single query to maintain consistency

  const activeIndex = queries.findIndex(q => q.id === activeQueryId);
  const activeQuery = queries[activeIndex];
  
  const handlePrevious = () => {
    if (activeIndex > 0) {
      onQuerySelect(queries[activeIndex - 1].id);
    }
  };
  
  const handleNext = () => {
    if (activeIndex < queries.length - 1) {
      onQuerySelect(queries[activeIndex + 1].id);
    }
  };

  return (
    <div className="relative inline-flex items-center gap-2">
      {/* Navigation Arrows - only show if multiple queries */}
      {queries.length > 1 && (
        <button
          onClick={handlePrevious}
          disabled={activeIndex === 0}
          className={`p-1 rounded transition-colors ${
            activeIndex === 0 
              ? 'text-gray-300 cursor-not-allowed' 
              : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
          }`}
          title="Previous query"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
      )}
      
      {/* Query Indicator */}
      <div className="relative">
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className="flex items-center gap-2 px-3 py-1 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-2">
            {activeQuery?.status === 'complete' ? (
              <CheckCircle className="w-3.5 h-3.5 text-green-500" />
            ) : (
              <Loader2 className="w-3.5 h-3.5 text-blue-500 animate-spin" />
            )}
            <span className="font-medium">
              {queries.length === 1 ? 'Query 1' : `Query ${activeIndex + 1} of ${queries.length}`}
            </span>
          </div>
          <ChevronDown className={`w-3.5 h-3.5 text-gray-500 transition-transform ${showDropdown ? 'rotate-180' : ''}`} />
        </button>
        
        {/* Dropdown Menu */}
        {showDropdown && (
          <>
            <div 
              className="fixed inset-0 z-10" 
              onClick={() => setShowDropdown(false)}
            />
            <div className="absolute top-full right-0 mt-1 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-20 max-h-60 overflow-y-auto">
              {queries.map((query, index) => (
                <button
                  key={query.id}
                  onClick={() => {
                    onQuerySelect(query.id);
                    setShowDropdown(false);
                  }}
                  className={`w-full px-3 py-2 text-left hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-0 ${
                    query.id === activeQueryId ? 'bg-blue-50' : ''
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <div className="flex-shrink-0 mt-0.5">
                      {query.status === 'complete' ? (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      ) : (
                        <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-gray-700">Query {index + 1}</span>
                        <span className="text-xs text-gray-500">
                          {new Date(query.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <p className="text-xs text-gray-600 text-left" title={query.question}>
                        {query.question}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </>
        )}
      </div>
      
      {/* Next Arrow - only show if multiple queries */}
      {queries.length > 1 && (
        <button
          onClick={handleNext}
          disabled={activeIndex === queries.length - 1}
          className={`p-1 rounded transition-colors ${
            activeIndex === queries.length - 1 
              ? 'text-gray-300 cursor-not-allowed' 
              : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
          }`}
          title="Next query"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      )}
      
    </div>
  );
};

export default CompactQuerySelector;