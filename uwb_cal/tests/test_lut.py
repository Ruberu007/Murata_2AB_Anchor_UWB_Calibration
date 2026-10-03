import numpy as np
import pytest
from uwb_cal.analysis.lut import orientation, monotonicity, interpolate_lut, validate_lut
from uwb_cal.demo import demo_project
from uwb_cal.analysis.engine import analyze


def test_orientation_and_monotonicity():
    assert orientation([-30,0,30], [70,0,-70])["orientation"] == "reversed"
    assert monotonicity([0,1,2,3], [0,10,9,20]) == "WARNING"
    assert monotonicity([0,1,2,3], [0,10,-10,20]) == "FAIL"
    assert monotonicity([0,1,2], [0,0,20]) == "FAIL"


def test_interpolation_and_validation():
    x, y = np.array([-100,0,100]), np.array([-50,0,50])
    assert interpolate_lut(x,y)(50) == 25
    assert interpolate_lut(x,y,"pchip")(50) == 25
    assert validate_lut(x,y)["mae"] == 0
    with pytest.raises(ValueError): interpolate_lut([0,10,9,20],[0,1,2,3],"pchip")


def test_demo_and_strong_reversal_gate():
    p = demo_project()
    f, r = analyze(p)
    assert r["production_ready"] and abs(r["zero_pdoa_offset_deg"]+41.7) < 1
    assert "pdoa_corrected" in f and (~f.valid).sum() > 0
    for d in p.datasets:
        if d.kind == "angle" and d.label == "EVB-CUSTOM" and d.true_angle_deg == 15:
            for record in d.records: record["pdoa_deg"] = -130
    _, r = analyze(p)
    assert r["monotonicity"] == "FAIL" and not r["production_ready"] and not r["lut"]


def test_reversed_lut_convention():
    p = demo_project()
    for d in p.datasets:
        if d.kind == "angle" and d.label == "EVB-CUSTOM":
            for record in d.records: record["pdoa_deg"] = -record["pdoa_deg"]
    _, r = analyze(p)
    assert r["orientation"] == "reversed" and r["pdoa_sign"] == -1
    assert r["lut"][0]["aoa_deg"] == -60
