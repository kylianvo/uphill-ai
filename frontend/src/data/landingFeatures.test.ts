import { describe, it, expect } from "vitest";
import { LANDING_FEATURES } from "./landingFeatures";
import { GLOSSARY, GlossaryKey } from "./glossary";

const TERM_MARKER = /\{\{term:([a-z_]+)\}\}/g;

function extractTermKeys(text: string): string[] {
  const keys: string[] = [];
  let match: RegExpExecArray | null;
  TERM_MARKER.lastIndex = 0;
  while ((match = TERM_MARKER.exec(text)) !== null) {
    keys.push(match[1]);
  }
  return keys;
}

describe("LANDING_FEATURES data integrity", () => {
  it("has exactly 6 features in the expected order", () => {
    expect(LANDING_FEATURES.map((f) => f.id)).toEqual([
      "scheduler",
      "chatbot",
      "goal",
      "pace",
      "gear",
      "nutrition",
    ]);
  });

  it("every {{term:KEY}} marker in howItWorks references a real glossary key, for both languages", () => {
    for (const feature of LANDING_FEATURES) {
      for (const lang of ["en", "vi"] as const) {
        for (const line of feature[lang].howItWorks) {
          for (const key of extractTermKeys(line)) {
            expect(GLOSSARY[key as GlossaryKey], `${feature.id}.${lang}: unknown term key "${key}"`).toBeDefined();
          }
        }
      }
    }
  });

  it("every feature has non-empty copy for both languages", () => {
    for (const feature of LANDING_FEATURES) {
      for (const lang of ["en", "vi"] as const) {
        const copy = feature[lang];
        expect(copy.tagline.length).toBeGreaterThan(0);
        expect(copy.cardBlurb.length).toBeGreaterThan(0);
        expect(copy.overview.length).toBeGreaterThan(0);
        expect(copy.howItWorks.length).toBeGreaterThan(0);
        expect(copy.personalizedChips.length).toBeGreaterThan(0);
        expect(copy.alwaysUpdated.length).toBeGreaterThan(0);
      }
    }
  });
});
