import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ForgotPasswordForm from "./ForgotPasswordForm";

const setup = (over: Partial<React.ComponentProps<typeof ForgotPasswordForm>> = {}) => {
  const props = {
    lang: "en" as const,
    initialEmail: "",
    onRequestCode: vi.fn().mockResolvedValue(undefined),
    onReset: vi.fn().mockResolvedValue(undefined),
    onBack: vi.fn(),
    ...over,
  };
  render(<ForgotPasswordForm {...props} />);
  return props;
};

describe("ForgotPasswordForm", () => {
  it("sends a code for the trimmed email and moves to the code step", async () => {
    const props = setup({ initialEmail: "  ada@uphill.ai " });
    fireEvent.click(screen.getByRole("button", { name: "Send code" }));
    await waitFor(() => expect(props.onRequestCode).toHaveBeenCalledWith("ada@uphill.ai"));
    expect(await screen.findByLabelText("6-digit code")).toBeDefined();
    expect(screen.getByText(/we sent a code/)).toBeDefined();
    expect((screen.getByRole("button", { name: /Resend code in/ }) as HTMLButtonElement).disabled).toBe(true);
  });

  it("resets with email, trimmed code and new password", async () => {
    const props = setup({ initialEmail: "ada@uphill.ai" });
    fireEvent.click(screen.getByRole("button", { name: "Send code" }));
    fireEvent.change(await screen.findByLabelText("6-digit code"), { target: { value: " 012345 " } });
    fireEvent.change(screen.getByLabelText("New password (8+ characters)"), { target: { value: "brandnewpass" } });
    fireEvent.click(screen.getByRole("button", { name: "Reset and sign in" }));
    await waitFor(() => expect(props.onReset).toHaveBeenCalledWith("ada@uphill.ai", "012345", "brandnewpass"));
  });

  it("shows a translated error when the code is rejected", async () => {
    setup({ initialEmail: "ada@uphill.ai", onReset: vi.fn().mockRejectedValue(new Error("Invalid or expired code.")) });
    fireEvent.click(screen.getByRole("button", { name: "Send code" }));
    fireEvent.change(await screen.findByLabelText("6-digit code"), { target: { value: "000000" } });
    fireEvent.change(screen.getByLabelText("New password (8+ characters)"), { target: { value: "brandnewpass" } });
    fireEvent.click(screen.getByRole("button", { name: "Reset and sign in" }));
    expect(await screen.findByText("That code is wrong or has expired. Request a new one.")).toBeDefined();
  });

  it("shows a send error and stays on the email step", async () => {
    setup({ initialEmail: "ada@uphill.ai", onRequestCode: vi.fn().mockRejectedValue(new Error("offline")) });
    fireEvent.click(screen.getByRole("button", { name: "Send code" }));
    expect(await screen.findByText("Couldn't send the code. Check your connection and try again.")).toBeDefined();
    expect(screen.queryByLabelText("6-digit code")).toBeNull();
  });

  it("renders Vietnamese copy and goes back", () => {
    const props = setup({ lang: "vi" });
    expect(screen.getByRole("button", { name: "Gửi mã" })).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "Quay lại đăng nhập" }));
    expect(props.onBack).toHaveBeenCalled();
  });
});
