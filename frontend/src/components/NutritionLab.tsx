"use client";

import React, { useState, useEffect } from "react";
import { BowlFood, XCircle, Target, WarningCircle, Clock, Package, ChartBar } from "@phosphor-icons/react";

interface NutritionProduct {
  brand: string;
  name: string;
  total_quantity: number;
  carbs_per_unit: number;
  sodium_per_unit: number;
  protein_per_unit: number;
  tech_notes: string;
}

interface HourlyEntry {
  hour: number;
  action: string;
  carbs: number;
  sodium: number;
}

interface NutritionPlan {
  products: NutritionProduct[];
  hourly_plan: HourlyEntry[];
  tips: string[];
}

interface NutritionLabProps {
  isOpen: boolean;
  onClose: () => void;
  lang: "en" | "vi";
  user?: any;
  activePlan?: any;
}

type ResultTab = "products" | "timeline" | "tips";

export const NutritionLab: React.FC<NutritionLabProps> = ({ isOpen, onClose, lang, user, activePlan }) => {
  const [fuelDuration, setFuelDuration] = useState("4.0");
  const [fuelTemp, setFuelTemp] = useState("moderate");
  const [fuelFormats, setFuelFormats] = useState<string[]>(["gel"]);
  const [athleteLevel, setAthleteLevel] = useState("Recreational");
  const [preferredBrands, setPreferredBrands] = useState("");
  const [additionalContext, setAdditionalContext] = useState("");
  const [targetCarb, setTargetCarb] = useState("60");
  const [targetSodium, setTargetSodium] = useState("500");

  const [plan, setPlan] = useState<NutritionPlan | null>(null);
  const [fuelLoading, setFuelLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<ResultTab>("products");
  const [expandedProduct, setExpandedProduct] = useState<number | null>(null);

  // Auto-fetch when modal opens
  useEffect(() => {
    if (isOpen) handleCalculateFueling();
  }, [isOpen]);

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
    setPlan(null);
    setActiveTab("products");
    setExpandedProduct(null);
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
        setPlan(result);
      } else {
        console.error("Failed to calculate fueling");
      }
    } catch (err) {
      console.error("Failed to calculate fueling:", err);
    } finally {
      setFuelLoading(false);
    }
  };

  // Compute max carbs/sodium across hourly plan for bar scaling
  const maxCarbs = plan ? Math.max(...plan.hourly_plan.map(h => h.carbs), 1) : 1;
  const maxSodium = plan ? Math.max(...plan.hourly_plan.map(h => h.sodium), 1) : 1;

  const statStyle = (color: string): React.CSSProperties => ({
    display: "flex", flexDirection: "column", alignItems: "center",
    background: `${color}0d`, border: `1px solid ${color}22`,
    borderRadius: "10px", padding: "8px 14px", minWidth: "64px"
  });

  const tabStyle = (active: boolean): React.CSSProperties => ({
    flex: 1, padding: "10px 0", fontSize: "13px", fontWeight: 700,
    textTransform: "uppercase", letterSpacing: "0.5px",
    border: "none", cursor: "pointer", transition: "all 0.2s",
    background: active ? "var(--text-primary)" : "transparent",
    color: active ? "white" : "var(--text-muted)",
    borderRadius: "12px"
  });

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

        {/* Input Grid */}
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
            <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Target Carbs (g/hr)" : "Mục tiêu Carbs (g/hr)"}</label>
            <input type="number" step="5" value={targetCarb} onChange={(e) => setTargetCarb(e.target.value)}
              style={{ width: "100%", background: "transparent", border: "none", fontSize: "18px", fontWeight: 700, color: "var(--text-primary)", outline: "none" }} />
          </div>

          <div style={{ background: "rgba(0,0,0,0.03)", padding: "16px", borderRadius: "16px", border: "1px solid rgba(0,0,0,0.05)" }}>
            <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Target Sodium (mg/hr)" : "Mục tiêu Natri (mg/hr)"}</label>
            <input type="number" step="50" value={targetSodium} onChange={(e) => setTargetSodium(e.target.value)}
              style={{ width: "100%", background: "transparent", border: "none", fontSize: "18px", fontWeight: 700, color: "var(--text-primary)", outline: "none" }} />
          </div>

          <div style={{ background: "rgba(0,0,0,0.03)", padding: "16px", borderRadius: "16px", border: "1px solid rgba(0,0,0,0.05)" }}>
            <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Preferred Brands" : "Thương hiệu ưu tiên"}</label>
            <input type="text" placeholder="e.g. Maurten, GU, Naak" value={preferredBrands} onChange={(e) => setPreferredBrands(e.target.value)}
              style={{ width: "100%", background: "transparent", border: "none", fontSize: "16px", fontWeight: 600, color: "var(--text-primary)", outline: "none" }} />
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

        {/* ── Results ── */}
        {plan && (
          <div style={{ marginTop: "32px", paddingTop: "32px", borderTop: "1px solid rgba(0,0,0,0.1)" }}>

            {/* Summary bar */}
            <div style={{ display: "flex", gap: "12px", marginBottom: "20px", flexWrap: "wrap" }}>
              <div style={statStyle("#22c55e")}>
                <span style={{ fontSize: "18px", fontWeight: 700, color: "#22c55e", fontFamily: "var(--font-mono)" }}>
                  {plan.products.reduce((s, p) => s + p.carbs_per_unit * p.total_quantity, 0).toFixed(0)}g
                </span>
                <span style={{ fontSize: "10px", textTransform: "uppercase", fontWeight: 600, color: "var(--text-muted)" }}>Total Carbs</span>
              </div>
              <div style={statStyle("#3b82f6")}>
                <span style={{ fontSize: "18px", fontWeight: 700, color: "#3b82f6", fontFamily: "var(--font-mono)" }}>
                  {plan.products.reduce((s, p) => s + p.sodium_per_unit * p.total_quantity, 0).toFixed(0)}mg
                </span>
                <span style={{ fontSize: "10px", textTransform: "uppercase", fontWeight: 600, color: "var(--text-muted)" }}>Total Sodium</span>
              </div>
              <div style={statStyle("#a855f7")}>
                <span style={{ fontSize: "18px", fontWeight: 700, color: "#a855f7", fontFamily: "var(--font-mono)" }}>
                  {plan.products.reduce((s, p) => s + p.total_quantity, 0)}
                </span>
                <span style={{ fontSize: "10px", textTransform: "uppercase", fontWeight: 600, color: "var(--text-muted)" }}>Total Units</span>
              </div>
              <div style={statStyle("#f59e0b")}>
                <span style={{ fontSize: "18px", fontWeight: 700, color: "#f59e0b", fontFamily: "var(--font-mono)" }}>
                  {plan.hourly_plan.length}h
                </span>
                <span style={{ fontSize: "10px", textTransform: "uppercase", fontWeight: 600, color: "var(--text-muted)" }}>Race Duration</span>
              </div>
            </div>

            {/* Tab switcher */}
            <div style={{ display: "flex", gap: "4px", background: "rgba(0,0,0,0.04)", padding: "4px", borderRadius: "16px", marginBottom: "20px" }}>
              <button id="tab-products" onClick={() => setActiveTab("products")} style={tabStyle(activeTab === "products")}>
                <Package size={14} style={{ display: "inline", marginRight: "5px", verticalAlign: "middle" }} />
                Fuel List
              </button>
              <button id="tab-timeline" onClick={() => setActiveTab("timeline")} style={tabStyle(activeTab === "timeline")}>
                <Clock size={14} style={{ display: "inline", marginRight: "5px", verticalAlign: "middle" }} />
                Timeline
              </button>
              <button id="tab-tips" onClick={() => setActiveTab("tips")} style={tabStyle(activeTab === "tips")}>
                <WarningCircle size={14} style={{ display: "inline", marginRight: "5px", verticalAlign: "middle" }} />
                Coach's Notes
              </button>
            </div>

            {/* ── Tab: Fuel List ── */}
            {activeTab === "products" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {plan.products.map((product, idx) => {
                  const isExpanded = expandedProduct === idx;
                  return (
                    <div key={idx} className="snow-glass" style={{
                      borderRadius: "16px", overflow: "hidden",
                      border: isExpanded ? "1px solid rgba(0,0,0,0.1)" : "1px solid rgba(0,0,0,0.05)",
                      boxShadow: isExpanded ? "0 12px 24px rgba(0,0,0,0.08)" : "0 4px 12px rgba(0,0,0,0.02)",
                      transition: "all 0.3s cubic-bezier(0.4,0,0.2,1)"
                    }}>
                      {/* Card Header */}
                      <div
                        onClick={() => setExpandedProduct(isExpanded ? null : idx)}
                        style={{ padding: "16px 20px", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "space-between", background: isExpanded ? "rgba(255,255,255,0.5)" : "transparent" }}
                      >
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <span style={{ fontSize: "11px", textTransform: "uppercase", letterSpacing: "1px", color: "var(--text-muted)", fontWeight: 700 }}>{product.brand}</span>
                          <h4 style={{ fontSize: "17px", fontWeight: 700, color: "var(--text-primary)", margin: "2px 0 0", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{product.name}</h4>
                        </div>
                        {/* Quantity badge */}
                        <div style={{ display: "flex", alignItems: "center", gap: "12px", flexShrink: 0, marginLeft: "12px" }}>
                          <span style={{ background: "var(--text-primary)", color: "white", fontSize: "13px", fontWeight: 700, padding: "4px 12px", borderRadius: "20px", fontFamily: "var(--font-mono)" }}>
                            × {product.total_quantity}
                          </span>
                          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style={{ transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.3s", opacity: 0.4 }}>
                            <path d="M5 7.5L10 12.5L15 7.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                        </div>
                      </div>

                      {/* Expanded macro details */}
                      <div style={{
                        maxHeight: isExpanded ? "300px" : "0px",
                        opacity: isExpanded ? 1 : 0,
                        overflow: "hidden",
                        transition: "all 0.3s cubic-bezier(0.4,0,0.2,1)"
                      }}>
                        <div style={{ padding: "0 20px 20px" }}>
                          <div style={{ display: "flex", gap: "10px", marginBottom: "14px" }}>
                            <div style={statStyle("#22c55e")}>
                              <span style={{ fontSize: "16px", fontWeight: 700, color: "#22c55e" }}>{product.carbs_per_unit}g</span>
                              <span style={{ fontSize: "10px", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>Carbs</span>
                            </div>
                            <div style={statStyle("#3b82f6")}>
                              <span style={{ fontSize: "16px", fontWeight: 700, color: "#3b82f6" }}>{product.sodium_per_unit}mg</span>
                              <span style={{ fontSize: "10px", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>Sodium</span>
                            </div>
                            {product.protein_per_unit > 0 && (
                              <div style={statStyle("#f59e0b")}>
                                <span style={{ fontSize: "16px", fontWeight: 700, color: "#f59e0b" }}>{product.protein_per_unit}g</span>
                                <span style={{ fontSize: "10px", color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>Protein</span>
                              </div>
                            )}
                          </div>
                          {product.tech_notes && (
                            <div style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: 1.5, background: "rgba(0,0,0,0.02)", padding: "10px 12px", borderRadius: "10px", borderLeft: "3px solid var(--accent-primary)" }}>
                              {product.tech_notes}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* ── Tab: Timeline ── */}
            {activeTab === "timeline" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "0" }}>
                {plan.hourly_plan.map((entry, idx) => {
                  const carbPct = (entry.carbs / maxCarbs) * 100;
                  const sodiumPct = (entry.sodium / maxSodium) * 100;
                  const isLast = idx === plan.hourly_plan.length - 1;
                  return (
                    <div key={idx} style={{ display: "flex", gap: "0", alignItems: "stretch" }}>
                      {/* Hour marker column */}
                      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: "52px", flexShrink: 0 }}>
                        <div style={{
                          width: "44px", height: "44px", borderRadius: "50%",
                          background: "var(--text-primary)", color: "white",
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontFamily: "var(--font-mono)", fontSize: "13px", fontWeight: 700, flexShrink: 0
                        }}>
                          {String(entry.hour).padStart(2, "0")}
                        </div>
                        {!isLast && (
                          <div style={{ width: "2px", flex: 1, minHeight: "20px", background: "rgba(0,0,0,0.08)", margin: "4px 0" }} />
                        )}
                      </div>

                      {/* Content */}
                      <div style={{ flex: 1, paddingLeft: "16px", paddingBottom: isLast ? "0" : "20px" }}>
                        <p style={{ fontSize: "14px", color: "var(--text-primary)", fontWeight: 600, margin: "10px 0 10px" }}>{entry.action}</p>
                        {/* Carb bar */}
                        <div style={{ marginBottom: "6px" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "3px" }}>
                            <span style={{ fontSize: "10px", fontWeight: 700, textTransform: "uppercase", color: "#22c55e" }}>Carbs</span>
                            <span style={{ fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>{entry.carbs}g</span>
                          </div>
                          <div style={{ height: "5px", borderRadius: "3px", background: "rgba(0,0,0,0.06)", overflow: "hidden" }}>
                            <div style={{ height: "100%", width: `${carbPct}%`, background: "#22c55e", borderRadius: "3px", transition: "width 0.6s ease" }} />
                          </div>
                        </div>
                        {/* Sodium bar */}
                        <div>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "3px" }}>
                            <span style={{ fontSize: "10px", fontWeight: 700, textTransform: "uppercase", color: "#3b82f6" }}>Sodium</span>
                            <span style={{ fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>{entry.sodium}mg</span>
                          </div>
                          <div style={{ height: "5px", borderRadius: "3px", background: "rgba(0,0,0,0.06)", overflow: "hidden" }}>
                            <div style={{ height: "100%", width: `${sodiumPct}%`, background: "#3b82f6", borderRadius: "3px", transition: "width 0.6s ease" }} />
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* ── Tab: Coach's Notes ── */}
            {activeTab === "tips" && plan.tips && plan.tips.length > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {plan.tips.map((tip, idx) => (
                  <div key={idx} style={{
                    display: "flex", gap: "14px", alignItems: "flex-start",
                    background: "rgba(0,0,0,0.02)", border: "1px dashed rgba(0,0,0,0.1)",
                    borderRadius: "14px", padding: "16px"
                  }}>
                    <span style={{
                      fontFamily: "var(--font-mono)", fontSize: "11px", fontWeight: 700,
                      color: "var(--accent-primary)", background: "rgba(0,0,0,0.04)",
                      padding: "4px 8px", borderRadius: "6px", flexShrink: 0, marginTop: "1px"
                    }}>
                      {String(idx + 1).padStart(2, "0")}
                    </span>
                    <p style={{ fontSize: "14px", color: "var(--text-secondary)", lineHeight: 1.6, margin: 0 }}>{tip}</p>
                  </div>
                ))}
              </div>
            )}

          </div>
        )}
      </div>
    </div>
  );
};
