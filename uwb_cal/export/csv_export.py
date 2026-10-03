from pathlib import Path
import pandas as pd


def export_csv(frame, path):
    frame.to_csv(path, index=False)


def export_lut_csv(result, path):
    if not result.get("lut"):
        raise ValueError("No valid LUT is available. Review angle calibration.")
    pd.DataFrame(result["lut"], columns=["pdoa_deg", "aoa_deg"]).to_csv(path, index=False)
