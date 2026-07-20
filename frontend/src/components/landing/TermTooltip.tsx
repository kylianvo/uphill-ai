import React, { useEffect, useRef, useState } from "react";
import { GLOSSARY, GlossaryKey } from "../../data/glossary";

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
  const wrapperRef = useRef<HTMLSpanElement>(null);
  const definition = GLOSSARY[termKey];

  useEffect(() => {
    if (!open) return;
    const handleOutsideClick = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
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
      {open && (
        <span
          role="tooltip"
          style={{
            position: "absolute",
            bottom: "calc(100% + 8px)",
            left: "50%",
            transform: "translateX(-50%)",
            width: "220px",
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
            zIndex: 50,
            textAlign: "left",
          }}
        >
          {definition[lang]}
        </span>
      )}
    </span>
  );
}
