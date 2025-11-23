import React, { useState } from "react";
import { Video as VideoIcon, Upload } from "lucide-react";
import { uploadFile, BASE_URL } from "../lib/api";

const TranslateVideoPage: React.FC = () => {
  const [queue, setQueue] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

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

  const handleUploadQueue = async () => {
    if (!queue.length) return;
    setLoading(true);
    setError(null);
    setResults([]);

    try {
      for (const f of queue) {
        const data = await uploadFile('/translate-video', f);
        setResults((prev) => [...prev, { file: f.name, ...data }]);
      }
      setQueue([]);
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

            <p className="text-gray-600 mb-4">Încarcă fișiere video (.mp4, .avi, .mov, .mkv)</p>

            <input
              type="file"
              accept=".mp4,.avi,.mov,.mkv,.webm"
              multiple
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
                <span>{queue.length ? `${queue.length} fișiere în coadă` : 'Selectează Video'}</span>
              </button>
            </div>

            {queue.length > 0 && (
              <button
                onClick={handleUploadQueue}
                disabled={loading}
                className="mt-4 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl font-medium hover:shadow-lg transition-all disabled:opacity-50"
              >
                {loading ? 'Traducere video...' : '📤 Traduce toate (detectare automată) → RO'}
              </button>
            )}

            {queue.length > 0 && (
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

            {error && <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600">{error}</div>}
            
            {results.length > 0 && (
              <div className="mt-6 p-6 bg-green-50 border border-green-200 rounded-xl text-left">
                <h3 className="font-bold text-green-800 mb-3">✅ Traduceri video complete!</h3>
                <div className="space-y-3 text-sm text-gray-700">
                  {results.map((res, idx) => (
                    <div key={`${res.originalFile}-${idx}`} className="p-3 rounded-xl border border-green-100 bg-white/60">
                      <p><strong>Fișier original:</strong> {res.originalFile}</p>
                      <p><strong>Limba originală:</strong> {res.originalLanguage}</p>
                      <p><strong>Limba tradusă:</strong> {res.translatedLanguage}</p>
                      {res.downloadUrl && (
                        <a
                          href={`${BASE_URL}${res.downloadUrl}`}
                          className="mt-3 inline-block px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                          download
                        >
                          📥 Descarcă Video Tradus
                        </a>
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

export default TranslateVideoPage;
