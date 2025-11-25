import React, { useState } from "react";
import { Video, Upload, Link as LinkIcon, ExternalLink, Loader2 } from "lucide-react";
import { uploadFile, BASE_URL } from "../lib/api";

const RedubVideoPage: React.FC = () => {
  const shortName = (name: string) => name.length > 50 ? `${name.slice(0, 47)}...` : name;

  const [queue, setQueue] = useState<File[]>([]);
  const [urlQueue, setUrlQueue] = useState<string[]>([]);
  const [destLang] = useState<string>('ro');
  const [detailLevel, setDetailLevel] = useState<string>('medium');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showUrlInput, setShowUrlInput] = useState(false);
  const [videoUrl, setVideoUrl] = useState("");
  const [urlError, setUrlError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [stage, setStage] = useState<string>("");
  const [translatorMode, setTranslatorMode] = useState<"cloud" | "local">("cloud");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length) {
      const files = Array.from(e.target.files);
      setQueue((prev) => [...prev, ...files]);
      setError(null);
    }
  };

  const handleUploadQueue = async () => {
    if (!queue.length && !urlQueue.length) return;
    setLoading(true);
    setError(null);
    setResults([]);
    setProgress(8);
    setStage("Pregătire...");

    try {
      const total = queue.length + urlQueue.length;
      let done = 0;
      const bump = () => {
        done += 1;
        const pct = Math.min(95, Math.round((done / Math.max(total, 1)) * 90) + 8);
        setProgress(pct);
      };

      for (const f of queue) {
        setStage(`Încărcare fișier: ${f.name}`);
        const data = await uploadFile('/redub-video', f, { dest_lang: destLang, translator_mode: translatorMode, detail_level: detailLevel });
        setResults((prev) => [...prev, { file: f.name, ...data }]);
        bump();
      }
      for (const u of urlQueue) {
        setStage(`Procesare link: ${u}`);
        const res = await fetch(`${BASE_URL}/api/redub-video-url`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: u, dest_lang: destLang, translator_mode: translatorMode, detail_level: detailLevel })
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.error || 'Eroare la procesarea link-ului');
        }
        const data = await res.json();
        setResults((prev) => [...prev, { file: u, ...data }]);
        bump();
      }
      setQueue([]);
      setUrlQueue([]);
      setStage("Finalizat");
      setProgress(100);
    } catch (err: any) {
      setError(err.message);
      setStage("Eroare");
    } finally {
      setLoading(false);
    }
  };

  const isValidVideoUrl = (url: string) => {
    const pattern = /(youtube\.com\/watch\?v=|youtu\.be\/|rutube\.ru\/)/i;
    return pattern.test(url.trim());
  };

  const addUrlToQueue = () => {
    if (!videoUrl.trim()) {
      setUrlError("Introduce un link YouTube/Rutube");
      return;
    }
    if (!isValidVideoUrl(videoUrl)) {
      setUrlError("Link invalid (acceptat: youtube sau rutube)");
      return;
    }
    setUrlQueue((prev) => [...prev, videoUrl.trim()]);
    setVideoUrl("");
    setUrlError(null);
  };

  const removeUrl = (url: string) => {
    setUrlQueue((prev) => prev.filter(u => u !== url));
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
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

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7">
          <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg fade-up-delay-2 h-full" style={{padding: '2rem'}}>
            <div className="liquidGlass-effect" />
            <div className="liquidGlass-tint" />
            <div className="liquidGlass-shine" />
            <div className="liquidGlass-content h-full">
              <div className="border-2 border-dashed border-green-300 rounded-xl p-12 text-center">
            <Upload className="w-16 h-16 mx-auto text-green-400 mb-4" />
            
            <div className="mb-6 flex flex-col gap-4">
              <div>
                <p className="font-semibold text-gray-700">Limba țintă: <span className="text-emerald-700">Română (fix)</span></p>
                <p className="text-xs text-gray-500">Redublarea se face mereu în limba română.</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block mb-2 font-semibold text-gray-700">Traducere:</label>
                  <select
                    value={translatorMode}
                    onChange={(e) => setTranslatorMode(e.target.value as "cloud" | "local")}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 w-full"
                  >
                    <option value="cloud">Cloud (GoogleTranslator)</option>
                    <option value="local">Local AI (Ollama qwen2.5:32b)</option>
                  </select>
                </div>
                <div>
                  <label className="block mb-2 font-semibold text-gray-700">Nivel detaliu rezumat:</label>
                  <select
                    value={detailLevel}
                    onChange={(e) => setDetailLevel(e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 w-full"
                  >
                    <option value="brief">Succint</option>
                    <option value="medium">Standard</option>
                    <option value="deep">Detaliat</option>
                  </select>
                </div>
              </div>
            </div>

            <p className="text-gray-600 mb-4">Încarcă video pentru redublare (.mp4, .avi, .mov, .mkv)</p>

            <input
              type="file"
              accept=".mp4,.avi,.mov,.mkv,.webm"
              multiple
              onChange={handleFileChange}
              className="hidden"
              id="redub-video-input"
            />

            <div className="flex flex-col items-center gap-4 max-w-md mx-auto">
              <div className="button-wrap button-wrap-green w-full">
                <div className="button-shadow"></div>
                <button 
                  className="glass-btn-green w-full"
                  onClick={() => document.getElementById('redub-video-input')?.click()}
                  type="button"
                >
                  <span>{queue.length ? `${queue.length} fișiere în coadă` : 'Selectează Video'}</span>
                </button>
              </div>

              <button
                className="text-sm text-blue-600 hover:underline"
                type="button"
                onClick={() => document.getElementById('redub-video-input')?.click()}
              >
                ➕ Adaugă mai multe
              </button>

              <div className="w-full">
                <div className="button-wrap w-full" style={{ '--btn-shadow': 'none' } as any}>
                  <button
                    type="button"
                    className="glass-btn w-full bg-gradient-to-r from-orange-500 to-amber-500 text-white flex items-center justify-center gap-2"
                    onClick={() => setShowUrlInput((v) => !v)}
                  >
                    <LinkIcon className="w-4 h-4" />
                    <span className="truncate">Video YouTube / Rutube</span>
                  </button>
                </div>
                {showUrlInput && (
                  <div className="mt-3 relative rounded-xl overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-r from-orange-100 via-amber-50 to-orange-100 opacity-80" />
                    <div className="relative p-4 border border-orange-200/80 backdrop-blur-sm rounded-xl shadow-sm space-y-3">
                      <div className="flex items-center gap-2 text-orange-700 font-semibold text-sm">
                        <div className="w-8 h-8 rounded-lg bg-orange-500/20 flex items-center justify-center border border-orange-200">
                          <LinkIcon className="w-4 h-4" />
                        </div>
                        <span>Adaugă link YouTube / Rutube</span>
                      </div>
                      <input
                        type="text"
                        value={videoUrl}
                        onChange={(e) => setVideoUrl(e.target.value)}
                        placeholder="https://www.youtube.com/watch?v=..."
                        className="w-full px-3 py-2 border border-orange-300 rounded-lg focus:ring-2 focus:ring-orange-400 bg-white/80"
                      />
                      {urlError && <p className="text-xs text-red-600">{urlError}</p>}
                      <div className="flex flex-wrap gap-2">
                        {isValidVideoUrl(videoUrl) && (
                          <a
                            href={videoUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-2 px-3 py-2 text-xs rounded-lg bg-orange-100 text-orange-700 border border-orange-200 hover:bg-orange-200"
                          >
                            <ExternalLink className="w-4 h-4" />
                            Preview
                          </a>
                        )}
                        <button
                          type="button"
                          onClick={addUrlToQueue}
                          className="px-3 py-2 text-xs rounded-lg bg-orange-500 text-white hover:bg-orange-600 shadow-sm"
                        >
                          Adaugă în coadă
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {(queue.length > 0 || urlQueue.length > 0) && (
                <button
                  onClick={handleUploadQueue}
                  disabled={loading}
                  className="w-full px-6 py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-emerald-500 via-teal-500 to-blue-500 shadow-lg hover:shadow-xl transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <span>🎙️</span>}
                  <span>{loading ? "Redublare în curs..." : `Redublează (auto) → ${destLang.toUpperCase()}`}</span>
                </button>
              )}
            </div>

            {queue.length > 0 && (
              <div className="mt-4 space-y-2 text-left">
                <p className="text-sm font-semibold text-gray-700">Coadă video:</p>
                {queue.map((f) => (
                  <div key={f.name} className="flex items-center justify-between bg-white/70 border border-gray-200 rounded-lg px-3 py-2 gap-2 min-w-0">
                    <span className="text-sm text-gray-800 truncate flex-1 min-w-0" title={f.name}>{shortName(f.name)}</span>
                    <button
                      onClick={() => setQueue((prev) => prev.filter(x => x.name !== f.name))}
                      className="text-xs text-red-600 hover:underline"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
            {urlQueue.length > 0 && (
              <div className="mt-4 space-y-2 text-left">
                <p className="text-sm font-semibold text-gray-700">Coadă link-uri:</p>
                {urlQueue.map((u) => (
                  <div key={u} className="flex items-center justify-between bg-orange-50 border border-orange-200 rounded-lg px-3 py-2 gap-2 min-w-0">
                    <a href={u} target="_blank" rel="noreferrer" className="text-sm text-orange-700 truncate flex-1 min-w-0" title={u}>
                      {shortName(u)}
                    </a>
                    <button
                      onClick={() => removeUrl(u)}
                      className="text-xs text-red-600 hover:underline"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}

            {(loading || progress > 0) && (
              <div className="mt-5 p-4 rounded-xl bg-white/70 border border-emerald-100 space-y-2">
                <div className="flex justify-between text-xs text-gray-600">
                  <span>{stage || "Progres redublare"}</span>
                  <span className="font-semibold text-emerald-700">{progress}%</span>
                </div>
                <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-emerald-400 via-teal-400 to-blue-400 transition-all"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}

            {error && <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600">{error}</div>}
            
            {results.length > 0 && (
              <div className="mt-6 p-6 bg-green-50 border border-green-200 rounded-xl text-left space-y-3">
                <h3 className="font-bold text-green-800 mb-2">✅ Redublare completă!</h3>
                    {results.map((res, idx) => (
                      <div key={`${res.originalFile}-${idx}`} className="p-3 rounded-xl border border-green-100 bg-white/60 space-y-2 min-w-0">
                        <p className="flex items-center gap-2 min-w-0">
                          <strong className="whitespace-nowrap">Fișier original:</strong>
                          <span className="truncate text-gray-800 flex-1 min-w-0" title={res.originalFile}>{shortName(res.originalFile)}</span>
                        </p>
                        <p><strong>Limba originală:</strong> {res.originalLanguage}</p>
                        <p><strong>Limba țintă:</strong> {res.targetLanguage}</p>
                    <div className="flex flex-wrap gap-2">
                      {(res.video_file || res.downloadUrl) && (
                        <div className="button-wrap button-wrap-green">
                          <div className="button-shadow"></div>
                          <a
                            href={`${BASE_URL}${res.video_file || res.downloadUrl}`}
                            className="glass-btn glass-btn-green inline-flex items-center gap-2 px-3 py-2"
                            download
                          >
                            🎬
                            <span>Video redublat</span>
                          </a>
                        </div>
                      )}
                      {res.subtitle_file && (
                        <div className="button-wrap button-wrap-blue">
                          <div className="button-shadow"></div>
                          <a
                            href={`${BASE_URL}${res.subtitle_file}`}
                            className="glass-btn glass-btn-blue inline-flex items-center gap-2 px-3 py-2"
                            download
                          >
                            📄
                            <span>Subtitrare</span>
                          </a>
                        </div>
                      )}
                    </div>
                    {(res.summary || res.insight) && (
                      <div className="p-3 rounded-lg bg-green-50 border border-green-100 text-sm text-gray-700">
                        <p className="font-semibold text-green-700 mb-1">Insight:</p>
                        <p className="leading-relaxed whitespace-pre-line">{res.summary || res.insight}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
          </div>
        </div>

        <div className="lg:col-span-5">
          <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg fade-up-delay-3 h-full" style={{padding: '1.25rem'}}>
            <div className="liquidGlass-effect" />
            <div className="liquidGlass-tint" />
            <div className="liquidGlass-shine" />
            <div className="liquidGlass-content h-full flex flex-col">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <p className="text-xs uppercase tracking-wide text-emerald-500 font-semibold">Insight redublare</p>
                  <h3 className="text-lg font-bold text-gray-800 leading-tight">Transcript + Observații</h3>
                </div>
                <span className="text-xs px-3 py-1 rounded-full bg-emerald-100 text-emerald-700 border border-emerald-200">
                  text only
                </span>
              </div>
              <div className="p-3 rounded-2xl bg-white/60 border border-emerald-100 shadow-inner min-h-[260px]">
                {results.length > 0 ? (
                  <div className="space-y-2 text-sm text-gray-700">
                    {results.map((res, idx) => (
                      <div key={`ins-${idx}`} className="p-2 rounded-xl bg-emerald-50 border border-emerald-100">
                        <p className="text-xs text-gray-500 truncate" title={res.originalFile}>{shortName(res.originalFile)}</p>
                        <p className="font-semibold text-emerald-700 mb-1">Insight</p>
                        <p className="leading-relaxed whitespace-pre-line">{res.summary || res.insight || "Nu a fost generat insight."}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-400 italic">Insight-urile procesărilor vor apărea aici după ce încarci un video.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RedubVideoPage;
