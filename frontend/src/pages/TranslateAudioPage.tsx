import React, { useState } from "react";
import { Mic, Upload, Download } from "lucide-react";
import { uploadFile, BASE_URL } from "../lib/api";

const TranslateAudioPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await uploadFile('/translate-audio', file);
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl mb-6 shadow-lg fade-up" style={{ padding: '1.5rem' }}>
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

      <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg fade-up-delay-2" style={{ padding: '2rem' }}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="border-2 border-dashed border-purple-300 rounded-xl p-12 text-center">
            <Upload className="w-16 h-16 mx-auto text-purple-400 mb-4" />

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

            <div className="flex flex-col items-center gap-4 max-w-md mx-auto">
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
                        : 'Tradu Audio (detectare automată) → RO'}
                    </span>
                  </button>
                </div>
              )}
            </div>

            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600">
                {error}
              </div>
            )}

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

export default TranslateAudioPage;
