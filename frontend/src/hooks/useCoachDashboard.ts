/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from "react";
import { useAppContext } from "../contexts/AppContext";

export function useCoachDashboard() {
  const { setActingAsAthleteId, setActingAsAthleteName, setActiveTab } = useAppContext();
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [roster, setRoster] = useState<any[]>([]);
  const [pendingInvites, setPendingInvites] = useState<any[]>([]);
  const [inviteEmail, setInviteEmail] = useState("");
  const [rosterLoading, setRosterLoading] = useState(false);
  const [inviteLoading, setInviteLoading] = useState(false);
  const [inviteErrorMsg, setInviteErrorMsg] = useState("");

  const authHeaders = () => {
    const token = localStorage.getItem("uphill_session_token");
    return { "Content-Type": "application/json", Authorization: `Bearer ${token}` };
  };

  const fetchRoster = async () => {
    setRosterLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/coaching/roster`, { headers: authHeaders() });
      if (res.ok) setRoster(await res.json());
    } catch (err) {
      console.error("Failed to fetch roster:", err);
    } finally {
      setRosterLoading(false);
    }
  };

  const fetchMyInvites = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/coaching/my-invites`, { headers: authHeaders() });
      if (res.ok) setPendingInvites(await res.json());
    } catch (err) {
      console.error("Failed to fetch pending invites:", err);
    }
  };

  const sendInvite = async (email: string) => {
    setInviteLoading(true);
    setInviteErrorMsg("");
    try {
      const res = await fetch(`${API_BASE_URL}/api/coaching/invite`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ athlete_email: email }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to send invite.");
      }
      setInviteEmail("");
      await fetchRoster();
    } catch (err: any) {
      setInviteErrorMsg(err.message);
    } finally {
      setInviteLoading(false);
    }
  };

  const acceptInvite = async (linkId: number) => {
    await fetch(`${API_BASE_URL}/api/coaching/invites/${linkId}/accept`, {
      method: "POST",
      headers: authHeaders(),
    });
    setPendingInvites((prev) => prev.filter((i) => i.id !== linkId));
  };

  const declineInvite = async (linkId: number) => {
    await fetch(`${API_BASE_URL}/api/coaching/invites/${linkId}/decline`, {
      method: "POST",
      headers: authHeaders(),
    });
    setPendingInvites((prev) => prev.filter((i) => i.id !== linkId));
  };

  const removeFromRoster = async (linkId: number) => {
    await fetch(`${API_BASE_URL}/api/coaching/roster/${linkId}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    await fetchRoster();
  };

  const enterAthleteView = (athleteId: number, athleteName: string) => {
    setActingAsAthleteId(athleteId);
    setActingAsAthleteName(athleteName);
    setActiveTab("planner" as any);
  };

  const exitAthleteView = () => {
    setActingAsAthleteId(null);
    setActingAsAthleteName("");
  };

  return {
    roster,
    setRoster,
    pendingInvites,
    setPendingInvites,
    inviteEmail,
    setInviteEmail,
    rosterLoading,
    inviteLoading,
    inviteErrorMsg,
    fetchRoster,
    fetchMyInvites,
    sendInvite,
    acceptInvite,
    declineInvite,
    removeFromRoster,
    enterAthleteView,
    exitAthleteView,
  };
}
