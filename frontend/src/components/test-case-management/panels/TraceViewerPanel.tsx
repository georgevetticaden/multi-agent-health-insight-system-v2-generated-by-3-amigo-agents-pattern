import React, { useState, useEffect, useRef } from 'react';
import { Activity, Loader2, Maximize2, Minimize2 } from 'lucide-react';

interface TraceViewerPanelProps {
  traceId: string;
  onEventSelect?: (eventId: string) => void;
  selectedEvent?: string | null;
}

const TraceViewerPanel: React.FC<TraceViewerPanelProps> = ({
  traceId,
  onEventSelect,
  selectedEvent
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Handle iframe load
  useEffect(() => {
    const handleIframeLoad = () => {
      setIsLoading(false);
      
      // Set up communication with iframe
      if (iframeRef.current?.contentWindow) {
        // Send initial configuration
        iframeRef.current.contentWindow.postMessage({
          type: 'config',
          embedded: true,
          showHeader: false
        }, '*');
      }
    };

    if (iframeRef.current) {
      iframeRef.current.addEventListener('load', handleIframeLoad);
      return () => {
        iframeRef.current?.removeEventListener('load', handleIframeLoad);
      };
    }
  }, []);

  // Handle messages from iframe
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'event-selected' && onEventSelect) {
        onEventSelect(event.data.eventId);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [onEventSelect]);

  // Send selected event to iframe
  useEffect(() => {
    if (iframeRef.current?.contentWindow && selectedEvent) {
      iframeRef.current.contentWindow.postMessage({
        type: 'highlight-event',
        eventId: selectedEvent
      }, '*');
    }
  }, [selectedEvent]);

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const iframeUrl = `/api/traces/${traceId}/hierarchical?embedded=true&hideHeader=true&hideFilters=true&hideColumns=trace,duration&t=${Date.now()}`;

  return (
    <div className={`h-full flex flex-col ${isFullscreen ? 'fixed inset-0 z-50 bg-white' : ''}`}>

      {/* Trace Viewer */}
      <div className="flex-1 relative bg-gray-50 min-h-0">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white">
            <div className="text-center">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2" />
              <p className="text-gray-600">Loading trace...</p>
            </div>
          </div>
        )}
        
        <iframe
          ref={iframeRef}
          src={iframeUrl}
          className="absolute inset-0 w-full h-full border-0"
          title="Trace Viewer"
          sandbox="allow-scripts allow-same-origin"
        />
      </div>
    </div>
  );
};

export default TraceViewerPanel;