import React, { useMemo, useState } from "react";
import { FileText, Video, Subtitles, Download, Upload, CheckCircle, Loader, AlertCircle, X } from "lucide-react";

/* =====================================================
   ✅ Cerințe implementate (FINAL + GLASS EFFECT)
   1) DOAR App.tsx modificat.
   2) "Rezumat Document": alegere între REZUMAT și TRADUCERE INTEGRALĂ.
   3) "Subtitrare": două căsuțe de selecție limbă (din/în)
   4) Fundal alb-albastru, animații FOARTE lente
   5) ✨ FADE-UP animations pentru carduri
   6) ✨ GLASS EFFECT pe header și footer cu sticky/fixed positioning
   ===================================================== */

// ---- CONFIG ----
const API_BASE_URL = "http://localhost:5000/api";

// ---- Limbi ----
type Lang = "en" | "zh" | "ru" | "ja" | "ro";
const LANG_LABEL: Record<Lang | "ro", string> = {
  en: "🇬🇧 Engleză (EN)",
  zh: "🇨🇳 Chineză (ZH)",
  ru: "🇷🇺 Rusă (RU)",
  ja: "🇯🇵 Japoneză (JA)",
  ro: "🇷🇴 Română (RO)",
};

// ---------- Global Keyframes + Liquid Glass Effect ----------
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
    <style>{`

      @keyframes colorShift { 0% { filter:hue-rotate(0deg) } 100% { filter:hue-rotate(60deg) } }
      @keyframes slowPan { 0% { background-position:0% 0% } 100% { background-position:300% 300% } }
      @keyframes floatXY { 0% { transform: translate(0,0) } 50% { transform: translate(10px,-10px) } 100% { transform: translate(0,0) } }
      @keyframes sparkle { 0% { opacity: .12; transform: translateY(0) } 50% { opacity: .35; transform: translateY(2px) } 100% { opacity: .12; transform: translateY(0) } }
      @keyframes grainShift { 0%{ transform:translate(0,0) } 100%{ transform:translate(-80px,-80px) } }
      @keyframes shineSweep { 0% { transform: rotate(0deg) } 100% { transform: rotate(360deg) } }
      @keyframes glowPulse { 0%,100% { opacity:.18 } 50% { opacity:.3 } }
      @keyframes fadeUp { 
        0% { opacity: 0; transform: translateY(30px); }
        100% { opacity: 1; transform: translateY(0); }
      }
      @keyframes liquidFlow {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
      }
      @keyframes waveMove {
        0% { transform: translateX(0) translateY(0); }
        50% { transform: translateX(-25px) translateY(15px); }
        100% { transform: translateX(0) translateY(0); }
      }
      

      /* Dropdown glass effect - Enhanced */
      select {
        position: relative;
      }

      select option {
        background: rgba(255, 255, 255, 0.98) !important;
        padding: 14px 16px !important;
        font-weight: 500 !important;
        color: #1f2937 !important;
        transition: all 0.2s ease !important;
      }

      select option:checked {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.95) 0%, rgba(96, 165, 250, 0.9) 100%) !important;
        color: white !important;
        font-weight: 600 !important;
      }

      select option:hover {
        background: linear-gradient(135deg, rgba(147, 197, 253, 0.3) 0%, rgba(191, 219, 254, 0.25) 100%) !important;
        color: #1e40af !important;
      }

      /* Dropdown list container styling (WebKit) */
      select::-webkit-scrollbar {
        width: 8px;
      }

      select::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(10px);
      }

      select::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, rgba(59, 130, 246, 0.6), rgba(96, 165, 250, 0.6));
        border-radius: 4px;
      }

      select::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, rgba(59, 130, 246, 0.8), rgba(96, 165, 250, 0.8));
      }
        
      /* LIQUID GLASS STYLES - Enhanced water effect */
      .liquidGlass-wrapper {
        position: relative;
        display: flex;
        font-weight: 600;
        overflow: hidden;
        color: black;
        cursor: pointer;
        box-shadow: 0 8px 12px rgba(0, 0, 0, 0.25), 0 0 30px rgba(59, 130, 246, 0.15);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 2.2);
      }
      
      .liquidGlass-effect {
        position: absolute;
        z-index: 0;
        inset: 0;
        backdrop-filter: blur(8px) saturate(180%);
        -webkit-backdrop-filter: blur(8px) saturate(180%);
        filter: url(#glass-distortion);
        overflow: hidden;
        isolation: isolate;
      }
      
      .liquidGlass-tint {
        z-index: 1;
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.3) 0%, rgba(191, 219, 254, 0.25) 100%);
        animation: waveMove 6s ease-in-out infinite;
      }
      
      .liquidGlass-shine {
        position: absolute;
        inset: 0;
        z-index: 2;
        overflow: hidden;
        box-shadow: inset 3px 3px 2px 0 rgba(255, 255, 255, 0.6),
          inset -2px -2px 2px 1px rgba(255, 255, 255, 0.5),
          inset 0 0 20px rgba(147, 197, 253, 0.2);
      }
      
      .liquidGlass-content {
        flex: 1;
        position: relative;
        z-index: 3;
      }
      
      /* Card specific hover effect */
      .liquidGlass-card {
        padding: 2.5rem;
        border-radius: 3rem;
      }
      
      .liquidGlass-card:hover {
        padding: 2.8rem;
        border-radius: 3.5rem;
      }
      
      .liquidGlass-card:hover .card-icon {
        transform: scale(0.95);
      }
      
      .card-icon {
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 2.2);
      }
      
      /* Header/Footer specific */
      .liquidGlass-header,
      .liquidGlass-footer {
        padding: 0.6rem;
      }
      
      .liquidGlass-header:hover,
      .liquidGlass-footer:hover {
        padding: 0.8rem;
      }
      
      .fade-up {
        animation: fadeUp 1.5s ease-out forwards;
      }
      
      .fade-up-delay-1 {
        animation: fadeUp 1.5s ease-out 0.1s forwards;
        opacity: 0;
      }
      
      .fade-up-delay-2 {
        animation: fadeUp 1.5s ease-out 0.2s forwards;
        opacity: 0;
      }
      
      .fade-up-delay-3 {
        animation: fadeUp 1.5s ease-out 0.3s forwards;
        opacity: 0;
      }
      
      @media (prefers-reduced-motion: reduce) { 
        [data-anim], .fade-up, .fade-up-delay-1, .fade-up-delay-2, .fade-up-delay-3,
        .liquidGlass-wrapper, .card-icon { 
          animation: none !important; 
          transform: none !important;
          opacity: 1 !important;
          transition: none !important;
        } 
      }
    `}</style>
  </>
);

// ---------- Error Boundary ----------
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

// ---------- Animated Background ----------
const BackgroundFX: React.FC = () => {
  const GRAIN_URL = useMemo(() => {
    const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120' viewBox='0 0 120 120'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)' opacity='0.35'/></svg>`;
    return `data:image/svg+xml;utf8,${svg}`;
  }, []);

  const blobs = Array.from({ length: 6 }).map((_, i) => ({
    id: i,
    size: 240 + (i % 3) * 110,
    top: `${(i * 13) % 85 + 5}%`,
    left: `${(i * 19) % 85 + 5}%`,
    duration: 120 + (i % 5) * 40,
    delay: i * 1.2,
    even: i % 2 === 0,
  }));

  const sparkles = Array.from({ length: 20 }).map((_, i) => ({
    id: i,
    top: `${(i * 7) % 100}%`,
    left: `${(i * 13) % 100}%`,
    size: (i % 3) + 1,
    delay: (i % 10) * 1.2,
    duration: 30 + (i % 6) * 10,
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
        <div key={b.id} data-anim className={`absolute rounded-full ${b.even ? "blur-3xl opacity-[0.16]" : "blur-2xl opacity-[0.10]"}`} style={{
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

      {sparkles.map((s) => (
        <span key={`s-${s.id}`} data-anim className="absolute rounded-full bg-white/70 shadow-[0_0_14px_rgba(255,255,255,0.6)]" style={{
          top: s.top,
          left: s.left,
          width: s.size,
          height: s.size,
          animation: `sparkle ${s.duration}s ease-in-out ${s.delay}s infinite`,
        }} />
      ))}

      <div data-anim className="absolute inset-0 opacity-[0.05] mix-blend-overlay" style={{ backgroundImage: `url("${GRAIN_URL}")`, animation: "grainShift 16s steps(6) infinite" }} />
    </div>
  );
};

// ================= Types =================
interface ApiResponse { summary?: string; bullets?: string[]; jobId?: string; downloadUrl?: string; file_path?: string }
interface JobStatus { status: "queued" | "running" | "done" | "error"; resultUrl?: string; log?: string }
interface ProcessedFile { id: string; name: string; type: string; status: "pending" | "processing" | "completed" | "error"; progress: number; result?: any; error?: string; downloadUrl?: string }

// ================= Mock & Real APIs =================
const mockApi = {
  summarize: async (_formData: FormData): Promise<ApiResponse> => {
    await new Promise((r) => setTimeout(r, 700));
    return { summary: "Acesta este un rezumat generat automat...", bullets: ["Punct cheie 1", "Punct cheie 2", "Punct cheie 3"] };
  },
  translateDoc: async (_formData: FormData): Promise<ApiResponse> => {
    await new Promise((r) => setTimeout(r, 800));
    return { downloadUrl: `doc_ro_${Date.now()}.pdf` };
  },
  subtitles: async (_formData: FormData) => ({ jobId: `sub_${Date.now()}` }),
  dubbing: async () => ({ jobId: `dub_${Date.now()}` }),
  getStatus: async (jobId: string): Promise<JobStatus> => {
    await new Promise((r) => setTimeout(r, 900));
    return { status: "done", resultUrl: `https://example.com/result/${jobId}.mp4`, log: "Procesare finalizată cu succes" };
  },
};

const realApi = {
  checkHealth: async (): Promise<boolean> => {
    try { const res = await fetch(`${API_BASE_URL}/health`); return res.ok } catch { return false }
  },
  summarizeOrTranslateDoc: async (
    file: File,
    mode: "summary" | "translation",
    srcLang: Lang,
    destLang: Lang,
    detailLevel: number = 50,
    youtubeLink: string = ""
  ): Promise<any> => {
    const form = new FormData();
    form.append("file", file);
    form.append("service", mode === "summary" ? "summarize" : "translation");
    form.append("src_lang", srcLang);
    form.append("dest_lang", destLang);
    form.append("detail_level", detailLevel.toString());
    form.append("youtube_link", youtubeLink);

    const endpoint = mode === "summary" ? "/summarize" : "/translation";
    const response = await fetch(`${API_BASE_URL}${endpoint}`, { method: "POST", body: form });
    if (!response.ok) { try { const e = await response.json(); throw new Error(e?.error || e?.message || "Processing failed") } catch { throw new Error("Processing failed") } }
    return response.json();
  },
  createSubtitles: async (
    file: File,
    srcLang: Lang,
    destLang: Lang
  ): Promise<any> => {
    const form = new FormData();
    form.append("file", file);
    form.append("service", "subtitles");
    form.append("src_lang", srcLang);
    form.append("dest_lang", destLang);

    const response = await fetch(`${API_BASE_URL}/subtitles`, { method: "POST", body: form });
    if (!response.ok) { try { const e = await response.json(); throw new Error(e?.error || e?.message || "Processing failed") } catch { throw new Error("Processing failed") } }
    return response.json();
  },
  createDubbing: async (file: File): Promise<any> => {
    const form = new FormData();
    form.append("file", file);
    const response = await fetch(`${API_BASE_URL}/dubbing`, { method: "POST", body: form });
    if (!response.ok) { try { const e = await response.json(); throw new Error(e?.error || e?.message || "Processing failed") } catch { throw new Error("Processing failed") } }
    return response.json();
  },
};

// ================= UI Components =================
const Footer: React.FC = () => (
  <footer className="liquidGlass-wrapper liquidGlass-footer sticky bottom-0 left-0 right-0 z-40 mt-auto rounded-3xl mx-4 mb-4">
    <div className="liquidGlass-effect" />
    <div className="liquidGlass-tint" />
    <div className="liquidGlass-shine" />
    <div className="liquidGlass-content container mx-auto px-6 py-4 w-full">
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="bg-gradient-to-r from-blue-500 to-sky-500 p-1.5 rounded-lg shadow-md"><FileText className="w-5 h-5 text-white" /></div>
          <span className="text-gray-800 font-semibold">Media Processor</span>
        </div>
        <div className="text-gray-600 text-sm text-center">© 2025 Media Processor Platform. Toate drepturile rezervate.</div>
        <div className="text-gray-600 text-sm">Creat cu <span className="text-red-500">♥</span> pentru procesare multimedia</div>
      </div>
    </div>
  </footer>
);

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
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-sky-600 bg-clip-text text-transparent">Media Processor</h1>
            <p className="text-sm text-gray-600">Procesare inteligentă multimedia</p>
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

const HomeCards: React.FC<{ onNavigate: (page: string) => void; backendStatus: string }> = ({ onNavigate, backendStatus }) => {
  const services = [
    { id: "summary", title: "Rezumat/Traducere Document", description: "Alege între rezumat sau traducere integrală (EN/ZH/RU/JA → RO)", icon: FileText, color: "from-blue-400 to-sky-400", hoverColor: "hover:from-blue-500 hover:to-sky-500", endpoint: "/api/summarize | /api/translation" },
    { id: "subtitles", title: "Subtitrare Video (EN/ZH/RU/JA → RO)", description: "Alege limba sursă și destinație (RO)", icon: Subtitles, color: "from-blue-400 to-sky-400", hoverColor: "hover:from-blue-500 hover:to-sky-500", endpoint: "/api/subtitles" },
    { id: "dubbing", title: "Dublare Video", description: "Dublează videoclipuri cu voci AI naturale", icon: Video, color: "from-blue-400 to-sky-400", hoverColor: "hover:from-blue-500 hover:to-sky-500", endpoint: "/api/dubbing" },
  ];
  
  return (
    <div className="min-h-[calc(100vh-140px)]">
      <div className="container mx-auto px-4 py-20">
        <div className="text-center mb-16 fade-up">
          {/* <div className="inline-block mb-6"><div className="bg-gradient-to-br from-blue-500 to-sky-500 p-4 rounded-2xl shadow-2xl animate-pulse"><FileText className="w-16 h-16 text-white" /></div></div> */}
          <h1 className="text-6xl font-bold bg-gradient-to-r from-blue-600 via-sky-600 to-blue-700 bg-clip-text text-transparent mb-7" style={{ paddingBottom: '0.15em' }}>Media Processing Platform</h1>
          {/* <p className="text-xl text-gray-700/90 max-w-2xl mx-auto">Alege serviciul de care ai nevoie pentru a procesa fișierele tale multimedia</p>
          {backendStatus === "offline" && (
            <div className="mt-8 p-5 bg-red-50/80 border-2 border-red-200 rounded-xl max-w-2xl mx-auto shadow-lg">
              <p className="text-red-600 font-medium">⚠️ Backend server is offline. Running in demo mode.</p>
            </div> )} */}
          
        </div>
        <div className="grid md:grid-cols-3 gap-8 max-w-7xl mx-auto">
          {services.map((service, index) => {
            const Icon = service.icon as any;
            const delayClass = index === 0 ? "fade-up-delay-1" : index === 1 ? "fade-up-delay-2" : "fade-up-delay-3";
            return (
              <button 
                key={service.id} 
                onClick={() => onNavigate(service.id)} 
                className={`liquidGlass-wrapper liquidGlass-card text-center ${delayClass} flex flex-col h-full`}
              >
                <div className="liquidGlass-effect" />
                <div className="liquidGlass-tint" />
                <div className="liquidGlass-shine" />
                <div className="liquidGlass-content flex flex-col items-center w-full h-full">
                  <div className="flex-1 flex flex-col items-center justify-start w-full">
                    <div className="flex justify-center mb-8">
                      <div className={`card-icon w-24 h-24 bg-gradient-to-br ${service.color} rounded-2xl flex items-center justify-center shadow-xl`}>
                        <Icon className="w-12 h-12 text-white" />
                      </div>
                    </div>
                    <h3 className="text-2xl font-bold text-gray-800 mb-4">{service.title}</h3>
                    <p className="text-gray-600 mb-4 leading-relaxed">{service.description}</p>
                    <p className="text-xs text-gray-400 mb-6 font-mono">Endpoint: {service.endpoint}</p>
                  </div>
                  <div className={`w-full bg-gradient-to-r ${service.color} ${service.hoverColor} text-white py-3 rounded-xl font-semibold shadow-lg transition-all duration-300`}>
                    Selectează Serviciul
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

// Pentru dropdown-urile cu efect de sticlă
const GlassSelect: React.FC<{
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  label: string;
}> = ({ value, onChange, options, label }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = React.useRef<HTMLDivElement>(null);
  const selectedOption = options.find(opt => opt.value === value);

  // Close on click outside
  React.useEffect(() => {
    if (!isOpen) return;
    
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  return (
    <div className="relative" ref={dropdownRef}>
      <label className="block text-gray-700 font-medium mb-2">{label}</label>
      <div 
        className="liquidGlass-wrapper rounded-2xl cursor-pointer" 
        style={{padding: '0'}} 
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content w-full">
          <div className="px-4 py-3 flex items-center justify-between font-medium text-gray-800">
            <span>{selectedOption?.label}</span>
            <svg className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} viewBox="0 0 16 16">
              <path d="M8 11L3 6h10z" fill="#3b82f6"/>
            </svg>
          </div>
        </div>
      </div>
      

      {isOpen && (
        <div 
          className="absolute left-0 right-0 mt-2 z-50 liquidGlass-wrapper rounded-2xl shadow-2xl" 
          style={{padding: '0.5rem', maxHeight: '240px', overflow: 'hidden'}}
        >
          <div className="liquidGlass-effect" />
          <div className="liquidGlass-tint" />
          <div className="liquidGlass-shine" />
          <div className="liquidGlass-content h-full overflow-y-auto space-y-1" style={{maxHeight: '230px'}}>
            {options.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => {
                  onChange(option.value);
                  setIsOpen(false);
                }}
                className={`w-full px-4 py-3 text-left rounded-xl transition-all duration-200 font-medium ${
                  option.value === value
                    ? 'bg-gradient-to-r from-blue-500 to-sky-500 text-white shadow-lg'
                    : 'hover:bg-blue-50/80 text-gray-800'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
// ================= Pagini =================
const SummaryPage: React.FC<{ backendStatus: string }> = ({ backendStatus }) => {

  const [files, setFiles] = useState<ProcessedFile[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [mode, setMode] = useState<"summary" | "translation">("summary");
  const [srcLang, setSrcLang] = useState<Lang>("en");
  const [destLang, setDestLang] = useState<Lang>("ro");
  const [detailLevel, setDetailLevel] = useState<number>(50);
  const [youtubeLink, setYoutubeLink] = useState<string>("");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [canSubmit, setCanSubmit] = useState(false);

  // ✅ FUNCȚIILE AICI
  const removeFile = (fileId: string) => setFiles((prev) => prev.filter((f) => f.id !== fileId));

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFiles = Array.from(e.target.files || []);
    if (uploadedFiles.length === 0) return;
    
    setSelectedFiles(uploadedFiles);
    setCanSubmit(true);
    
    console.log(`${uploadedFiles.length} fișiere selectate:`, uploadedFiles.map(f => f.name));
  };

  const handleSubmit = async () => {
    if (selectedFiles.length === 0 || isProcessing) return;
    
    setIsProcessing(true);
    setCanSubmit(false);
    
    const newFiles: ProcessedFile[] = selectedFiles.map((file) => ({ 
      id: Math.random().toString(36).substr(2, 9), 
      name: file.name, 
      type: file.type, 
      status: "pending", 
      progress: 0 
    }));
    
    setFiles((prev) => [...prev, ...newFiles]);

    for (const [index, file] of selectedFiles.entries()) {
      const fileId = newFiles[index].id;
      try {
        setFiles((prev) => prev.map((f) => (f.id === fileId ? { ...f, status: "processing", progress: 15 } : f)));

        let result: any;
        if (backendStatus === "online") {
          result = await realApi.summarizeOrTranslateDoc(file, mode, srcLang, destLang, detailLevel, youtubeLink);
        } else {
          if (mode === "summary") {
            const fd = new FormData();
            fd.append("file", file);
            fd.append("service", "summarize");
            fd.append("src_lang", srcLang);
            fd.append("dest_lang", destLang);
            fd.append("detail_level", detailLevel.toString());
            fd.append("youtube_link", youtubeLink);
            result = await mockApi.summarize(fd);
          } else {
            const fd = new FormData();
            fd.append("file", file);
            fd.append("service", "translation");
            fd.append("src_lang", srcLang);
            fd.append("dest_lang", destLang);
            fd.append("detail_level", detailLevel.toString());
  fd.append("youtube_link", youtubeLink);
            result = await mockApi.translateDoc(fd);
          }
        }
        setFiles((prev) => prev.map((f) => (f.id === fileId ? { ...f, status: "completed", progress: 100, result, downloadUrl: (result && (result.downloadUrl || result.file_path)) || undefined } : f)));
      } catch (error: any) {
        setFiles((prev) => prev.map((f) => (f.id === fileId ? { ...f, status: "error", progress: 0, error: error.message || "Processing failed" } : f)));
      }
    }

    setIsProcessing(false);
    setSelectedFiles([]);
  };

  const handleCancel = () => {
    setSelectedFiles([]);
    setCanSubmit(false);
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    if (fileInput) fileInput.value = "";
    
    console.log("Selecție anulată");
  };

  return (
    
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="liquidGlass-wrapper rounded-3xl mb-6 shadow-lg fade-up" style={{padding: '1.5rem'}}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content flex items-start gap-4">
          <div className="bg-gradient-to-br from-blue-400 to-sky-400 w-16 h-16 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg"><FileText className="w-8 h-8 text-white" /></div>
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Rezumat / Traducere Document</h2>
            <p className="text-gray-600 mb-2">Alege modul de procesare și încarcă documentul</p>
            {/* <p className="text-xs text-gray-400 font-mono">Endpoints: POST /api/summarize sau POST /api/translation</p> */}
          </div>
        </div>
      </div>

      <div className="liquidGlass-wrapper rounded-3xl mb-6 shadow-lg fade-up-delay-1" style={{padding: '1.5rem'}}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content space-y-6">
          
          {/* Mod procesare */}
          <fieldset className="space-y-3">
            <legend id="mode-legend" className="block text-gray-700 font-medium">Mod procesare</legend>
            <p id="mode-help" className="text-xs text-gray-500">Alege între <strong>Rezumat</strong> (sinteză rapidă) și <strong>Traducere integrală</strong> (păstrează conținutul complet).</p>
            <div role="radiogroup" aria-labelledby="mode-legend" aria-describedby="mode-help" className="grid sm:grid-cols-2 gap-3">
              <label className="cursor-pointer rounded-2xl border border-gray-200 bg-white/80 backdrop-blur px-4 py-3 shadow-sm hover:shadow transition-all duration-300 has-[:checked]:border-blue-400 has-[:checked]:bg-blue-50/50">
                <div className="flex items-start gap-3">
                  <input type="radio" name="mode" value="summary" checked={mode === "summary"} onChange={() => setMode("summary")} className="peer mt-1 h-4 w-4 rounded-full appearance-none bg-gray-300 checked:bg-blue-500 checked:shadow-[0_0_0_2px_rgba(59,130,246,0.3)_inset,0_0_4px_1px_rgba(59,130,246,0.4)] transition-all duration-300 checked:scale-70 cursor-pointer" />
                  <div><div className="font-semibold text-gray-800">Rezumat</div></div>
                </div>
              </label>
              <label className="cursor-pointer rounded-2xl border border-gray-200 bg-white/80 backdrop-blur px-4 py-3 shadow-sm hover:shadow transition-all duration-300 has-[:checked]:border-blue-400 has-[:checked]:bg-blue-50/50">
                <div className="flex items-start gap-3">
                  <input type="radio" name="mode" value="translation" checked={mode === "translation"} onChange={() => setMode("translation")} className="peer mt-1 h-4 w-4 rounded-full appearance-none bg-gray-300 checked:bg-blue-500 checked:shadow-[0_0_8px_2px_rgba(59,130,246,0.8)_inset,0_0_4px_1px_rgba(59,130,246,0.4)] transition-all duration-300 checked:scale-70 cursor-pointer" />
                  <div><div className="font-semibold text-gray-800">Traducere integrală</div></div>
                </div>
              </label>
            </div>
          </fieldset>

          {/* Limbi - grid 2 coloane */}
          <div className="grid md:grid-cols-2 gap-6">
            <GlassSelect
              label="Limba documentului original"
              value={srcLang}
              onChange={(val) => setSrcLang(val as Exclude<Lang, "ro">)}
              options={[
                { value: "ro", label: "🇷🇴 Română (RO)" },
                { value: "en", label: "🇬🇧 Engleză (EN)" },
                { value: "zh", label: "🇨🇳 Chineză (ZH)" },
                { value: "ru", label: "🇷🇺 Rusă (RU)" },
                { value: "ja", label: "🇯🇵 Japoneză (JA)" }
              ]}
            />
            
            <GlassSelect
              label="Limba țintă"
              value={destLang}
              onChange={(val) => setDestLang(val as Lang)}
              options={[
                { value: "ro", label: "🇷🇴 Română (RO)" },
                { value: "en", label: "🇬🇧 Engleză (EN)" },
                { value: "zh", label: "🇨🇳 Chineză (ZH)" },
                { value: "ru", label: "🇷🇺 Rusă (RU)" },
                { value: "ja", label: "🇯🇵 Japoneză (JA)" }
              ]}
            />
          </div>

          {/* Slider */}
          <div>
            <label className="block text-gray-700 font-medium mb-2">Nivel de detaliere al informațiilor</label>
            <input type="range" min="1" max="100" step="1" value={detailLevel} onChange={(e) => setDetailLevel(Number(e.target.value))} className="w-full h-2 bg-gradient-to-r from-sky-300 via-blue-300 to-sky-400 rounded-lg appearance-none cursor-pointer accent-sky-600 transition-all duration-300" />
            <div className="flex justify-between text-sm text-gray-500 mt-3 font-medium">
              <span>Minim detaliat</span>
              <span>Maxim detaliat</span>
            </div>
          </div>
          
        </div>
      </div>

      {/* ✅ BLOC NOU CU BUTOANE */}
      <div className="liquidGlass-wrapper rounded-3xl mb-6 shadow-lg fade-up-delay-2" style={{padding: '2rem'}}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="border-2 border-dashed border-sky-300 rounded-xl p-12 text-center hover:border-sky-400 hover:bg-sky-50/30 transition-all">
            <Upload className="w-16 h-16 mx-auto text-sky-400 mb-4" />
            <label className="cursor-pointer">
              <span className="text-sky-600 text-lg font-semibold block mb-4">
                Încarcă documente (.pdf, .doc, .docx, .txt, .ppt, .pptx, mp3, mp4)
              </span>
              <input 
                type="file" 
                accept=".pdf,.doc,.docx,.txt,.ppt,.pptx,.mp3,.mp4" 
                multiple 
                onChange={handleFileSelect} 
                className="hidden" 
                disabled={isProcessing} 
              />
              <span className={`inline-block px-6 py-3 bg-gradient-to-r from-blue-500 to-sky-500 text-white rounded-xl font-semibold transition-all shadow-md ${
                isProcessing ? "opacity-50 cursor-not-allowed" : "hover:from-blue-600 hover:to-sky-600 hover:shadow-lg"
              }`}>
                Selectează Fișiere
              </span>
            </label>
            
            {selectedFiles.length > 0 && (
              <div className="mt-6 p-4 bg-blue-50/50 rounded-xl border border-blue-200">
                <p className="text-sm font-medium text-gray-700 mb-2">
                  📎 {selectedFiles.length} fișier{selectedFiles.length > 1 ? 'e' : ''} selectat{selectedFiles.length > 1 ? 'e' : ''}:
                </p>
                <div className="space-y-1">
                  {selectedFiles.map((file, idx) => (
                    <p key={idx} className="text-xs text-gray-600">• {file.name}</p>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* BUTOANE TRIMITE / ANULEAZĂ */}
      {canSubmit && !isProcessing && (
        <div className="liquidGlass-wrapper rounded-2xl mb-6 shadow-lg fade-up" style={{padding: '1rem'}}>
          <div className="liquidGlass-effect" />
          <div className="liquidGlass-tint" />
          <div className="liquidGlass-shine" />
          <div className="liquidGlass-content flex gap-4">
            <button
              onClick={handleSubmit}
              disabled={isProcessing}
              className="flex-1 px-6 py-4 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <CheckCircle className="w-5 h-5" />
              Trimite Fișierele ({selectedFiles.length})
            </button>
            
            <button
              onClick={handleCancel}
              disabled={isProcessing}
              className="flex-1 px-6 py-4 bg-gradient-to-r from-red-500 to-rose-500 hover:from-red-600 hover:to-rose-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <X className="w-5 h-5" />
              Anulează
            </button>
          </div>
        </div>
      )}
      <div className="liquidGlass-wrapper rounded-2xl mb-5 shadow-md fade-up-delay-3" style={{padding: '1rem'}}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="border border-cyan-300 rounded-lg p-4 text-center hover:border-cyan-400 hover:bg-cyan-50/30 transition-all duration-300">
            <input type="text" placeholder="Link YouTube" value={youtubeLink} onChange={(e) => setYoutubeLink(e.target.value)} className="w-full p-2 text-center text-cyan-600 bg-transparent border-none outline-none text-base font-medium placeholder-cyan-400 focus:placeholder-transparent transition-all" />
          </div>
        </div>
      </div>

      {isProcessing && (
        <div className="liquidGlass-wrapper rounded-3xl mb-6 shadow-lg fade-up" style={{padding: '1.5rem'}}>
          <div className="liquidGlass-effect" />
          <div className="liquidGlass-tint" />
          <div className="liquidGlass-shine" />
          <div className="liquidGlass-content">
            <p className="text-sky-700 text-center font-medium">Procesare în curs...</p>
          </div>
        </div>
      )}

      {files.length > 0 && (
        <div className="liquidGlass-wrapper rounded-3xl shadow-lg fade-up" style={{padding: '1.5rem'}}>
          <div className="liquidGlass-effect" />
          <div className="liquidGlass-tint" />
          <div className="liquidGlass-shine" />
          <div className="liquidGlass-content">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Fișiere Procesate ({files.length})</h3>
            <div className="space-y-4">
              {files.map((file) => (
                <div key={file.id} className="liquidGlass-wrapper rounded-xl shadow-sm" style={{padding: '1rem'}}>
                  <div className="liquidGlass-effect" />
                  <div className="liquidGlass-tint" />
                  <div className="liquidGlass-shine" />
                  <div className="liquidGlass-content">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        {file.status === "completed" && <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />}
                        {file.status === "processing" && <Loader className="w-5 h-5 text-blue-500 animate-spin flex-shrink-0" />}
                        {file.status === "error" && <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />}
                        <span className="text-gray-800 font-medium truncate">{file.name}</span>
                      </div>
                      <button onClick={() => removeFile(file.id)} className="p-1 hover:bg-gray-200 rounded transition-colors"><X className="w-4 h-4 text-gray-500" /></button>
                    </div>
                    {file.status === "completed" && file.result && (
                      <div className="mt-4 space-y-4">
                        {mode === "summary" && file.result.summary && (
                          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                            <h4 className="text-sm font-semibold text-gray-800 mb-2">Rezumat:</h4>
                            <p className="text-gray-700 text-sm">{file.result.summary}</p>
                          </div>
                        )}
                        {file.status === "completed" && file.downloadUrl && mode === "translation" && (
                          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                            <h4 className="text-sm font-semibold text-gray-800 mb-2">✅ Traducere generată</h4>
                            <a href={`${API_BASE_URL.replace(/\/api$/, '')}/download/${encodeURIComponent(file.downloadUrl)}`} className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-sky-500 text-white rounded-lg hover:from-blue-600 hover:to-sky-600 transition-all shadow-md text-sm font-medium">
                              <Download className="w-4 h-4" /> Descarcă Traducerea
                            </a>
                          </div>
                        )}
                      </div>
                    )}
                    {file.status === "error" && (
                      <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg"><p className="text-sm text-red-600">{file.error}</p></div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};


const SubtitlesPage: React.FC<{ backendStatus: string }> = ({ backendStatus }) => {
  const [files, setFiles] = useState<ProcessedFile[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [srcLangSub, setSrcLangSub] = useState <Lang>("en");
  const [destLangSub, setDestLangSub] = useState<Lang>("ro");

  const pollStatus = async (jobId: string): Promise<JobStatus> => mockApi.getStatus(jobId);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFiles = Array.from(e.target.files || []); if (uploadedFiles.length === 0) return;
    const newFiles: ProcessedFile[] = uploadedFiles.map((file) => ({ id: Math.random().toString(36).substr(2, 9), name: file.name, type: file.type, status: "pending", progress: 0 }));
    setFiles((prev) => [...prev, ...newFiles]); setIsProcessing(true);

    for (const [index, file] of uploadedFiles.entries()) {
      const fileId = newFiles[index].id;
      try {
        setFiles((prev) => prev.map((f) => (f.id === fileId ? { ...f, status: "processing", progress: 20 } : f)));
        let response: any;
        if (backendStatus === "online") {
          response = await realApi.createSubtitles(file, srcLangSub, destLangSub);
        } else {
          const fd = new FormData();
          fd.append("file", file);
          fd.append("service", "subtitles");
          fd.append("src_lang", srcLangSub);
          fd.append("dest_lang", destLangSub);
          response = await mockApi.subtitles(fd);
        }

        if (response.jobId) {
          setFiles((prev) => prev.map((f) => (f.id === fileId ? { ...f, progress: 50 } : f)));
          const status = await pollStatus(response.jobId);
          setFiles((prev) => prev.map((f) => (f.id === fileId ? { ...f, status: "completed", progress: 100, result: { jobId: response.jobId, ...status }, downloadUrl: status.resultUrl } : f)));
        } else {
          setFiles((prev) => prev.map((f) => (f.id === fileId ? { ...f, status: "completed", progress: 100, result: response, downloadUrl: response?.downloadUrl || response?.file_path } : f)));
        }
      } catch (error: any) {
        setFiles((prev) => prev.map((f) => (f.id === fileId ? { ...f, status: "error", progress: 0, error: error.message || "Processing failed" } : f)));
      }
    }

    setIsProcessing(false); e.target.value = "";
  };

  const removeFile = (fileId: string) => setFiles((prev) => prev.filter((f) => f.id !== fileId));

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="bg-white/80 backdrop-blur-sm border border-white/60 rounded-3xl p-6 mb-6 shadow-lg fade-up">
        <div className="flex items-start gap-4">
          <div className="bg-gradient-to-br from-blue-400 to-sky-400 w-16 h-16 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg"><Subtitles className="w-8 h-8 text-white" /></div>
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Subtitrare Video</h2>
            <p className="text-gray-600 mb-2">Selectează limba sursă și țintă (RO) și încarcă fișierul video</p>
            <p className="text-xs text-gray-400 font-mono">Backend Endpoint: POST /api/subtitles</p>
          </div>
        </div>
      </div>

      <div className="bg-white/80 backdrop-blur-sm border border-white/60 rounded-2xl p-6 mb-6 shadow-lg grid md:grid-cols-2 gap-6 fade-up-delay-1">
        <div>
          <label className="block text-gray-700 font-medium mb-2">Limba sursă</label>
          <select value={srcLangSub} onChange={(e)=>setSrcLangSub(e.target.value as Lang)} className="w-full border border-gray-300 rounded-lg px-3 py-2 bg-white">
            <option value="ro">{LANG_LABEL.ro}</option>
            <option value="en">{LANG_LABEL.en}</option>
            <option value="zh">{LANG_LABEL.zh}</option>
            <option value="ru">{LANG_LABEL.ru}</option>
            <option value="ja">{LANG_LABEL.ja}</option>
          </select>
        </div>
        <div>
          <label className="block text-gray-700 font-medium mb-2">Limba țintă</label>
          <select value={destLangSub} onChange={(e)=>setDestLangSub(e.target.value as Lang)} className="w-full border border-gray-300 rounded-lg px-3 py-2 bg-white">
            <option value="ro">{LANG_LABEL.ro}</option>
            <option value="en">{LANG_LABEL.en}</option>
            <option value="zh">{LANG_LABEL.zh}</option>
            <option value="ru">{LANG_LABEL.ru}</option>
            <option value="ja">{LANG_LABEL.ja}</option>
          </select>
        </div>
      </div>

      <div className="bg-white/80 backdrop-blur-sm border border-white/60 rounded-3xl p-8 mb-6 shadow-lg fade-up-delay-2">
        <div className="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center hover:border-blue-400 hover:bg-blue-50/50 transition-all">
          <Upload className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <label className="cursor-pointer">
            <span className="text-xl font-semibold text-gray-800 block mb-2">Încarcă Video</span>
            <span className="text-gray-500 text-sm block mb-4">Formate acceptate: MP4, WebM, AVI, MOV</span>
            <input type="file" accept="video/mp4,video/webm,video/avi,video/quicktime" multiple onChange={handleFileUpload} className="hidden" disabled={isProcessing} />
            <span className={`inline-block px-6 py-3 bg-gradient-to-r from-blue-500 to-sky-500 text-white rounded-xl font-semibold transition-all shadow-md ${isProcessing ? "opacity-50 cursor-not-allowed" : "hover:from-blue-600 hover:to-sky-600 hover:shadow-lg"}`}>{isProcessing ? "Procesare..." : "Selectează Video"}</span>
          </label>
        </div>
      </div>

      {files.length > 0 && (
        <div className="bg-white/80 backdrop-blur-sm border border-white/60 rounded-3xl p-6 shadow-lg fade-up-delay-3">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Videoclipuri Procesate ({files.length})</h3>
          <div className="space-y-4">
            {files.map((file) => (
              <div key={file.id} className="bg-gradient-to-r from-gray-50 to-gray-100 border border-gray-200 rounded-xl p-4 shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    {file.status === "completed" && <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />}
                    {file.status === "processing" && <Loader className="w-5 h-5 text-blue-500 animate-spin flex-shrink-0" />}
                    {file.status === "error" && <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />}
                    <span className="text-gray-800 font-medium truncate">{file.name}</span>
                  </div>
                  <button onClick={() => removeFile(file.id)} className="p-1 hover:bg-gray-200 rounded transition-colors"><X className="w-4 h-4 text-gray-500" /></button>
                </div>
                {file.status === "processing" && (
                  <div className="mb-3">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-gradient-to-r from-blue-500 to-sky-500 h-2 rounded-full transition-all duration-500" style={{ width: `${file.progress}%` }} />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{file.progress}% completat</p>
                  </div>
                )}
                {file.status === "completed" && file.result && (
                  <div className="mt-4 space-y-3">
                    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <h4 className="text-sm font-semibold text-gray-800 mb-2">✅ Subtitrare completă!</h4>
                      <p className="text-sm text-gray-700 mb-3">Job ID: {file.result.jobId || "demo"}</p>
                      {file.downloadUrl && (
                        <a href={file.downloadUrl} download className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-sky-500 text-white rounded-lg hover:from-blue-600 hover:to-sky-600 transition-all shadow-md text-sm font-medium">
                          <Download className="w-4 h-4" /> Descarcă Subtitrare
                        </a>
                      )}
                    </div>
                  </div>
                )}
                {file.status === "error" && (
                  <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg"><p className="text-sm text-red-600">{file.error}</p></div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const DubbingPage: React.FC<{ backendStatus: string }> = ({ backendStatus }) => {
  const [files, setFiles] = useState<ProcessedFile[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  const pollStatus = async (jobId: string): Promise<JobStatus> => mockApi.getStatus(jobId);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFiles = Array.from(e.target.files || []); if (uploadedFiles.length === 0) return;
    const newFiles: ProcessedFile[] = uploadedFiles.map((file) => ({ id: Math.random().toString(36).substr(2, 9), name: file.name, type: file.type, status: "pending", progress: 0 }));
    setFiles((prev) => [...prev, ...newFiles]); setIsProcessing(true);
    for (const [index, file] of uploadedFiles.entries()) {
      const fileId = newFiles[index].id;
      try {
        setFiles((prev) => prev.map((f) => (f.id === fileId ? { ...f, status: "processing", progress: 20 } : f)));
        let response: any;
        if (backendStatus === "online") {
          response = await realApi.createDubbing(file);
        } else {
          const fd = new FormData();
          fd.append("file", file);
          response = await mockApi.dubbing();
        }
        if (response.jobId) {
          setFiles((prev) => prev.map((f) => (f.id === fileId ? { ...f, progress: 50 } : f)));
          const status = await pollStatus(response.jobId);
          setFiles((prev) => prev.map((f) => (f.id === fileId ? { ...f, status: "completed", progress: 100, result: { jobId: response.jobId, ...status }, downloadUrl: status.resultUrl } : f)));
        } else {
          setFiles((prev) => prev.map((f) => (f.id === fileId ? { ...f, status: "completed", progress: 100, result: response, downloadUrl: response?.downloadUrl || response?.file_path } : f)));
        }
      } catch (error: any) {
        setFiles((prev) => prev.map((f) => (f.id === fileId ? { ...f, status: "error", progress: 0, error: error.message || "Processing failed" } : f)));
      }
    }
    setIsProcessing(false); e.target.value = "";
  };

  const removeFile = (fileId: string) => setFiles((prev) => prev.filter((f) => f.id !== fileId));

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="bg-white/80 backdrop-blur-sm border border-white/60 rounded-3xl p-6 mb-6 shadow-lg fade-up">
        <div className="flex items-start gap-4">
          <div className="bg-gradient-to-br from-blue-400 to-sky-400 w-16 h-16 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg"><Video className="w-8 h-8 text-white" /></div>
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Dublare Video</h2>
            <p className="text-gray-600 mb-2">Dublează videoclipuri cu voci AI naturale</p>
            <p className="text-xs text-gray-400 font-mono">Backend Endpoint: POST /api/dubbing</p>
          </div>
        </div>
      </div>
      
      <div className="bg-white/80 backdrop-blur-sm border border-white/60 rounded-3xl p-8 mb-6 shadow-lg fade-up-delay-1">
        <div className="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center hover:border-sky-400 hover:bg-sky-50/50 transition-all">
          <Upload className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <label className="cursor-pointer">
            <span className="text-xl font-semibold text-gray-800 block mb-2">Încarcă Video</span>
            <span className="text-gray-500 text-sm block mb-4">Formate acceptate: MP4, WebM, AVI, MOV</span>
            <input type="file" accept="video/mp4,video/webm,video/avi,video/quicktime" multiple onChange={handleFileUpload} className="hidden" disabled={isProcessing} />
            <span className={`inline-block px-6 py-3 bg-gradient-to-r from-blue-500 to-sky-500 text-white rounded-xl font-semibold transition-all shadow-md ${isProcessing ? "opacity-50 cursor-not-allowed" : "hover:from-blue-600 hover:to-sky-600 hover:shadow-lg"}`}>{isProcessing ? "Procesare..." : "Selectează Video"}</span>
          </label>
        </div>
      </div>
      
      {files.length > 0 && (
        <div className="bg-white/80 backdrop-blur-sm border border-white/60 rounded-3xl p-6 shadow-lg fade-up-delay-2">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Videoclipuri Procesate ({files.length})</h3>
          <div className="space-y-4">
            {files.map((file) => (
              <div key={file.id} className="bg-gradient-to-r from-gray-50 to-gray-100 border border-gray-200 rounded-xl p-4 shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    {file.status === "completed" && <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />}
                    {file.status === "processing" && <Loader className="w-5 h-5 text-blue-500 animate-spin flex-shrink-0" />}
                    {file.status === "error" && <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />}
                    <span className="text-gray-800 font-medium truncate">{file.name}</span>
                  </div>
                  <button onClick={() => removeFile(file.id)} className="p-1 hover:bg-gray-200 rounded transition-colors"><X className="w-4 h-4 text-gray-500" /></button>
                </div>
                {file.status === "processing" && (
                  <div className="mb-3">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-gradient-to-r from-blue-500 to-sky-500 h-2 rounded-full transition-all duration-500" style={{ width: `${file.progress}%` }} />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{file.progress}% completat</p>
                  </div>
                )}
                {file.status === "completed" && file.result && (
                  <div className="mt-4 space-y-3">
                    <div className="p-4 bg-sky-50 border border-sky-200 rounded-lg">
                      <h4 className="text-sm font-semibold text-gray-800 mb-2">✅ Dublare completă!</h4>
                      <p className="text-sm text-gray-700 mb-3">Job ID: {file.result.jobId}</p>
                      {file.downloadUrl && (
                        <a href={file.downloadUrl} download className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-sky-500 text-white rounded-lg hover:from-blue-600 hover:to-sky-600 transition-all shadow-md text-sm font-medium">
                          <Download className="w-4 h-4" />Descarcă Video Dublat
                        </a>
                      )}
                    </div>
                  </div>
                )}
                {file.status === "error" && (
                  <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg"><p className="text-sm text-red-600">{file.error}</p></div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ================= App (root) =================
const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState("home");
  const [backendStatus, setBackendStatus] = useState<string>("checking");

  React.useEffect(() => {
    const checkBackend = async () => {
      const isOnline = await realApi.checkHealth();
      setBackendStatus(isOnline ? "online" : "offline");
    };
    checkBackend();
    const interval = setInterval(checkBackend, 30000);
    return () => clearInterval(interval);
  }, []);

  const renderPage = () => {
    switch (currentPage) {
      case "summary": return <SummaryPage backendStatus={backendStatus} />;
      case "subtitles": return <SubtitlesPage backendStatus={backendStatus} />;
      case "dubbing": return <DubbingPage backendStatus={backendStatus} />;
      default: return <HomeCards onNavigate={setCurrentPage} backendStatus={backendStatus} />;
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
    </ErrorBoundary>)};

export default App;