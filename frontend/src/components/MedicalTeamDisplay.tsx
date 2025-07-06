import React, { useEffect, useState } from 'react';
import { 
  Shield, Heart, FlaskConical, TrendingUp, 
  Stethoscope, Pill, Activity, Brain,
  BarChart3, Loader2, CheckCircle,
  AlertCircle, Clock
} from 'lucide-react';
import { TeamMember, TeamUpdate } from '../types/medical-team';

interface MedicalTeamDisplayProps {
  teamUpdate?: TeamUpdate;
  onSpecialistClick?: (id: string) => void;
}

const iconMap: { [key: string]: React.ComponentType<any> } = {
  Brain, Heart, Flask: FlaskConical, Activity, BarChart3, 
  Stethoscope, Pill, Shield, TrendingUp
};

const MedicalTeamDisplay: React.FC<MedicalTeamDisplayProps> = ({ 
  teamUpdate,
  onSpecialistClick 
}) => {
  const [animatedProgress, setAnimatedProgress] = useState<{ [key: string]: number }>({});
  const [showDetails, setShowDetails] = useState<{ [key: string]: boolean }>({});
  
  console.log('[MedicalTeamDisplay] Received teamUpdate:', teamUpdate);

  useEffect(() => {
    // Animate progress bars
    if (teamUpdate?.members) {
      teamUpdate.members.forEach(member => {
        if (member.progress !== undefined) {
          setTimeout(() => {
            setAnimatedProgress(prev => ({
              ...prev,
              [member.id]: member.progress || 0
            }));
          }, 100);
        }
      });
    }
  }, [teamUpdate?.members]);

  const getStatusIcon = (status: TeamMember['status']) => {
    switch (status) {
      case 'waiting':
        return <Clock className="w-4 h-4 text-gray-400" />;
      case 'thinking':
      case 'analyzing':
        return <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />;
      case 'complete':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: TeamMember['status']) => {
    switch (status) {
      case 'waiting':
        return 'border-gray-200 bg-gray-50';
      case 'thinking':
        return 'border-blue-300 bg-blue-50';
      case 'analyzing':
        return 'border-blue-400 bg-blue-50 shadow-md';
      case 'complete':
        return 'border-green-300 bg-green-50';
      case 'error':
        return 'border-red-300 bg-red-50';
      default:
        return 'border-gray-200';
    }
  };

  const getTeamStatusMessage = () => {
    if (!teamUpdate) return 'Initializing medical team...';
    
    switch (teamUpdate.teamStatus) {
      case 'assembling':
        return 'CMO is analyzing your query and assembling the team...';
      case 'analyzing':
        return `${teamUpdate.members.filter(m => m.status === 'analyzing').length} specialists are analyzing your health data...`;
      case 'synthesizing':
        return 'CMO is synthesizing findings from all specialists...';
      case 'complete':
        return 'Analysis complete. Review findings below.';
      default:
        return 'Processing your request...';
    }
  };

  if (!teamUpdate || teamUpdate.members.length === 0) {
    return (
      <div className="bg-white/70 backdrop-blur-sm p-6 m-4 rounded-xl shadow-sm border border-gray-200">
        <div className="text-center text-gray-500">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2" />
          <p>Waiting for health query...</p>
        </div>
      </div>
    );
  }

  const cmo = teamUpdate.members.find(m => m.id === 'cmo');
  const specialists = teamUpdate.members.filter(m => m.id !== 'cmo');

  return (
    <div className="bg-white/70 backdrop-blur-sm p-6 m-4 rounded-xl shadow-sm border border-gray-200">
      {/* Status Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-900">Medical Team Analysis</h3>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full animate-pulse ${
              teamUpdate.teamStatus === 'complete' ? 'bg-green-500' : 'bg-blue-500'
            }`} />
            <span className="text-sm font-medium text-gray-700">
              {teamUpdate.teamStatus === 'complete' ? 'Complete' : 'In Progress'}
            </span>
          </div>
        </div>
        <p className="text-sm text-gray-600">{getTeamStatusMessage()}</p>
        
        {/* Overall Progress Bar */}
        {teamUpdate.teamStatus !== 'complete' && (
          <div className="mt-3">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>Overall Progress</span>
              <span>{teamUpdate.overallProgress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${teamUpdate.overallProgress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* CMO Card */}
      {cmo && (
        <div className={`mb-4 p-4 rounded-lg border-2 transition-all duration-300 ${getStatusColor(cmo.status)}`}>
          <div className="flex items-start gap-3">
            <div className={`w-12 h-12 bg-gradient-to-r ${cmo.gradient || 'from-blue-500 to-blue-600'} rounded-full flex items-center justify-center flex-shrink-0`}>
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-semibold text-gray-900">{cmo.name}</h4>
                  <p className="text-sm text-gray-600">{cmo.specialty}</p>
                </div>
                {getStatusIcon(cmo.status)}
              </div>
              {cmo.message && (
                <p className="text-sm text-gray-700 mt-2 italic">"{cmo.message}"</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Specialists Grid */}
      {specialists.length > 0 && (
        <>
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Specialist Team</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {specialists.map((specialist, index) => {
              const Icon = specialist.icon ? iconMap[specialist.icon] : Stethoscope;
              const isActive = specialist.status === 'analyzing' || specialist.status === 'thinking';
              const progress = animatedProgress[specialist.id] || 0;

              return (
                <div
                  key={specialist.id}
                  className={`p-4 rounded-lg border-2 transition-all duration-300 cursor-pointer ${getStatusColor(specialist.status)} ${
                    isActive ? 'scale-102' : ''
                  } hover:shadow-md`}
                  onClick={() => onSpecialistClick?.(specialist.id)}
                  style={{
                    animationDelay: `${index * 100}ms`
                  }}
                >
                  <div className="flex items-start gap-3">
                    <div className={`w-10 h-10 bg-gradient-to-r ${specialist.gradient || 'from-gray-400 to-gray-500'} rounded-full flex items-center justify-center flex-shrink-0 ${
                      isActive ? 'animate-pulse' : ''
                    }`}>
                      <Icon className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <div>
                          <h5 className="font-medium text-gray-900 text-sm">{specialist.name}</h5>
                          <p className="text-xs text-gray-600">{specialist.specialty}</p>
                        </div>
                        {getStatusIcon(specialist.status)}
                      </div>

                      {/* Current Task */}
                      {specialist.currentTask && specialist.status === 'analyzing' && (
                        <p className="text-xs text-gray-600 mt-2 mb-1">{specialist.currentTask}</p>
                      )}

                      {/* Progress Bar */}
                      {specialist.status === 'analyzing' && specialist.progress !== undefined && (
                        <div className="mt-2">
                          <div className="w-full bg-gray-200 rounded-full h-1.5">
                            <div
                              className="bg-blue-500 h-1.5 rounded-full transition-all duration-500"
                              style={{ width: `${progress}%` }}
                            />
                          </div>
                        </div>
                      )}

                      {/* Completion Details */}
                      {specialist.status === 'complete' && (
                        <div className="mt-2 space-y-1">
                          {specialist.confidence !== undefined && (
                            <div className="flex justify-between text-xs">
                              <span className="text-gray-600">Confidence</span>
                              <span className="font-medium text-gray-900">{Math.round(specialist.confidence)}%</span>
                            </div>
                          )}
                          {specialist.toolCalls !== undefined && (
                            <div className="flex justify-between text-xs">
                              <span className="text-gray-600">Tool calls</span>
                              <span className="font-medium text-gray-900">{specialist.toolCalls}</span>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Error State */}
                      {specialist.status === 'error' && (
                        <p className="text-xs text-red-600 mt-2">Analysis failed. CMO will adapt.</p>
                      )}

                      {/* Show Details Toggle */}
                      {specialist.message && specialist.status === 'complete' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setShowDetails(prev => ({
                              ...prev,
                              [specialist.id]: !prev[specialist.id]
                            }));
                          }}
                          className="text-xs text-blue-600 hover:text-blue-700 mt-2"
                        >
                          {showDetails[specialist.id] ? 'Hide' : 'Show'} findings
                        </button>
                      )}

                      {/* Detailed Findings */}
                      {showDetails[specialist.id] && specialist.message && (
                        <div className="mt-2 p-2 bg-white rounded text-xs text-gray-700 border border-gray-200">
                          {specialist.message}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {/* Team Summary Stats */}
      {teamUpdate.teamStatus === 'complete' && specialists.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-gray-900">{specialists.length}</p>
              <p className="text-xs text-gray-600">Specialists Consulted</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {specialists.reduce((sum, s) => sum + (s.toolCalls || 0), 0)}
              </p>
              <p className="text-xs text-gray-600">Total Tool Calls</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {Math.round(
                  specialists.reduce((sum, s) => sum + (s.confidence || 0), 0) / specialists.length
                )}%
              </p>
              <p className="text-xs text-gray-600">Avg Confidence</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MedicalTeamDisplay;