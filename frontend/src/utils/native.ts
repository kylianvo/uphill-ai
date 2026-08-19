import { Capacitor } from '@capacitor/core';
import { Haptics, ImpactStyle } from '@capacitor/haptics';

export const isNativePlatform = (): boolean => {
  return Capacitor.isNativePlatform();
};

export const getPlatform = (): string => {
  return Capacitor.getPlatform();
};

export const triggerHaptic = async (style: ImpactStyle = ImpactStyle.Light): Promise<void> => {
  if (isNativePlatform()) {
    try {
      await Haptics.impact({ style });
    } catch {
      // Gracefully fall back if device does not support haptics
    }
  }
};

export const getApiBaseUrl = (): string => {
  // 1. Check browser/webview localStorage override if available
  if (typeof window !== 'undefined' && typeof window.localStorage !== 'undefined') {
    try {
      const override = window.localStorage.getItem('UPHILL_API_URL_OVERRIDE');
      if (override) {
        return override.replace(/\/+$/, '');
      }
    } catch {
      // Ignore localStorage access errors
    }
  }

  // 2. Check build-time environment variable
  const envApiUrl =
    (typeof process !== 'undefined' && (process.env?.NEXT_PUBLIC_API_URL || process.env?.NEXT_PUBLIC_API_BASE_URL)) || '';
  if (envApiUrl) {
    return envApiUrl.replace(/\/+$/, '');
  }

  // 3. Handle Capacitor native mobile platform defaults
  if (isNativePlatform()) {
    const platform = getPlatform();
    // Android emulator host machine loopback
    if (platform === 'android') {
      return 'http://10.0.2.2:8000';
    }
    // iOS simulator / dev host
    return 'http://localhost:8000';
  }

  // 4. Default web fallback
  return 'http://localhost:8000';
};
