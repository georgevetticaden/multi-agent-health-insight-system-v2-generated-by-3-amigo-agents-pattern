import React from 'react';
import { Eye, Settings, Network, ArrowRight, AlertTriangle, Users, Brain, Zap, TrendingUp } from 'lucide-react';

const ThreeGulfsVisualization = () => {
  return (
    <div className="w-full bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50 p-8 overflow-x-auto">
      {/* Title */}
      <div className="text-center mb-8">
        <h2 className="text-5xl font-bold mb-3">
          <span className="bg-gradient-to-r from-blue-600 via-orange-600 to-purple-600 bg-clip-text text-transparent">
            The Three Gulfs Multiplied: Single Agent to Multi-Agent Complexity
          </span>
        </h2>
        <p className="text-2xl text-gray-700 max-w-5xl mx-auto">
          How Challenging Evaluation Problems Become Exponentially Harder<br/>
          When 8 Agents Must Coordinate Across Domains
        </p>
      </div>

      {/* Three Panels */}
      <div className="flex justify-center gap-6 min-w-max">
        
        {/* Panel 1: Single Agent - Challenging */}
        <div className="bg-white rounded-xl p-6 border-2 border-gray-200 shadow-lg w-96">
          <div className="text-center mb-6">
            <div className="flex items-center justify-center gap-2 mb-2">
              <Brain className="w-10 h-10 text-gray-600" />
              <h3 className="text-3xl font-bold text-gray-800">Single Agent System</h3>
            </div>
            <p className="text-lg text-gray-600">Already Non-Deterministic</p>
          </div>

          {/* Simple Flow */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6 border border-gray-200">
            <div className="flex items-center justify-between">
              <div className="text-center">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-2 border-2 border-gray-300">
                  <span className="text-2xl">📝</span>
                </div>
                <p className="text-base text-gray-600">Query</p>
              </div>
              <ArrowRight className="w-8 h-8 text-gray-400" />
              <div className="text-center">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-2 border-2 border-gray-300">
                  <Brain className="w-8 h-8 text-gray-600" />
                </div>
                <p className="text-base text-gray-600">LLM</p>
              </div>
              <ArrowRight className="w-8 h-8 text-gray-400" />
              <div className="text-center">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-2 border-2 border-gray-300">
                  <span className="text-2xl">📄</span>
                </div>
                <p className="text-base text-gray-600">Response</p>
              </div>
            </div>
          </div>

          {/* Already Challenging Gulfs */}
          <div className="space-y-4">
            <div className="bg-blue-50 rounded-lg p-4 border-2 border-blue-200">
              <div className="flex items-center gap-3 mb-2">
                <Eye className="w-7 h-7 text-blue-600" />
                <h4 className="text-xl font-semibold text-blue-800">Gulf of Comprehension</h4>
              </div>
              <div className="flex items-center justify-between">
                <p className="text-lg text-blue-700">• 1 LLM call to trace</p>
                <span className="text-blue-600 font-bold text-2xl">×1</span>
              </div>
              <p className="text-lg text-blue-700 mt-1">• Non-deterministic output</p>
              <div className="mt-2 h-3 bg-blue-100 rounded-full overflow-hidden">
                <div className="h-full w-1/5 bg-blue-500 rounded-full"></div>
              </div>
            </div>

            <div className="bg-orange-50 rounded-lg p-4 border-2 border-orange-200">
              <div className="flex items-center gap-3 mb-2">
                <Settings className="w-7 h-7 text-orange-600" />
                <h4 className="text-xl font-semibold text-orange-800">Gulf of Specification</h4>
              </div>
              <div className="flex items-center justify-between">
                <p className="text-lg text-orange-700">• 1 prompt to perfect</p>
                <span className="text-orange-600 font-bold text-2xl">×1</span>
              </div>
              <p className="text-lg text-orange-700 mt-1">• Hidden ambiguities</p>
              <div className="mt-2 h-3 bg-orange-100 rounded-full overflow-hidden">
                <div className="h-full w-1/5 bg-orange-500 rounded-full"></div>
              </div>
            </div>

            <div className="bg-purple-50 rounded-lg p-4 border-2 border-purple-200">
              <div className="flex items-center gap-3 mb-2">
                <Network className="w-7 h-7 text-purple-600" />
                <h4 className="text-xl font-semibold text-purple-800">Gulf of Generalization</h4>
              </div>
              <div className="flex items-center justify-between">
                <p className="text-lg text-purple-700">• Variable behavior</p>
                <span className="text-purple-600 font-bold text-2xl">×1</span>
              </div>
              <p className="text-lg text-purple-700 mt-1">• Edge case surprises</p>
              <div className="mt-2 h-3 bg-purple-100 rounded-full overflow-hidden">
                <div className="h-full w-1/5 bg-purple-500 rounded-full"></div>
              </div>
            </div>
          </div>
        </div>

        {/* Arrow Between Panels */}
        <div className="flex items-center">
          <div className="text-center">
            <ArrowRight className="w-12 h-12 text-gray-500" />
            <p className="text-lg text-gray-600 mt-2">Add 8 Agents</p>
          </div>
        </div>

        {/* Panel 2: Multi-Agent - Multiplying */}
        <div className="bg-gradient-to-b from-yellow-50 to-orange-50 rounded-xl p-6 border-2 border-orange-300 shadow-lg w-96">
          <div className="text-center mb-6">
            <div className="flex items-center justify-center gap-2 mb-2">
              <Users className="w-10 h-10 text-orange-600" />
              <h3 className="text-3xl font-bold text-orange-800">Multi-Agent System</h3>
            </div>
            <p className="text-lg text-orange-600">8 Coordinating Specialists</p>
          </div>

          {/* Complex Flow */}
          <div className="bg-white rounded-lg p-4 mb-6 border-2 border-orange-200">
            <div className="relative h-48">
              {/* CMO in center */}
              <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10">
                <div className="w-20 h-20 bg-gradient-to-br from-orange-400 to-yellow-500 rounded-full flex items-center justify-center shadow-lg border-2 border-white">
                  <Brain className="w-10 h-10 text-white" />
                </div>
                <p className="text-center text-base font-semibold text-orange-700 mt-1">CMO</p>
              </div>
              
              {/* 8 Specialists around CMO with tool indicators */}
              {[...Array(8)].map((_, i) => {
                const angle = (i * 45) * Math.PI / 180;
                const x = 50 + 35 * Math.cos(angle);
                const y = 50 + 35 * Math.sin(angle);
                
                // Tool icons positions (2 tools per specialist)
                const toolAngle1 = angle - 0.3;
                const toolAngle2 = angle + 0.3;
                const toolRadius = 48;
                
                return (
                  <div key={i}>
                    {/* Specialist node */}
                    <div
                      className="absolute transform -translate-x-1/2 -translate-y-1/2"
                      style={{ left: `${x}%`, top: `${y}%` }}
                    >
                      <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-500 rounded-full flex items-center justify-center border-2 border-white shadow">
                        <span className="text-white text-sm font-bold">S{i+1}</span>
                      </div>
                    </div>
                    
                    {/* Tool icons */}
                    <div
                      className="absolute transform -translate-x-1/2 -translate-y-1/2"
                      style={{ 
                        left: `${50 + toolRadius * Math.cos(toolAngle1)}%`, 
                        top: `${50 + toolRadius * Math.sin(toolAngle1)}%` 
                      }}
                    >
                      <div className="text-orange-600 text-lg">🔧</div>
                    </div>
                    <div
                      className="absolute transform -translate-x-1/2 -translate-y-1/2"
                      style={{ 
                        left: `${50 + toolRadius * Math.cos(toolAngle2)}%`, 
                        top: `${50 + toolRadius * Math.sin(toolAngle2)}%` 
                      }}
                    >
                      <div className="text-orange-600 text-lg opacity-70">🔧</div>
                    </div>
                  </div>
                );
              })}
              
              {/* Connection lines */}
              <svg className="absolute inset-0 w-full h-full" style={{ zIndex: 0 }}>
                {[...Array(8)].map((_, i) => {
                  const angle = (i * 45) * Math.PI / 180;
                  const x1 = 50;
                  const y1 = 50;
                  const x2 = 50 + 35 * Math.cos(angle);
                  const y2 = 50 + 35 * Math.sin(angle);
                  return (
                    <line
                      key={i}
                      x1={`${x1}%`}
                      y1={`${y1}%`}
                      x2={`${x2}%`}
                      y2={`${y2}%`}
                      stroke="rgb(251 146 60)"
                      strokeWidth="2"
                      opacity="0.5"
                    />
                  );
                })}
              </svg>
            </div>
          </div>

          {/* Tool Proliferation Indicator */}
          <div className="bg-gradient-to-r from-gray-100 to-orange-100 rounded-lg p-3 mb-4 border border-orange-300">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-2xl">🔧</span>
                <span className="text-base font-semibold text-gray-700">Tool Call Explosion</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-600">1 tool</span>
                <ArrowRight className="w-5 h-5 text-orange-500" />
                <span className="text-orange-600 font-bold">15+ tools</span>
              </div>
            </div>
            <div className="text-sm text-gray-600 mt-1">Each specialist invokes 2-3 data tools</div>
          </div>

          {/* Multiplying Gulfs */}
          <div className="space-y-4">
            <div className="bg-blue-100 rounded-lg p-4 border-2 border-blue-400">
              <div className="flex items-center gap-3 mb-2">
                <Eye className="w-7 h-7 text-blue-600" />
                <h4 className="text-xl font-semibold text-blue-800">Gulf of Comprehension</h4>
                <TrendingUp className="w-6 h-6 text-red-600" />
              </div>
              <div className="flex items-center justify-between">
                <p className="text-lg text-blue-700">• Distributed agent reasoning</p>
                <div className="flex items-center gap-2">
                  <span className="text-red-600 font-bold text-xl animate-pulse">×21 LLM</span>
                  <span className="text-orange-600 font-bold text-lg">+</span>
                  <span className="text-orange-600 font-bold text-xl animate-pulse">×15 Tools</span>
                </div>
              </div>
              <p className="text-lg text-blue-700 mt-1">• 90+ second traces</p>
              <div className="mt-2 h-3 bg-blue-200 rounded-full overflow-hidden">
                <div className="h-full w-3/5 bg-gradient-to-r from-blue-500 to-red-500 rounded-full"></div>
              </div>
            </div>

            <div className="bg-orange-100 rounded-lg p-4 border-2 border-orange-400">
              <div className="flex items-center gap-3 mb-2">
                <Settings className="w-7 h-7 text-orange-600" />
                <h4 className="text-xl font-semibold text-orange-800">Gulf of Specification</h4>
                <TrendingUp className="w-6 h-6 text-red-600" />
              </div>
              <div className="flex items-center justify-between">
                <p className="text-lg text-orange-700">• 8 coordination points</p>
                <span className="text-red-600 font-bold text-2xl animate-pulse">×8</span>
              </div>
              <p className="text-lg text-orange-700 mt-1">• Cascading ambiguity</p>
              <div className="mt-2 h-3 bg-orange-200 rounded-full overflow-hidden">
                <div className="h-full w-3/5 bg-gradient-to-r from-orange-500 to-red-500 rounded-full"></div>
              </div>
            </div>

            <div className="bg-purple-100 rounded-lg p-4 border-2 border-purple-400">
              <div className="flex items-center gap-3 mb-2">
                <Network className="w-7 h-7 text-purple-600" />
                <h4 className="text-xl font-semibold text-purple-800">Gulf of Generalization</h4>
                <TrendingUp className="w-6 h-6 text-red-600" />
              </div>
              <div className="flex items-center justify-between">
                <p className="text-lg text-purple-700">• 5 eval dimensions</p>
                <span className="text-red-600 font-bold text-2xl animate-pulse">×40</span>
              </div>
              <p className="text-lg text-purple-700 mt-1">• Compound failures</p>
              <div className="mt-2 h-3 bg-purple-200 rounded-full overflow-hidden">
                <div className="h-full w-3/5 bg-gradient-to-r from-purple-500 to-red-500 rounded-full"></div>
              </div>
            </div>
          </div>
        </div>

        {/* Arrow Between Panels */}
        <div className="flex items-center">
          <div className="text-center">
            <ArrowRight className="w-12 h-12 text-gray-500" />
            <p className="text-lg text-gray-600 mt-2">Cascade Effect</p>
          </div>
        </div>

        {/* Panel 3: Exponential Complexity */}
        <div className="bg-gradient-to-b from-red-50 to-pink-50 rounded-xl p-6 border-2 border-red-400 shadow-lg w-96">
          <div className="text-center mb-6">
            <div className="flex items-center justify-center gap-2 mb-2">
              <Zap className="w-10 h-10 text-red-600" />
              <h3 className="text-3xl font-bold text-red-800">Exponential Complexity</h3>
            </div>
            <p className="text-lg text-red-600">Cascading Failure Modes</p>
          </div>

          {/* Explosion Visual */}
          <div className="bg-white rounded-lg p-4 mb-6 relative overflow-hidden border-2 border-red-300">
            <div className="relative h-48">
              {/* Central explosion point */}
              <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                <div className="w-32 h-32 rounded-full bg-gradient-to-r from-red-200 to-pink-200 animate-ping"></div>
                <div className="w-24 h-24 rounded-full bg-gradient-to-r from-red-300 to-orange-300 animate-ping animation-delay-200 absolute top-4 left-4"></div>
                <div className="w-16 h-16 rounded-full bg-gradient-to-r from-red-500 to-orange-500 absolute top-8 left-8 flex items-center justify-center">
                  <AlertTriangle className="w-8 h-8 text-white animate-pulse" />
                </div>
              </div>
              
              {/* Radiating complexity indicators */}
              <div className="absolute top-4 left-4 text-red-600 font-bold text-lg animate-pulse">21+ LLM</div>
              <div className="absolute top-4 right-4 text-orange-600 font-bold text-lg animate-pulse animation-delay-300">15+ Tools</div>
              <div className="absolute bottom-4 left-4 text-purple-600 font-bold text-lg animate-pulse animation-delay-600">8 Agents</div>
              <div className="absolute bottom-4 right-4 text-pink-600 font-bold text-lg animate-pulse animation-delay-900">40 Failures</div>
            </div>
          </div>

          {/* Exponential Gulfs */}
          <div className="space-y-4">
            <div className="bg-gradient-to-r from-blue-100 to-red-100 rounded-lg p-4 border-2 border-red-400">
              <div className="flex items-center gap-3 mb-2">
                <Eye className="w-7 h-7 text-blue-600" />
                <h4 className="text-xl font-semibold text-red-800">Comprehension Explosion</h4>
              </div>
              <p className="text-base text-red-700">• Distributed reasoning chains</p>
              <p className="text-base text-red-700">• Parallel execution paths</p>
              <p className="text-base text-red-700">• Tool invocation cascades</p>
              <p className="text-base text-red-700">• Data retrieval explosions</p>
              <div className="mt-2 h-3 bg-red-200 rounded-full overflow-hidden">
                <div className="h-full w-full bg-gradient-to-r from-blue-500 via-red-500 to-pink-500 rounded-full animate-pulse"></div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-orange-100 to-red-100 rounded-lg p-4 border-2 border-red-400">
              <div className="flex items-center gap-3 mb-2">
                <Settings className="w-7 h-7 text-orange-600" />
                <h4 className="text-xl font-semibold text-red-800">Specification Chaos</h4>
              </div>
              <p className="text-base text-red-700">• Cross-domain ambiguity</p>
              <p className="text-base text-red-700">• Coordination protocol gaps</p>
              <p className="text-base text-red-700">• Context propagation loss</p>
              <div className="mt-2 h-3 bg-red-200 rounded-full overflow-hidden">
                <div className="h-full w-full bg-gradient-to-r from-orange-500 via-red-500 to-pink-500 rounded-full animate-pulse"></div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-purple-100 to-red-100 rounded-lg p-4 border-2 border-red-400">
              <div className="flex items-center gap-3 mb-2">
                <Network className="w-7 h-7 text-purple-600" />
                <h4 className="text-xl font-semibold text-red-800">Generalization Breakdown</h4>
              </div>
              <p className="text-base text-red-700">• Combinatorial failure modes</p>
              <p className="text-base text-red-700">• Edge case multiplication</p>
              <p className="text-base text-red-700">• Emergent misbehaviors</p>
              <div className="mt-2 h-3 bg-red-200 rounded-full overflow-hidden">
                <div className="h-full w-full bg-gradient-to-r from-purple-500 via-red-500 to-pink-500 rounded-full animate-pulse"></div>
              </div>
            </div>
          </div>

          {/* Bottom Alert */}
          <div className="mt-4 bg-red-100 rounded-lg p-3 border-2 border-red-500">
            <p className="text-red-700 text-center font-semibold text-lg">
              Traditional Testing Approaches Fail Completely
            </p>
          </div>
        </div>
      </div>

      {/* Bottom Caption */}
      <div className="text-center mt-8">
        <p className="text-gray-600 text-xl italic max-w-5xl mx-auto">
          "A single health query now touches 21+ LLM calls, 15+ tool invocations across 8 agents, creating intricate coordination patterns that span 90+ seconds of real-time processing."
        </p>
      </div>
    </div>
  );
};

export default ThreeGulfsVisualization;