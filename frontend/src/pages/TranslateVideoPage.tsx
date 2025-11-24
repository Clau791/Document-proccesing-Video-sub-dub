import React, { useState } from "react";
import { Video as VideoIcon, Upload, Link as LinkIcon, ExternalLink, FileText, Sparkles } from "lucide-react";
import { uploadFile, BASE_URL } from "../lib/api";

const TranslateVideoPage: React.FC = () => {
  const [queue, setQueue] = useState<File[]>([]);
  const [urlQueue, setUrlQueue] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showUrlInput, setShowUrlInput] = useState(false);
  const [videoUrl, setVideoUrl] = useState("");
  const [urlError, setUrlError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length) {
      const files = Array.from(e.target.files);
      setQueue((prev) => [...prev, ...files]);
      setError(null);
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
    setResults([]);

    try {
      for (const f of queue) {
        const data = await uploadFile('/translate-video', f);
        setResults((prev) => [...prev, { file: f.name, ...data }]);
      }
      for (const u of urlQueue) {
        const res = await fetch(`${BASE_URL}/api/translate-video-url`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: u })
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.error || 'Eroare la procesarea link-ului');
        }
        const data = await res.json();
        setResults((prev) => [...prev, { file: u, ...data }]);
      }
      setQueue([]);
      setUrlQueue([]);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-6 py-10 max-w-7xl">
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
              <h2 className="text-3xl font-bold text-gray-800 mb-2">II.3 - Traducere Fișiere Video</h2>
              <p className="text-gray-700 mb-1">✔️ Rezultat doar text: transcript tradus + insight, nu se generează video.</p>
              <p className="text-xs text-gray-400 font-mono">Endpoint: POST /api/translate-video</p>
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
              <div className="border-2 border-dashed border-purple-300 rounded-xl p-10 text-center h-full">
                <Upload className="w-16 h-16 mx-auto text-purple-400 mb-4" />
                <p className="text-gray-600 mb-4">Încarcă fișiere video (.mp4, .avi, .mov, .mkv)</p>

                <input
                  type="file"
                  accept=".mp4,.avi,.mov,.mkv,.webm"
                  multiple
                  onChange={handleFileChange}
                  className="hidden"
                  id="translate-video-input"
                />

                <div className="flex flex-col items-center gap-4 max-w-md mx-auto">
                  <div className="button-wrap button-wrap-blue w-full">
                    <div className="button-shadow"></div>
                    <button 
                      className="glass-btn-blue w-full"
                      onClick={() => document.getElementById('translate-video-input')?.click()}
                      type="button"
                    >
                      <span>{queue.length ? `${queue.length} fișiere în coadă` : 'Adaugă Video'}</span>
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
                    onClick={() => document.getElementById('translate-video-input')?.click()}
                  >
                    ➕ Adaugă mai multe
                  </button>

                  {(queue.length > 0 || urlQueue.length > 0) && (
                    <button
                      onClick={handleUploadQueue}
                      disabled={loading}
                      className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl font-medium hover:shadow-lg transition-all disabled:opacity-50"
                    >
                      {loading ? 'Traducere video...' : '📤 Traduce toate (detectare automată) → RO'}
                    </button>
                  )}
                </div>

                {(queue.length > 0) && (
                  <div className="mt-4 space-y-2 text-left">
                    <p className="text-sm font-semibold text-gray-700">Coadă video:</p>
                    {queue.map((f) => (
                      <div key={f.name} className="flex items-center justify-between bg-white/70 border border-gray-200 rounded-lg px-3 py-2">
                        <span className="text-sm text-gray-800 truncate">{f.name}</span>
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
                      <div key={u} className="flex items-center justify-between bg-orange-50 border border-orange-200 rounded-lg px-3 py-2">
                        <a href={u} target="_blank" rel="noreferrer" className="text-sm text-orange-700 truncate flex-1 mr-2">
                          {u}
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

                {error && <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600">{error}</div>}
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-5 h-full">
          <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg h-full fade-up-delay-3" style={{padding: '1.5rem'}}>
            <div className="liquidGlass-effect" />
            <div className="liquidGlass-tint" />
            <div className="liquidGlass-shine" />
            <div className="liquidGlass-content h-full">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center shadow-inner">
                  <FileText className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Rezultat</p>
                  <h3 className="text-xl font-bold text-gray-800">Transcript + Insight</h3>
                  <p className="text-xs text-gray-500">Doar text – fișier .txt descărcabil</p>
                </div>
              </div>

              {results.length === 0 && (
                <div className="rounded-2xl border border-dashed border-gray-200 p-4 text-gray-500 text-sm bg-white/60 flex flex-col gap-2">
                  <span>După procesare vei vedea aici transcriptul și insight-ul extras.</span>
                  <div className="flex items-center gap-2 text-xs text-purple-600">
                    <Sparkles className="w-4 h-4" />
                    <span>Textul este indexat și în căutarea inteligentă.</span>
                  </div>
                </div>
              )}

              {results.length > 0 && (
                <div className="space-y-4 max-h-[480px] overflow-y-auto pr-1">
                  {results.map((res, idx) => {
                    const download = res.download_url || res.downloadUrl;
                    return (
                      <div key={`${res.originalFile || res.file}-${idx}`} className="p-4 rounded-2xl border border-purple-100 bg-white/70 shadow-sm">
                        <div className="flex items-center justify-between gap-3 flex-wrap">
                          <div>
                            <p className="text-sm font-semibold text-gray-800">{res.originalFile || res.file}</p>
                            <p className="text-xs text-gray-500">Orig: {res.originalLanguage || 'AUTO'} → RO</p>
                          </div>
                          {download && (
                            <a
                              href={`${BASE_URL}${download}`}
                              className="inline-flex items-center gap-2 px-3 py-2 text-sm rounded-lg bg-purple-600 text-white hover:bg-purple-700"
                              download
                            >
                              📥 Descarcă .txt
                            </a>
                          )}
                        </div>
                        {res.insight && (
                          <div className="mt-3 text-sm text-gray-700">
                            <p className="font-semibold text-purple-700 mb-1">Insight:</p>
                            <p className="leading-relaxed whitespace-pre-line">{res.insight}</p>
                          </div>
                        )}
                        {res.transcript && (
                          <div className="mt-3 text-sm text-gray-700">
                            <p className="font-semibold text-purple-700 mb-1">Transcript tradus:</p>
                            <p className="leading-relaxed whitespace-pre-line">{res.transcript}</p>
                          </div>
                        )}
                        {res.note && <p className="mt-2 text-xs text-gray-500 italic">{res.note}</p>}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TranslateVideoPage;
