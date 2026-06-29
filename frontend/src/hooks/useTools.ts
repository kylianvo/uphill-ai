/* eslint-disable @typescript-eslint/no-explicit-any */
import { useRef } from "react";
import { useAppContext } from "../contexts/AppContext";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useTools() {
  const ctx = useAppContext();
  const { setParserLoading, setUploadedFileName, setParserErrorMsg, setParsedSummary, setGpxCheckpoints, setPacedCheckpoints, gpxCheckpoints, setPacingLoading, targetFlatPace } = ctx;
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDropzoneClick = () => {
    fileInputRef.current?.click();
  };
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await processFile(file);
  };
  const processFile = async (file: File) => {
    setParserLoading(true);
    setUploadedFileName(file.name);
    setParserErrorMsg("");
    setParsedSummary(null);
    setGpxCheckpoints([]);
    setPacedCheckpoints([]);

    const formData = new FormData();
    formData.append("file", file);

    const extension = file.name.split(".").pop()?.toLowerCase();
    let url = "";

    if (extension === "fit") {
      url = `${API_BASE_URL}/api/parser/fit`;
    } else if (extension === "gpx") {
      url = `${API_BASE_URL}/api/parser/gpx`;
    } else {
      setParserErrorMsg("Unsupported file format. Please upload a .fit or .gpx file.");
      setParserLoading(false);
      return;
    }

    try {
      const response = await fetch(url, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || "Parsing failed on server");
      }

      const result = await response.json();
      const sum = result.summary;

      if (extension === "fit") {
        const fitDist = parseFloat(((sum.total_distance_meters || 0) / 1000).toFixed(2));
        const fitElev = Math.round(sum.total_elevation_gain_meters || 0);
        setParsedSummary({
          distance_km: fitDist,
          duration_mins: parseFloat(((sum.total_duration_seconds || 0) / 60).toFixed(1)),
          elevation_gain_m: fitElev,
          avg_hr: sum.avg_heart_rate ? Math.round(sum.avg_heart_rate) : undefined,
          avg_speed: sum.avg_speed_mps ? `${(16.6667 / sum.avg_speed_mps).toFixed(2)} min/km` : undefined,
          source_type: "FIT",
        });
      } else {
        const gpxDist = parseFloat(((sum.total_distance_meters || 0) / 1000).toFixed(2));
        const gpxElev = Math.round(sum.total_elevation_gain_meters || 0);
        setParsedSummary({
          distance_km: gpxDist,
          duration_mins: 0,
          elevation_gain_m: gpxElev,
          source_type: "GPX",
        });
        setGpxCheckpoints(result.checkpoints);
      }
    } catch (err: any) {
      setParserErrorMsg(err.message || "An error occurred while uploading/parsing.");
    } finally {
      setParserLoading(false);
    }
  };


  const handleCalculatePacing = async () => {
    if (gpxCheckpoints.length === 0) return;
    setPacingLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/coach/calculate-pacing`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          checkpoints: gpxCheckpoints,
          target_flat_pace_min_km: parseFloat(targetFlatPace)
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setPacedCheckpoints(result);
      }
    } catch (err) {
      console.error("Failed to calculate pacing:", err);
    } finally {
      setPacingLoading(false);
    }
  };

  return { handleDropzoneClick, handleFileChange, processFile, fileInputRef, handleCalculatePacing };
}
