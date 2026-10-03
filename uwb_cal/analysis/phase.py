import numpy as np


def unwrap_phase(values):
    """Unwrap finite segments in acquisition order; missing samples remain missing."""
    values = np.asarray(values, dtype=float)
    result = values.copy()
    indices = np.flatnonzero(np.isfinite(values))
    for segment in np.split(indices, np.where(np.diff(indices) > 1)[0] + 1):
        if len(segment):
            result[segment] = np.rad2deg(np.unwrap(np.deg2rad(values[segment])))
    return result


def align_branch(values, center):
    """Choose the equivalent 360-degree branch nearest a known center."""
    return np.asarray(values) + 360 * np.round((center - np.nanmedian(values)) / 360)


def zero_offset(values):
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if not len(finite):
        raise ValueError("At least one valid 0-degree calibration dataset is required.")
    return float(np.median(unwrap_phase(finite)))
