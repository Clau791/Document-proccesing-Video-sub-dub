# Multimedia Platform (Document Processing – Video Sub/Dub)

Aplicație completă (frontend React + backend Flask) pentru:
- Rezumat documente și video
- Subtitrări video și redublare
- Traduceri documente/audio/video cu progres SSE
- Istoric operațiuni și căutare full-text (rezumate incluse)

> 🔧 Frontend poate rula static; pentru funcționalitate completă rulează backend-ul local.

---

## Cerințe de instalare (Ubuntu/macOS)

### Frontend
- Node.js 18+ (recomandat), npm.

### Backend
- Python 3.11/3.12 (recomandat; 3.14 sare dependențe cheie).
- ffmpeg în PATH.
- (opțional) Tesseract pentru OCR.
- (opțional) CUDA/cuDNN dacă vrei GPU pentru Whisper/TTS/torch.

---

## Instalare rapidă

```bash
# frontend
cd frontend
npm install

# backend
cd ../backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools wheel
pip install -r requirements.txt
```

Comandă one-liner (bash) de la rădăcina proiectului (frontend + backend):
```bash
npm install && cd backend && python3.11 -m venv .venv && source .venv/bin/activate && pip install -U pip setuptools wheel && pip install -r requirements.txt
```

Pe Ubuntu (instalare dependențe de sistem + Python 3.11 + ffmpeg + Tesseract), apoi proiectul:
```bash
sudo apt update && sudo apt install -y software-properties-common \
  && sudo add-apt-repository -y ppa:deadsnakes/ppa \
  && sudo apt update && sudo apt install -y python3.11 python3.11-venv ffmpeg tesseract-ocr \
  && cd /path/catre/Document-proccesing-Video-sub-dub \
  && npm install \
  && cd backend && python3.11 -m venv .venv && source .venv/bin/activate \
  && pip install -U pip setuptools wheel && pip install -r requirements.txt
```

---

## Rulare (ambele simultan)

Din rădăcina proiectului:
```bash
npm install
npm run dev   # pornește backend (în .venv) + frontend (Vite)
```

Backend pornește pe `http://localhost:5000`, frontend pe `http://localhost:5173/`.

---

## Endpoint-uri backend (principal)

- `GET /api/health` – healthcheck  
- `GET /api/llm-status` – status LLM extern  
- `GET /api/history` – istoric operațiuni  
- `GET /api/history/search` – căutare full-text (FTS5) în fișiere/meta/rezumate  
- `POST /api/ppt-analysis`  
- `POST /api/document-analysis`  
- `POST /api/image-ocr`  
- `POST /api/translate-document`  
- `POST /api/translate-audio`  
- `POST /api/translate-video`  
- `POST /api/subtitle-ro`  
- `POST /api/redub-video`  
- `POST /api/live-start`, `POST /api/live-stop`

Rezumatul generat este salvat în `processed/` și expus prin `summaryUrl/summary_file`; istoricul indexează și conținutul rezumatelor pentru căutare.

---

## Structură (scurt)

- `frontend/` – React + Vite UI (liquid glass, pagini pentru traduceri, subtitrări, redub, căutare istoric)
- `backend/`
  - `app.py` – Flask API + SSE + socketio
  - `services/` – procesare (analiză, traducere, subtitrare, redublare)
  - `history.py` – SQLite + FTS5 (istoric + rezumate indexate)
  - `uploads/`, `processed/`, `cache/` – fișiere temporare/output
  - `requirements.txt` – dependențe backend
  - `README.md` – detalii backend

---

## Note suplimentare

- Pe CPU, Whisper rulează în FP32 (warning FP16 expected); pentru performanță folosește GPU.
- Python 3.14 va ignora dependențe heavy (transformers/whisper/TTS/librosa etc.), deci funcționalitatea completă necesită 3.11/3.12.
