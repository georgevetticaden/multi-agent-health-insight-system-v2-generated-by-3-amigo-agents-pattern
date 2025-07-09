import React, { useState, useEffect } from 'react';
import { FileText, Code, Palette, User, ArrowRight, Package, Layers, Layout, ArrowDown, Database, Globe, Zap, Shield } from 'lucide-react';

const ThreeAmigosPipeline = () => {
  const [buildStep, setBuildStep] = useState(0);
  const maxSteps = 4;

  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.key === 'ArrowRight' && buildStep < maxSteps) {
        setBuildStep(prev => prev + 1);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [buildStep]);

  return (
    <div className="w-full bg-gradient-to-br from-slate-900 via-blue-900 to-purple-900 p-8 overflow-x-auto">
      {/* Title and Subtitle Section - Always visible */}
      <div className="text-center mb-8">
        <h2 className="text-5xl font-bold mb-4">
          <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            The 3 Amigos Pipeline: From Vision to Implementation
          </span>
        </h2>
        <p className="text-2xl text-gray-200 font-medium max-w-6xl mx-auto">
          From initial vision to working system—how three AI agents collaborate to build enterprise software
        </p>
      </div>

      <div className="min-w-max mx-auto">
        {/* Top Row: Product Owner, PM Agent, UX Agent */}
        <div className="flex items-stretch justify-center gap-8 mb-4">
          {/* Column 1: Product Owner Input - Build step 1 */}
          <div 
            className="bg-gradient-to-b from-yellow-500/20 to-orange-500/20 rounded-xl p-6 border border-yellow-500/30 w-80 transition-all duration-700 ease-out"
            style={{ 
              minHeight: '360px',
              opacity: buildStep >= 1 ? 1 : 0,
              transform: buildStep >= 1 ? 'translateY(0)' : 'translateY(20px)'
            }}
          >
            <div className="text-center mb-4">
              <div className="w-20 h-20 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-full mx-auto mb-4 flex items-center justify-center">
                <User className="w-12 h-12 text-white" />
              </div>
              <h3 className="text-3xl font-bold text-yellow-300">Product Owner</h3>
              <p className="text-gray-300 text-lg mt-1">Vision & Domain Knowledge</p>
            </div>
            
            <div className="bg-yellow-500/10 rounded-lg p-2 mb-3">
              <p className="text-yellow-300 font-bold text-xl text-center">📁 Provides 5 documents to PM Agent:</p>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-white/10 rounded-lg p-3">
                <FileText className="w-8 h-8 text-yellow-400 mb-1" />
                <div className="text-white font-medium text-lg">Domain Requirements</div>
                <div className="text-gray-300 text-lg">Health system specs</div>
              </div>
              
              <div className="bg-white/10 rounded-lg p-3">
                <FileText className="w-6 h-6 text-yellow-400 mb-1" />
                <div className="text-white font-medium text-lg">Architecture Brief</div>
                <div className="text-gray-300 text-lg">Multi-agent approach</div>
              </div>
              
              <div className="bg-white/10 rounded-lg p-3">
                <FileText className="w-6 h-6 text-yellow-400 mb-1" />
                <div className="text-white font-medium text-lg">Tool Interface</div>
                <div className="text-gray-300 text-lg">Pre-built tools</div>
              </div>
              
              <div className="bg-white/10 rounded-lg p-3">
                <FileText className="w-6 h-6 text-yellow-400 mb-1" />
                <div className="text-white font-medium text-lg">+ 2 more</div>
                <div className="text-gray-300 text-lg">Visual refs, Research</div>
              </div>
            </div>
          </div>

          {/* Arrow 1 - Build step 2a */}
          <div 
            className="flex flex-col items-center justify-center pt-20 transition-all duration-500 ease-out"
            style={{
              opacity: buildStep >= 2 ? 1 : 0,
              transform: buildStep >= 2 ? 'scale(1)' : 'scale(0.8)'
            }}
          >
            <p className="text-yellow-400 text-lg font-medium mb-1">5 documents</p>
            <ArrowRight className="w-12 h-12 text-yellow-400" />
            <p className="text-gray-400 text-lg mt-1">as input</p>
          </div>

          {/* Column 2: PM Agent - Build step 2b */}
          <div 
            className="bg-gradient-to-b from-blue-500/20 to-cyan-500/20 rounded-xl p-6 border border-blue-500/30 w-80 transition-all duration-700 ease-out"
            style={{ 
              minHeight: '360px',
              opacity: buildStep >= 2 ? 1 : 0,
              transform: buildStep >= 2 ? 'translateY(0)' : 'translateY(20px)',
              transitionDelay: '200ms'
            }}
          >
            <div className="text-center mb-4">
              <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full mx-auto mb-4 flex items-center justify-center">
                <Package className="w-12 h-12 text-white" />
              </div>
              <h3 className="text-3xl font-bold text-blue-300">PM Agent</h3>
              <p className="text-gray-300 text-lg mt-1">Requirements & Architecture</p>
            </div>
            
            <div className="bg-blue-500/10 rounded-lg p-2 mb-3">
              <p className="text-blue-300 font-bold text-xl text-center">✨ Creates 7 artifacts for UX Agent:</p>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-white/10 rounded-lg p-3">
                <FileText className="w-8 h-8 text-blue-400 mb-1" />
                <div className="text-white font-medium text-lg">PRD.md</div>
                <div className="text-gray-300 text-lg">12-page requirements</div>
              </div>
              
              <div className="bg-white/10 rounded-lg p-3">
                <Code className="w-8 h-8 text-blue-400 mb-1" />
                <div className="text-white font-medium text-lg">Architecture</div>
                <div className="text-gray-300 text-lg">Orchestration patterns</div>
              </div>
              
              <div className="bg-white/10 rounded-lg p-3">
                <Code className="w-6 h-6 text-blue-400 mb-1" />
                <div className="text-white font-medium text-lg">API Specs</div>
                <div className="text-gray-300 text-lg">23 endpoints</div>
              </div>
              
              <div className="bg-white/10 rounded-lg p-3">
                <FileText className="w-6 h-6 text-blue-400 mb-1" />
                <div className="text-white font-medium text-lg">+ 3 more</div>
                <div className="text-gray-300 text-lg">Data models, stories...</div>
              </div>
            </div>
          </div>

          {/* Arrow 2 - Build step 3a */}
          <div 
            className="flex flex-col items-center justify-center pt-20 transition-all duration-500 ease-out"
            style={{
              opacity: buildStep >= 3 ? 1 : 0,
              transform: buildStep >= 3 ? 'scale(1)' : 'scale(0.8)'
            }}
          >
            <p className="text-blue-400 text-lg font-medium mb-1">7 artifacts</p>
            <ArrowRight className="w-12 h-12 text-blue-400" />
            <p className="text-gray-400 text-lg mt-1">as input</p>
          </div>

          {/* Column 3: UX Agent - Build step 3b */}
          <div 
            className="bg-gradient-to-b from-purple-500/20 to-pink-500/20 rounded-xl p-6 border border-purple-500/30 w-80 transition-all duration-700 ease-out"
            style={{ 
              minHeight: '360px',
              opacity: buildStep >= 3 ? 1 : 0,
              transform: buildStep >= 3 ? 'translateY(0)' : 'translateY(20px)',
              transitionDelay: '200ms'
            }}
          >
            <div className="text-center mb-4">
              <div className="w-20 h-20 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full mx-auto mb-4 flex items-center justify-center">
                <Palette className="w-12 h-12 text-white" />
              </div>
              <h3 className="text-3xl font-bold text-purple-300">UX Agent</h3>
              <p className="text-gray-300 text-lg mt-1">Design & Experience</p>
            </div>
            
            <div className="bg-purple-500/10 rounded-lg p-2 mb-3">
              <p className="text-purple-300 font-bold text-xl text-center">✨ Creates 8 artifacts for Claude Code:</p>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-white/10 rounded-lg p-3">
                <Palette className="w-8 h-8 text-purple-400 mb-1" />
                <div className="text-white font-medium text-lg">Design System</div>
                <div className="text-gray-300 text-lg">Medical UI language</div>
              </div>
              
              <div className="bg-white/10 rounded-lg p-3">
                <Layout className="w-8 h-8 text-purple-400 mb-1" />
                <div className="text-white font-medium text-lg">Components</div>
                <div className="text-gray-300 text-lg">23 React specs</div>
              </div>
              
              <div className="bg-white/10 rounded-lg p-3">
                <Code className="w-8 h-8 text-purple-400 mb-1" />
                <div className="text-white font-medium text-lg">Prototypes</div>
                <div className="text-gray-300 text-lg">2 HTML demos</div>
              </div>
              
              <div className="bg-white/10 rounded-lg p-3">
                <FileText className="w-8 h-8 text-purple-400 mb-1" />
                <div className="text-white font-medium text-lg">+ 4 more</div>
                <div className="text-gray-300 text-lg">Visuals, animations...</div>
              </div>
            </div>
          </div>
        </div>

        {/* Arrows pointing down with labels - Build step 4 */}
        <div 
          className="flex items-start justify-center gap-8 mb-4 transition-all duration-700 ease-out"
          style={{ 
            marginTop: '-10px',
            opacity: buildStep >= 4 ? 1 : 0,
            transform: buildStep >= 4 ? 'translateY(0)' : 'translateY(-20px)'
          }}
        >
          {/* Arrow under Product Owner */}
          <div className="w-80 flex justify-center" style={{ paddingRight: '20px' }}>
            <div className="flex flex-col items-center">
              <ArrowDown className="w-12 h-12 text-yellow-400" />
              <p className="text-yellow-400 text-lg font-medium mt-1">5 inputs</p>
            </div>
          </div>
          
          {/* Spacer for horizontal arrow */}
          <div className="w-12"></div>
          
          {/* Arrow under PM Agent */}
          <div className="w-80 flex justify-center">
            <div className="flex flex-col items-center">
              <ArrowDown className="w-12 h-12 text-blue-400" />
              <p className="text-blue-400 text-lg font-medium mt-1">7 outputs</p>
            </div>
          </div>
          
          {/* Spacer for horizontal arrow */}
          <div className="w-12"></div>
          
          {/* Arrow under UX Agent */}
          <div className="w-80 flex justify-center" style={{ paddingLeft: '20px' }}>
            <div className="flex flex-col items-center">
              <ArrowDown className="w-12 h-12 text-purple-400" />
              <p className="text-purple-400 text-lg font-medium mt-1">8 outputs</p>
            </div>
          </div>
        </div>

        {/* Bottom Row: Claude Code - Build step 4 */}
        <div className="flex justify-center">
          <div 
            className="bg-gradient-to-b from-green-500/20 to-emerald-500/20 rounded-xl p-6 border border-green-500/30 mb-8 transition-all duration-1000 ease-out"
            style={{ 
              width: '74rem',
              opacity: buildStep >= 4 ? 1 : 0,
              transform: buildStep >= 4 ? 'translateY(0)' : 'translateY(30px)',
              transitionDelay: '300ms'
            }}
          >
            {/* First Row: Claude Code, Inputs, and Outputs */}
            <div className="grid grid-cols-3 gap-6 mb-6">
              {/* Left: Claude Code Identity */}
              <div className="flex items-center gap-4">
                <div className="w-20 h-20 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center">
                  <Code className="w-12 h-12 text-white" />
                </div>
                <div>
                  <h3 className="text-3xl font-bold text-green-300">Claude Code</h3>
                  <p className="text-gray-300 text-lg">Implementation Engine</p>
                </div>
              </div>

              {/* Center: Total Artifacts */}
              <div className="bg-gradient-to-r from-green-600/20 to-emerald-600/20 rounded-lg px-6 py-3 flex items-center justify-center">
                <div className="text-center">
                  <div className="flex items-center gap-3">
                    <div>
                      <div className="text-4xl font-bold text-green-300">20+</div>
                      <div className="text-white text-base">Artifacts</div>
                    </div>
                    <div className="text-left">
                      <p className="text-green-300 font-bold text-lg">📥 Receives all inputs</p>
                      <p className="text-gray-300 text-base">5 from PO + 7 from PM + 8 from UX</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right: What Claude Code Creates */}
              <div className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 rounded-lg px-6 py-3">
                <div className="text-lg font-bold text-purple-300 mb-2">🚀 Claude Code creates:</div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-base">
                  <div className="flex items-center gap-2">
                    <Database className="w-5 h-5 text-purple-400" />
                    <span className="text-white">Multi-Agent Backend</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Globe className="w-5 h-5 text-purple-400" />
                    <span className="text-white">React Frontend</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Zap className="w-5 h-5 text-purple-400" />
                    <span className="text-white">SSE Streaming</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Shield className="w-5 h-5 text-purple-400" />
                    <span className="text-white">Error Handling</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Second Row: CLAUDE.md as Implementation Guide */}
            <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-lg p-4">
              <div className="flex items-center gap-8">
                <div className="flex items-center gap-3">
                  <FileText className="w-10 h-10 text-blue-400" />
                  <div>
                    <div className="text-xl font-bold text-blue-300">CLAUDE.md - The Implementation Guide</div>
                    <div className="text-gray-300 text-lg">Guides Claude Code through the rich artifacts by specifying:</div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-xl">
                  <div className="flex items-center gap-2">
                    <span className="text-yellow-400 font-bold">1.</span>
                    <span className="text-gray-300">Review PO inputs</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-blue-400 font-bold">2.</span>
                    <span className="text-gray-300">Study PM outputs</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-purple-400 font-bold">3.</span>
                    <span className="text-gray-300">Examine UX designs</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-green-400 font-bold">4.</span>
                    <span className="text-gray-300">Apply patterns</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default ThreeAmigosPipeline;