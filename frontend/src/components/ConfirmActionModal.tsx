"use client";

import React, { useEffect } from "react";
import { createPortal } from "react-dom";
import { X, Warning, Check, Trash } from "@phosphor-icons/react";

export interface ConfirmActionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string | React.ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  isDestructive?: boolean;
  isLoading?: boolean;
}

export default function ConfirmActionModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  isDestructive = false,
  isLoading = false,
}: ConfirmActionModalProps) {
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isLoading) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, isLoading, onClose]);

  if (!isOpen) return null;

  const content = (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-modal-title"
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0, 0, 0, 0.65)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
        padding: "16px",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget && !isLoading) onClose();
      }}
    >
      <div
        style={{
          background: "var(--bg-card, #18181b)",
          color: "var(--text-primary, #ffffff)",
          border: "1px solid var(--border-color, #27272a)",
          borderRadius: "16px",
          width: "100%",
          maxWidth: "420px",
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.4)",
          overflow: "hidden",
          animation: "scaleIn 0.15s ease-out",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "16px 20px",
            borderBottom: "1px solid var(--border-color, #27272a)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "32px",
                height: "32px",
                borderRadius: "8px",
                background: isDestructive ? "rgba(239, 68, 68, 0.15)" : "rgba(16, 185, 129, 0.15)",
                color: isDestructive ? "#ef4444" : "#10b981",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              {isDestructive ? <Trash size={18} weight="bold" /> : <Warning size={18} weight="bold" />}
            </div>
            <h3
              id="confirm-modal-title"
              style={{ margin: 0, fontSize: "16px", fontWeight: "600", color: "var(--text-primary, #ffffff)" }}
            >
              {title}
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            aria-label="Close"
            style={{
              background: "none",
              border: "none",
              color: "var(--text-muted, #71717a)",
              cursor: isLoading ? "not-allowed" : "pointer",
              padding: "4px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              borderRadius: "6px",
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Message */}
        <div style={{ padding: "20px", fontSize: "14px", lineHeight: "1.6", color: "var(--text-secondary, #d4d4d8)" }}>
          {message}
        </div>

        {/* Action Buttons */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-end",
            gap: "10px",
            padding: "14px 20px",
            borderTop: "1px solid var(--border-color, #27272a)",
            background: "rgba(0, 0, 0, 0.15)",
          }}
        >
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            style={{
              padding: "8px 16px",
              borderRadius: "8px",
              fontSize: "13px",
              fontWeight: "600",
              cursor: isLoading ? "not-allowed" : "pointer",
              background: "transparent",
              border: "1px solid var(--border-color, #3f3f46)",
              color: "var(--text-primary, #ffffff)",
              opacity: isLoading ? 0.6 : 1,
            }}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isLoading}
            style={{
              padding: "8px 18px",
              borderRadius: "8px",
              fontSize: "13px",
              fontWeight: "600",
              cursor: isLoading ? "not-allowed" : "pointer",
              background: isDestructive ? "#ef4444" : "#10b981",
              border: "none",
              color: "#ffffff",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              opacity: isLoading ? 0.7 : 1,
              boxShadow: isDestructive
                ? "0 4px 12px rgba(239, 68, 68, 0.25)"
                : "0 4px 12px rgba(16, 185, 129, 0.25)",
            }}
          >
            {isDestructive ? <Trash size={15} weight="bold" /> : <Check size={15} weight="bold" />}
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );

  return typeof document !== "undefined" ? createPortal(content, document.body) : null;
}
