from datetime import datetime, timedelta, timezone
import numpy as np
from .models.measurement import Project, Dataset


def demo_project():
    project = Project()
    project.metadata.update(project_name="SYNTHETIC TEST DATA — Type 2AB demo", synthetic=True, notes="Synthetic measurements only. Not hardware validation.")
    rng = np.random.default_rng(42)
    start = datetime(2026, 10, 2, 10, tzinfo=timezone.utc)

    def record(i, phase, distance=None):
        power = float(rng.normal(100, 4))
        tdoa = int(rng.normal(-28, 2))
        return dict(timestamp=(start + timedelta(milliseconds=50*i)).isoformat(), pdoa_deg=float((phase+180)%360-180), pdoa_raw=int(phase*35.74), tdoa_raw=tdoa % 2**41, measured_distance_m=distance, stsPower=power, sts2Power=float(rng.normal(95, 4)), stsFpIndex=float(rng.normal(23000, 2)), sts2FpIndex=float(rng.normal(23010, 2)), stsRxTime=100000+i*1000, sts2RxTime=100010+i*1000, xtalOffset=int(rng.normal(390, 2)), stsF1=1600, stsF2=1700, stsF3=2100, sts2F1=1550, sts2F2=1650, sts2F3=2000)

    for label in ["EVB-EVB", "EVB-CUSTOM"]:
        for angle in range(-60, 61, 15):
            phase = -41.7 + angle*2.4 if label == "EVB-CUSTOM" else angle*2.4
            records = [record(i, phase+rng.normal(0, 1.5)) for i in range(80)]
            records[5]["pdoa_deg"] += 45
            project.datasets.append(Dataset(f"{label} {angle:+d} deg", records, label=label, true_angle_deg=angle))
    for distance in [1, 2, 3, 5]:
        project.datasets.append(Dataset(f"Custom {distance} m", [record(i, -41.7, float(distance+0.12+rng.normal(0, 0.015))) for i in range(80)], kind="distance", true_distance_m=distance))
    project.datasets.append(Dataset("Moving synthetic tag", [record(i, -170+i*2+rng.normal(0, 0.8), float(2+i*0.002)) for i in range(200)], kind="movement", true_distance_m=None))
    return project
