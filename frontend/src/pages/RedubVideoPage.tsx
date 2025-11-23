import React, { useState } from "react";
import { Video, Upload } from "lucide-react";
import { uploadFile, BASE_URL } from "../lib/api";

const RedubVideoPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
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
      const data = await uploadFile('/redub-video', file, { dest_lang: destLang });
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
                {loading ? 'Redublare în curs...' : `🎙️ Redublează (detectare automată) → ${destLang.toUpperCase()}`}
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
                {(result.video_file || result.downloadUrl) && (
                  <a
                    href={`${BASE_URL}${result.video_file || result.downloadUrl}`}
                    className="mt-4 inline-block px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    download
                  >
                    📥 Descarcă Video Redublat
                  </a>
                )}
                {result.subtitle_file && (
                  <div className="mt-3">
                    <a
                      href={`${BASE_URL}${result.subtitle_file}`}
                      className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                      download
                    >
                      📄 Descarcă Subtitrare
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

export default RedubVideoPage;
