import json
from pathlib import Path
import numpy as np
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget, QPushButton, QLabel, QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem, QTableView, QTextEdit, QTextBrowser, QScrollArea, QInputDialog, QCheckBox, QListWidget, QDockWidget)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from uwb_cal.models.measurement import Project, Dataset
from uwb_cal.parsers.rf_diag_parser import parse_file
from uwb_cal.analysis.engine import analyze
from uwb_cal.demo import demo_project
from uwb_cal.export.csv_export import export_csv, export_lut_csv
from uwb_cal.export.json_export import export_json
from uwb_cal.export.c_header_export import export_c_header
from uwb_cal.export.report_export import export_report
from .plots import figures
from .settings_help import settings_description
from .guides import PAGE_GUIDES, PLOT_GUIDES, page_guide
from .theme import apply_theme
from .result_views import angle_summary, distance_summary, movement_summary, comparison_summary, calibration_summary


class MainWindow(QMainWindow):
    def __init__(self, project=None):
        super().__init__()
        self.project = project or Project()
        self.project_path = None
        self.frame = None
        self.setWindowTitle("Type 2AB — Custom PCB External Calibration")
        self.resize(1350, 900)
        self.tabs = QTabWidget()
        self.tabs.tabBar().hide()
        self.build_shell()
        self.pages = {}
        for name in ["Project", "Import Data", "Raw Data", "Fixed Angle Analysis", "Distance / Antenna Delay", "Movement Analysis", "EVB vs Custom Comparison", "Calibration Results", "Export"]:
            widget = QWidget()
            layout = QVBoxLayout(widget)
            self.tabs.addTab(widget, name)
            self.pages[name] = layout
        self.tabs.currentChanged.connect(self.page_changed)
        self.navigation.currentRowChanged.connect(self.tabs.setCurrentIndex)
        self.navigation.setCurrentRow(0)
        self.page_changed(0)
        apply_theme(self)
        self.build_project()
        self.build_import()
        self.build_raw()
        self.build_analysis()
        self.build_export()
        self.filter.setCurrentText(self.project.settings["filter"])
        self.method.setCurrentText(self.project.settings["interpolation"])
        self.refresh_metadata()
        self.refresh_datasets()
        if any(d.enabled and d.records for d in self.project.datasets):
            self.run_analysis()

    def build_shell(self):
        root = QWidget()
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)
        sidebar = QWidget()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(215)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(15, 24, 15, 18)
        brand = QLabel('UWB\nCalibration Studio')
        brand.setObjectName('brand')
        side.addWidget(brand)
        sub = QLabel('RF DIAGNOSTICS  /  TYPE 2AB')
        sub.setObjectName('brandSub')
        side.addWidget(sub)
        side.addSpacing(20)
        self.navigation = QListWidget()
        self.navigation.setObjectName('navigation')
        for i, name in enumerate(PAGE_GUIDES, 1):
            short = {'Distance / Antenna Delay': 'Distance & delay', 'EVB vs Custom Comparison': 'EVB vs custom', 'Fixed Angle Analysis': 'Fixed angle', 'Movement Analysis': 'Movement', 'Calibration Results': 'Results'}.get(name, name)
            self.navigation.addItem(f'{i:02d}   {short}')
        side.addWidget(self.navigation, 1)
        self.session_summary = QLabel('No captures loaded\nStart a project or try the demo.')
        self.session_summary.setObjectName('sidebarNote')
        self.session_summary.setWordWrap(True)
        side.addWidget(self.session_summary)
        note = QLabel('DUAL ANTENNA\nExternal PCB calibration\nLocal files • Offline analysis')
        note.setObjectName('sidebarNote')
        side.addWidget(note)
        shell.addWidget(sidebar)
        workspace = QWidget()
        workspace.setObjectName('workspace')
        column = QVBoxLayout(workspace)
        column.setContentsMargins(16, 12, 16, 12)
        heading = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        self.page_title = QLabel()
        self.page_title.setObjectName('pageTitle')
        self.page_subtitle = QLabel()
        self.page_subtitle.setObjectName('pageSubtitle')
        titles.addWidget(self.page_title)
        titles.addWidget(self.page_subtitle)
        heading.addLayout(titles, 1)
        self.mode_badge = QLabel('OFFLINE')
        self.mode_badge.setObjectName('badge')
        heading.addWidget(self.mode_badge)
        guide_button = QPushButton('Working guide')
        guide_button.clicked.connect(self.toggle_guide)
        heading.addWidget(guide_button)
        column.addLayout(heading)
        column.addWidget(self.tabs, 1)
        shell.addWidget(workspace, 1)
        self.setCentralWidget(root)
        self.guide_dock = QDockWidget('Working guide — this page', self)
        self.guide_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.guide_dock.setMinimumWidth(300)
        self.guide_browser = QTextBrowser()
        self.guide_browser.setOpenExternalLinks(False)
        self.guide_dock.setWidget(self.guide_browser)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.guide_dock)
        self.guide_dock.hide()

    def page_changed(self, index):
        if index < 0:
            return
        name = self.tabs.tabText(index)
        self.page_title.setText(name)
        self.page_subtitle.setText(PAGE_GUIDES[name][0])
        self.guide_browser.setHtml(page_guide(name))
        self.guide_dock.setWindowTitle('Working guide — ' + name)
        if self.navigation.currentRow() != index:
            self.navigation.setCurrentRow(index)

    def toggle_guide(self):
        self.guide_dock.setVisible(not self.guide_dock.isVisible())

    def update_session_summary(self):
        active = [d for d in self.project.datasets if d.enabled]
        self.session_summary.setText(f'{len(active)} enabled captures\n{sum(len(d.records) for d in active):,} measurements\n' + ('Synthetic demonstration' if self.project.metadata.get('synthetic') else 'Your measured data'))
        self.mode_badge.setText('SYNTHETIC DEMO' if self.project.metadata.get('synthetic') else 'OFFLINE • LOCAL')

    def action(self, layout, text, callback):
        button = QPushButton(text)
        button.setProperty('primary', text.startswith(('Run Analysis', 'Angle Capture', 'Save Project', 'Engineering HTML')))
        button.clicked.connect(lambda: self.guard(callback))
        layout.addWidget(button)
        return button

    def guard(self, callback):
        try:
            callback()
        except Exception as error:
            QMessageBox.warning(self, "Calibration tool", str(error))

    def build_project(self):
        layout = self.pages["Project"]
        self.banner = QLabel()
        layout.addWidget(self.banner)
        form = QFormLayout()
        self.metadata_fields = {}
        for key in self.project.metadata:
            if key == "synthetic":
                continue
            edit = QLineEdit()
            form.addRow(key.replace("_", " ").title(), edit)
            self.metadata_fields[key] = edit
        layout.addLayout(form)
        for text, callback in [("New Project", self.new_project), ("Load Project", self.load_project), ("Save Project", self.save_project), ("Load Demo Project (replaces current workspace)", self.load_demo)]:
            self.action(layout, text, callback)
        layout.addStretch()

    def collect_metadata(self):
        self.project.metadata.update({key: edit.text() for key, edit in self.metadata_fields.items()})

    def refresh_metadata(self):
        for key, edit in self.metadata_fields.items():
            edit.setText(str(self.project.metadata.get(key, "")))
        self.banner.setText("SYNTHETIC TEST DATA — do not mix with user measurements" if self.project.metadata.get("synthetic") else "Offline analysis. Raw powers are NOT dBm. No firmware/OTP programming.")
        self.update_session_summary()

    def new_project(self):
        self.project = Project()
        self.project_path = None
        self.reset_view()

    def reset_view(self):
        self.frame = None
        self.refresh_metadata()
        self.refresh_datasets()
        self.filter.setCurrentText(self.project.settings["filter"])
        self.method.setCurrentText(self.project.settings["interpolation"])
        self.raw_model.clear()
        for edit in self.text_views.values():
            edit.clear()
        for plots in self.plot_tabs.values():
            self.clear_plots(plots)

    def load_demo(self):
        self.project = demo_project()
        self.project_path = None
        self.reset_view()
        self.run_analysis()

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load calibration project", "", "Project (*.json)")
        if path:
            self.project = Project.load(path)
            self.project_path = path
            self.reset_view()
            self.run_analysis()

    def save_project(self):
        self.collect_metadata()
        if self.project.datasets:
            self.run_analysis()
        path, _ = QFileDialog.getSaveFileName(self, "Save calibration project", "project.json", "JSON (*.json)")
        if path:
            self.project.save(path)
            self.project_path = path

    def build_import(self):
        layout = self.pages["Import Data"]
        form = QFormLayout()
        self.kind = QComboBox()
        self.kind.addItems(["angle", "distance", "movement"])
        self.label = QComboBox()
        self.label.addItems(["EVB-CUSTOM", "EVB-EVB"])
        self.angle = QDoubleSpinBox()
        self.angle.setRange(-180, 180)
        self.distance = QDoubleSpinBox()
        self.distance.setRange(0.001, 10000)
        self.distance.setDecimals(3)
        self.distance.setValue(2)
        self.range_scale = QLineEdit()
        self.range_scale.setPlaceholderText("Optional explicit metres per header code; blank = opaque")
        for title, widget in [("Dataset type", self.kind), ("Setup", self.label), ("Known angle (deg)", self.angle), ("Known distance (m)", self.distance), ("Header range scale (m/code)", self.range_scale)]:
            form.addRow(title, widget)
        layout.addLayout(form)
        self.action(layout, 'Angle Capture Checklist (-180 to +180) / Prepare Final Results', self.open_angle_sweep)
        self.action(layout, "Import RF diagnostic text / CSV", self.import_file)
        layout.addWidget(QLabel("CSV columns: pdoa_deg, tdoa_raw, measured_distance_m and optional diagnostic fields.\nSelect a dataset to attach an ordered distance list. Edit enabled, angle, distance or label directly below."))
        self.dataset_table = QTableWidget(0, 7)
        self.dataset_table.setHorizontalHeaderLabels(["Enabled", "Name", "Type", "Setup", "True angle", "True distance", "Samples"])
        self.dataset_table.itemChanged.connect(self.dataset_changed)
        layout.addWidget(self.dataset_table)
        self.action(layout, "Attach measured distances (CSV/list) to selected dataset", self.attach_distances)
        self.action(layout, "Enter one measured distance for selected dataset", self.manual_distance)
        self.action(layout, "Remove selected dataset", self.remove_dataset)

    def open_angle_sweep(self):
        from .sweep_dialog import AngleSweepDialog
        AngleSweepDialog(self).exec()

    def import_file(self):
        if self.project.metadata.get("synthetic"):
            raise ValueError("Create or load a real project before importing user measurements. Demo data cannot be mixed with user data.")
        path, _ = QFileDialog.getOpenFileName(self, "Import log", "", "Logs (*.txt *.log *.csv);;All files (*)")
        if not path:
            return
        scale = float(self.range_scale.text()) if self.range_scale.text().strip() else None
        if scale is not None and (not np.isfinite(scale) or scale <= 0):
            raise ValueError("Header scale must be a positive finite metres-per-code value.")
        records, warnings = parse_file(path, scale)
        if not records:
            raise ValueError("No recognizable measurements were found in this file.")
        kind = self.kind.currentText()
        name = Path(path).stem
        existing = {d.name for d in self.project.datasets}
        suffix = 2
        while name in existing:
            name = f"{Path(path).stem} ({suffix})"
            suffix += 1
        self.project.datasets.append(Dataset(name, records, kind=kind, label=self.label.currentText(), true_angle_deg=self.angle.value() if kind == "angle" else None, true_distance_m=self.distance.value() if kind != "movement" else None, source=path, warnings=warnings, source_text=Path(path).read_text(encoding='utf-8-sig', errors='replace')))
        self.refresh_datasets()
        self.run_analysis()
        if warnings:
            QMessageBox.information(self, "Import warnings", "\n".join(warnings[:8]))

    def refresh_datasets(self):
        table = self.dataset_table
        table.blockSignals(True)
        table.setRowCount(len(self.project.datasets))
        for row, d in enumerate(self.project.datasets):
            enabled = QTableWidgetItem()
            enabled.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable)
            enabled.setCheckState(Qt.CheckState.Checked if d.enabled else Qt.CheckState.Unchecked)
            table.setItem(row, 0, enabled)
            for column, value in enumerate([d.name, d.kind, d.label, d.true_angle_deg, d.true_distance_m, len(d.records)], 1):
                item = QTableWidgetItem("" if value is None else str(value))
                if column in [1, 2, 6]:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(row, column, item)
        table.resizeColumnsToContents()
        table.setAlternatingRowColors(True)
        table.blockSignals(False)
        self.update_session_summary()

    def dataset_changed(self, item):
        def change():
            d = self.project.datasets[item.row()]
            column = item.column()
            if column == 0:
                d.enabled = item.checkState() == Qt.CheckState.Checked
            elif column == 3:
                if item.text() not in ["EVB-EVB", "EVB-CUSTOM"]:
                    raise ValueError("Setup must be EVB-EVB or EVB-CUSTOM.")
                d.label = item.text()
            elif column in [4, 5]:
                value = float(item.text()) if item.text() else None
                if value is not None and (not np.isfinite(value) or (column == 5 and value <= 0)):
                    raise ValueError("Assignments must be finite; distance must be positive.")
                setattr(d, "true_angle_deg" if column == 4 else "true_distance_m", value)
            self.project.results = {}
            self.frame = None
        self.guard(change)
        self.refresh_datasets()

    def selected_dataset(self):
        row = self.dataset_table.currentRow()
        if row < 0:
            raise ValueError("Select a dataset first.")
        return self.project.datasets[row]

    def attach_distances(self):
        import pandas as pd
        d = self.selected_dataset()
        path, _ = QFileDialog.getOpenFileName(self, "Ordered measured distances", "", "CSV or list (*.csv *.txt)")
        if not path:
            return
        if Path(path).suffix.lower() == ".csv":
            values = pd.read_csv(path)["measured_distance_m"].tolist()
        else:
            values = [float(v) for v in Path(path).read_text().replace(",", " ").split()]
        if len(values) != len(d.records) or not all(np.isfinite(v) and v >= 0 for v in values):
            raise ValueError("Provide one finite nonnegative measured distance per record, in acquisition order.")
        for record, value in zip(d.records, values):
            record["measured_distance_m"] = float(value)
        self.run_analysis()

    def manual_distance(self):
        d = self.selected_dataset()
        value, ok = QInputDialog.getDouble(self, "Measured distance", "Measured metres (applied to every record; SD cannot be assessed from this constant)", 2, 0, 10000, 4)
        if ok:
            for record in d.records:
                record["measured_distance_m"] = value
            d.warnings.append("Measured range manually assigned as a constant; this cannot establish measurement stability.")
            self.run_analysis()

    def remove_dataset(self):
        d = self.selected_dataset()
        self.project.datasets.remove(d)
        self.reset_view()
        if self.project.datasets:
            self.run_analysis()

    def build_raw(self):
        layout = self.pages["Raw Data"]
        search = QLineEdit()
        search.setPlaceholderText("Filter any column")
        layout.addWidget(search)
        self.raw_model = QStandardItemModel()
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.raw_model)
        self.proxy.setFilterKeyColumn(-1)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        search.textChanged.connect(self.proxy.setFilterFixedString)
        self.raw_table = QTableView()
        self.raw_table.setModel(self.proxy)
        self.raw_table.setSortingEnabled(True)
        self.raw_table.setAlternatingRowColors(True)
        layout.addWidget(self.raw_table)

    def build_analysis(self):
        self.text_views, self.plot_tabs = {}, {}
        settings_layout = self.pages["Fixed Angle Analysis"]
        row = QHBoxLayout()
        self.filter = QComboBox()
        self.filter.addItems(["MAD", "IQR", "None"])
        self.method = QComboBox()
        self.method.addItems(["linear", "pchip"])
        self.filter.setToolTip("Choose how unusually far-away readings are flagged. See the explanation below.")
        self.method.setToolTip("Choose how the lookup estimates angles between measured points. See the explanation below.")
        row.addWidget(QLabel("Filter")); row.addWidget(self.filter)
        row.addWidget(QLabel("Interpolation")); row.addWidget(self.method)
        settings_layout.addLayout(row)
        self.settings_help = QTextBrowser()
        self.settings_help.setMinimumHeight(58)
        self.settings_help.setMaximumHeight(76)
        settings_layout.addWidget(self.settings_help)
        self.show_settings_help = QCheckBox("Show explanations and current values for all settings (scroll in the description)")
        settings_layout.addWidget(self.show_settings_help)
        self.show_settings_help.toggled.connect(self.refresh_settings_help)
        self.filter.currentTextChanged.connect(self.refresh_settings_help)
        self.method.currentTextChanged.connect(self.refresh_settings_help)
        self.refresh_settings_help()
        actions = QHBoxLayout()
        self.action(actions, "Edit project-specific settings", self.edit_settings)
        self.action(actions, "Run Analysis / Refresh All Pages", self.run_analysis)
        settings_layout.addLayout(actions)
        for name in ["Fixed Angle Analysis", "Distance / Antenna Delay", "Movement Analysis", "EVB vs Custom Comparison", "Calibration Results"]:
            view = QTextEdit()
            view.setReadOnly(True)
            self.text_views[name] = view
            if name in ["Fixed Angle Analysis", "Distance / Antenna Delay", "Movement Analysis"]:
                # Plots and long statistics must not compete for vertical space.
                content = QTabWidget()
                plots = QTabWidget()
                plots.setUsesScrollButtons(True)
                plots.tabBar().setExpanding(False)
                content.addTab(plots, 'Plots')
                content.addTab(view, 'Statistics / details')
                self.pages[name].addWidget(content, 1)
                self.plot_tabs[name] = plots
            else:
                self.pages[name].addWidget(view)

    def refresh_settings_help(self, *_):
        self.settings_help.setMaximumHeight(170 if self.show_settings_help.isChecked() else 76)
        self.settings_help.setHtml(settings_description(self.project.settings, self.filter.currentText(), self.method.currentText(), self.show_settings_help.isChecked()))

    def edit_settings(self):
        current_settings = dict(self.project.settings, filter=self.filter.currentText(), interpolation=self.method.currentText())
        text, ok = QInputDialog.getMultiLineText(self, "Project-specific criteria (NOT Murata specifications)", "The description on Fixed Angle Analysis explains every setting. Edit values below, keeping the setting names. Signed TDoA width defaults to 41; reference sign must be +1 or -1.", json.dumps(current_settings, indent=2))
        if ok:
            settings = json.loads(text)
            if set(settings) != set(self.project.settings):
                raise ValueError("Keep all existing setting keys.")
            for key, value in settings.items():
                if key not in ["filter", "interpolation", "reference_sign"] and (not isinstance(value, (float, int)) or not np.isfinite(value) or value <= 0):
                    raise ValueError(f"{key} must be a positive finite number.")
            if settings["reference_sign"] not in [-1, 1] or not isinstance(settings["tdoa_bits"], int) or not 2 <= settings["tdoa_bits"] <= 64:
                raise ValueError("Invalid reference sign or TDoA field width.")
            if settings["filter"] not in ["MAD", "IQR", "None"] or settings["interpolation"] not in ["linear", "pchip"]:
                raise ValueError("Unsupported filter or interpolation.")
            if settings["imbalance_notice"] <= 1 or settings["imbalance_large"] <= settings["imbalance_notice"]:
                raise ValueError("Power ratio thresholds must satisfy 1 < noticeable < large.")
            self.project.settings = settings
            self.filter.setCurrentText(settings["filter"])
            self.method.setCurrentText(settings["interpolation"])
            self.refresh_settings_help()
            self.run_analysis()

    def clear_plots(self, tabs):
        while tabs.count():
            widget = tabs.widget(0)
            tabs.removeTab(0)
            widget.deleteLater()

    def run_analysis(self):
        self.collect_metadata()
        self.project.settings["filter"] = self.filter.currentText()
        self.project.settings["interpolation"] = self.method.currentText()
        self.refresh_settings_help()
        self.frame, result = analyze(self.project)
        self.raw_model.clear()
        columns = list(self.frame.columns)
        self.raw_model.setHorizontalHeaderLabels(columns)
        for values in self.frame.itertuples(index=False, name=None):
            items = []
            for value in values:
                item = QStandardItem()
                item.setEditable(False)
                item.setData(value if isinstance(value, (str, int, float, bool)) else str(value), Qt.ItemDataRole.DisplayRole)
                items.append(item)
            self.raw_model.appendRow(items)
        self.text_views['Fixed Angle Analysis'].setHtml(angle_summary(result))
        self.text_views['Distance / Antenna Delay'].setHtml(distance_summary(result.get('range')))
        self.text_views['Movement Analysis'].setHtml(movement_summary(result['movements']))
        self.text_views['EVB vs Custom Comparison'].setHtml(comparison_summary(result['comparison']))
        self.text_views['Calibration Results'].setHtml(calibration_summary(result))
        for tabs in self.plot_tabs.values():
            self.clear_plots(tabs)
        for index, (title, figure) in enumerate(figures(self.frame, result)):
            page = "Fixed Angle Analysis" if index < 7 else "Distance / Antenna Delay" if index < 9 else "Movement Analysis"
            widget = QWidget()
            layout = QVBoxLayout(widget)
            canvas = FigureCanvasQTAgg(figure)
            canvas.setMinimumHeight(220)
            layout.addWidget(NavigationToolbar2QT(canvas, self))
            layout.addWidget(canvas, 1)
            from html import escape
            explanation = QLabel('<b>How to read:</b> ' + escape(PLOT_GUIDES[index][1]))
            explanation.setObjectName('plotGuide')
            explanation.setWordWrap(True)
            explanation.setMaximumHeight(68)
            explanation.setToolTip(PLOT_GUIDES[index][2])
            layout.addWidget(explanation)
            short_titles = ['Raw PDoA', 'Corrected PDoA', 'PDoA spread', 'Mean TDoA', 'TDoA spread', 'STS powers', 'First-path difference', 'Measured distance', 'Range error', 'PDoA over time', 'TDoA over time', 'Range over time', 'STS powers over time', 'First paths over time']
            tab_index = self.plot_tabs[page].addTab(widget, short_titles[index])
            self.plot_tabs[page].setTabToolTip(tab_index, title)
            canvas.draw_idle()
        self.statusBar().showMessage(f"{len(self.frame)} measurements; {sum(~self.frame.valid)} rejected/missing retained. Project-specific readiness: {result['production_ready']}")
        self.update_session_summary()

    def build_export(self):
        layout = self.pages["Export"]
        layout.addWidget(QLabel("Exports contain external physical corrections only. Firmware conversion still requires documentation.\nNon-ready LUTs are engineering candidates; headers carry a readiness flag. HTML reports include all plots."))
        for text, kind in [("Full measurements CSV", "csv"), ("Calibration LUT CSV", "lut"), ("Calibration JSON", "json"), ("Firmware C header", "header"), ("Engineering HTML report", "report")]:
            self.action(layout, text, lambda k=kind: self.export(k))
        layout.addStretch()

    def export(self, kind):
        self.run_analysis()
        ext = {"csv": "csv", "lut": "csv", "json": "json", "header": "h", "report": "html"}[kind]
        path, _ = QFileDialog.getSaveFileName(self, "Export", f"calibration.{ext}", f"{ext.upper()} (*.{ext})")
        if not path:
            return
        if kind == "csv": export_csv(self.frame, path)
        elif kind == "lut": export_lut_csv(self.project.results, path)
        elif kind == "json": export_json(self.project, path)
        elif kind == "header": export_c_header(self.project.results, path)
        else: export_report(self.project, self.frame, path)
        self.statusBar().showMessage(f"Exported {path}")
