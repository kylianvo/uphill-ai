"use client";
import React, { useEffect } from "react";
import { createPortal } from "react-dom";
import { X } from "@phosphor-icons/react";

/** The dialog frame shared by the B-race sheets (same overlay as ConfirmActionModal). */
export default function BRaceModalShell({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const content = (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={title}
      style={{ position: "fixed", inset: 0, backgroundColor: "rgba(0,0,0,0.65)", backdropFilter: "blur(4px)", display: "flex",
        alignItems: "center", justifyContent: "center", zIndex: 9999, padding: "16px" }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div style={{ background: "#ffffff", borderRadius: "16px", width: "100%", maxWidth: "460px", maxHeight: "90vh",
        overflowY: "auto", padding: "20px", display: "flex", flexDirection: "column", gap: "14px", color: "#17231d", boxShadow: "0 12px 40px rgba(0,0,0,0.25)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <h3 style={{ margin: 0, fontSize: "17px" }}>{title}</h3>
          <button type="button" aria-label="Close" onClick={onClose}
            style={{ border: "none", background: "none", cursor: "pointer", minWidth: 44, minHeight: 44, color: "inherit" }}>
            <X size={20} aria-hidden="true" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
  return typeof document !== "undefined" ? createPortal(content, document.body) : content;
}
