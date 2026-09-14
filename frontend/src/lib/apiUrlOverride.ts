if (typeof window !== "undefined") {
  // Check for api query parameter to override API URL
  const params = new URLSearchParams(window.location.search);
  const apiParam = params.get("api");
  if (apiParam) {
    let cleanParam = apiParam.trim();
    if (
      (cleanParam.startsWith('"') && cleanParam.endsWith('"')) ||
      (cleanParam.startsWith("'") && cleanParam.endsWith("'"))
    ) {
      cleanParam = cleanParam.slice(1, -1).trim();
    }
    if (
      cleanParam === "default" ||
      cleanParam === "reset" ||
      cleanParam === "clear"
    ) {
      localStorage.removeItem("UPHILL_API_URL_OVERRIDE");
    } else {
      localStorage.setItem("UPHILL_API_URL_OVERRIDE", cleanParam);
    }
    // Remove query param from URL to keep it clean
    const cleanUrl = new URL(window.location.href);
    cleanUrl.searchParams.delete("api");
    window.history.replaceState(null, "", cleanUrl.pathname + cleanUrl.search);
  }
}
export const getApiBaseUrl = (): string => {
  if (typeof window !== "undefined") {
    const override = localStorage.getItem("UPHILL_API_URL_OVERRIDE");
    if (override) return override;
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
};
const API_BASE_URL = getApiBaseUrl();
if (typeof window !== "undefined") {
  const originalFetch = window.fetch;
  window.fetch = async (input, init) => {
    let url =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.toString()
          : input.url;
    const override = localStorage.getItem("UPHILL_API_URL_OVERRIDE");
    if (override) {
      if (url.startsWith(API_BASE_URL)) {
        url = url.replace(API_BASE_URL, override);
      } else if (url.startsWith("http://localhost:18000")) {
        url = url.replace("http://localhost:18000", override);
      } else if (url.startsWith("http://localhost:8000")) {
        url = url.replace("http://localhost:8000", override);
      }
    }
    return originalFetch(url, init);
  };
}
