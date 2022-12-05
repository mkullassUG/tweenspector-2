# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ["MainApplication.py"],
    pathex=["../venv/Lib/site-packages"],
    binaries=[],
    datas=[
        (
            "C:\\Users\\Admin\\Uniwersytet_s2\\sem1\\ProjZesp\\local\\tweenspector\\venv\\Lib\\site-packages\\pl_core_news_lg",
            "pl_core_news_lg"
        ),
        (
            "C:\\Users\\Admin\\Uniwersytet_s2\\sem1\\ProjZesp\\local\\tweenspector\\venv\\Lib\\site-packages\\pl_core_news_lg-3.3.0.dist-info",
            "pl_core_news_lg-3.3.0.dist-info"
        ),
        (
            "C:\\Users\\Admin\\Uniwersytet_s2\\sem1\\ProjZesp\\local\\tweenspector\\venv\\Lib\\site-packages\\pycairo-1.21.0.dist-info",
            "pycairo-1.21.0.dist-info"
        ),
        (
            "C:\\Users\\Admin\\Uniwersytet_s2\\sem1\\ProjZesp\\local\\tweenspector\\venv\\Lib\\site-packages\\pycares-4.2.2.dist-info",
            "pycares-4.2.2.dist-info"
        ),
        (
            "C:\\Users\\Admin\\Uniwersytet_s2\\sem1\\ProjZesp\\local\\tweenspector\\venv\\Lib\\site-packages\\pycparser",
            "pycparser"
        ),
        (
            "C:\\Users\\Admin\\Uniwersytet_s2\\sem1\\ProjZesp\\local\\tweenspector\\venv\\Lib\\site-packages\\pycparser-2.21.dist-info",
            "pycparser-2.21.dist-info"
        ),
        (
            "C:\\Users\\Admin\\Uniwersytet_s2\\sem1\\ProjZesp\\local\\tweenspector\\venv\\Lib\\site-packages\\cairo",
            "cairo"
        )
    ],
    hiddenimports=[
        "babel.numbers",
        "pl_core_news_lg",
        "pl_core_news_lg-3.3.0.dist-info",
        "spacy-model-pl_core_news_lg",
        "pycairo",
        "pycairo-1.21.0.dist-info",
        "pycares",
        "pycares-4.2.2.dist-info",
        "pycparser",
        "pycparser-2.21.dist-info"
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
a.datas += [
    (
        "wordcloud\\stopwords",
        "C:\\Users\\Admin\\Uniwersytet_s2\\sem1\\ProjZesp\\local\\tweenspector\\venv\\Lib\\site-packages\\wordcloud\\stopwords",
        "DATA"
    ),
    (
        "wordcloud\\DroidSansMono.ttf",
        "C:\\Users\\Admin\\Uniwersytet_s2\\sem1\\ProjZesp\\local\\tweenspector\\venv\\Lib\\site-packages\\wordcloud\\DroidSansMono.ttf",
        "DATA"
    )
]
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MainApplication',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
