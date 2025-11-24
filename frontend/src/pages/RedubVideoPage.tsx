import React, { useState } from "react";
import { Video, Upload, Link as LinkIcon, ExternalLink } from "lucide-react";
import { uploadFile, BASE_URL } from "../lib/api";

const RedubVideoPage: React.FC = () => {
  const [queue, setQueue] = useState<File[]>([]);
  const [urlQueue, setUrlQueue] = useState<string[]>([]);
  const [destLang, setDestLang] = useState<string>('en');
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

  const handleUploadQueue = async () => {
    if (!queue.length && !urlQueue.length) return;
    setLoading(true);
    setError(null);
    setResults([]);

    try {
      for (const f of queue) {
        const data = await uploadFile('/redub-video', f, { dest_lang: destLang });
        setResults((prev) => [...prev, { file: f.name, ...data }]);
      }
      for (const u of urlQueue) {
        const res = await fetch(`${BASE_URL}/api/redub-video-url`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: u, dest_lang: destLang })
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

              {queue.length > 0 && (
                <button
                  onClick={handleUploadQueue}
                  disabled={loading}
                  className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-xl font-medium hover:shadow-lg transition-all disabled:opacity-50"
                >
                  {loading ? 'Redublare în curs...' : `🎙️ Redublează (detectare automată) → ${destLang.toUpperCase()}`}
                </button>
              )}
            </div>

            {queue.length > 0 && (
              <div className="mt-4 space-y-2 text-left">
                <p className="text-sm font-semibold text-gray-700">Coadă video:</p>
                {queue.map((f) => (
                  <div key={f.name} className="flex items-center justify-between bg-white/70 border border-gray-200 rounded-lg px-3 py-2">
                    <span className="text-sm text-gray-800 truncate">{f.name}</span>
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
            
            {results.length > 0 && (
              <div className="mt-6 p-6 bg-green-50 border border-green-200 rounded-xl text-left">
                <h3 className="font-bold text-green-800 mb-3">✅ Redublare completă!</h3>
                <div className="space-y-3 text-sm text-gray-700">
                  {results.map((res, idx) => (
                    <div key={`${res.originalFile}-${idx}`} className="p-3 rounded-xl border border-green-100 bg-white/60">
                      <p><strong>Fișier original:</strong> {res.originalFile}</p>
                      <p><strong>Limba originală:</strong> {res.originalLanguage}</p>
                      <p><strong>Limba țintă:</strong> {res.targetLanguage}</p>
                      {(res.video_file || res.downloadUrl) && (
                        <a
                          href={`${BASE_URL}${res.video_file || res.downloadUrl}`}
                          className="mt-3 inline-block px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                          download
                        >
                          📥 Descarcă Video Redublat
                        </a>
                      )}
                      {res.subtitle_file && (
                        <div className="mt-2">
                          <a
                            href={`${BASE_URL}${res.subtitle_file}`}
                            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                            download
                          >
                            📄 Descarcă Subtitrare
                          </a>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RedubVideoPage;
