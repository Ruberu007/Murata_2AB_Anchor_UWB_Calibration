from dataclasses import dataclass, field, asdict
import json
from pathlib import Path


@dataclass
class Dataset:
    name: str
    records: list[dict]
    kind: str = "angle"
    label: str = "EVB-CUSTOM"
    true_angle_deg: float | None = None
    true_distance_m: float | None = 2.0
    enabled: bool = True
    source: str = ""
    warnings: list[str] = field(default_factory=list)
    source_text: str = ""


@dataclass
class Project:
    metadata: dict = field(default_factory=lambda: dict(project_name="Untitled", pcb_revision="", uwb_module="Murata LBUA5QJ2AB-828", antenna_model="Taoglas UWC.20", uwb_channel="", calibration_tag="", operator="", notes="", synthetic=False))
    datasets: list[Dataset] = field(default_factory=list)
    settings: dict = field(default_factory=lambda: dict(filter="MAD", threshold=3.5, tdoa_bits=41, reference_sign=1, interpolation="linear", mae_limit=5.0, max_error_limit=10.0, minimum_samples=10, phase_sd_limit=10.0, tdoa_sd_limit=20.0, small_reversal_deg=5.0, imbalance_notice=2.0, imbalance_large=4.0, phase_jump_deg=30.0, range_jump_m=0.5, fp_jump=100.0, range_sd_limit_m=0.1))
    results: dict = field(default_factory=dict)
    sweep: dict = field(default_factory=lambda: dict(start=-180, stop=180, step=15, calibration_min=-60, calibration_max=60))

    def save(self, path):
        Path(path).write_text(json.dumps(asdict(self), indent=2, allow_nan=False), encoding="utf-8")

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "datasets" not in data:
            raise ValueError("This is not a calibration project JSON file.")
        project = cls()
        project.metadata.update(data.get("metadata", {}))
        project.settings.update(data.get("settings", {}))
        project.datasets = [Dataset(**item) for item in data["datasets"]]
        project.results = data.get("results", {})
        project.sweep.update(data.get("sweep", {}))
        return project
