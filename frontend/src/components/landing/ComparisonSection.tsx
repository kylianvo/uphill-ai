import { BookOpen, Fingerprint, ShieldCheck, CaretDown, ArrowUpRight, Mountains, ChatCircle, PlugsConnected, CalendarBlank, Watch, Heartbeat, ArrowsClockwise, Target, Users } from "@phosphor-icons/react";
import { COMPARISON_COPY, COMPARISON_SOURCES } from "./comparisonCopy";
import styles from "./ComparisonSection.module.css";

const ICONS = [BookOpen, Fingerprint, ShieldCheck];
const CATEGORY_ICONS = [Mountains, ChatCircle, PlugsConnected, CalendarBlank, Watch];
const ROW_ICONS = [BookOpen, Heartbeat, Mountains, ShieldCheck, ArrowsClockwise, Target, Users, Watch];

export function ComparisonSection({ lang }: { lang: "en" | "vi" }) {
  const copy = COMPARISON_COPY[lang];

  return (
    <section className={styles.section} aria-labelledby="comparison-heading" lang={lang}>
      <header className={`${styles.header} scroll-reveal`}>
        <h2 id="comparison-heading">{copy.heading}</h2>
        <p>{copy.intro}</p>
      </header>

      <div className={styles.highlights}>
        {copy.cards.map((card, index) => {
          const Icon = ICONS[index];
          return (
            <article className={`${styles.highlight} scroll-reveal stagger-${index + 1} ${index === 1 ? styles.context : ""}`} key={card.title}>
              <div className={styles.highlightTitle}>
                <Icon size={28} weight="duotone" aria-hidden="true" />
                <h3>{card.title}</h3>
              </div>
              <p>{card.body}</p>
              {index === 1 && <div className={styles.contextSignals} aria-hidden="true">
                <span><Heartbeat size={18} />AeT / AnT</span>
                <span><Watch size={18} />HRV</span>
                <span><Mountains size={18} />{lang === "en" ? "Race profile" : "Profile Race"}</span>
                <span><CalendarBlank size={18} />{lang === "en" ? "Your schedule" : "Lịch của bạn"}</span>
              </div>}
            </article>
          );
        })}
      </div>

      <div className={styles.desktop}>
        <table className={styles.table} aria-labelledby="comparison-heading">
          <thead>
            <tr>
              <td />
              {copy.columns.map((column, index) => {
                const examples = column.indexOf(" (");
                const Icon = CATEGORY_ICONS[index];
                return <th key={column} scope="col">
                  <span className={styles.categoryIcon}><Icon size={24} weight="duotone" aria-hidden="true" /></span>
                  {examples < 0 ? column : <>{column.slice(0, examples)}<span className={styles.examples}>{column.slice(examples + 1)}</span></>}
                </th>;
              })}
            </tr>
          </thead>
          <tbody>
            {copy.rows.map((row, rowIndex) => {
              const Icon = ROW_ICONS[rowIndex];
              return <tr key={row.label} className="scroll-reveal">
                <th scope="row"><span className={styles.rowLabel}><Icon size={19} weight="duotone" aria-hidden="true" />{row.label}</span></th>
                {row.cells.map((cell, index) => <td key={index}>{cell}</td>)}
              </tr>;
            })}
          </tbody>
        </table>
      </div>

      <div className={styles.mobile}>
        {copy.columns.slice(1).map((column, index) => {
          const Icon = CATEGORY_ICONS[index + 1];
          return <article key={column} className={`${styles.competitor} scroll-reveal`}>
            <details open={index === 0}>
              <summary><span className={styles.categoryIcon}><Icon size={24} weight="duotone" aria-hidden="true" /></span><h3>{column}</h3><CaretDown size={20} aria-hidden="true" /></summary>
            <dl>
              {copy.rows.map((row) => (
                <div key={row.label} className={styles.mobileRow}>
                  <dt>{row.label}</dt>
                  <dd><strong>Uphill AI</strong><span>{row.cells[0]}</span></dd>
                  <dd><strong>{column}</strong><span>{row.cells[index + 1]}</span></dd>
                </div>
              ))}
            </dl>
            </details>
          </article>;
        })}
      </div>

      <p className={styles.honesty}>{copy.honesty}</p>
      <footer className={styles.footer}>
        <p>{copy.footnote}</p>
        <ul>
          {COMPARISON_SOURCES.map((source) => (
            <li key={source.url}><a href={source.url} target="_blank" rel="noopener noreferrer">{source.label}<ArrowUpRight size={13} aria-hidden="true" /></a></li>
          ))}
        </ul>
      </footer>
    </section>
  );
}
