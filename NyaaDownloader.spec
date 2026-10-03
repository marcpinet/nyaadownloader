# PyInstaller build: `pyinstaller NyaaDownloader.spec` → dist/NyaaDownloader.exe
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = [("nyaadownloader/assets", "nyaadownloader/assets")]
datas += collect_data_files("PTT")  # keyword lists loaded at runtime

a = Analysis(
    ["nyaadownloader/__main__.py"],
    pathex=["."],
    datas=datas,
    hiddenimports=collect_submodules("PTT") + ["winotify"],
    excludes=["tkinter", "PIL", "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtWebEngineCore", "PySide6.QtPdf"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="NyaaDownloader",
    console=False,
    upx=False,
    icon="nyaadownloader/assets/nyaa.ico",
)
