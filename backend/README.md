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

## Rulare
```bash
cd backend
source .venv/bin/activate
python app.py
```
Serverul pornește pe `http://localhost:5000`.

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
