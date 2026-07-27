import { describe, it, expect, vi, beforeEach } from "vitest";
import { act } from "@testing-library/react";
import { renderHookWithApp } from "../test-utils/renderWithAppContext";
import { useCoachNotes } from "./useCoachNotes";

function jsonResponse(body: unknown, ok = true) {
  return { ok, json: async () => body } as Response;
}

describe("useCoachNotes", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    localStorage.setItem("uphill_session_token", "test-token");
  });

  it("fetchNotes populates notes scoped to the target", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse({ notes: [{ id: 1, note: "Great effort." }] }));
    const { result } = renderHookWithApp(() => useCoachNotes(42, "plan", null));

    await act(async () => {
      await result.current.fetchNotes();
    });

    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("target_type=plan"), expect.anything());
    expect(result.current.notes).toHaveLength(1);
  });

  it("addNote posts and refetches", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ id: 2, note: "New note" }))
      .mockResolvedValueOnce(jsonResponse({ notes: [{ id: 2, note: "New note" }] }));
    const { result } = renderHookWithApp(() => useCoachNotes(42, "workout", 7));

    await act(async () => {
      await result.current.addNote("New note");
    });

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      expect.stringContaining("/api/coaching/athletes/42/notes"),
      expect.objectContaining({ method: "POST" })
    );
    expect(result.current.notes).toHaveLength(1);
  });

  it("fetchNotes is a no-op when athleteId is null", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    const { result } = renderHookWithApp(() => useCoachNotes(null, "plan", null));

    await act(async () => {
      await result.current.fetchNotes();
    });

    expect(fetchMock).not.toHaveBeenCalled();
  });
});
