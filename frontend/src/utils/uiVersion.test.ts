import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { isShellV2 } from './uiVersion';

const setSearch = (search: string) => window.history.replaceState({}, '', '/' + search);

describe('isShellV2', () => {
  beforeEach(() => {
    window.localStorage.clear();
    setSearch('');
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it('defaults to off', () => {
    expect(isShellV2()).toBe(false);
  });

  it('is on when NEXT_PUBLIC_UI_V2 is "true"', () => {
    vi.stubEnv('NEXT_PUBLIC_UI_V2', 'true');
    expect(isShellV2()).toBe(true);
  });

  it('?ui=v2 turns it on and persists', () => {
    setSearch('?ui=v2');
    expect(isShellV2()).toBe(true);
    setSearch('');
    expect(isShellV2()).toBe(true);
    expect(window.localStorage.getItem('UPHILL_UI_VERSION')).toBe('v2');
  });

  it('?ui=v1 overrides the env var', () => {
    vi.stubEnv('NEXT_PUBLIC_UI_V2', 'true');
    setSearch('?ui=v1');
    expect(isShellV2()).toBe(false);
    setSearch('');
    expect(isShellV2()).toBe(false);
  });

  it('falls back to env/default when localStorage throws', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('denied');
    });
    expect(isShellV2()).toBe(false);
    vi.stubEnv('NEXT_PUBLIC_UI_V2', 'true');
    expect(isShellV2()).toBe(true);
  });
});
