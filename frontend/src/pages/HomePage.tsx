import React from "react";
import { FileText, BookOpen, Languages, Presentation, FileType, Image as ImageIcon, Mic, Video as VideoIcon, Video, Radio, Subtitles, PlayCircle, MessageSquare } from "lucide-react";
import HistoryList from "../components/HistoryList";

type Props = { onNavigate: (page: string) => void };

const HomePage: React.FC<Props> = ({ onNavigate }) => {
  const categories = [
    {
      id: "category-ii",
      title: "I. Traducere Automată Multilingvă",
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
      title: "II. Subtitrare și Redublaj",
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
      title: "III. Subtitrare Live",
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {categories.map((cat, idx) => (
          <div
            key={cat.id}
            className={`liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg fade-up${idx} h-full`}
          >
            <div className="liquidGlass-effect" />
            <div className="liquidGlass-tint" />
            <div className="liquidGlass-shine" />
            <div className="liquidGlass-content p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className={`bg-gradient-to-br ${cat.color} w-11 h-11 rounded-xl flex items-center justify-center shadow-lg`}>
                  <cat.icon className="w-5 h-5 text-white" />
                </div>
                <div>
                  <div className="text-xs text-gray-500">Categoria {idx + 1} din {categories.length}</div>
                  <h3 className="text-lg font-bold text-gray-800 leading-tight">{cat.title}</h3>
                  <p className="text-gray-600 text-sm leading-snug">{cat.description}</p>
                </div>
              </div>

              <div
                className="grid gap-2"
                style={{ gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))" }}
              >
                {cat.subcategories.map((sub) => (
                  <button
                    key={sub.id}
                    onClick={() => onNavigate(sub.id)}
                    className="group flex items-center gap-2 px-3 py-2 rounded-lg border border-blue-200 bg-white/80 hover:border-blue-400 hover:shadow-md transition-colors duration-200 w-full min-h-[54px]"
                  >
                    <div className="bg-gray-100 group-hover:bg-blue-50 p-2 rounded-lg">
                      <sub.icon className="w-4 h-4 text-gray-700 group-hover:text-blue-600" />
                    </div>
                    <span className="text-gray-800 text-sm font-medium group-hover:text-blue-700">{sub.name}</span>
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
