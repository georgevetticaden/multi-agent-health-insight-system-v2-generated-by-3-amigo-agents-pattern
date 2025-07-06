import React, { useState } from 'react';
import { PanelLeftClose, Download, Share2, Maximize2, FileText } from 'lucide-react';
import CodeArtifact from './CodeArtifact';
import CompactQuerySelector, { Query } from './medical-team/CompactQuerySelector';

interface Visualization {
  id: string;
  title: string;
  code: string;
  timestamp: Date;
  threadId: string;
  queryId?: string;
  queryText?: string;
}

interface VisualizationPanelProps {
  visualizations: Visualization[];
  currentVizId: string;
  onVizChange: (vizId: string) => void;
  width: number;
  onClose: () => void;
  queries?: Query[];
  activeQueryId?: string;
  onQuerySelect?: (queryId: string) => void;
}

const VisualizationPanel: React.FC<VisualizationPanelProps> = ({
  visualizations,
  currentVizId,
  onVizChange,
  width,
  onClose,
  queries = [],
  activeQueryId = '',
  onQuerySelect
}) => {
  // Filter visualizations by active query
  const filteredVisualizations = visualizations.filter(viz => 
    !activeQueryId || !viz.queryId || viz.queryId === activeQueryId
  );
  
  // Find current viz from filtered list, or default to first one for the query
  let currentViz = filteredVisualizations.find(v => v.id === currentVizId);
  if (!currentViz && filteredVisualizations.length > 0) {
    currentViz = filteredVisualizations[filteredVisualizations.length - 1];
    // Update the parent component to use this viz
    onVizChange(currentViz.id);
  }
  
  const [showExportMenu, setShowExportMenu] = useState(false);

  const handleExport = (format: 'pdf' | 'png' | 'csv') => {
    console.log(`Exporting as ${format}...`);
    setShowExportMenu(false);
  };

  return (
    <div className="h-full bg-white/70 backdrop-blur-sm flex flex-col">
      <div className="bg-white/90 border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-medium text-gray-900">Health Visualizations</h2>
          <div className="flex items-center gap-2">
            {queries.length > 0 && onQuerySelect && (
              <CompactQuerySelector
                queries={queries}
                activeQueryId={activeQueryId}
                onQuerySelect={onQuerySelect}
              />
            )}
            <button className="p-1 hover:bg-gray-100 rounded transition-colors" title="Full screen">
              <Maximize2 className="w-4 h-4 text-gray-600" />
            </button>
            <div className="relative">
              <button 
                onClick={() => setShowExportMenu(!showExportMenu)}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
                title="Export"
              >
                <Download className="w-4 h-4 text-gray-600" />
              </button>
              {showExportMenu && (
                <div className="absolute right-0 mt-1 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
                  <button onClick={() => handleExport('pdf')} className="px-4 py-2 text-sm hover:bg-gray-50 w-full text-left">
                    Export as PDF
                  </button>
                  <button onClick={() => handleExport('png')} className="px-4 py-2 text-sm hover:bg-gray-50 w-full text-left">
                    Export as PNG
                  </button>
                  <button onClick={() => handleExport('csv')} className="px-4 py-2 text-sm hover:bg-gray-50 w-full text-left">
                    Export data as CSV
                  </button>
                </div>
              )}
            </div>
            <button className="p-1 hover:bg-gray-100 rounded transition-colors" title="Share">
              <Share2 className="w-4 h-4 text-gray-600" />
            </button>
            <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded transition-colors" title="Close panel">
              <PanelLeftClose className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>
        
        <div className="flex gap-2 overflow-x-auto pb-1">
          {filteredVisualizations.map((viz, idx) => (
            <button
              key={viz.id}
              onClick={() => onVizChange(viz.id)}
              className={`px-3 py-1.5 text-sm rounded-lg whitespace-nowrap transition-all ${
                viz.id === currentVizId 
                  ? 'bg-blue-50 text-blue-700 border border-blue-300 font-medium shadow-sm'
                  : 'bg-white hover:bg-gray-50 border border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <FileText className="w-3 h-3" />
                {viz.title || `Visualization ${idx + 1}`}
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto bg-gray-50/50">
        <div className="p-4">
          {currentViz ? (
            <div className="space-y-4">
              <div className="text-xs text-gray-500">
                Created {new Date(currentViz.timestamp).toLocaleString()}
              </div>
              <CodeArtifact code={currentViz.code} language="javascript" data={{}} />
            </div>
          ) : (
            <div className="text-center text-gray-500 mt-8">
              <p>No visualization selected</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VisualizationPanel;