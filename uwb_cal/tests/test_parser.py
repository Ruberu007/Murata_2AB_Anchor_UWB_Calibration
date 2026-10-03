from pathlib import Path
import pytest
from uwb_cal.parsers.rf_diag_parser import parse_text, parse_file, FIELDS


def test_full_parser():
    text = Path("examples/sample_rf_diag.txt").read_text()
    records, warnings = parse_text(text + "\n" + text)
    assert len(records) == 2 and not warnings
    assert all(f in records[0] for f in FIELDS)
    assert records[0]["pdoa_raw"] == -4312
    assert records[0]["pdoa_deg"] == -120.634
    assert records[0]["timestamp"].endswith("+05:30")
    assert "measured_distance_m" not in records[0]
    records, _ = parse_text(text, range_scale_m=.01)
    assert records[0]["measured_distance_m"] == pytest.approx(.41)


def test_missing_fields_and_unknown():
    records, warnings = parse_text("[bad] X range=0x29\n tdoa = 2199023255551\n unknown = 42\n pdoa = -3")
    assert len(records) == 1 and warnings
    assert "unknown" not in records[0] and "pdoa_deg" not in records[0]
    assert parse_text("")[0] == []


def test_csv(tmp_path):
    path = tmp_path / "ranges.csv"
    path.write_text("measured_distance_m,tdoa\n2.1,2199023255551\n")
    records, _ = parse_file(path)
    assert records[0]["measured_distance_m"] == 2.1
    assert records[0]["tdoa_raw"] == 2199023255551
