"use client";

import { useState } from "react";
import Link from "next/link";

export type LegalSection = {
  heading: string;
  body?: string[];
  bullets?: string[];
};

export type LegalContent = {
  title: string;
  updated: string;
  intro: string[];
  sections: LegalSection[];
  footer?: string;
};

/**
 * Shell for the standalone legal/support routes (/privacy, /support).
 *
 * Deliberately self-contained: it holds its own language state instead of
 * reading AppContext, because these pages must render correctly for a logged-out
 * visitor -- an API partner reviewing our integration, or an app-store reviewer --
 * who never touches the authenticated app.
 *
 * Styling uses the .legal-* classes in globals.css. This project configures
 * Tailwind in postcss.config but never imports it into globals.css, so utility
 * classes do not exist -- follow the hand-written CSS convention instead.
 */
export default function LegalShell({ en, vi }: { en: LegalContent; vi: LegalContent }) {
  const [lang, setLang] = useState<"en" | "vi">("en");
  const c = lang === "vi" ? vi : en;

  return (
    <main className="legal-page">
      <div className="legal-container">
        <nav className="legal-nav">
          <Link href="/" className="legal-back">
            ← Uphill AI
          </Link>
          <div className="legal-lang">
            {(["en", "vi"] as const).map((code) => (
              <button
                key={code}
                type="button"
                onClick={() => setLang(code)}
                aria-pressed={lang === code}
                className={`legal-lang-btn${lang === code ? " is-active" : ""}`}
              >
                {code === "en" ? "EN" : "VI"}
              </button>
            ))}
          </div>
        </nav>

        <header className="legal-header">
          <h1 className="legal-title">{c.title}</h1>
          <p className="legal-updated">{c.updated}</p>
        </header>

        {c.intro.map((p, i) => (
          <p key={i} className="legal-p">
            {p}
          </p>
        ))}

        {c.sections.map((s, i) => (
          <section key={i} className="legal-section">
            <h2 className="legal-heading">{s.heading}</h2>
            {s.body?.map((p, j) => (
              <p key={j} className="legal-p">
                {p}
              </p>
            ))}
            {s.bullets && (
              <ul className="legal-list">
                {s.bullets.map((b, j) => (
                  <li key={j}>{b}</li>
                ))}
              </ul>
            )}
          </section>
        ))}

        {c.footer && <p className="legal-footer">{c.footer}</p>}
      </div>
    </main>
  );
}
