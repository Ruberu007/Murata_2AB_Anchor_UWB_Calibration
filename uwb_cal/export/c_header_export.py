from pathlib import Path


def export_c_header(result, path):
    if not result.get("lut"):
        raise ValueError("No LUT available; a firmware header cannot be generated.")
    lines = ["#ifndef CUSTOM_UWB_CALIBRATION_H", "#define CUSTOM_UWB_CALIBRATION_H", "/* CUSTOM PCB EXTERNAL CORRECTIONS. No OTP/register writes.", " * Raw powers are NOT dBm. Firmware unit conversion still required.", " * Apply: phase = SIGN * (unwrapped_pdoa - ZERO_OFFSET); then lookup.", " * Keep calibrated phase branch. Do not extrapolate beyond LUT domain.", " * Range correction: measured_distance - EXTERNAL_RANGE_BIAS.", " * Combine external corrections with module factory calibration as documented.", f" * Project readiness: {'READY' if result.get('production_ready') else 'NOT RECOMMENDED / ENGINEERING REVIEW ONLY'}", " */", f"#define CUSTOM_LUT_PRODUCTION_READY {int(bool(result.get('production_ready')))}", f"#define CUSTOM_PDOA_ZERO_OFFSET_DEG ({result['zero_pdoa_offset_deg']:.9f}f)", f"#define CUSTOM_PDOA_SIGN ({result.get('pdoa_sign', 1)})"]
    if "range" in result:
        lines += [f"#define CUSTOM_EXTERNAL_RANGE_BIAS_M ({result['range']['bias_m']:.9f}f)", f"#define CUSTOM_EXTERNAL_DELAY_PS ({result['range']['delay_ps']:.9f}f)"]
    else:
        lines.append("/* Range calibration unavailable; no range constant emitted. */")
    lines += ["typedef struct { float pdoa_deg; float aoa_deg; } uwb_aoa_lut_t;", "static const uwb_aoa_lut_t custom_anchor_lut[] = {"]
    lines += [f"    {{{p['pdoa_deg']:.9f}f, {p['aoa_deg']:.9f}f}}," for p in result["lut"]]
    lines += ["};", f"#define CUSTOM_ANCHOR_LUT_COUNT {len(result['lut'])}", "#endif", ""]
    Path(path).write_text("\n".join(lines), encoding="utf-8")
