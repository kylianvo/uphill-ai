import React from "react";
import { useRaceMatch, RaceMatch, RaceCandidate } from "../hooks/useRaceMatch";
import { RaceMatchChip } from "./RaceMatchChip";

interface RaceNameFieldProps {
  value: string;
  onChange: (value: string) => void;
  lang: "en" | "vi";
  distanceKm?: number | string;
  distanceLabel?: string;
  onMatchChange?: (match: RaceMatch | null) => void;
  placeholder?: string;
  className?: string;
  style?: React.CSSProperties;
}

function candidateLabel(candidate: RaceCandidate): string {
  const parts = [
    candidate.distance_label,
    candidate.elevation_gain_m ? `${candidate.elevation_gain_m}m D+` : null,
  ].filter(Boolean);
  return parts.length ? `${candidate.race_name} — ${parts.join(", ")}` : candidate.race_name;
}

export function RaceNameField({
  value,
  onChange,
  lang,
  distanceKm,
  distanceLabel,
  onMatchChange,
  placeholder,
  className,
  style,
}: RaceNameFieldProps) {
  const { selectedMatch, candidates, selectCandidate, reopenPicker, dismissCandidates } = useRaceMatch(value, {
    distanceKm,
    distanceLabel,
  });
  const [activeIndex, setActiveIndex] = React.useState(0);
  const lastReportedMatch = React.useRef<RaceMatch | null>(null);

  React.useEffect(() => {
    if (lastReportedMatch.current !== selectedMatch) {
      lastReportedMatch.current = selectedMatch;
      onMatchChange?.(selectedMatch);
    }
    // Deliberately reacting only to selectedMatch, not onMatchChange identity,
    // so re-renders from unrelated parent state don't re-fire the callback.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedMatch]);

  React.useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setActiveIndex(0);
  }, [candidates]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (candidates.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, candidates.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      selectCandidate(candidates[activeIndex]);
    } else if (e.key === "Escape") {
      e.preventDefault();
      dismissCandidates();
    }
  };

  return (
    <div style={{ position: "relative" }}>
      <input
        type="text"
        className={className}
        style={style}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        role="combobox"
        aria-expanded={candidates.length > 0}
        aria-autocomplete="list"
      />
      {candidates.length > 0 && (
        <ul
          role="listbox"
          style={{
            marginTop: "6px",
            marginBottom: 0,
            paddingLeft: 0,
            listStyle: "none",
            border: "1px solid var(--border-color)",
            borderRadius: "8px",
            overflow: "hidden",
          }}
        >
          {candidates.map((candidate, index) => (
            <li
              key={`${index}-${candidate.race_name}-${candidate.distance_label ?? ""}`}
              role="option"
              aria-selected={index === activeIndex}
              style={{
                padding: "8px 10px",
                fontSize: "12px",
                cursor: "pointer",
                background: index === activeIndex ? "rgba(16,185,129,0.12)" : "transparent",
                color: "var(--text-secondary)",
              }}
              onMouseEnter={() => setActiveIndex(index)}
              onMouseDown={(e) => {
                e.preventDefault();
                selectCandidate(candidate);
              }}
            >
              {candidateLabel(candidate)}
            </li>
          ))}
        </ul>
      )}
      {candidates.length === 0 && <RaceMatchChip match={selectedMatch} lang={lang} onChangeClick={reopenPicker} />}
    </div>
  );
}
