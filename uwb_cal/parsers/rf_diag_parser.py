"""Tolerant firmware log parser. Header range codes remain opaque tokens."""
import re
from datetime import datetime
from pathlib import Path
import pandas as pd

FIELDS = ("ipatovRxTime ipatovRxStatus ipatovPOA stsRxTime stsRxStatus stsPOA sts2RxTime sts2RxStatus sts2POA tdoa pdoa xtalOffset ciaDiag1 ipatovPeak ipatovPower ipatovF1 ipatovF2 ipatovF3 ipatovFpIndex ipatovAccumCount stsPeak stsPower stsF1 stsF2 stsF3 stsFpIndex stsAccumCount sts2Peak sts2Power sts2F1 sts2F2 sts2F3 sts2FpIndex sts2AccumCount").split()


def parse_text(text, range_scale_m=None):
    records, warnings, current = [], [], None

    def finish():
        if current is not None:
            records.append(current.copy())
            missing = [f for f in FIELDS if f not in current]
            if missing:
                warnings.append(f"Record {len(records)} incomplete: missing {', '.join(missing)}")

    for number, line in enumerate(text.splitlines(), 1):
        header = re.match(r"\[([^\]]+)\]\s*(\S+).*?range=(\S+)", line)
        if header:
            finish()
            current = {"timestamp": None, "device": header[2], "range_code": header[3]}
            try:
                current["timestamp"] = datetime.fromisoformat(header[1].replace("Z", "+00:00")).isoformat()
            except ValueError:
                warnings.append(f"Line {number}: invalid timestamp.")
            if range_scale_m is not None:
                try:
                    current["measured_distance_m"] = int(header[3], 0) * float(range_scale_m)
                except ValueError:
                    warnings.append(f"Line {number}: invalid configured range code.")
            continue
        diagnostic = re.search(r"PDoA diagnostic:\s*([-+]?\d+)\s*raw,\s*([-+\d.eE]+)\s*degrees", line)
        field = re.match(r"\s*(\w+)\s*=\s*([-+]?(?:0[xX][\da-fA-F]+|\d+)(?:\.\d+)?)\s*(?:\(0[xX][\da-fA-F]+\))?\s*$", line)
        if current is None and (diagnostic or field):
            current = {"timestamp": None}
            warnings.append(f"Line {number}: record has no timestamp header.")
        if diagnostic:
            try:
                current.update(pdoa_raw=int(diagnostic[1]), pdoa_deg=float(diagnostic[2]))
            except ValueError:
                warnings.append(f"Line {number}: invalid PDoA diagnostic.")
        elif field and field[1] in FIELDS + ["measured_distance_m"]:
            try:
                value = float(field[2]) if field[1] == "measured_distance_m" else int(field[2], 16 if "x" in field[2].lower() else 10)
                current[field[1]] = value
                if field[1] == "tdoa":
                    current["tdoa_raw"] = value
                if field[1] == "pdoa":
                    current["pdoa_raw"] = value
            except ValueError:
                warnings.append(f"Line {number}: invalid {field[1]}.")
        elif current is not None and "PDoA reported by firmware:" in line:
            match = re.search(r":\s*([-+\d.]+)", line)
            if match:
                try:
                    current["firmware_pdoa_deg"] = float(match[1])
                except ValueError:
                    warnings.append(f"Line {number}: invalid firmware-reported PDoA.")
    finish()
    if not any("pdoa_deg" in r for r in records):
        warnings.append("No PDoA values were found in this file. Raw PDoA units are not converted without firmware documentation.")
    return records, warnings


def parse_file(path, range_scale_m=None):
    if Path(path).suffix.lower() == ".csv":
        frame = pd.read_csv(path)
        records = frame.astype(object).where(frame.notna(), None).to_dict("records")
        for record in records:
            if "tdoa_raw" not in record and record.get("tdoa") is not None:
                record["tdoa_raw"] = record["tdoa"]
        return records, []
    return parse_text(Path(path).read_text(encoding="utf-8-sig", errors="replace"), range_scale_m)
