import { describe, it, expect, vi, beforeEach } from "vitest";
import { act } from "@testing-library/react";
import { renderHookWithApp } from "../test-utils/renderWithAppContext";
import { useAppAuth } from "./useAppAuth";

function jsonResponse(body: unknown, ok = true) {
  return { ok, json: async () => body } as Response;
}

describe("useAppAuth", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    localStorage.clear();
  });

  it("stores the session token and opens onboarding after register", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse({
          session_token: "tok-register-123",
          user: { id: 1, email: "ada@uphill.ai", onboarding_complete: false },
        })
      )
      .mockResolvedValueOnce(jsonResponse({ plans: [] })); // fetchRecentPlansWithToken

    const { result } = renderHookWithApp(() => useAppAuth());

    act(() => {
      result.current.setNameInput("Ada Athlete");
      result.current.setEmailInput("ada@uphill.ai");
      result.current.setPasswordInput("correcthorse");
      result.current.setConfirmPasswordInput("correcthorse");
    });

    await act(async () => {
      await result.current.handleRegister({ preventDefault: () => {} } as React.FormEvent);
    });

    expect(localStorage.getItem("uphill_session_token")).toBe("tok-register-123");
    const [url, opts] = fetchMock.mock.calls[0];
    expect(url).toContain("/api/auth/register");
    expect(JSON.parse(opts.body)).toMatchObject({
      name: "Ada Athlete",
      email: "ada@uphill.ai",
      password: "correcthorse",
    });
  });

  it("rejects registration when passwords do not match, without calling fetch", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    const { result } = renderHookWithApp(() => useAppAuth());

    act(() => {
      result.current.setPasswordInput("correcthorse");
      result.current.setConfirmPasswordInput("different-password");
    });

    await act(async () => {
      await result.current.handleRegister({ preventDefault: () => {} } as React.FormEvent);
    });

    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("surfaces the server error message on failed login", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: "Invalid email or password." }, false));

    const { result } = renderHookWithApp(() => useAppAuth());

    act(() => {
      result.current.setEmailInput("wrong@uphill.ai");
      result.current.setPasswordInput("wrong-password");
    });

    await act(async () => {
      await result.current.handleEmailLogin({ preventDefault: () => {} } as React.FormEvent);
    });

    expect(localStorage.getItem("uphill_session_token")).toBeNull();
  });

  it("stores the session token on successful login", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse({
          session_token: "tok-login-456",
          user: { id: 2, email: "login-test@uphill.ai", onboarding_complete: true },
        })
      )
      .mockResolvedValueOnce(jsonResponse({ plans: [] }));

    const { result } = renderHookWithApp(() => useAppAuth());

    act(() => {
      result.current.setEmailInput("login-test@uphill.ai");
      result.current.setPasswordInput("correcthorse");
    });

    await act(async () => {
      await result.current.handleEmailLogin({ preventDefault: () => {} } as React.FormEvent);
    });

    expect(localStorage.getItem("uphill_session_token")).toBe("tok-login-456");
  });
});
