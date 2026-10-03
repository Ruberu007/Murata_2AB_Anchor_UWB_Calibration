import json
from pathlib import Path


def export_json(project, path):
    r = project.results
    payload = dict(project=project.metadata, settings=project.settings, zero_pdoa_offset_deg=r.get("zero_pdoa_offset_deg"), orientation=r.get("orientation"), external_range_bias_m=r.get("range", {}).get("bias_m"), external_delay_ps=r.get("range", {}).get("delay_ps"), lut=r.get("lut", []), results=r)
    Path(path).write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
