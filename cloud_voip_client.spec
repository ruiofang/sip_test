# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['cloud_voip_client.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('client_config.json', '.'),  # 包含配置文件
    ],
    hiddenimports=[
        'pyaudio',
        'wave',
        'threading',
        'socket',
        'json',
        'struct',
        'uuid',
        'argparse',
        'warnings',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CloudVoIPClient',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 保留控制台窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None  # 可以添加图标文件路径
)
