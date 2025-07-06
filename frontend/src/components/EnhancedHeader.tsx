import React from 'react';
import { Settings, Bell, Brain, RefreshCw } from 'lucide-react';

interface EnhancedHeaderProps {
  userName?: string;
  lastCheckup?: string;
  onSettingsClick?: () => void;
  onResetClick?: () => void;
}

const EnhancedHeader: React.FC<EnhancedHeaderProps> = ({ 
  userName = 'User', 
  lastCheckup = 'N/A',
  onSettingsClick,
  onResetClick 
}) => {
  return (
    <header className="bg-white/80 backdrop-blur-sm border-b border-gray-200">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-sm">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Health Insight Assistant</h1>
            <p className="text-sm text-gray-600">Powered by Multi-Agent AI • Snowflake Cortex</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors relative">
            <Bell className="w-5 h-5 text-gray-600" />
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
          </button>
          
          <div className="flex items-center gap-3 bg-gray-50 px-4 py-2 rounded-xl">
            <div className="text-right">
              <p className="text-sm font-medium text-gray-900">{userName}</p>
              <p className="text-xs text-gray-500">Last checkup: {lastCheckup}</p>
            </div>
            <div 
              className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full flex items-center justify-center cursor-pointer hover:opacity-80 transition-opacity"
              onClick={onResetClick}
              title="Click to reset demo"
            >
              <span className="text-white font-medium">
                {userName.split(' ').map(n => n[0]).join('').toUpperCase()}
              </span>
            </div>
          </div>
          
          <button 
            onClick={onSettingsClick}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Settings className="w-5 h-5 text-gray-600" />
          </button>
        </div>
      </div>
    </header>
  );
};

export default EnhancedHeader;