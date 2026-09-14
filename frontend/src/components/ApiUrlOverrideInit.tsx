"use client";
import "@/lib/apiUrlOverride";

// Runs the ?api= / UPHILL_API_URL_OVERRIDE bootstrap for every route
// (both the marketing page and the app) by side-effecting on import.
export default function ApiUrlOverrideInit() {
  return null;
}
