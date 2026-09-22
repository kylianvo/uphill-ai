import { translations } from "../app/translations";

interface ClarificationChipsBarProps {
  options: string[];
  onSelect: (option: string) => void;
  lang: string;
}

export default function ClarificationChipsBar({ options, onSelect, lang }: ClarificationChipsBarProps) {
  if (!options.length) return null;

  const t = (key: keyof typeof translations.en) =>
    translations[lang as keyof typeof translations]?.[key] || translations.en[key] || key;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
      <div style={{ fontSize: "13px", fontWeight: 500, color: "var(--text-secondary)" }}>
        {t("chat_clarify_hint")}
      </div>
      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
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
    </div>
  );
}
