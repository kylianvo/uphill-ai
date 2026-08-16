import { LocalNotifications, LocalNotificationSchema } from '@capacitor/local-notifications';
import { isNativePlatform } from './native';

export interface ScheduleNotificationOptions {
  id?: number;
  title: string;
  body: string;
  scheduleAt?: Date;
  extra?: Record<string, unknown>;
}

export const hasNotificationPermission = async (): Promise<boolean> => {
  if (isNativePlatform()) {
    try {
      const status = await LocalNotifications.checkPermissions();
      return status.display === 'granted';
    } catch {
      return false;
    }
  }

  if (typeof window !== 'undefined' && 'Notification' in window) {
    return Notification.permission === 'granted';
  }

  return false;
};

export const requestNotificationPermission = async (): Promise<boolean> => {
  if (isNativePlatform()) {
    try {
      const result = await LocalNotifications.requestPermissions();
      return result.display === 'granted';
    } catch {
      return false;
    }
  }

  if (typeof window !== 'undefined' && 'Notification' in window) {
    try {
      const result = await Notification.requestPermission();
      return result === 'granted';
    } catch {
      return false;
    }
  }

  return false;
};

export const scheduleNotification = async (
  options: ScheduleNotificationOptions
): Promise<boolean> => {
  const granted = await hasNotificationPermission();
  if (!granted) {
    const requested = await requestNotificationPermission();
    if (!requested) {
      return false;
    }
  }

  const notifId = options.id ?? Math.floor(Math.random() * 1000000);

  if (isNativePlatform()) {
    try {
      const notification: LocalNotificationSchema = {
        id: notifId,
        title: options.title,
        body: options.body,
        extra: options.extra,
        schedule: options.scheduleAt
          ? { at: options.scheduleAt, allowWhileIdle: true }
          : undefined,
      };

      await LocalNotifications.schedule({
        notifications: [notification],
      });
      return true;
    } catch (e) {
      console.warn('Failed to schedule native notification:', e);
      return false;
    }
  }

  // Web Browser fallback
  if (typeof window !== 'undefined' && 'Notification' in window && Notification.permission === 'granted') {
    if (!options.scheduleAt || options.scheduleAt.getTime() <= Date.now()) {
      new Notification(options.title, { body: options.body });
      return true;
    } else {
      const delay = Math.max(0, options.scheduleAt.getTime() - Date.now());
      setTimeout(() => {
        if (Notification.permission === 'granted') {
          new Notification(options.title, { body: options.body });
        }
      }, delay);
      return true;
    }
  }

  return false;
};

export const scheduleDailyWorkoutReminder = async (
  hour: number,
  minute: number,
  title: string = "Today's Training | Uphill AI",
  body: string = "Check your planned workout and nutrition targets for today."
): Promise<boolean> => {
  const now = new Date();
  const scheduledTime = new Date();
  scheduledTime.setHours(hour, minute, 0, 0);

  if (scheduledTime.getTime() <= now.getTime()) {
    scheduledTime.setDate(scheduledTime.getDate() + 1);
  }

  return scheduleNotification({
    id: 10001, // dedicated ID for daily reminder
    title,
    body,
    scheduleAt: scheduledTime,
    extra: { type: 'daily_workout_reminder' },
  });
};

export const scheduleFuelingReminder = async (
  intervalMinutes: number = 30,
  raceDurationHours: number = 2
): Promise<number> => {
  const totalIntervals = Math.floor((raceDurationHours * 60) / intervalMinutes);
  if (totalIntervals <= 0) return 0;

  const notifications: LocalNotificationSchema[] = [];
  const now = Date.now();

  for (let i = 1; i <= totalIntervals; i++) {
    const triggerTime = new Date(now + i * intervalMinutes * 60 * 1000);
    notifications.push({
      id: 20000 + i,
      title: `⚡ Fueling Alert #${i}`,
      body: `Time to fuel! Aim for 25-30g carbs & hydrate.`,
      schedule: { at: triggerTime, allowWhileIdle: true },
      extra: { type: 'fueling_interval', interval: i },
    });
  }

  if (isNativePlatform()) {
    try {
      const granted = await hasNotificationPermission();
      if (!granted) {
        const requested = await requestNotificationPermission();
        if (!requested) return 0;
      }
      await LocalNotifications.schedule({ notifications });
      return totalIntervals;
    } catch {
      return 0;
    }
  }

  return totalIntervals;
};

export const cancelAllNotifications = async (): Promise<void> => {
  if (isNativePlatform()) {
    try {
      const pending = await LocalNotifications.getPending();
      if (pending.notifications.length > 0) {
        await LocalNotifications.cancel({ notifications: pending.notifications });
      }
    } catch (e) {
      console.warn('Failed to cancel notifications:', e);
    }
  }
};
