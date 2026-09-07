/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState } from "react";
import { useAppContext } from "../contexts/AppContext";

import { translations } from "../app/translations";
import { usePaceZones } from "../hooks/usePaceZones";
import { ZONE_NUMBER_COLORS } from "../data/workoutLibrary";
import { X, User, Heartbeat, Watch, SignOut, Warning, Bell, CheckCircle, Key, ArrowCounterClockwise, Lightbulb, Lightning, Check, ArrowsClockwise, Sparkle } from '@phosphor-icons/react';
import {
  scheduleDailyKnowledgeReminder,
  scheduleNotification,
  cancelNotification,
  requestNotificationPermission,
  buildWorkoutReminderContent,
  DAILY_WORKOUT_REMINDER_ID,
  DAILY_KNOWLEDGE_REMINDER_ID,
} from '../utils/notifications';
import { triggerHaptic } from '../utils/native';
import ConnectedAccounts from '../components/ConnectedAccounts';

export default function ProfileSettingsModal() {
  const ctx = useAppContext();
  const { lang, setLang, user, setUser, profileSettingsOpen, setProfileSettingsOpen, profileForm, setProfileForm, activePlan, setActivePlan, workouts, setWorkouts, setSources, setAuthModalOpen, setOnboardingOpen, handleLogout } = ctx;
  const { zones: paceZones, loading: syncingFitness, fetchPaceZones, syncFitness } = usePaceZones();
  const [selectedModel, setSelectedModel] = useState<"4_zone" | "5_zone">(
    user?.pace_zone_model === "4_zone" ? "4_zone" : "5_zone"
  );
  const [thresholdPace, setThresholdPace] = useState<string>(user?.threshold_pace || "");
  const [syncMsg, setSyncMsg] = useState<string>("");

  const [prevUser, setPrevUser] = useState(user);
  if (user !== prevUser) {
    setPrevUser(user);
    if (user?.threshold_pace) setThresholdPace(user.threshold_pace);
    if (user?.pace_zone_model === "4_zone" || user?.pace_zone_model === "5_zone") {
      setSelectedModel(user.pace_zone_model);
    }
  }

  React.useEffect(() => {
    if (profileSettingsOpen) {
      fetchPaceZones(selectedModel);
    }
  }, [profileSettingsOpen, selectedModel]);

  const handleSyncFitness = async () => {
    setSyncMsg(lang === "vi" ? "Đang đồng bộ từ COROS..." : "Syncing from COROS...");
    triggerHaptic();
    const res = await syncFitness();
    if (res.success && res.data) {
      const tp = res.data.threshold_pace;
      const vo2 = res.data.coros_vo2max;
      if (tp) {
        setThresholdPace(tp);
      }
      setSyncMsg(
        lang === "vi"
          ? `Đã đồng bộ! Ngưỡng: ${tp || "—"} /km | VO2max: ${vo2 || "—"}`
          : `Synced! Threshold: ${tp || "—"} /km | VO2max: ${vo2 || "—"}`
      );
      await fetchPaceZones(selectedModel);
    } else {
      setSyncMsg(lang === "vi" ? `Đồng bộ thất bại: ${res.error}` : `Sync failed: ${res.error}`);
    }
    setTimeout(() => setSyncMsg(""), 5000);
  };
  const [passwordFormOpen, setPasswordFormOpen] = useState(false);
  const [newPassword, setNewPassword] = useState("");
  const [passwordMsg, setPasswordMsg] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");

  const [reminderEnabled, setReminderEnabled] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("uphill_reminder_enabled") === "true";
    }
    return false;
  });
  const [reminderTime, setReminderTime] = useState<string>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("uphill_reminder_time") || "07:00";
    }
    return "07:00";
  });
  const [testNotifMsg, setTestNotifMsg] = useState<string>("");

  const [knowledgeReminderEnabled, setKnowledgeReminderEnabled] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("uphill_knowledge_reminder_enabled") === "true";
    }
    return false;
  });

  const handleToggleReminder = async (enabled: boolean) => {
    setReminderEnabled(enabled);
    if (typeof window !== "undefined") {
      localStorage.setItem("uphill_reminder_enabled", String(enabled));
    }
    if (enabled) {
      await requestNotificationPermission();
      const [h, m] = reminderTime.split(":").map(Number);
      const { title, body } = buildWorkoutReminderContent(activePlan, workouts, lang);
      await scheduleNotification({
        id: DAILY_WORKOUT_REMINDER_ID,
        title,
        body,
        repeatDailyAt: { hour: h || 7, minute: m || 0 },
        extra: { type: "daily_workout_reminder" },
      });
      triggerHaptic();
    } else {
      await cancelNotification(DAILY_WORKOUT_REMINDER_ID);
    }
  };

  const handleToggleKnowledgeReminder = async (enabled: boolean) => {
    setKnowledgeReminderEnabled(enabled);
    if (typeof window !== "undefined") {
      localStorage.setItem("uphill_knowledge_reminder_enabled", String(enabled));
    }
    if (enabled) {
      await requestNotificationPermission();
      const [h, m] = reminderTime.split(":").map(Number);
      await scheduleDailyKnowledgeReminder(h || 7, m || 0, lang);
      triggerHaptic();
    } else {
      await cancelNotification(DAILY_KNOWLEDGE_REMINDER_ID);
    }
  };

  const handleSendTestNotification = async () => {
    setTestNotifMsg(lang === "en" ? "Sending..." : "Đang gửi...");
    triggerHaptic();
    const success = await scheduleNotification({
      title: lang === "en" ? "Uphill AI Coach" : "Huấn luyện viên Uphill AI",
      body: lang === "en" ? "Notifications are active! Your training reminders will appear here." : "Thông báo đã sẵn sàng! Lịch tập sẽ được nhắc nhở tại đây.",
    });
    if (success) {
      setTestNotifMsg(lang === "en" ? "Notification sent!" : "Đã gửi thông báo!");
    } else {
      setTestNotifMsg(lang === "en" ? "Enable notifications in settings" : "Vui lòng cấp quyền thông báo");
    }
    setTimeout(() => setTestNotifMsg(""), 3000);
  };


  React.useEffect(() => {
    if (profileSettingsOpen && user) {
      fetchPaceZones();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profileSettingsOpen]);

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







          gender: profileForm.gender || null,
          height_cm: profileForm.height_cm ? parseFloat(profileForm.height_cm) : null,
          weight_kg: profileForm.weight_kg ? parseFloat(profileForm.weight_kg) : null,







          max_hr: parseInt(profileForm.max_hr),







          resting_hr: parseInt(profileForm.resting_hr),







          aet_hr: parseInt(profileForm.aet_hr),







          ant_hr: parseInt(profileForm.ant_hr),





          gemini_api_key: profileForm.gemini_api_key,







          zone2_pace_min: profileForm.zone2_pace_min,







          zone2_pace_max: profileForm.zone2_pace_max,
          threshold_pace: thresholdPace || null,
          pace_zone_model: selectedModel,







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







            <X size={20} aria-hidden="true" />







          </button>















          {/* Header */}







          <div style={{ marginBottom: "24px" }}>







            <div style={{ fontSize: "22px", fontWeight: "800", letterSpacing: "-0.02em" }}>







              {lang === "en" ? "Profile Settings" : "Cài đặt Hồ sơ"}







            </div>







            <p style={{ color: "var(--text-muted)", fontSize: "13px", marginTop: "4px" }}>







              {lang === "en" ? "Manage your physiology parameters and security settings" : "Quản lý các thông số thể chất và cài đặt bảo mật của bạn"}







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

                  <label style={labelStyle}>{lang === "en" ? "Gender" : "Giới tính"}</label>

                  <select style={inputStyle} value={profileForm.gender} onChange={e => setProfileForm({ ...profileForm, gender: e.target.value })}>
                    <option value="">{lang === "en" ? "Prefer not to say" : "Không muốn tiết lộ"}</option>
                    <option value="male">{lang === "en" ? "Male" : "Nam"}</option>
                    <option value="female">{lang === "en" ? "Female" : "Nữ"}</option>
                    <option value="other">{lang === "en" ? "Other" : "Khác"}</option>
                  </select>

                </div>

                <div>

                  <label style={labelStyle}>{lang === "en" ? "Height (cm)" : "Chiều cao (cm)"}</label>

                  <input type="number" style={inputStyle} value={profileForm.height_cm} onChange={e => setProfileForm({ ...profileForm, height_cm: e.target.value })} />

                </div>

                <div>

                  <label style={labelStyle}>{lang === "en" ? "Weight (kg)" : "Cân nặng (kg)"}</label>

                  <input type="number" step="0.1" style={inputStyle} value={profileForm.weight_kg} onChange={e => setProfileForm({ ...profileForm, weight_kg: e.target.value })} />

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

                {/* Threshold Pace & COROS Sync Card */}
                <div
                  style={{
                    gridColumn: "1 / -1",
                    padding: "12px 14px",
                    borderRadius: "10px",
                    background: "rgba(0, 0, 0, 0.02)",
                    border: "1px solid rgba(0, 0, 0, 0.06)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "6px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <Lightning size={16} weight="bold" color="var(--accent-primary)" />
                      <span style={{ fontSize: "13px", fontWeight: 700, color: "var(--text-primary)" }}>
                        {lang === "vi" ? "Ngưỡng Pace (Threshold Pace)" : "Threshold Pace"}
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={handleSyncFitness}
                      disabled={syncingFitness}
                      style={{
                        minHeight: "44px",
                        padding: "6px 12px",
                        borderRadius: "8px",
                        background: "rgba(25, 206, 139, 0.12)",
                        color: "var(--accent-primary)",
                        border: "1px solid rgba(25, 206, 139, 0.3)",
                        fontSize: "12px",
                        fontWeight: "700",
                        cursor: syncingFitness ? "default" : "pointer",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "6px",
                      }}
                      aria-label={lang === "vi" ? "Đồng bộ từ COROS" : "Sync from COROS"}
                    >
                      <ArrowsClockwise size={14} weight="bold" />
                      <span>
                        {syncingFitness
                          ? lang === "vi"
                            ? "Đang đồng bộ..."
                            : "Syncing..."
                          : lang === "vi"
                          ? "Đồng bộ từ COROS"
                          : "Sync from COROS"}
                      </span>
                    </button>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <input
                      type="text"
                      placeholder="4:34"
                      style={{ ...inputStyle, flex: 1 }}
                      value={thresholdPace}
                      onChange={(e) => setThresholdPace(e.target.value)}
                    />
                    {user?.coros_vo2max && (
                      <div style={{ fontSize: "11px", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                        VO2max: <strong style={{ color: "var(--text-primary)" }}>{user.coros_vo2max}</strong>
                      </div>
                    )}
                  </div>

                  {syncMsg && (
                    <div
                      style={{
                        fontSize: "11px",
                        color: syncMsg.includes("thất bại") || syncMsg.includes("failed") ? "var(--accent-alert)" : "var(--accent-primary)",
                        fontWeight: "600",
                      }}
                    >
                      {syncMsg}
                    </div>
                  )}
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

                <div style={{ marginTop: "14px" }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
                    <label style={{ ...labelStyle, margin: 0 }}>
                      {lang === "en" ? "Your Training Zones" : "Vùng Tập Luyện Của Bạn"}
                    </label>

                    {/* Model Toggle */}
                    <div style={{ display: "flex", gap: "6px" }}>
                      <button
                        type="button"
                        onClick={async () => {
                          setSelectedModel("5_zone");
                          triggerHaptic();
                          await fetchPaceZones("5_zone");
                        }}
                        style={{
                          minHeight: "36px",
                          padding: "4px 10px",
                          borderRadius: "6px",
                          border: selectedModel === "5_zone" ? "1px solid var(--accent-primary)" : "1px solid var(--border-color)",
                          background: selectedModel === "5_zone" ? "rgba(25, 206, 139, 0.12)" : "transparent",
                          color: selectedModel === "5_zone" ? "var(--accent-primary)" : "var(--text-secondary)",
                          fontSize: "11px",
                          fontWeight: "700",
                          cursor: "pointer",
                        }}
                      >
                        5-Zone
                      </button>
                      <button
                        type="button"
                        onClick={async () => {
                          setSelectedModel("4_zone");
                          triggerHaptic();
                          await fetchPaceZones("4_zone");
                        }}
                        style={{
                          minHeight: "36px",
                          padding: "4px 10px",
                          borderRadius: "6px",
                          border: selectedModel === "4_zone" ? "1px solid var(--accent-primary)" : "1px solid var(--border-color)",
                          background: selectedModel === "4_zone" ? "rgba(25, 206, 139, 0.12)" : "transparent",
                          color: selectedModel === "4_zone" ? "var(--accent-primary)" : "var(--text-secondary)",
                          fontSize: "11px",
                          fontWeight: "700",
                          cursor: "pointer",
                        }}
                      >
                        4-Zone (Uphill)
                      </button>
                    </div>
                  </div>

                  {/* Dynamic Zone Rows */}
                  {selectedModel === "4_zone" ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "6px" }}>
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "6px 10px", borderRadius: "8px", background: `${ZONE_NUMBER_COLORS[1]}14`, borderLeft: `3px solid ${ZONE_NUMBER_COLORS[1]}` }}>
                        <span style={{ fontSize: "12px", fontWeight: 700, color: ZONE_NUMBER_COLORS[1] }}>{lang === "en" ? "Zone 1 (Recovery < AeT)" : "Zone 1 (Phục hồi < AeT)"}</span>
                        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "1px" }}>
                          <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-primary)" }}>{paceZones ? `${paceZones.zone1_pace} /km` : "—"}</span>
                          <span style={{ fontSize: "10px", fontWeight: 500, color: "var(--text-muted)" }}>{paceZones ? paceZones.zone1_hr : ""}</span>
                        </div>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "6px 10px", borderRadius: "8px", background: `${ZONE_NUMBER_COLORS[2]}14`, borderLeft: `3px solid ${ZONE_NUMBER_COLORS[2]}` }}>
                        <span style={{ fontSize: "12px", fontWeight: 700, color: ZONE_NUMBER_COLORS[2] }}>{lang === "en" ? "Zone 2 (Aerobic Capacity AeT-AnT)" : "Zone 2 (Khả năng hiếu khí AeT-AnT)"}</span>
                        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "1px" }}>
                          <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-primary)" }}>{paceZones ? `${paceZones.zone2_pace} /km` : "—"}</span>
                          <span style={{ fontSize: "10px", fontWeight: 500, color: "var(--text-muted)" }}>{paceZones ? paceZones.zone2_hr : ""}</span>
                        </div>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "6px 10px", borderRadius: "8px", background: `${ZONE_NUMBER_COLORS[3]}14`, borderLeft: `3px solid ${ZONE_NUMBER_COLORS[3]}` }}>
                        <span style={{ fontSize: "12px", fontWeight: 700, color: ZONE_NUMBER_COLORS[3] }}>{lang === "en" ? "Zone 3 (Threshold AnT)" : "Zone 3 (Ngưỡng AnT)"}</span>
                        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "1px" }}>
                          <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-primary)" }}>{paceZones ? `${paceZones.zone3_pace} /km` : "—"}</span>
                          <span style={{ fontSize: "10px", fontWeight: 500, color: "var(--text-muted)" }}>{paceZones ? paceZones.zone3_hr : ""}</span>
                        </div>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "6px 10px", borderRadius: "8px", background: `${ZONE_NUMBER_COLORS[4]}14`, borderLeft: `3px solid ${ZONE_NUMBER_COLORS[4]}` }}>
                        <span style={{ fontSize: "12px", fontWeight: 700, color: ZONE_NUMBER_COLORS[4] }}>{lang === "en" ? "Zone 4 (Max / Anaerobic > AnT)" : "Zone 4 (Tối đa / Kỵ khí > AnT)"}</span>
                        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "1px" }}>
                          <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-primary)" }}>{paceZones ? `${paceZones.zone4_pace} /km` : "—"}</span>
                          <span style={{ fontSize: "10px", fontWeight: 500, color: "var(--text-muted)" }}>{paceZones ? paceZones.zone4_hr : ""}</span>
                        </div>
                      </div>
                    </div>
                  ) : (
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
                  )}
                </div>















              <div style={{ marginTop: "12px" }}>







                <label style={labelStyle}>{t("profile_gemini_key")}</label>







                <input type="password" style={inputStyle} placeholder={lang === "en" ? "Leave blank to use system key" : "Để trống để sử dụng key của hệ thống"} value={profileForm.gemini_api_key} onChange={e => setProfileForm({ ...profileForm, gemini_api_key: e.target.value })} />







              </div>







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







                  <Check size={14} weight="bold" aria-hidden="true" style={{ verticalAlign: "middle", marginRight: "4px" }} />{passwordMsg}







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







                      <Key size={14} weight="bold" aria-hidden="true" style={{ verticalAlign: "middle", marginRight: "6px" }} />{lang === "en" ? "Set Account Password" : "Thiết lập Mật khẩu Tài khoản"}







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







                      <ArrowCounterClockwise size={14} weight="bold" aria-hidden="true" style={{ verticalAlign: "middle", marginRight: "6px" }} />{lang === "en" ? "Change Account Password" : "Thay đổi Mật khẩu Tài khoản"}







                    </button>







                  )}







                </div>







              )}







            </div>







            {/* Mobile Training Reminders & Notifications */}
            <div style={{ background: "rgba(25, 206, 139, 0.04)", border: "1px solid rgba(25, 206, 139, 0.25)", borderRadius: "14px", padding: "16px", marginTop: "16px", display: "flex", flexDirection: "column", gap: "12px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <Bell size={18} weight="duotone" style={{ color: "var(--color-green)" }} />
                  <span style={{ fontWeight: "700", fontSize: "13.5px", color: "var(--text-bright)" }}>
                    {lang === "en" ? "Training Reminders" : "Nhắc nhở Tập luyện"}
                  </span>
                </div>
                <label style={{ display: "flex", alignItems: "center", cursor: "pointer" }}>
                  <input
                    type="checkbox"
                    checked={reminderEnabled}
                    onChange={(e) => handleToggleReminder(e.target.checked)}
                    style={{ width: "18px", height: "18px", accentColor: "var(--color-green)", cursor: "pointer" }}
                  />
                </label>
              </div>

              <div style={{ fontSize: "12px", color: "var(--text-secondary)", lineHeight: "1.4" }}>
                {lang === "en"
                  ? "Receive daily reminders for planned workouts and fueling targets directly on your device."
                  : "Nhận thông báo nhắc nhở bài tập và dinh dưỡng hàng ngày trực tiếp trên thiết bị."}
              </div>

              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingTop: "6px", borderTop: "1px dashed rgba(25, 206, 139, 0.2)" }}>
                <span style={{ fontSize: "12.5px", color: "var(--text-primary)", fontWeight: "600", display: "inline-flex", alignItems: "center" }}>
                  <Lightbulb size={15} weight="bold" aria-hidden="true" style={{ verticalAlign: "middle", marginRight: "6px", color: "var(--accent-primary)" }} />
                  {lang === "en" ? "Daily Knowledge" : "Kiến thức Hằng ngày"}
                </span>
                <label style={{ display: "flex", alignItems: "center", cursor: "pointer" }}>
                  <input
                    type="checkbox"
                    checked={knowledgeReminderEnabled}
                    onChange={(e) => handleToggleKnowledgeReminder(e.target.checked)}
                    style={{ width: "18px", height: "18px", accentColor: "var(--color-green)", cursor: "pointer" }}
                  />
                </label>
              </div>

              {(reminderEnabled || knowledgeReminderEnabled) && (
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingTop: "6px", borderTop: "1px dashed rgba(25, 206, 139, 0.2)" }}>
                  <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
                    {lang === "en" ? "Reminder Time" : "Giờ nhắc nhở"}:
                  </span>
                  <input
                    type="time"
                    value={reminderTime}
                    onChange={(e) => {
                      setReminderTime(e.target.value);
                      if (typeof window !== "undefined") {
                        localStorage.setItem("uphill_reminder_time", e.target.value);
                      }
                      const [h, m] = e.target.value.split(":").map(Number);
                      if (reminderEnabled) {
                        const { title, body } = buildWorkoutReminderContent(activePlan, workouts, lang);
                        scheduleNotification({
                          id: DAILY_WORKOUT_REMINDER_ID,
                          title,
                          body,
                          repeatDailyAt: { hour: h || 7, minute: m || 0 },
                          extra: { type: "daily_workout_reminder" },
                        });
                      }
                      if (knowledgeReminderEnabled) {
                        scheduleDailyKnowledgeReminder(h || 7, m || 0, lang);
                      }
                    }}
                    style={{ background: "rgba(255,255,255,0.7)", border: "1px solid var(--border-color)", borderRadius: "6px", padding: "4px 8px", fontSize: "12px", color: "var(--text-primary)" }}
                  />
                </div>
              )}

              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingTop: "4px" }}>
                <button
                  type="button"
                  onClick={handleSendTestNotification}
                  style={{ background: "rgba(255,255,255,0.8)", border: "1px solid var(--border-color)", borderRadius: "8px", padding: "6px 12px", fontSize: "11.5px", fontWeight: "600", cursor: "pointer", color: "var(--text-primary)", display: "inline-flex", alignItems: "center" }}
                >
                  <Lightning size={14} weight="fill" aria-hidden="true" style={{ verticalAlign: "middle", marginRight: "4px", color: "#f59e0b" }} />
                  {lang === "en" ? "Test Notification" : "Thử Thông báo"}
                </button>
                {testNotifMsg && (
                  <span style={{ fontSize: "11.5px", color: "var(--color-green)", fontWeight: "600", display: "flex", alignItems: "center", gap: "4px" }}>
                    <CheckCircle size={14} weight="fill" /> {testNotifMsg}
                  </span>
                )}
              </div>
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







                <SignOut size={16} weight="bold" aria-hidden="true" style={{ verticalAlign: "middle", marginRight: "6px" }} />{lang === "en" ? "Sign Out" : "Đăng xuất"}







              </button>







            </div>







          </form>

          <ConnectedAccounts />













        </div>







      </div>







    );







  };
