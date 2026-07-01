import { describe, it, expect, vi, beforeEach } from "vitest";
import { act } from "@testing-library/react";
import { renderHookWithApp } from "../test-utils/renderWithAppContext";
import { useAppContext } from "../contexts/AppContext";
import { useTools } from "./useTools";

function jsonResponse(body: unknown, ok = true) {
  return { ok, json: async () => body, text: async () => JSON.stringify(body) } as Response;
}

function makeFile(name: string) {
  return new File(["dummy content"], name);
}

describe("useTools.processFile", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  it("routes .fit files to /api/parser/fit and computes distance/elevation", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        summary: {
          total_distance_meters: 10000,
          total_duration_seconds: 3600,
          total_elevation_gain_meters: 250,
          avg_heart_rate: 145,
        },
      })
    );

    const { result } = renderHookWithApp(() => {
      const ctx = useAppContext();
      const tools = useTools();
      return { ctx, tools };
    });

    await act(async () => {
      await result.current.tools.processFile(makeFile("morning-run.fit"));
    });

    expect(fetchMock.mock.calls[0][0]).toContain("/api/parser/fit");
    expect(result.current.ctx.parsedSummary).toMatchObject({
      distance_km: 10,
      duration_mins: 60,
      elevation_gain_m: 250,
      avg_hr: 145,
      source_type: "FIT",
    });
  });

  it("routes .gpx files to /api/parser/gpx and stores checkpoints", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        summary: { total_distance_meters: 5000, total_elevation_gain_meters: 100 },
        checkpoints: [{ name: "KM 1.0" }],
      })
    );

    const { result } = renderHookWithApp(() => {
      const ctx = useAppContext();
      const tools = useTools();
      return { ctx, tools };
    });

    await act(async () => {
      await result.current.tools.processFile(makeFile("route.gpx"));
    });

    expect(fetchMock.mock.calls[0][0]).toContain("/api/parser/gpx");
    expect(result.current.ctx.parsedSummary?.source_type).toBe("GPX");
    expect(result.current.ctx.gpxCheckpoints).toEqual([{ name: "KM 1.0" }]);
  });

  it("rejects unsupported file extensions without calling fetch", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;

    const { result } = renderHookWithApp(() => {
      const ctx = useAppContext();
      const tools = useTools();
      return { ctx, tools };
    });

    await act(async () => {
      await result.current.tools.processFile(makeFile("workout.tcx"));
    });

    expect(fetchMock).not.toHaveBeenCalled();
    expect(result.current.ctx.parserErrorMsg).toMatch(/unsupported file format/i);
  });

  it("surfaces the server error text when parsing fails", async () => {
    const fetchMock = fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValueOnce(jsonResponse({}, false));

    const { result } = renderHookWithApp(() => {
      const ctx = useAppContext();
      const tools = useTools();
      return { ctx, tools };
    });

    await act(async () => {
      await result.current.tools.processFile(makeFile("corrupt.fit"));
    });

    expect(result.current.ctx.parserErrorMsg).toBeTruthy();
    expect(result.current.ctx.parsedSummary).toBeNull();
  });
});
