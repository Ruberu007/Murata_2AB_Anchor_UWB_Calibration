import numpy as np
from scipy.interpolate import interp1d, PchipInterpolator
from scipy.stats import spearmanr


def orientation(angles, phases, reference_sign=1):
    if len(angles) < 2 or np.ptp(phases) == 0:
        return dict(orientation="unknown", spearman=None, slope=None)
    rho = float(spearmanr(angles, phases).statistic)
    slope = float(np.polyfit(angles, phases, 1)[0])
    return dict(orientation="reversed" if slope * reference_sign < 0 else "normal", spearman=rho, slope=slope)


def monotonicity(angles, phases, small_reversal_deg=5):
    if len(angles) < 3:
        return "INSUFFICIENT"
    y = np.asarray(phases)[np.argsort(angles)]
    direction = 1 if y[-1] >= y[0] else -1
    differences = direction * np.diff(y)
    if np.any(differences == 0):
        return "FAIL"
    if np.all(differences > 0):
        return "PASS"
    return "WARNING" if np.min(differences) >= -small_reversal_deg else "FAIL"


def interpolate_lut(phases, angles, method="linear"):
    order = np.argsort(phases)
    x, y = np.asarray(phases)[order], np.asarray(angles)[order]
    if len(x) < 2 or np.any(np.diff(x) <= 0):
        raise ValueError("LUT requires at least two distinct PDoA points.")
    if method == "pchip":
        if monotonicity(y, x) != "PASS":
            raise ValueError("PCHIP requires strictly monotonic calibration data.")
        return PchipInterpolator(x, y, extrapolate=True)
    return interp1d(x, y, kind="linear", fill_value="extrapolate")


def validate_lut(phases, angles, method="linear"):
    if len(phases) < 3:
        raise ValueError("Leave-one-angle-out validation requires at least three angles.")
    errors = []
    for i, (phase, angle) in enumerate(zip(phases, angles)):
        keep = np.arange(len(phases)) != i
        prediction = float(interpolate_lut(np.asarray(phases)[keep], np.asarray(angles)[keep], method)(phase))
        errors.append(dict(angle_deg=float(angle), predicted_deg=prediction, error_deg=prediction - float(angle), extrapolated=bool(phase < np.min(np.asarray(phases)[keep]) or phase > np.max(np.asarray(phases)[keep]))))
    e = np.array([row["error_deg"] for row in errors])
    return dict(mae=float(np.mean(abs(e))), rmse=float(np.sqrt(np.mean(e**2))), max_error=float(np.max(abs(e))), errors=errors, note="Held-out endpoints use extrapolation; deployment outside the calibrated domain is unsupported.")
