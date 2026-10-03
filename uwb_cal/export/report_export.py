import base64
from io import BytesIO
from html import escape
from pathlib import Path
import json
from uwb_cal.gui.plots import figures


def export_report(project, frame, path):
    r = project.results
    sections = ["<!doctype html><html><head><meta charset='utf-8'><title>UWB calibration report</title><style>body{font-family:Arial;max-width:1100px;margin:auto;padding:24px}pre{white-space:pre-wrap}img{max-width:100%}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:5px}</style></head><body>", "<h1>CUSTOM TYPE 2AB CALIBRATION CHECK</h1>"]
    if project.metadata.get("synthetic"):
        sections.append("<h2>SYNTHETIC TEST DATA — not hardware validation</h2>")
    sections.append('<h2>Angle capture coverage and LUT sector</h2><pre>' + escape(json.dumps(dict(calibration_sector_deg=r.get('calibration_sector_deg'), angle_capture_checklist=r.get('angle_capture_checklist')), indent=2)) + '</pre>')
    for title, data in [("Project", project.metadata), ("Datasets", [dict(name=d.name, kind=d.kind, label=d.label, angle=d.true_angle_deg, distance=d.true_distance_m, enabled=d.enabled, source=d.source) for d in project.datasets]), ("Project-specific acceptance settings", project.settings), ("Readiness", r.get("readiness")), ("Engineering notes", r.get("engineering_notes")), ("Warnings", r.get("warnings")), ("Statistics", r.get("statistics")), ("LUT and validation", dict(lut=r.get("lut"), validation=r.get("validation"))), ("Range correction", r.get("range")), ("EVB comparison", r.get("comparison")), ("Movement evidence", r.get("movements"))]:
        sections.append(f"<h2>{escape(title)}</h2><pre>{escape(json.dumps(data, indent=2, allow_nan=False))}</pre>")
    for title, figure in figures(frame, r):
        buffer = BytesIO()
        figure.savefig(buffer, format="png", dpi=100)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        sections.append(f"<h2>{escape(title)}</h2><img alt='{escape(title)}' src='data:image/png;base64,{encoded}'>")
    sections.append("</body></html>")
    Path(path).write_text("\n".join(sections), encoding="utf-8")
