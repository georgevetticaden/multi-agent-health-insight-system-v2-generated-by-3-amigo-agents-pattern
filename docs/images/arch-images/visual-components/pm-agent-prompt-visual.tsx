import React from 'react';
import { FileText, Brain, Package, Users, Activity, Database, Code, Layout, BookOpen, Layers, Target, Building } from 'lucide-react';

const PMAgentPromptVisual = () => {
  return (
    <div className="w-full bg-gradient-to-br from-slate-900 via-blue-900 to-purple-900 p-8">
      {/* Title */}
      <div className="text-center mb-8">
        <h2 className="text-4xl font-bold mb-3">
          <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Product Owner's Strategic Input to PM Agent
          </span>
        </h2>
        <p className="text-xl text-gray-300 max-w-5xl mx-auto">
          Three essential elements that transform a vague idea into comprehensive product specifications
        </p>
      </div>

      {/* Single Row with Three Columns */}
      <div className="flex gap-6 max-w-7xl mx-auto">
        
        {/* Column 1: Core Requirements */}
        <div className="flex-1 bg-gradient-to-b from-yellow-500/20 to-orange-500/20 rounded-xl p-6 border border-yellow-500/30">
          {/* Category Label */}
          <div className="text-center mb-3">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-500/20 text-yellow-300 border border-yellow-500/30">
              DOMAIN REQUIREMENTS
            </span>
          </div>
          
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-full mx-auto mb-4 flex items-center justify-center">
              <Target className="w-9 h-9 text-white" />
            </div>
            <h3 className="text-3xl font-bold text-yellow-300 mb-2">Core Requirements</h3>
            <p className="text-gray-300 text-base">What I need the system to do</p>
          </div>
          
          <div className="space-y-3">
            <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
              <div className="flex items-start gap-3">
                <Users className="w-6 h-6 text-yellow-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-white font-medium text-lg">Multi-Agent Architecture</div>
                  <div className="text-gray-300 text-base">CMO orchestrating 8 medical specialists</div>
                </div>
              </div>
            </div>
            
            <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
              <div className="flex items-start gap-3">
                <Activity className="w-6 h-6 text-yellow-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-white font-medium text-lg">Progressive Disclosure</div>
                  <div className="text-gray-300 text-base">Results based on query complexity</div>
                </div>
              </div>
            </div>
            
            <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
              <div className="flex items-start gap-3">
                <Brain className="w-6 h-6 text-yellow-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-white font-medium text-lg">Real-time Visualization</div>
                  <div className="text-gray-300 text-base">Live specialist collaboration</div>
                </div>
              </div>
            </div>
            
            <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
              <div className="flex items-start gap-3">
                <Layers className="w-6 h-6 text-yellow-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-white font-medium text-lg">Thread Management</div>
                  <div className="text-gray-300 text-base">Health consultation history</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Column 2: Reference Documents */}
        <div className="flex-1 bg-gradient-to-b from-blue-500/20 to-cyan-500/20 rounded-xl p-6 border border-blue-500/30">
          {/* Category Label */}
          <div className="text-center mb-3">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-500/20 text-blue-300 border border-blue-500/30">
              BEST PRACTICES / PATTERNS
            </span>
          </div>
          
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full mx-auto mb-4 flex items-center justify-center">
              <BookOpen className="w-9 h-9 text-white" />
            </div>
            <h3 className="text-3xl font-bold text-blue-300 mb-2">Context Documents</h3>
            <p className="text-gray-300 text-base">Knowledge base for informed decisions</p>
          </div>
          
          <div className="space-y-3">
            <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
              <div className="flex items-start gap-3">
                <Building className="w-6 h-6 text-blue-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-white font-medium text-lg">Anthropic Multi-Agent Blog</div>
                  <div className="text-gray-300 text-base">Orchestrator pattern blueprint</div>
                </div>
              </div>
            </div>
            
            <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
              <div className="flex items-start gap-3">
                <Database className="w-6 h-6 text-blue-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-white font-medium text-lg">Domain Requirements</div>
                  <div className="text-gray-300 text-base">Health-specific data types</div>
                </div>
              </div>
            </div>
            
            <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
              <div className="flex items-start gap-3">
                <Code className="w-6 h-6 text-blue-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-white font-medium text-lg">Tool Interface Docs</div>
                  <div className="text-gray-300 text-base">Pre-built health data access</div>
                </div>
              </div>
            </div>
            
            <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
              <div className="flex items-start gap-3">
                <Layout className="w-6 h-6 text-blue-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-white font-medium text-lg">Visual Mockups</div>
                  <div className="text-gray-300 text-base">Target UI/UX examples</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Column 3: Expected Artifacts */}
        <div className="flex-1 bg-gradient-to-b from-purple-500/20 to-pink-500/20 rounded-xl p-6 border border-purple-500/30">
          {/* Category Label */}
          <div className="text-center mb-3">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-500/20 text-purple-300 border border-purple-500/30">
              REQUESTED OUTPUTS
            </span>
          </div>
          
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full mx-auto mb-4 flex items-center justify-center">
              <Package className="w-9 h-9 text-white" />
            </div>
            <h3 className="text-3xl font-bold text-purple-300 mb-2">Expected Deliverables</h3>
            <p className="text-gray-300 text-base">Complete specs for UX Designer Agent and Claude Code</p>
          </div>
          
          <div className="space-y-3">
            <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
              <div className="flex items-start gap-3">
                <FileText className="w-6 h-6 text-purple-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-white font-medium text-lg">PRD Document</div>
                  <div className="text-gray-300 text-base">Production features defined</div>
                </div>
              </div>
            </div>
            
            <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
              <div className="flex items-start gap-3">
                <Building className="w-6 h-6 text-purple-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-white font-medium text-lg">System Architecture</div>
                  <div className="text-gray-300 text-base">Medical team structure</div>
                </div>
              </div>
            </div>
            
            <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
              <div className="flex items-start gap-3">
                <Code className="w-6 h-6 text-purple-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-white font-medium text-lg">API Specifications</div>
                  <div className="text-gray-300 text-base">Health data endpoints</div>
                </div>
              </div>
            </div>
            
            <div className="bg-white/10 rounded-lg p-4 backdrop-blur-sm">
              <div className="flex items-start gap-3">
                <Database className="w-6 h-6 text-purple-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-white font-medium text-lg">Data Models</div>
                  <div className="text-gray-300 text-base">Health information schemas</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Summary */}
      <div className="text-center mt-8">
        <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-xl p-4 border border-blue-500/30 max-w-5xl mx-auto">
          <p className="text-lg text-white whitespace-nowrap">
            <span className="text-yellow-400 font-bold">Core requirements + Context docs</span> → 
            <span className="text-gray-300"> PM Agent transforms into </span> → 
            <span className="text-purple-400 font-bold">7 comprehensive deliverables</span>
          </p>
        </div>
      </div>
    </div>
  );
};

export default PMAgentPromptVisual;