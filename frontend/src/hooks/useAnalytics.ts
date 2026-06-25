import { useEffect, useRef } from 'react';

export interface AnalyticsEvent {
  event_name: string;
  properties?: Record<string, any>;
  url?: string;
}

// Global queue to survive component unmounts
const eventQueue: AnalyticsEvent[] = [];

export function useAnalytics() {
  const isFlushing = useRef(false);

  const trackEvent = (event_name: string, properties?: Record<string, any>) => {
    eventQueue.push({
      event_name,
      properties,
      url: typeof window !== 'undefined' ? window.location.pathname : '',
    });
  };

  const getBackendUrl = () => {
    if (typeof window !== 'undefined') {
      const override = localStorage.getItem('UPHILL_API_URL_OVERRIDE');
      if (override) return override;
    }
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  };

  const flushEvents = async () => {
    if (eventQueue.length === 0 || isFlushing.current) return;
    
    isFlushing.current = true;
    const batch = [...eventQueue];
    eventQueue.length = 0; // Clear queue
    
    try {
      const token = localStorage.getItem('uphill_session_token');
      const backendUrl = getBackendUrl();
      
      const response = await fetch(`${backendUrl}/api/analytics/track_batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          events: batch,
          session_id: localStorage.getItem('uphill_session_id')
        })
      });
      
      if (!response.ok) {
        // If it failed, put them back in the queue
        eventQueue.unshift(...batch);
      }
    } catch (e) {
      eventQueue.unshift(...batch);
    } finally {
      isFlushing.current = false;
    }
  };

  useEffect(() => {
    // Generate a simple session ID if one doesn't exist
    if (typeof window !== 'undefined' && !localStorage.getItem('uphill_session_id')) {
      localStorage.setItem('uphill_session_id', Math.random().toString(36).substring(2, 15));
    }

    // Flush every 5 seconds
    const interval = setInterval(flushEvents, 5000);
    
    // Also flush on visibility change (e.g. user leaves page)
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        if (eventQueue.length > 0) {
           const token = localStorage.getItem('uphill_session_token');
           const backendUrl = localStorage.getItem('UPHILL_API_URL_OVERRIDE') || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
           fetch(`${backendUrl}/api/analytics/track_batch`, {
             method: 'POST',
             headers: {
               'Content-Type': 'application/json',
               ...(token ? { 'Authorization': `Bearer ${token}` } : {})
             },
             body: JSON.stringify({
               events: eventQueue,
               session_id: localStorage.getItem('uphill_session_id')
             }),
             keepalive: true
           }).catch(() => {});
           eventQueue.length = 0;
        }
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  return { trackEvent };
}
