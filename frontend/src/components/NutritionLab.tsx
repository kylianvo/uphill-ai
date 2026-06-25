"use client";

import React, { useState } from "react";
import { BowlFood, XCircle, Target } from "@phosphor-icons/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface NutritionLabProps {
  isOpen: boolean;
  onClose: () => void;
  lang: "en" | "vi";
  user?: any;
  activePlan?: any;
}

export const NutritionLab: React.FC<NutritionLabProps> = ({ isOpen, onClose, lang, user, activePlan }) => {
  const [fuelDuration, setFuelDuration] = useState("4.0");
  const [fuelTemp, setFuelTemp] = useState("moderate");
  const [fuelFormats, setFuelFormats] = useState<string[]>(["gel"]);
  const [athleteLevel, setAthleteLevel] = useState("Recreational");
  const [preferredBrands, setPreferredBrands] = useState("");
  const [additionalContext, setAdditionalContext] = useState("");
  const [targetCarb, setTargetCarb] = useState("60");
  const [targetSodium, setTargetSodium] = useState("500");
  
  const [fuelStrategy, setFuelStrategy] = useState<string | null>(null);
  const [fuelLoading, setFuelLoading] = useState(false);

  if (!isOpen) return null;

  const toggleFormat = (f: string) => {
    if (fuelFormats.includes(f)) {
      if (fuelFormats.length > 1) setFuelFormats(fuelFormats.filter(x => x !== f));
    } else {
      setFuelFormats([...fuelFormats, f]);
    }
  };

  const handleCalculateFueling = async () => {
    setFuelLoading(true);
    setFuelStrategy(null);
    try {
      let baseUrl = "http://localhost:8000";
      if (typeof window !== "undefined") {
        baseUrl = localStorage.getItem("UPHILL_API_URL_OVERRIDE") || process.env.NEXT_PUBLIC_API_URL || baseUrl;
      }

      let userProfileStr = "None";
      if (user) {
        userProfileStr = `Age: ${user.age || 'N/A'}, Max HR: ${user.max_hr || 'N/A'}, Resting HR: ${user.resting_hr || 'N/A'}, Weekly volume: ${user.current_weekly_km || 'N/A'}km`;
      }
      let activePlanStr = "None";
      if (activePlan?.target_event) {
        activePlanStr = `Distance: ${activePlan.target_event.distance_km || 'N/A'}km, Elevation: ${activePlan.target_event.elevation_gain_m || 'N/A'}m, Duration: ${activePlan.target_event.duration_hours || 'N/A'}h`;
      }

      const response = await fetch(`${baseUrl}/api/coach/calculate-fueling`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_time_hours: parseFloat(fuelDuration),
          weather_temp: fuelTemp,
          preferred_format: fuelFormats,
          target_carb_h: parseFloat(targetCarb) || 60,
          target_sodium_h: parseFloat(targetSodium) || 500,
          athlete_level: athleteLevel,
          preferred_brands: preferredBrands,
          additional_context: additionalContext,
          user_profile: userProfileStr,
          active_plan_context: activePlanStr
        }),
      });
      if (response.ok) {
        const result = await response.json();
        setFuelStrategy(result.plan);
      } else {
        console.error("Failed to calculate fueling");
      }
    } catch (err) {
      console.error("Failed to calculate fueling:", err);
    } finally {
      setFuelLoading(false);
    }
  };

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 1000,
      background: "rgba(255, 255, 255, 0.4)", backdropFilter: "blur(30px)", WebkitBackdropFilter: "blur(30px)",
      display: "flex", alignItems: "center", justifyContent: "center",
      padding: "20px"
    }}>
      <div style={{
        width: "100%", maxWidth: "800px", maxHeight: "90vh", overflowY: "auto",
        background: "rgba(255, 255, 255, 0.8)", border: "1px solid rgba(0,0,0,0.1)",
        borderRadius: "24px", padding: "32px", position: "relative",
        boxShadow: "0 20px 40px rgba(0,0,0,0.05)"
      }}>
        <button onClick={onClose} style={{
          position: "absolute", top: "20px", right: "20px", background: "none", border: "none",
          cursor: "pointer", color: "var(--text-secondary)"
        }}>
          <XCircle size={32} weight="duotone" />
        </button>

        <h2 style={{ fontSize: "28px", fontWeight: 700, marginBottom: "8px", color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "10px" }}>
          <BowlFood size={32} color="var(--accent-primary)" weight="duotone" /> 
          Nutrition Lab
        </h2>
        <p style={{ color: "var(--text-secondary)", marginBottom: "32px", fontSize: "15px" }}>
          {lang === "en" ? "Metabolic command center. Calibrate your hourly intake based on race conditions and exact product specs." : "Trung tâm điều khiển trao đổi chất. Tùy chỉnh lượng nạp dựa trên điều kiện đua."}
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "16px", marginBottom: "32px" }}>
          
          <div style={{ background: "rgba(0,0,0,0.03)", padding: "16px", borderRadius: "16px", border: "1px solid rgba(0,0,0,0.05)" }}>
            <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Duration (Hrs)" : "Thời gian (Giờ)"}</label>
            <input type="number" step="0.5" value={fuelDuration} onChange={(e) => setFuelDuration(e.target.value)}
              style={{ width: "100%", background: "transparent", border: "none", fontSize: "24px", fontWeight: 700, color: "var(--text-primary)", outline: "none" }} />
          </div>
          
          <div style={{ background: "rgba(0,0,0,0.03)", padding: "16px", borderRadius: "16px", border: "1px solid rgba(0,0,0,0.05)" }}>
            <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Athlete Level" : "Trình độ"}</label>
            <select value={athleteLevel} onChange={(e) => setAthleteLevel(e.target.value)}
              style={{ width: "100%", background: "transparent", border: "none", fontSize: "18px", fontWeight: 600, color: "var(--text-primary)", outline: "none", appearance: "none" }}>
              <option value="Recreational">{lang === "en" ? "Recreational" : "Nghiệp dư"}</option>
              <option value="Competitive">{lang === "en" ? "Competitive" : "Thi đấu"}</option>
              <option value="Elite">{lang === "en" ? "Elite" : "Chuyên nghiệp"}</option>
            </select>
          </div>

          <div style={{ background: "rgba(0,0,0,0.03)", padding: "16px", borderRadius: "16px", border: "1px solid rgba(0,0,0,0.05)" }}>
            <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Temperature" : "Nhiệt độ"}</label>
            <select value={fuelTemp} onChange={(e) => setFuelTemp(e.target.value)}
              style={{ width: "100%", background: "transparent", border: "none", fontSize: "18px", fontWeight: 600, color: "var(--text-primary)", outline: "none", appearance: "none" }}>
              <option value="cool">{lang === "en" ? "Cool" : "Lạnh"}</option>
              <option value="moderate">{lang === "en" ? "Moderate" : "Ôn hòa"}</option>
              <option value="hot">{lang === "en" ? "Hot" : "Nóng"}</option>
            </select>
          </div>

          <div style={{ background: "rgba(0,0,0,0.03)", padding: "16px", borderRadius: "16px", border: "1px solid rgba(0,0,0,0.05)" }}>
            <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Preferred Brands" : "Thương hiệu ưu tiên"}</label>
            <input type="text" placeholder="e.g. Maurten, GU, Naak" value={preferredBrands} onChange={(e) => setPreferredBrands(e.target.value)}
              style={{ width: "100%", background: "transparent", border: "none", fontSize: "16px", fontWeight: 600, color: "var(--text-primary)", outline: "none" }} />
          </div>

          <div style={{ background: "rgba(0,0,0,0.03)", padding: "16px", borderRadius: "16px", border: "1px solid rgba(0,0,0,0.05)" }}>
            <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Target Carbs (g/hr)" : "Mục tiêu Carbs (g/hr)"}</label>
            <input type="number" step="5" value={targetCarb} onChange={(e) => setTargetCarb(e.target.value)}
              style={{ width: "100%", background: "transparent", border: "none", fontSize: "18px", fontWeight: 700, color: "var(--text-primary)", outline: "none" }} />
          </div>

          <div style={{ background: "rgba(0,0,0,0.03)", padding: "16px", borderRadius: "16px", border: "1px solid rgba(0,0,0,0.05)" }}>
            <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Target Sodium (mg/hr)" : "Mục tiêu Natri (mg/hr)"}</label>
            <input type="number" step="50" value={targetSodium} onChange={(e) => setTargetSodium(e.target.value)}
              style={{ width: "100%", background: "transparent", border: "none", fontSize: "18px", fontWeight: 700, color: "var(--text-primary)", outline: "none" }} />
          </div>

          <div style={{ background: "rgba(0,0,0,0.03)", padding: "16px", borderRadius: "16px", border: "1px solid rgba(0,0,0,0.05)", gridColumn: "1 / -1" }}>
            <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Formats" : "Định dạng"}</label>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              {["gel", "drink mix", "chew", "bar"].map(f => (
                <button key={f} onClick={() => toggleFormat(f)} style={{ padding: "6px 16px", borderRadius: "20px", border: fuelFormats.includes(f) ? "none" : "1px solid var(--border-color)", background: fuelFormats.includes(f) ? "var(--text-primary)" : "transparent", color: fuelFormats.includes(f) ? "white" : "var(--text-primary)", fontSize: "14px", fontWeight: 600, cursor: "pointer", textTransform: "capitalize", transition: "0.2s" }}>
                  {f}
                </button>
              ))}
            </div>
          </div>

          <div style={{ background: "rgba(0,0,0,0.03)", padding: "16px", borderRadius: "16px", border: "1px solid rgba(0,0,0,0.05)", gridColumn: "1 / -1" }}>
            <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Additional Context" : "Ghi chú thêm"}</label>
            <textarea placeholder={lang === "en" ? "Any stomach issues, preferred flavor, or strategy..." : "Vấn đề dạ dày, hương vị yêu thích..."} value={additionalContext} onChange={(e) => setAdditionalContext(e.target.value)}
              style={{ width: "100%", background: "transparent", border: "none", fontSize: "15px", color: "var(--text-primary)", outline: "none", resize: "none", minHeight: "60px", fontFamily: "inherit" }} />
          </div>

        </div>

        <button 
          onClick={handleCalculateFueling} 
          disabled={fuelLoading}
          style={{ width: "100%", padding: "16px", borderRadius: "16px", background: "var(--text-primary)", color: "white", fontSize: "16px", fontWeight: 600, border: "none", cursor: fuelLoading ? "not-allowed" : "pointer", opacity: fuelLoading ? 0.7 : 1, transition: "0.2s" }}
        >
          {fuelLoading ? (lang === "en" ? "Calculating Macros..." : "Đang tính toán...") : (lang === "en" ? "Synthesize Plan" : "Lên Kế Hoạch")}
        </button>

        {fuelStrategy && (
          <div style={{ marginTop: "32px", paddingTop: "32px", borderTop: "1px solid rgba(0,0,0,0.1)" }}>
            <h3 style={{ fontSize: "14px", textTransform: "uppercase", letterSpacing: "1px", color: "var(--accent-primary)", marginBottom: "16px", fontWeight: 700, display: "flex", alignItems: "center", gap: "6px" }}>
              <Target size={18} weight="fill" /> OUTPUT LOG
            </h3>
            <div className="markdown-body" style={{ color: "var(--text-secondary)", lineHeight: 1.6, fontSize: "15px", fontFamily: "var(--font-outfit)" }}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{fuelStrategy}</ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
