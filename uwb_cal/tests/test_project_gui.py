import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from uwb_cal.gui.main_window import MainWindow
from uwb_cal.demo import demo_project
from uwb_cal.analysis.engine import analyze


def test_gui_demo_and_loaded_settings():
    app = QApplication.instance() or QApplication([])
    project = demo_project()
    project.settings["filter"] = "IQR"
    project.settings["interpolation"] = "pchip"
    window = MainWindow(project)
    assert window.tabs.count() == 9
    assert window.filter.currentText() == "IQR"
    assert window.method.currentText() == "pchip"
    assert window.raw_model.rowCount() == 1960
    assert window.project.results["range"]["bias_m"] > .1
    window.resize(1280, 720)
    window.tabs.setCurrentIndex(3)
    window.show()
    app.processEvents()
    assert window.plot_tabs['Fixed Angle Analysis'].height() >= 300
    assert window.plot_tabs['Fixed Angle Analysis'].tabText(0) == 'Raw PDoA'
    for index in range(9):
        window.tabs.setCurrentIndex(index)
        assert 'What to do' in window.guide_browser.toPlainText()
        assert window.navigation.currentRow() == index
    assert 'Angle prediction accuracy' in window.text_views['Calibration Results'].toPlainText()
    window.close()
    app.processEvents()


def test_disabled_and_manual_readiness():
    project = demo_project()
    project.datasets[0].enabled = False
    frame, results = analyze(project)
    assert project.datasets[0].name not in frame.dataset_name.unique()
    assert frame.range_error_m.notna().sum() > 0
    for dataset in project.datasets:
        if dataset.kind == "distance":
            dataset.warnings.append("Measured range manually assigned as a constant")
    _, results = analyze(project)
    assert results["readiness"]["External antenna-delay calc"] != "READY (physical quantity only)"
