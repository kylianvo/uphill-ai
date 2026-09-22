interface ClarificationChipsBarProps {
  options: string[];
  onSelect: (option: string) => void;
}

export default function ClarificationChipsBar({ options, onSelect }: ClarificationChipsBarProps) {
  if (!options.length) return null;
  return (
    <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", padding: "8px 0" }}>
      {options.map((opt) => (
        <button
          key={opt}
          onClick={() => onSelect(opt)}
          style={{
            padding: "6px 14px",
            borderRadius: "999px",
            border: "1px solid rgba(0,0,0,0.12)",
            backgroundColor: "rgba(255,255,255,0.8)",
            fontSize: "13px",
            cursor: "pointer",
          }}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}
