from uwb_cal.demo import demo_project
from uwb_cal.analysis.engine import analyze


def test_movement_and_matched_comparison():
    p = demo_project()
    frame, r = analyze(p)
    assert len(r["comparison"]) == 9*7
    assert r["movements"]["Moving synthetic tag"]["events"]
    assert "certainty" in r["movements"]["Moving synthetic tag"]["conclusion"]
    for d in p.datasets:
        if d.kind == "movement":
            d.records[10]["measured_distance_m"] = 100
    _, r = analyze(p)
    assert any(e["event"] == "distance jump" for e in r["movements"]["Moving synthetic tag"]["events"])
