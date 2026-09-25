// Google OAuth client IDs are public (they ship in every page and in the iOS
// Info.plist URL scheme), so they're hardcoded as fallbacks here. The env vars
// still win when set, but a native build from a fresh checkout -- which has no
// gitignored frontend/.env* -- must not ship with undefined IDs: that broke
// Google Sign-In in the iOS/Android app while web (CI sets the env) still worked.
export const GOOGLE_WEB_CLIENT_ID =
  process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ||
  "451637841654-0eoo8qsa5fgnpm4cq0br8phgkhh92c5a.apps.googleusercontent.com";

// Must match the reversed-client-ID URL scheme in ios/App/App/Info.plist.
export const GOOGLE_IOS_CLIENT_ID =
  process.env.NEXT_PUBLIC_GOOGLE_IOS_CLIENT_ID ||
  "451637841654-ncj3jhv24t9rq665noctori05faajiej.apps.googleusercontent.com";
