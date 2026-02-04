# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

app_name = "RDR2_L10N_Tool"

hiddenimports = []
hiddenimports += collect_submodules("PySide6")

datas = []
# Ако имаш някакви data файлове (templates/lang/etc), добавяш ги тук.
# Пример: datas += [("templates", "templates")]

# PySide6 си дърпа Qt plugin-и сам, но понякога е полезно да се collect-нат данни:
datas += collect_data_files("PySide6", include_py_files=False)

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # GUI app
    icon="assets/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name=app_name,
)
