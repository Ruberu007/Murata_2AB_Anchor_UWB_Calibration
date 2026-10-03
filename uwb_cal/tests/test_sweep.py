import pytest
from uwb_cal.parsers.rf_diag_parser import parse_text
from uwb_cal.models.measurement import Project
from uwb_cal.analysis.sweep import capture_angle, sweep_status, planned_angles, export_final_bundle
from uwb_cal.analysis.engine import analyze


def test_decimal_fields_with_hex_annotations():
    records, _ = parse_text('[2026-10-02T11:04:07.899+05:30] X range=0x29\n PDoA diagnostic: -4312 raw, -120.634 degrees\n tdoa = 2199023255379 (0x01FFFFFFFF53)\n stsPower = 61 (0x0000003D)\n sts2Power = 869 (0x00000365)\n pdoa = -4312 (0xEF28)')
    assert records[0]['tdoa_raw'] == 2199023255379
    assert records[0]['stsPower'] == 61 and records[0]['sts2Power'] == 869
    assert records[0]['pdoa_raw'] == -4312


def test_capture_persistence_and_partial_bundle(tmp_path):
    file = tmp_path / 'rf_angle_0Degree.txt'
    file.write_text('[2026-10-02T11:04:07+05:30] X range=0x29\n PDoA diagnostic: -1 raw, -41.7 degrees\n tdoa = 2199023255551 (0x01FFFFFFFFFF)')
    p = Project()
    a = capture_angle(p, file, 0)
    b = capture_angle(p, file, 0)
    assert a.name != b.name
    assert planned_angles(p)[0] == -180 and planned_angles(p)[-1] == 180
    zero = next(r for r in sweep_status(p) if r['angle_deg'] == 0)
    assert zero['captures'] == 2 and zero['status'] == 'SAVED'
    p.save(tmp_path / 'saved.json')
    loaded = Project.load(tmp_path / 'saved.json')
    assert loaded.datasets[0].source_text == file.read_text()
    frame, results = analyze(loaded)
    assert not results['production_ready']
    assert frame.tdoa_signed.iloc[0] == -1
    export_final_bundle(loaded, frame, tmp_path / 'results')
    assert len(list((tmp_path / 'results' / 'rf_angle_captures').glob('*.txt'))) == 2
    assert (tmp_path / 'results' / 'angle_summary.csv').exists()
    assert not (tmp_path / 'results' / 'custom_calibration.h').exists()
    with pytest.raises(ValueError): capture_angle(p, file, 181)
