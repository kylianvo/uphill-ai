import styles from "./TrainingWorkspace.module.css";
import { useAppContext } from "../contexts/AppContext";
import { BowlFood, Sneaker, Gauge, Crosshair, CaretRight } from '@phosphor-icons/react';

export default function ToolsView({ isMobile }: { isMobile: boolean }) {
  const ctx = useAppContext();
  const { lang, setIsNutritionLabOpen, setIsGearVaultOpen, setIsPaceStrategyOpen, setIsGoalDeterminerOpen } = ctx;

  const tools = [
    {
      id: "nutrition",
      title: "Nutrition Lab",
      desc:
        lang === "en"
          ? "Launch the metabolic command center to calculate custom gel recipes."
          : "Mở trung tâm dinh dưỡng để tính toán công thức gel tùy chỉnh.",
      icon: BowlFood,
      onClick: () => setIsNutritionLabOpen(true),
    },
    {
      id: "gear",
      title: "Gear Finder",
      desc:
        lang === "en"
          ? "Launch the technical equipment matching vault."
          : "Mở kho tìm kiếm trang bị kỹ thuật.",
      icon: Sneaker,
      onClick: () => setIsGearVaultOpen(true),
    },
    {
      id: "pace",
      title: "Pace Strategy",
      desc:
        lang === "en"
          ? "Turn a target finish time into a segment-by-segment race pacing plan."
          : "Biến thời gian về đích mục tiêu thành kế hoạch pacing theo từng đoạn.",
      icon: Gauge,
      onClick: () => setIsPaceStrategyOpen(true),
    },
    {
      id: "goal",
      title: "Goal Determiner",
      desc:
        lang === "en"
          ? "Find out what finish time you could realistically target at your next race."
          : "Tìm ra thời gian về đích thực tế cho giải chạy sắp tới của bạn.",
      icon: Crosshair,
      onClick: () => setIsGoalDeterminerOpen(true),
    },
  ];

  return (
    <section className={styles.tools} data-mobile={isMobile}>
      <h2>{lang === "en" ? "Tools" : "Công cụ"}</h2>
      <div className={styles.toolList}>
        {tools.map((tool) => {
          const Icon = tool.icon;
          return <button type="button" key={tool.id} className={styles.tool} onClick={tool.onClick}>
            <Icon size={28} weight="duotone" aria-hidden="true" />
            <span><span className={styles.toolTitle}>{tool.title}</span><span className={styles.toolDescription}>{tool.desc}</span></span>
            <CaretRight size={20} aria-hidden="true" />
          </button>;
        })}
      </div>
    </section>
  );
}
