import React from "react";

export interface MarkdownOptions {
  citations?: Array<{
    ref?: string;
    source_id?: string;
    title?: string;
    book?: string;
    chapter?: string;
    section?: string;
    citation_label?: string;
    [key: string]: unknown;
  }>;
  onCitationClick?: (citation: unknown) => void;
}

const CITATION_REGEX = /\[ref:([a-zA-Z0-9_\-]+)\]|\[([a-f0-9]{8,16})\]|\[(\d{1,2})\](?!\()/g;

export const parseCitationsInText = (
  text: string,
  options?: MarkdownOptions,
  keyPrefix: string = "txt"
): React.ReactNode[] => {
  if (!text) return [];

  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  CITATION_REGEX.lastIndex = 0;
  while ((match = CITATION_REGEX.exec(text)) !== null) {
    // Text before match
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }

    const matchedRef = match[1] || match[2] || match[3];
    const citations = options?.citations || [];

    let displayIndex: number | string = matchedRef;
    let matchedCite = null;

    if (match[3]) {
      // Direct numeric index like [1]
      const num = parseInt(match[3], 10);
      displayIndex = num;
      if (num >= 1 && num <= citations.length) {
        matchedCite = citations[num - 1];
      }
    } else {
      // Hex hash or ref tag
      const foundIdx = citations.findIndex(
        (c) => c.ref === matchedRef || c.source_id === matchedRef || (c.ref && c.ref.startsWith(matchedRef))
      );
      if (foundIdx !== -1) {
        displayIndex = foundIdx + 1;
        matchedCite = citations[foundIdx];
      } else {
        displayIndex = 1;
      }
    }

    // Build rich book tooltip
    let tooltip = "Training for the Uphill Athlete";
    if (matchedCite) {
      if (matchedCite.citation_label) {
        tooltip = matchedCite.citation_label;
      } else if (matchedCite.book && matchedCite.chapter) {
        tooltip = `${matchedCite.book} — ${matchedCite.chapter}`;
      } else if (matchedCite.title) {
        tooltip = `Training for the Uphill Athlete — ${matchedCite.title}`;
      }
    }

    parts.push(
      <button
        type="button"
        key={`${keyPrefix}-cite-${match.index}`}
        className="chat-citation-pill"
        title={tooltip}
        aria-label={`Citation: ${tooltip}`}
        onClick={(e) => {
          e.stopPropagation();
          options?.onCitationClick?.(matchedCite || displayIndex);
        }}
        style={{
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          verticalAlign: "super",
          fontSize: "10.5px",
          fontWeight: "700",
          color: "#0284c7",
          backgroundColor: "rgba(2, 132, 199, 0.08)",
          border: "1px solid rgba(2, 132, 199, 0.22)",
          borderRadius: "4px",
          padding: "0 4px",
          margin: "0 2px",
          cursor: "pointer",
          lineHeight: "1.2",
          textDecoration: "none",
        }}
      >
        [{displayIndex}]
      </button>
    );

    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : [text];
};

export const parseInlineStyles = (
  text: string,
  options?: MarkdownOptions
): React.ReactNode[] => {
  const parts = text.split("**");
  return parts.flatMap((part, index) => {
    if (index % 2 === 1) {
      return (
        <strong key={index} style={{ fontWeight: "700", color: "var(--text-bright)" }}>
          {parseCitationsInText(part, options, `b-${index}`)}
        </strong>
      );
    }
    return parseCitationsInText(part, options, `t-${index}`);
  });
};

export const parseMarkdown = (text: string, options?: MarkdownOptions) => {
  if (!text) return null;
  const lines = text.split("\n");
  return lines.map((line, lineIdx) => {
    const trimmed = line.trim();
    if (trimmed.startsWith("### ")) {
      return (
        <h4 key={lineIdx} style={{ fontSize: "15px", fontWeight: "700", marginTop: "12px", marginBottom: "6px", color: "var(--accent-secondary)" }}>
          {parseInlineStyles(trimmed.substring(4), options)}
        </h4>
      );
    }
    if (trimmed.startsWith("## ")) {
      return (
        <h3 key={lineIdx} style={{ fontSize: "16px", fontWeight: "700", marginTop: "16px", marginBottom: "8px", color: "var(--accent-secondary)" }}>
          {parseInlineStyles(trimmed.substring(3), options)}
        </h3>
      );
    }
    if (trimmed.startsWith("# ")) {
      return (
        <h2 key={lineIdx} style={{ fontSize: "18px", fontWeight: "700", marginTop: "20px", marginBottom: "10px", color: "var(--accent-secondary)" }}>
          {parseInlineStyles(trimmed.substring(2), options)}
        </h2>
      );
    }
    const isBullet = trimmed.startsWith("* ") || trimmed.startsWith("- ") || trimmed.startsWith("• ");
    if (isBullet) {
      return (
        <li key={lineIdx} style={{ marginLeft: "16px", marginBottom: "4px", listStyleType: "disc" }}>
          {parseInlineStyles(trimmed.substring(2), options)}
        </li>
      );
    }
    const numMatch = trimmed.match(/^(\d+)\.\s(.*)/);
    if (numMatch) {
      return (
        <li key={lineIdx} style={{ marginLeft: "16px", marginBottom: "4px", listStyleType: "decimal" }}>
          {parseInlineStyles(numMatch[2], options)}
        </li>
      );
    }
    if (trimmed === "") {
      return <div key={lineIdx} style={{ height: "8px" }} />;
    }
    return (
      <p key={lineIdx} style={{ marginBottom: "6px", lineHeight: "1.4" }}>
        {parseInlineStyles(line, options)}
      </p>
    );
  });
};
