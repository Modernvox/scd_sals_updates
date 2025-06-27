# hook-flask_limiter.py
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = (
    collect_submodules('flask_limiter') +
    collect_submodules('limits') +
    collect_submodules('limits.storage') +
    [
        'limits.storage.memory',
        'limits.strategies',
        'limits.util'
    ]
)
datas = collect_data_files('flask_limiter') + collect_data_files('limits')