import React, { useState, useEffect, useRef } from 'react';
import MedicalTeamOrgChart from './MedicalTeamOrgChart';
import StreamingAnalysis from './StreamingAnalysis';
import CompactQuerySelector, { Query } from './CompactQuerySelector';
import { TeamUpdate, TeamMember } from '../../types/medical-team';
import { Loader2, Brain, Heart, FlaskConical, Activity, BarChart3, Shield, Pill, Apple, GripVertical, Stethoscope } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';

const iconMap: { [key: string]: React.ComponentType<any> } = {
  Brain, Heart, FlaskConical, Activity, BarChart3, Shield, Pill, Apple, Stethoscope
};

interface MedicalTeamTabProps {
  teamUpdate?: TeamUpdate;
  streamingContent?: string[];
  onAgentClick?: (agentId: string) => void;
  isVisible?: boolean;
  currentQuery?: string;
  onQueryChange?: (queryId: string, queryText: string) => void;
  onQueryCreated?: (query: Query) => void;
  externalQueries?: Query[];
  externalActiveQueryId?: string;
}

interface QueryData {
  teamUpdate: TeamUpdate;
  completedAnalyses: Array<{ agentId: string; summary: string; }>;
  agentStreamingContent: { [key: string]: string[] };
}

const MedicalTeamTab: React.FC<MedicalTeamTabProps> = ({
  teamUpdate,
  streamingContent = [],
  onAgentClick,
  isVisible = true,
  currentQuery,
  onQueryChange,
  onQueryCreated,
  externalQueries = [],
  externalActiveQueryId
}) => {
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [agentStreamingContent, setAgentStreamingContent] = useState<{ [key: string]: string[] }>({});
  const prevTeamUpdateRef = useRef<TeamUpdate | undefined>();
  
  // Query management state
  const [queries, setQueries] = useState<Query[]>([]);
  const [activeQueryId, setActiveQueryId] = useState<string>('');
  const [queryDataMap, setQueryDataMap] = useState<{ [queryId: string]: QueryData }>({});
  
  const [completedAnalyses, setCompletedAnalyses] = useState<Array<{
    agentId: string;
    summary: string;
  }>>([]);
  const [processedCompletions, setProcessedCompletions] = useState<Set<string>>(new Set());

  // Resizable divider state
  const [topSectionHeight, setTopSectionHeight] = useState(50); // percentage
  const [isResizing, setIsResizing] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Track when a new query starts
  const [isProcessingQuery, setIsProcessingQuery] = useState(false);
  const processedQueryRef = useRef<string>('');
  const lastActiveQueryRef = useRef<string>('');
  
  // Sync with external queries from TwoPanelLayout
  useEffect(() => {
    if (externalQueries && externalQueries.length > 0) {
      setQueries(externalQueries);
      // Only auto-set active query if we don't have one yet, or if it's a brand new query
      if (!activeQueryId) {
        const latestQuery = externalQueries[externalQueries.length - 1];
        if (latestQuery) {
          setActiveQueryId(latestQuery.id);
          lastActiveQueryRef.current = latestQuery.id;
        }
      } else {
        // Check if current activeQueryId still exists in external queries
        const currentQueryExists = externalQueries.some(q => q.id === activeQueryId);
        if (!currentQueryExists && externalQueries.length > 0) {
          // If current query doesn't exist, default to latest
          const latestQuery = externalQueries[externalQueries.length - 1];
          setActiveQueryId(latestQuery.id);
          lastActiveQueryRef.current = latestQuery.id;
        }
      }
    }
  }, [externalQueries]);
  
  // Sync active query ID from parent
  useEffect(() => {
    if (externalActiveQueryId && externalActiveQueryId !== activeQueryId) {
      setActiveQueryId(externalActiveQueryId);
      lastActiveQueryRef.current = externalActiveQueryId;
      
      // Load data for this query if it exists
      if (queryDataMap[externalActiveQueryId]) {
        const savedData = queryDataMap[externalActiveQueryId];
        setCompletedAnalyses(savedData.completedAnalyses);
        setAgentStreamingContent(savedData.agentStreamingContent);
        setProcessedCompletions(new Set(savedData.completedAnalyses.map(a => a.agentId)));
      } else {
        // Clear data if switching to a query without saved data
        setCompletedAnalyses([]);
        setAgentStreamingContent({});
        setProcessedCompletions(new Set());
      }
    }
  }, [externalActiveQueryId, queryDataMap]);
  
  // Reset queries when conversation changes (detected by no teamUpdate)
  useEffect(() => {
    if (!teamUpdate && !currentQuery && externalQueries.length === 0) {
      setQueries([]);
      setActiveQueryId('');
      setQueryDataMap({});
      processedQueryRef.current = '';
      setIsProcessingQuery(false);
      lastActiveQueryRef.current = '';
    }
  }, [teamUpdate, currentQuery, externalQueries]);
  
  useEffect(() => {
    if (currentQuery && teamUpdate && !isProcessingQuery) {
      const cmo = teamUpdate.members.find(m => m.id === 'cmo');
      
      // Check if this is a new query starting (CMO beginning to think)
      if (cmo && cmo.status === 'thinking' && currentQuery !== processedQueryRef.current) {
        // Set processing flag to prevent duplicate processing
        setIsProcessingQuery(true);
        
        // Check if we already have this query
        const existingQuery = queries.find(q => q.question === currentQuery);
        
        if (!existingQuery) {
          const newQueryId = uuidv4();
          const newQuery: Query = {
            id: newQueryId,
            question: currentQuery,
            timestamp: new Date(),
            status: 'analyzing',
            teamSize: teamUpdate.members.filter(m => m.id !== 'cmo').length
          };
          
          console.log('Creating new query:', newQuery);
          
          // Use single source of truth for queries
          if (onQueryCreated) {
            onQueryCreated(newQuery);
          }
          
          setQueries(prev => {
            // Double-check to prevent duplicates
            const alreadyExists = prev.some(q => q.question === currentQuery);
            if (alreadyExists) {
              console.log('Query already exists, skipping creation');
              return prev;
            }
            return [...prev, newQuery];
          });
          
          setActiveQueryId(newQueryId);
          processedQueryRef.current = currentQuery;
          lastActiveQueryRef.current = newQueryId;
          
          // Reset state for new query
          setCompletedAnalyses([]);
          setProcessedCompletions(new Set());
          setAgentStreamingContent({});
          setSelectedAgentId(null);
        } else {
          // If query exists, just set it as active
          setActiveQueryId(existingQuery.id);
          processedQueryRef.current = currentQuery;
          lastActiveQueryRef.current = existingQuery.id;
        }
        
        // Reset processing flag after a delay
        setTimeout(() => setIsProcessingQuery(false), 1000);
      }
    }
  }, [currentQuery, teamUpdate, isProcessingQuery, queries]);

  // Save current query data
  useEffect(() => {
    if (activeQueryId && teamUpdate) {
      setQueryDataMap(prev => ({
        ...prev,
        [activeQueryId]: {
          teamUpdate,
          completedAnalyses,
          agentStreamingContent
        }
      }));
      
      // Update query status if team is complete
      if (teamUpdate.teamStatus === 'complete') {
        console.log('🔍 [TRACE DEBUGGING] MedicalTeamTab - Team complete, updating query status');
        console.log('🔍 [TRACE DEBUGGING] MedicalTeamTab - Team update has traceId:', teamUpdate.traceId);
        console.log('🔍 [TRACE DEBUGGING] MedicalTeamTab - activeQueryId:', activeQueryId);
        console.log('🔍 [TRACE DEBUGGING] MedicalTeamTab - Full teamUpdate:', teamUpdate);
        setQueries(prev => prev.map(q => 
          q.id === activeQueryId ? { ...q, status: 'complete' } : q
        ));
      }
    }
  }, [activeQueryId, teamUpdate, completedAnalyses, agentStreamingContent]);

  // Get data for display based on active query
  const displayData = activeQueryId && queryDataMap[activeQueryId] 
    ? queryDataMap[activeQueryId] 
    : { 
        teamUpdate: activeQueryId === lastActiveQueryRef.current ? teamUpdate : undefined, 
        completedAnalyses: activeQueryId === lastActiveQueryRef.current ? completedAnalyses : [], 
        agentStreamingContent: activeQueryId === lastActiveQueryRef.current ? agentStreamingContent : {} 
      };
      
  // Debug logging
  console.log('🔍 [TRACE DEBUGGING] MedicalTeamTab - Display data:', {
    activeQueryId,
    teamStatus: displayData.teamUpdate?.teamStatus,
    traceId: displayData.teamUpdate?.traceId,
    showTraceLink: displayData.teamUpdate?.teamStatus === 'complete' && displayData.teamUpdate?.traceId,
    fullDisplayData: displayData,
    queryDataMap: queryDataMap,
    currentTeamUpdate: teamUpdate
  });

  // Find active agent from display data
  const activeAgent = displayData.teamUpdate?.members.find(
    (m: TeamMember) => m.status === 'analyzing' || m.status === 'thinking'
  );

  // Update streaming content for active agent
  useEffect(() => {
    if (activeAgent && streamingContent.length > 0) {
      // Add each new content item for the active agent
      streamingContent.forEach(content => {
        if (content && content.trim()) {
          setAgentStreamingContent(prev => {
            const existingContent = prev[activeAgent.id] || [];
            // Only add if it's not the last item (to avoid duplicates)
            const lastItem = existingContent[existingContent.length - 1];
            if (lastItem !== content) {
              return {
                ...prev,
                [activeAgent.id]: [...existingContent, content]
              };
            }
            return prev;
          });
        }
      });
    }
  }, [activeAgent, streamingContent]);

  // Handle agent completion
  useEffect(() => {
    if (!teamUpdate) return;

    teamUpdate.members.forEach(member => {
      if (member.status === 'complete' && member.message && !processedCompletions.has(member.id)) {
        setCompletedAnalyses(prev => [...prev, {
          agentId: member.id,
          summary: member.message
        }]);
        setProcessedCompletions(prev => new Set([...prev, member.id]));
      }
    });
  }, [teamUpdate, processedCompletions]);

  // Auto-select active agent
  useEffect(() => {
    if (activeAgent) {
      setSelectedAgentId(activeAgent.id);
    }
  }, [activeAgent]);

  const handleAgentClick = (agentId: string) => {
    setSelectedAgentId(agentId);
    onAgentClick?.(agentId);
  };

  const getAgentIcon = (agent?: TeamMember) => {
    if (!agent || !agent.icon) return Brain;
    return iconMap[agent.icon] || Brain;
  };

  // Get streaming content for selected or active agent
  const displayAgent = selectedAgentId 
    ? displayData.teamUpdate?.members.find(m => m.id === selectedAgentId)
    : activeAgent;

  const displayStreamingContent = displayAgent 
    ? displayData.agentStreamingContent[displayAgent.id] || []
    : [];
    
  const handleQuerySelect = (queryId: string) => {
    setActiveQueryId(queryId);
    // Reset selections when switching queries
    setSelectedAgentId(null);
    
    // Load saved data for this query or reset if no data
    if (!queryDataMap[queryId]) {
      // If switching to a query without saved data, clear current data
      setCompletedAnalyses([]);
      setAgentStreamingContent({});
      setProcessedCompletions(new Set());
    } else {
      // Load saved data
      const savedData = queryDataMap[queryId];
      setCompletedAnalyses(savedData.completedAnalyses);
      setAgentStreamingContent(savedData.agentStreamingContent);
      // Rebuild processed completions set
      setProcessedCompletions(new Set(savedData.completedAnalyses.map(a => a.agentId)));
    }
    
    // Notify parent to scroll to query in conversation
    const query = queries.find(q => q.id === queryId);
    if (query && onQueryChange) {
      onQueryChange(queryId, query.question);
    }
  };

  // Handle resize
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing || !containerRef.current) return;
      
      const containerRect = containerRef.current.getBoundingClientRect();
      const newHeight = ((e.clientY - containerRect.top) / containerRect.height) * 100;
      
      // Limit between 20% and 80%
      setTopSectionHeight(Math.min(80, Math.max(20, newHeight)));
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  return (
    <div ref={containerRef} className="flex flex-col h-full bg-gray-50">
      {/* Section 1: Medical Team Hierarchy with Status (Scrollable) */}
      <div 
        className="flex-shrink-0 overflow-y-auto"
        style={{ height: `${topSectionHeight}%` }}
      >
        {/* Section Header with Integrated Query Selector */}
        <div className="px-4 pt-4 pb-2 sticky top-0 bg-gray-50 z-10">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">Team Hierarchy & Status</h3>
            {queries.length > 0 && (
              <CompactQuerySelector
                queries={queries}
                activeQueryId={activeQueryId}
                onQuerySelect={handleQuerySelect}
              />
            )}
          </div>
        </div>
        
        {/* Org Chart */}
        <div className="px-4 pb-4">
          <MedicalTeamOrgChart
            teamMembers={displayData.teamUpdate?.members || []}
            onAgentClick={handleAgentClick}
            key={`${isVisible ? 'visible' : 'hidden'}-${activeQueryId}`} // Force re-render when visibility or query changes
          />
        </div>

        {/* Active Agent Status Bar with Overall Progress */}
        {displayAgent && (displayAgent.status === 'analyzing' || displayAgent.status === 'thinking') && (
          <div className="mx-4 mb-4">
            <div className="bg-gradient-to-r from-blue-50 to-blue-100 px-4 py-3 rounded-lg border border-blue-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {React.createElement(getAgentIcon(displayAgent), {
                    className: "w-5 h-5 text-blue-600"
                  })}
                  <h3 className="font-semibold text-blue-900">
                    {displayAgent.name} - {displayAgent.specialty}
                  </h3>
                  <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
                </div>
                <div className="flex items-center gap-4">
                  {displayAgent.progress !== undefined && (
                    <span className="text-sm text-blue-700">
                      Agent: {displayAgent.progress}%
                    </span>
                  )}
                  {displayData.teamUpdate && (
                    <span className="text-sm text-blue-800 font-medium">
                      Overall: {displayData.teamUpdate.overallProgress}%
                    </span>
                  )}
                </div>
              </div>
              
              {/* Current Task Display */}
              {displayAgent.currentTask && (
                <div className="mt-2 text-sm text-blue-700">
                  <span className="font-medium">Current task:</span> {displayAgent.currentTask}
                </div>
              )}
              
              {/* Dual Progress Bars */}
              <div className="mt-3 space-y-1">
                {/* Agent Progress */}
                {displayAgent.progress !== undefined && (
                  <div>
                    <div className="flex items-center justify-between text-xs text-blue-600 mb-1">
                      <span>Agent Progress</span>
                      <span>{displayAgent.progress}%</span>
                    </div>
                    <div className="w-full bg-blue-200/50 rounded-full h-1.5 overflow-hidden">
                      <div 
                        className="bg-blue-600 h-full transition-all duration-500 ease-out"
                        style={{ width: `${displayAgent.progress}%` }}
                      />
                    </div>
                  </div>
                )}
                
                {/* Overall Team Progress */}
                {displayData.teamUpdate && (
                  <div>
                    <div className="flex items-center justify-between text-xs text-blue-600 mb-1">
                      <span>Overall Team Progress</span>
                      <span>{displayData.teamUpdate.overallProgress}%</span>
                    </div>
                    <div className="w-full bg-green-200/50 rounded-full h-1.5 overflow-hidden">
                      <div 
                        className="bg-green-600 h-full transition-all duration-500 ease-out"
                        style={{ width: `${displayData.teamUpdate.overallProgress}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Movable Divider */}
      <div 
        className={`relative h-2 bg-gray-300 hover:bg-gray-400 cursor-row-resize flex items-center justify-center ${
          isResizing ? 'bg-blue-500' : ''
        }`}
        onMouseDown={handleMouseDown}
      >
        <GripVertical className="w-4 h-4 text-gray-600 rotate-90" />
      </div>

      {/* Section 2: Completed Analyses (Scrollable) */}
      <div 
        className="flex-1 min-h-0 flex flex-col overflow-y-auto"
        style={{ height: `${100 - topSectionHeight}%` }}
      >
        {/* Section Header */}
        <div className="px-4 pt-4 pb-2 sticky top-0 bg-gray-50 z-10">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">Analysis Results</h3>
            {(() => {
              const shouldShowTrace = displayData.teamUpdate?.teamStatus === 'complete' && displayData.teamUpdate?.traceId;
              console.log('🔍 [TRACE DEBUGGING] Trace button check:', {
                teamStatus: displayData.teamUpdate?.teamStatus,
                traceId: displayData.teamUpdate?.traceId,
                shouldShowTrace: shouldShowTrace
              });
              
              return shouldShowTrace ? (
                <button
                  onClick={() => {
                    const url = `/test-case-management/${displayData.teamUpdate.traceId}`;
                    console.log('🔍 [TRACE DEBUGGING] Opening test case management dashboard:', url);
                    window.open(url, '_blank');
                  }}
                  className="text-sm px-3 py-1 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-md transition-colors flex items-center gap-1"
                  title="Create and manage test cases for this health query"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                  Create Test Case
                </button>
              ) : null;
            })()}
          </div>
        </div>
        
        {/* Scrollable Content */}
        <div className="px-4 pb-4">
          <StreamingAnalysis
            activeAgent={displayAgent}
            streamingContent={displayStreamingContent}
            completedAnalyses={displayData.completedAnalyses}
            teamMembers={displayData.teamUpdate?.members || []}
          />
        </div>
      </div>
    </div>
  );
};

export default MedicalTeamTab;