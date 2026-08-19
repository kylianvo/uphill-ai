import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getApiBaseUrl, isNativePlatform, getPlatform, triggerHaptic } from './native';
import { Capacitor } from '@capacitor/core';
import { Haptics, ImpactStyle } from '@capacitor/haptics';

vi.mock('@capacitor/haptics', () => {
  return {
    Haptics: {
      impact: vi.fn(),
      notification: vi.fn(),
      selectionStart: vi.fn(),
      selectionChanged: vi.fn(),
      selectionEnd: vi.fn(),
    },
    ImpactStyle: {
      Heavy: 'HEAVY',
      Medium: 'MEDIUM',
      Light: 'LIGHT',
    },
  };
});

describe('native utilities', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('isNativePlatform', () => {
    it('delegates to Capacitor.isNativePlatform', () => {
      const spy = vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(true);
      expect(isNativePlatform()).toBe(true);
      expect(spy).toHaveBeenCalledTimes(1);
    });
  });

  describe('getPlatform', () => {
    it('delegates to Capacitor.getPlatform', () => {
      const spy = vi.spyOn(Capacitor, 'getPlatform').mockReturnValue('ios');
      expect(getPlatform()).toBe('ios');
      expect(spy).toHaveBeenCalledTimes(1);
    });
  });

  describe('triggerHaptic', () => {
    it('calls Haptics.impact when running on native platform', async () => {
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(true);

      await triggerHaptic(ImpactStyle.Medium);
      expect(Haptics.impact).toHaveBeenCalledWith({ style: ImpactStyle.Medium });
    });

    it('does not call Haptics.impact when running on web', async () => {
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(false);

      await triggerHaptic();
      expect(Haptics.impact).not.toHaveBeenCalled();
    });
  });

  describe('getApiBaseUrl', () => {
    it('prioritizes localStorage UPHILL_API_URL_OVERRIDE if present', () => {
      localStorage.setItem('UPHILL_API_URL_OVERRIDE', 'https://custom-api.example.com/');
      expect(getApiBaseUrl()).toBe('https://custom-api.example.com');
    });

    it('returns Android host alias 10.0.2.2 on Android native when no env is set', () => {
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(true);
      vi.spyOn(Capacitor, 'getPlatform').mockReturnValue('android');
      expect(getApiBaseUrl()).toBe('http://10.0.2.2:8000');
    });

    it('returns localhost:8000 on iOS native simulator when no env is set', () => {
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(true);
      vi.spyOn(Capacitor, 'getPlatform').mockReturnValue('ios');
      expect(getApiBaseUrl()).toBe('http://localhost:8000');
    });

    it('defaults to http://localhost:8000 on web when no override/env set', () => {
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(false);
      expect(getApiBaseUrl()).toBe('http://localhost:8000');
    });
  });
});
