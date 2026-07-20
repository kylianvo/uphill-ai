import React from "react";
import { TermTooltip } from "./TermTooltip";
import { GlossaryKey } from "../../data/glossary";

const TERM_PATTERN = /\{\{term:([a-z_]+)\}\}(.*?)\{\{\/term\}\}/g;

export function renderWithTerms(text: string, lang: "en" | "vi"): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  TERM_PATTERN.lastIndex = 0;
  while ((match = TERM_PATTERN.exec(text)) !== null) {
    if (match.index > lastIndex) {
      nodes.push(text.slice(lastIndex, match.index));
    }
    const [, termKey, label] = match;
    nodes.push(
      <TermTooltip key={`term-${key++}`} termKey={termKey as GlossaryKey} lang={lang}>
        {label}
      </TermTooltip>
    );
    lastIndex = TERM_PATTERN.lastIndex;
  }
  if (lastIndex < text.length) {
    nodes.push(text.slice(lastIndex));
  }
  return nodes;
}
