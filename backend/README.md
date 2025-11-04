backend/
│
├── app.py                          # 🔥 Flask App Principal (API Gateway)
├── config.py                       # ⚙️ Configurări globale
├── requirements.txt                # 📦 Dependențe Python
├── .env                           # 🔐 Variabile de mediu
│
├── uploads/                       # 📤 Fișiere încărcate temporar
├── processed/                     # ✅ Fișiere procesate (output)
├── cache/                         # 💾 Cache pentru modele AI
│
├── routes/                        # 🛣️ API Routes (organizate pe categorii)
│   ├── __init__.py
│   ├── category_i_routes.py      # Categoria I: Analiză documente
│   ├── category_ii_routes.py     # Categoria II: Traducere
│   ├── category_iii_routes.py    # Categoria III: Subtitrare
│   └── category_iv_routes.py     # Categoria IV: Live subtitle
│
├── services/                      # 🔧 Servicii de procesare (logica business)
│   ├── __init__.py
│   │
│   ├── category_i/               # 🟦 Categoria I
│   │   ├── __init__.py
│   │   ├── ppt_analyzer.py       # I.1: PowerPoint
│   │   ├── document_parser.py    # I.2: Word/PDF/eBook
│   │   └── image_ocr.py          # I.3: OCR imagini
│   │
│   ├── category_ii/              # 🟪 Categoria II
│   │   ├── __init__.py
│   │   ├── document_translator.py # II.1: Traducere documente
│   │   ├── audio_translator.py    # II.2: Traducere audio
│   │   └── video_translator.py    # II.3: Traducere video
│   │
│   ├── category_iii/             # 🟩 Categoria III
│   │   ├── __init__.py
│   │   ├── subtitle_generator.py  # III.1: Subtitrare RO→RO
│   │   └── video_redubber.py      # III.2: Redublare video
│   │
│   ├── category_iv/              # 🟧 Categoria IV
│   │   ├── __init__.py
│   │   └── live_subtitle.py       # IV: Live subtitle RO↔RU
│   │
│   └── shared/                   # 🔄 Servicii comune
│       ├── __init__.py
│       ├── whisper_ro.py         # Transcriere Whisper RO
│       ├── vosk_transcriber.py   # Transcriere multilingvă
│       ├── translator.py         # Traducere text
│       ├── tts_engine.py         # Text-to-Speech
│       ├── subtitle_attacher.py  # Atașare subtitrări
│       └── file_utils.py         # Utilități fișiere
│
├── models/                       # 🗄️ Modele de date (opțional - pentru DB)
│   ├── __init__.py
│   └── document.py
│
├── utils/                        # 🛠️ Funcții auxiliare
│   ├── __init__.py
│   ├── validators.py             # Validare input
│   ├── error_handlers.py         # Gestionare erori
│   └── response_builder.py       # Construire răspunsuri
│
└── tests/                        # ✅ Teste unitare
    ├── __init__.py
    ├── test_category_i.py
    ├── test_category_ii.py
    ├── test_category_iii.py
    └── test_category_iv.py