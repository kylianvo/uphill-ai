/* eslint-disable @typescript-eslint/no-explicit-any */
import { useAppContext } from "../contexts/AppContext";
import { User } from "../types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useKnowledge() {
  const ctx = useAppContext();
  const { setSources, user, setRagLoading, setRagErrorMsg, linkInput, setLinkInput, lang, setDailyCards, setKnowledgeTopic } = ctx;

  const fetchSourcesWithToken = async (currentUser: User | null, token: string) => {
    const activeUser = currentUser || user;
    if (!activeUser || activeUser.role !== 'admin') {
      setSources([]);
      return;
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/sources`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setSources(data);
      }
    } catch (err) {
      console.error("Failed to load knowledge sources:", err);
    }
  };
  const fetchSources = () => {
    const token = localStorage.getItem("uphill_session_token");
    if (token) fetchSourcesWithToken(user, token);
  };
  const handleAddLink = async () => {
    if (!linkInput.trim()) return;
    setRagLoading(true);
    setRagErrorMsg("");

    const token = localStorage.getItem("uphill_session_token");
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/link`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ url: linkInput }),
      });

      if (!response.ok) {
        const errorText = await response.json();
        throw new Error(errorText.detail || "Link ingestion failed.");
      }

      setLinkInput("");
      await fetchSources();
    } catch (err: any) {
      setRagErrorMsg(err.message);
    } finally {
      setRagLoading(false);
    }
  };
  const handlePdfFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setRagLoading(true);
    setRagErrorMsg("");

    const formData = new FormData();
    formData.append("file", file);

    const token = localStorage.getItem("uphill_session_token");
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/upload`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.json();
        throw new Error(errorText.detail || "PDF upload failed.");
      }

      await fetchSources();
    } catch (err: any) {
      setRagErrorMsg(err.message);
    } finally {
      setRagLoading(false);
    }
  };
  const handleDeleteSource = async (id: number) => {
    const token = localStorage.getItem("uphill_session_token");
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag/sources/${id}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });
      if (response.ok) {
        await fetchSources();
      }
    } catch (err) {
      console.error("Failed to delete source:", err);
    }
  };


  const shuffleDailyCards = async () => {
    const token = localStorage.getItem("uphill_session_token");
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/knowledge/cards/random?n=3&lang=${lang}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) { const d = await res.json(); setDailyCards(d.cards || []); }
    } catch (e) {}
  };

  const filterKnowledgeByTopic = async (topic: string) => {
    setKnowledgeTopic(topic);
    const token = localStorage.getItem("uphill_session_token");
    if (!token) return;
    try {
      const url = topic === "All"
        ? `${API_BASE_URL}/api/knowledge/cards?lang=${lang}`
        : `${API_BASE_URL}/api/knowledge/cards?topic=${topic}&lang=${lang}`;
      const res = await fetch(url, { headers: { "Authorization": `Bearer ${token}` } });
      if (res.ok) { const d = await res.json(); setDailyCards(d.cards || []); }
    } catch (e) {}
  };
  return { shuffleDailyCards, filterKnowledgeByTopic, fetchSourcesWithToken, fetchSources, handleAddLink, handlePdfFileChange, handleDeleteSource };
}
