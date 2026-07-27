"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useState } from "react";
import { ChatCircleText } from "@phosphor-icons/react";
import { useCoachNotes } from "../hooks/useCoachNotes";

export function CoachNoteThread({
  athleteId,
  targetType,
  targetId,
  lang,
  canAdd,
}: {
  athleteId: number | null;
  targetType: string;
  targetId: number | null;
  lang: "en" | "vi";
  canAdd: boolean;
}) {
  const { notes, fetchNotes, addNote } = useCoachNotes(athleteId, targetType, targetId);
  const [expanded, setExpanded] = useState(false);
  const [draft, setDraft] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (athleteId) fetchNotes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [athleteId, targetType, targetId]);

  if (!athleteId) return null;

  const handleAdd = async () => {
    if (!draft.trim()) return;
    setSaving(true);
    await addNote(draft.trim());
    setDraft("");
    setSaving(false);
  };

  return (
    <div style={{ marginTop: "6px" }}>
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "6px",
          padding: "6px 10px",
          background: "rgba(16,185,129,0.08)",
          border: "1px solid var(--border-color)",
          borderRadius: "8px",
          fontSize: "12px",
          color: "var(--text-secondary)",
          cursor: "pointer",
        }}
      >
        <ChatCircleText size={14} weight="fill" />
        {lang === "en" ? `Coach notes (${notes.length})` : `Ghi chú HLV (${notes.length})`}
      </button>

      {expanded && (
        <div
          style={{
            marginTop: "8px",
            padding: "10px 12px",
            border: "1px solid var(--border-color)",
            borderRadius: "8px",
            background: "rgba(255,255,255,0.5)",
          }}
        >
          {notes.length === 0 ? (
            <p style={{ fontSize: "12px", color: "var(--text-muted)", margin: 0 }}>
              {lang === "en" ? "No notes yet." : "Chưa có ghi chú nào."}
            </p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {notes.map((n: any) => (
                <div key={n.id} style={{ fontSize: "12.5px", color: "var(--text-primary)" }}>
                  {n.note}
                </div>
              ))}
            </div>
          )}

          {canAdd && (
            <div style={{ display: "flex", gap: "6px", marginTop: "10px" }}>
              <input
                type="text"
                className="chat-input"
                style={{ flex: 1, borderRadius: "8px", padding: "8px 10px", fontSize: "12px" }}
                placeholder={lang === "en" ? "Add a note…" : "Thêm ghi chú…"}
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
              />
              <button
                className="btn btn-primary"
                disabled={!draft.trim() || saving}
                onClick={handleAdd}
                style={{ padding: "8px 14px", fontSize: "12px" }}
              >
                {lang === "en" ? "Add" : "Thêm"}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
