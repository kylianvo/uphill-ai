import { useEffect, useState } from "react";

// Matches the app shell's own breakpoint (see isViewportMobile in
// src/app/app/page.tsx) so components shared between the app and the
// standalone marketing/science pages stay visually consistent.
const MOBILE_BREAKPOINT = 900;

export function useIsMobileViewport(): boolean {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const update = () => setIsMobile(window.innerWidth <= MOBILE_BREAKPOINT);
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  return isMobile;
}
