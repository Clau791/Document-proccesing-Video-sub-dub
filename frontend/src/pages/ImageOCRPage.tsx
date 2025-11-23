import React, { useState } from "react";
import { Image as ImageIcon, Upload } from "lucide-react";
import { uploadFile, BASE_URL } from "../lib/api";

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
                    href={`${BASE_URL}/download/${result.downloadUrl}`}
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

export default ImageOCRPage;
