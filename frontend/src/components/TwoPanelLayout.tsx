import React, { useState, useRef, useEffect } from 'react';
import ChatInterface from './ChatInterface';
import CodeArtifact from './CodeArtifact';
import EnhancedHeader from './EnhancedHeader';
import ThreadSidebar, { HealthThread } from './ThreadSidebar';
import WelcomeState from './WelcomeState';
import VisualizationPanel from './VisualizationPanel';
import TabContainer from './TabContainer';
import MedicalTeamTab from './medical-team/MedicalTeamTab';
import { AppState, TeamUpdate } from '../types/medical-team';
import { PanelLeftClose, PanelLeftOpen, GripVertical } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';
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

interface ConversationVisualizations {
  [threadId: string]: {
    current: string;
    items: Visualization[];
  };
}

const TwoPanelLayout: React.FC = () => {
  // State management
  const [appState, setAppState] = useState<AppState>(() => {
    const savedThreads = localStorage.getItem('healthThreads');
    return savedThreads ? 'idle' : 'welcome';
  });

  const [threads, setThreads] = useState<HealthThread[]>(() => {
    const saved = localStorage.getItem('healthThreads');
    return saved ? JSON.parse(saved) : [];
  });

  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [teamUpdate, setTeamUpdate] = useState<TeamUpdate | undefined>();
  const [vizHistory, setVizHistory] = useState<ConversationVisualizations>(() => {
    const saved = localStorage.getItem('vizHistory');
    return saved ? JSON.parse(saved) : {};
  });
  const [isPanelOpen, setIsPanelOpen] = useState(true);
  const [panelWidth, setPanelWidth] = useState(45);
  const [isResizing, setIsResizing] = useState(false);
  const [artifactsMap, setArtifactsMap] = useState<Map<string, any>>(new Map());
  const [currentArtifactId, setCurrentArtifactId] = useState<string | null>(null);
  const [isStreamingCode, setIsStreamingCode] = useState(false);
  const [streamingContent, setStreamingContent] = useState<string[]>([]);
  const [lastStreamingContent, setLastStreamingContent] = useState<string>('');
  const [activeRightTab, setActiveRightTab] = useState<string>('medical-team');
  const [currentQuery, setCurrentQuery] = useState<string>('');
  const [scrollToQuery, setScrollToQuery] = useState<string>('');
  const [threadQueries, setThreadQueries] = useState<Map<string, Query[]>>(new Map());
  const [activeQueryId, setActiveQueryId] = useState<string>('');
  
  const containerRef = useRef<HTMLDivElement>(null);
  const chatInterfaceRef = useRef<any>(null);

  // Save threads to localStorage
  useEffect(() => {
    if (threads.length > 0) {
      localStorage.setItem('healthThreads', JSON.stringify(threads));
    }
  }, [threads]);

  // Save visualization history to localStorage
  useEffect(() => {
    localStorage.setItem('vizHistory', JSON.stringify(vizHistory));
  }, [vizHistory]);
  
  // Debug teamUpdate state changes
  useEffect(() => {
    console.log('🔍 [TRACE DEBUGGING] teamUpdate state changed:', teamUpdate);
  }, [teamUpdate]);
  
  // Debug isStreamingCode state changes
  useEffect(() => {
    console.log('🔍 [TRACE DEBUGGING] isStreamingCode state changed:', isStreamingCode);
  }, [isStreamingCode]);
  
  // Debug panel visibility conditions
  useEffect(() => {
    const shouldShowPanel = isPanelOpen && activeThreadId && (teamUpdate || isStreamingCode || currentArtifactId || vizHistory[activeThreadId]?.items?.length > 0);
    console.log('🔍 [TRACE DEBUGGING] Panel visibility check:', {
      shouldShowPanel,
      isPanelOpen,
      activeThreadId,
      hasTeamUpdate: !!teamUpdate,
      teamUpdateValue: teamUpdate,
      isStreamingCode,
      currentArtifactId,
      vizHistoryLength: activeThreadId ? vizHistory[activeThreadId]?.items?.length || 0 : 0,
      vizHistoryForThread: activeThreadId ? vizHistory[activeThreadId] : null
    });
  }, [isPanelOpen, activeThreadId, teamUpdate, isStreamingCode, currentArtifactId, vizHistory]);
  
  // Handle pending question after component mounts
  useEffect(() => {
    if (activeThreadId) {
      const pendingQuestion = localStorage.getItem('pendingQuestion');
      if (pendingQuestion) {
        // Check for chatInterfaceRef periodically
        const checkInterval = setInterval(() => {
          if (chatInterfaceRef.current) {
            clearInterval(checkInterval);
            localStorage.removeItem('pendingQuestion');
            // Small delay to ensure the interface is ready
            setTimeout(() => {
              console.log('Sending pending question:', pendingQuestion);
              chatInterfaceRef.current?.sendMessage(pendingQuestion);
            }, 1000);
          }
        }, 100);
        
        // Clear interval after 5 seconds if ref never becomes available
        setTimeout(() => clearInterval(checkInterval), 5000);
      }
    }
  }, [activeThreadId]);

  // Handle first conversation
  const handleStartFirstConversation = (question?: string) => {
    setAppState('idle'); // Start in idle state so user can see their message
    const newThread = createNewThread(question);
    setThreads([newThread]);
    setActiveThreadId(newThread.id);
    
    // Store the question to send after component mounts
    if (question) {
      localStorage.setItem('pendingQuestion', question);
    }
  };

  // Create new thread
  const createNewThread = (initialQuestion?: string): HealthThread => {
    const category = categorizeHealthQuery(initialQuestion || '');
    return {
      id: uuidv4(),
      title: initialQuestion ? generateThreadTitle(initialQuestion) : 'New Health Conversation',
      summary: initialQuestion || 'Start a new health query...',
      timestamp: new Date(),
      category
    };
  };

  const handleNewThread = () => {
    const newThread = createNewThread();
    setThreads(prev => [newThread, ...prev]);
    setActiveThreadId(newThread.id);
    setAppState('idle');
    setTeamUpdate(undefined);
    setStreamingContent([]);
    setCurrentQuery('');
  };

  const handleThreadSelect = (id: string) => {
    setActiveThreadId(id);
    setAppState('idle');
    // Reset current query when switching threads
    setCurrentQuery('');
    // Reset active query when switching threads
    const queries = threadQueries.get(id) || [];
    if (queries.length > 0) {
      setActiveQueryId(queries[queries.length - 1].id);
    } else {
      setActiveQueryId('');
    }
    // Mark as read
    setThreads(prev => prev.map(thread => 
      thread.id === id ? { ...thread, unread: false } : thread
    ));
  };

  // Handle app state changes from ChatInterface
  const handleAppStateChange = (state: AppState) => {
    setAppState(state);
    
    // Auto-open panel when CMO starts analyzing
    if ((state === 'cmo-analyzing' || state === 'team-assembling' || state === 'team-working') && !isPanelOpen) {
      setIsPanelOpen(true);
    }
  };

  // Handle team updates from ChatInterface
  const handleTeamUpdate = (update: TeamUpdate) => {
    console.log('🔍 [TRACE DEBUGGING] TwoPanelLayout received team update:', update);
    console.log('🔍 [TRACE DEBUGGING] Update has traceId:', update.traceId);
    console.log('🔍 [TRACE DEBUGGING] Update members length:', update.members.length);
    console.log('🔍 [TRACE DEBUGGING] Current teamUpdate state:', teamUpdate);
    
    // If this update only contains traceId, we need to preserve existing team state
    if (update.traceId && update.members.length === 0) {
      console.log('🔍 [TRACE DEBUGGING] Update contains only traceId, need to preserve team state');
      
      // Get the latest team update from state
      setTeamUpdate(prev => {
        console.log('🔍 [TRACE DEBUGGING] Previous teamUpdate in setter:', prev);
        if (prev) {
          console.log('🔍 [TRACE DEBUGGING] Merging traceId with existing team update');
          const mergedUpdate = {
            ...prev,
            traceId: update.traceId
          };
          console.log('🔍 [TRACE DEBUGGING] Merged team update:', mergedUpdate);
          return mergedUpdate;
        } else {
          console.log('🔍 [TRACE DEBUGGING] No previous team update to merge with, using update as-is');
          return update;
        }
      });
    } else {
      console.log('🔍 [TRACE DEBUGGING] Setting new team update (not merging)');
      console.log('🔍 [TRACE DEBUGGING] New update value:', update);
      setTeamUpdate(update);
    }
    
    // Auto-switch to Medical Team tab when team activity starts
    if (update.teamStatus !== 'complete' && activeRightTab !== 'medical-team') {
      setActiveRightTab('medical-team');
    }
    
    // Track queries - delegate to MedicalTeamTab to prevent duplicates
    // MedicalTeamTab will handle query creation when CMO starts analyzing
  };
  
  // Handle streaming content updates
  const handleStreamingContent = (content: string) => {
    setStreamingContent(prev => [...prev, content]);
    setLastStreamingContent(content);
  };

  // Update thread title based on query
  const updateThreadTitle = (threadId: string, newTitle: string) => {
    setThreads(prev => prev.map(thread => 
      thread.id === threadId ? { ...thread, title: newTitle } : thread
    ));
  };

  // Helper functions
  const categorizeHealthQuery = (query: string): HealthThread['category'] => {
    const lowerQuery = query.toLowerCase();
    if (lowerQuery.includes('lab') || lowerQuery.includes('test') || lowerQuery.includes('result')) {
      return 'lab';
    }
    if (lowerQuery.includes('medication') || lowerQuery.includes('drug') || lowerQuery.includes('prescription')) {
      return 'medication';
    }
    if (lowerQuery.includes('condition') || lowerQuery.includes('diagnosis') || lowerQuery.includes('disease')) {
      return 'condition';
    }
    return 'general';
  };

  const generateThreadTitle = (query: string): string => {
    const medicalTopics = {
      cholesterol: ['cholesterol', 'ldl', 'hdl', 'lipid', 'triglycerides'],
      diabetes: ['hba1c', 'glucose', 'diabetes', 'metformin', 'insulin'],
      cardiac: ['heart', 'cardiac', 'blood pressure', 'hypertension'],
      labs: ['lab', 'results', 'abnormal', 'test']
    };

    const lowerQuery = query.toLowerCase();
    for (const [topic, keywords] of Object.entries(medicalTopics)) {
      if (keywords.some(keyword => lowerQuery.includes(keyword))) {
        return `${topic.charAt(0).toUpperCase() + topic.slice(1)} Analysis`;
      }
    }

    // Extract key terms for title
    const words = query.split(' ').filter(word => word.length > 4);
    if (words.length > 0) {
      return words.slice(0, 3).join(' ') + ' Analysis';
    }

    return `Health Query - ${new Date().toLocaleDateString()}`;
  };

  const generateVisualizationTitle = (artifact: any): string => {
    // Try to extract title from the code
    const titleMatch = artifact.code.match(/title[:\s]+["']([^"']+)["']/);
    if (titleMatch) {
      return titleMatch[1];
    }
    
    // Generate based on content
    if (artifact.code.includes('LineChart')) return 'Trend Analysis';
    if (artifact.code.includes('BarChart')) return 'Comparison Chart';
    if (artifact.code.includes('PieChart')) return 'Distribution Analysis';
    
    return 'Health Visualization';
  };

  // Artifact handling
  const artifacts = Array.from(artifactsMap.values());
  const currentArtifact = currentArtifactId ? artifactsMap.get(currentArtifactId) : null;

  const handleNewArtifact = (artifact: any) => {
    if (!activeThreadId) return;

    // Update artifact map
    setArtifactsMap(prev => {
      const newMap = new Map(prev);
      newMap.set(artifact.id, artifact);
      return newMap;
    });
    setCurrentArtifactId(artifact.id);
    setIsPanelOpen(true);
    
    // Handle streaming
    if (artifact.isStreaming) {
      setIsStreamingCode(true);
    } else {
      if (artifact.id === currentArtifactId) {
        setTimeout(() => setIsStreamingCode(false), 500);
      }
      
      // Add to visualization history when complete
      const viz: Visualization = {
        id: artifact.id,
        title: generateVisualizationTitle(artifact),
        code: artifact.code,
        timestamp: new Date(),
        threadId: activeThreadId,
        queryId: activeQueryId,
        queryText: currentQuery
      };

      setVizHistory(prev => ({
        ...prev,
        [activeThreadId]: {
          current: viz.id,
          items: [...(prev[activeThreadId]?.items || []), viz]
        }
      }));

      setAppState('visualizing');
      // Auto-switch to visualization tab when visualization is ready
      setActiveRightTab('visualization');
      setTimeout(() => setAppState('complete'), 2000);
    }
  };

  const handleCodeStreamStart = () => {
    console.log('🔍 [TRACE DEBUGGING] handleCodeStreamStart called');
    setIsStreamingCode(true);
    setIsPanelOpen(true);
    // Auto-switch to visualization tab when code streaming starts
    setActiveRightTab('visualization');
    console.log('🔍 [TRACE DEBUGGING] Panel visibility conditions:', {
      isPanelOpen: true,
      activeThreadId,
      teamUpdate,
      isStreamingCode: true,
      currentArtifactId,
      vizHistoryLength: vizHistory[activeThreadId]?.items.length || 0
    });
  };

  const handleMessageSend = (message: string) => {
    if (!activeThreadId) return;
    
    // Track current query for medical team tab
    setCurrentQuery(message);
    
    // Don't create duplicate queries - let MedicalTeamTab handle query creation
    // This prevents duplicate queries being created
    
    // Update thread title if it's the first real query
    const thread = threads.find(t => t.id === activeThreadId);
    if (thread?.title === 'New Health Conversation') {
      updateThreadTitle(activeThreadId, generateThreadTitle(message));
    }
  };
  
  // Handle query change from MedicalTeamTab
  const handleQueryChange = (queryId: string, queryText: string) => {
    setActiveQueryId(queryId);
    
    // Update current visualization to match the query
    if (activeThreadId && vizHistory[activeThreadId]) {
      const queryVisualizations = vizHistory[activeThreadId].items.filter(viz => viz.queryId === queryId);
      if (queryVisualizations.length > 0) {
        // Set the first visualization for this query as current
        const latestVizForQuery = queryVisualizations[queryVisualizations.length - 1];
        setVizHistory(prev => ({
          ...prev,
          [activeThreadId]: {
            ...prev[activeThreadId],
            current: latestVizForQuery.id
          }
        }));
      }
    }
    
    // Trigger scroll in ChatInterface
    setScrollToQuery(queryText);
    // Reset after a moment to allow re-selection of same query
    setTimeout(() => setScrollToQuery(''), 100);
  };
  
  // Handle reset - clear everything and go back to welcome
  const handleReset = () => {
    // Clear all state
    setThreads([]);
    setActiveThreadId(null);
    setTeamUpdate(undefined);
    setVizHistory({});
    setArtifactsMap(new Map());
    setCurrentArtifactId(null);
    setIsStreamingCode(false);
    setAppState('welcome');
    
    // Clear localStorage
    localStorage.removeItem('healthThreads');
    localStorage.removeItem('vizHistory');
    localStorage.removeItem('pendingQuestion');
  };

  // Existing resize handlers...
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isResizing || !containerRef.current) return;
    const containerRect = containerRef.current.getBoundingClientRect();
    const newLeftWidth = ((e.clientX - containerRect.left - 320) / (containerRect.width - 320)) * 100;
    if (newLeftWidth >= 20 && newLeftWidth <= 80) {
      setPanelWidth(100 - newLeftWidth);
    }
  };

  const handleMouseUp = () => {
    setIsResizing(false);
  };

  useEffect(() => {
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isResizing]);

  // Render based on app state
  if (appState === 'welcome' && threads.length === 0) {
    return (
      <div className="min-h-screen gradient-health-subtle">
        <EnhancedHeader 
          userName="George Vetticaden"
          lastCheckup="2 weeks ago"
          onSettingsClick={() => console.log('Settings clicked')}
          onResetClick={handleReset}
        />
        <WelcomeState onStartConversation={handleStartFirstConversation} />
      </div>
    );
  }

  return (
    <div className="min-h-screen gradient-health-subtle">
      <EnhancedHeader 
        userName="George Vetticaden"
        lastCheckup="2 weeks ago"
        onSettingsClick={() => console.log('Settings clicked')}
        onResetClick={handleReset}
      />
      
      <div ref={containerRef} className="flex h-[calc(100vh-73px)]">
        {/* Thread Sidebar */}
        <ThreadSidebar
          threads={threads}
          activeThreadId={activeThreadId}
          onThreadSelect={handleThreadSelect}
          onNewThread={handleNewThread}
        />

        {/* Main Chat Area */}
        <div 
          className="flex-1 flex flex-col overflow-hidden"
          style={{ width: isPanelOpen ? `${100 - panelWidth}%` : '100%' }}
        >
          {/* Medical Team Display removed - now in right panel */}

          {/* Chat Interface */}
          <div className="flex-1 overflow-hidden bg-gray-50/50">
            <ChatInterface 
              ref={chatInterfaceRef}
              conversationId={activeThreadId ?? undefined}
              onArtifact={handleNewArtifact}
              onCodeStreamStart={handleCodeStreamStart}
              onAppStateChange={handleAppStateChange}
              onTeamUpdate={handleTeamUpdate}
              onStreamingContent={handleStreamingContent}
              onMessageSend={handleMessageSend}
              appState={appState}
              scrollToQuery={scrollToQuery}
            />
          </div>
        </div>

        {/* Resizer - Show when panel should be visible */}
        {isPanelOpen && activeThreadId && (teamUpdate || isStreamingCode || currentArtifactId || vizHistory[activeThreadId]?.items?.length > 0) && (
          <div
            className={`relative w-2 bg-gray-300 hover:bg-gray-400 cursor-col-resize group transition-colors ${
              isResizing ? 'bg-blue-500' : ''
            }`}
            onMouseDown={handleMouseDown}
          >
            <div className="absolute inset-0 flex items-center justify-center">
              <GripVertical className="w-4 h-4 text-gray-600 group-hover:text-gray-700" />
            </div>
          </div>
        )}

        {/* Right Panel with Tabs */}
        {isPanelOpen && activeThreadId && (teamUpdate || isStreamingCode || currentArtifactId || vizHistory[activeThreadId]?.items?.length > 0) && (
          <div
            className="bg-white shadow-xl overflow-hidden flex flex-col"
            style={{ width: `${panelWidth}%` }}
          >
            <TabContainer
              activeTab={activeRightTab}
              onTabChange={setActiveRightTab}
              showVisualizationTab={vizHistory[activeThreadId]?.items.length > 0 || isStreamingCode}
            >
              {/* Medical Team Tab */}
              <MedicalTeamTab
                teamUpdate={teamUpdate}
                streamingContent={[lastStreamingContent].filter(Boolean)}
                onAgentClick={(id) => console.log('Agent clicked:', id)}
                isVisible={activeRightTab === 'medical-team'}
                currentQuery={currentQuery}
                onQueryChange={handleQueryChange}
                externalQueries={threadQueries.get(activeThreadId) || []}
                externalActiveQueryId={activeQueryId}
                onQueryCreated={(query: Query) => {
                  if (!activeThreadId) return;
                  
                  setThreadQueries(prev => {
                    const updated = new Map(prev);
                    const existing = updated.get(activeThreadId) || [];
                    // Check if query already exists
                    if (!existing.some(q => q.id === query.id)) {
                      updated.set(activeThreadId, [...existing, query]);
                    }
                    return updated;
                  });
                  
                  setActiveQueryId(query.id);
                }}
              />
              
              {/* Visualization Tab */}
              <div className="h-full" key={activeRightTab === 'visualization' ? 'viz-visible' : 'viz-hidden'}>
                {(vizHistory[activeThreadId]?.items.length > 0 && !isStreamingCode && !currentArtifactId) ? (
                  <div className="h-full flex flex-col">
                    <VisualizationPanel
                      visualizations={vizHistory[activeThreadId].items}
                      currentVizId={vizHistory[activeThreadId].current}
                      onVizChange={(vizId) => {
                        setVizHistory(prev => ({
                          ...prev,
                          [activeThreadId]: {
                          ...prev[activeThreadId],
                          current: vizId
                        }
                      }));
                      }}
                      width={100}
                      onClose={() => setIsPanelOpen(false)}
                      queries={threadQueries.get(activeThreadId) || []}
                      activeQueryId={activeQueryId}
                      onQuerySelect={(queryId) => {
                        const query = threadQueries.get(activeThreadId)?.find(q => q.id === queryId);
                        if (query) {
                          handleQueryChange(queryId, query.question);
                        }
                      }}
                    />
                  </div>
                ) : (
                  /* Show streaming artifact panel */
                  <div className="h-full flex flex-col">
                    {/* Panel Header */}
                    <div className="bg-white/90 border-b border-gray-200 px-4 py-3">
                      <div className="flex items-center justify-between">
                        <h2 className="font-medium text-gray-900">Visualizations</h2>
                        <div className="flex items-center gap-2">
                          {(threadQueries.get(activeThreadId) || []).length > 0 && (
                            <CompactQuerySelector
                              queries={threadQueries.get(activeThreadId) || []}
                              activeQueryId={activeQueryId}
                              onQuerySelect={(queryId) => {
                                const query = threadQueries.get(activeThreadId)?.find(q => q.id === queryId);
                                if (query) {
                                  handleQueryChange(queryId, query.question);
                                }
                              }}
                            />
                          )}
                          <button
                            onClick={() => setIsPanelOpen(false)}
                            className="p-1 hover:bg-gray-100 rounded transition-colors"
                          >
                            <PanelLeftClose className="w-5 h-5 text-gray-600" />
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Artifact Content */}
                    <div className="flex-1 overflow-y-auto bg-gray-50/50">
                      <div className="p-4">
                        {currentArtifact ? (
                          <CodeArtifact
                            code={currentArtifact.code}
                            language={currentArtifact.language || 'javascript'}
                            data={currentArtifact.data}
                            isStreaming={currentArtifact.isStreaming || false}
                          />
                        ) : isStreamingCode ? (
                          <div className="text-center text-blue-600 mt-8">
                            <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
                            <p className="mt-4">Generating visualization...</p>
                          </div>
                        ) : (
                          <div className="text-center text-gray-500 mt-8">
                            <p>No visualizations yet</p>
                            <p className="text-sm mt-2">Health insights will appear here</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </TabContainer>
          </div>
        )}

        {/* Toggle Button */}
        {!isPanelOpen && (
          <button
            onClick={() => setIsPanelOpen(true)}
            className="fixed right-4 top-24 bg-white shadow-lg rounded-lg p-2 hover:bg-gray-50 transition-colors z-10 border border-gray-300"
            title="Show visualizations"
          >
            <PanelLeftOpen className="w-5 h-5 text-gray-700" />
          </button>
        )}
      </div>
    </div>
  );
};

export default TwoPanelLayout;