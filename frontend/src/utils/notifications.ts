import { LocalNotifications, LocalNotificationSchema } from '@capacitor/local-notifications';
import { isNativePlatform, getApiBaseUrl } from './native';
import type { ActivePlan, Workout } from '../types';

export const DAILY_WORKOUT_REMINDER_ID = 10001;
export const DAILY_KNOWLEDGE_REMINDER_ID = 10002;

const DAY_OFFSETS: Record<string, number> = {
  Monday: 0, Tuesday: 1, Wednesday: 2, Thursday: 3, Friday: 4, Saturday: 5, Sunday: 6,
};

const getMondayOf = (d: Date): Date => {
  const offset = d.getDay() === 0 ? 6 : d.getDay() - 1;
  const m = new Date(d);
  m.setDate(d.getDate() - offset);
  return m;
};

const isSameDate = (a: Date, b: Date): boolean =>
  a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();

/** Mirrors usePlanner.ts's getWorkoutDateObj -- kept standalone here since it
 *  only needs activePlan/workouts (already in AppContext), not the rest of
 *  the usePlanner hook's state. */
export const findTodaysWorkout = (activePlan: ActivePlan | null, workouts: Workout[]): Workout | null => {
  if (!activePlan?.start_date || !workouts?.length) return null;
  try {
    const parts = activePlan.start_date.split('-');
    const sd = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
    const startMonday = getMondayOf(sd);
    const today = new Date();

    return (
      workouts.find((wo) => {
        const offset = DAY_OFFSETS[wo.day_of_week] ?? 0;
        const workoutDate = new Date(startMonday);
        workoutDate.setDate(startMonday.getDate() + (wo.week_number - 1) * 7 + offset);
        return isSameDate(workoutDate, today);
      }) ?? null
    );
  } catch {
    return null;
  }
};

export interface ScheduleNotificationOptions {
  id?: number;
  title: string;
  body: string;
  scheduleAt?: Date;
  /** Recurs every day at this wall-clock time (persisted by the OS scheduler). */
  repeatDailyAt?: { hour: number; minute: number };
  extra?: Record<string, unknown>;
  /** Default true. Set false for incidental/event notifications that shouldn't
   *  surprise the user with a permission prompt outside an explicit opt-in flow. */
  promptForPermission?: boolean;
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
  let granted = await hasNotificationPermission();
  if (!granted) {
    if (options.promptForPermission === false) return false;
    granted = await requestNotificationPermission();
    if (!granted) return false;
  }

  const notifId = options.id ?? Math.floor(Math.random() * 1000000);

  if (isNativePlatform()) {
    try {
      const notification: LocalNotificationSchema = {
        id: notifId,
        title: options.title,
        body: options.body,
        extra: options.extra,
        schedule: options.repeatDailyAt
          ? { on: { hour: options.repeatDailyAt.hour, minute: options.repeatDailyAt.minute }, allowWhileIdle: true }
          : options.scheduleAt
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

  // Web Browser fallback — the browser has no OS-level daily scheduler, so a
  // repeatDailyAt request is best-effort: fire once at the next occurrence.
  if (typeof window !== 'undefined' && 'Notification' in window && Notification.permission === 'granted') {
    let fireAt: Date | undefined = options.scheduleAt;
    if (options.repeatDailyAt) {
      fireAt = new Date();
      fireAt.setHours(options.repeatDailyAt.hour, options.repeatDailyAt.minute, 0, 0);
      if (fireAt.getTime() <= Date.now()) {
        fireAt.setDate(fireAt.getDate() + 1);
      }
    }

    if (!fireAt || fireAt.getTime() <= Date.now()) {
      new Notification(options.title, { body: options.body });
      return true;
    } else {
      const delay = Math.max(0, fireAt.getTime() - Date.now());
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

/** Builds workout-reminder copy from today's actual planned workout when
 *  available, falling back to generic copy otherwise (no active plan, rest
 *  day with no matching workout row, etc). */
export const buildWorkoutReminderContent = (
  activePlan: ActivePlan | null,
  workouts: Workout[],
  lang: 'en' | 'vi' = 'en'
): { title: string; body: string } => {
  const title = lang === 'vi' ? "Kế hoạch tập luyện hôm nay | Uphill AI" : "Today's Training | Uphill AI";
  const workout = findTodaysWorkout(activePlan, workouts);

  if (!workout) {
    return {
      title,
      body: lang === 'vi'
        ? 'Xem bài tập và mục tiêu dinh dưỡng hôm nay của bạn.'
        : 'Check your planned workout and nutrition targets for today.',
    };
  }

  const distance = workout.distance_km ? `${workout.distance_km}km` : null;
  const duration = workout.duration_minutes ? `${workout.duration_minutes} min` : null;
  const detail = [distance, duration].filter(Boolean).join(' · ');

  return {
    title,
    body: detail ? `${workout.title} — ${detail}` : workout.title,
  };
};

export const scheduleDailyWorkoutReminder = async (
  hour: number,
  minute: number,
  title: string = "Today's Training | Uphill AI",
  body: string = "Check your planned workout and nutrition targets for today."
): Promise<boolean> => {
  return scheduleNotification({
    id: DAILY_WORKOUT_REMINDER_ID,
    title,
    body,
    repeatDailyAt: { hour, minute },
    extra: { type: 'daily_workout_reminder' },
  });
};

interface KnowledgeCardSnippet {
  chapter_title?: string;
  summary?: string;
}

const fetchRandomKnowledgeCard = async (lang: 'en' | 'vi'): Promise<KnowledgeCardSnippet | null> => {
  if (typeof window === 'undefined') return null;
  const token = window.localStorage.getItem('uphill_session_token');
  if (!token) return null;
  try {
    const res = await fetch(`${getApiBaseUrl()}/api/knowledge/cards/random?n=1&lang=${lang}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data.cards?.[0] ?? null;
  } catch {
    return null;
  }
};

export const scheduleDailyKnowledgeReminder = async (
  hour: number,
  minute: number,
  lang: 'en' | 'vi' = 'en'
): Promise<boolean> => {
  const card = await fetchRandomKnowledgeCard(lang);
  const title = lang === 'vi' ? '💡 Kiến thức hôm nay | Uphill AI' : "💡 Today's Knowledge | Uphill AI";
  const fallbackBody = lang === 'vi'
    ? 'Có một mẹo huấn luyện mới đang chờ bạn trong Knowledge Hub.'
    : 'A new coaching insight is waiting for you in the Knowledge Hub.';
  const body = card?.chapter_title
    ? `${card.chapter_title}${card.summary ? ` — ${card.summary}` : ''}`
    : fallbackBody;

  return scheduleNotification({
    id: DAILY_KNOWLEDGE_REMINDER_ID,
    title,
    body: body.slice(0, 180),
    repeatDailyAt: { hour, minute },
    extra: { type: 'daily_knowledge_reminder' },
  });
};

export const notifyPlanGenerated = async (lang: 'en' | 'vi' = 'en'): Promise<boolean> => {
  return scheduleNotification({
    title: lang === 'vi' ? '🏔️ Kế hoạch của bạn đã sẵn sàng | Uphill AI' : "🏔️ Your Training Plan is Ready | Uphill AI",
    body: lang === 'vi'
      ? 'Coach Uphill đã hoàn thành kế hoạch tập luyện của bạn. Xem ngay!'
      : "Coach Uphill has finished building your training plan. Take a look!",
    extra: { type: 'plan_generated' },
    promptForPermission: false,
  });
};

export const notifyGearPlanReady = async (lang: 'en' | 'vi' = 'en'): Promise<boolean> => {
  return scheduleNotification({
    title: lang === 'vi' ? '👟 Gợi ý giày đã sẵn sàng | Uphill AI' : '👟 Your Shoe Recommendations are Ready | Uphill AI',
    body: lang === 'vi'
      ? 'Gợi ý giày chạy phù hợp với bạn đã có trong Gear Vault.'
      : 'Your personalized shoe picks are waiting in the Gear Vault.',
    extra: { type: 'gear_plan_ready' },
    promptForPermission: false,
  });
};

export const notifyNutritionPlanReady = async (lang: 'en' | 'vi' = 'en'): Promise<boolean> => {
  return scheduleNotification({
    title: lang === 'vi' ? '🍌 Kế hoạch dinh dưỡng đã sẵn sàng | Uphill AI' : '🍌 Your Fueling Plan is Ready | Uphill AI',
    body: lang === 'vi'
      ? 'Chiến lược Fueling & dinh dưỡng cho buổi tập của bạn đã sẵn sàng.'
      : 'Your race/workout fueling strategy has been calculated.',
    extra: { type: 'nutrition_plan_ready' },
    promptForPermission: false,
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

export const cancelNotification = async (id: number): Promise<void> => {
  if (isNativePlatform()) {
    try {
      await LocalNotifications.cancel({ notifications: [{ id }] });
    } catch (e) {
      console.warn('Failed to cancel notification:', e);
    }
  }
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
