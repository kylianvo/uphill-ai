'use client';
import styles from './ProductDevices.module.css';

const SHOTS = {
  'ios-plan-week2': [780, 1696],
  'ios-coros-workout': [780, 1696],
  'web-calendar-month': [1100, 610],
  'ios-plan-builder': [780, 1696],
  'ios-adapt-week': [780, 1696],
  'ios-coach-saturday': [780, 1695],
  'ios-goal-determiner': [780, 1696],
  'ios-pace-strategy': [780, 1696],
  'ios-nutrition-lab': [780, 1696],
  'ios-gear-vault': [780, 1696],
} as const;

type Shot = keyof typeof SHOTS;
export function ProductDevice({ shot, alt, device = 'laptop', priority = false }: {
  shot: Shot; alt: string; device?: 'laptop' | 'phone' | 'closeup'; priority?: boolean;
}) {
  const [width, height] = SHOTS[shot];
  const base = `${process.env.NEXT_PUBLIC_BASE_PATH || ''}/landing/${shot}`;
  return (
    <div className={`${styles.device} ${styles[device]}`}>
      <div className={styles.screen}>
        <picture>
          {shot === 'ios-coach-saturday' && <source media="(prefers-reduced-motion: reduce)" srcSet={`${base}.png`} type="image/png" />}
          <source srcSet={`${base}.webp`} type="image/webp" />
          <img src={`${base}.png`} alt={alt} width={width} height={height}
            loading={priority ? 'eager' : 'lazy'} fetchPriority={priority ? 'high' : 'auto'} decoding="async" />
        </picture>
      </div>
      {device === 'laptop' && <div className={styles.laptopBase} aria-hidden="true" />}
    </div>
  );
}

// Cropped supplied COROS photograph; its display is not athlete data.
export function CorosWatchPhoto({ lang }: { lang: 'en' | 'vi' }) {
  const base = process.env.NEXT_PUBLIC_BASE_PATH || '';
  return (
    <div className={styles.watch}>
      <picture>
        <source srcSet={`${base}/landing/coros-activity.webp`} type="image/webp" />
        <img src={`${base}/landing/coros-activity.png`} width={430} height={657} loading="lazy" decoding="async"
          alt={lang === 'en' ? 'Real COROS watch photograph showing an activity screen with heart rate, calories and elapsed time. Display values are illustrative.' : 'Ảnh đồng hồ COROS thật với màn hình hoạt động: HR, calories và thời gian. Các số chỉ để minh hoạ.'} />
      </picture>
    </div>
  );
}
