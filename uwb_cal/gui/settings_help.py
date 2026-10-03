"""Plain-language help shared by the Fixed Angle Analysis controls."""
from html import escape


FILTER_HELP = {
    "MAD": "MAD (Median Absolute Deviation) compares each reading with the middle reading, called the median. It flags readings much farther from the median than the usual spread. Recommended for stationary UWB measurements because a few bad readings have little effect on this estimate.",
    "IQR": "IQR (Interquartile Range) measures the spread of the middle 50% of readings. It flags readings outside a band extended below the lower quarter and above the upper quarter. This is an alternative way to identify unusually low or high readings.",
    "None": "No outlier filtering: every available finite reading is used, including unusual readings. Missing values still cannot be used in calculations. Use this to inspect the effect of filtering.",
}

INTERPOLATION_HELP = {
    "linear": "Linear interpolation joins neighboring calibration points with straight lines. For example, if PDoA 0° means angle 0° and PDoA 40° means angle 20°, a PDoA of 20° gives an estimated angle of 10°. This is the recommended starting choice.",
    "pchip": "PCHIP (Piecewise Cubic Hermite Interpolating Polynomial) uses a smooth curve between neighboring calibration points while preserving their direction. It is allowed only when PDoA consistently increases or consistently decreases as the physical angle increases. It is not automatically more accurate than linear interpolation.",
}

SETTING_HELP = {
    "filter": ("Outlier method", "Chooses MAD, IQR or None. On this tab, filtering examines unwrapped PDoA readings within each dataset."),
    "threshold": ("Filter tolerance", "For MAD: allowed distance from the median = threshold × 1.4826 × MAD. For IQR: each end of the middle-50% band is extended by threshold × IQR. A larger value retains more readings; a smaller value rejects more. Ignored with None. If MAD or IQR is zero, only the middle plateau/band is retained."),
    "tdoa_bits": ("TDoA signed field width (bits)", "TDoA is a receive-time difference. This tells the app how many bits firmware used to store signed values. At 41 bits, 2199023255551 decodes to −1. Confirm this width with the firmware team; it is not a noise threshold."),
    "reference_sign": ("Expected angle direction", "+1 expects PDoA to increase as the physical angle increases; −1 expects it to decrease. A slope in the opposite direction is reported as reversed orientation. This setting does not swap antennas or write firmware settings."),
    "interpolation": ("Angle estimation between measured points", "Chooses straight lines (linear) or a smooth direction-preserving curve (pchip) for the PDoA-to-angle lookup table (LUT). Stay within the measured calibration range in use."),
    "mae_limit": ("Average angle-error limit (degrees)", "MAE means Mean Absolute Error: the average size of angle errors, ignoring their sign. Validation leaves out one known angle at a time and predicts it from the others. With 5°, the average error must be no more than 5° to meet this readiness criterion."),
    "max_error_limit": ("Worst angle-error limit (degrees)", "The largest absolute error in leave-one-angle-out validation. With 10°, no held-out angle may have an error larger than 10° to meet this criterion. Held-out endpoints use extrapolation for validation only."),
    "minimum_samples": ("Minimum accepted readings per angle dataset", "Each enabled custom-PCB fixed-angle dataset must contain at least this many accepted readings to meet the sample-count readiness criterion. Missing and rejected readings do not count."),
    "phase_sd_limit": ("PDoA spread limit (degrees)", "SD means Standard Deviation: how much readings vary around their average. Lower SD means steadier phase at a fixed position. Raw fixed-angle dataset SD and filtered per-angle corrected-phase SD are checked against this limit; unstable raw data cannot be hidden by filtering."),
    "tdoa_sd_limit": ("TDoA spread limit (raw diagnostic units)", "Limits variation in signed TDoA for stationary readings. Used for raw datasets and filtered angle groups. It also supplies the minimum deviation threshold for moving-log TDoA spike detection. These units are not converted to seconds or metres."),
    "small_reversal_deg": ("Small local reversal tolerance (PDoA degrees)", "The phase trend should keep the same direction as physical angle increases (monotonic). A backward step within this tolerance gives a warning; a larger backward step fails and blocks the LUT. Even a small reversal prevents production-ready status. Equal phase points also fail because their angle mapping is ambiguous."),
    "imbalance_notice": ("Noticeable STS power imbalance ratio", "STS1 and STS2 are the two logged receive paths. A value of 2 means one path's mean raw power is at least twice the other's. This produces NOTICEABLE IMBALANCE unless the larger threshold is reached. Raw powers are diagnostic values, not dBm."),
    "imbalance_large": ("Large STS power imbalance ratio", "A value of 4 means one path's mean raw power is at least four times the other's, producing LARGE IMBALANCE. Moving-log detection also flags individual samples at this ratio. This is a project threshold, not a hardware specification."),
    "phase_jump_deg": ("Moving-tag phase jump (degrees)", "Flags a change larger than this value between neighboring unwrapped PDoA samples. A normal raw ±180° phase wrap is listed separately and does not alone prove RF instability. Faster real motion or long sample gaps can also cause large changes."),
    "range_jump_m": ("Moving-tag distance jump (metres)", "Flags a measured-distance change larger than this value between neighboring samples. A value of 0.5 means a jump over 50 cm. Consider tag speed and sampling interval when choosing it."),
    "fp_jump": ("Moving-tag first-path jump (raw index units)", "The first-path index identifies where the receiver detected the start of the radio signal. Flags an STS1 or STS2 index change larger than this value between neighboring samples. No conversion to time or distance is assumed."),
    "range_sd_limit_m": ("Stationary range-error spread limit (metres)", "Checks the standard deviation of measured range errors at each known distance. A value of 0.1 allows up to 10 cm of spread. This checks repeatability, not mean range bias. Manually assigning one constant measured distance cannot establish stability."),
}


def settings_description(settings, filter_name, interpolation, detailed=False):
    text = ["<b>Filter = which readings to use.</b> " + escape(FILTER_HELP[filter_name]),
            "<p><b>Interpolation = how to estimate an angle between calibration points.</b> " + escape(INTERPOLATION_HELP[interpolation]) + "</p>",
            f"<p><b>Current filter tolerance: {escape(str(settings['threshold']))}.</b> Larger values keep more readings; smaller values reject more. Rejected readings stay in Raw Data and appear as red crosses in plots. Original measurements are preserved.</p>",
            "<p>Start with <b>MAD + linear</b>. Change a setting, then click <b>Run Analysis / Refresh All Pages</b> to apply it. Use <b>Edit project-specific settings</b> to change the numeric values. All limits are <b>project-specific defaults, not Murata specifications</b>.</p>"]
    if detailed:
        text.append("<h3>What each setting means</h3><table cellspacing='8' width='100%'>")
        for key, (title, explanation) in SETTING_HELP.items():
            value = filter_name if key == "filter" else interpolation if key == "interpolation" else settings.get(key)
            text.append(f"<tr><td valign='top'><b>{escape(title)}</b><br><code>{escape(key)} = {escape(str(value))}</code></td><td>{escape(explanation)}</td></tr>")
        text.append("</table><p><b>Terms:</b> PDoA = phase difference between receive paths; AoA = physical angle of arrival; LUT = lookup table; STS = the firmware's secure timestamp sequence receive diagnostics. Confirm the STS1/STS2-to-antenna mapping with your firmware team.</p>")
    return "".join(text)
