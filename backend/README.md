# Backend – Sistem AI Integrat

## Descriere
Backend Flask care expune servicii pentru:
- Analiză documente (PPT, Word/PDF/eBook, OCR imagini)
- Traducere (documente, audio, video) cu progres SSE
- Subtitrare RO + rezumat video
- Redublare video cu Whisper + TTS local
- Istoric operațiuni (SQLite)

## Instalare (recomandat Python 3.11/3.12)
```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -r requirements.txt
```

Dependențe externe:
- ffmpeg în PATH
- (opțional) Tesseract pentru OCR
- (opțional) CUDA pentru Whisper/TTS pe GPU
- (opțional) pe CPU merge, dar cu FP32 și latență mai mare (whisper emite warning FP16)

## Rulare
```bash
cd backend
source .venv/bin/activate
python app.py
```
Serverul pornește pe `http://localhost:5000`.

## Compatibilitate Ubuntu
- Funcționează pe Ubuntu cu Python 3.11/3.12 și ffmpeg instalat.
- Pentru GPU: instalează driver NVIDIA + CUDA/cuDNN compatibile cu torch; altfel rulează pe CPU.
- Evită Python 3.14 dacă vrei toate funcționalitățile (anumite dependențe se sar la install).

## Endpoint-uri principale
- `GET /api/health` – healthcheck
- `GET /api/llm-status` – status LLM extern
- `GET /api/history` – istoric operațiuni
- `POST /api/ppt-analysis`
- `POST /api/document-analysis`
- `POST /api/image-ocr`
- `POST /api/translate-document`
- `POST /api/translate-audio`
- `POST /api/translate-video`
- `POST /api/subtitle-ro`
- `POST /api/redub-video`
- `POST /api/live-start`, `POST /api/live-stop`

## Structură (scurt)
- `app.py` – Flask app, rute, SSE
- `requirements.txt` – dependențe
- `uploads/`, `processed/`, `cache/` – fișiere temporare/output
- `services/` – logică pe categorii (analiză/traducere/subtitrare/redublare)
- `history.py` – persistă istoricul în SQLite
- Căutare: `/api/history/search` face full-text search (FTS5) în service/file/meta/rezumat; rezumatele sunt indexate dacă există `summary_text/summary_url`.
- Rezumate: fișierele de rezumat generate sunt salvate în `processed/` și expuse în răspuns (download/resume).
