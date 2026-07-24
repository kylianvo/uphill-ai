/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from "react";

export function useCoachNotes(athleteId: number | null, targetType: string, targetId: number | null) {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const [notes, setNotes] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const authHeaders = () => {
    const token = localStorage.getItem("uphill_session_token");
    return { "Content-Type": "application/json", Authorization: `Bearer ${token}` };
  };

  const fetchNotes = async () => {
    if (!athleteId) return;
    setLoading(true);
    try {
      const params = new URLSearchParams({ target_type: targetType });
      if (targetId !== null) params.set("target_id", String(targetId));
      const res = await fetch(`${API_BASE_URL}/api/coaching/athletes/${athleteId}/notes?${params}`, {
        headers: authHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setNotes(data.notes || []);
      }
    } catch (err) {
      console.error("Failed to fetch coach notes:", err);
    } finally {
      setLoading(false);
    }
  };

  const addNote = async (note: string) => {
    if (!athleteId || !note.trim()) return;
    await fetch(`${API_BASE_URL}/api/coaching/athletes/${athleteId}/notes`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ target_type: targetType, target_id: targetId, note }),
    });
    await fetchNotes();
  };

  return { notes, loading, fetchNotes, addNote };
}
