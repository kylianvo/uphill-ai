import React from "react";

export const parseInlineStyles = (text: string): React.ReactNode[] => {
  const parts = text.split("**");
  return parts.map((part, index) => {
    if (index % 2 === 1) {
      return <strong key={index} style={{ fontWeight: "700", color: "var(--text-bright)" }}>{part}</strong>;
    }
    return part;
  });
};

export const parseMarkdown = (text: string) => {
  if (!text) return null;
  const lines = text.split("\n");
  return lines.map((line, lineIdx) => {
    const trimmed = line.trim();
    if (trimmed.startsWith("### ")) {
      return (
        <h4 key={lineIdx} style={{ fontSize: "15px", fontWeight: "700", marginTop: "12px", marginBottom: "6px", color: "var(--accent-secondary)" }}>
          {parseInlineStyles(trimmed.substring(4))}
        </h4>
      );
    }
    if (trimmed.startsWith("## ")) {
      return (
        <h3 key={lineIdx} style={{ fontSize: "16px", fontWeight: "700", marginTop: "16px", marginBottom: "8px", color: "var(--accent-secondary)" }}>
          {parseInlineStyles(trimmed.substring(3))}
        </h3>
      );
    }
    if (trimmed.startsWith("# ")) {
      return (
        <h2 key={lineIdx} style={{ fontSize: "18px", fontWeight: "700", marginTop: "20px", marginBottom: "10px", color: "var(--accent-secondary)" }}>
          {parseInlineStyles(trimmed.substring(2))}
        </h2>
      );
    }
    const isBullet = trimmed.startsWith("* ") || trimmed.startsWith("- ") || trimmed.startsWith("• ");
    if (isBullet) {
      return (
        <li key={lineIdx} style={{ marginLeft: "16px", marginBottom: "4px", listStyleType: "disc" }}>
          {parseInlineStyles(trimmed.substring(2))}
        </li>
      );
    }
    const numMatch = trimmed.match(/^(\d+)\.\s(.*)/);
    if (numMatch) {
      return (
        <li key={lineIdx} style={{ marginLeft: "16px", marginBottom: "4px", listStyleType: "decimal" }}>
          {parseInlineStyles(numMatch[2])}
        </li>
      );
    }
    if (trimmed === "") {
      return <div key={lineIdx} style={{ height: "8px" }} />;
    }
    return (
      <p key={lineIdx} style={{ marginBottom: "6px", lineHeight: "1.4" }}>
        {parseInlineStyles(line)}
      </p>
    );
  });
};
