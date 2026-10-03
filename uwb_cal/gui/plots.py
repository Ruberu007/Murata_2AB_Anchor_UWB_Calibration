from matplotlib.figure import Figure
import numpy as np


def figures(frame, result):
    """Shared GUI/report plots preserve individual accepted and rejected samples."""
    angle = frame[(frame.kind == "angle") & (frame.label == "EVB-CUSTOM")]
    distance = frame[(frame.kind == "distance") & (frame.label == "EVB-CUSTOM")].copy()
    distance["range_error_m"] = distance.measured_distance_m-distance.true_distance_m
    motion = frame[frame.kind == "movement"]
    specs = [("Physical angle vs raw PDoA", angle, "true_angle_deg", "pdoa_deg"), ("Physical angle vs corrected PDoA", angle, "true_angle_deg", "pdoa_corrected"), ("Angle vs PDoA SD", None, "angle_deg", "phase_sd"), ("Angle vs mean signed TDoA", None, "angle_deg", "tdoa_mean"), ("Angle vs TDoA SD", None, "angle_deg", "tdoa_sd"), ("Angle vs STS power (raw, NOT dBm)", angle, "true_angle_deg", ["stsPower", "sts2Power"]), ("Angle vs first-path difference", angle, "true_angle_deg", "fp_difference"), ("True vs measured distance", distance, "true_distance_m", "measured_distance_m"), ("Range error vs true distance", distance, "true_distance_m", "range_error_m"), ("Moving PDoA", motion, "elapsed_s", ["pdoa_deg", "pdoa_unwrapped"]), ("Moving signed TDoA", motion, "elapsed_s", "tdoa_signed"), ("Moving range", motion, "elapsed_s", "measured_distance_m"), ("Moving STS powers (raw, NOT dBm)", motion, "elapsed_s", ["stsPower", "sts2Power"]), ("Moving first-path indices", motion, "elapsed_s", ["stsFpIndex", "sts2FpIndex"])]
    output = []
    for title, data, x, ys in specs:
        fig = Figure(figsize=(7, 3.6), tight_layout=True)
        fig.set_facecolor('#ffffff')
        ax = fig.subplots()
        ax.set_facecolor('#f7fafc')
        ax.set_prop_cycle(color=['#087f8c', '#d19328', '#566bc1', '#19a58e', '#b26597', '#528bad'])
        if data is None:
            points = result.get("angle_points", [])
            ax.plot([p[x] for p in points], [p[ys] for p in points], "o-")
        else:
            for y in ys if isinstance(ys, list) else [ys]:
                for name, group in data.groupby("dataset_name"):
                    good = group[group.valid]
                    bad = group[~group.valid]
                    ax.scatter(good[x], good[y], s=8, alpha=.55, label=f"{name}: {y}")
                    if len(bad):
                        ax.scatter(bad[x], bad[y], marker="x", color="red", s=22, label="rejected")
            if not data.empty and data.dataset_name.nunique() < 4:
                ax.legend(fontsize=6)
        labels = {'true_angle_deg': 'Known physical angle (°)', 'pdoa_deg': 'Original phase (°)', 'pdoa_corrected': 'Corrected phase (°)', 'angle_deg': 'Known physical angle (°)', 'phase_sd': 'Phase spread / SD (°)', 'tdoa_mean': 'Mean signed TDoA (raw units)', 'tdoa_sd': 'TDoA spread / SD (raw units)', 'fp_difference': 'First-path index difference (raw units)', 'true_distance_m': 'True distance (m)', 'measured_distance_m': 'Measured distance (m)', 'range_error_m': 'Range error (m)', 'elapsed_s': 'Elapsed time (s) / sample order', 'tdoa_signed': 'Signed TDoA (raw units)'}
        ylabel = 'Raw STS power (not dBm)' if ys == ['stsPower', 'sts2Power'] else 'First-path index (raw units)' if ys == ['stsFpIndex', 'sts2FpIndex'] else 'Phase (°)' if isinstance(ys, list) else labels.get(ys, ys)
        ax.set(title=title, xlabel=labels.get(x, x), ylabel=ylabel)
        ax.title.set_color('#17354d')
        ax.tick_params(colors='#496278', labelsize=9)
        for spine in ax.spines.values():
            spine.set_color('#cddce6')
        ax.grid(color='#dce6ed', alpha=.8)
        has_points = any(np.isfinite(np.asarray(line.get_ydata(), dtype=float)).any() for line in ax.lines)
        has_points |= any(np.isfinite(np.ma.asarray(collection.get_offsets(), dtype=float).filled(np.nan)).all(axis=1).any() for collection in ax.collections)
        if not has_points:
            message = 'No usable measurements for this chart.\nImport and enable the relevant datasets, then run analysis.'
            if ys == 'pdoa_corrected' or data is None:
                message = 'No calibrated angle points available.\nInclude an enabled custom-PCB 0° capture and angles\ninside the selected LUT sector, then run analysis.'
            ax.text(.5, .5, message, ha='center', va='center', transform=ax.transAxes, fontsize=10, wrap=True)
        elif ys == 'measured_distance_m' and x == 'true_distance_m':
            endpoints = [float(data[x].min()), float(data[x].max())]
            ax.plot(endpoints, endpoints, '--', color='#58758a', linewidth=1, label='Ideal: measured = true')
            ax.legend(fontsize=7)
        elif ys == 'range_error_m':
            ax.axhline(0, linestyle='--', color='#58758a', linewidth=1)
        output.append((title, fig))
    return output
