# SwiftHarryDM.spec - STANDALONE SINGLE EXE

from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE
import os
import sys

def get_all_datas():
    datas = []
    
    # Include all text files
    text_files = [
        'EULA.txt', 'ATTRIBUTION.txt', 'LICENSE_KEY_POLICY.txt', 
        'LICENSE.txt', 'PRIVACY_POLICY.txt', 'REFUND_POLICY.txt',
        'TERMS_AND_CONDITIONS.txt', 'requirements.txt'
    ]
    
    for txt_file in text_files:
        if os.path.exists(txt_file):
            datas.append((txt_file, '.'))
    
    # Include src folder
    for root, dirs, files in os.walk('src'):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(root, '.')
            datas.append((full_path, rel_path))
    
    # Include ffmpeg binaries INSIDE the exe
    if os.path.exists('ffmpeg.exe'):
        datas.append(('ffmpeg.exe', '.'))
    if os.path.exists('ffprobe.exe'):
        datas.append(('ffprobe.exe', '.'))
    
    # Include app icon
    if os.path.exists('app.ico'):
        datas.append(('app.ico', '.'))
    
    return datas

# Collect all hidden imports
hiddenimports = collect_submodules('src')
hiddenimports += [
    'downloader',
    'youtube_downloader', 
    'vimeo_downloader',
    'dailymotion_downloader',
    'playlist_downloader',
    'utils',
    'download_window',
    'yt_dlp',
    'flask',
    'flask_cors',
    'yt_dlp.extractor',
    'yt_dlp.postprocessor',
    'yt_dlp.downloader',
    'pkg_resources',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=get_all_datas(),
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SwiftHarryDM',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app.ico',
)