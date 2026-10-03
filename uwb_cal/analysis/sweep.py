"""Persist individual angle captures and assemble a reviewable final result bundle."""
import re
from pathlib import Path
import pandas as pd
from uwb_cal.models.measurement import Dataset
from uwb_cal.parsers.rf_diag_parser import parse_file


def planned_angles(project):
    s = project.sweep
    start, stop, step = int(s['start']), int(s['stop']), int(s['step'])
    if not -180 <= start <= stop <= 180 or step < 1:
        raise ValueError('Choose angles between -180 and +180 and a positive step.')
    return sorted(set(range(start, stop + 1, step)) | {stop})


def capture_angle(project, path, angle, distance=2.0, label='EVB-CUSTOM'):
    if project.metadata.get('synthetic'):
        raise ValueError('Create a real project before saving RF captures.')
    if not -180 <= angle <= 180:
        raise ValueError('The physical angle must be between -180 and +180 degrees.')
    records, warnings = parse_file(path)
    if not records or not any(r.get('pdoa_deg') is not None for r in records):
        raise ValueError('No PDoA degree measurements were found in this capture.')
    existing = {d.name for d in project.datasets}
    base = f'{label} {angle:+g} deg'
    name, i = base, 2
    while name in existing:
        name = f'{base} capture {i}'
        i += 1
    dataset = Dataset(name, records, true_angle_deg=float(angle), true_distance_m=float(distance), label=label, source=str(path), warnings=warnings, source_text=Path(path).read_text(encoding='utf-8-sig', errors='replace'))
    project.datasets.append(dataset)
    project.results = {}
    return dataset


def sweep_status(project):
    rows = []
    for angle in planned_angles(project):
        datasets = [d for d in project.datasets if d.enabled and d.kind == 'angle' and d.label == 'EVB-CUSTOM' and d.true_angle_deg == angle]
        rows.append(dict(angle_deg=angle, captures=len(datasets), samples=sum(len(d.records) for d in datasets), status='SAVED' if datasets else 'MISSING'))
    return rows


def export_final_bundle(project, frame, folder):
    from uwb_cal.export.csv_export import export_csv, export_lut_csv
    from uwb_cal.export.json_export import export_json
    from uwb_cal.export.c_header_export import export_c_header
    from uwb_cal.export.report_export import export_report
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    logs = folder / 'rf_angle_captures'
    logs.mkdir(exist_ok=True)
    for i, dataset in enumerate(project.datasets, 1):
        if dataset.kind == 'angle' and dataset.source_text:
            name = re.sub(r'[^a-zA-Z0-9_+.-]', '_', dataset.name)
            suffix = '.csv' if Path(dataset.source).suffix.lower() == '.csv' else '.txt'
            (logs / f'{i:03d}_{name}{suffix}').write_text(dataset.source_text, encoding='utf-8')
    project.save(folder / 'project.json')
    export_csv(frame, folder / 'all_measurements.csv')
    pd.DataFrame(sweep_status(project)).to_csv(folder / 'angle_checklist.csv', index=False)
    summary = []
    for (angle, label), group in frame[frame.kind == 'angle'].groupby(['true_angle_deg', 'label']):
        valid = group[group.valid]
        summary.append(dict(angle_deg=float(angle), setup=label, total=len(group), accepted=len(valid), rejected=len(group)-len(valid), pdoa_median_deg=valid.pdoa_unwrapped.median(), pdoa_sd_deg=valid.pdoa_unwrapped.std(), signed_tdoa_mean=valid.tdoa_signed.mean(), signed_tdoa_sd=valid.tdoa_signed.std(), sts1_mean_power=valid.stsPower.mean(), sts2_mean_power=valid.sts2Power.mean()))
    pd.DataFrame(summary).to_csv(folder / 'angle_summary.csv', index=False)
    export_json(project, folder / 'calibration.json')
    export_report(project, frame, folder / 'engineering_report.html')
    if project.results.get('lut'):
        export_lut_csv(project.results, folder / 'lut.csv')
        export_c_header(project.results, folder / 'custom_calibration.h')
    (folder / 'READ_ME.txt').write_text('Review engineering_report.html and calibration.json first. All angles are included in diagnostics; the LUT uses only the selected calibration sector. Missing angles are listed in angle_checklist.csv. Original imported logs are in rf_angle_captures. No firmware/OTP settings are written.\nLUT readiness: ' + str(project.results.get('production_ready')) + '\n', encoding='utf-8')
