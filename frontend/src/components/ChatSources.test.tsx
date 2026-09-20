import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import ChatSources from "./ChatSources";

describe("ChatSources", () => {
  it("renders null when isOpen is false", () => {
    const { container } = render(
      <ChatSources
        isOpen={false}
        onClose={vi.fn()}
        sources={null}
        lang="en"
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders empty citations notice when sources has no items", () => {
    render(
      <ChatSources
        isOpen={true}
        onClose={vi.fn()}
        sources={{ message_id: 10, citations: [], evidence: [] }}
        lang="en"
      />
    );

    expect(screen.getByText("Evidence & Citations")).toBeDefined();
    expect(screen.getByText("Message #10")).toBeDefined();
    expect(
      screen.getByText("No external citations recorded for this response.")
    ).toBeDefined();
  });

  it("renders Vietnamese empty notice when lang is vi", () => {
    render(
      <ChatSources
        isOpen={true}
        onClose={vi.fn()}
        sources={{ message_id: 10, citations: [], evidence: [] }}
        lang="vi"
      />
    );

    expect(screen.getByText("Tài liệu & Trích dẫn")).toBeDefined();
    expect(screen.getByText("Tin nhắn #10")).toBeDefined();
    expect(
      screen.getByText("Không có tài liệu trích dẫn ngoài nào cho câu trả lời này.")
    ).toBeDefined();
  });

  it("renders citations with domain, title, quote, and safe link", () => {
    const sources = {
      message_id: 42,
      citations: [
        {
          source_id: "uphill_kb_scheduler_1",
          title: "Training for the Uphill Athlete - Aerobic Base",
          domain: "scheduler",
          quote: "Zone 2 creates the mitochondrial density needed for ultras.",
          url: "https://uphillathlete.com/aerobic-base",
        },
      ],
      evidence: [
        {
          title: "Aerobic Capacity Fundamentals",
          content: "Long slow distance running builds capillarization in working muscles.",
        },
      ],
    };

    render(
      <ChatSources
        isOpen={true}
        onClose={vi.fn()}
        sources={sources}
        lang="en"
      />
    );

    expect(screen.getByText("scheduler")).toBeDefined();
    expect(screen.getByText("Training for the Uphill Athlete - Aerobic Base")).toBeDefined();
    expect(screen.getByText(/Zone 2 creates the mitochondrial density/)).toBeDefined();
    expect(screen.getByText("Aerobic Capacity Fundamentals")).toBeDefined();

    const link = screen.getByRole("link", { name: /View original source/i });
    expect(link.getAttribute("href")).toBe("https://uphillathlete.com/aerobic-base");
    expect(link.getAttribute("target")).toBe("_blank");
    expect(link.getAttribute("rel")).toBe("noopener noreferrer");
  });

  it("calls onClose when close button or Escape key is pressed", () => {
    const onClose = vi.fn();
    render(
      <ChatSources
        isOpen={true}
        onClose={onClose}
        sources={{ message_id: 1, citations: [], evidence: [] }}
        lang="en"
      />
    );

    const closeBtn = screen.getByRole("button", { name: /Close/i });
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalledTimes(1);

    fireEvent.keyDown(window, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(2);
  });
});
