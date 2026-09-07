"use client";

/**
 * Attribution for COROS-sourced data.
 *
 * Required by COROS API Agreement 14.5: wherever COROS data or data derived
 * from it is displayed, we must show an attribution naming COROS AND the
 * specific device model, no less prominent than any other source. Failure is
 * defined as a material breach, so this is not a decorative component.
 *
 * `deviceModel` is nullable because the backend cannot always resolve it
 * (e.g. `queryDevices` returned an unrecognised shape). When that happens we
 * still attribute COROS by name -- we never invent a device name.
 */
export default function CorosAttribution({
  deviceModel,
  provider = "coros",
}: {
  deviceModel: string | null;
  provider?: string;
}) {
  if (provider !== "coros") return null;
  return (
    <span className="device-attribution">
      {deviceModel ? `Data provided by COROS · ${deviceModel}` : "Data provided by COROS"}
    </span>
  );
}
