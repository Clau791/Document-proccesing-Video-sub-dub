import React from "react";
import { FileText, BookOpen, Languages, Presentation, FileType, Image as ImageIcon, Mic, Video as VideoIcon, Video, Radio, Subtitles, PlayCircle, MessageSquare } from "lucide-react";
import HistoryList from "../components/HistoryList";

type Props = { onNavigate: (page: string) => void };

const HomePage: React.FC<Props> = ({ onNavigate }) => {
  const categories = [
    {
      id: "category-i",
      title: "I. Analiză și Stocare Documente",
      description: "Procesare inteligentă PPT, Word, PDF, Imagine cu OCR",
      icon: BookOpen,
      color: "from-blue-400 to-sky-400",
      subcategories: [
        { id: "ppt", name: "PowerPoint", icon: Presentation },
        { id: "word-pdf", name: "Word/PDF/eBook", icon: FileType },
        { id: "image-ocr", name: "Imagine OCR", icon: ImageIcon }
      ]
    },
    {
      id: "category-ii",
      title: "II. Traducere Automată Multilingvă",
      description: "EN/ZH/RU/JA → RO pentru documente, audio, video",
      icon: Languages,
      color: "from-purple-400 to-pink-400",
      subcategories: [
        { id: "translate-docs", name: "Documente scrise", icon: FileText },
        { id: "translate-audio", name: "Fișiere audio", icon: Mic },
        { id: "translate-video", name: "Fișiere video", icon: VideoIcon }
      ]
    },
    {
      id: "category-iii",
      title: "III. Subtitrare și Redublaj",
      description: "Subtitrare RO și redublare video",
      icon: Subtitles,
      color: "from-green-400 to-emerald-400",
      subcategories: [
        { id: "subtitle-ro", name: "Subtitrare RO", icon: PlayCircle },
        { id: "redub-video", name: "Redublare video", icon: Video }
      ]
    },
    {
      id: "category-iv",
      title: "IV. Subtitrare Live",
      description: "Subtitrare bidirecțională în timp real",
      icon: Radio,
      color: "from-orange-400 to-red-400",
      subcategories: [
        { id: "live-subtitle", name: "Live subtitle RO ↔ RU", icon: MessageSquare }
      ]
    }
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {categories.map((cat, idx) => (
          <div
            key={cat.id}
            className={`liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg fade-up${idx}`}
          >
            <div className="liquidGlass-effect" />
            <div className="liquidGlass-tint" />
            <div className="liquidGlass-shine" />
            <div className="liquidGlass-content p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className={`bg-gradient-to-br ${cat.color} w-14 h-14 rounded-xl flex items-center justify-center shadow-lg`}>
                  <cat.icon className="w-7 h-7 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-800">{cat.title}</h3>
                  <p className="text-gray-600 text-sm">{cat.description}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {cat.subcategories.map((sub) => (
                  <button
                    key={sub.id}
                    onClick={() => onNavigate(sub.id)}
                    className="group flex items-center gap-3 p-4 rounded-2xl border border-gray-200 bg-white/70 hover:border-blue-400 hover:shadow-md transition-all"
                  >
                    <div className="bg-gray-100 group-hover:bg-blue-50 p-2 rounded-lg">
                      <sub.icon className="w-5 h-5 text-gray-700 group-hover:text-blue-600" />
                    </div>
                    <span className="text-gray-800 font-medium group-hover:text-blue-700">{sub.name}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-8">
        <HistoryList />
      </div>
    </div>
  );
};

export default HomePage;
