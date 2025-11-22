import React, { useState, useEffect, useMemo } from "react";
import { 
  FileText, Video, Subtitles, Download, Upload, CheckCircle, Loader, AlertCircle, X, 
  FileImage, BookOpen, Languages, Mic, VideoIcon, MessageSquare, Presentation,
  FileType, Image as ImageIcon, Globe, PlayCircle, Radio
} from "lucide-react";
import './styles/glass_buttons.css';

/* =====================================================
   ✅ SISTEM AI INTEGRAT - Conform cerințe funcționale
   
   I. Analiză și stocare documente
      1. PowerPoint (PPT/PPTX) - Slide-uri, paragrafe, bullet points
      2. Word/PDF/eBook - Paragrafe individuale cu asocieri
      3. Imagine (JPG, PNG, TIFF) - OCR inteligent
   
   II. Traducere automată multilingvă (EN/ZH/RU/JA → RO)
      1. Documente scrise - Traducere completă
      2. Fișiere audio - ASR + Traducere + Generare audio RO
      3. Fișiere video - Extragere audio + Traducere + TTS RO
   
   III. Subtitrare automată și redublaj
      1. Subtitrare în limba originală (RO → RO)
      2. Redublare video (audio înlocuit RO → EN sau invers)
   
   IV. Subtitrare bidirecțională în timp real (RO ↔ RU)
   ===================================================== */

// Backend rulează pe localhost:5000
const BASE_URL = 'http://localhost:5000';
const API_URL = `${BASE_URL}/api`;

type Lang = "en" | "zh" | "ru" | "ja" | "ro";
const LANG_LABEL: Record<Lang, string> = {
  en: "🇬🇧 Engleză (EN)",
  zh: "🇨🇳 Chineză (ZH)",
  ru: "🇷🇺 Rusă (RU)",
  ja: "🇯🇵 Japoneză (JA)",
  ro: "🇷🇴 Română (RO)",
};

// ========== UTILITY FUNCTIONS ==========

// Utility pentru upload
const uploadFile = async (
  endpoint: string,
  file: File,
  additionalData?: Record<string, string>
): Promise<any> => {
  const formData = new FormData();
  formData.append('file', file);
  
  if (additionalData) {
    Object.entries(additionalData).forEach(([key, value]) => {
      formData.append(key, value);
    });
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Upload failed');
  }

  return response.json();
};

// ========== SVG Filters & Global Styles ==========
const GlobalKeyframes = () => (
  <>
    <svg style={{ position: 'absolute', width: 0, height: 0 }}>
      <defs>
        <filter id="glass-distortion">
          <feTurbulence type="fractalNoise" baseFrequency="0.008 0.002" numOctaves="4" result="warp" seed="5">
            <animate attributeName="baseFrequency" values="0.008 0.002;0.01 0.003;0.008 0.002" dur="8s" repeatCount="indefinite" />
          </feTurbulence>
          <feDisplacementMap xChannelSelector="R" yChannelSelector="G" scale="50" in="SourceGraphic" in2="warp" />
        </filter>
      </defs>
    </svg>
  </>
);

// ========== Error Boundary ==========
class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean; error?: any }>{
  constructor(props: any) { super(props); this.state = { hasError: false }; }
  static getDerivedStateFromError(error: any) { return { hasError: true, error }; }
  componentDidCatch(error: any, info: any) { console.error("UI crashed:", error, info); }
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen grid place-items-center bg-gradient-to-br from-white via-sky-50 to-blue-50 p-6">
          <div className="max-w-lg w-full bg-white/90 backdrop-blur border border-gray-200 rounded-2xl p-6 shadow-xl">
            <h2 className="text-xl font-bold mb-2 text-gray-800">A apărut o eroare în UI</h2>
            <p className="text-sm text-gray-600 mb-4">Verifică dependențele și componentele recente.</p>
            <pre className="text-xs text-red-600 whitespace-pre-wrap bg-red-50 border border-red-200 rounded-lg p-3 overflow-auto max-h-48">{String(this.state.error)}</pre>
            <button className="mt-4 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-500 to-sky-500 text-white" onClick={() => location.reload()}>Reîncarcă</button>
          </div>
        </div>
      );
    }
    return this.props.children as any;
  }
}

// ========== Animated Background ==========
const BackgroundFX: React.FC = () => {
  const blobs = Array.from({ length: 3 }).map((_, i) => ({
    id: i,
    size: 240 + (i % 3) * 110,
    top: `${(i * 13) % 85 + 5}%`,
    left: `${(i * 19) % 85 + 5}%`,
    duration: 120 + (i % 5) * 40,
    delay: i * 1.2,
    even: i % 2 === 0,
  }));

  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div data-anim className="absolute inset-0" style={{
        background:
          "radial-gradient(1200px 600px at 0% 0%, rgba(59,130,246,0.28), transparent)," +
          "radial-gradient(1000px 600px at 100% 0%, rgba(96,165,250,0.28), transparent)," +
          "radial-gradient(900px 500px at -10% 80%, rgba(191,219,254,0.45), transparent)," +
          "linear-gradient(to bottom right, #ffffff, #eaf2ff)",
        filter: "saturate(1.15) contrast(1.03)",
        animation: "colorShift 180s linear infinite",
      }} />

      <div data-anim className="absolute -inset-[20%] opacity-[0.06]" style={{
        background:
          "conic-gradient(from 0deg at 50% 50%, rgba(255,255,255,0.0) 0deg, rgba(255,255,255,0.5) 35deg, rgba(255,255,255,0.0) 70deg)",
        transformOrigin: "50% 50%",
        animation: "shineSweep 240s linear infinite",
      }} />

      <div className="absolute inset-0 opacity-[0.14]" style={{ maskImage: "radial-gradient(60% 60% at 50% 50%, black, transparent)" }}>
        <div data-anim className="w-full h-full" style={{
          backgroundImage:
            "linear-gradient(to right, rgba(30,64,175,0.08) 1px, transparent 1px)," +
            "linear-gradient(to bottom, rgba(30,64,175,0.08) 1px, transparent 1px)",
          backgroundSize: "36px 36px",
          animation: "slowPan 600s linear infinite",
        }} />
      </div>

      {blobs.map((b, idx) => (
        <div key={b.id} data-anim className={`absolute rounded-full ${b.even ? "blur-xl opacity-[0.12]" : "blur-lg opacity-[0.8]"}`} style={{
          top: b.top,
          left: b.left,
          width: b.size,
          height: b.size,
          background:
            idx % 2 === 0
              ? "radial-gradient(circle at 30% 30%, rgba(96,165,250,0.45), rgba(59,130,246,0.25), transparent 60%)"
              : "radial-gradient(circle at 70% 60%, rgba(147,197,253,0.4), rgba(191,219,254,0.25), transparent 60%)",
          animation: `floatXY ${b.duration}s ease-in-out ${b.delay}s infinite`,
        }} />
      ))}
    </div>
  );
};

// ========== NavBar ==========
const NavBar: React.FC<{ currentPage: string; onNavigate: (page: string) => void; backendStatus: string }> = ({ currentPage, onNavigate, backendStatus }) => (
  <nav className="liquidGlass-wrapper liquidGlass-header sticky top-0 left-0 right-0 z-50 rounded-3xl mx-4 mt-4 mb-2">
    <div className="liquidGlass-effect" />
    <div className="liquidGlass-tint" />
    <div className="liquidGlass-shine" />
    <div className="liquidGlass-content container mx-auto px-6 py-2 w-full">
      <div className="flex items-center justify-between">
        <button onClick={() => onNavigate("home")} className="flex items-center gap-3 hover:opacity-80 transition-all duration-300 group">
          <div className="bg-gradient-to-br from-blue-500 to-sky-500 p-2.5 rounded-xl shadow-lg group-hover:shadow-xl group-hover:scale-105 transition-all duration-300"><FileText className="w-7 h-7 text-white" /></div>
          <div className="text-left">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-sky-600 bg-clip-text text-transparent">Sistem AI Integrat</h1>
            <p className="text-sm text-gray-600">Analiză, Traducere, Subtitrare</p>
          </div>
        </button>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-gray-50/90 to-gray-100/90 rounded-xl border border-gray-200 shadow-sm">
            <div className={`w-2.5 h-2.5 rounded-full shadow-lg ${backendStatus === "online" ? "bg-green-500 animate-pulse shadow-green-400" : backendStatus === "offline" ? "bg-red-500 shadow-red-400" : "bg-yellow-500 animate-pulse shadow-yellow-400"}`} />
            <span className="text-xs font-medium text-gray-700">Backend: {backendStatus === "online" ? "Online" : backendStatus === "offline" ? "Offline" : "Verificare..."}</span>
          </div>
          {currentPage !== "home" && (
            <button onClick={() => onNavigate("home")} className="px-5 py-2 bg-gradient-to-r from-blue-500 to-sky-500 hover:from-blue-600 hover:to-sky-600 text-white rounded-xl transition-all duration-300 shadow-md hover:shadow-lg font-medium">← Înapoi</button>
          )}
        </div>
      </div>
    </div>
  </nav>
);

// ========== Footer ==========
const Footer: React.FC = () => (
  <footer className="liquidGlass-wrapper liquidGlass-footer sticky bottom-0 left-0 right-0 z-40 mt-auto rounded-3xl mx-4 mb-4">
    <div className="liquidGlass-effect" />
    <div className="liquidGlass-tint" />
    <div className="liquidGlass-shine" />
    <div className="liquidGlass-content container mx-auto px-6 py-4 w-full">
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="bg-gradient-to-r from-blue-500 to-sky-500 p-1.5 rounded-lg shadow-md"><FileText className="w-5 h-5 text-white" /></div>
          <span className="text-gray-800 font-semibold">Sistem AI Integrat</span>
        </div>
        <div className="text-gray-600 text-sm text-center">© 2025 Platformă de procesare AI. Toate drepturile rezervate.</div>
        <div className="text-gray-600 text-sm">Creat cu <span className="text-red-500">♥</span> pentru procesare multimedia</div>
      </div>
    </div>
  </footer>
);

// ========== Home - Categorii principale ==========
const HomeCards: React.FC<{ onNavigate: (page: string) => void }> = ({ onNavigate }) => {
  const categories = [
    {
      id: "category-i",
      title: "I. Analiză și Stocare Documente",
      description: "Procesare inteligentă PPT, Word, PDF, Imagine cu OCR",
      icon: BookOpen,
      color: "from-blue-400 to-sky-400",
      subcategories: [
        { id: "ppt", name: "PowerPoint", icon: Presentation },
        { id: "word-pdf", name: "Word/PDF/eBook", icon: FileType },
        { id: "image-ocr", name: "Imagine OCR", icon: ImageIcon }
      ]
    },
    {
      id: "category-ii",
      title: "II. Traducere Automată Multilingvă",
      description: "EN/ZH/RU/JA → RO pentru documente, audio, video",
      icon: Languages,
      color: "from-purple-400 to-pink-400",
      subcategories: [
        { id: "translate-docs", name: "Documente scrise", icon: FileText },
        { id: "translate-audio", name: "Fișiere audio", icon: Mic },
        { id: "translate-video", name: "Fișiere video", icon: VideoIcon }
      ]
    },
    {
      id: "category-iii",
      title: "III. Subtitrare și Redublaj",
      description: "Subtitrare automată RO → RO și redublare video",
      icon: Subtitles,
      color: "from-green-400 to-emerald-400",
      subcategories: [
        { id: "subtitle-ro", name: "Subtitrare RO → RO", icon: Subtitles },
        { id: "redub-video", name: "Redublare video", icon: Video }
      ]
    },
    {
      id: "category-iv",
      title: "IV. Subtitrare Bidirecțională Live",
      description: "Dialog în timp real RO ↔ RU cu subtitrări",
      icon: Radio,
      color: "from-orange-400 to-red-400",
      subcategories: [
        { id: "live-subtitle", name: "Dialog live RO ↔ RU", icon: MessageSquare }
      ]
    }
  ];

  return (
    <div className="min-h-[calc(100vh-140px)]">
      <div className="container mx-auto px-4 py-20">
        <div className="text-center mb-16 fade-up">
          <h1 className="text-6xl font-bold bg-gradient-to-r from-blue-600 via-sky-600 to-blue-700 bg-clip-text text-transparent mb-7" style={{ paddingBottom: '0.15em' }}>
            Sistem AI Integrat
          </h1>
          <p className="text-xl text-gray-700/90 max-w-3xl mx-auto">
            Alege categoria de servicii AI pentru procesarea documentelor și fișierelor multimedia
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-7xl mx-auto">
          {categories.map((cat, index) => {
            const Icon = cat.icon as any;
            const delayClass = `fade-up-delay-${index + 1}`;
            
            return (
              <div key={cat.id} className={`liquidGlass-wrapper liquidGlass-card ${delayClass}`}>
                <div className="liquidGlass-effect" />
                <div className="liquidGlass-tint" />
                <div className="liquidGlass-shine" />
                <div className="liquidGlass-content">
                  <div className="flex items-start gap-4 mb-6">
                    <div className={`w-16 h-16 bg-gradient-to-br ${cat.color} rounded-2xl flex items-center justify-center shadow-xl flex-shrink-0`}>
                      <Icon className="w-8 h-8 text-white" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-800 mb-2">{cat.title}</h3>
                      <p className="text-gray-600 text-sm">{cat.description}</p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    {cat.subcategories.map((sub) => {
                      const SubIcon = sub.icon as any;
                      return (
                        <button
                          key={sub.id}
                          onClick={() => onNavigate(sub.id)}
                          className="w-full flex items-center gap-3 px-4 py-3 bg-white/60 hover:bg-white/80 border border-gray-200 hover:border-blue-300 rounded-xl transition-all duration-300 text-left group"
                        >
                          <SubIcon className="w-5 h-5 text-gray-600 group-hover:text-blue-600 transition-colors" />
                          <span className="text-gray-800 font-medium group-hover:text-blue-600 transition-colors">{sub.name}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

// ========== I.1 - PowerPoint Analysis ==========
const PPTAnalysisPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Selectează un fișier PPT/PPTX');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await uploadFile('/ppt-analysis', file);
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl mb-6 shadow-lg fade-up" style={{padding: '1.5rem'}}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="flex items-start gap-4">
            <div className="bg-gradient-to-br from-blue-400 to-sky-400 w-16 h-16 rounded-xl flex items-center justify-center shadow-lg">
              <Presentation className="w-8 h-8 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">I.1 - Analiză PowerPoint</h2>
              <p className="text-gray-600 mb-2">Extrage și stochează slide-uri, paragrafe, bullet points și imagini</p>
              <p className="text-xs text-gray-400 font-mono">Endpoint: POST /api/ppt-analysis</p>
            </div>
          </div>
        </div>
      </div>

      <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg fade-up-delay-2" style={{padding: '2rem'}}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="border-2 border-dashed border-blue-300 rounded-xl p-12 text-center">
            <Upload className="w-16 h-16 mx-auto text-blue-400 mb-4" />
            <p className="text-gray-600 mb-4">Încarcă fișiere PowerPoint (.ppt, .pptx)</p>
            
            <input
              type="file"
              accept=".ppt,.pptx"
              onChange={handleFileChange}
              className="hidden"
              id="ppt-file-input"
            />
            
            <div className="button-wrap button-wrap-blue" style={{ display: 'inline-block' }}>
              <div className="button-shadow"></div>
              <button 
                className="glass-btn-blue"
                onClick={() => document.getElementById('ppt-file-input')?.click()}
                type="button"
              >
                <span>{file ? `📄 ${file.name}` : 'Selectează Fișier PPT/PPTX'}</span>
              </button>
            </div>

            {file && (
              <button
                onClick={handleUpload}
                disabled={loading}
                className="mt-4 px-6 py-3 bg-gradient-to-r from-blue-500 to-sky-500 text-white rounded-xl font-medium hover:shadow-lg transition-all disabled:opacity-50"
              >
                {loading ? 'Se procesează...' : '📤 Încarcă și Analizează'}
              </button>
            )}

            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600">
                {error}
              </div>
            )}

            {result && (
              <div className="mt-6 p-6 bg-green-50 border border-green-200 rounded-xl text-left">
                <h3 className="font-bold text-green-800 mb-3">✅ Analiză completă!</h3>
                <div className="space-y-2 text-sm text-gray-700">
                  <p><strong>Fișier:</strong> {result.originalFile}</p>
                  {result.totalSlides && <p><strong>Slide-uri:</strong> {result.totalSlides}</p>}
                  {result.totalParagraphs && <p><strong>Paragrafe:</strong> {result.totalParagraphs}</p>}
                </div>
                {result.downloadUrl && (
                  <a
                    href={`http://localhost:5000/download/${result.downloadUrl}`}
                    className="mt-4 inline-block px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    download
                  >
                    📥 Descarcă Rezultat
                  </a>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// ========== I.2 - Document Analysis ==========
const WordPDFAnalysisPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    try {
      const data = await uploadFile('/document-analysis', file);
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl mb-6 shadow-lg fade-up" style={{padding: '1.5rem'}}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="flex items-start gap-4">
            <div className="bg-gradient-to-br from-blue-400 to-sky-400 w-16 h-16 rounded-xl flex items-center justify-center shadow-lg">
              <FileType className="w-8 h-8 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">I.2 - Analiză Word/PDF/eBook</h2>
              <p className="text-gray-600 mb-2">Extrage paragrafe cu asocieri: pagină, capitol, document, imagini</p>
              <p className="text-xs text-gray-400 font-mono">Endpoint: POST /api/document-analysis</p>
            </div>
          </div>
        </div>
      </div>

      <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg fade-up-delay-2" style={{padding: '2rem'}}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="border-2 border-dashed border-blue-300 rounded-xl p-12 text-center">
            <Upload className="w-16 h-16 mx-auto text-blue-400 mb-4" />
            <p className="text-gray-600 mb-4">Încarcă documente (.doc, .docx, .pdf, .epub)</p>

            <input
              type="file"
              accept=".doc,.docx,.pdf,.epub"
              onChange={handleFileChange}
              className="hidden"
              id="doc-file-input"
            />

            <div className="button-wrap button-wrap-blue" style={{ display: 'inline-block' }}>
              <div className="button-shadow"></div>
              <button 
                className="glass-btn-blue"
                onClick={() => document.getElementById('doc-file-input')?.click()}
                type="button"
              >
                <span>{file ? `📄 ${file.name}` : 'Selectează Document'}</span>
              </button>
            </div>

            {file && (
              <button
                onClick={handleUpload}
                disabled={loading}
                className="mt-4 px-6 py-3 bg-gradient-to-r from-blue-500 to-sky-500 text-white rounded-xl font-medium hover:shadow-lg transition-all disabled:opacity-50"
              >
                {loading ? 'Se procesează...' : '📤 Analizează Document'}
              </button>
            )}

            {error && <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600">{error}</div>}
            
            {result && (
              <div className="mt-6 p-6 bg-green-50 border border-green-200 rounded-xl text-left">
                <h3 className="font-bold text-green-800 mb-3">✅ Analiză completă!</h3>
                <div className="space-y-2 text-sm text-gray-700">
                  <p><strong>Fișier:</strong> {result.originalFile}</p>
                  {result.totalPages && <p><strong>Pagini:</strong> {result.totalPages}</p>}
                  {result.totalParagraphs && <p><strong>Paragrafe:</strong> {result.totalParagraphs}</p>}
                </div>
                {result.downloadUrl && (
                  <a
                    href={`http://localhost:5000/download/${result.downloadUrl}`}
                    className="mt-4 inline-block px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    download
                  >
                    📥 Descarcă Rezultat
                  </a>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// ========== I.3 - Image OCR ==========
const ImageOCRPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    try {
      const data = await uploadFile('/image-ocr', file);
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl mb-6 shadow-lg fade-up" style={{padding: '1.5rem'}}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="flex items-start gap-4">
            <div className="bg-gradient-to-br from-blue-400 to-sky-400 w-16 h-16 rounded-xl flex items-center justify-center shadow-lg">
              <ImageIcon className="w-8 h-8 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">I.3 - Extragere Text din Imagini (OCR)</h2>
              <p className="text-gray-600 mb-2">OCR inteligent: Tesseract / TrOCR / Surya</p>
              <p className="text-xs text-gray-400 font-mono">Endpoint: POST /api/image-ocr</p>
            </div>
          </div>
        </div>
      </div>

      <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg fade-up-delay-2" style={{padding: '2rem'}}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="border-2 border-dashed border-blue-300 rounded-xl p-12 text-center">
            <Upload className="w-16 h-16 mx-auto text-blue-400 mb-4" />
            <p className="text-gray-600 mb-4">Încarcă imagini (.jpg, .png, .tiff)</p>

            <input
              type="file"
              accept=".jpg,.jpeg,.png,.tiff,.bmp"
              onChange={handleFileChange}
              className="hidden"
              id="img-file-input"
            />

            <div className="button-wrap button-wrap-blue" style={{ display: 'inline-block' }}>
              <div className="button-shadow"></div>
              <button 
                className="glass-btn-blue"
                onClick={() => document.getElementById('img-file-input')?.click()}
                type="button"
              >
                <span>{file ? `📄 ${file.name}` : 'Selectează Imagine'}</span>
              </button>
            </div>

            {file && (
              <button
                onClick={handleUpload}
                disabled={loading}
                className="mt-4 px-6 py-3 bg-gradient-to-r from-blue-500 to-sky-500 text-white rounded-xl font-medium hover:shadow-lg transition-all disabled:opacity-50"
              >
                {loading ? 'Procesare OCR...' : '📤 Extrage Text'}
              </button>
            )}

            {error && <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600">{error}</div>}
            
            {result && (
              <div className="mt-6 p-6 bg-green-50 border border-green-200 rounded-xl text-left">
                <h3 className="font-bold text-green-800 mb-3">✅ OCR completat!</h3>
                <div className="space-y-2 text-sm text-gray-700">
                  <p><strong>Fișier:</strong> {result.originalFile}</p>
                  {result.extractedText && <p><strong>Text extras:</strong> {result.extractedText.substring(0, 200)}...</p>}
                  {result.detectedLanguage && <p><strong>Limbă detectată:</strong> {result.detectedLanguage}</p>}
                </div>
                {result.downloadUrl && (
                  <a
                    href={`http://localhost:5000/download/${result.downloadUrl}`}
                    className="mt-4 inline-block px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    download
                  >
                    📥 Descarcă Text
                  </a>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// ========== II.1 - Translate Documents ==========
const TranslateDocsPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

    // ➜ PROGRES (pagini)
  const [pagesDone, setPagesDone] = useState(0);
  const [pagesTotal, setPagesTotal] = useState(0);
  const [percent, setPercent] = useState(0);
  const [showProgress, setShowProgress] = useState(false);

  useEffect(() => {
    // Conectare la SSE-ul backendului
    const es = new EventSource("http://127.0.0.1:5000/events"); // același host/port ca app.py

    es.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (typeof data.percent === "number") setPercent(data.percent);
        if (typeof data.pages_done === "number") setPagesDone(data.pages_done);
        if (typeof data.pages_total === "number") setPagesTotal(data.pages_total);
        setShowProgress(true);
      } catch { /* ignore */ }
    };

    es.onerror = () => {
      // închidem pe eroare (ex: backend oprit)
      es.close();
    };

    return () => es.close();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setResult(null); // Resetează rezultatul la fișier nou
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await uploadFile('/translate-document', file); 
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Cardul de titlu */}
      <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl mb-6 shadow-lg fade-up" style={{padding: '1.5rem'}}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="flex items-start gap-4">
            <div className="bg-gradient-to-br from-purple-400 to-pink-400 w-16 h-16 rounded-xl flex items-center justify-center shadow-lg">
              <FileText className="w-8 h-8 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">II.1 - Traducere Documente Scrise</h2>
              <p className="text-gray-600 mb-2">Traducere completă EN/ZH/RU/JA → RO</p>
              <p className="text-xs text-gray-400 font-mono">Endpoint: POST /api/translate-document</p>
            </div>
          </div>
        </div>
      </div>

      {/* Cardul de upload */}
      <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg fade-up-delay-2" style={{padding: '2rem'}}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="border-2 border-dashed border-purple-300 rounded-xl p-12 text-center">
            <Upload className="w-16 h-16 mx-auto text-purple-400 mb-4" />
            
            <p className="text-gray-600 mb-4">Încarcă documente (.pdf, .docx, .pptx)</p>

            <input
              type="file"
              accept=".pdf,.docx,.pptx"
              onChange={handleFileChange}
              className="hidden"
              id="translate-doc-input"
            />

            {/* Container vertical pentru butoane */}
            <div className="flex flex-col items-center gap-4  max-w-md mx-auto">

              {/* --- Buton 1: Selectare Fișier --- */}
              <div className="button-wrap button-wrap-blue w-full">
                <div className="button-shadow"></div>
                <button 
                  className="glass-btn glass-btn-blue w-full"
                  onClick={() => document.getElementById('translate-doc-input')?.click()}
                  type="button"
                >
                  <span className="truncate">{file ? `📄 ${file.name}` : 'Selectează Document'}</span>
                </button>
              </div>

              {/* --- Buton 2: Traducere --- */}
              {file && (
                <div className="button-wrap button-wrap-purple w-full">
                  <div className="button-shadow"></div>
                  <button
                    onClick={handleUpload}
                    disabled={loading}
                    className="glass-btn glass-btn-purple w-full"
                  >
                    {/* <Upload className="w-5 h-5 flex-shrink-0" /> */}
                    <span className="truncate">{loading ? 'Traducere în curs...' : 'Tradu in RO'}</span>
                  </button>
                </div>
              )}
            </div>

            {error && <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600">{error}</div>}
            
            {/* --- Card Rezultat --- */}
            {result && (
              <div className="mt-6 p-6 rounded-2xl text-left shadow-lg 
                            bg-green-600/10 border border-green-500/30 
                            backdrop-blur-lg">
                <h3 className="font-bold text-green-800 mb-3">✅ Traducere completă!</h3>
                <div className="space-y-2 text-sm text-gray-700">
                  <p><strong>Fișier original:</strong> {result.originalFile}</p>
                  <p><strong>Limba originală:</strong> {result.originalLanguage}</p>
                  <p><strong>Limba tradusă:</strong> {result.translatedLanguage}</p>
                </div>

                {/* --- Buton 3: Descarcă (Stil Verde) --- */}
                {result.downloadUrl && (
                  <div className="button-wrap button-wrap-green w-full mt-6">
                    <div className="button-shadow"></div>
                    <a
                      href={`${BASE_URL}${result.downloadUrl}`}
                      className="glass-btn glass-btn-green w-full flex items-center justify-center gap-2 leading-none"
                      download
                    >
                      {/* dacă vrei fără icon, șterge <Download /> */}
                      <Download className="w-5 h-5 flex-shrink-0" />
                      <span className="truncate">Descarcă Document Tradus</span>
                    </a>
                  </div>
                )}

                
              </div>
            )}
            
          </div>
        </div>
      </div>

      {/* --- Progres Traducere (SSE) --- */}
{showProgress && (
  <div className="mt-6">
    <div className="w-full h-3 bg-gray-200/70 rounded-full overflow-hidden">
      <div
        className="h-3 bg-green-500 transition-all duration-300"
        style={{ width: `${percent}%` }}
      />
    </div>
    <div className="mt-2 text-xs text-gray-600">
      {pagesTotal > 0
        ? <>Progres: {pagesDone}/{pagesTotal} pagini ({percent}%)</>
        : <>Progres: {percent}%</>}
    </div>
  </div>
)}

    </div>
  );
};
// ========== II.2 - Translate Audio ==========
const TranslateAudioPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [srcLang, setSrcLang] = useState<string>('en');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setResult(null); // resetăm rezultatul la fișier nou (ca la translate-docs)
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await uploadFile('/translate-audio', file, { src_lang: srcLang });
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Card titlu */}
      <div
        className="liquidGlass-wrapper liquidGlass-card rounded-3xl mb-6 shadow-lg fade-up"
        style={{ padding: '1.5rem' }}
      >
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="flex items-start gap-4">
            <div className="bg-gradient-to-br from-purple-400 to-pink-400 w-16 h-16 rounded-xl flex items-center justify-center shadow-lg">
              <Mic className="w-8 h-8 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">
                II.2 - Traducere Fișiere Audio
              </h2>
              <p className="text-gray-600 mb-2">
                ASR multilingv + Traducere + Generare audio _RO
              </p>
              <p className="text-xs text-gray-400 font-mono">
                Endpoint: POST /api/translate-audio
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Card upload – stil ca la TranslateDocsPage */}
      <div
        className="liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg fade-up-delay-2"
        style={{ padding: '2rem' }}
      >
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="border-2 border-dashed border-purple-300 rounded-xl p-12 text-center">
            <Upload className="w-16 h-16 mx-auto text-purple-400 mb-4" />

            {/* Limba sursă */}
            <div className="mb-6 max-w-md mx-auto text-left">
              <label className="block mb-2 font-semibold text-gray-700">
                Limba sursă:
              </label>
              <select
                value={srcLang}
                onChange={(e) => setSrcLang(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              >
                <option value="en">🇬🇧 Engleză</option>
                <option value="zh">🇨🇳 Chineză</option>
                <option value="ru">🇷🇺 Rusă</option>
                <option value="ja">🇯🇵 Japoneză</option>
              </select>
            </div>

            <p className="text-gray-600 mb-4">
              Încarcă fișiere audio (.mp3, .wav, .m4a, .ogg, .flac)
            </p>

            <input
              type="file"
              accept=".mp3,.wav,.m4a,.ogg,.flac"
              onChange={handleFileChange}
              className="hidden"
              id="translate-audio-input"
            />

            {/* Container vertical pentru butoane – ca la translate-docs */}
            <div className="flex flex-col items-center gap-4 max-w-md mx-auto">
              {/* Buton 1: Selectează Audio */}
              <div className="button-wrap button-wrap-blue w-full">
                <div className="button-shadow"></div>
                <button
                  className="glass-btn glass-btn-blue w-full"
                  onClick={() =>
                    document.getElementById('translate-audio-input')?.click()
                  }
                  type="button"
                >
                  <span className="truncate">
                    {file ? `🔊 ${file.name}` : 'Selectează Audio'}
                  </span>
                </button>
              </div>

              {/* Buton 2: Traduce Audio */}
              {file && (
                <div className="button-wrap button-wrap-purple w-full">
                  <div className="button-shadow"></div>
                  <button
                    onClick={handleUpload}
                    disabled={loading}
                    className="glass-btn glass-btn-purple w-full"
                  >
                    <span className="truncate">
                      {loading
                        ? 'Traducere audio în curs...'
                        : `Tradu Audio ${srcLang.toUpperCase()} → RO`}
                    </span>
                  </button>
                </div>
              )}
            </div>

            {/* Eroare */}
            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600">
                {error}
              </div>
            )}

            {/* Rezultat */}
            {result && (
              <div
                className="mt-6 p-6 rounded-2xl text-left shadow-lg 
                           bg-green-600/10 border border-green-500/30 
                           backdrop-blur-lg"
              >
                <h3 className="font-bold text-green-800 mb-3">
                  ✅ Traducere audio completă!
                </h3>
                <div className="space-y-2 text-sm text-gray-700">
                  <p>
                    <strong>Fișier original:</strong> {result.originalFile}
                  </p>
                  <p>
                    <strong>Limba originală:</strong> {result.originalLanguage}
                  </p>
                  <p>
                    <strong>Limba tradusă:</strong> {result.translatedLanguage}
                  </p>
                </div>

                {/* Buton download – la fel ca la TranslateDocsPage, dar pentru audio */}
                {result.downloadUrl && (
                  <div className="button-wrap button-wrap-green w-full mt-6">
                    <div className="button-shadow"></div>
                    <a
                      href={`${BASE_URL}${result.downloadUrl}`}
                      className="glass-btn glass-btn-green w-full flex items-center justify-center gap-2 leading-none"
                      download
                    >
                      <Download className="w-5 h-5 flex-shrink-0" />
                      <span className="truncate">
                        Descarcă Audio Tradus
                      </span>
                    </a>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};


// ========== II.3 - Translate Video ==========
const TranslateVideoPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [srcLang, setSrcLang] = useState<string>('en');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    try {
      const data = await uploadFile('/translate-video', file, { src_lang: srcLang });
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl mb-6 shadow-lg fade-up" style={{padding: '1.5rem'}}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="flex items-start gap-4">
            <div className="bg-gradient-to-br from-purple-400 to-pink-400 w-16 h-16 rounded-xl flex items-center justify-center shadow-lg">
              <VideoIcon className="w-8 h-8 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">II.3 - Traducere Fișiere Video</h2>
              <p className="text-gray-600 mb-2">Extragere audio + Traducere + TTS RO → Video _RO</p>
              <p className="text-xs text-gray-400 font-mono">Endpoint: POST /api/translate-video</p>
            </div>
          </div>
        </div>
      </div>

      <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg fade-up-delay-2" style={{padding: '2rem'}}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="border-2 border-dashed border-purple-300 rounded-xl p-12 text-center">
            <Upload className="w-16 h-16 mx-auto text-purple-400 mb-4" />
            
            <div className="mb-6">
              <label className="block mb-2 font-semibold text-gray-700">Limba sursă:</label>
              <select
                value={srcLang}
                onChange={(e) => setSrcLang(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              >
                <option value="en">🇬🇧 Engleză</option>
                <option value="zh">🇨🇳 Chineză</option>
                <option value="ru">🇷🇺 Rusă</option>
                <option value="ja">🇯🇵 Japoneză</option>
              </select>
            </div>

            <p className="text-gray-600 mb-4">Încarcă fișiere video (.mp4, .avi, .mov, .mkv)</p>

            <input
              type="file"
              accept=".mp4,.avi,.mov,.mkv,.webm"
              onChange={handleFileChange}
              className="hidden"
              id="translate-video-input"
            />

            <div className="button-wrap button-wrap-blue" style={{ display: 'inline-block' }}>
              <div className="button-shadow"></div>
              <button 
                className="glass-btn-blue"
                onClick={() => document.getElementById('translate-video-input')?.click()}
                type="button"
              >
                <span>{file ? `📄 ` : 'Selectează Video'}</span>
              </button>
            </div>

            {file && (
              <button
                onClick={handleUpload}
                disabled={loading}
                className="mt-4 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl font-medium hover:shadow-lg transition-all disabled:opacity-50"
              >
                {loading ? 'Traducere video...' : `📤 Traduce Video ${srcLang.toUpperCase()} → RO`}
              </button>
            )}

            {error && <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600">{error}</div>}
            
            {result && (
              <div className="mt-6 p-6 bg-green-50 border border-green-200 rounded-xl text-left">
                <h3 className="font-bold text-green-800 mb-3">✅ Traducere video completă!</h3>
                <div className="space-y-2 text-sm text-gray-700">
                  <p><strong>Fișier original:</strong> {result.originalFile}</p>
                  <p><strong>Limba originală:</strong> {result.originalLanguage}</p>
                  <p><strong>Limba tradusă:</strong> {result.translatedLanguage}</p>
                </div>
                {result.downloadUrl && (
                  <a
                    href={`http://localhost:5000/download/${result.downloadUrl}`}
                    className="mt-4 inline-block px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    download
                  >
                    📥 Descarcă Video Tradus
                  </a>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// ========== III.1 - Subtitle RO ==========
const SubtitleROPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [attachMode, setAttachMode] = useState<string>('soft');
  const [detailLevel, setDetailLevel] = useState<string>('medium');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [percent, setPercent] = useState(0);
  const [eta, setEta] = useState<number | null>(null);
  const [stage, setStage] = useState<string>("");
  const [detail, setDetail] = useState<string>("");
  const [showProgress, setShowProgress] = useState(false);
  const [summary, setSummary] = useState<string>("");
  const [displayedSummary, setDisplayedSummary] = useState<string>("");

  useEffect(() => {
    const es = new EventSource("http://127.0.0.1:5000/events");
    es.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (data.type === "task_progress") {
          if (typeof data.percent === "number") setPercent(Math.round(data.percent));
          if (typeof data.eta_seconds === "number") setEta(data.eta_seconds);
          if (typeof data.stage === "string") setStage(data.stage);
          if (typeof data.detail === "string") setDetail(data.detail);
          setShowProgress(true);
        }
      } catch {
        /* ignore */
      }
    };
    es.onerror = () => es.close();
    return () => es.close();
  }, []);

  const formatEta = (seconds: number | null) => {
    if (seconds === null) return "";
    const s = Math.max(0, Math.round(seconds));
    const m = Math.floor(s / 60);
    const rem = s % 60;
    return `${m}m ${rem.toString().padStart(2, '0')}s`;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setResult(null);
      setPercent(0);
      setEta(null);
      setStage("");
      setDetail("");
      setShowProgress(false);
      setSummary("");
      setDisplayedSummary("");
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setPercent(0);
    setEta(null);
    setStage("pregătire");
    setDetail("");
    setShowProgress(true);
    setSummary("");
    setDisplayedSummary("");

    try {
      const data = await uploadFile('/subtitle-ro', file, { attach: attachMode, detail_level: detailLevel });
      setResult(data);
      if (data.summary) setSummary(data.summary);
      setPercent(100);
      setEta(0);
      setStage("gata");
      setDetail("complet");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Efect de scriere pentru rezumat
  useEffect(() => {
    if (!summary) {
      setDisplayedSummary("");
      return;
    }
    setDisplayedSummary("");
    let idx = 0;
    const interval = setInterval(() => {
      idx += 4;
      setDisplayedSummary(summary.slice(0, idx));
      if (idx >= summary.length) {
        clearInterval(interval);
      }
    }, 20);
    return () => clearInterval(interval);
  }, [summary]);

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl mb-6 shadow-lg fade-up" style={{padding: '1.5rem'}}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="flex items-start gap-4">
            <div className="bg-gradient-to-br from-green-400 to-emerald-400 w-16 h-16 rounded-xl flex items-center justify-center shadow-lg">
              <Subtitles className="w-8 h-8 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">III.1 - Subtitrare în Limba Originală (RO → RO)</h2>
              <p className="text-gray-600 mb-2">Generare automată de subtitrare + rezumat video</p>
              <p className="text-xs text-gray-400 font-mono">Endpoint: POST /api/subtitle-ro</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        <div className="lg:col-span-2">
          <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg fade-up-delay-2" style={{padding: '2rem'}}>
            <div className="liquidGlass-effect" />
            <div className="liquidGlass-tint" />
            <div className="liquidGlass-shine" />
            <div className="liquidGlass-content">
              <div className="border-2 border-dashed border-green-300 rounded-xl p-10 text-center">
                <Upload className="w-16 h-16 mx-auto text-green-400 mb-4" />
                
                <div className="mb-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                  <div>
                    <label className="block mb-2 font-semibold text-gray-700">Mod atașare subtitrare:</label>
                    <select
                      value={attachMode}
                      onChange={(e) => setAttachMode(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                    >
                      <option value="soft">Soft (detașabil - .srt separat)</option>
                      <option value="hard">Hard (burnt-in - încorporat în video)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block mb-2 font-semibold text-gray-700">Nivel detaliu rezumat:</label>
                    <select
                      value={detailLevel}
                      onChange={(e) => setDetailLevel(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                    >
                      <option value="brief">Succint</option>
                      <option value="medium">Standard</option>
                      <option value="deep">Detaliat</option>
                    </select>
                  </div>
                </div>

                <p className="text-gray-600 mb-4">Încarcă video în română (.mp4, .avi, .mov, .mkv)</p>

                <input
                  type="file"
                  accept=".mp4,.avi,.mov,.mkv,.webm"
                  onChange={handleFileChange}
                  className="hidden"
                  id="subtitle-ro-input"
                />

                <div className="flex flex-col items-center gap-4 max-w-md mx-auto">
                  <div className="button-wrap button-wrap-green w-full">
                    <div className="button-shadow"></div>
                    <button 
                      className="glass-btn glass-btn-green w-full"
                      onClick={() => document.getElementById('subtitle-ro-input')?.click()}
                      type="button"
                    >
                      <span className="truncate">{file ? `📄 ${file.name}` : 'Selectează Video'}</span>
                    </button>
                  </div>

                  {file && (
                    <div className="button-wrap button-wrap-purple w-full">
                      <div className="button-shadow"></div>
                      <button
                        onClick={handleUpload}
                        disabled={loading}
                        className="glass-btn glass-btn-purple w-full"
                      >
                        <span className="truncate">{loading ? 'Procesare...' : '🎬 Subtitrare + Rezumat'}</span>
                      </button>
                    </div>
                  )}
                </div>

                {showProgress && (
                  <div className="mt-6 text-left space-y-2 p-4 bg-white/60 border border-green-100 rounded-xl shadow-sm">
                    <div className="flex justify-between text-sm text-gray-700">
                      <span className="font-medium">Progres: {percent}% {stage && `(${stage})`}</span>
                      <span className="text-gray-500">ETA: {formatEta(eta)}</span>
                    </div>
                    {detail && <div className="text-xs text-gray-500">Etapă: {detail}</div>}
                    <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-green-400 to-emerald-500 transition-all"
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                  </div>
                )}

                {error && <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600">{error}</div>}
                
                {result && (
                  <div className="mt-6 p-6 bg-green-50 border border-green-200 rounded-xl text-left">
                    <h3 className="font-bold text-green-800 mb-3">✅ Subtitrare generată!</h3>
                    <div className="space-y-2 text-sm text-gray-700">
                      <p><strong>Fișier original:</strong> {result.originalFile}</p>
                      {result.subtitle_file && <p><strong>Fișier SRT:</strong> {result.subtitle_file}</p>}
                      {result.segments && <p><strong>Total segmente:</strong> {result.segments}</p>}
                    </div>
                    <div className="mt-4 space-y-3">
                      {(result.video_file || result.downloadUrl || result.subtitle_file) && (
                        <div className="button-wrap button-wrap-green w-full">
                          <div className="button-shadow"></div>
                          <a
                            href={`http://localhost:5000${result.video_file || result.downloadUrl || result.subtitle_file}`}
                            className="glass-btn glass-btn-green w-full flex items-center justify-center gap-2 leading-none"
                            download
                          >
                            <Download className="w-5 h-5 flex-shrink-0" />
                            <span className="truncate">Descarcă rezultat</span>
                          </a>
                        </div>
                      )}
                      <div className="flex flex-wrap gap-3">
                        {result.subtitle_file && (
                          <div className="button-wrap button-wrap-blue">
                            <div className="button-shadow"></div>
                            <a
                              href={`http://localhost:5000${result.subtitle_file}`}
                              className="glass-btn glass-btn-blue flex items-center gap-2 px-4"
                              download
                            >
                              <Download className="w-4 h-4" />
                              <span>SRT</span>
                            </a>
                          </div>
                        )}
                        {result.video_file && (
                          <div className="button-wrap button-wrap-purple">
                            <div className="button-shadow"></div>
                            <a
                              href={`http://localhost:5000${result.video_file}`}
                              className="glass-btn glass-btn-purple flex items-center gap-2 px-4"
                              download
                            >
                              <Download className="w-4 h-4" />
                              <span>Video</span>
                            </a>
                          </div>
                        )}
                        {result.summary_file && (
                          <div className="button-wrap button-wrap-green">
                            <div className="button-shadow"></div>
                            <a
                              href={`http://localhost:5000${result.summary_file}`}
                              className="glass-btn glass-btn-green flex items-center gap-2 px-4"
                              download
                            >
                              <Download className="w-4 h-4" />
                              <span>Rezumat</span>
                            </a>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-1">
          <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg fade-up-delay-3 sticky top-6" style={{padding: '1.25rem'}}>
            <div className="liquidGlass-effect" />
            <div className="liquidGlass-tint" />
            <div className="liquidGlass-shine" />
            <div className="liquidGlass-content">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <p className="text-xs uppercase tracking-wide text-emerald-500 font-semibold">Rezumat video</p>
                  <h3 className="text-lg font-bold text-gray-800">Insight rapid</h3>
                </div>
                <span className="text-xs px-3 py-1 rounded-full bg-emerald-100 text-emerald-700 border border-emerald-200">
                  live typing
                </span>
              </div>
              <div className="p-3 rounded-2xl bg-white/60 border border-emerald-100 shadow-inner min-h-[180px]">
                {displayedSummary ? (
                  <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed font-mono">{displayedSummary}</p>
                ) : (
                  <p className="text-sm text-gray-400 italic">Rezumatul va apărea aici automat după procesare.</p>
                )}
              </div>
              {summary && (
                <div className="button-wrap button-wrap-green w-full mt-3">
                  <div className="button-shadow"></div>
                  <button
                    onClick={() => navigator.clipboard.writeText(summary)}
                    className="glass-btn glass-btn-green w-full text-sm"
                  >
                    Copiază rezumat
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ========== III.2 - Redub Video ==========
const RedubVideoPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [srcLang, setSrcLang] = useState<string>('ro');
  const [destLang, setDestLang] = useState<string>('en');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    try {
      const data = await uploadFile('/redub-video', file, { src_lang: srcLang, dest_lang: destLang });
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl mb-6 shadow-lg fade-up" style={{padding: '1.5rem'}}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="flex items-start gap-4">
            <div className="bg-gradient-to-br from-green-400 to-emerald-400 w-16 h-16 rounded-xl flex items-center justify-center shadow-lg">
              <Video className="w-8 h-8 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">III.2 - Redublare Video (Audio Înlocuit)</h2>
              <p className="text-gray-600 mb-2">Traducere audio RO ↔ EN + înlocuire + rezumat</p>
              <p className="text-xs text-gray-400 font-mono">Endpoint: POST /api/redub-video</p>
            </div>
          </div>
        </div>
      </div>

      <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg fade-up-delay-2" style={{padding: '2rem'}}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="border-2 border-dashed border-green-300 rounded-xl p-12 text-center">
            <Upload className="w-16 h-16 mx-auto text-green-400 mb-4" />
            
            <div className="mb-6 flex gap-4 justify-center">
              <div>
                <label className="block mb-2 font-semibold text-gray-700">Din limba:</label>
                <select
                  value={srcLang}
                  onChange={(e) => setSrcLang(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                >
                  <option value="ro">🇷🇴 Română</option>
                  <option value="en">🇬🇧 Engleză</option>
                </select>
              </div>
              <div>
                <label className="block mb-2 font-semibold text-gray-700">În limba:</label>
                <select
                  value={destLang}
                  onChange={(e) => setDestLang(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                >
                  <option value="en">🇬🇧 Engleză</option>
                  <option value="ro">🇷🇴 Română</option>
                </select>
              </div>
            </div>

            <p className="text-gray-600 mb-4">Încarcă video pentru redublare (.mp4, .avi, .mov, .mkv)</p>

            <input
              type="file"
              accept=".mp4,.avi,.mov,.mkv,.webm"
              onChange={handleFileChange}
              className="hidden"
              id="redub-video-input"
            />

            <div className="button-wrap button-wrap-green" style={{ display: 'inline-block' }}>
              <div className="button-shadow"></div>
              <button 
                className="glass-btn-green"
                onClick={() => document.getElementById('redub-video-input')?.click()}
                type="button"
              >
                <span>{file ? `📄 ` : 'Selectează Video'}</span>
              </button>
            </div>

            {file && (
              <button
                onClick={handleUpload}
                disabled={loading}
                className="mt-4 px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-xl font-medium hover:shadow-lg transition-all disabled:opacity-50"
              >
                {loading ? 'Redublare în curs...' : `🎙️ Redublează ${srcLang.toUpperCase()} → ${destLang.toUpperCase()}`}
              </button>
            )}

            {error && <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600">{error}</div>}
            
            {result && (
              <div className="mt-6 p-6 bg-green-50 border border-green-200 rounded-xl text-left">
                <h3 className="font-bold text-green-800 mb-3">✅ Redublare completă!</h3>
                <div className="space-y-2 text-sm text-gray-700">
                  <p><strong>Fișier original:</strong> {result.originalFile}</p>
                  <p><strong>Limba originală:</strong> {result.originalLanguage}</p>
                  <p><strong>Limba țintă:</strong> {result.targetLanguage}</p>
                </div>
                {result.downloadUrl && (
                  <a
                    href={`http://localhost:5000/download/${result.downloadUrl}`}
                    className="mt-4 inline-block px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    download
                  >
                    📥 Descarcă Video Redublat
                  </a>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// ========== IV - Live Subtitle ==========
const LiveSubtitlePage: React.FC = () => {
  const [sessionId] = useState<string>(() => `session_${Date.now()}`);
  const [participants] = useState([
    { id: 'user1', name: 'Ion', language: 'ro' },
    { id: 'user2', name: 'Ivan', language: 'ru' }
  ]);
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startSession = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/live-start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, participants })
      });
      
      if (!response.ok) throw new Error('Failed to start session');
      
      setIsActive(true);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const stopSession = async () => {
    try {
      await fetch('http://localhost:5000/api/live-stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
      setIsActive(false);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl mb-6 shadow-lg fade-up" style={{padding: '1.5rem'}}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="flex items-start gap-4">
            <div className="bg-gradient-to-br from-orange-400 to-red-400 w-16 h-16 rounded-xl flex items-center justify-center shadow-lg">
              <MessageSquare className="w-8 h-8 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">IV - Subtitrare Bidirecțională Live (RO ↔ RU)</h2>
              <p className="text-gray-600 mb-2">Dialog în timp real între 2+ persoane cu subtitrări simultane</p>
              <p className="text-xs text-gray-400 font-mono">Endpoint: WebSocket /api/live-start</p>
            </div>
          </div>
        </div>
      </div>

      <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg fade-up-delay-2" style={{padding: '2rem'}}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="border-2 border-solid border-orange-300 rounded-xl p-12 text-center">
            <Radio className="w-16 h-16 mx-auto text-orange-400 mb-4" />
            
            <div className="mb-6 text-left bg-white/50 rounded-xl p-4">
              <p className="font-semibold mb-2">📋 Detalii sesiune:</p>
              <p><strong>Session ID:</strong> {sessionId}</p>
              <p><strong>Status:</strong> {isActive ? '🟢 Activ' : '🔴 Inactiv'}</p>
              <p className="mt-2"><strong>Participanți:</strong></p>
              <ul className="ml-4 mt-1">
                {participants.map(p => (
                  <li key={p.id}>• {p.name} ({p.language.toUpperCase()})</li>
                ))}
              </ul>
            </div>

            <p className="text-gray-600 mb-6">Funcționalitate în timp real - WebSocket</p>

            {!isActive ? (
              <button
                onClick={startSession}
                className="px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl font-medium hover:shadow-lg transition-all"
              >
                🎙️ Pornește Sesiune Live
              </button>
            ) : (
              <button
                onClick={stopSession}
                className="px-6 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-xl font-medium hover:shadow-lg transition-all"
              >
                ⏹️ Oprește Sesiune
              </button>
            )}

            {error && <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600">{error}</div>}
          </div>
        </div>
      </div>
    </div>
  );
};

// ========== MAIN APP ==========
const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState("home");
  const [backendStatus, setBackendStatus] = useState<string>("checking");

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/health');
        setBackendStatus(response.ok ? "online" : "offline");
      } catch {
        setBackendStatus("offline");
      }
    };
    checkBackend();
    const interval = setInterval(checkBackend, 30000);
    return () => clearInterval(interval);
  }, []);

  const renderPage = () => {
    switch (currentPage) {
      // I - Analiză și stocare
      case "ppt": return <PPTAnalysisPage />;
      case "word-pdf": return <WordPDFAnalysisPage />;
      case "image-ocr": return <ImageOCRPage />;
      
      // II - Traducere multilingvă
      case "translate-docs": return <TranslateDocsPage />;
      case "translate-audio": return <TranslateAudioPage />;
      case "translate-video": return <TranslateVideoPage />;
      
      // III - Subtitrare și redublaj
      case "subtitle-ro": return <SubtitleROPage />;
      case "redub-video": return <RedubVideoPage />;
      
      // IV - Live subtitle
      case "live-subtitle": return <LiveSubtitlePage />;
      
      default: return <HomeCards onNavigate={setCurrentPage} />;
    }
  };

  return (
    <ErrorBoundary>
      <div className="min-h-screen flex flex-col relative">
        <GlobalKeyframes />
        <BackgroundFX />
        <NavBar currentPage={currentPage} onNavigate={setCurrentPage} backendStatus={backendStatus} />
        <main className="flex-1">{renderPage()}</main>
        <Footer />
      </div>
    </ErrorBoundary>
  );
};

export default App;
