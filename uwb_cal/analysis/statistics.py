import numpy as np


def describe(values):
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if not len(x):
        return dict(count=0, mean=None, median=None, sd=None, minimum=None, maximum=None, mad=None, iqr=None)
    return dict(count=len(x), mean=float(x.mean()), median=float(np.median(x)), sd=float(x.std(ddof=1)) if len(x) > 1 else None, minimum=float(x.min()), maximum=float(x.max()), mad=float(np.median(abs(x - np.median(x)))), iqr=float(np.percentile(x, 75) - np.percentile(x, 25)))


def filter_mask(values, method="MAD", threshold=3.5):
    if threshold <= 0:
        raise ValueError("Filter threshold must be positive.")
    x = np.asarray(values, dtype=float)
    mask = np.isfinite(x)
    finite = x[mask]
    if not len(finite) or method == "None":
        return mask
    if method == "MAD":
        center = np.median(finite)
        mad = np.median(abs(finite - center))
        # Zero MAD does not imply all samples are good: retain only the median plateau.
        mask &= abs(x - center) <= (threshold * 1.4826 * mad if mad else 1e-9)
    elif method == "IQR":
        low, high = np.percentile(finite, [25, 75])
        mask &= (x >= low - threshold * (high - low)) & (x <= high + threshold * (high - low))
    else:
        raise ValueError("Unknown filtering method.")
    return mask
