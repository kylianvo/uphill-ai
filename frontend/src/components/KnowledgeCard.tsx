/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState } from "react";
import { Book, Mountains, BowlFood, Bed, Timer, Brain, Backpack, CaretDown, CaretUp } from "@phosphor-icons/react";
import { useAnalytics } from "../hooks/useAnalytics";

export const topicColors: Record<string, string> = {
  Training: "#3b82f6", Nutrition: "#10b981", Recovery: "#8b5cf6",
  Pacing: "#f59e0b", Mindset: "#ec4899", Gear: "#14b8a6",
};

export const topicIcons: Record<string, React.ReactNode> = {
  Training: <Mountains weight="fill" />,
  Nutrition: <BowlFood weight="fill" />,
  Recovery: <Bed weight="fill" />,
  Pacing: <Timer weight="fill" />,
  Mindset: <Brain weight="fill" />,
  Gear: <Backpack weight="fill" />,
};

export const KnowledgeCard = ({ card, expanded = false }: { card: any; expanded?: boolean }) => {
  const [open, setOpen] = useState(expanded);
  const { trackEvent } = useAnalytics();
  const color = topicColors[card.topic] || "#6366f1";
  const icon = topicIcons[card.topic] || <Book weight="fill" />;

  const handleToggle = () => {
    if (!open) {
      trackEvent('knowledge_card_clicked', { topic: card.topic, chapter_title: card.chapter_title });
    }
    setOpen(!open);
  };

  return (
    <div style={{
      background: "var(--bg-card)", border: `1px solid var(--border-color)`,
      borderRadius: "14px", padding: "16px", cursor: "pointer",
      transition: "all 0.2s cubic-bezier(0.16, 1, 0.3, 1)", backdropFilter: "blur(8px)",
      boxShadow: "inset 0 1px 0 rgba(255,255,255,0.05)"
    }}
      onClick={handleToggle}
      onMouseEnter={e => {
        e.currentTarget.style.background = "var(--bg-card-hover)";
        e.currentTarget.style.transform = "translateY(-1px)";
      }}
      onMouseLeave={e => {
        e.currentTarget.style.background = "var(--bg-card)";
        e.currentTarget.style.transform = "translateY(0)";
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "8px", marginBottom: "8px" }}>
        <span style={{
          display: "flex", alignItems: "center", gap: "4px",
          fontSize: "10px", fontWeight: "700", padding: "4px 8px", borderRadius: "20px",
          background: `${color}22`, color: color, letterSpacing: "0.5px", flexShrink: 0,
        }}>{icon} {card.topic?.toUpperCase()}</span>
        <span style={{ fontSize: "14px", color: "var(--text-muted)", flexShrink: 0 }}>
          {open ? <CaretUp weight="bold" /> : <CaretDown weight="bold" />}
        </span>
      </div>
      <div style={{ fontWeight: "700", fontSize: "14px", color: "var(--text-bright)", marginBottom: "8px", lineHeight: "1.4" }}>
        {card.chapter_title}
      </div>
      <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.6", margin: 0 }}>
        {card.summary}
      </p>
      {open && card.key_points?.length > 0 && (
        <ul style={{ marginTop: "12px", paddingLeft: "16px", display: "flex", flexDirection: "column", gap: "6px" }}>
          {card.key_points.map((pt: string, i: number) => (
            <li key={i} style={{ fontSize: "12.5px", color: "var(--text-secondary)", lineHeight: "1.5" }}>
              {pt}
            </li>
          ))}
        </ul>
      )}
      {open && card.tags?.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "4px", marginTop: "10px" }}>
          {card.tags.map((tag: string, i: number) => (
            <span key={i} style={{
              fontSize: "10px", padding: "2px 6px", borderRadius: "10px",
              background: "rgba(255,255,255,0.1)", color: "var(--text-muted)",
            }}>#{tag}</span>
          ))}
        </div>
      )}
    </div>
  );
};
