'use client';
import { useAnalytics } from '@/hooks/useAnalytics';
import { usePathname } from 'next/navigation';
import { useEffect } from 'react';

export default function AnalyticsProvider() {
  const { trackEvent } = useAnalytics();
  const pathname = usePathname();

  useEffect(() => {
    trackEvent('page_view', { path: pathname });
  }, [pathname, trackEvent]);

  return null;
}
