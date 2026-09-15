/* eslint-disable @typescript-eslint/no-explicit-any */
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

  if (isMobile) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "12px", padding: "4px 0" }}>
        {tools.map((tool) => {
          const IconComponent = tool.icon;
          return (
            <div
              key={tool.id}
              className="card"
              onClick={tool.onClick}
              style={{
                padding: "16px",
                display: "flex",
                flexDirection: "row",
                alignItems: "center",
                gap: "14px",
                cursor: "pointer",
                background: "var(--bg-card)",
                border: "1px solid rgba(0, 0, 0, 0.08)",
                borderRadius: "16px",
                boxShadow: "0 2px 10px rgba(0, 0, 0, 0.04)",
                transition: "all 0.15s ease",
              }}
            >
              <div
                style={{
                  width: "48px",
                  height: "48px",
                  borderRadius: "14px",
                  background: "rgba(16, 185, 129, 0.1)",
                  border: "1px solid rgba(16, 185, 129, 0.2)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                }}
              >
                <IconComponent size={26} color="#059669" weight="duotone" />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3
                  style={{
                    fontSize: "16px",
                    fontWeight: "700",
                    margin: "0 0 4px 0",
                    color: "#0f172a",
                    lineHeight: "1.25",
                  }}
                >
                  {tool.title}
                </h3>
                <p
                  style={{
                    color: "#475569",
                    fontSize: "13px",
                    lineHeight: "1.4",
                    margin: 0,
                  }}
                >
                  {tool.desc}
                </p>
              </div>
              <CaretRight size={20} color="#94a3b8" weight="bold" style={{ flexShrink: 0 }} />
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {tools.map((tool) => {
        const IconComponent = tool.icon;
        return (
          <div
            key={tool.id}
            className="card"
            style={{
              padding: "24px",
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              alignItems: "center",
              textAlign: "center",
              cursor: "pointer",
              border: "1px solid var(--accent-primary)",
            }}
            onClick={tool.onClick}
          >
            <IconComponent
              size={48}
              color="var(--accent-primary)"
              weight="duotone"
              style={{ marginBottom: "16px" }}
            />
            <h3
              style={{
                fontSize: "20px",
                marginBottom: "8px",
                color: "var(--text-primary)",
              }}
            >
              {tool.title}
            </h3>
            <p
              style={{
                color: "var(--text-secondary)",
                fontSize: "13px",
                marginBottom: "0",
              }}
            >
              {tool.desc}
            </p>
          </div>
        );
      })}
    </div>
  );
}
