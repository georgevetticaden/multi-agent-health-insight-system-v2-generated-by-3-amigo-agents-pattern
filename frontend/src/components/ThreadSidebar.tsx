import React, { useState } from 'react';
import { Plus, Search, Calendar, Pill, FileText, ChevronRight } from 'lucide-react';

export interface HealthThread {
  id: string;
  title: string;
  summary: string;
  timestamp: Date;
  category: 'lab' | 'medication' | 'condition' | 'general';
  unread?: boolean;
}

interface ThreadSidebarProps {
  threads: HealthThread[];
  activeThreadId?: string;
  onThreadSelect: (id: string) => void;
  onNewThread: () => void;
  onDeleteThread?: (id: string) => void;
}

const ThreadSidebar: React.FC<ThreadSidebarProps> = ({
  threads,
  activeThreadId,
  onThreadSelect,
  onNewThread,
  onDeleteThread
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const filteredThreads = threads.filter(thread => {
    const matchesSearch = thread.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         thread.summary.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = !selectedCategory || thread.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const groupThreadsByDate = (threads: HealthThread[]) => {
    const today = new Date();
    const thisWeek = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
    
    const groups: { [key: string]: HealthThread[] } = {
      'Today': [],
      'This Week': [],
      'Older': []
    };

    threads.forEach(thread => {
      const threadDate = new Date(thread.timestamp);
      if (threadDate.toDateString() === today.toDateString()) {
        groups['Today'].push(thread);
      } else if (threadDate > thisWeek) {
        groups['This Week'].push(thread);
      } else {
        groups['Older'].push(thread);
      }
    });

    return groups;
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'lab': return <FileText className="w-4 h-4" />;
      case 'medication': return <Pill className="w-4 h-4" />;
      case 'condition': return <Calendar className="w-4 h-4" />;
      default: return <ChevronRight className="w-4 h-4" />;
    }
  };

  const groupedThreads = groupThreadsByDate(filteredThreads);

  return (
    <aside className="w-80 bg-white/60 backdrop-blur-sm border-r border-gray-200 flex flex-col">
      {/* New Thread Button */}
      <div className="p-4 border-b border-gray-200">
        <button
          onClick={onNewThread}
          className="w-full bg-blue-500 hover:bg-blue-600 text-white px-4 py-3 rounded-xl transition-colors flex items-center justify-center gap-2 font-medium shadow-sm"
        >
          <Plus className="w-5 h-5" />
          New Health Conversation
        </button>
      </div>

      {/* Search */}
      <div className="p-4 border-b border-gray-200">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conversations..."
            className="w-full bg-white/80 border border-gray-300 pl-10 pr-4 py-2 rounded-lg placeholder-gray-500 outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Category Filters */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex gap-2 text-xs">
          <button
            onClick={() => setSelectedCategory(selectedCategory === 'lab' ? null : 'lab')}
            className={`flex-1 px-3 py-2 rounded-lg transition-colors border ${
              selectedCategory === 'lab' 
                ? 'bg-blue-50 text-blue-700 border-blue-300' 
                : 'bg-white hover:bg-gray-50 border-gray-300'
            }`}
          >
            Lab Results
          </button>
          <button
            onClick={() => setSelectedCategory(selectedCategory === 'medication' ? null : 'medication')}
            className={`flex-1 px-3 py-2 rounded-lg transition-colors border ${
              selectedCategory === 'medication' 
                ? 'bg-purple-50 text-purple-700 border-purple-300' 
                : 'bg-white hover:bg-gray-50 border-gray-300'
            }`}
          >
            Medications
          </button>
          <button
            onClick={() => setSelectedCategory(selectedCategory === 'condition' ? null : 'condition')}
            className={`flex-1 px-3 py-2 rounded-lg transition-colors border ${
              selectedCategory === 'condition' 
                ? 'bg-green-50 text-green-700 border-green-300' 
                : 'bg-white hover:bg-gray-50 border-gray-300'
            }`}
          >
            Conditions
          </button>
        </div>
      </div>

      {/* Thread List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {Object.entries(groupedThreads).map(([groupName, threads]) => (
          threads.length > 0 && (
            <div key={groupName}>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                {groupName}
              </h3>
              <div className="space-y-2">
                {threads.map(thread => (
                  <div
                    key={thread.id}
                    onClick={() => onThreadSelect(thread.id)}
                    className={`bg-white/80 px-4 py-3 rounded-lg cursor-pointer hover:bg-white transition-colors shadow-sm ${
                      activeThreadId === thread.id ? 'border-l-4 border-blue-500 shadow-md' : ''
                    } ${thread.unread ? 'border-l-4 border-orange-500' : ''}`}
                  >
                    <div className="flex items-start gap-2">
                      <div className="mt-0.5 text-gray-400">
                        {getCategoryIcon(thread.category)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-gray-900 mb-1 truncate">{thread.title}</h4>
                        <p className="text-sm text-gray-600 line-clamp-2">{thread.summary}</p>
                        <p className="text-xs text-gray-400 mt-1">
                          {new Date(thread.timestamp).toLocaleTimeString([], { 
                            hour: '2-digit', 
                            minute: '2-digit' 
                          })}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )
        ))}
      </div>
    </aside>
  );
};

export default ThreadSidebar;