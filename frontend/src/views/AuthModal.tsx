/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState } from "react";
import { useAppContext } from "../contexts/AppContext";
import { useAppAuth } from "../hooks/useAppAuth";
import { usePlanner } from "../hooks/usePlanner";
import { translations } from "../app/translations";
import { X, XCircle, Warning } from '@phosphor-icons/react';

export default function AuthModal() {
  const ctx = useAppContext();
  const { lang, authModalOpen, setAuthModalOpen, authErrorMsg, setAuthErrorMsg } = ctx;
  const {
    emailInput, setEmailInput,
    passwordInput, setPasswordInput,
    nameInput, setNameInput,
    confirmPasswordInput, setConfirmPasswordInput,
    authTab, setAuthTab,
    showPassword, setShowPassword,
    authLoading, setAuthLoading,
    handleRegister, handleEmailLogin
  } = useAppAuth();
  const t = (key: keyof typeof translations.en) => translations[lang]?.[key] || translations.en[key] || key;




    if (!authModalOpen) return null;



    const DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"];



    const inputStyle: React.CSSProperties = { borderRadius: "8px", width: "100%", height: "36px", margin: 0, padding: "0 10px", fontSize: "13px", background: "transparent", border: "1px solid var(--border-color)", color: "var(--text-primary)", boxSizing: "border-box" as const };



    const labelStyle: React.CSSProperties = { display: "block", fontSize: "11.5px", fontWeight: "600", color: "var(--text-muted)", marginBottom: "5px" };



    const cardBtnStyle = (selected: boolean): React.CSSProperties => ({



      flex: "1 1 auto", minWidth: "120px", padding: "10px 12px", borderRadius: "10px", border: `1.5px solid ${selected ? "var(--accent-primary)" : "var(--border-color)"}`,



      background: selected ? "rgba(16,185,129,0.08)" : "rgba(255,255,255,0.3)", color: selected ? "var(--accent-primary)" : "var(--text-primary)",



      fontWeight: selected ? "700" : "500", fontSize: "12.5px", cursor: "pointer", textAlign: "center" as const, transition: "all 0.15s"



    });







    return (



      <div style={{ position: "fixed", inset: 0, background: "rgba(255,255,255,0.35)", backdropFilter: "blur(16px)", display: "flex", justifyContent: "center", alignItems: "center", zIndex: 1000, padding: "20px" }}>



        <div style={{ background: "var(--bg-card)", backdropFilter: "blur(30px)", border: "1px solid var(--border-color)", borderRadius: "24px", padding: "32px", width: "100%", maxWidth: "480px", maxHeight: "90vh", overflowY: "auto", boxShadow: "0 20px 60px rgba(0,0,0,0.1)", position: "relative", color: "var(--text-primary)" }}>







          {/* Header */}



          <button



            onClick={() => setAuthModalOpen(false)}



            style={{ position: "absolute", top: "20px", right: "20px", background: "transparent", border: "none", cursor: "pointer", color: "var(--text-muted)", padding: "4px", display: "flex", alignItems: "center", justifyContent: "center", borderRadius: "50%", transition: "all 0.2s" }}



            onMouseOver={(e) => e.currentTarget.style.color = "var(--text-primary)"}



            onMouseOut={(e) => e.currentTarget.style.color = "var(--text-muted)"}



          >



            <XCircle size={24} weight="duotone" />



          </button>



          <div style={{ textAlign: "center", marginBottom: "24px" }}>



            <div style={{ fontSize: "26px", fontWeight: "800", letterSpacing: "-0.03em" }}>Uphill<span style={{ color: "var(--accent-primary)" }}>.AI</span></div>



            <p style={{ color: "var(--text-muted)", fontSize: "13px", marginTop: "4px" }}>Your elite running intelligence coach</p>



          </div>







          {authErrorMsg && (



            <div style={{ color: "#ef4444", background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.15)", borderRadius: "8px", padding: "10px", fontSize: "12.5px", marginBottom: "16px" }}>



              <Warning weight="fill" style={{marginRight: "4px", verticalAlign: "middle"}}/> {authErrorMsg}



            </div>



          )}







          {/* OAuth Buttons (always visible) */}



          <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "16px" }}>



            <div id="google-signin-btn" style={{ width: "100%", height: "40px", minHeight: "40px", display: "flex", justifyContent: "center" }} />



          </div>







          {/* Divider */}



          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>



            <div style={{ flex: 1, height: "1px", background: "rgba(0,0,0,0.08)" }} />



            <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>or</span>



            <div style={{ flex: 1, height: "1px", background: "rgba(0,0,0,0.08)" }} />



          </div>







          {/* Tab switcher */}



          <div style={{ display: "flex", background: "rgba(255,255,255,0.4)", border: "1px solid var(--border-color)", padding: "3px", borderRadius: "10px", marginBottom: "18px" }}>



            {(["login", "register"] as const).map(tab => (



              <button key={tab} type="button" onClick={() => { setAuthTab(tab); setAuthErrorMsg(""); }}



                style={{ flex: 1, height: "30px", fontSize: "12px", borderRadius: "8px", border: "none", background: authTab === tab ? "var(--accent-primary)" : "transparent", color: authTab === tab ? "#fff" : "var(--text-secondary)", fontWeight: "600", cursor: "pointer", transition: "all 0.15s" }}>



                {tab === "login" ? "Sign In" : "Create Account"}



              </button>



            ))}



          </div>







          {authTab === "login" ? (



            <form onSubmit={handleEmailLogin} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>



              <div>



                <label style={labelStyle}>Email</label>



                <input type="email" style={inputStyle} className="chat-input" placeholder="you@example.com" value={emailInput} onChange={e => setEmailInput(e.target.value)} required />



              </div>



              <div>



                <label style={labelStyle}>Password</label>



                <div style={{ position: "relative" }}>



                  <input type={showPassword ? "text" : "password"} style={{ ...inputStyle, paddingRight: "40px" }} className="chat-input" placeholder="Your password" value={passwordInput} onChange={e => setPasswordInput(e.target.value)} required />



                  <button type="button" onClick={() => setShowPassword(!showPassword)} style={{ position: "absolute", right: "10px", top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", fontSize: "14px", color: "var(--text-muted)" }}>{showPassword ? "👁️" : "🙈"}</button>



                </div>



              </div>



              <button type="submit" className="btn btn-primary" style={{ width: "100%", height: "40px", fontSize: "13.5px", marginTop: "4px" }} disabled={authLoading}>



                {authLoading ? "Signing in..." : "Sign In"}



              </button>



            </form>



          ) : (



            <form onSubmit={handleRegister} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>



              <div>



                <label style={labelStyle}>Full Name</label>



                <input type="text" style={inputStyle} className="chat-input" placeholder="Alex Runner" value={nameInput} onChange={e => setNameInput(e.target.value)} required />



              </div>



              <div>



                <label style={labelStyle}>Email</label>



                <input type="email" style={inputStyle} className="chat-input" placeholder="you@example.com" value={emailInput} onChange={e => setEmailInput(e.target.value)} required />



              </div>



              <div>



                <label style={labelStyle}>Password</label>



                <div style={{ position: "relative" }}>



                  <input type={showPassword ? "text" : "password"} style={{ ...inputStyle, paddingRight: "40px" }} className="chat-input" placeholder="Min 8 characters" value={passwordInput} onChange={e => setPasswordInput(e.target.value)} required minLength={8} />



                  <button type="button" onClick={() => setShowPassword(!showPassword)} style={{ position: "absolute", right: "10px", top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", fontSize: "14px", color: "var(--text-muted)" }}>{showPassword ? "👁️" : "🙈"}</button>



                </div>



              </div>



              <div>



                <label style={labelStyle}>Confirm Password</label>



                <input type="password" style={inputStyle} className="chat-input" placeholder="Repeat password" value={confirmPasswordInput} onChange={e => setConfirmPasswordInput(e.target.value)} required minLength={8} />



              </div>



              <button type="submit" className="btn btn-primary" style={{ width: "100%", height: "40px", fontSize: "13.5px", marginTop: "4px" }} disabled={authLoading}>



                {authLoading ? "Creating account..." : "Create Account"}



              </button>



            </form>



          )}



          {authLoading && <div style={{ textAlign: "center", color: "var(--accent-secondary)", fontSize: "11px", marginTop: "12px" }}>Authenticating...</div>}



        </div>



      </div>



    );



  };
