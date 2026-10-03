# Build a standalone Windows executable: python -m PyInstaller UWB_Calibration.spec
from pathlib import Path

root = Path(SPECPATH)
a = Analysis(
    [str(root / 'main.py')],
    pathex=[str(root)],
    binaries=[],
    datas=[(str(root / 'README.md'), '.'), (str(root / 'examples'), 'examples')],
    hiddenimports=['matplotlib.backends.backend_qtagg'],
    hookspath=[],
    hooksconfig={'matplotlib': {'backends': ['QtAgg']}},
    runtime_hooks=[],
    excludes=['pytest', 'tkinter', 'PyQt5', 'PyQt6', 'PySide2'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name='UWB_Calibration',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)
