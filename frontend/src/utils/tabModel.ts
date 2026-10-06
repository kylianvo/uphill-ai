export type TabName = "home" | "about" | "chat" | "planner" | "tools" | "knowledge" | "coach" | "me";

// Tabs reachable from Me > More under the v2 shell. They are not in the nav.
export const ME_SUBTABS: readonly TabName[] = ["tools", "knowledge", "about"];

const QUERY_TO_TAB: Record<string, TabName> = {
  plan: "planner",
  coach: "chat",
  me: "me",
  athletes: "coach",
  tools: "tools",
  knowledge: "knowledge",
  about: "about",
};

const TAB_TO_QUERY: Partial<Record<TabName, string>> = Object.fromEntries(
  Object.entries(QUERY_TO_TAB).map(([q, t]) => [t, q]),
);

export const tabFromQuery = (value: string | null | undefined): TabName | null =>
  (value && QUERY_TO_TAB[value]) || null;

export const tabToQuery = (tab: TabName): string | null => TAB_TO_QUERY[tab] ?? null;

// Returns the search string (with leading "?" or empty) with `tab` set, other params preserved.
export const withTabParam = (search: string, tab: TabName): string => {
  const params = new URLSearchParams(search);
  const q = tabToQuery(tab);
  if (q) params.set("tab", q);
  else params.delete("tab");
  const s = params.toString();
  return s ? `?${s}` : "";
};

export const v2NavTabs = (isCoach: boolean): TabName[] => [
  "planner",
  "chat",
  "me",
  ...(isCoach ? (["coach"] as TabName[]) : []),
];

const V2_LABELS: Partial<Record<TabName, string>> = {
  planner: "Plan",
  chat: "Coach",
  me: "Me",
  coach: "Athletes",
};

export const v2TabLabel = (tab: TabName): string | null => V2_LABELS[tab] ?? null;

// Me stays highlighted while one of its sub-screens is open.
export const isNavTabActive = (tab: TabName, activeTab: TabName, shellV2: boolean): boolean =>
  activeTab === tab || (shellV2 && tab === "me" && ME_SUBTABS.includes(activeTab));

// The v2 default replaces the old defaults only; a tab the user already chose is kept.
export const shouldApplyV2Default = (current: TabName): boolean =>
  current === "tools" || current === "home";

// Only mirror ?tab= for signed-in users, and only for tabs reachable in the v2 shell.
export const shouldMirrorTab = (tab: TabName, signedIn: boolean): boolean =>
  signedIn && (v2NavTabs(true).includes(tab) || ME_SUBTABS.includes(tab));

// openedFromMe is only meaningful while a Me sub-screen is showing.
export const reconcileOpenedFromMe = (openedFromMe: boolean, tab: TabName): boolean =>
  openedFromMe && ME_SUBTABS.includes(tab);

// A ?tab= deep link; the Athletes tab is ignored for non-coaches.
export const deepLinkTab = (value: string | null | undefined, isCoach: boolean): TabName | null => {
  const tab = tabFromQuery(value);
  return tab === "coach" && !isCoach ? null : tab;
};

// Tabs a ?tab= deep link may only open for a signed-in user with the right role.
export const deepLinkNeedsRole = (tab: TabName | null): boolean => tab === "coach";

// What to do with a role-gated deep link held since boot: wait for the user to load,
// open it for a coach, or drop it for anyone else.
export const resolveHeldDeepLink = (user: { is_coach?: boolean } | null | undefined): "wait" | "apply" | "drop" =>
  !user ? "wait" : user.is_coach ? "apply" : "drop";
