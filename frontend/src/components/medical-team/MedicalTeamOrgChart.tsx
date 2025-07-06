import React, { useRef, useEffect, useState } from 'react';
import AgentCard from './AgentCard';
import { TeamMember } from '../../types/medical-team';

interface MedicalTeamOrgChartProps {
  teamMembers: TeamMember[];
  onAgentClick?: (agentId: string) => void;
}

const MedicalTeamOrgChart: React.FC<MedicalTeamOrgChartProps> = ({
  teamMembers,
  onAgentClick
}) => {
  const [connectionPaths, setConnectionPaths] = useState<string[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);
  const cmoRef = useRef<HTMLDivElement>(null);
  const specialistRefs = useRef<(HTMLDivElement | null)[]>([]);

  // Separate CMO and specialists
  const cmo = teamMembers.find(m => m.id === 'cmo');
  const specialists = teamMembers.filter(m => m.id !== 'cmo');
  
  // Reset refs array when specialists change
  useEffect(() => {
    specialistRefs.current = specialistRefs.current.slice(0, specialists.length);
  }, [specialists.length]);

  // Calculate SVG paths for connections
  useEffect(() => {
    const calculatePaths = () => {
      if (!containerRef.current || !cmoRef.current || specialists.length === 0) return;

      const paths: string[] = [];
      const containerRect = containerRef.current.getBoundingClientRect();

      // Get CMO position
      const cmoRect = cmoRef.current.getBoundingClientRect();
      const cmoX = cmoRect.left + cmoRect.width / 2 - containerRect.left;
      const cmoY = cmoRect.bottom - containerRect.top;

      // Calculate paths to each specialist
      specialistRefs.current.forEach((ref, index) => {
        if (!ref) return;

        const specRect = ref.getBoundingClientRect();
        const specX = specRect.left + specRect.width / 2 - containerRect.left;
        const specY = specRect.top - containerRect.top;

        // Create curved path
        const midY = (cmoY + specY) / 2;
        const path = `M ${cmoX} ${cmoY} Q ${cmoX} ${midY} ${specX} ${specY}`;
        paths.push(path);
      });

      setConnectionPaths(paths);
    };

    // Calculate paths multiple times to ensure they render correctly
    calculatePaths();
    const timer1 = setTimeout(calculatePaths, 100);
    const timer2 = setTimeout(calculatePaths, 300);
    const timer3 = setTimeout(calculatePaths, 500);
    
    // Also recalculate on window resize
    window.addEventListener('resize', calculatePaths);
    
    // Add visibility change listener to recalculate when tab becomes visible
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        calculatePaths();
        setTimeout(calculatePaths, 100);
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      window.removeEventListener('resize', calculatePaths);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [teamMembers, specialists.length]);

  // Determine which connections are active
  const getConnectionClass = (index: number) => {
    const specialist = specialists[index];
    if (!specialist) return 'connection-line';
    
    if (specialist.status === 'analyzing' || specialist.status === 'thinking') {
      return 'connection-line active';
    }
    
    return 'connection-line';
  };

  if (!cmo && specialists.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <p>Waiting for medical team assembly...</p>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="relative p-8 bg-white rounded-xl shadow-sm">
      {/* SVG for connection lines */}
      <svg 
        className="absolute inset-0 w-full h-full pointer-events-none"
        style={{ zIndex: 0 }}
        preserveAspectRatio="none"
      >
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
          >
            <polygon
              points="0 0, 10 3, 0 6"
              fill="#e5e7eb"
            />
          </marker>
        </defs>
        {connectionPaths.map((path, index) => (
          <path
            key={index}
            d={path}
            className={getConnectionClass(index)}
            fill="none"
            strokeWidth="2"
            strokeDasharray={specialists[index]?.status === 'analyzing' || specialists[index]?.status === 'thinking' ? '5,5' : undefined}
            markerEnd="url(#arrowhead)"
          />
        ))}
      </svg>

      {/* Top row of specialists */}
      {specialists.length > 0 && (
        <div 
          className="grid grid-cols-3 gap-4 justify-items-center relative stagger-animation mb-8" 
          style={{ zIndex: 1 }}
        >
          {specialists.slice(0, 3).map((specialist, index) => (
            <div 
              key={specialist.id}
              ref={el => specialistRefs.current[index] = el}
            >
              <AgentCard
                agent={specialist}
                onClick={() => onAgentClick?.(specialist.id)}
                isActive={specialist.status === 'analyzing' || specialist.status === 'thinking'}
              />
            </div>
          ))}
        </div>
      )}

      {/* CMO in the middle */}
      {cmo && (
        <div className="flex justify-center mb-8 relative" style={{ zIndex: 1 }}>
          <div ref={cmoRef}>
            <AgentCard 
              agent={cmo} 
              onClick={() => onAgentClick?.(cmo.id)}
            />
          </div>
        </div>
      )}

      {/* Bottom row of specialists */}
      {specialists.length > 3 && (
        <div 
          className="grid grid-cols-3 gap-4 justify-items-center relative stagger-animation" 
          style={{ zIndex: 1 }}
        >
          {specialists.slice(3, 6).map((specialist, index) => (
            <div 
              key={specialist.id}
              ref={el => specialistRefs.current[index + 3] = el}
            >
              <AgentCard
                agent={specialist}
                onClick={() => onAgentClick?.(specialist.id)}
                isActive={specialist.status === 'analyzing' || specialist.status === 'thinking'}
              />
            </div>
          ))}
        </div>
      )}

      {/* Team Status Summary */}
      {specialists.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-200 flex justify-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-gray-400 rounded-full" />
            <span className="text-gray-600">Waiting: {specialists.filter(s => s.status === 'waiting').length}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
            <span className="text-gray-600">Active: {specialists.filter(s => s.status === 'analyzing' || s.status === 'thinking').length}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full" />
            <span className="text-gray-600">Complete: {specialists.filter(s => s.status === 'complete').length}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default MedicalTeamOrgChart;