import React, { useEffect, useState } from "react";
import { Clock, MoreHorizontal } from "lucide-react";
import { BASE_URL } from "../lib/api";

type HistoryItem = {
  id: number;
  service: string;
  original_file: string;
  download_url: string;
  status: string;
  created_at: string;
  meta?: Record<string, any>;
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

const HistoryList: React.FC = () => {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  const load = async (limit = 3) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${BASE_URL}/api/history?limit=${limit}`);
      if (!res.ok) throw new Error("Nu s-a putut încărca istoricul");
      const data = await res.json();
      setItems(data.items || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg">
      <div className="liquidGlass-effect" />
      <div className="liquidGlass-tint" />
      <div className="liquidGlass-shine" />
      <div className="liquidGlass-content p-4">
        <div className="flex items-center gap-2 mb-3">
          <Clock className="w-5 h-5 text-gray-700" />
          <h3 className="font-semibold text-gray-800">Istoric operațiuni</h3>
          <button onClick={() => load(expanded ? 30 : 3)} className="ml-auto text-xs text-blue-600 hover:underline">Reîncarcă</button>
        </div>
        {loading && <p className="text-sm text-gray-500">Se încarcă...</p>}
        {error && <p className="text-sm text-red-500">{error}</p>}
        {!loading && !error && (
          <div className="space-y-2 max-h-80 overflow-auto">
            {items.map(item => (
              <div key={item.id} className="p-3 rounded-xl border border-gray-200 bg-white/70 flex items-center justify-between gap-3">
                <div className="flex flex-col text-sm text-gray-800">
                  <span className="font-semibold">{serviceLabel[item.service] || item.service}</span>
                  <span className="text-gray-600 text-xs">{item.original_file}</span>
                  <span className="text-gray-400 text-xs">{new Date(item.created_at).toLocaleString()}</span>
                </div>
                <div className="flex items-center gap-2">
                  {item.download_url && (
                    <a
                      href={`${BASE_URL}${item.download_url}`}
                      className="px-3 py-1 text-xs rounded-lg bg-blue-500 text-white hover:bg-blue-600"
                      download
                    >
                      Descarcă
                    </a>
                  )}
                  {item.summary_url && (
                    <a
                      href={`${BASE_URL}${item.summary_url}`}
                      className="px-3 py-1 text-xs rounded-lg bg-green-500 text-white hover:bg-green-600"
                      download
                    >
                      Rezumat
                    </a>
                  )}
                  {!item.download_url && !item.summary_url && (
                    <span className="text-xs text-gray-400">Fără fișier</span>
                  )}
                </div>
              </div>
            ))}
            {items.length === 0 && <p className="text-sm text-gray-500">Nu există încă intrări.</p>}
            <div className="flex justify-center pt-2">
              <button
                onClick={() => {
                  const next = !expanded;
                  setExpanded(next);
                  load(next ? 30 : 3);
                }}
                className="flex items-center gap-1 text-xs text-blue-600 hover:underline"
                title={expanded ? "Ascunde" : "Afișează mai multe"}
              >
                <MoreHorizontal className="w-4 h-4" />
                {expanded ? "mai puține" : "mai multe"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoryList;
