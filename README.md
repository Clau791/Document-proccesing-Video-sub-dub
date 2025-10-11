# 🎯 Attack Hub - Security Testing Tool

Un instrument pentru testarea securității rețelelor, construit cu React (frontend) și Python/Flask (backend).

## 📋 Ce este npm?

**npm** = Node Package Manager

Este un "magazin de piese" pentru JavaScript:
- **Instalează librării** (de exemplu, React, Vite)
- **Gestionează dependențe** (lista de librării necesare)
- **Rulează scripturi** (comenzi personalizate precum `npm run dev`)

## 🏗️ Cum funcționează sistemul?

```
User (Browser)  →  Frontend (React, port 5173)  →  Backend (Python, port 3000)  →  API Extern
                       ↓                                ↓
                  App.jsx                        server.py (cu API_KEY secret)
```

**Flow-ul complet:**
1. Tu apeși "Start" în browser
2. React trimite request la `http://localhost:3000/api/attack`
3. Python primește request-ul
4. Python adaugă `API_KEY` secret (invizibil în browser!)
5. Python trimite request la API-ul extern
6. Python returnează răspunsul
7. React afișează rezultatul

## 🛠️ Cerințe

### Software necesar:
- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))
- **npm** (vine cu Node.js)

### Verificare instalare:
```bash
python --version   # Trebuie să fie 3.8+
node --version     # Trebuie să fie 18+
npm --version      # Orice versiune
```

## 🚀 Instalare Pas cu Pas

### Pasul 1: Descarcă proiectul
```bash
# Dacă ai Git:
git clone <url-repo>
cd attack-hub

# Sau descarcă ZIP și extrage
```

### Pasul 2: Creează structura (dacă nu există)
```bash
mkdir -p backend frontend/src
```

### Pasul 3: Copiază fișierele
Copiază toate fișierele din artifact-uri în locațiile corecte:
- `package.json` → în ROOT (attack-hub/)
- `server.py` → în backend/
- `requirements.txt` → în backend/
- `package.json` (frontend) → în frontend/
- `vite.config.js` → în frontend/
- `index.html` → în frontend/
- `main.jsx` → în frontend/src/
- `index.css` → în frontend/src/
- `App.jsx` (artifact-ul React) → în frontend/src/
- `.gitignore` → în ROOT
- `run.sh` sau `run.bat` → în ROOT

### Pasul 4: Setup Backend (Python)
```bash
cd backend

# Creează virtual environment (mediu izolat pentru librării)
python -m venv venv

# Activează-l
# Linux/Mac:
source venv/bin/activate
# Windows CMD:
venv\Scripts\activate
# Windows PowerShell:
venv\Scripts\Activate.ps1

# Instalează librăriile Python
pip install -r requirements.txt

cd ..
```

**Ce face fiecare librărie:**
- `flask` = Framework pentru server web
- `flask-cors` = Permite comunicarea între frontend și backend
- `requests` = Trimite HTTP requests către API extern
- `python-dotenv` = Citește fișiere .env (opțional)

### Pasul 5: Setup Frontend (React)
```bash
cd frontend

# Instalează librăriile JavaScript
npm install

cd ..
```

**Ce instalează:**
- `react` = Librăria pentru UI
- `vite` = Tool rapid pentru development
- `lucide-react` = Iconițe frumoase

### Pasul 6: Setup ROOT
```bash
# În folderul principal (attack-hub/)
npm install
```

Aceasta instalează `concurrently` - tool-ul care rulează backend și frontend simultan.

### Pasul 7: Configurare API Key

**Opțiunea A: Variabile de mediu (Recomandat)**

Linux/Mac:
```bash
export API_KEY="Your-api-Key"
export API_URL="https://website/"
```

Windows PowerShell:
```powershell
setx API_KEY="Your-api-Key"
setx API_URL "https://mythicalstressapi.net/"
```

Windows CMD:
```cmd
set API_KEY=Your-api-Key
set API_URL=https://website/
```

**Opțiunea B: Editează run.sh / run.bat**
Deschide `run.sh` sau `run.bat` și modifică linia:
```bash
export API_KEY="PUNE-CHEIA-TA-AICI"
```

### Pasul 8: Pornire
```bash
# Linux/Mac:
chmod +x run.sh
./run.sh

# Windows:
run.bat

# Sau direct cu npm:
npm run dev
```

## 🎮 Utilizare

După pornire, deschide browser la:
- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:3000
- **Health Check**: http://localhost:3000/api/health

### Testare backend:
```bash
curl http://localhost:3000/api/health
```

Răspuns așteptat:
```json
{
  "status": "ok",
  "message": "Backend is running!",
  "api_key_loaded": true
}
```

## 📦 Comenzi Disponibile

Din ROOT (attack-hub/):
```bash
npm run dev              # Start tot (backend + frontend)
npm run backend          # Start doar backend
npm run frontend         # Start doar frontend
npm run install-all      # Instalează toate dependențele
npm run build            # Build frontend pentru producție
```

## 🐛 Troubleshooting

### Backend nu pornește
```bash
cd backend
source venv/bin/activate  # sau venv\Scripts\activate pe Windows
pip install -r requirements.txt
python server.py
```

Dacă vezi erori despre module lipsă:
```bash
pip install flask flask-cors requests
```

### Frontend nu pornește
```bash
cd frontend
npm install
npm run dev
```

### Port ocupat
Schimbă portul:
```bash
export PORT=3001  # Backend va rula pe 3001
```

### API Key lipsă
Dacă vezi "❌ API Key Missing":
```bash
# Setează variabila:
export API_KEY="cheia-ta"
```

### "concurrently: command not found"
```bash
# În ROOT:
npm install
```

### CORS errors
Verifică că backend-ul are:
```python
CORS(app, origins=["http://localhost:5173"])
```

## 📚 Înțelegerea Structurii

```
attack-hub/
├── package.json          # ← Configurare npm ROOT (concurrently)
│                         # Conține scriptul "dev" care pornește tot
│
├── backend/
│   ├── server.py        # ← Codul Python (Flask server)
│   │                    # Primește requests de la frontend
│   │                    # Adaugă API_KEY secret
│   │                    # Trimite la API extern
│   │
│   ├── requirements.txt # ← Lista de librării Python
│   │                    # pip citește asta la "pip install -r"
│   │
│   └── venv/            # ← Virtual environment (se creează)
│                        # Conține toate librăriile Python instalate
│
└── frontend/
    ├── package.json     # ← Configurare npm pentru frontend
    │                    # Lista de librării JavaScript
    │
    ├── src/
    │   ├── App.jsx      # ← Codul React (interfața ta)
    │   ├── main.jsx     # ← Punctul de intrare React
    │   └── index.css    # ← Stiluri CSS
    │
    ├── index.html       # ← HTML principal
    ├── vite.config.js   # ← Configurare Vite
    │
    └── node_modules/    # ← Librăriile instalate (se creează)
                         # npm le instalează aici
```

## 🔐 Securitate

**❌ NU face:**
- Nu pune API_KEY în cod (hardcoded)
- Nu face commit la fișiere .env
- Nu partaja API_KEY public

**✅ Fă:**
- Folosește variabile de mediu
- Păstrează API_KEY secret
- Adaugă .env în .gitignore

## 📝 License

MIT

---

**Need help?** Verifică logs-urile pentru erori:
- Backend: Vezi terminal-ul unde rulează Python# Document-proccesing-Video-sub-dub
