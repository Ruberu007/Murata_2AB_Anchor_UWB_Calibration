from pathlib import Path
from datetime import datetime
import re
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox
from uwb_cal.analysis.sweep import sweep_status, capture_angle, export_final_bundle


class AngleSweepDialog(QDialog):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setWindowTitle('Save RF captures by physical angle / Prepare final results')
        self.resize(950, 750)
        layout = QVBoxLayout(self)
        note = QLabel('Select a physical angle in the checklist, then import its stationary RF details file.\nEach capture is saved immediately in your project and copied beside it. Repeated captures are retained.\nThe full sweep is diagnostic data. Choose a narrower AoA calibration sector with a unique phase-to-angle relationship.')
        note.setWordWrap(True)
        layout.addWidget(note)
        controls = QHBoxLayout()
        self.controls = {}
        for key, title in [('start', 'Sweep start'), ('stop', 'Sweep end'), ('step', 'Angle step'), ('calibration_min', 'LUT sector start'), ('calibration_max', 'LUT sector end')]:
            spin = QSpinBox()
            spin.setRange(1, 360) if key == 'step' else spin.setRange(-180, 180)
            spin.setValue(int(owner.project.sweep[key]))
            controls.addWidget(QLabel(title))
            controls.addWidget(spin)
            self.controls[key] = spin
        layout.addLayout(controls)
        button = QPushButton('Update angle checklist')
        button.clicked.connect(lambda: owner.guard(self.update_plan))
        layout.addWidget(button)
        self.progress = QLabel()
        layout.addWidget(self.progress)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(['Physical angle (degrees)', 'Saved captures', 'Total readings', 'Status'])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        for title, callback in [('Import and save RF file for selected angle', self.import_capture), ('Prepare Final Results (all saved captures)', self.prepare_results)]:
            button = QPushButton(title)
            button.clicked.connect(lambda checked=False, cb=callback: owner.guard(cb))
            layout.addWidget(button)
        self.refresh()
        zero = next((i for i, r in enumerate(self.rows) if r['angle_deg'] == 0), 0)
        self.table.selectRow(zero)

    def update_plan(self):
        values = {key: spin.value() for key, spin in self.controls.items()}
        if values['start'] > values['stop'] or values['calibration_min'] >= values['calibration_max']:
            raise ValueError('Start must be before end; the LUT sector must have nonzero width.')
        self.owner.project.sweep.update(values)
        self.owner.project.results = {}
        self.refresh()

    def refresh(self):
        self.rows = sweep_status(self.owner.project)
        self.table.setRowCount(len(self.rows))
        for i, row in enumerate(self.rows):
            for j, value in enumerate([row['angle_deg'], row['captures'], row['samples'], row['status']]):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()
        saved = sum(r['status'] == 'SAVED' for r in self.rows)
        self.progress.setText(f'{saved} / {len(self.rows)} planned angles saved. Missing angles remain visible; partial results are labeled.')

    def ensure_project_path(self):
        if not self.owner.project_path:
            path, _ = QFileDialog.getSaveFileName(self, 'Choose project file for automatic saving', 'angle_calibration.json', 'Project JSON (*.json)')
            if not path:
                return False
            self.owner.project_path = path
        self.owner.collect_metadata()
        return True

    def import_capture(self):
        if self.owner.project.metadata.get('synthetic'):
            raise ValueError('Create or load a real project first; demo data cannot be mixed with measurements.')
        row = self.table.currentRow()
        if row < 0:
            raise ValueError('Select the physical angle in the checklist first.')
        angle = self.rows[row]['angle_deg']
        path, _ = QFileDialog.getOpenFileName(self, f'RF details at {angle:+d} degrees', '', 'RF logs (*.txt *.log *.csv);;All files (*)')
        if not path or not self.ensure_project_path():
            return
        dataset = capture_angle(self.owner.project, path, angle, self.owner.distance.value(), self.owner.label.currentText())
        self.owner.collect_metadata()
        self.owner.project.save(self.owner.project_path)
        archive = Path(self.owner.project_path).with_suffix('')
        archive = archive.parent / (archive.name + '_rf_captures')
        archive.mkdir(parents=True, exist_ok=True)
        name = re.sub(r'[^a-zA-Z0-9_+.-]', '_', dataset.name)
        (archive / (name + Path(path).suffix)).write_text(dataset.source_text, encoding='utf-8')
        self.owner.refresh_datasets()
        self.refresh()
        self.table.selectRow(row)
        self.progress.setText(self.progress.text() + f' Last saved: {angle:+d} degrees, {len(dataset.records)} readings.')

    def prepare_results(self):
        self.update_plan()
        if not self.ensure_project_path():
            return
        self.owner.run_analysis()
        self.owner.project.save(self.owner.project_path)
        folder = QFileDialog.getExistingDirectory(self, 'Choose parent folder for final result bundle')
        if not folder:
            return
        from uuid import uuid4
        output = Path(folder) / ('UWB_results_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + uuid4().hex[:6])
        export_final_bundle(self.owner.project, self.owner.frame, output)
        missing = sum(r['status'] == 'MISSING' for r in self.rows)
        ready = self.owner.project.results.get('production_ready', False)
        QMessageBox.information(self, 'Results saved', f'Results saved to:\n{output}\n\nMissing planned angles: {missing}\nAoA LUT ready against project criteria: {ready}\nOpen engineering_report.html for the full review. Missing or unstable data can prevent a final LUT.')
        self.owner.tabs.setCurrentIndex(7)
