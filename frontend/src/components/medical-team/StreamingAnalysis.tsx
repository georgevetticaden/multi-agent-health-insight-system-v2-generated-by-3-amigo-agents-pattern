import React, { useRef, useEffect, useState } from 'react';
import { 
  Brain, Heart, FlaskConical, Activity, BarChart3, 
  Shield, Pill, FileText, Loader2, Apple, CheckCircle, Stethoscope 
} from 'lucide-react';
import { TeamMember } from '../../types/medical-team';

interface StreamingAnalysisProps {
  activeAgent?: TeamMember;
  streamingContent?: string[];
  completedAnalyses?: Array<{
    agentId: string;
    summary: string;
  }>;
  teamMembers?: TeamMember[];
}

const iconMap: { [key: string]: React.ComponentType<any> } = {
  Brain, Heart, FlaskConical, Activity, BarChart3, 
  Shield, Pill, Apple, Stethoscope
};

const StreamingAnalysis: React.FC<StreamingAnalysisProps> = ({
  activeAgent,
  streamingContent = [],
  completedAnalyses = [],
  teamMembers = []
}) => {
  const contentRef = useRef<HTMLDivElement>(null);
  const [showCursor, setShowCursor] = useState(true);

  // Auto-scroll to bottom when new content arrives
  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [streamingContent]);

  // Cursor blink effect
  useEffect(() => {
    const interval = setInterval(() => {
      setShowCursor(prev => !prev);
    }, 500);
    return () => clearInterval(interval);
  }, []);

  const getAgentIcon = (agent?: TeamMember) => {
    if (!agent || !agent.icon) return Brain;
    return iconMap[agent.icon] || Brain;
  };

  const getAgentById = (agentId: string): TeamMember | undefined => {
    return teamMembers.find(member => member.id === agentId);
  };

  if (!activeAgent && completedAnalyses.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500 p-8">
        <div className="text-center">
          <Brain className="w-12 h-12 mx-auto mb-3 text-gray-400" />
          <p>Waiting for analysis to begin...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Completed Analyses Section */}
      {completedAnalyses.length > 0 && (
        <div className="space-y-3 mb-4">
            {completedAnalyses.map((analysis) => {
              const agent = getAgentById(analysis.agentId);
              if (!agent) return null;
              
              const AgentIcon = getAgentIcon(agent);
              
              return (
                <div 
                  key={analysis.agentId} 
                  className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start gap-3">
                    {/* Agent Icon with Gradient Background */}
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 bg-gradient-to-r ${agent.gradient || 'from-gray-400 to-gray-500'}`}>
                      <AgentIcon className="w-5 h-5 text-white" />
                    </div>
                    
                    {/* Agent Info and Summary */}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h5 className="font-semibold text-gray-900">{agent.name}</h5>
                        <span className="text-xs text-gray-500">• {agent.specialty}</span>
                        {agent.confidence && (
                          <span className="ml-auto text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full">
                            {agent.confidence}% confidence
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-700 leading-relaxed">{analysis.summary}</p>
                      {agent.toolCalls && (
                        <div className="mt-2 text-xs text-gray-500">
                          {agent.toolCalls} queries executed
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
            
            {/* Dr. Vitality Synthesis - Show only when all specialists are complete and CMO is synthesizing */}
            {(() => {
              const cmo = teamMembers.find(m => m.id === 'cmo');
              const specialists = teamMembers.filter(m => m.id !== 'cmo');
              const allSpecialistsComplete = specialists.length > 0 && specialists.every(s => s.status === 'complete');
              const cmoSynthesizing = cmo && (cmo.status === 'analyzing' || cmo.status === 'complete') && cmo.progress && cmo.progress >= 90;
              
              return allSpecialistsComplete && cmoSynthesizing;
            })() && (
              <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg border border-blue-200 p-4">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-sm">
                      <Brain className="w-6 h-6 text-white" />
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="font-semibold text-blue-900">Dr. Vitality - Chief Medical Officer</h4>
                      {teamMembers.find(m => m.id === 'cmo')?.status === 'analyzing' && (
                        <span className="text-xs bg-blue-200 text-blue-700 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <Loader2 className="w-3 h-3 animate-spin" />
                          Synthesizing
                        </span>
                      )}
                      {teamMembers.find(m => m.id === 'cmo')?.status === 'complete' && (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <CheckCircle className="w-3 h-3" />
                          Complete
                        </span>
                      )}
                    </div>
                    <div className="bg-white/80 rounded p-3 text-sm text-gray-700">
                      {teamMembers.find(m => m.id === 'cmo')?.status === 'analyzing' ? (
                        <p className="text-blue-700 italic">Synthesizing findings from all specialists...</p>
                      ) : (
                        <p className="font-medium">Comprehensive analysis complete. Final synthesis has been provided in the chat.</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

      {/* Active Streaming Content Section */}
      {activeAgent && activeAgent.status === 'analyzing' && streamingContent.length > 0 && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <div className="bg-gray-100 px-3 py-2 border-b border-gray-200">
            <h4 className="text-xs font-semibold text-gray-700 flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              LIVE STREAM - {activeAgent.name}
            </h4>
          </div>
          <div className="p-3">
              <div 
                ref={contentRef}
                className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm leading-relaxed max-h-[200px] overflow-y-auto"
              >
                {streamingContent.length > 0 ? (
                  <>
                    {streamingContent.map((line, index) => (
                      <div 
                        key={index} 
                        className="mb-1"
                        style={{ animation: 'fadeIn 0.3s ease-out' }}
                      >
                        {line}
                      </div>
                    ))}
                    {/* Cursor */}
                    <span 
                      className="inline-block w-2 h-4 bg-green-400 ml-1"
                      style={{ 
                        opacity: showCursor ? 1 : 0,
                        transition: 'opacity 0.1s'
                      }}
                    />
                  </>
                ) : (
                  <div className="text-gray-500 italic">
                    Waiting for analysis data...
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

      {/* Empty State when no completed analyses */}
      {completedAnalyses.length === 0 && (!activeAgent || activeAgent.status !== 'analyzing' || streamingContent.length === 0) && (
        <div className="py-12">
          <div className="text-center text-gray-500">
            <Brain className="w-12 h-12 mx-auto mb-3 text-gray-400" />
            <p>No completed analyses yet</p>
            <p className="text-sm mt-2">Analyses will appear here as specialists complete their work</p>
          </div>
        </div>
      )}

    </div>
  );
};

export default StreamingAnalysis;