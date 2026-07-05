/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState } from "react";
import { useAppContext } from "../contexts/AppContext";

import { translations } from "../app/translations";
import { usePaceZones } from "../hooks/usePaceZones";
import { ZONE_NUMBER_COLORS } from "../data/workoutLibrary";
import { X, User, Heartbeat, Watch, SignOut, Warning } from '@phosphor-icons/react';

export default function ProfileSettingsModal() {
  const ctx = useAppContext();
  const { lang, setLang, user, setUser, profileSettingsOpen, setProfileSettingsOpen, profileForm, setProfileForm, setActivePlan, setWorkouts, setSources, setAuthModalOpen, setOnboardingOpen, handleLogout } = ctx;
  const [doubleDays, setDoubleDays] = useState<string[]>([]);
  const { zones: paceZones, fetchPaceZones } = usePaceZones();
  const [passwordFormOpen, setPasswordFormOpen] = useState(false);
  const [newPassword, setNewPassword] = useState("");
  const [passwordMsg, setPasswordMsg] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");


  React.useEffect(() => {
    if (profileSettingsOpen && user) {
      Promise.resolve().then(() => {
        try { setDoubleDays(JSON.parse(user.double_session_days || "[]")); } catch { setDoubleDays([]); }
      });
      fetchPaceZones();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profileSettingsOpen]);

  const toggleDoubleDay = (day: string) => {
    setDoubleDays(prev => {
      if (prev.includes(day)) return prev.filter(d => d !== day);
      if (prev.length >= 2) return prev;
      return [...prev, day];
    });
  };

  const [savingProfile, setSavingProfile] = useState(false);
  const [profileMsg, setProfileMsg] = useState("");
  const [profileError, setProfileError] = useState("");
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";


  const handleSetLang = (l: string) => {
    setLang(l as "en"|"vi");
    if(typeof window !== "undefined") localStorage.setItem("uphill_lang", l);
  };

  const handleSetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMsg("");
    setPasswordError("");
    if (newPassword !== confirmNewPassword) {
      setPasswordError("Passwords do not match.");
      return;
    }
    try {
      const token = localStorage.getItem("uphill_session_token");
      if(!token) throw new Error("Not authenticated");
      const res = await fetch(`${API_BASE_URL}/api/auth/update-password`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ new_password: newPassword })
      });
      if(!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to update password");
      }
      setPasswordMsg("Password updated successfully.");
      setNewPassword("");
      setConfirmNewPassword("");
    } catch(err: any) {
      setPasswordError(err.message || "Failed to update password.");
    }
  };

  const t = (key: keyof typeof translations.en) => translations[lang]?.[key] || translations.en[key] || key;

  const handleSaveProfile = async (e?: React.FormEvent) => {







    if (e) e.preventDefault();







    ;







    setProfileError("");







    const token = localStorage.getItem("uphill_session_token");







    if (!token) return;







    try {







      const response = await fetch(`${API_BASE_URL}/api/auth/update-profile`, {







        method: "POST",







        headers: {







          "Content-Type": "application/json",







          "Authorization": `Bearer ${token}`







        },







        body: JSON.stringify({







          age: parseInt(profileForm.age),







          current_weekly_km: parseFloat(profileForm.current_weekly_km),







          max_hr: parseInt(profileForm.max_hr),







          resting_hr: parseInt(profileForm.resting_hr),







          aet_hr: parseInt(profileForm.aet_hr),







          ant_hr: parseInt(profileForm.ant_hr),







          use_treadmill: profileForm.use_treadmill,







          gemini_api_key: profileForm.gemini_api_key,







          zone2_pace_min: profileForm.zone2_pace_min,







          zone2_pace_max: profileForm.zone2_pace_max,
          double_session_days: doubleDays,







        }),







      });















      if (!response.ok) {







        const errData = await response.json();







        throw new Error(errData.detail || "Profile update failed.");







      }















      const updatedUser = await response.json();







      setUser(updatedUser);
      fetchPaceZones();







      setAuthModalOpen(false);







      setOnboardingOpen(false);







    } catch (err: any) {







      setProfileError(err.message || "Failed to save physiology settings.");







    } finally {







      ;







    }







  };








    if (!profileSettingsOpen || !user) return null;















    const inputStyle: React.CSSProperties = {







      borderRadius: "8px", width: "100%", height: "36px", margin: 0, padding: "0 10px",







      fontSize: "13px", background: "transparent", border: "1px solid var(--border-color)",







      color: "var(--text-primary)", boxSizing: "border-box" as const







    };







    const labelStyle: React.CSSProperties = {







      display: "block", fontSize: "11.5px", fontWeight: "600", color: "var(--text-muted)", marginBottom: "5px"







    };















    return (







      <div style={{ position: "fixed", inset: 0, background: "rgba(255,255,255,0.35)", backdropFilter: "blur(16px)", display: "flex", justifyContent: "center", alignItems: "center", zIndex: 1000, padding: "20px" }}>







        <div style={{ background: "var(--bg-card)", backdropFilter: "blur(30px)", border: "1px solid var(--border-color)", borderRadius: "24px", padding: "32px", width: "100%", maxWidth: "520px", maxHeight: "90vh", overflowY: "auto", boxShadow: "0 20px 60px rgba(0,0,0,0.1)", position: "relative", color: "var(--text-primary)" }}>















          {/* Close button */}







          <button







            type="button"







            onClick={() => { setProfileSettingsOpen(false); setPasswordFormOpen(false); setPasswordMsg(""); setPasswordError(""); }}







            style={{ position: "absolute", top: "20px", right: "20px", background: "none", border: "none", fontSize: "20px", cursor: "pointer", color: "var(--text-muted)" }}







          >







            ✕







          </button>















          {/* Header */}







          <div style={{ marginBottom: "24px" }}>







            <div style={{ fontSize: "22px", fontWeight: "800", letterSpacing: "-0.02em" }}>







              {lang === "en" ? "Profile Settings" : "Cài đặt Hồ sơ"}







            </div>







            <p style={{ color: "var(--text-muted)", fontSize: "13px", marginTop: "4px" }}>







              {lang === "en" ? "Manage your physiology parameters and security settings" : "Quản lý các thông số sinh lý và cài đặt bảo mật của bạn"}







            </p>







          </div>















          {profileError && (







            <div style={{ color: "#ef4444", background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.15)", borderRadius: "8px", padding: "10px", fontSize: "12.5px", marginBottom: "16px" }}>







              <Warning weight="fill" style={{marginRight: "4px", verticalAlign: "middle"}}/> {profileError}







            </div>







          )}















          <form onSubmit={handleSaveProfile} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>















            {/* Physiology Section */}







            <div>







              <h3 style={{ fontSize: "14px", fontWeight: "700", borderBottom: "1px solid var(--border-color)", paddingBottom: "6px", marginBottom: "12px", color: "var(--accent-primary)" }}>







                {t("profile_title").toUpperCase()}







              </h3>







              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>







                <div>







                  <label style={labelStyle}>{t("profile_age").replace(" (Years)", "")}</label>







                  <input type="number" style={inputStyle} value={profileForm.age} onChange={e => setProfileForm({ ...profileForm, age: e.target.value })} required />







                </div>







                <div>







                  <label style={labelStyle}>{lang === "en" ? "Weekly Volume (km)" : "Khối lượng tuần (km)"}</label>







                  <input type="number" step="0.1" style={inputStyle} value={profileForm.current_weekly_km} onChange={e => setProfileForm({ ...profileForm, current_weekly_km: e.target.value })} required />







                </div>







                <div>







                  <label style={labelStyle}>{t("profile_max_hr")}</label>







                  <input type="number" style={inputStyle} value={profileForm.max_hr} onChange={e => setProfileForm({ ...profileForm, max_hr: e.target.value })} required />







                </div>







                <div>







                  <label style={labelStyle}>{t("profile_resting_hr")}</label>







                  <input type="number" style={inputStyle} value={profileForm.resting_hr} onChange={e => setProfileForm({ ...profileForm, resting_hr: e.target.value })} required />







                </div>







                <div>







                  <label style={labelStyle}>{t("profile_aet_hr")}</label>







                  <input type="number" style={inputStyle} value={profileForm.aet_hr} onChange={e => setProfileForm({ ...profileForm, aet_hr: e.target.value })} required />
                  <p style={{ fontSize: "11px", color: "var(--text-muted)", margin: "4px 0 0 0" }}>{t("profile_aet_hint")}</p>







                </div>







                <div>







                  <label style={labelStyle}>{t("profile_ant_hr")}</label>







                  <input type="number" style={inputStyle} value={profileForm.ant_hr} onChange={e => setProfileForm({ ...profileForm, ant_hr: e.target.value })} required />
                  <p style={{ fontSize: "11px", color: "var(--text-muted)", margin: "4px 0 0 0" }}>{t("profile_ant_hint")}</p>







                </div>







                <div>







                  <label style={labelStyle}>{lang === "en" ? "Zone 2 Pace Min" : "Zone 2 Pace Min"}</label>







                  <input type="text" style={inputStyle} value={profileForm.zone2_pace_min} onChange={e => setProfileForm({ ...profileForm, zone2_pace_min: e.target.value })} required />







                </div>







                <div>







                  <label style={labelStyle}>{lang === "en" ? "Zone 2 Pace Max" : "Zone 2 Pace Max"}</label>







                  <input type="text" style={inputStyle} value={profileForm.zone2_pace_max} onChange={e => setProfileForm({ ...profileForm, zone2_pace_max: e.target.value })} required />







                </div>







              </div>

                <div style={{ marginTop: "12px" }}>
                  <label style={labelStyle}>{lang === "en" ? "Your Training Zones" : "Your Training Zones"}</label>
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "6px" }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "6px 10px", borderRadius: "8px", background: `${ZONE_NUMBER_COLORS[1]}14`, borderLeft: `3px solid ${ZONE_NUMBER_COLORS[1]}` }}>
                      <span style={{ fontSize: "12px", fontWeight: 700, color: ZONE_NUMBER_COLORS[1] }}>{lang === "en" ? "Zone 1 (Recovery)" : "Zone 1 (Recovery)"}</span>
                      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "1px" }}>
                        <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-primary)" }}>{paceZones ? `${paceZones.zone1_pace} /km` : "—"}</span>
                        <span style={{ fontSize: "10px", fontWeight: 500, color: "var(--text-muted)" }}>{paceZones ? paceZones.zone1_hr : ""}</span>
                      </div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "6px 10px", borderRadius: "8px", background: `${ZONE_NUMBER_COLORS[2]}14`, borderLeft: `3px solid ${ZONE_NUMBER_COLORS[2]}` }}>
                      <span style={{ fontSize: "12px", fontWeight: 700, color: ZONE_NUMBER_COLORS[2] }}>{lang === "en" ? "Zone 2 (Easy)" : "Zone 2 (Easy)"}</span>
                      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "1px" }}>
                        <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-primary)" }}>{paceZones ? `${paceZones.zone2_pace} /km` : "—"}</span>
                        <span style={{ fontSize: "10px", fontWeight: 500, color: "var(--text-muted)" }}>{paceZones ? paceZones.zone2_hr : ""}</span>
                      </div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "6px 10px", borderRadius: "8px", background: `${ZONE_NUMBER_COLORS[3]}14`, borderLeft: `3px solid ${ZONE_NUMBER_COLORS[3]}` }}>
                      <span style={{ fontSize: "12px", fontWeight: 700, color: ZONE_NUMBER_COLORS[3] }}>{lang === "en" ? "Zone 3 (Tempo)" : "Zone 3 (Tempo)"}</span>
                      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "1px" }}>
                        <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-primary)" }}>{paceZones ? `${paceZones.zone3_pace} /km` : "—"}</span>
                        <span style={{ fontSize: "10px", fontWeight: 500, color: "var(--text-muted)" }}>{paceZones ? paceZones.zone3_hr : ""}</span>
                      </div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "6px 10px", borderRadius: "8px", background: `${ZONE_NUMBER_COLORS[4]}14`, borderLeft: `3px solid ${ZONE_NUMBER_COLORS[4]}` }}>
                      <span style={{ fontSize: "12px", fontWeight: 700, color: ZONE_NUMBER_COLORS[4] }}>{lang === "en" ? "Zone 4 (Threshold)" : "Zone 4 (Threshold)"}</span>
                      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "1px" }}>
                        <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-primary)" }}>{paceZones ? `${paceZones.zone4_pace} /km` : "—"}</span>
                        <span style={{ fontSize: "10px", fontWeight: 500, color: "var(--text-muted)" }}>{paceZones ? paceZones.zone4_hr : ""}</span>
                      </div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "6px 10px", borderRadius: "8px", background: `${ZONE_NUMBER_COLORS[5]}14`, borderLeft: `3px solid ${ZONE_NUMBER_COLORS[5]}` }}>
                      <span style={{ fontSize: "12px", fontWeight: 700, color: ZONE_NUMBER_COLORS[5] }}>{lang === "en" ? "Zone 5 (Interval)" : "Zone 5 (Interval)"}</span>
                      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "1px" }}>
                        <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-primary)" }}>{paceZones ? `${paceZones.zone5_pace} /km` : "—"}</span>
                        <span style={{ fontSize: "10px", fontWeight: 500, color: "var(--text-muted)" }}>{paceZones ? paceZones.zone5_hr : ""}</span>
                      </div>
                    </div>
                  </div>
                </div>








              <div style={{ marginTop: "12px" }}>







                <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", cursor: "pointer", color: "var(--text-primary)" }}>







                  <input type="checkbox" checked={profileForm.use_treadmill} onChange={e => setProfileForm({ ...profileForm, use_treadmill: e.target.checked })} style={{ width: "16px", height: "16px", accentColor: "var(--accent-primary)" }} />







                  {t("profile_treadmill")}







                </label>







              </div>







              <div style={{ marginTop: "12px" }}>







                <label style={labelStyle}>{t("profile_gemini_key")}</label>







                <input type="password" style={inputStyle} placeholder={lang === "en" ? "Leave blank to use system key" : "Để trống để sử dụng key của hệ thống"} value={profileForm.gemini_api_key} onChange={e => setProfileForm({ ...profileForm, gemini_api_key: e.target.value })} />







              </div>







            </div>















            {/* Double Session Days Section */}
            <div style={{ marginTop: "10px" }}>
              <h3 style={{ fontSize: "14px", fontWeight: "700", borderBottom: "1px solid var(--border-color)", paddingBottom: "6px", marginBottom: "12px", color: "var(--accent-primary)" }}>
                {lang === "en" ? "DOUBLE SESSION DAYS" : "NGÀY TẬP HAI BUỔI"}
              </h3>
              <p style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "12px" }}>
                {lang === "en"
                  ? "Pick up to 2 days for morning + afternoon sessions. Choose from your preferred training days."
                  : "Chọn tối đa 2 ngày để tập buổi sáng + buổi chiều. Chọn từ các ngày tập ưa thích của bạn."}
              </p>
              {(() => {
                const ALL_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
                const DAY_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"];
                let preferredDays: string[] = [];
                try { preferredDays = JSON.parse(user?.preferred_run_days || "[]"); } catch { preferredDays = []; }
                const days = preferredDays.length > 0 ? preferredDays : ALL_DAYS;
                return (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                    {days.map((day: string) => {
                      const di = ALL_DAYS.indexOf(day);
                      const label = lang === "vi" ? DAY_VI[di] ?? day : day.slice(0, 3);
                      const selected = doubleDays.includes(day);
                      const disabled = !selected && doubleDays.length >= 2;
                      return (
                        <button
                          key={day}
                          type="button"
                          onClick={() => !disabled && toggleDoubleDay(day)}
                          style={{
                            padding: "6px 14px", borderRadius: "99px", fontSize: "12px", fontWeight: "600",
                            cursor: disabled ? "not-allowed" : "pointer", opacity: disabled ? 0.4 : 1,
                            border: selected ? "1.5px solid var(--accent-primary)" : "1.5px solid var(--border-color)",
                            background: selected ? "rgba(16,185,129,0.12)" : "rgba(0,0,0,0.04)",
                            color: selected ? "var(--accent-primary)" : "var(--text-secondary)",
                            transition: "all 120ms",
                          }}
                        >
                          {selected ? "⚡ " : ""}{label}
                        </button>
                      );
                    })}
                  </div>
                );
              })()}
              {doubleDays.length > 0 && (
                <p style={{ fontSize: "11px", color: "var(--accent-primary)", marginTop: "10px", fontWeight: "600" }}>
                  {lang === "en"
                    ? `Selected: ${doubleDays.join(", ")} — these days will have morning + afternoon sessions`
                    : `Đã chọn: ${doubleDays.join(", ")} — những ngày này sẽ có buổi sáng + buổi chiều`}
                </p>
              )}
            </div>

            {/* Language Settings Section */}







            <div style={{ marginTop: "10px" }}>







              <h3 style={{ fontSize: "14px", fontWeight: "700", borderBottom: "1px solid var(--border-color)", paddingBottom: "6px", marginBottom: "12px", color: "var(--accent-primary)" }}>







                {lang === "en" ? "LANGUAGE CONFIGURATION" : "CẤU HÌNH NGÔN NGỮ"}







              </h3>







              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px" }}>







                <span style={{ fontSize: "13.5px", color: "var(--text-primary)" }}>







                  {lang === "en" ? "Select Language:" : "Chọn ngôn ngữ:"}







                </span>







                <div style={{ display: "flex", background: "rgba(0, 0, 0, 0.05)", border: "1px solid var(--border-color)", padding: "2px", borderRadius: "8px", gap: "2px" }}>







                  <button







                    type="button"







                    onClick={() => handleSetLang("en")}







                    style={{ padding: "6px 12px", fontSize: "11px", borderRadius: "6px", border: "none", background: lang === "en" ? "var(--accent-primary)" : "transparent", color: lang === "en" ? "#ffffff" : "var(--text-secondary)", cursor: "pointer", fontWeight: lang === "en" ? "600" : "500", transition: "all 0.15s" }}







                  >







                    English







                  </button>







                  <button







                    type="button"







                    onClick={() => handleSetLang("vi")}







                    style={{ padding: "6px 12px", fontSize: "11px", borderRadius: "6px", border: "none", background: lang === "vi" ? "var(--accent-primary)" : "transparent", color: lang === "vi" ? "#ffffff" : "var(--text-secondary)", cursor: "pointer", fontWeight: lang === "vi" ? "600" : "500", transition: "all 0.15s" }}







                  >







                    Tiếng Việt







                  </button>







                </div>







              </div>







            </div>















            {/* Account Settings Section */}







            <div style={{ marginTop: "10px" }}>







              <h3 style={{ fontSize: "14px", fontWeight: "700", borderBottom: "1px solid var(--border-color)", paddingBottom: "6px", marginBottom: "12px", color: "var(--accent-primary)" }}>{lang === "en" ? "ACCOUNT & SECURITY" : "TÀI KHOẢN & BẢO MẬT"}</h3>







              <div style={{ fontSize: "13px", display: "flex", flexDirection: "column", gap: "6px", marginBottom: "14px" }}>







                <div>{lang === "en" ? "Name:" : "Tên:"} <strong>{user.name}</strong></div>







                <div>Email: <strong>{user.email}</strong></div>







                <div>{lang === "en" ? "Login Provider:" : "Phương thức đăng nhập:"} <strong style={{ textTransform: "capitalize" }}>{user.provider}</strong></div>







              </div>















              {/* Password configuration */}







              {passwordMsg && (







                <div style={{ color: "#10b981", background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.15)", borderRadius: "8px", padding: "10px", fontSize: "12.5px", marginBottom: "12px" }}>







                  ✓ {passwordMsg}







                </div>







              )}







              {passwordError && (







                <div style={{ color: "#ef4444", background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.15)", borderRadius: "8px", padding: "10px", fontSize: "12.5px", marginBottom: "12px" }}>







                  <Warning weight="fill" style={{marginRight: "4px", verticalAlign: "middle"}}/> {passwordError}







                </div>







              )}















              {!user.has_password ? (







                <div style={{ background: "rgba(245,158,11,0.06)", border: "1px solid rgba(245,158,11,0.2)", borderRadius: "12px", padding: "14px" }}>







                  <div style={{ fontSize: "12.5px", fontWeight: "700", color: "#d97706", marginBottom: "4px" }}>







                    {lang === "en" ? "No Password Configured" : "Chưa Thiết lập Mật khẩu"}







                  </div>







                  <p style={{ fontSize: "12px", color: "var(--text-secondary)", margin: "0 0 10px 0" }}>







                    {lang === "en"







                      ? `You currently sign in via OAuth (${user.provider}). Add a password to log in directly using your email address later.`







                      : `Bạn đang đăng nhập qua OAuth (${user.provider}). Hãy thiết lập mật khẩu để đăng nhập trực tiếp bằng email sau này.`}







                  </p>















                  {passwordFormOpen ? (







                    <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>







                      <div>







                        <label style={labelStyle}>{lang === "en" ? "New Password" : "Mật khẩu Mới"}</label>







                        <input type="password" style={inputStyle} placeholder="Min 8 characters" value={newPassword} onChange={e => setNewPassword(e.target.value)} required minLength={8} />







                      </div>







                      <div>







                        <label style={labelStyle}>{lang === "en" ? "Confirm New Password" : "Xác nhận Mật khẩu Mới"}</label>







                        <input type="password" style={inputStyle} placeholder="Repeat password" value={confirmNewPassword} onChange={e => setConfirmNewPassword(e.target.value)} required minLength={8} />







                      </div>







                      <div style={{ display: "flex", gap: "8px" }}>







                        <button type="button" onClick={handleSetPassword} className="btn btn-primary" style={{ height: "32px", fontSize: "12px", padding: "0 14px" }}>







                          {lang === "en" ? "Set Password" : "Thiết lập mật khẩu"}







                        </button>







                        <button type="button" onClick={() => setPasswordFormOpen(false)} style={{ height: "32px", border: "1px solid var(--border-color)", background: "transparent", color: "var(--text-secondary)", borderRadius: "8px", padding: "0 12px", cursor: "pointer", fontSize: "12px" }}>







                          {lang === "en" ? "Cancel" : "Hủy"}







                        </button>







                      </div>







                    </div>







                  ) : (







                    <button type="button" onClick={() => setPasswordFormOpen(true)} className="btn btn-primary" style={{ height: "32px", fontSize: "12.5px", padding: "0 14px" }}>







                      🔑 {lang === "en" ? "Set Account Password" : "Thiết lập Mật khẩu Tài khoản"}







                    </button>







                  )}







                </div>







              ) : (







                <div>







                  {passwordFormOpen ? (







                    <div style={{ background: "rgba(255,255,255,0.2)", border: "1px solid var(--border-color)", borderRadius: "12px", padding: "14px", display: "flex", flexDirection: "column", gap: "10px" }}>







                      <div>







                        <label style={labelStyle}>{lang === "en" ? "New Password" : "Mật khẩu Mới"}</label>







                        <input type="password" style={inputStyle} placeholder="Min 8 characters" value={newPassword} onChange={e => setNewPassword(e.target.value)} required minLength={8} />







                      </div>







                      <div>







                        <label style={labelStyle}>{lang === "en" ? "Confirm New Password" : "Xác nhận Mật khẩu Mới"}</label>







                        <input type="password" style={inputStyle} placeholder="Repeat password" value={confirmNewPassword} onChange={e => setConfirmNewPassword(e.target.value)} required minLength={8} />







                      </div>







                      <div style={{ display: "flex", gap: "8px" }}>







                        <button type="button" onClick={handleSetPassword} className="btn btn-primary" style={{ height: "32px", fontSize: "12px", padding: "0 14px" }}>







                          {lang === "en" ? "Update Password" : "Cập nhật Mật khẩu"}







                        </button>







                        <button type="button" onClick={() => setPasswordFormOpen(false)} style={{ height: "32px", border: "1px solid var(--border-color)", background: "transparent", color: "var(--text-secondary)", borderRadius: "8px", padding: "0 12px", cursor: "pointer", fontSize: "12px" }}>







                          {lang === "en" ? "Cancel" : "Hủy"}







                        </button>







                      </div>







                    </div>







                  ) : (







                    <button type="button" onClick={() => setPasswordFormOpen(true)} style={{ height: "32px", border: "1px solid var(--border-color)", background: "transparent", color: "var(--text-primary)", borderRadius: "8px", padding: "0 12px", cursor: "pointer", fontSize: "12.5px", fontWeight: "600" }}>







                      🔄 {lang === "en" ? "Change Account Password" : "Thay đổi Mật khẩu Tài khoản"}







                    </button>







                  )}







                </div>







              )}







            </div>















            {/* Bottom Actions */}







            <div style={{ display: "flex", gap: "10px", borderTop: "1px solid var(--border-color)", paddingTop: "18px", marginTop: "10px" }}>







              <button type="button" onClick={() => { setProfileSettingsOpen(false); setPasswordFormOpen(false); setPasswordMsg(""); setPasswordError(""); }} style={{ height: "40px", borderRadius: "10px", border: "1px solid var(--border-color)", background: "transparent", color: "var(--text-secondary)", fontWeight: "600", fontSize: "13px", cursor: "pointer", padding: "0 14px" }}>







                {lang === "en" ? "Cancel" : "Hủy"}







              </button>







              <button type="submit" className="btn btn-primary" style={{ flex: 1, height: "40px", fontSize: "13px" }} disabled={savingProfile}>







                {savingProfile ? (lang === "en" ? "Saving..." : "Đang lưu...") : (lang === "en" ? "Save Settings" : "Lưu cài đặt")}







              </button>







              <button







                type="button"







                onClick={() => { setProfileSettingsOpen(false); handleLogout(); }}







                style={{ height: "40px", borderRadius: "10px", border: "1px solid rgba(239,68,68,0.3)", background: "rgba(239,68,68,0.06)", color: "#dc2626", fontWeight: "700", fontSize: "13px", cursor: "pointer", padding: "0 14px", whiteSpace: "nowrap" }}







              >







                🚪 {lang === "en" ? "Sign Out" : "Đăng xuất"}







              </button>







            </div>







          </form>















        </div>







      </div>







    );







  };
