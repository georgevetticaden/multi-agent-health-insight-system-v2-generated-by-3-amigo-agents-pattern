import React, { useState, useEffect } from 'react';
import { Users, BarChart3 } from 'lucide-react';

interface Tab {
  id: string;
  label: string;
  icon: React.ReactNode;
  isVisible: boolean;
}

interface TabContainerProps {
  activeTab?: string;
  onTabChange?: (tabId: string) => void;
  children: React.ReactNode;
  showVisualizationTab?: boolean;
}

const TabContainer: React.FC<TabContainerProps> = ({
  activeTab: controlledActiveTab,
  onTabChange,
  children,
  showVisualizationTab = false
}) => {
  const [internalActiveTab, setInternalActiveTab] = useState('medical-team');
  
  // Use controlled or internal state
  const activeTab = controlledActiveTab ?? internalActiveTab;
  
  const tabs: Tab[] = [
    {
      id: 'medical-team',
      label: 'Medical Team',
      icon: <Users className="w-4 h-4" />,
      isVisible: true
    },
    {
      id: 'visualization',
      label: 'Visualization',
      icon: <BarChart3 className="w-4 h-4" />,
      isVisible: showVisualizationTab
    }
  ];

  const handleTabClick = (tabId: string) => {
    if (onTabChange) {
      onTabChange(tabId);
    } else {
      setInternalActiveTab(tabId);
    }
  };

  // Auto-switch to visualization tab when it becomes visible
  useEffect(() => {
    if (showVisualizationTab && activeTab !== 'visualization') {
      handleTabClick('visualization');
    }
  }, [showVisualizationTab]);

  const visibleTabs = tabs.filter(tab => tab.isVisible);

  return (
    <div className="flex flex-col h-full">
      {/* Tab Navigation */}
      <div className="flex bg-gray-50 border-b border-gray-200">
        {visibleTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => handleTabClick(tab.id)}
            className={`
              flex-1 px-4 py-3 flex items-center justify-center gap-2
              font-medium text-sm transition-all duration-200 relative
              ${activeTab === tab.id
                ? 'text-blue-600 bg-white border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
              }
            `}
          >
            {tab.icon}
            <span>{tab.label}</span>
            {activeTab === tab.id && (
              <div 
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600"
                style={{ 
                  animation: 'slideIn 0.2s ease-out' 
                }}
              />
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {React.Children.map(children, (child, index) => {
          if (!React.isValidElement(child)) return null;
          
          const tabId = visibleTabs[index]?.id;
          const isActive = tabId === activeTab;
          
          return (
            <div
              className={`
                h-full transition-all duration-200
                ${isActive ? 'block opacity-100' : 'hidden opacity-0'}
              `}
              style={{
                animation: isActive ? 'tabSlideIn 0.2s ease-out' : undefined
              }}
            >
              {React.isValidElement(child) && child.type && typeof child.type !== 'string'
                ? React.cloneElement(child as React.ReactElement<any>, { isVisible: isActive })
                : child}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TabContainer;