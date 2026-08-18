# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Print Recovery MVP
# Build on Windows:  pyinstaller packaging/windows/print-recovery.spec

block_cipher = None

a = Analysis(
    ['../../app.py'],
    pathex=['../..'],
    binaries=[],
    datas=[
        ('../../templates', 'templates'),
        ('../../docs/target-contracts', 'docs/target-contracts'),
        ('../../config.example.json', '.'),
    ],
    hiddenimports=[
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'werkzeug.security',
        'adapters',
        'checkpoint_confidence',
        'config',
        'coordinate_conversion',
        'crash_report',
        'evidence_bundle',
        'interruption_classification',
        'job_manifest',
        'lifecycle_observer',
        'logging_utils',
        'migrations',
        'offline_mode',
        'orientation_validation',
        'output_naming',
        'readiness_summary',
        'recovery_report',
        'recovery_safety',
        'registration_strip',
        'secrets_store',
        'signal_matrix',
        'event_replay',
        'backup_restore',
        'printer_contract',
        'rip_observer',
        'rip_path_contract',
        'synthetic_interruptions',
        'trace_archive',
        'trace_index',
        'upgrade_backup',
        'release_review',
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
    [],
    exclude_binaries=True,
    name='PrintRecovery',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,          # Keep console so logs are visible; change to False for pure GUI feel
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,             # Add path to .ico later if desired
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PrintRecovery',
)
