import type { User } from "../types";

// Last profile /api/auth/me returned, so a relaunch can show the signed-in app
// at once and revalidate in the background instead of waiting on the network.
// gemini_api_key is left out: it has no business sitting in localStorage, and
// the background /api/auth/me fills it back in.
const KEY = "uphill_cached_user";

export function loadCachedUser(): User | null {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

export function saveCachedUser(user: User): void {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { gemini_api_key, ...rest } = user;
  try {
    localStorage.setItem(KEY, JSON.stringify(rest));
  } catch {
    // Storage full or blocked: the next launch just waits on /api/auth/me.
  }
}

export function clearCachedUser(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    // ignore
  }
}
