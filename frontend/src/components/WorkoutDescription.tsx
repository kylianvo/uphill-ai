import React from 'react';

interface WorkoutDescriptionProps {
  description: string;
}

export default function WorkoutDescription({ description }: WorkoutDescriptionProps) {
  if (!description) return null;

  // Regex to extract sections.
  // Looks for keywords followed by a colon or dash, capturing the text until the next keyword or end of string.
  const extractSection = (keyword: string) => {
    // Escape keywords for regex safety although they are hardcoded
    const regex = new RegExp(`${keyword}[:\\-]\\s*([\\s\\S]*?)(?=(Process|Overall|Reason|Benefit|Warning)[:\\-]|$)`, 'i');
    const match = description.match(regex);
    return match ? match[1].trim() : null;
  };

  const sections = {
    overall: extractSection('Overall'),
    process: extractSection('Process'),
    reason: extractSection('Reason'),
    benefit: extractSection('Benefit'),
    warning: extractSection('Warning'),
  };

  // If no specific sections are found, fall back to rendering the raw text
  const hasSections = Object.values(sections).some((val) => val !== null);
  if (!hasSections) {
    return (
      <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginBottom: "8px", lineHeight: "1.4" }}>
        {description}
      </p>
    );
  }

  const labelStyle = {
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
    fontSize: "9px",
    textTransform: "uppercase" as const,
    letterSpacing: "0.15em",
    color: "var(--text-tertiary)",
    paddingTop: "3px", // Align with first line of adjacent text
  };

  const contentStyle = {
    fontSize: "13px",
    color: "var(--text-secondary)",
    lineHeight: "1.6",
  };

  const renderBold = (text: string | null) => {
    if (!text) return null;
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} style={{ fontWeight: 600, color: "var(--text-primary)" }}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      gap: "16px",
      marginTop: "16px",
      paddingTop: "16px",
      borderTop: "1px solid var(--border-subtle, rgba(128, 128, 128, 0.15))"
    }}>
      {/* Overall Summary */}
      {sections.overall && (
        <div style={{ ...contentStyle, color: "var(--text-primary)", maxWidth: "65ch" }}>
          {renderBold(sections.overall)}
        </div>
      )}

      {/* Asymmetric Spec Grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "100px 1fr",
        gap: "12px 16px"
      }}>
        {/* Execution / Process */}
        {sections.process && (
          <>
            <div style={labelStyle}>Execution</div>
            <div style={contentStyle}>{renderBold(sections.process)}</div>
          </>
        )}

        {/* Rationale / Reason */}
        {sections.reason && (
          <>
            <div style={labelStyle}>Rationale</div>
            <div style={contentStyle}>{renderBold(sections.reason)}</div>
          </>
        )}

        {/* Adaptation / Benefit */}
        {sections.benefit && (
          <>
            <div style={labelStyle}>Adaptation</div>
            <div style={{ ...contentStyle, color: "var(--accent-primary, #10b981)" }}>{renderBold(sections.benefit)}</div>
          </>
        )}

        {/* Warning Box */}
        {sections.warning && (
          <>
            <div style={{ ...labelStyle, color: "var(--accent-warning, #f43f5e)" }}>Warning</div>
            <div style={{ ...contentStyle, color: "var(--accent-warning, #f43f5e)", fontWeight: 500 }}>
              {renderBold(sections.warning)}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
