import React, { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { GLOSSARY, GlossaryKey } from "../../data/glossary";

const POPOVER_WIDTH = 220;
const VIEWPORT_MARGIN = 8;

export function TermTooltip({
  termKey,
  lang,
  children,
}: {
  termKey: GlossaryKey;
  lang: "en" | "vi";
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [popoverPosition, setPopoverPosition] = useState<{ top: number; left: number } | null>(null);
  const wrapperRef = useRef<HTMLSpanElement>(null);
  const tooltipRef = useRef<HTMLSpanElement>(null);
  const definition = GLOSSARY[termKey];

  useEffect(() => {
    if (!open || !wrapperRef.current) return;
    const rect = wrapperRef.current.getBoundingClientRect();
    const left = Math.min(
      Math.max(rect.left + rect.width / 2 - POPOVER_WIDTH / 2, VIEWPORT_MARGIN),
      window.innerWidth - POPOVER_WIDTH - VIEWPORT_MARGIN
    );
    setPopoverPosition({ top: rect.top - VIEWPORT_MARGIN, left });
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handleOutsideClick = (event: MouseEvent) => {
      const target = event.target as Node;
      const insideTrigger = wrapperRef.current?.contains(target);
      const insideTooltip = tooltipRef.current?.contains(target);
      if (!insideTrigger && !insideTooltip) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, [open]);

  if (!definition) {
    return <>{children}</>;
  }

  return (
    <span ref={wrapperRef} style={{ position: "relative", display: "inline-block" }}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        style={{
          background: "none",
          border: "none",
          padding: 0,
          font: "inherit",
          color: "var(--accent-primary)",
          fontWeight: 700,
          cursor: "pointer",
          textDecoration: "underline dotted",
        }}
      >
        {children}
        <sup style={{ fontSize: "9px", marginLeft: "1px" }}>i</sup>
      </button>
      {open &&
        popoverPosition &&
        typeof document !== "undefined" &&
        createPortal(
          <span
            ref={tooltipRef}
            role="tooltip"
            style={{
              position: "fixed",
              top: popoverPosition.top,
              left: popoverPosition.left,
              transform: "translateY(-100%)",
              width: `${POPOVER_WIDTH}px`,
              background: "var(--bg-card)",
              backdropFilter: "blur(24px)",
              WebkitBackdropFilter: "blur(24px)",
              border: "1px solid var(--border-color)",
              borderRadius: "12px",
              padding: "10px 12px",
              fontSize: "12px",
              lineHeight: 1.5,
              fontWeight: 400,
              color: "var(--text-secondary)",
              boxShadow: "0 10px 30px rgba(0,0,0,0.12)",
              zIndex: 2000,
              textAlign: "left",
            }}
          >
            {definition[lang]}
          </span>,
          document.body
        )}
    </span>
  );
}
