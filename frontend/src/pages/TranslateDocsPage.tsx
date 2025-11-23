import React, { useEffect, useState } from "react";
import { FileText, Upload, Download } from "lucide-react";
import { uploadFile, BASE_URL } from "../lib/api";

const TranslateDocsPage: React.FC = () => {
  const [queue, setQueue] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [pagesDone, setPagesDone] = useState(0);
  const [pagesTotal, setPagesTotal] = useState(0);
  const [percent, setPercent] = useState(0);
  const [showProgress, setShowProgress] = useState(false);

  useEffect(() => {
    const es = new EventSource("http://127.0.0.1:5000/events");

    es.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (typeof data.percent === "number") setPercent(data.percent);
        if (typeof data.pages_done === "number") setPagesDone(data.pages_done);
        if (typeof data.pages_total === "number") setPagesTotal(data.pages_total);
        setShowProgress(true);
      } catch { /* ignore */ }
    };

    es.onerror = () => es.close();
    return () => es.close();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length) {
      const files = Array.from(e.target.files);
      setQueue((prev) => [...prev, ...files]);
      setError(null);
      setResults([]);
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
        const data = await uploadFile('/translate-document', f); 
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
              multiple
              onChange={handleFileChange}
              className="hidden"
              id="translate-doc-input"
            />

            <div className="flex flex-col items-center gap-4  max-w-md mx-auto">
              <div className="button-wrap button-wrap-blue w-full">
                <div className="button-shadow"></div>
                <button 
                  className="glass-btn glass-btn-blue w-full"
                  onClick={() => document.getElementById('translate-doc-input')?.click()}
                  type="button"
                >
                  <span className="truncate">{queue.length ? `${queue.length} fișiere în coadă` : 'Selectează Documente'}</span>
                </button>
              </div>

              {queue.length > 0 && (
                <div className="button-wrap button-wrap-purple w-full">
                  <div className="button-shadow"></div>
                  <button
                    onClick={handleUploadQueue}
                    disabled={loading}
                    className="glass-btn glass-btn-purple w-full"
                  >
                    <span className="truncate">{loading ? 'Traducere în curs...' : 'Tradu toate în RO'}</span>
                  </button>
                </div>
              )}
            </div>

            {queue.length > 0 && (
              <div className="mt-4 space-y-2 text-left">
                <p className="text-sm font-semibold text-gray-700">Coadă documente:</p>
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
              <div className="mt-6 p-6 rounded-2xl text-left shadow-lg bg-green-600/10 border border-green-500/30 backdrop-blur-lg">
                <h3 className="font-bold text-green-800 mb-3">✅ Traducere completă!</h3>
                <div className="space-y-3 text-sm text-gray-700">
                  {results.map((res, idx) => (
                    <div key={`${res.originalFile}-${idx}`} className="p-3 rounded-xl border border-green-100 bg-white/60">
                      <p><strong>Fișier original:</strong> {res.originalFile}</p>
                      <p><strong>Limba originală:</strong> {res.originalLanguage}</p>
                      <p><strong>Limba tradusă:</strong> {res.translatedLanguage}</p>
                      {res.downloadUrl && (
                        <div className="button-wrap button-wrap-green w-full mt-3">
                          <div className="button-shadow"></div>
                          <a
                            href={`${BASE_URL}${res.downloadUrl}`}
                            className="glass-btn glass-btn-green w-full flex items-center justify-center gap-2 leading-none"
                            download
                          >
                            <Download className="w-5 h-5 flex-shrink-0" />
                            <span className="truncate">Descarcă Document Tradus</span>
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

export default TranslateDocsPage;
