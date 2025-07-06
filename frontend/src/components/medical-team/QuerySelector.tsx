import React from 'react';
import { Clock, CheckCircle, Loader2 } from 'lucide-react';

export interface Query {
  id: string;
  question: string;
  timestamp: Date;
  status: 'analyzing' | 'complete';
  teamSize?: number;
}

interface QuerySelectorProps {
  queries: Query[];
  activeQueryId: string;
  onQuerySelect: (queryId: string) => void;
}

const QuerySelector: React.FC<QuerySelectorProps> = ({
  queries,
  activeQueryId,
  onQuerySelect
}) => {
  if (queries.length <= 1) {
    return null; // Don't show selector if only one query
  }

  return (
    <div className="bg-white border-b border-gray-200 px-4 py-3">
      <div className="flex items-center gap-2 mb-2">
        <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wider">Query History</h4>
        <span className="text-xs text-gray-500">({queries.length} queries in this conversation)</span>
      </div>
      
      <div className="flex gap-2 overflow-x-auto pb-2">
        {queries.map((query, index) => (
          <button
            key={query.id}
            onClick={() => onQuerySelect(query.id)}
            className={`
              flex-shrink-0 px-3 py-2 rounded-lg border transition-all duration-200
              ${activeQueryId === query.id 
                ? 'bg-blue-50 border-blue-300 shadow-sm' 
                : 'bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm'
              }
            `}
          >
            <div className="flex items-start gap-2">
              <div className="flex-shrink-0 mt-0.5">
                {query.status === 'complete' ? (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                ) : (
                  <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                )}
              </div>
              
              <div className="text-left">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-gray-700">Query {index + 1}</span>
                  {query.teamSize && (
                    <span className="text-xs text-gray-500">• {query.teamSize} specialists</span>
                  )}
                </div>
                <p className="text-xs text-gray-600 line-clamp-2 max-w-[200px]">
                  {query.question}
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <Clock className="w-3 h-3 text-gray-400" />
                  <span className="text-xs text-gray-500">
                    {new Date(query.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default QuerySelector;