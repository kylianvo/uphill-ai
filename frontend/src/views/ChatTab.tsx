/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useRef } from "react";
import { useAppContext } from "../contexts/AppContext";
import { parseMarkdown } from "../utils/markdown";
import { translations } from "../app/translations";

const API_BASE_URL = typeof window !== "undefined"
  ? (localStorage.getItem("UPHILL_API_URL_OVERRIDE") || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000")
  : (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");

export default function ChatTab({ isMobile }: { isMobile: boolean }) {
  const ctx = useAppContext();
  const chatBottomRef = useRef<HTMLDivElement>(null);

  const {
    chatMessages, setChatMessages,
    chatInput, setChatInput,
    chatLoading, setChatLoading,
    lang, user,
    activePlan, workouts, planForm,
  } = ctx;

  const t = (key: keyof typeof translations.en) =>
    translations[lang]?.[key] || translations.en[key] || key;

  const handleSendMessage = async (textToSend?: string) => {
    const messageText = textToSend || chatInput;
    if (!messageText.trim()) return;

    if (!textToSend) setChatInput("");

    const updatedMessages = [...chatMessages, { role: "user" as const, content: messageText }];
    setChatMessages(updatedMessages);
    setChatLoading(true);

    const token = typeof window !== "undefined" ? localStorage.getItem("uphill_session_token") : null;
    const headers: any = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const apiBase = typeof window !== "undefined"
      ? (localStorage.getItem("UPHILL_API_URL_OVERRIDE") || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000")
      : (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");

    try {
      const response = await fetch(`${apiBase}/api/coach/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          messages: updatedMessages,
          user_profile: {
            age: user?.age ?? 30,
            current_weekly_km: user?.current_weekly_km ?? 30.0,
            max_hr: user?.max_hr ?? 185,
            resting_hr: user?.resting_hr ?? 60,
            aet_hr: user?.aet_hr ?? 135,
            ant_hr: user?.ant_hr ?? 165,
            use_treadmill: user?.use_treadmill === 1,
            gemini_api_key: user?.gemini_api_key ?? "",
            zone2_pace_min: user?.zone2_pace_min ?? "6:30",
            zone2_pace_max: user?.zone2_pace_max ?? "5:45",
            recent_race: planForm?.race_name,
          },
          context_data: activePlan ? {
            race_name: activePlan.race_name,
            race_date: activePlan.race_date,
            goal_type: activePlan.goal_type,
            total_weeks: activePlan.total_weeks,
            workouts,
          } : null,
        }),
      });

      if (!response.ok) throw new Error("Failed to communicate with Coach API");
      const replyData = await response.json();
      setChatMessages((prev: any) => [...prev, replyData]);
    } catch {
      setChatMessages((prev: any) => [
        ...prev,
        { role: "assistant", content: "Sorry, I had trouble reaching the coaching server. Please make sure the backend server is running." },
      ]);
    } finally {
      setChatLoading(false);
      setTimeout(() => chatBottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    }
  };

  const sendPresetPrompt = (prompt: string) => handleSendMessage(prompt);

  const welcomeText = lang === "en"
    ? "Hello! I'm Coach Uphill AI. Are you training for a trail ultra or a road marathon?"
    : "Xin chào! Tôi là Coach Uphill AI. Bạn đang chuẩn bị cho một giải chạy trail ultra hay marathon đường bằng?";

  return (
    <div style={{ width: "100%", display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <div style={{ display: "flex", flexDirection: "column", flex: 1, width: "100%", minHeight: 0 }}>
        {!isMobile && (
          <h3 style={{ marginBottom: "12px", fontSize: "20px" }}>
            {lang === "en" ? "Chat Workspace" : "Không gian Trò chuyện"}
          </h3>
        )}
        <div className="chat-pane" style={{ flex: 1, display: "flex", flexDirection: "column", width: "100%", minHeight: isMobile ? "0px" : "350px" }}>
          <div className="chat-header" style={{ padding: isMobile ? "8px 12px" : "16px 20px" }}>
            <span className="coach-status-dot"></span>
            <span className="chat-header-title" style={{ fontSize: isMobile ? "13px" : "16px" }}>
              {lang === "en" ? "Coach Uphill (AI)" : "Huấn luyện viên Uphill (AI)"}
            </span>
          </div>

          <div className="chat-history" style={{ padding: isMobile ? "8px" : "20px", gap: isMobile ? "8px" : "16px", minHeight: 0, flex: 1, height: isMobile ? "0px" : undefined, overflowY: "auto" }}>
            {chatMessages.map((msg: any, idx: any) => (
              <div
                key={idx}
                className={`chat-bubble ${msg.role === "user" ? "chat-bubble-user" : "chat-bubble-assistant"}`}
                style={{ fontSize: isMobile ? "13px" : "14.5px", padding: isMobile ? "8px 12px" : "12px 18px", maxWidth: isMobile ? "90%" : "80%" }}
              >
                {msg.role === "assistant"
                  ? parseMarkdown(idx === 0 ? welcomeText : msg.content)
                  : msg.content}
              </div>
            ))}
            {chatLoading && (
              <div className="chat-bubble chat-bubble-assistant" style={{ fontStyle: "italic", opacity: 0.7, fontSize: isMobile ? "13px" : "14.5px", padding: isMobile ? "8px 12px" : "12px 18px" }}>
                {lang === "en" ? "Coach Uphill is thinking..." : "Coach Uphill đang suy nghĩ..."}
              </div>
            )}
            <div ref={chatBottomRef}></div>
          </div>

          <div className="preset-prompt-list" style={{ padding: isMobile ? "0 8px" : "0 20px", gap: "4px", marginBottom: isMobile ? "4px" : "8px" }}>
            <button className="preset-prompt-btn" style={{ fontSize: isMobile ? "10px" : "12px", padding: isMobile ? "3px 8px" : "4px 10px" }}
              onClick={() => sendPresetPrompt(lang === "en" ? "Can you give me an ME workout for trails?" : "Bạn có thể cho tôi một bài tập ME chạy địa hình không?")}>
              {lang === "en" ? "ME Workout" : "Bài tập ME"}
            </button>
            <button className="preset-prompt-btn" style={{ fontSize: isMobile ? "10px" : "12px", padding: isMobile ? "3px 8px" : "4px 10px" }}
              onClick={() => sendPresetPrompt(lang === "en" ? "How does the 80/20 rule work?" : "Quy tắc 80/20 hoạt động như thế nào?")}>
              {lang === "en" ? "80/20 Rule" : "Quy tắc 80/20"}
            </button>
          </div>

          <div className="chat-input-bar" style={{ padding: isMobile ? "12px" : "16px" }}>
            <input
              type="text"
              className="chat-input"
              style={{ padding: isMobile ? "10px 16px" : "12px 16px", fontSize: "14px" }}
              placeholder={t("chat_input_placeholder")}
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
              disabled={chatLoading}
            />
            <button className="chat-send-btn" style={{ width: isMobile ? "38px" : "44px", height: isMobile ? "38px" : "44px" }}
              onClick={() => handleSendMessage()} disabled={chatLoading}>
              <svg width={isMobile ? "15" : "18"} height={isMobile ? "15" : "18"} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
