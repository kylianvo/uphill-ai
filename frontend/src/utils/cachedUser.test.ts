import { beforeEach, describe, expect, it } from "vitest";
import type { User } from "../types";
import { clearCachedUser, loadCachedUser, saveCachedUser } from "./cachedUser";

const user = { id: 7, email: "ada@uphill.ai", name: "Ada", role: "user", gemini_api_key: "secret" } as User;

describe("cachedUser", () => {
  beforeEach(() => localStorage.clear());

  it("round-trips the profile without the Gemini API key", () => {
    saveCachedUser(user);
    const cached = loadCachedUser();
    expect(cached).toMatchObject({ id: 7, email: "ada@uphill.ai", name: "Ada" });
    expect(cached).not.toHaveProperty("gemini_api_key");
    expect(localStorage.getItem("uphill_cached_user")).not.toContain("secret");
  });

  it("returns null when nothing is cached or the entry is corrupt", () => {
    expect(loadCachedUser()).toBeNull();
    localStorage.setItem("uphill_cached_user", "{not json");
    expect(loadCachedUser()).toBeNull();
  });

  it("clears the cached profile", () => {
    saveCachedUser(user);
    clearCachedUser();
    expect(loadCachedUser()).toBeNull();
  });
});
