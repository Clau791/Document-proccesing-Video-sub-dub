import React, { useEffect, useState } from "react";
import { Subtitles, Upload, Download, Link as LinkIcon, ExternalLink } from "lucide-react";
import { uploadFile, BASE_URL } from "../lib/api";

const SubtitleROPage: React.FC = () => {
  const shortName = (name: string) => name.length > 50 ? `${name.slice(0, 47)}...` : name;

  const [queue, setQueue] = useState<File[]>([]);
  const [urlQueue, setUrlQueue] = useState<string[]>([]);
  const [attachMode, setAttachMode] = useState<string>('hard');
  const [detailLevel, setDetailLevel] = useState<string>('medium');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [percent, setPercent] = useState(0);
  const [eta, setEta] = useState<number | null>(null);
  const [stage, setStage] = useState<string>("");
  const [detail, setDetail] = useState<string>("");
  const [showProgress, setShowProgress] = useState(false);
  const [summary, setSummary] = useState<string>("");
  const [displayedSummary, setDisplayedSummary] = useState<string>("");
  const [showUrlInput, setShowUrlInput] = useState(false);
  const [videoUrl, setVideoUrl] = useState("");
  const [urlError, setUrlError] = useState<string | null>(null);
  const [translatorMode, setTranslatorMode] = useState<"cloud" | "local">("cloud");

  useEffect(() => {
    const es = new EventSource(`${BASE_URL}/events`);
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
    if (e.target.files && e.target.files.length) {
      const files = Array.from(e.target.files);
      setQueue((prev) => [...prev, ...files]);
      setError(null);
      setResults([]);
      setPercent(0);
      setEta(null);
      setStage("");
      setDetail("");
      setShowProgress(false);
      setSummary("");
      setDisplayedSummary("");
    }
  };

  const removeFromQueue = (name: string) => {
    setQueue((prev) => prev.filter(f => f.name !== name));
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

  const handleUploadQueue = async () => {
    if (!queue.length && !urlQueue.length) return;
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
      const newResults: any[] = [];
      if (queue.length) {
        for (const f of queue) {
          const data = await uploadFile('/subtitle-ro', f, { attach: attachMode, detail_level: detailLevel, translator_mode: translatorMode });
          newResults.push({ file: f.name, ...data });
          if (data.summary) setSummary(data.summary);
        }
      }
      if (urlQueue.length) {
        for (const u of urlQueue) {
          const res = await fetch(`${BASE_URL}/api/subtitle-ro-url`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: u, attach: attachMode, detail_level: detailLevel, translator_mode: translatorMode })
          });
          if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || 'Eroare la procesarea link-ului');
          }
          const data = await res.json();
          newResults.push({ file: u, ...data });
          if (data.summary) setSummary(data.summary);
        }
      }
      setResults(newResults);
      setQueue([]);
      setUrlQueue([]);
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
    <div className="container mx-auto px-6 py-10 max-w-7xl">
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
              <h2 className="text-3xl font-bold text-gray-800 mb-2">III.1 - Subtitrare Video</h2>
              <p className="text-gray-600 mb-2">Generare automată de subtitrare + rezumat video</p>
              <p className="text-xs text-gray-400 font-mono">Endpoint: POST /api/subtitle-ro</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        <div className="lg:col-span-7 h-full">
          <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg fade-up-delay-2 h-full" style={{padding: '2rem'}}>
            <div className="liquidGlass-effect" />
            <div className="liquidGlass-tint" />
            <div className="liquidGlass-shine" />
            <div className="liquidGlass-content h-full flex flex-col">
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
                  <div>
                    <label className="block mb-2 font-semibold text-gray-700">Traducere:</label>
                    <select
                      value={translatorMode}
                      onChange={(e) => setTranslatorMode(e.target.value as "cloud" | "local")}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                    >
                      <option value="cloud">Cloud (GoogleTranslator)</option>
                      <option value="local">Local AI (Ollama qwen2.5:32b)</option>
                    </select>
                  </div>
                </div>

                <p className="text-gray-600 mb-4">Încarcă video în română (.mp4, .avi, .mov, .mkv)</p>

                <input
                  type="file"
                  accept=".mp4,.avi,.mov,.mkv,.webm"
                  multiple
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
                      <span className="truncate">{queue.length ? `${queue.length} fișiere în coadă` : 'Selectează Video'}</span>
                    </button>
                  </div>

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
                      <div className="mt-3 p-3 rounded-xl border border-orange-200 bg-white/70 space-y-2">
                        <input
                          type="text"
                          value={videoUrl}
                          onChange={(e) => setVideoUrl(e.target.value)}
                          placeholder="https://www.youtube.com/watch?v=..."
                          className="w-full px-3 py-2 border border-orange-300 rounded-lg focus:ring-2 focus:ring-orange-400"
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
                            className="px-3 py-2 text-xs rounded-lg bg-orange-500 text-white hover:bg-orange-600"
                          >
                            Adaugă în coadă
                          </button>
                        </div>
                      </div>
                    )}
                  </div>

                  <button
                    className="text-sm text-blue-600 hover:underline"
                    type="button"
                    onClick={() => document.getElementById('subtitle-ro-input')?.click()}
                  >
                    ➕ Adaugă mai multe
                  </button>

                  {queue.length > 0 && (
                    <div className="button-wrap button-wrap-purple w-full">
                      <div className="button-shadow"></div>
                      <button
                        onClick={handleUploadQueue}
                        disabled={loading}
                        className="glass-btn glass-btn-purple w-full"
                      >
                        <span className="truncate">{loading ? 'Procesare...' : '🎬 Subtitrare + Rezumat'}</span>
                      </button>
                    </div>
                  )}
                </div>

                {queue.length > 0 && (
                  <div className="mt-4 space-y-2 text-left">
                    <p className="text-sm font-semibold text-gray-700">Coadă video:</p>
                    {queue.map((f) => (
                      <div key={f.name} className="flex items-center justify-between bg-white/70 border border-gray-200 rounded-lg px-3 py-2 gap-2 min-w-0">
                        <span className="text-sm text-gray-800 truncate flex-1 min-w-0" title={f.name}>{shortName(f.name)}</span>
                        <button
                          onClick={() => removeFromQueue(f.name)}
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
                
                {results.length > 0 && (
                  <div className="mt-6 p-6 bg-green-50 border border-green-200 rounded-xl text-left space-y-4">
                    <h3 className="font-bold text-green-800 mb-2">✅ Subtitrări generate</h3>
                    {results.map((res, idx) => (
                      <div key={`${res.originalFile}-${idx}`} className="p-3 rounded-xl border border-green-100 bg-white/70 space-y-2 min-w-0">
                        <p className="flex items-center gap-2 min-w-0">
                          <strong className="whitespace-nowrap">Fișier original:</strong>
                          <span className="truncate text-gray-800 flex-1 min-w-0" title={res.originalFile}>{shortName(res.originalFile)}</span>
                        </p>
                        {res.subtitle_file && <p><strong>Fișier SRT:</strong> {res.subtitle_file}</p>}
                        {res.segments && <p><strong>Total segmente:</strong> {res.segments}</p>}
                        <div className="flex flex-wrap gap-2">
                          {(res.video_file || res.downloadUrl || res.subtitle_file) && (
                            <div className="button-wrap button-wrap-green">
                              <div className="button-shadow"></div>
                              <a
                                href={`http://localhost:5000${res.video_file || res.downloadUrl || res.subtitle_file}`}
                                className="glass-btn glass-btn-green inline-flex items-center gap-2 px-3 py-2"
                                download
                              >
                                <Download className="w-4 h-4" />
                                <span>Rezultat</span>
                              </a>
                            </div>
                          )}
                          {res.subtitle_file && (
                            <div className="button-wrap button-wrap-blue">
                              <div className="button-shadow"></div>
                              <a
                                href={`http://localhost:5000${res.subtitle_file}`}
                                className="glass-btn glass-btn-blue inline-flex items-center gap-2 px-3 py-2"
                                download
                              >
                                <Download className="w-4 h-4" />
                                <span>SRT</span>
                              </a>
                            </div>
                          )}
                          {res.video_file && (
                            <div className="button-wrap button-wrap-purple">
                              <div className="button-shadow"></div>
                              <a
                                href={`http://localhost:5000${res.video_file}`}
                                className="glass-btn glass-btn-purple inline-flex items-center gap-2 px-3 py-2"
                                download
                              >
                                <Download className="w-4 h-4" />
                                <span>Video</span>
                              </a>
                            </div>
                          )}
                          {res.summary_file && (
                            <div className="button-wrap button-wrap-green">
                              <div className="button-shadow"></div>
                              <a
                                href={`http://localhost:5000${res.summary_file}`}
                                className="glass-btn glass-btn-green inline-flex items-center gap-2 px-3 py-2"
                                download
                              >
                                <Download className="w-4 h-4" />
                                <span>Rezumat</span>
                              </a>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-5 h-full">
          <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg fade-up-delay-3 h-full" style={{padding: '1.25rem'}}>
            <div className="liquidGlass-effect" />
            <div className="liquidGlass-tint" />
            <div className="liquidGlass-shine" />
            <div className="liquidGlass-content h-full flex flex-col">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <p className="text-xs uppercase tracking-wide text-emerald-500 font-semibold">Rezumat video</p>
                  <h3 className="text-lg font-bold text-gray-800">Insight rapid</h3>
                </div>
                <span className="text-xs px-3 py-1 rounded-full bg-emerald-100 text-emerald-700 border border-emerald-200">
                  live typing
                </span>
              </div>
              <div className="p-3 rounded-2xl bg-white/60 border border-emerald-100 shadow-inner min-h-[260px]">
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

export default SubtitleROPage;
