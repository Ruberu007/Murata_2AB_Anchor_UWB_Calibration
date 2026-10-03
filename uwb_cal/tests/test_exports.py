import json
import pandas as pd
from uwb_cal.demo import demo_project
from uwb_cal.analysis.engine import analyze
from uwb_cal.models.measurement import Project
from uwb_cal.export.csv_export import export_csv, export_lut_csv
from uwb_cal.export.json_export import export_json
from uwb_cal.export.c_header_export import export_c_header
from uwb_cal.export.report_export import export_report


def test_exports_and_roundtrip(tmp_path):
    project = demo_project()
    frame, result = analyze(project)
    export_csv(frame, tmp_path/"raw.csv")
    export_lut_csv(result, tmp_path/"lut.csv")
    export_json(project, tmp_path/"cal.json")
    export_c_header(result, tmp_path/"cal.h")
    export_report(project, frame, tmp_path/"report.html")
    project.save(tmp_path/"project.json")
    loaded = Project.load(tmp_path/"project.json")
    assert len(loaded.datasets) == len(project.datasets)
    assert loaded.settings == project.settings
    assert len(pd.read_csv(tmp_path/"raw.csv")) == len(frame)
    assert len(pd.read_csv(tmp_path/"lut.csv")) == 9
    assert json.loads((tmp_path/"cal.json").read_text())["external_range_bias_m"] > .1
    header = (tmp_path/"cal.h").read_text()
    assert "CUSTOM_PDOA_ZERO_OFFSET_DEG" in header and "CUSTOM_EXTERNAL_RANGE_BIAS_M" in header
    assert "SYNTHETIC TEST DATA" in (tmp_path/"report.html").read_text()
    assert "data:image/png;base64" in (tmp_path/"report.html").read_text()
