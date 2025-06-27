# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py', 'flask_server.py', 'gui_dev.py'],
    pathex=[],
    binaries=[('C:\\Users\\lovei\\AppData\\Local\\Programs\\Python\\Python312\\python312.dll', '.')],
    datas=[('encrypted_keys.json', '.'), ('templates', 'templates'), ('static', 'static')],
    hiddenimports=['encodings', 'encodings.*', 'flask_socketio', 'engineio', 'flask_limiter', 'limits'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SwiftSaleApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SwiftSaleApp',
)
