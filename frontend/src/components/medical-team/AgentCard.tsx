import React from 'react';
import { 
  Brain, Heart, FlaskConical, Activity, BarChart3, 
  Shield, Pill, Loader2, CheckCircle, AlertCircle, 
  Clock, Zap, Apple, Stethoscope 
} from 'lucide-react';
import { TeamMember } from '../../types/medical-team';

interface AgentCardProps {
  agent: TeamMember;
  isActive?: boolean;
  onClick?: () => void;
  connectionRef?: React.RefObject<HTMLDivElement>;
}

const iconMap: { [key: string]: React.ComponentType<any> } = {
  Brain, Heart, FlaskConical, Activity, BarChart3, 
  Shield, Pill, Apple, Stethoscope
};

const AgentCard: React.FC<AgentCardProps> = ({ 
  agent, 
  isActive = false, 
  onClick,
  connectionRef 
}) => {
  const Icon = agent.icon ? iconMap[agent.icon] || Brain : Brain;
  
  const getStatusIcon = () => {
    switch (agent.status) {
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

  const getCardStyles = () => {
    const baseStyles = `
      relative w-36 h-20 bg-white rounded-xl p-3 cursor-pointer 
      transition-all duration-300 flex flex-col justify-between
    `;
    
    if (agent.status === 'analyzing' || agent.status === 'thinking') {
      return `${baseStyles} border-2 border-blue-400 shadow-lg scale-105 animate-pulse`;
    }
    
    if (agent.status === 'complete') {
      return `${baseStyles} border-2 border-green-300 shadow-md`;
    }
    
    if (agent.status === 'error') {
      return `${baseStyles} border-2 border-red-300`;
    }
    
    return `${baseStyles} border-2 border-gray-200 hover:border-gray-300 hover:shadow-md`;
  };

  const getGradientStyles = () => {
    if (agent.gradient) {
      return `bg-gradient-to-r ${agent.gradient}`;
    }
    return 'bg-gradient-to-r from-gray-400 to-gray-500';
  };

  return (
    <div 
      ref={connectionRef}
      className={getCardStyles()}
      onClick={onClick}
      style={{
        animation: isActive ? 'activePulse 2s infinite' : undefined
      }}
    >
      {/* Agent Info */}
      <div className="flex items-start gap-2">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${getGradientStyles()}`}>
          <Icon className="w-4 h-4 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-semibold text-gray-900 truncate">{agent.name}</div>
          <div className="text-xs text-gray-600 truncate">{agent.specialty}</div>
        </div>
      </div>

      {/* Status Row */}
      <div className="flex items-center justify-between mt-1">
        <div className="flex items-center gap-1">
          {getStatusIcon()}
          {agent.status === 'analyzing' && (
            <Zap className="w-3 h-3 text-blue-600" />
          )}
        </div>
        
        {/* Confidence or Progress */}
        {agent.status === 'complete' && agent.confidence !== undefined && (
          <span className="text-xs font-semibold text-green-600">
            {Math.round(agent.confidence)}%
          </span>
        )}
        
        {agent.status === 'analyzing' && agent.progress !== undefined && (
          <span className="text-xs text-gray-600">
            {agent.progress}%
          </span>
        )}
      </div>

      {/* Progress Bar for Active Analysis */}
      {agent.status === 'analyzing' && agent.progress !== undefined && (
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gray-200 rounded-b-xl overflow-hidden">
          <div 
            className="h-full bg-blue-500 transition-all duration-500"
            style={{ width: `${agent.progress}%` }}
          />
        </div>
      )}
    </div>
  );
};

export default AgentCard;