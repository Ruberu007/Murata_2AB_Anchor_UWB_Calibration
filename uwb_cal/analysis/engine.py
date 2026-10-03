import numpy as np
import pandas as pd
from uwb_cal.parsers.rf_diag_parser import FIELDS
from .tdoa import decode_signed_tdoa
from .phase import unwrap_phase, align_branch
from .statistics import filter_mask, describe
from .lut import orientation, monotonicity, validate_lut
from .antenna_delay import analyze_range
from .quality import balance, movement, compare


def prepare(project):
    frames, warnings = [], []
    for dataset in project.datasets:
        if not dataset.enabled or not dataset.records:
            continue
        frame = pd.DataFrame(dataset.records)
        for column in FIELDS + ["pdoa_deg", "pdoa_raw", "tdoa_raw", "measured_distance_m"]:
            if column not in frame:
                frame[column] = np.nan
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if "timestamp" not in frame:
            frame["timestamp"] = None
        for key, value in dict(dataset_name=dataset.name, true_angle_deg=dataset.true_angle_deg, true_distance_m=dataset.true_distance_m, label=dataset.label, kind=dataset.kind).items():
            frame[key] = value
        signed = []
        for raw in frame.tdoa_raw:
            try:
                signed.append(decode_signed_tdoa(raw, int(project.settings["tdoa_bits"])) if pd.notna(raw) else np.nan)
            except ValueError as error:
                warnings.append(f"{dataset.name}: {error}")
                signed.append(np.nan)
        frame["tdoa_signed"] = signed
        if any(pd.notna(r) and r >= 2 ** (int(project.settings["tdoa_bits"]) - 1) for r in frame.tdoa_raw):
            warnings.append(f"{dataset.name}: Some TDoA values appear to be wrapped. Signed conversion has been applied.")
        frame["pdoa_unwrapped"] = unwrap_phase(frame.pdoa_deg)
        field = "measured_distance_m" if dataset.kind == "distance" else "pdoa_unwrapped"
        frame["valid"] = filter_mask(frame[field], project.settings["filter"], project.settings["threshold"])
        frame["rejection_reason"] = np.where(frame.valid, "", np.where(frame[field].isna(), "missing calibration value", "outlier"))
        frame["sts_power_ratio"] = frame.stsPower / frame.sts2Power.where(frame.sts2Power != 0)
        frame["sts_power_difference"] = frame.stsPower - frame.sts2Power
        frame["fp_difference"] = frame.sts2FpIndex - frame.stsFpIndex
        frame["rx_time_difference"] = frame.sts2RxTime - frame.stsRxTime
        frame["range_error_m"] = frame.measured_distance_m - (float(dataset.true_distance_m) if dataset.true_distance_m is not None else np.nan)
        frame["sample"] = np.arange(len(frame))
        timestamps = pd.to_datetime(frame.timestamp, utc=True, errors="coerce")
        frame["elapsed_s"] = (timestamps - timestamps.dropna().iloc[0]).dt.total_seconds() if timestamps.notna().any() else frame["sample"]
        warnings.extend(dataset.warnings)
        frames.append(frame)
    if not frames:
        raise ValueError("Import or enable at least one dataset.")
    return pd.concat(frames, ignore_index=True), list(dict.fromkeys(warnings))


def analyze(project):
    frame, warnings = prepare(project)
    s = project.settings
    result = dict(warnings=warnings, statistics=[], angle_points=[], lut=[], readiness={}, comparison=[], movements={})
    frame["pdoa_corrected"] = np.nan
    fixed = frame[(frame.kind == "angle") & (frame.label == "EVB-CUSTOM") & frame.true_angle_deg.notna()]
    low, high = project.sweep['calibration_min'], project.sweep['calibration_max']
    fixed = fixed[fixed.true_angle_deg.between(low, high)]
    result['calibration_sector_deg'] = [low, high]
    from .sweep import sweep_status
    result['angle_capture_checklist'] = sweep_status(project)
    sweep_active = any(d.source_text and d.kind == 'angle' for d in project.datasets)
    if sweep_active:
        missing_sector = [r['angle_deg'] for r in result['angle_capture_checklist'] if low <= r['angle_deg'] <= high and r['status'] == 'MISSING']
        if missing_sector:
            warnings.append('Missing planned calibration-sector angles: ' + ', '.join(map(str, missing_sector)) + '. Results are partial.')
    else:
        missing_sector = []
    if any(frame[frame.kind == 'angle'].true_angle_deg.abs() > 90):
        warnings.append('Wide-angle sweep retained for diagnostics. Two-antenna phase alone may have front/back ambiguity; do not assume a unique -180 to +180 degree AoA lookup.')
    good = fixed[fixed.valid]
    zero = good[good.true_angle_deg == 0]
    if zero.empty:
        warnings.append("At least one 0-degree calibration dataset is required.")
        result["zero_pdoa_offset_deg"] = None
    else:
        centers = zero.groupby("dataset_name").pdoa_unwrapped.median()
        anchor = float(centers.iloc[0])
        aligned = [align_branch(g.pdoa_unwrapped.to_numpy(), anchor) for _, g in zero.groupby("dataset_name")]
        offset = float(np.median(np.concatenate(aligned)))
        result["zero_pdoa_offset_deg"] = offset
        result["suggested_pdoa_correction_deg"] = -offset
        # Align each stationary dataset, then unwrap the median trajectory in angle order.
        centers = good.groupby("true_angle_deg").pdoa_unwrapped.apply(lambda x: float(np.median(align_branch(x.to_numpy(), offset)))).sort_index()
        trajectory = unwrap_phase(centers.to_numpy())
        zero_index = list(centers.index).index(0)
        trajectory += 360 * round((offset - trajectory[zero_index]) / 360)
        for angle, target in zip(centers.index, trajectory):
            indices = fixed.index[fixed.true_angle_deg == angle]
            for _, group in frame.loc[indices].groupby("dataset_name"):
                vals = align_branch(group.pdoa_unwrapped.to_numpy(), target)
                frame.loc[group.index, "pdoa_corrected"] = vals - offset
            values = frame.loc[indices]
            accepted = values[values.valid]
            result["angle_points"].append(dict(angle_deg=float(angle), pdoa_deg=float(accepted.pdoa_corrected.median()), phase_sd=describe(accepted.pdoa_corrected)["sd"], tdoa_mean=describe(accepted.tdoa_signed)["mean"], tdoa_sd=describe(accepted.tdoa_signed)["sd"]))
    for name, group in frame.groupby("dataset_name"):
        accepted = group[group.valid]
        metrics = ["pdoa_unwrapped", "pdoa_corrected", "tdoa_signed", "stsPower", "sts2Power", "stsFpIndex", "sts2FpIndex", "stsF1", "stsF2", "stsF3", "sts2F1", "sts2F2", "sts2F3", "sts_power_ratio", "sts_power_difference", "fp_difference", "rx_time_difference", "xtalOffset"]
        result["statistics"].append(dict(dataset=name, total=len(group), valid=len(accepted), rejected=len(group)-len(accepted), raw_metrics={c: describe(group[c]) for c in ["pdoa_unwrapped", "tdoa_signed", "measured_distance_m"]}, metrics={c: describe(accepted[c]) for c in metrics}, rf_balance=balance(accepted, s)))
    points = result["angle_points"]
    if len(points) >= 3:
        a = np.array([p["angle_deg"] for p in points])
        p = np.array([p["pdoa_deg"] for p in points])
        result.update(orientation(a, p, s["reference_sign"]))
        monotone = monotonicity(a, p, s["small_reversal_deg"])
        result["monotonicity"] = monotone
        if monotone != "FAIL" and (s["interpolation"] != "pchip" or monotone == "PASS"):
            sign = -1 if result["orientation"] == "reversed" else 1
            result["pdoa_sign"] = sign
            oriented = p * sign
            result["lut"] = [dict(pdoa_deg=float(oriented[i]), aoa_deg=float(a[i])) for i in np.argsort(oriented)]
            try:
                result["validation"] = validate_lut(oriented, a, s["interpolation"])
            except ValueError as error:
                warnings.append(str(error))
        else:
            warnings.append("PDoA data is strongly non-monotonic or unsuitable for PCHIP. LUT generation is not recommended.")
    else:
        result.update(monotonicity="INSUFFICIENT", orientation="unknown")
    range_frame = frame[(frame.kind == "distance") & (frame.label == "EVB-CUSTOM") & frame.valid]
    try:
        result["range"] = analyze_range(range_frame)
    except ValueError as error:
        warnings.append(str(error))
    result["comparison"] = compare(frame[frame.valid])
    for name, group in frame[frame.kind == "movement"].groupby("dataset_name"):
        result["movements"][name] = movement(group.reset_index(drop=True), s)
    fixed_stats = [r for r in result["statistics"] if r["dataset"] in fixed.dataset_name.unique()]
    sample_ok = bool(fixed_stats) and all(r["valid"] >= s["minimum_samples"] for r in fixed_stats)
    stable = bool(points) and all(p["phase_sd"] is not None and p["phase_sd"] <= s["phase_sd_limit"] for p in points)
    tdoa_ok = bool(points) and all(p["tdoa_sd"] is not None and p["tdoa_sd"] <= s["tdoa_sd_limit"] for p in points)
    raw_stable = bool(fixed_stats) and all(r["raw_metrics"]["pdoa_unwrapped"]["sd"] is not None and r["raw_metrics"]["pdoa_unwrapped"]["sd"] <= s["phase_sd_limit"] for r in fixed_stats)
    raw_tdoa_stable = bool(fixed_stats) and all(r["raw_metrics"]["tdoa_signed"]["sd"] is not None and r["raw_metrics"]["tdoa_signed"]["sd"] <= s["tdoa_sd_limit"] for r in fixed_stats)
    if not raw_stable:
        warnings.append("Raw fixed-position PDoA is unstable or insufficient at project thresholds. Review raw measurements before using a LUT; filtering cannot establish RF stability.")
    if not raw_tdoa_stable:
        warnings.append("Raw fixed-position TDoA is unstable or insufficient at project thresholds.")
    zero_sd = describe(zero.pdoa_unwrapped)["sd"] if not zero.empty else None
    validation = result.get("validation", {})
    ready = bool(result["lut"]) and result["monotonicity"] == "PASS" and sample_ok and stable and raw_stable and tdoa_ok and raw_tdoa_stable and validation.get("mae", float("inf")) <= s["mae_limit"] and validation.get("max_error", float("inf")) <= s["max_error_limit"]
    result["production_ready"] = ready
    if missing_sector:
        result['production_ready'] = ready = False
    if high - low > 180:
        warnings.append('Selected LUT sector exceeds 180 degrees. Full-circle AoA uniqueness has not been established; no deployable LUT is emitted. Select a validated narrower sector.')
        result['lut'] = []
        result['production_ready'] = ready = False
    range_result = result.get("range")
    manual_range = any(d.kind == "distance" and d.enabled and any("manually assigned" in w for w in d.warnings) for d in project.datasets)
    range_stable = bool(range_result) and not manual_range and all(r["sd_m"] is not None and r["sd_m"] <= s["range_sd_limit_m"] for r in range_result["by_distance"])
    result["readiness"] = {"Parser": "WARNING" if warnings else "PASS", "Sample count": "PASS" if sample_ok else "WARNING", "0-degree stability": "PASS" if zero_sd is not None and zero_sd <= s["phase_sd_limit"] else "WARNING", "PDoA phase unwrap": "REVIEW (adjacent changes assumed <180 degrees)", "PDoA monotonicity": result["monotonicity"], "ANT1/ANT2 orientation": result["orientation"].upper(), "TDoA stability": "PASS" if tdoa_ok else "WARNING", "RF path power balance": "WARNING" if any(r["rf_balance"]["status"] != "NORMAL" for r in fixed_stats) else "PASS", "Distance offset stability": "PASS" if range_stable else "WARNING", "AoA LUT generation": "READY (project criteria)" if ready else "NOT RECOMMENDED", "External antenna-delay calc": "READY (physical quantity only)" if range_stable else "REVIEW / INSUFFICIENT"}
    result["engineering_notes"] = ["CUSTOM PCB EXTERNAL PDOA OFFSET; not a final Murata parameter.", "LUT input = CUSTOM_PDOA_SIGN * (unwrapped PDoA - zero offset). Preserve the calibrated branch; do not extrapolate in deployment.", "Reversed orientation: consider swapping logical ANT1/ANT2 or inverting the coordinate-transform PDoA sign; no firmware settings were changed.", "Raw power values are diagnostics, NOT dBm.", "All acceptance thresholds are PROJECT-SPECIFIC DEFAULTS, not Murata specifications.", "Unwrapping cannot resolve undersampled motion or phase changes exceeding 180 degrees per sample/angle step.", "Inspect RF/antenna hardware and acquisition conditions when fixed-position data is unstable. Statistics alone do not establish a hardware fault."]
    project.results = result
    return frame, result
