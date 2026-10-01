import { describe, expect, it } from "vitest";
import {
  deepLinkNeedsRole,
  resolveHeldDeepLink,
  reconcileOpenedFromMe,
  shouldMirrorTab,
  isNavTabActive,
  shouldApplyV2Default,
  deepLinkTab,
  tabFromQuery,
  tabToQuery,
  v2NavTabs,
  v2TabLabel,
  withTabParam,
} from "./tabModel";

describe("tabModel", () => {
  it("maps query values to tabs and back", () => {
    expect(tabFromQuery("plan")).toBe("planner");
    expect(tabFromQuery("coach")).toBe("chat");
    expect(tabFromQuery("athletes")).toBe("coach");
    expect(tabFromQuery("me")).toBe("me");
    expect(tabFromQuery("bogus")).toBeNull();
    expect(tabFromQuery(null)).toBeNull();
    expect(tabToQuery("planner")).toBe("plan");
    expect(tabToQuery("chat")).toBe("coach");
    expect(tabToQuery("coach")).toBe("athletes");
    expect(tabToQuery("home")).toBeNull();
  });

  it("preserves other query params", () => {
    expect(withTabParam("?api=x&ui=v2&mode=desktop", "me")).toBe("?api=x&ui=v2&mode=desktop&tab=me");
    expect(withTabParam("?tab=me&ui=v2", "planner")).toBe("?tab=plan&ui=v2");
    expect(withTabParam("?tab=me", "home")).toBe("");
  });

  it("builds the v2 nav", () => {
    expect(v2NavTabs(false)).toEqual(["planner", "chat", "me"]);
    expect(v2NavTabs(true)).toEqual(["planner", "chat", "me", "coach"]);
    expect(["planner", "chat", "me", "coach"].map((t) => v2TabLabel(t as never))).toEqual(["Plan", "Coach", "Me", "Athletes"]);
  });

  it("highlights Me for sub-screens under v2 only", () => {
    expect(isNavTabActive("me", "tools", true)).toBe(true);
    expect(isNavTabActive("me", "about", true)).toBe(true);
    expect(isNavTabActive("me", "tools", false)).toBe(false);
    expect(isNavTabActive("planner", "tools", true)).toBe(false);
  });

  it("only replaces the old default tabs", () => {
    expect(shouldApplyV2Default("tools")).toBe(true);
    expect(shouldApplyV2Default("home")).toBe(true);
    expect(shouldApplyV2Default("me")).toBe(false);
    expect(shouldApplyV2Default("knowledge")).toBe(false);
  });

  it("mirrors ?tab= only for signed-in users on nav or Me sub-tabs", () => {
    expect(shouldMirrorTab("tools", false)).toBe(false);
    expect(shouldMirrorTab("planner", false)).toBe(false);
    expect(shouldMirrorTab("planner", true)).toBe(true);
    expect(shouldMirrorTab("knowledge", true)).toBe(true);
    expect(shouldMirrorTab("home", true)).toBe(false);
  });

  it("drops openedFromMe once a Me sub-screen is left", () => {
    expect(reconcileOpenedFromMe(true, "tools")).toBe(true);
    expect(reconcileOpenedFromMe(true, "planner")).toBe(false);
    expect(reconcileOpenedFromMe(true, "me")).toBe(false);
    expect(reconcileOpenedFromMe(false, "tools")).toBe(false);
  });

  it("ignores the athletes deep link for non-coaches", () => {
    expect(deepLinkTab("athletes", false)).toBeNull();
    expect(deepLinkTab("athletes", true)).toBe("coach");
    expect(deepLinkTab("plan", false)).toBe("planner");
  });
});

describe("held role-gated deep link", () => {
  it("only the Athletes tab needs a role", () => {
    expect(deepLinkNeedsRole("coach")).toBe(true);
    expect(deepLinkNeedsRole("planner")).toBe(false);
    expect(deepLinkNeedsRole(null)).toBe(false);
  });
  it("waits for the user, applies for coaches, drops for everyone else", () => {
    expect(resolveHeldDeepLink(null)).toBe("wait");
    expect(resolveHeldDeepLink(undefined)).toBe("wait");
    expect(resolveHeldDeepLink({ is_coach: true })).toBe("apply");
    expect(resolveHeldDeepLink({ is_coach: false })).toBe("drop");
    expect(resolveHeldDeepLink({})).toBe("drop");
  });
});
