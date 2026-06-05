# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Lab Receipt System (نظام إدارة الاستلام المختبري).

Build EXE:
    pyinstaller lab_system.spec

Build with console for debugging:
    pyinstaller --debug all lab_system.spec
"""

import sys
from pathlib import Path

BLOCK_CIPHER_LIST = None

a = Analysis(
    ['main.py'],
    pathex=[str(Path.cwd())],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('VERSION', '.'),
    ],
    hiddenimports=[
        'lab_system.app.ui.app',
        'lab_system.app.ui.receipts_page',
        'lab_system.app.ui.receipt_dialog',
        'lab_system.app.ui.receipt_detail_dialog',
        'lab_system.app.ui.org_page',
        'lab_system.app.ui.users_page',
        'lab_system.app.ui.reports_page',
        'lab_system.app.ui.settings_page',
        'lab_system.app.ui.audit_page',
        'lab_system.app.ui.backup_page',
        'lab_system.app.database.db',
        'lab_system.app.services.auth_service',
        'lab_system.app.services.backup_service',
        'lab_system.app.services.catalog_service',
        'lab_system.app.services.org_service',
        'lab_system.app.services.receipt_service',
        'lab_system.app.services.recovery_service',
        'lab_system.app.services.report_service',
        'lab_system.app.services.seed_service',
        'lab_system.app.services.user_service',
        'lab_system.app.printing.receipt_pdf',
        'lab_system.app.attachments.manager',
        'lab_system.app.audit.logger',
        'lab_system.app.sync.service',
        'lab_system.app.sync.api_client',
        'lab_system.app.sync.device',
        'lab_system.app.diagnostics.startup',
        'lab_system.app.settings.config',
        'lab_system.app.utils.constants',
        'lab_system.app.utils.errors',
        'lab_system.app.utils.logging',
        'lab_system.app.utils.validators',
        'lab_system.app.auth.permissions',
        'lab_system.app.auth.security',
        'lab_system.app.database.connection',
        'lab_system.app.services.base_service',
        'sqlite3',
        'bcrypt',
        'reportlab',
        'reportlab.pdfbase',
        'reportlab.pdfbase.ttfonts',
        'qrcode',
        'barcode',
        'barcode.writer',
        'PIL',
        'PIL._imaging',
        'openpyxl',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'cv2',
        'transformers',
        'torch',
        'tensorflow',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='LabReceiptSystem',
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
    icon='assets/icons/app.ico',
)


