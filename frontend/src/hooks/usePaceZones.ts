import { useState } from "react";

export interface PaceZones {
  zone1_pace: string;
  zone2_pace: string;
  zone3_pace: string;
  zone4_pace: string;
  zone5_pace: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function usePaceZones() {
  const [zones, setZones] = useState<PaceZones | null>(null);

  const fetchPaceZones = async () => {
    const token = typeof window !== "undefined" ? localStorage.getItem("uphill_session_token") : null;
    if (!token) return;
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/pace-zones`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setZones(data);
      }
    } catch (err) {
      console.error("Failed to load pace zones:", err);
    }
  };

  return { zones, fetchPaceZones };
}
