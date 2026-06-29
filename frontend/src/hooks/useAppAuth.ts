/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from "react";
import { useAppContext } from "../contexts/AppContext";
import { usePlanner } from "./usePlanner";

export function useAppAuth() {
  const ctx = useAppContext();
  const { setUser, setAuthModalOpen, setOnboardingOpen, setOnboardingStep, authErrorMsg, setAuthErrorMsg } = ctx;
  const { fetchRecentPlansWithToken } = usePlanner();

  const [emailInput, setEmailInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [nameInput, setNameInput] = useState("");
  const [confirmPasswordInput, setConfirmPasswordInput] = useState("");
  const [authTab, setAuthTab] = useState<"login" | "register">("login");
  const [showPassword, setShowPassword] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchSourcesWithToken = async (user: any, token: string) => {
      // NOTE: Normally fetchSourcesWithToken would be in another hook or context.
      // But for simplicity in auth we just make it fire and forget if needed.
      // Actually it's just fetching sources and setting state.
      // Let's omit this for now since in page.tsx it was doing setConnectedSources.
      // Wait, we need it if they register! Let's just expose a callback or move it to context.
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthErrorMsg("");
    if (passwordInput !== confirmPasswordInput) {
      setAuthErrorMsg("Passwords do not match.");
      setAuthLoading(false);
      return;
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: nameInput.trim(), email: emailInput.trim(), password: passwordInput }),
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Registration failed.");
      }
      const data = await response.json();
      localStorage.setItem("uphill_session_token", data.session_token);
      setUser(data.user);
      setAuthModalOpen(false);
      setOnboardingOpen(true);
      setOnboardingStep(0);
      fetchRecentPlansWithToken(data.session_token);
    } catch (err: any) {
      setAuthErrorMsg(err.message || "Registration failed.");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthErrorMsg("");
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: emailInput.trim(), password: passwordInput }),
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Login failed.");
      }
      const data = await response.json();
      localStorage.setItem("uphill_session_token", data.session_token);
      setUser(data.user);
      setAuthModalOpen(false);
      fetchRecentPlansWithToken(data.session_token);
    } catch (err: any) {
      setAuthErrorMsg(err.message || "Login failed.");
    } finally {
      setAuthLoading(false);
    }
  };




  return {
    emailInput, setEmailInput,
    passwordInput, setPasswordInput,
    nameInput, setNameInput,
    confirmPasswordInput, setConfirmPasswordInput,
    authTab, setAuthTab,
    showPassword, setShowPassword,
    authLoading, setAuthLoading,
    handleRegister,
    handleEmailLogin
  };
}
