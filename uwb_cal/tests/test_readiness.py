from uwb_cal.demo import demo_project
from uwb_cal.analysis.engine import analyze


def test_raw_instability_cannot_be_hidden_by_filtering():
    project = demo_project()
    for dataset in project.datasets:
        if dataset.kind == "angle" and dataset.label == "EVB-CUSTOM" and dataset.true_angle_deg == 0:
            for record in dataset.records[:15]:
                record["pdoa_deg"] = 50.0
    _, result = analyze(project)
    assert not result["production_ready"]
    assert any("Raw fixed-position PDoA is unstable" in w for w in result["warnings"])
