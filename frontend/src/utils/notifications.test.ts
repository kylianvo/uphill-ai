import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  requestNotificationPermission,
  hasNotificationPermission,
  scheduleNotification,
  scheduleDailyWorkoutReminder,
  scheduleDailyKnowledgeReminder,
  scheduleFuelingReminder,
  cancelAllNotifications,
  cancelNotification,
  findTodaysWorkout,
  buildWorkoutReminderContent,
  notifyPlanGenerated,
  notifyGearPlanReady,
  notifyNutritionPlanReady,
  DAILY_KNOWLEDGE_REMINDER_ID,
} from './notifications';
import type { ActivePlan, Workout } from '../types';
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
        notifications: [
          { id: 1, title: 'A', body: 'A' },
          { id: 2, title: 'B', body: 'B' },
        ],
      });
      vi.mocked(LocalNotifications.cancel).mockResolvedValue();

      await cancelAllNotifications();
      expect(LocalNotifications.cancel).toHaveBeenCalledWith({
        notifications: [
          { id: 1, title: 'A', body: 'A' },
          { id: 2, title: 'B', body: 'B' },
        ],
      });
    });
  });

  describe('cancelNotification', () => {
    it('cancels a single notification by id on native platform', async () => {
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(true);
      vi.mocked(LocalNotifications.cancel).mockResolvedValue();

      await cancelNotification(DAILY_KNOWLEDGE_REMINDER_ID);
      expect(LocalNotifications.cancel).toHaveBeenCalledWith({
        notifications: [{ id: DAILY_KNOWLEDGE_REMINDER_ID }],
      });
    });
  });

  describe('scheduleDailyKnowledgeReminder', () => {
    const originalFetch = global.fetch;

    afterEach(() => {
      global.fetch = originalFetch;
      window.localStorage.clear();
    });

    it('schedules a daily knowledge notification using a fetched card', async () => {
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(true);
      vi.mocked(LocalNotifications.checkPermissions).mockResolvedValue({ display: 'granted' });
      vi.mocked(LocalNotifications.schedule).mockResolvedValue({ notifications: [] });
      window.localStorage.setItem('uphill_session_token', 'token-123');
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ cards: [{ chapter_title: 'Zone 2 Basics', summary: 'Train slow to race fast.' }] }),
      }) as unknown as typeof fetch;

      const success = await scheduleDailyKnowledgeReminder(8, 0, 'en');
      expect(success).toBe(true);
      expect(LocalNotifications.schedule).toHaveBeenCalledWith(
        expect.objectContaining({
          notifications: [
            expect.objectContaining({
              id: DAILY_KNOWLEDGE_REMINDER_ID,
              body: expect.stringContaining('Zone 2 Basics'),
            }),
          ],
        })
      );
    });

    it('falls back to generic copy when no card is available', async () => {
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(true);
      vi.mocked(LocalNotifications.checkPermissions).mockResolvedValue({ display: 'granted' });
      vi.mocked(LocalNotifications.schedule).mockResolvedValue({ notifications: [] });
      window.localStorage.removeItem('uphill_session_token');

      const success = await scheduleDailyKnowledgeReminder(8, 0, 'en');
      expect(success).toBe(true);
      expect(LocalNotifications.schedule).toHaveBeenCalledWith(
        expect.objectContaining({
          notifications: [
            expect.objectContaining({
              id: DAILY_KNOWLEDGE_REMINDER_ID,
              body: expect.stringContaining('Knowledge Hub'),
            }),
          ],
        })
      );
    });
  });

  describe('findTodaysWorkout / buildWorkoutReminderContent', () => {
    const activePlan: ActivePlan = {
      id: 1,
      race_name: 'Test 50K',
      race_date: '2026-12-01',
      start_date: '2026-08-17', // a Monday
      goal_type: 'race',
      total_weeks: 12,
    };

    const mondayWorkout: Workout = {
      id: 1,
      plan_id: 1,
      week_number: 1,
      day_of_week: 'Monday',
      phase: 'base',
      title: 'Easy Run',
      type: 'easy',
      duration_minutes: 45,
      distance_km: 8,
      target_zone: 'Z2',
      treadmill_incline: 0,
      treadmill_speed: 0,
      elevation_gain_m: 50,
      grade_percent: 1,
      is_completed: 0,
      is_missed: 0,
    };

    const tuesdayWorkout: Workout = { ...mondayWorkout, id: 2, day_of_week: 'Tuesday', title: 'Rest' };

    beforeEach(() => {
      vi.useFakeTimers();
      vi.setSystemTime(new Date(2026, 7, 17)); // Monday, Aug 17 2026
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('finds the workout whose computed calendar date is today', () => {
      const found = findTodaysWorkout(activePlan, [mondayWorkout, tuesdayWorkout]);
      expect(found?.id).toBe(1);
    });

    it('returns null when no workout falls on today', () => {
      const found = findTodaysWorkout(activePlan, [tuesdayWorkout]);
      expect(found).toBeNull();
    });

    it('returns null with no active plan or no start_date', () => {
      expect(findTodaysWorkout(null, [mondayWorkout])).toBeNull();
      expect(findTodaysWorkout({ ...activePlan, start_date: undefined }, [mondayWorkout])).toBeNull();
    });

    it('builds dynamic content from today\'s workout', () => {
      const { body } = buildWorkoutReminderContent(activePlan, [mondayWorkout], 'en');
      expect(body).toContain('Easy Run');
      expect(body).toContain('8km');
      expect(body).toContain('45 min');
    });

    it('falls back to generic copy when no workout matches today', () => {
      const { body } = buildWorkoutReminderContent(activePlan, [tuesdayWorkout], 'en');
      expect(body).toBe('Check your planned workout and nutrition targets for today.');
    });

    it('falls back to generic Vietnamese copy', () => {
      const { title, body } = buildWorkoutReminderContent(null, [], 'vi');
      expect(title).toContain('Kế hoạch tập luyện');
      expect(body).toContain('dinh dưỡng');
    });
  });

  describe('event completion notifications', () => {
    beforeEach(() => {
      vi.spyOn(Capacitor, 'isNativePlatform').mockReturnValue(true);
      vi.mocked(LocalNotifications.schedule).mockResolvedValue({ notifications: [] });
    });

    it('notifyPlanGenerated fires immediately without prompting for permission', async () => {
      vi.mocked(LocalNotifications.checkPermissions).mockResolvedValue({ display: 'granted' });
      const result = await notifyPlanGenerated('en');
      expect(result).toBe(true);
      expect(LocalNotifications.requestPermissions).not.toHaveBeenCalled();
      expect(LocalNotifications.schedule).toHaveBeenCalledWith(
        expect.objectContaining({
          notifications: [expect.objectContaining({ extra: { type: 'plan_generated' } })],
        })
      );
    });

    it('skips silently (no prompt) when permission was never granted', async () => {
      vi.mocked(LocalNotifications.checkPermissions).mockResolvedValue({ display: 'prompt' });
      const result = await notifyGearPlanReady('en');
      expect(result).toBe(false);
      expect(LocalNotifications.requestPermissions).not.toHaveBeenCalled();
      expect(LocalNotifications.schedule).not.toHaveBeenCalled();
    });

    it('notifyNutritionPlanReady fires with Vietnamese copy', async () => {
      vi.mocked(LocalNotifications.checkPermissions).mockResolvedValue({ display: 'granted' });
      const result = await notifyNutritionPlanReady('vi');
      expect(result).toBe(true);
      expect(LocalNotifications.schedule).toHaveBeenCalledWith(
        expect.objectContaining({
          notifications: [expect.objectContaining({ extra: { type: 'nutrition_plan_ready' } })],
        })
      );
    });
  });
});
