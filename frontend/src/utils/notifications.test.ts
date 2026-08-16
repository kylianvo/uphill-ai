import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  requestNotificationPermission,
  hasNotificationPermission,
  scheduleNotification,
  scheduleDailyWorkoutReminder,
  scheduleFuelingReminder,
  cancelAllNotifications,
} from './notifications';
import { LocalNotifications } from '@capacitor/local-notifications';
import { Capacitor } from '@capacitor/core';

vi.mock('@capacitor/local-notifications', () => {
  return {
    LocalNotifications: {
      checkPermissions: vi.fn(),
      requestPermissions: vi.fn(),
      schedule: vi.fn(),
      cancel: vi.fn(),
      getPending: vi.fn().mockResolvedValue({ notifications: [] }),
    },
  };
});

describe('notification utilities', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.clearAllMocks();
  });

  describe('permissions', () => {
    it('returns true if native permission is granted', async () => {
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(true);
      vi.mocked(LocalNotifications.checkPermissions).mockResolvedValue({ display: 'granted' });

      const granted = await hasNotificationPermission();
      expect(granted).toBe(true);
    });

    it('requests permissions when on native platform', async () => {
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(true);
      vi.mocked(LocalNotifications.requestPermissions).mockResolvedValue({ display: 'granted' });

      const granted = await requestNotificationPermission();
      expect(granted).toBe(true);
      expect(LocalNotifications.requestPermissions).toHaveBeenCalledTimes(1);
    });

    it('handles web notification permission gracefully', async () => {
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(false);
      const granted = await hasNotificationPermission();
      expect(typeof granted).toBe('boolean');
    });
  });

  describe('scheduleNotification', () => {
    it('schedules notification on native platform', async () => {
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(true);
      vi.mocked(LocalNotifications.checkPermissions).mockResolvedValue({ display: 'granted' });
      vi.mocked(LocalNotifications.schedule).mockResolvedValue({ notifications: [] });

      const success = await scheduleNotification({
        id: 101,
        title: 'Workout Time',
        body: '8km Easy Run with Coach Uphill',
      });

      expect(success).toBe(true);
      expect(LocalNotifications.schedule).toHaveBeenCalledWith(
        expect.objectContaining({
          notifications: [
            expect.objectContaining({
              id: 101,
              title: 'Workout Time',
              body: '8km Easy Run with Coach Uphill',
            }),
          ],
        })
      );
    });
  });

  describe('scheduleDailyWorkoutReminder', () => {
    it('schedules a daily morning reminder', async () => {
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(true);
      vi.mocked(LocalNotifications.checkPermissions).mockResolvedValue({ display: 'granted' });
      vi.mocked(LocalNotifications.schedule).mockResolvedValue({ notifications: [] });

      const success = await scheduleDailyWorkoutReminder(7, 30, 'Morning Workout', 'Check today plan');
      expect(success).toBe(true);
      expect(LocalNotifications.schedule).toHaveBeenCalledTimes(1);
    });
  });

  describe('scheduleFuelingReminder', () => {
    it('schedules multi-interval fueling alerts for long runs', async () => {
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(true);
      vi.mocked(LocalNotifications.checkPermissions).mockResolvedValue({ display: 'granted' });
      vi.mocked(LocalNotifications.schedule).mockResolvedValue({ notifications: [] });

      // 30 min intervals over a 2 hour run = 4 fueling points
      const count = await scheduleFuelingReminder(30, 2);
      expect(count).toBe(4);
      expect(LocalNotifications.schedule).toHaveBeenCalledTimes(1);
    });
  });

  describe('cancelAllNotifications', () => {
    it('cancels pending native notifications', async () => {
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(true);
      vi.mocked(LocalNotifications.getPending).mockResolvedValue({
        notifications: [{ id: 1 }, { id: 2 }],
      });
      vi.mocked(LocalNotifications.cancel).mockResolvedValue();

      await cancelAllNotifications();
      expect(LocalNotifications.cancel).toHaveBeenCalledWith({
        notifications: [{ id: 1 }, { id: 2 }],
      });
    });
  });
});
