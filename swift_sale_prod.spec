# swift_sale_prod.spec

import os
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

block_cipher = None
project_dir = os.getcwd()

# ─── Hidden imports ────────────────────────────────────────────────────────────
hiddenimports = (
    collect_submodules('flask_socketio')
    + collect_submodules('engineio')
    + collect_submodules('flask_limiter')
    + collect_submodules('limits')
    + collect_submodules('limits.storage')
    + [
        'simple_websocket',
        'engineio.async_drivers.threading',
        'engineio.async_drivers.eventlet',
        'engineio.async_drivers.gevent',
        'engineio.async_drivers.gevent_uwsgi',
        'engineio.async_drivers.aiohttp',
        'engineio.async_drivers.sanic',
        'engineio.async_drivers.tornado',
        'gevent',
        'geventwebsocket',
        'eventlet',
        'stripe_service',
        'database',
        'config',
        'gui_dev',
        'waitress',
        'stripe',
        'tkinter',
        'limits.storage.memory',
        'limits.strategies',
        'limits.util',
        # ─── Newly added for the latest updates ────────────────────────────────
        'bidder_manager',
        'telegram_service',
        'PIL',
        'PyPDF2',
        'reportlab'
    ]
)

# ─── Data files ────────────────────────────────────────────────────────────────
basic_files = [
    'cert.pem',
    'key.pem',
    'fernet.key',
    'bidders.db',        # freshly-shipped, empty bidders.db
    'swiftsale_logo.png',
    'swiftsale_logo.ico',
    'ngrok.exe'
]

datas = []
for fname in basic_files:
    fpath = os.path.join(project_dir, fname)
    if os.path.exists(fpath):
        datas.append((fpath, '.'))

# ─── Templates ─────────────────────────────────────────────────────────────────
templates_dir = os.path.join(project_dir, 'templates')
if os.path.isdir(templates_dir):
    for root, _, files in os.walk(templates_dir):
        rel = os.path.relpath(root, project_dir)
        for f in files:
            if f.lower().endswith('.html'):
                datas.append((os.path.join(root, f), rel))

# ─── Static assets ─────────────────────────────────────────────────────────────
static_dir = os.path.join(project_dir, 'static')
if os.path.isdir(static_dir):
    for root, _, files in os.walk(static_dir):
        rel = os.path.relpath(root, project_dir)
        for f in files:
            datas.append((os.path.join(root, f), rel))

# New “helper EXE” block: bundle into dist\SwiftSaleApp\helpers\DoubleClickCopy.exe
helper_src = os.path.join(project_dir, 'helpers', 'DoubleClickCopy.exe')
if os.path.exists(helper_src):
    datas.append((helper_src, 'helpers'))


# ─── Analysis ─────────────────────────────────────────────────────────────────
a = Analysis(
    ['main.py', 'flask_server.py', 'gui_dev.py'],
    pathex=[project_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

# ─── PYZ ────────────────────────────────────────────────────────────────────────
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ─── EXE ────────────────────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],  # no additional binaries
    exclude_binaries=True,
    name='SwiftSaleApp_3.1',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon=os.path.join(project_dir, 'swiftsale_logo.ico'),
)

# ─── COLLECT ────────────────────────────────────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='SwiftSaleApp'
)
