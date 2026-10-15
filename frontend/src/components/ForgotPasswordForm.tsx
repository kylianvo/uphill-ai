import React, { useEffect, useState } from "react";
import { translations } from "../app/translations";

type Props = {
  lang: "en" | "vi";
  initialEmail: string;
  onRequestCode: (email: string) => Promise<void>;
  onReset: (email: string, code: string, newPassword: string) => Promise<void>;
  onBack: () => void;
};

const RESEND_SECONDS = 60;
// Same look as the AuthModal fields.
const inputStyle: React.CSSProperties = { borderRadius: "8px", width: "100%", height: "36px", margin: 0, padding: "0 10px", fontSize: "13px", background: "transparent", border: "1px solid var(--border-color)", color: "var(--text-primary)", boxSizing: "border-box" };
const labelStyle: React.CSSProperties = { display: "block", fontSize: "11.5px", fontWeight: 600, color: "var(--text-muted)", marginBottom: "5px" };
const linkStyle: React.CSSProperties = { background: "none", border: "none", color: "var(--accent-primary)", fontSize: "12.5px", fontWeight: 600, cursor: "pointer", minHeight: "44px", padding: 0 };

export default function ForgotPasswordForm({ lang, initialEmail, onRequestCode, onReset, onBack }: Props) {
  const t = (key: keyof typeof translations.en) => translations[lang]?.[key] || translations.en[key];
  const [step, setStep] = useState<"email" | "code">("email");
  const [email, setEmail] = useState(initialEmail);
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [resendIn, setResendIn] = useState(0);

  useEffect(() => {
    if (resendIn <= 0) return;
    const id = setTimeout(() => setResendIn((s) => s - 1), 1000);
    return () => clearTimeout(id);
  }, [resendIn]);

  const sendCode = async () => {
    setBusy(true);
    setError("");
    try {
      await onRequestCode(email.trim());
      setStep("code");
      setResendIn(RESEND_SECONDS);
    } catch {
      setError(t("auth_send_failed"));
    } finally {
      setBusy(false);
    }
  };

  const reset = async () => {
    setBusy(true);
    setError("");
    try {
      await onReset(email.trim(), code.trim(), newPassword);
    } catch {
      setError(t("auth_reset_invalid"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); if (step === "email") sendCode(); else reset(); }}
      style={{ display: "flex", flexDirection: "column", gap: "12px" }}
    >
      <div style={{ fontSize: "15px", fontWeight: 700 }}>{t("auth_forgot_title")}</div>
      <p style={{ margin: 0, fontSize: "12.5px", color: "var(--text-muted)" }}>
        {step === "email" ? t("auth_forgot_intro") : t("auth_code_sent")}
      </p>
      {error && <div role="alert" style={{ color: "#ef4444", fontSize: "12.5px" }}>{error}</div>}

      <div>
        <label htmlFor="forgot-email" style={labelStyle}>Email</label>
        <input id="forgot-email" type="email" style={inputStyle} className="chat-input" value={email}
          onChange={(e) => setEmail(e.target.value)} required readOnly={step === "code"} autoComplete="username" />
      </div>

      {step === "email" ? (
        <button type="submit" className="btn btn-primary" style={{ width: "100%", height: "40px", fontSize: "13.5px" }}
          disabled={busy || !email.trim()}>
          {t("auth_send_code")}
        </button>
      ) : (
        <>
          <div>
            <label htmlFor="forgot-code" style={labelStyle}>{t("auth_code_label")}</label>
            <input id="forgot-code" style={inputStyle} className="chat-input" value={code}
              onChange={(e) => setCode(e.target.value)} inputMode="numeric" autoComplete="one-time-code"
              maxLength={8} required />
          </div>
          <div>
            <label htmlFor="forgot-new-password" style={labelStyle}>{t("auth_new_password")}</label>
            <input id="forgot-new-password" type="password" style={inputStyle} className="chat-input"
              value={newPassword} onChange={(e) => setNewPassword(e.target.value)} minLength={8}
              autoComplete="new-password" required />
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: "100%", height: "40px", fontSize: "13.5px" }}
            disabled={busy || code.trim().length !== 6 || newPassword.length < 8}>
            {t("auth_reset_submit")}
          </button>
          <button type="button" style={linkStyle} onClick={sendCode} disabled={busy || resendIn > 0}>
            {resendIn > 0 ? t("auth_resend_in").replace("{s}", String(resendIn)) : t("auth_resend_code")}
          </button>
        </>
      )}

      <button type="button" style={linkStyle} onClick={onBack}>{t("auth_back_to_sign_in")}</button>
    </form>
  );
}
