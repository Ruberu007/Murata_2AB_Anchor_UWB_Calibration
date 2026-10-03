import numpy as np
import pandas as pd

SPEED_OF_LIGHT = 299792458.0


def analyze_range(frame):
    data = frame.copy()
    for column in ["true_distance_m", "measured_distance_m"]:
        data[column] = pd.to_numeric(data[column], errors="coerce").astype(float)
    data = data.dropna(subset=["true_distance_m", "measured_distance_m"])
    if data.empty:
        raise ValueError("Measured distance is missing. Antenna-delay calibration cannot be calculated.")
    data["range_error_m"] = data.measured_distance_m - data.true_distance_m
    bias = float(data.range_error_m.mean())
    groups = data.groupby("true_distance_m").agg(measured_mean=("measured_distance_m", "mean"), bias_m=("range_error_m", "mean"), sd_m=("range_error_m", "std"), count=("range_error_m", "count")).reset_index()
    slope, intercept = (np.polyfit(data.true_distance_m, data.measured_distance_m, 1) if data.true_distance_m.nunique() > 1 else (None, None))
    return dict(label="CUSTOM PCB EXTERNAL RANGE / ANTENNA-DELAY CORRECTION", bias_m=bias, correction_m=-bias, bias_mm=bias * 1000, delay_ps=bias / SPEED_OF_LIGHT * 1e12, delay_ns=bias / SPEED_OF_LIGHT * 1e9, slope=float(slope) if slope is not None else None, intercept_m=float(intercept) if intercept is not None else None, by_distance=groups.astype(object).where(groups.notna(), None).to_dict("records"), note="Equivalent one-way propagation delay, not a DS-TWR register correction. Final firmware value may need Murata module-specific factory calibration + custom PCB external correction. Firmware unit/sign/path allocation still requires confirmation.")
