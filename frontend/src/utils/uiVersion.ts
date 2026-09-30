const STORAGE_KEY = 'UPHILL_UI_VERSION';

// Feature flag for the v2 app shell. Precedence: ?ui=v1|v2 query (persisted to
// localStorage) > stored value > NEXT_PUBLIC_UI_V2 build-time env > off.
export const isShellV2 = (): boolean => {
  if (typeof window !== 'undefined') {
    try {
      const q = new URLSearchParams(window.location?.search ?? '').get('ui');
      if (q === 'v1' || q === 'v2') {
        window.localStorage.setItem(STORAGE_KEY, q);
      }
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored === 'v2') return true;
      if (stored === 'v1') return false;
    } catch {
      // Ignore localStorage access errors
    }
  }
  // Literal form required: Next.js only inlines `process.env.NEXT_PUBLIC_X` verbatim.
  return process.env.NEXT_PUBLIC_UI_V2 === 'true';
};
