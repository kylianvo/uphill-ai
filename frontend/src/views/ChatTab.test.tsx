import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import ChatTab from "./ChatTab";
import * as useCoachChatModule from "../hooks/useCoachChat";
import { AppProvider, AppContext } from "../contexts/AppContext";

vi.mock("../hooks/useCoachChat");

describe("ChatTab", () => {
  const mockSend = vi.fn();
  const mockRetry = vi.fn();
  const mockClear = vi.fn();
  const mockLoadOlder = vi.fn();
  const mockFetchMessageSources = vi.fn();
  const mockClearMessageSources = vi.fn();
  const mockSetPaceHandoff = vi.fn();
  const mockSetIsPaceStrategyOpen = vi.fn();
  const mockHandleTabSwitch = vi.fn();

  const defaultHookReturn: useCoachChatModule.UseCoachChatReturn = {
    messages: [],
    activeRequest: null,
    status: "idle",
    error: null,
    hasMore: false,
    isLoadingOlder: false,
    send: mockSend,
    retry: mockRetry,
    clear: mockClear,
    loadOlder: mockLoadOlder,
    refreshTurn: vi.fn(),
    selectedMessageSources: null,
    fetchMessageSources: mockFetchMessageSources,
    clearMessageSources: mockClearMessageSources,
    clarifyOptions: null,
    dismissClarify: vi.fn(),
    proposalStates: {},
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useCoachChatModule.useCoachChat).mockReturnValue(defaultHookReturn);
  });

  interface TestContextValue {
    lang?: string;
    setPaceHandoff?: ReturnType<typeof vi.fn>;
    setIsPaceStrategyOpen?: ReturnType<typeof vi.fn>;
    handleTabSwitch?: ReturnType<typeof vi.fn>;
    [key: string]: unknown;
  }

  const renderWithContext = (ui: React.ReactElement, contextOverrides?: TestContextValue) => {
    if (contextOverrides) {
      // Render with context overrides by wrapping with a context provider that supplies the mocked values
      const contextValue: TestContextValue = {
        lang: "en",
        setPaceHandoff: mockSetPaceHandoff,
        setIsPaceStrategyOpen: mockSetIsPaceStrategyOpen,
        handleTabSwitch: mockHandleTabSwitch,
        ...contextOverrides,
      };
      return render(
        <AppContext.Provider value={contextValue as unknown as React.ContextType<typeof AppContext>}>
          {ui}
        </AppContext.Provider>
      );
    }
    return render(<AppProvider>{ui}</AppProvider>);
  };

  it("renders honest empty state with capabilities and boundary notice, without tools or apply buttons", () => {
    renderWithContext(<ChatTab isMobile={false} />);

    expect(screen.getByText("Coach Uphill AI")).toBeDefined();
    expect(screen.getByText(/Ask questions about training principles/i)).toBeDefined();
    expect(screen.getByText(/Explain 80\/20 intensity distribution/i)).toBeDefined();
    expect(screen.getByText(/Zone 2 aerobic base principles/i)).toBeDefined();
    expect(screen.getByText(/Muscular Endurance \(ME\) workouts/i)).toBeDefined();
    expect(
      screen.getByText(/Coach chat answers questions and explains principles\. It will not modify/i)
    ).toBeDefined();

    // Invariant: No write tools, Apply buttons, or fabricated tool cards
    expect(screen.queryByText(/Apply/i)).toBeNull();
    expect(screen.queryByText(/Modify plan/i)).toBeNull();
  });

  it("displays retrieving and generating status labels", () => {
    vi.mocked(useCoachChatModule.useCoachChat).mockReturnValue({
      ...defaultHookReturn,
      status: "retrieving",
      messages: [{ role: "user", content: "Explain Zone 2" }],
    });

    renderWithContext(<ChatTab isMobile={false} />);
    expect(screen.getAllByText(/Retrieving training principles\.\.\./i).length).toBeGreaterThan(0);
  });

  it("renders interrupted badge and explicit Retry button on interrupted partial message", () => {
    vi.mocked(useCoachChatModule.useCoachChat).mockReturnValue({
      ...defaultHookReturn,
      status: "interrupted",
      messages: [
        { role: "user", content: "Tell me about nutrition" },
        {
          role: "assistant",
          content: "You should eat 60g carbs per hour during...",
          interrupted: true,
          request_id: "turn-uuid-1",
        },
      ],
    });

    renderWithContext(<ChatTab isMobile={false} />);

    expect(screen.getByText(/You should eat 60g carbs/i)).toBeDefined();
    expect(screen.getByText("Interrupted")).toBeDefined();

    const retryBtn = screen.getByRole("button", { name: "Retry" });
    expect(retryBtn).toBeDefined();

    fireEvent.click(retryBtn);
    expect(mockRetry).toHaveBeenCalledWith("turn-uuid-1");
  });

  it("displays localized error for daily turn quota exceeded (429)", () => {
    vi.mocked(useCoachChatModule.useCoachChat).mockReturnValue({
      ...defaultHookReturn,
      error: { code: "coach_turn_quota_exceeded" },
    });

    renderWithContext(<ChatTab isMobile={false} />);
    expect(
      screen.getByText(/Daily chat limit reached \(50 turns\)\. Please try again tomorrow\./i)
    ).toBeDefined();
  });

  it("displays localized error for clear conflict during active turn (409)", () => {
    vi.mocked(useCoachChatModule.useCoachChat).mockReturnValue({
      ...defaultHookReturn,
      error: { code: "chat_in_progress" },
    });

    renderWithContext(<ChatTab isMobile={false} />);
    expect(
      screen.getByText(/Cannot clear chat while Coach is replying\./i)
    ).toBeDefined();
  });

  it("renders Sources button and calls fetchMessageSources when clicked", () => {
    vi.mocked(useCoachChatModule.useCoachChat).mockReturnValue({
      ...defaultHookReturn,
      messages: [
        {
          id: 42,
          role: "assistant",
          content: "Zone 2 running builds capillary density.",
          citations: [{ source_id: "kb-1", title: "Manual" }],
        },
      ],
    });

    renderWithContext(<ChatTab isMobile={false} />);

    const sourcesBtn = screen.getByRole("button", { name: /Sources \(1\)/i });
    expect(sourcesBtn).toBeDefined();

    fireEvent.click(sourcesBtn);
    expect(mockFetchMessageSources).toHaveBeenCalledWith(42);
  });

  it("renders load older button when hasMore is true", () => {
    vi.mocked(useCoachChatModule.useCoachChat).mockReturnValue({
      ...defaultHookReturn,
      hasMore: true,
      messages: [{ id: 5, role: "user", content: "Hi" }],
    });

    renderWithContext(<ChatTab isMobile={false} />);

    const loadOlderBtn = screen.getByRole("button", { name: /Load older messages/i });
    expect(loadOlderBtn).toBeDefined();

    fireEvent.click(loadOlderBtn);
    expect(mockLoadOlder).toHaveBeenCalledTimes(1);
  });

  it("triggers send with user input when clicking send button", () => {
    renderWithContext(<ChatTab isMobile={false} />);

    const input = screen.getByPlaceholderText("Ask your AI coach...");
    fireEvent.change(input, { target: { value: "How do I build aerobic capacity?" } });

    const sendBtn = screen.getByRole("button", { name: "" }); // icon button
    fireEvent.click(sendBtn);

    expect(mockSend).toHaveBeenCalledWith("How do I build aerobic capacity?");
  });

  it("renders a RichCardRenderer card when an assistant message has toolCalls", () => {
    vi.mocked(useCoachChatModule.useCoachChat).mockReturnValue({
      ...defaultHookReturn,
      messages: [
        {
          role: "assistant",
          content: "Here's week 4.",
          toolCalls: [
            {
              type: "tool_result",
              tool_call_id: "call_1",
              name: "get_week",
              status: "success",
              card_type: "week_schedule",
              card_data: {
                week_number: 4,
                total_distance_km: 48.5,
                total_elevation_gain_m: 1650,
                plan_start_date: "2026-08-31",
                race_date: "2026-11-01",
                workouts: [],
              },
            },
          ],
        },
      ],
    });
    renderWithContext(<ChatTab isMobile={false} />);
    expect(screen.getByText(/Week 4/)).toBeDefined();
  });

  it("clicking Open in Pace Strategy sets paceHandoff and switches to the tools tab", () => {
    vi.mocked(useCoachChatModule.useCoachChat).mockReturnValue({
      ...defaultHookReturn,
      messages: [
        {
          role: "assistant",
          content: "Here's your pacing plan.",
          toolCalls: [
            {
              type: "tool_result",
              tool_call_id: "call_2",
              name: "pace_strategy",
              status: "success",
              card_type: "pacing_splits",
              card_data: {
                race_name: "Dalat Ultra Trail 70K",
                distance_label: "70K",
                total_distance_km: 71.2,
                total_elevation_m: 3150.0,
                target_time_formatted: "12h 45m",
                splits: [],
              },
            },
          ],
        },
      ],
    });

    renderWithContext(<ChatTab isMobile={false} />, {
      setPaceHandoff: mockSetPaceHandoff,
      setIsPaceStrategyOpen: mockSetIsPaceStrategyOpen,
      handleTabSwitch: mockHandleTabSwitch,
    });

    fireEvent.click(screen.getByText("Open in Pace Strategy"));

    expect(mockSetPaceHandoff).toHaveBeenCalledWith(
      expect.objectContaining({ race_name: "Dalat Ultra Trail 70K" })
    );
    expect(mockSetIsPaceStrategyOpen).toHaveBeenCalledWith(true);
    expect(mockHandleTabSwitch).toHaveBeenCalledWith("tools");
  });

  it("shows clarification chips and sends the selected option on click", () => {
    const dismissClarify = vi.fn();

    vi.mocked(useCoachChatModule.useCoachChat).mockReturnValue({
      ...defaultHookReturn,
      clarifyOptions: ["Dalat Ultra Trail", "VMM"],
      dismissClarify,
      send: mockSend,
    });
    renderWithContext(<ChatTab isMobile={false} />);
    fireEvent.click(screen.getByText("Dalat Ultra Trail"));
    expect(mockSend).toHaveBeenCalledWith("Dalat Ultra Trail");
    expect(dismissClarify).toHaveBeenCalled();
  });

  it("shows context-aware starter chips built from the active plan when there are no messages", () => {
    renderWithContext(<ChatTab isMobile={false} />, {
      activePlan: { race_name: "Dalat Ultra Trail 70K", current_week: 4 },
    });
    expect(screen.getByText(/Week 4/)).toBeDefined();
    expect(screen.getByText(/Dalat Ultra Trail 70K/)).toBeDefined();
  });

  it("localizes plan-aware starter chips to Vietnamese instead of the English template", () => {
    renderWithContext(<ChatTab isMobile={false} />, {
      lang: "vi",
      activePlan: { race_name: "Dalat Ultra Trail 70K", current_week: 4 },
    });
    expect(screen.getByText(/Tuần 4/)).toBeDefined();
    expect(screen.getByText(/Dalat Ultra Trail 70K/)).toBeDefined();
    expect(screen.queryByText(/What are my key workouts/i)).toBeNull();
    expect(screen.queryByText(/Calculate a conservative pacing plan/i)).toBeNull();
  });

  it("falls back to the static chip for that slot instead of 'Week undefined' when current_week is missing", () => {
    renderWithContext(<ChatTab isMobile={false} />, {
      activePlan: { race_name: "Dalat Ultra Trail 70K", current_week: undefined },
    });
    expect(screen.queryByText(/Week undefined/)).toBeNull();
    expect(screen.getByText("Explain 80/20 intensity distribution")).toBeDefined();
  });
});
