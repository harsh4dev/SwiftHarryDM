# SwiftHarryDM.spec (PyInstaller 6.x compatible)

from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
import os

# Helper to include entire src folder
def get_src_datas(src_folder='src'):
    datas = []
    for root, dirs, files in os.walk(src_folder):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(root, '.')  # preserve folder structure
            datas.append((full_path, rel_path))
    return datas

# Include all your legal and policy text files + src folder
datas = [
    ('EULA.txt', '.'),
    ('ATTRIBUTION.txt', '.'),
    ('LICENSE_KEY_POLICY.txt', '.'),
    ('LICENSE.txt', '.'),
    ('PRIVACY_POLICY.txt', '.'),
    ('REFUND_POLICY.txt', '.'),
    ('TERMS_AND_CONDITIONS.txt', '.'),
    ('requirements.txt', '.'),
    ('license/public.pem', 'license'),
]

# add all src files
datas += get_src_datas('src')

# Auto-detect submodules inside src
hiddenimports = collect_submodules('src')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SwiftHarryDM',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='app.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='SwiftHarryDM'
)