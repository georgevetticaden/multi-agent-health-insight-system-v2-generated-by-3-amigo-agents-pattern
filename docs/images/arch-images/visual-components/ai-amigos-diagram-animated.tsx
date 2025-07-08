import React, { useState, useEffect } from 'react';
import {
  User,
  Code2,
  Palette,
  Users
} from 'lucide-react';

const AIAmigosHero = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const maxSteps = 4;

  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.key === 'ArrowRight' && currentStep < maxSteps) {
        setCurrentStep(currentStep + 1);
      } else if (e.key === 'ArrowLeft' && currentStep > 0) {
        setCurrentStep(currentStep - 1);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [currentStep]);

  return (
    <div className="w-full h-full bg-gradient-to-br from-slate-900 via-blue-900 to-purple-900 p-4 overflow-auto relative">
      <div className="max-w-7xl mx-auto pb-8">
        
        {/* Header - Always visible */}
        <div className="text-center mb-4">
          <h1 className="text-5xl font-bold mb-4 text-center">
            <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Meet the 3 Amigo Agents:
            </span>
            <br />
            <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              The Future of Product Development
            </span>
          </h1>
          <p className="text-xl text-gray-300 mb-2">
            One Product Owner, Three AI Specialists, Infinite Possibilities
          </p>
          <p className="text-lg text-gray-400 italic">
            Your Complete AI Product Team Working in Perfect Harmony
          </p>
        </div>

        {/* Bicycle Wheel Layout */}
        <div className="relative mx-auto mt-32" style={{ width: '1008px', height: '1050px' }}>
          {/* Outer Circle - Always visible */}
          <svg className="absolute inset-0 w-full h-full" style={{ overflow: 'visible' }}>
            {/* Main circle */}
            <circle 
              cx="504" 
              cy="504" 
              r="504" 
              fill="none" 
              stroke="rgba(59, 130, 246, 0.5)" 
              strokeWidth="4" 
            />
            
            {/* Arrow indicators with labels - conditionally visible */}
            {currentStep >= 1 && (
              <>
                {/* Arrow 1: PM to Designer - 2 o'clock position */}
                <g transform="translate(940, 252)">
                  <text x="0" y="0" fill="#3b82f6" fontSize="55" fontWeight="bold" textAnchor="middle" dominantBaseline="middle" transform="rotate(60)">
                    &gt;
                  </text>
                </g>
                {/* Label for Arrow 1 */}
                <g transform="translate(870, 285)">
                  <text fill="#60a5fa" fontSize="18" fontWeight="bold" textAnchor="middle" transform="rotate(60)">
                    <tspan x="0" dy="-10">Requirements in</tspan>
                    <tspan x="0" dy="20">Natural Language</tspan>
                  </text>
                </g>
              </>
            )}
            
            {currentStep >= 2 && (
              <>
                {/* Arrow 2: Designer to Claude Code - 6 o'clock position */}
                <g transform="translate(504, 1005)">
                  <text x="0" y="0" fill="#3b82f6" fontSize="55" fontWeight="bold" textAnchor="middle" dominantBaseline="middle" transform="rotate(180)">
                    &gt;
                  </text>
                  <text x="0" y="-40" fill="#a78bfa" fontSize="18" fontWeight="bold" textAnchor="middle">
                    Visual Specs & Components
                  </text>
                </g>
              </>
            )}
            
            {currentStep >= 3 && (
              <>
                {/* Arrow 3: Claude Code back to PM - 10 o'clock position */}
                <g transform="translate(68, 252)">
                  <text x="0" y="0" fill="#3b82f6" fontSize="55" fontWeight="bold" textAnchor="middle" dominantBaseline="middle" transform="rotate(-60)">
                    &gt;
                  </text>
                </g>
                {/* Label for Arrow 3 */}
                <g transform="translate(128, 285)">
                  <text fill="#34d399" fontSize="18" fontWeight="bold" textAnchor="middle" transform="rotate(-60)">
                    <tspan x="0" dy="-10">Working Features</tspan>
                    <tspan x="0" dy="20">for Validation</tspan>
                  </text>
                </g>
              </>
            )}
            
            {/* Workflow Step Labels - conditionally visible */}
            {currentStep >= 1 && (
              /* Step 1: Between Product Owner and PM Agent */
              <g transform="translate(504, 280)">
                <rect x="-130" y="-65" width="260" height="160" rx="8" fill="rgba(96, 165, 250, 0.1)" stroke="rgba(96, 165, 250, 0.3)" strokeWidth="1"/>
                <text fill="#60a5fa" fontSize="22" fontWeight="bold" textAnchor="middle">
                  <tspan x="0" dy="-40">1. Define & Plan</tspan>
                  <tspan x="0" dy="35" fontSize="16" fill="#cbd5e1">Product Owner works with</tspan>
                  <tspan x="0" dy="20" fontSize="16" fill="#cbd5e1">PM Agent to define problem</tspan>
                  <tspan x="0" dy="20" fontSize="16" fill="#cbd5e1">statement, business case,</tspan>
                  <tspan x="0" dy="20" fontSize="16" fill="#cbd5e1">requirements, and user stories</tspan>
                </text>
              </g>
            )}
            
            {currentStep >= 2 && (
              /* Step 2: Between PM Agent and UX Designer */
              <g transform="translate(735, 504)">
                <rect x="-105" y="-75" width="210" height="180" rx="8" fill="rgba(167, 139, 250, 0.1)" stroke="rgba(167, 139, 250, 0.3)" strokeWidth="1"/>
                <text fill="#a78bfa" fontSize="22" fontWeight="bold" textAnchor="middle">
                  <tspan x="0" dy="-50">2. Design & Iterate</tspan>
                  <tspan x="0" dy="35" fontSize="16" fill="#cbd5e1">Requirements flow to</tspan>
                  <tspan x="0" dy="20" fontSize="16" fill="#cbd5e1">Designer Agent to create</tspan>
                  <tspan x="0" dy="20" fontSize="16" fill="#cbd5e1">mockups, UI components,</tspan>
                  <tspan x="0" dy="20" fontSize="16" fill="#cbd5e1">and style guides. PO</tspan>
                  <tspan x="0" dy="20" fontSize="16" fill="#cbd5e1">iterates until satisfied</tspan>
                </text>
              </g>
            )}
            
            {currentStep >= 3 && (
              /* Step 3: Between Claude Code Agent and PM Agent */
              <g transform="translate(273, 504)">
                <rect x="-105" y="-75" width="210" height="180" rx="8" fill="rgba(52, 211, 153, 0.1)" stroke="rgba(52, 211, 153, 0.3)" strokeWidth="1"/>
                <text fill="#34d399" fontSize="22" fontWeight="bold" textAnchor="middle">
                  <tspan x="0" dy="-50">3. Build & Test</tspan>
                  <tspan x="0" dy="35" fontSize="16" fill="#cbd5e1">UX artifacts guide Claude</tspan>
                  <tspan x="0" dy="20" fontSize="16" fill="#cbd5e1">Code Agent to implement</tspan>
                  <tspan x="0" dy="20" fontSize="16" fill="#cbd5e1">the UI and design backend</tspan>
                  <tspan x="0" dy="20" fontSize="16" fill="#cbd5e1">agent architecture to</tspan>
                  <tspan x="0" dy="20" fontSize="16" fill="#cbd5e1">power the app</tspan>
                </text>
              </g>
            )}
          </svg>
            
          {/* Center Hub - Product Owner - Always visible */}
          <div className="absolute" style={{ 
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -30%)'
          }}>
            <div className="flex flex-col items-center">
              {/* Glow effect */}
              <div className="absolute -inset-8 bg-yellow-500/10 rounded-full blur-2xl"></div>
              <div className="w-40 h-40 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-full flex items-center justify-center shadow-2xl border-4 border-yellow-400/50 relative z-10 transition-transform hover:scale-105">
                <User className="w-24 h-24 text-white" />
              </div>
              <div className="text-xl font-semibold text-yellow-300 bg-yellow-600/20 px-6 py-3 rounded-lg relative z-10 mt-4">👤 Product Owner</div>
              <p className="text-lg text-gray-300 mt-2 relative z-10">Human</p>
              <p className="text-base text-gray-400 relative z-10">Vision & Direction</p>
            </div>
          </div>
          
          {/* Compelling text - visible at step 4 - positioned absolutely */}
          {currentStep >= 4 && (
            <div className="absolute" style={{ 
              top: '75%',
              left: '50%',
              transform: 'translateX(-50%)'
            }}>
              <div className="text-center max-w-3xl">
                <p className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-3">
                  Product Owner Orchestrates the AI Triad
                </p>
                <p className="text-lg text-gray-300 leading-relaxed">
                  One Human Vision Commands Three Specialized Agents<br />
                  Transforming Ideas into Reality
                </p>
              </div>
            </div>
          )}
            
          {/* PM Agent - Top (12 o'clock) - visible at step 1 */}
          {currentStep >= 1 && (
            <div className="absolute" style={{ 
              top: '-96px', 
              left: '50%', 
              transform: 'translateX(-50%)' 
            }}>
              <div className="w-64 h-48 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl flex flex-col items-center justify-center shadow-xl border-4 border-blue-400/50 transition-transform hover:scale-105 p-4">
                <Users className="w-12 h-12 text-white mb-2" />
                <div className="text-xl font-semibold text-white">🤖 PM Agent</div>
                <p className="text-2xl font-bold text-yellow-300 mt-1 whitespace-nowrap">Product Manager</p>
                <p className="text-base text-white/80 text-center">Requirements & Roadmap</p>
              </div>
            </div>
          )}
          
          {/* UX Designer - Right (3 o'clock) - visible at step 2 */}
          {currentStep >= 2 && (
            <div className="absolute" style={{ 
              top: '50%',
              right: '-108px',
              transform: 'translateY(-50%)'
            }}>
              <div className="w-64 h-48 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex flex-col items-center justify-center shadow-xl border-4 border-purple-400/50 transition-transform hover:scale-105 p-4">
                <Palette className="w-12 h-12 text-white mb-2" />
                <div className="text-xl font-semibold text-white">🤖 Designer Agent</div>
                <p className="text-2xl font-bold text-yellow-300 mt-1">UX Designer</p>
                <p className="text-base text-white/80 text-center">Design & Experience</p>
              </div>
            </div>
          )}
          
          {/* Engineer - Left (9 o'clock) - visible at step 3 */}
          {currentStep >= 3 && (
            <div className="absolute" style={{ 
              top: '50%',
              left: '-108px',
              transform: 'translateY(-50%)'
            }}>
              <div className="w-64 h-48 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl flex flex-col items-center justify-center shadow-xl border-4 border-green-400/50 transition-transform hover:scale-105 p-4">
                <Code2 className="w-12 h-12 text-white mb-2" />
                <div className="text-xl font-semibold text-white whitespace-nowrap">🤖 Claude Code Agent</div>
                <p className="text-2xl font-bold text-yellow-300 mt-1">Engineer</p>
                <p className="text-base text-white/80 text-center whitespace-nowrap">Implementation & Code</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AIAmigosHero;