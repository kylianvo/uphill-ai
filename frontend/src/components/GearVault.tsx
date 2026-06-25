"use client";

import React, { useState } from "react";
import { Sneaker, XCircle, Target, CaretDown, WarningCircle, CheckCircle, Question, Ruler, Path, RocketLaunch } from "@phosphor-icons/react";

interface ShoeRecommendation {
  model: string;
  brand: string;
  foam_material: string;
  outsole_compound: string;
  lug_depth: string;
  drop: string;
  stack: string;
  price: string;
  pros: string;
  cons: string;
}

interface GearPlanResponse {
  recommendations: ShoeRecommendation[];
  tips: string[];
}

interface GearVaultProps {
  isOpen: boolean;
  onClose: () => void;
  lang: "en" | "vi";
}

export const GearVault: React.FC<GearVaultProps> = ({ isOpen, onClose, lang }) => {
  const [shoeSurface, setShoeSurface] = useState("trail");
  const [shoeCushion, setShoeCushion] = useState("balanced");
  const [shoeWidth, setShoeWidth] = useState("normal");
  const [shoeCarbon, setShoeCarbon] = useState<string>("any");
  const [shoeBudget, setShoeBudget] = useState("");
  const [shoeBrands, setShoeBrands] = useState("");
  const [shoeContext, setShoeContext] = useState("");
  
  // Conditional States
  const [shoeTerrain, setShoeTerrain] = useState<string[]>(["runnable"]); // For trail
  const [shoeUseCase, setShoeUseCase] = useState("daily training"); // For road
  const [shoeDistance, setShoeDistance] = useState(""); // For racing/trail

  const [gearPlan, setGearPlan] = useState<GearPlanResponse | null>(null);
  const [gearLoading, setGearLoading] = useState(false);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (!isOpen) return null;

  const toggleTerrain = (t: string) => {
    if (shoeTerrain.includes(t)) {
      if (shoeTerrain.length > 1) setShoeTerrain(shoeTerrain.filter(x => x !== t));
    } else {
      setShoeTerrain([...shoeTerrain, t]);
    }
  };

  const handleRecommendShoes = async () => {
    setGearLoading(true);
    setGearPlan(null);
    setExpandedIndex(null);
    try {
      let baseUrl = "http://localhost:8000";
      if (typeof window !== "undefined") {
        baseUrl = localStorage.getItem("UPHILL_API_URL_OVERRIDE") || process.env.NEXT_PUBLIC_API_URL || baseUrl;
      }
      
      const payload = {
        surface: shoeSurface,
        cushioning: shoeCushion,
        width: shoeWidth,
        carbon_plate: shoeCarbon,
        budget: shoeBudget,
        terrain: shoeSurface === "trail" ? shoeTerrain : [],
        use_case: shoeSurface === "road" ? shoeUseCase : "",
        preferred_brands: shoeBrands,
        additional_context: shoeContext,
        race_distance: shoeDistance
      };

      const response = await fetch(`${baseUrl}/api/coach/recommend-shoes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (response.ok) {
        const result = await response.json();
        setGearPlan(result);
      } else {
        console.error("Failed to recommend shoes");
      }
    } catch (err) {
      console.error("Failed to calculate shoes:", err);
    } finally {
      setGearLoading(false);
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
          <Sneaker size={32} color="var(--accent-primary)" weight="duotone" /> 
          Gear Finder
        </h2>
        <p style={{ color: "var(--text-secondary)", marginBottom: "32px", fontSize: "15px" }}>
          {lang === "en" ? "Technical equipment matching. Cross-references your biomechanics with our proprietary gear database." : "Tùy chỉnh trang bị kỹ thuật. So khớp cơ sinh học của bạn với cơ sở dữ liệu."}
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "16px", marginBottom: "32px" }}>
          
          <div style={{ background: "rgba(0,0,0,0.03)", padding: "16px", borderRadius: "16px", border: "1px solid rgba(0,0,0,0.05)" }}>
            <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Surface" : "Mặt đường"}</label>
            <select value={shoeSurface} onChange={(e) => setShoeSurface(e.target.value)}
              style={{ width: "100%", background: "transparent", border: "none", fontSize: "18px", fontWeight: 600, color: "var(--text-primary)", outline: "none", appearance: "none" }}>
              <option value="trail">Trail</option>
              <option value="road">Road</option>
            </select>
          </div>

          {shoeSurface === "trail" && (
             <div style={{ background: "rgba(0,0,0,0.03)", padding: "16px", borderRadius: "16px", border: "1px solid rgba(0,0,0,0.05)", gridColumn: "1 / -1" }}>
               <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Terrain" : "Địa hình"}</label>
               <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                 {["muddy", "technical", "rocky", "runnable"].map(t => (
                   <button key={t} onClick={() => toggleTerrain(t)} style={{ padding: "6px 16px", borderRadius: "20px", border: shoeTerrain.includes(t) ? "none" : "1px solid var(--border-color)", background: shoeTerrain.includes(t) ? "var(--text-primary)" : "transparent", color: shoeTerrain.includes(t) ? "white" : "var(--text-primary)", fontSize: "14px", fontWeight: 600, cursor: "pointer", textTransform: "capitalize", transition: "0.2s" }}>
                     {t}
                   </button>
                 ))}
               </div>
             </div>
          )}

          {shoeSurface === "road" && (
             <div style={{ background: "rgba(0,0,0,0.03)", padding: "16px", borderRadius: "16px", border: "1px solid rgba(0,0,0,0.05)" }}>
               <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Use Case" : "Mục đích"}</label>
               <select value={shoeUseCase} onChange={(e) => setShoeUseCase(e.target.value)}
                 style={{ width: "100%", background: "transparent", border: "none", fontSize: "18px", fontWeight: 600, color: "var(--text-primary)", outline: "none", appearance: "none" }}>
                 <option value="racing">Racing</option>
                 <option value="daily training">Daily Training</option>
                 <option value="tempo/long run">Tempo / Long Run</option>
               </select>
             </div>
          )}

          {(shoeSurface === "trail" || (shoeSurface === "road" && shoeUseCase === "racing")) && (
            <div style={{ background: "rgba(0,0,0,0.03)", padding: "16px", borderRadius: "16px", border: "1px solid rgba(0,0,0,0.05)" }}>
              <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Race Distance" : "Cự ly giải"}</label>
              <input type="text" placeholder="e.g. 50k, 100 miles, Marathon" value={shoeDistance} onChange={(e) => setShoeDistance(e.target.value)}
                style={{ width: "100%", background: "transparent", border: "none", fontSize: "16px", fontWeight: 600, color: "var(--text-primary)", outline: "none" }} />
            </div>
          )}
          
          <div style={{ background: "rgba(0,0,0,0.03)", padding: "16px", borderRadius: "16px", border: "1px solid rgba(0,0,0,0.05)" }}>
            <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Cushioning" : "Độ êm"}</label>
            <select value={shoeCushion} onChange={(e) => setShoeCushion(e.target.value)}
              style={{ width: "100%", background: "transparent", border: "none", fontSize: "18px", fontWeight: 600, color: "var(--text-primary)", outline: "none", appearance: "none" }}>
              <option value="plush">Plush (Max Cushion)</option>
              <option value="balanced">Balanced</option>
              <option value="firm">Firm / Minimal</option>
            </select>
          </div>

          <div style={{ background: "rgba(0,0,0,0.03)", padding: "16px", borderRadius: "16px", border: "1px solid rgba(0,0,0,0.05)" }}>
            <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Width" : "Độ rộng"}</label>
            <select value={shoeWidth} onChange={(e) => setShoeWidth(e.target.value)}
              style={{ width: "100%", background: "transparent", border: "none", fontSize: "18px", fontWeight: 600, color: "var(--text-primary)", outline: "none", appearance: "none" }}>
              <option value="normal">Normal</option>
              <option value="wide">Wide</option>
              <option value="narrow">Narrow</option>
            </select>
          </div>

          <div style={{ background: "rgba(0,0,0,0.03)", padding: "16px", borderRadius: "16px", border: "1px solid rgba(0,0,0,0.05)" }}>
            <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Carbon Plate" : "Đế Carbon"}</label>
            <select value={shoeCarbon} onChange={(e) => setShoeCarbon(e.target.value)}
              style={{ width: "100%", background: "transparent", border: "none", fontSize: "18px", fontWeight: 600, color: "var(--text-primary)", outline: "none", appearance: "none" }}>
              <option value="any">No Preference</option>
              <option value="yes">Required</option>
              <option value="no">Exclude</option>
            </select>
          </div>

          <div style={{ background: "rgba(0,0,0,0.03)", padding: "16px", borderRadius: "16px", border: "1px solid rgba(0,0,0,0.05)" }}>
            <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Budget" : "Ngân sách"}</label>
            <input type="text" placeholder="e.g. Under $150, Any" value={shoeBudget} onChange={(e) => setShoeBudget(e.target.value)}
              style={{ width: "100%", background: "transparent", border: "none", fontSize: "16px", fontWeight: 600, color: "var(--text-primary)", outline: "none" }} />
          </div>

          <div style={{ background: "rgba(0,0,0,0.03)", padding: "16px", borderRadius: "16px", border: "1px solid rgba(0,0,0,0.05)" }}>
            <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Preferred Brands" : "Thương hiệu ưu tiên"}</label>
            <input type="text" placeholder="e.g. Salomon, Hoka" value={shoeBrands} onChange={(e) => setShoeBrands(e.target.value)}
              style={{ width: "100%", background: "transparent", border: "none", fontSize: "16px", fontWeight: 600, color: "var(--text-primary)", outline: "none" }} />
          </div>

          <div style={{ background: "rgba(0,0,0,0.03)", padding: "16px", borderRadius: "16px", border: "1px solid rgba(0,0,0,0.05)", gridColumn: "1 / -1" }}>
            <label style={{ display: "block", fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", marginBottom: "8px", fontWeight: 600 }}>{lang === "en" ? "Special Requirements" : "Yêu cầu đặc biệt"}</label>
            <textarea placeholder={lang === "en" ? "E.g. Achilles issues, need a roomy toebox..." : "Ví dụ: đau gót chân, cần mũi giày rộng..."} value={shoeContext} onChange={(e) => setShoeContext(e.target.value)}
              style={{ width: "100%", background: "transparent", border: "none", fontSize: "15px", color: "var(--text-primary)", outline: "none", resize: "none", minHeight: "60px", fontFamily: "inherit" }} />
          </div>

        </div>

        <button 
          onClick={handleRecommendShoes} 
          disabled={gearLoading}
          style={{ width: "100%", padding: "16px", borderRadius: "16px", background: "var(--text-primary)", color: "white", fontSize: "16px", fontWeight: 600, border: "none", cursor: gearLoading ? "not-allowed" : "pointer", opacity: gearLoading ? 0.7 : 1, transition: "0.2s" }}
        >
          {gearLoading ? (lang === "en" ? "Analyzing..." : "Đang phân tích...") : (lang === "en" ? "Match Equipment" : "Tìm Trang Bị")}
        </button>

        {gearPlan && (
          <div style={{ marginTop: "32px", paddingTop: "32px", borderTop: "1px solid rgba(0,0,0,0.1)" }}>
            <h3 style={{ fontSize: "14px", textTransform: "uppercase", letterSpacing: "1px", color: "var(--accent-primary)", marginBottom: "16px", fontWeight: 700, display: "flex", alignItems: "center", gap: "6px" }}>
              <Target size={18} weight="fill" /> MATCH RESULTS
            </h3>
            
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {gearPlan.recommendations.map((shoe, idx) => {
                const isExpanded = expandedIndex === idx;
                const isTrail = shoeSurface === "trail";
                
                return (
                  <div key={idx} className="snow-glass" style={{
                    borderRadius: "16px",
                    overflow: "hidden",
                    transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                    border: isExpanded ? "1px solid rgba(0,0,0,0.1)" : "1px solid rgba(0,0,0,0.05)",
                    boxShadow: isExpanded ? "0 12px 24px rgba(0,0,0,0.08)" : "0 4px 12px rgba(0,0,0,0.02)"
                  }}>
                    {/* Header: Clickable Area */}
                    <div 
                      onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                      style={{
                        padding: "16px 20px",
                        display: "flex",
                        flexDirection: "column",
                        gap: "12px",
                        cursor: "pointer",
                        background: isExpanded ? "rgba(255,255,255,0.5)" : "transparent"
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                        <div>
                          <span style={{ fontSize: "12px", textTransform: "uppercase", letterSpacing: "1px", color: "var(--text-muted)", fontWeight: 700 }}>
                            {shoe.brand}
                          </span>
                          <h4 style={{ fontSize: "20px", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
                            {shoe.model}
                          </h4>
                        </div>
                        <CaretDown size={20} color="var(--text-muted)" style={{ transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.3s" }} />
                      </div>
                      
                      {/* Discrete Stats Row */}
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                        <span style={{ display: "flex", alignItems: "center", gap: "4px", background: "rgba(0,0,0,0.04)", padding: "4px 10px", borderRadius: "8px", fontSize: "12px", fontWeight: 600, color: "var(--text-secondary)" }}>
                          <RocketLaunch size={14} /> {shoe.foam_material}
                        </span>
                        {isTrail && shoe.outsole_compound && shoe.outsole_compound !== "None" && (
                          <span style={{ display: "flex", alignItems: "center", gap: "4px", background: "rgba(0,0,0,0.04)", padding: "4px 10px", borderRadius: "8px", fontSize: "12px", fontWeight: 600, color: "var(--text-secondary)" }}>
                            <Path size={14} /> {shoe.outsole_compound}
                          </span>
                        )}
                        {isTrail && shoe.lug_depth && shoe.lug_depth !== "None" && (
                          <span style={{ display: "flex", alignItems: "center", gap: "4px", background: "rgba(0,0,0,0.04)", padding: "4px 10px", borderRadius: "8px", fontSize: "12px", fontWeight: 600, color: "var(--text-secondary)" }}>
                            <Target size={14} /> {shoe.lug_depth}
                          </span>
                        )}
                        <span style={{ display: "flex", alignItems: "center", gap: "4px", background: "rgba(0,0,0,0.04)", padding: "4px 10px", borderRadius: "8px", fontSize: "12px", fontWeight: 600, color: "var(--text-secondary)" }}>
                          <Ruler size={14} /> Drop: {shoe.drop}
                        </span>
                        <span style={{ display: "flex", alignItems: "center", gap: "4px", background: "rgba(0,0,0,0.04)", padding: "4px 10px", borderRadius: "8px", fontSize: "12px", fontWeight: 600, color: "var(--text-secondary)" }}>
                          <Ruler size={14} /> Stack: {shoe.stack}
                        </span>
                      </div>
                    </div>

                    {/* Expanded Content */}
                    <div style={{
                      maxHeight: isExpanded ? "600px" : "0px",
                      opacity: isExpanded ? 1 : 0,
                      overflow: "hidden",
                      transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)"
                    }}>
                      <div style={{ padding: "0 20px 20px 20px" }}>
                        <div style={{ borderTop: "1px solid rgba(0,0,0,0.05)", paddingTop: "16px", marginBottom: "16px" }}>
                          <div style={{ fontSize: "11px", textTransform: "uppercase", fontWeight: 700, color: "var(--text-muted)", marginBottom: "8px", display: "flex", alignItems: "center", gap: "4px" }}>
                            <CheckCircle size={14} color="var(--accent-primary)" /> PROS / BEST FOR
                          </div>
                          <div style={{ fontSize: "14px", color: "var(--text-primary)", lineHeight: 1.5, background: "rgba(0,255,0,0.03)", padding: "12px", borderRadius: "12px", border: "1px solid rgba(0,255,0,0.05)" }}>
                            {shoe.pros}
                          </div>
                        </div>

                        <div style={{ marginBottom: "16px" }}>
                          <div style={{ fontSize: "11px", textTransform: "uppercase", fontWeight: 700, color: "var(--text-muted)", marginBottom: "8px", display: "flex", alignItems: "center", gap: "4px" }}>
                            <WarningCircle size={14} color="#ff4444" /> CONS / DRAWBACKS
                          </div>
                          <div style={{ fontSize: "14px", color: "var(--text-primary)", lineHeight: 1.5, background: "rgba(255,0,0,0.02)", padding: "12px", borderRadius: "12px", border: "1px solid rgba(255,0,0,0.05)" }}>
                            {shoe.cons}
                          </div>
                        </div>

                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid rgba(0,0,0,0.05)", paddingTop: "16px" }}>
                          <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>Estimated Price</span>
                          <span style={{ fontFamily: "var(--font-mono)", fontSize: "18px", fontWeight: 600, color: "var(--text-primary)" }}>
                            {shoe.price}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {gearPlan.tips && gearPlan.tips.length > 0 && (
              <div style={{ marginTop: "24px", background: "rgba(0,0,0,0.02)", border: "1px dashed rgba(0,0,0,0.1)", borderRadius: "16px", padding: "16px" }}>
                <h4 style={{ fontSize: "13px", textTransform: "uppercase", letterSpacing: "0.5px", fontWeight: 700, color: "var(--text-primary)", display: "flex", alignItems: "center", gap: "6px", marginBottom: "12px" }}>
                  <WarningCircle size={16} /> COACH'S NOTES
                </h4>
                <ul style={{ margin: 0, paddingLeft: "20px", color: "var(--text-secondary)", fontSize: "14px", lineHeight: 1.5 }}>
                  {gearPlan.tips.map((tip, idx) => (
                    <li key={idx} style={{ marginBottom: "6px" }}>{tip}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
