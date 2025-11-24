import React, { useState } from "react";
import { Search, Download } from "lucide-react";
import { BASE_URL } from "../lib/api";

type Item = {
  id: number;
  service: string;
  original_file: string;
  download_url: string;
  summary_url?: string;
  status: string;
  meta?: Record<string, any>;
  created_at: string;
};

const serviceLabel: Record<string, string> = {
  "ppt-analysis": "PPT",
  "document-analysis": "DOC",
  "image-ocr": "OCR",
  "translate-document": "Traducere Doc",
  "translate-audio": "Traducere Audio",
  "translate-video": "Traducere Video",
  "subtitle-ro": "Subtitrare",
  "redub-video": "Redublare"
};

const SearchPage: React.FC = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const doSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${BASE_URL}/api/history/search?q=${encodeURIComponent(query)}&limit=50`);
      if (!res.ok) throw new Error("Eroare la căutare");
      const data = await res.json();
      setResults(data.items || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    doSearch();
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg">
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content p-6">
          <form onSubmit={onSubmit} className="flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <Search className="w-6 h-6 text-gray-700" />
              <h2 className="text-xl font-bold text-gray-800">Căutare în istoric (natural language)</h2>
            </div>
            <div className="flex flex-col md:flex-row gap-3">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ex: traduce fișierul pdf în română cu subtitrare"
                className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="submit"
                disabled={loading}
                className="px-5 py-3 bg-gradient-to-r from-blue-500 to-sky-500 text-white rounded-xl font-medium shadow hover:shadow-lg disabled:opacity-50"
              >
                {loading ? "Caută..." : "Caută"}
              </button>
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
          </form>
        </div>
      </div>

      <div className="mt-6 space-y-3">
        {results.map((item) => (
          <div key={item.id} className="p-4 rounded-2xl border border-gray-200 bg-white/80 flex flex-col md:flex-row md:items-center md:justify-between gap-3 min-w-0">
            <div className="text-sm text-gray-800 space-y-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs px-2 py-1 rounded-lg bg-gray-100 text-gray-700 font-semibold">
                  {serviceLabel[item.service] || item.service}
                </span>
                <span className={`text-xs ${item.status === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                  {item.status}
                </span>
              </div>
              <p className="font-semibold truncate" title={item.original_file}>Fișier: {item.original_file}</p>
              <p className="text-gray-500 text-xs">Creat: {new Date(item.created_at).toLocaleString()}</p>
              {item.meta && Object.keys(item.meta).length > 0 && (
                <p className="text-gray-600 text-xs truncate">Meta: {Object.entries(item.meta).map(([k,v]) => `${k}:${v}`).join(" · ")}</p>
              )}
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {item.download_url ? (
                <a
                  href={`${BASE_URL}${item.download_url}`}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 text-sm max-w-full"
                  download
                >
                  <Download className="w-4 h-4" />
                  <span className="truncate max-w-[160px]" title="Descarcă">Descarcă</span>
                </a>
              ) : (
                <span className="text-xs text-gray-400">Fără fișier</span>
              )}
              {item.summary_url && (
                <a
                  href={`${BASE_URL}${item.summary_url}`}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 text-sm max-w-full"
                  download
                >
                  <Download className="w-4 h-4" />
                  <span className="truncate max-w-[160px]" title="Rezumat">Rezumat</span>
                </a>
              )}
            </div>
          </div>
        ))}
        {results.length === 0 && !loading && (
          <p className="text-sm text-gray-500">Nicio intrare găsită încă.</p>
        )}
      </div>
    </div>
  );
};

export default SearchPage;
