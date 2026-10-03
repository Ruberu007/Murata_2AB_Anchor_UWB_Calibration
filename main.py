import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="Offline Type 2AB external PCB calibration")
    parser.add_argument("--demo", action="store_true", help="Load SYNTHETIC TEST DATA")
    parser.add_argument("--project", help="Load local project JSON")
    parser.add_argument("--smoke-test", action="store_true", help="Launch, analyze demo, then exit automatically")
    args = parser.parse_args()
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    from uwb_cal.gui.main_window import MainWindow
    from uwb_cal.demo import demo_project
    from uwb_cal.models.measurement import Project
    app = QApplication(sys.argv)
    project = Project.load(args.project) if args.project else demo_project() if args.demo or args.smoke_test else Project()
    window = MainWindow(project)
    window.show()
    if args.smoke_test:
        assert window.frame is not None and len(window.frame) > 0
        assert window.project.results["lut"]
        QTimer.singleShot(1000, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
