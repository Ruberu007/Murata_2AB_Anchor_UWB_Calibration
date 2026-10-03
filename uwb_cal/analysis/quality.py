import numpy as np
import pandas as pd


def balance(frame, settings):
    ratio = frame.stsPower.mean() / frame.sts2Power.mean() if frame.sts2Power.mean() > 0 else None
    magnitude = max(ratio, 1 / ratio) if ratio is not None and ratio > 0 else None
    status = "UNKNOWN" if magnitude is None else "LARGE IMBALANCE" if magnitude >= settings["imbalance_large"] else "NOTICEABLE IMBALANCE" if magnitude >= settings["imbalance_notice"] else "NORMAL"
    return dict(status=status, mean_power_ratio=ratio, note="Raw power diagnostics are NOT dBm. Thresholds are project-specific.")


def movement(frame, settings):
    events = []
    tests = [("phase wrap", "pdoa_deg", 180), ("PDoA jump", "pdoa_unwrapped", settings["phase_jump_deg"]), ("distance jump", "measured_distance_m", settings["range_jump_m"]), ("STS1 first-path jump", "stsFpIndex", settings["fp_jump"]), ("STS2 first-path jump", "sts2FpIndex", settings["fp_jump"])]
    for label, field, threshold in tests:
        for index in frame.index[frame[field].diff().abs() > threshold]:
            events.append(dict(sample=int(index), event=label))
    t = frame.tdoa_signed
    mad = (t - t.median()).abs().median()
    for index in frame.index[(t - t.median()).abs() > max(3.5 * 1.4826 * mad, settings["tdoa_sd_limit"])]:
        events.append(dict(sample=int(index), event="TDoA spike"))
    ratio = frame.sts_power_ratio
    for index in frame.index[(ratio >= settings["imbalance_large"]) | (ratio <= 1 / settings["imbalance_large"])]:
        events.append(dict(sample=int(index), event="large STS power imbalance"))
    available = any(frame[c].notna().sum() >= 2 for c in ["pdoa_deg", "tdoa_signed", "measured_distance_m"])
    unstable = any(e["event"] != "phase wrap" for e in events)
    conclusion = "Insufficient moving-tag measurements." if not available else "Raw diagnostic discontinuities detected; inspect RF conditions and acquisition timing. This does not establish a hardware fault." if unstable else "Available raw diagnostics are relatively smooth at configured thresholds. Inspect AoA mapping, coordinate transforms and visualization; this is evidence, not certainty."
    return dict(events=events, conclusion=conclusion)


def compare(frame):
    rows = []
    metrics = ["pdoa_unwrapped", "tdoa_signed", "stsPower", "sts2Power", "sts_power_ratio", "fp_difference", "xtalOffset"]
    # Match kind, angle and distance: pooled mismatched operating points are misleading.
    for key, group in frame.groupby(["kind", "true_angle_deg", "true_distance_m"], dropna=False):
        reference = group[group.label == "EVB-EVB"]
        custom = group[group.label == "EVB-CUSTOM"]
        if reference.empty or custom.empty:
            continue
        for metric in metrics:
            a, b = reference[metric].dropna(), custom[metric].dropna()
            if a.empty or b.empty:
                continue
            rows.append(dict(kind=key[0], angle_deg=None if pd.isna(key[1]) else key[1], distance_m=None if pd.isna(key[2]) else key[2], parameter=metric, evb_mean=float(a.mean()), custom_mean=float(b.mean()), absolute_difference=float(abs(b.mean() - a.mean())), ratio=float(b.mean() / a.mean()) if a.mean() != 0 and metric in ["stsPower", "sts2Power", "sts_power_ratio"] else None, evb_sd=float(a.std()) if len(a)>1 else None, custom_sd=float(b.std()) if len(b)>1 else None))
    return rows
