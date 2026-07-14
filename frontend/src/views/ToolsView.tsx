/* eslint-disable @typescript-eslint/no-explicit-any */
import { useAppContext } from "../contexts/AppContext";
import { BowlFood, Sneaker, Gauge, Crosshair } from '@phosphor-icons/react';

export default function ToolsView({ isMobile }: { isMobile: boolean }) {
  const ctx = useAppContext();
  const { lang, setIsNutritionLabOpen, setIsGearVaultOpen, setIsPaceStrategyOpen, setIsGoalDeterminerOpen } = ctx;

    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        {/* Card 1: Precision Fueling Engine (Launch Button) */}
        <div className="card" style={{ padding: isMobile ? "16px" : "24px", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", textAlign: "center", cursor: "pointer", border: "1px solid var(--accent-primary)" }} onClick={() => setIsNutritionLabOpen(true)}>
          <BowlFood size={48} color="var(--accent-primary)" weight="duotone" style={{ marginBottom: "16px" }} />
          <h3 style={{ fontSize: isMobile ? "18px" : "20px", marginBottom: "8px", color: "var(--text-primary)" }}>
            Nutrition Lab
          </h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "13px", marginBottom: "0" }}>
            {lang === "en"
              ? "Launch the metabolic command center to calculate custom gel recipes."
              : "Mở trung tâm dinh dưỡng để tính toán công thức gel tùy chỉnh."}
          </p>
        </div>

        {/* Card 2: Gear Finder (Launch Button) */}
        <div className="card" style={{ padding: isMobile ? "16px" : "24px", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", textAlign: "center", cursor: "pointer", border: "1px solid var(--accent-primary)" }} onClick={() => setIsGearVaultOpen(true)}>
          <Sneaker size={48} color="var(--accent-primary)" weight="duotone" style={{ marginBottom: "16px" }} />
          <h3 style={{ fontSize: isMobile ? "18px" : "20px", marginBottom: "8px", color: "var(--text-primary)" }}>
            Gear Finder
          </h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "13px", marginBottom: "0" }}>
            {lang === "en"
              ? "Launch the technical equipment matching vault."
              : "Mở kho tìm kiếm trang bị kỹ thuật."}
          </p>
        </div>

        {/* Card 3: Pace Strategy (Launch Button) */}
        <div className="card" style={{ padding: isMobile ? "16px" : "24px", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", textAlign: "center", cursor: "pointer", border: "1px solid var(--accent-primary)" }} onClick={() => setIsPaceStrategyOpen(true)}>
          <Gauge size={48} color="var(--accent-primary)" weight="duotone" style={{ marginBottom: "16px" }} />
          <h3 style={{ fontSize: isMobile ? "18px" : "20px", marginBottom: "8px", color: "var(--text-primary)" }}>
            Pace Strategy
          </h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "13px", marginBottom: "0" }}>
            {lang === "en"
              ? "Turn a target finish time into a segment-by-segment race pacing plan."
              : "Biến thời gian về đích mục tiêu thành kế hoạch pacing theo từng đoạn."}
          </p>
        </div>

        {/* Card 4: Goal Determiner (Launch Button) */}
        <div className="card" style={{ padding: isMobile ? "16px" : "24px", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", textAlign: "center", cursor: "pointer", border: "1px solid var(--accent-primary)" }} onClick={() => setIsGoalDeterminerOpen(true)}>
          <Crosshair size={48} color="var(--accent-primary)" weight="duotone" style={{ marginBottom: "16px" }} />
          <h3 style={{ fontSize: isMobile ? "18px" : "20px", marginBottom: "8px", color: "var(--text-primary)" }}>
            Goal Determiner
          </h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "13px", marginBottom: "0" }}>
            {lang === "en"
              ? "Find out what finish time you could realistically target at your next race."
              : "Tìm ra thời gian về đích thực tế cho giải chạy sắp tới của bạn."}
          </p>
        </div>

      </div>
    );
}
