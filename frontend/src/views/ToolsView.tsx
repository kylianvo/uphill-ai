/* eslint-disable @typescript-eslint/no-explicit-any */
import { useAppContext } from "../contexts/AppContext";
import { useTools } from "../hooks/useTools";
import { translations } from "../app/translations";
import { BowlFood, Sneaker, UploadSimple, FileArrowUp, Path, MapPin, Footprints, Clock, ArrowsMerge, PlayCircle, CheckCircle, Fire, Info } from '@phosphor-icons/react';

export default function ToolsView({ isMobile }: { isMobile: boolean }) {
  const ctx = useAppContext();
  const { lang, parserLoading, parserErrorMsg, parsedSummary, gpxCheckpoints, pacedCheckpoints, uploadedFileName, setIsNutritionLabOpen, setIsGearVaultOpen, targetFlatPace, setTargetFlatPace, pacingLoading } = ctx;
  const { handleDropzoneClick, handleFileChange, fileInputRef, handleCalculatePacing } = useTools();
  const t = (key: keyof typeof translations.en) => translations[lang]?.[key] || translations.en[key] || key;

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

        {/* Card 3: GPX Checkpoint Pacer */}
        <div className="card" style={{ padding: isMobile ? "16px" : "24px" }}>
          <h3 style={{ fontSize: isMobile ? "16px" : "18px", marginBottom: "8px", color: "var(--accent-primary)" }}>GPX Checkpoint Pacer</h3>
          <p style={{ color: "var(--text-secondary)", fontSize: "12.5px", marginBottom: "16px" }}>
            {lang === "en"
              ? "Upload a course GPX file to parse checkpoint metrics, or a workout FIT file to view telemetry."
              : "Tải lên tệp GPX đường chạy để phân tích thông số checkpoint, hoặc tệp FIT buổi tập để xem dữ liệu đo lường."}
          </p>

          <div className="dropzone" onClick={handleDropzoneClick} style={{ padding: "12px 10px", gap: "4px", marginBottom: "16px", cursor: "pointer" }}>
            <div className="dropzone-icon" style={{ fontSize: "18px" }}>📥</div>
            <div className="dropzone-title" style={{ fontSize: "12px" }}>
              {lang === "en" ? "Upload GPX or FIT" : "Tải lên tệp GPX hoặc FIT"}
            </div>
            <div className="dropzone-subtitle" style={{ fontSize: "10px", color: "var(--text-muted)" }}>
              {lang === "en" ? "Drag or tap here" : "Kéo hoặc chạm vào đây"}
            </div>
            {uploadedFileName && (
              <div style={{ color: "var(--accent-primary)", fontSize: "11px", fontWeight: "600", marginTop: "2px" }}>
                {uploadedFileName}
              </div>
            )}
          </div>

          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden-file-input"
            accept=".fit,.gpx"
            style={{ display: "none" }}
          />

          {parserLoading && (
            <div style={{ textTransform: "lowercase", textAlign: "center", color: "var(--accent-secondary)", fontSize: "11px", marginBottom: "12px" }}>
              {lang === "en" ? "Extracting telemetry..." : "Đang trích xuất dữ liệu đo lường..."}
            </div>
          )}

          {parserErrorMsg && (
            <div style={{ color: "var(--accent-alert)", fontSize: "11px", padding: "8px", background: "rgba(239, 68, 68, 0.08)", borderRadius: "6px", marginBottom: "12px" }}>
              {parserErrorMsg}
            </div>
          )}

          {parsedSummary && (
            <div style={{ padding: "10px", background: "rgba(255,255,255,0.15)", border: "1px solid var(--border-color)", borderRadius: "8px", marginBottom: "16px" }}>
              <div style={{ fontWeight: "700", fontSize: "11.5px", color: "var(--accent-secondary)", marginBottom: "6px" }}>
                {lang === "en" ? "Parsed Telemetry" : "Dữ liệu Đo lường đã Phân tích"}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                <div className="metric-item" style={{ padding: "6px" }}>
                  <div className="metric-label" style={{ fontSize: "9px" }}>
                    {lang === "en" ? "Distance" : "Cự ly"}
                  </div>
                  <div className="metric-value" style={{ fontSize: "12px" }}>{parsedSummary.distance_km} km</div>
                </div>
                <div className="metric-item" style={{ padding: "6px" }}>
                  <div className="metric-label" style={{ fontSize: "9px" }}>
                    {lang === "en" ? "Elevation" : "Độ cao"}
                  </div>
                  <div className="metric-value" style={{ fontSize: "12px" }}>{parsedSummary.elevation_gain_m} m</div>
                </div>
              </div>
            </div>
          )}

          <div style={{ marginBottom: "12px" }}>
            <label style={{ display: "block", fontSize: "11.5px", color: "var(--text-muted)", marginBottom: "4px" }}>
              {lang === "en" ? "Target Flat Pace (min/km)" : "Flat Pace Mục tiêu (min/km)"}
            </label>
            <input
              type="number"
              step="0.1"
              className="chat-input"
              style={{ borderRadius: "8px", width: "100%", padding: "8px" }}
              value={targetFlatPace}
              onChange={(e) => setTargetFlatPace(e.target.value)}
            />
          </div>

          <button
            className="btn btn-primary"
            style={{
              width: "100%", marginBottom: "12px", height: "36px", fontSize: "12.5px",
              ...(gpxCheckpoints.length === 0 ? { filter: "blur(3px)", opacity: 0.7, pointerEvents: "none" } : {})
            }}
            onClick={handleCalculatePacing}
            disabled={gpxCheckpoints.length === 0 || pacingLoading}
          >
            {pacingLoading
              ? (lang === "en" ? "Calculating Splits..." : "Đang tính toán checkpoint...")
              : gpxCheckpoints.length === 0
                ? (lang === "en" ? "Upload GPX First" : "Cần tải lên GPX trước")
                : (lang === "en" ? "Generate Splits" : "Tạo Checkpoint Pace")}
          </button>

          {pacedCheckpoints.length > 0 && (
            <div style={{ maxHeight: "160px", overflowY: "auto", border: "1px solid var(--border-color)", borderRadius: "8px", background: "rgba(255, 255, 255, 0.2)" }}>
              <table style={{ width: "100%", fontSize: "11px", borderCollapse: "collapse", textAlign: "left" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border-color)", color: "var(--text-muted)" }}>
                    <th style={{ padding: "6px" }}>{lang === "en" ? "Name" : "Tên"}</th>
                    <th style={{ padding: "6px" }}>{lang === "en" ? "Dist" : "Cự ly"}</th>
                    <th style={{ padding: "6px" }}>Pace</th>
                    <th style={{ padding: "6px" }}>{lang === "en" ? "Split" : "Tách (Split)"}</th>
                  </tr>
                </thead>
                <tbody>
                  {pacedCheckpoints.map((cp: any, idx: any) => (
                    <tr key={idx} style={{ borderBottom: "1px solid rgba(0,0,0,0.02)" }}>
                      <td style={{ padding: "6px", fontWeight: "600" }}>{cp.name}</td>
                      <td style={{ padding: "6px" }}>{cp.distance_km}k</td>
                      <td style={{ padding: "6px" }}>{cp.target_pace}/k</td>
                      <td style={{ padding: "700", fontWeight: "700" }}>{cp.split_time}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </div>
    );
}
