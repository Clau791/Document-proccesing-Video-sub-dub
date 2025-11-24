import React from "react";
import { FileText, Languages, Search } from "lucide-react";

export const NavBar: React.FC<{ currentPage: string; onNavigate: (page: string) => void; backendStatus: string }> = ({ currentPage, onNavigate, backendStatus }) => (
  <nav className="liquidGlass-wrapper liquidGlass-header sticky top-0 left-0 right-0 z-50 rounded-3xl mx-4 mt-4 mb-2">
    <div className="liquidGlass-effect" />
    <div className="liquidGlass-tint" />
    <div className="liquidGlass-shine" />
    <div className="liquidGlass-content container mx-auto px-6 py-2 w-full">
      <div className="flex items-center justify-between">
        <button onClick={() => onNavigate("home")} className="flex items-center gap-3 hover:opacity-80 transition-all duration-300 group">
          <div className="bg-gradient-to-br from-blue-500 to-sky-500 p-2.5 rounded-xl shadow-lg group-hover:shadow-xl group-hover:scale-105 transition-all duration-300"><FileText className="w-7 h-7 text-white" /></div>
          <div className="text-left">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-sky-600 bg-clip-text text-transparent">Sistem AI Integrat</h1>
            <p className="text-sm text-gray-600">Analiză, Traducere, Subtitrare</p>
          </div>
        </button>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-gray-50/90 to-gray-100/90 rounded-xl border border-gray-200 shadow-sm">
            <div className={`w-2.5 h-2.5 rounded-full shadow-lg ${backendStatus === "online" ? "bg-green-500 animate-pulse shadow-green-400" : backendStatus === "offline" ? "bg-red-500 shadow-red-400" : "bg-yellow-500 animate-pulse shadow-yellow-400"}`} />
            <span className="text-xs font-medium text-gray-700">Server: {backendStatus === "online" ? "Online" : backendStatus === "offline" ? "Offline" : "Verificare..."}</span>
          </div>
          <button
            onClick={() => onNavigate("search")}
            className="px-3 py-2 bg-white/80 border border-gray-200 rounded-xl shadow-sm hover:shadow group flex items-center gap-2"
            title="Căutare istoric"
          >
            <Search className="w-4 h-4 text-gray-700 group-hover:text-blue-600" />
            <span className="text-sm text-gray-700 group-hover:text-blue-600">Căutare</span>
          </button>
          {currentPage !== "home" && (
            <button onClick={() => onNavigate("home")} className="px-5 py-2 bg-gradient-to-r from-blue-500 to-sky-500 hover:from-blue-600 hover:to-sky-600 text-white rounded-xl transition-all duration-300 shadow-md hover:shadow-lg font-medium">← Înapoi</button>
          )}
        </div>
      </div>
    </div>
  </nav>
);

export const Footer: React.FC = () => (
  <footer className="liquidGlass-wrapper liquidGlass-footer sticky bottom-0 left-0 right-0 z-40 mt-auto rounded-3xl mx-4 mb-4">
    <div className="liquidGlass-effect" />
    <div className="liquidGlass-tint" />
    <div className="liquidGlass-shine" />
    <div className="liquidGlass-content container mx-auto px-6 py-4 w-full">
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="bg-gradient-to-r from-blue-500 to-sky-500 p-1.5 rounded-lg shadow-md"><Languages className="w-5 h-5 text-white" /></div>
          <span className="text-gray-800 font-semibold">Sistem AI Integrat</span>
        </div>
        <div className="text-gray-600 text-sm text-center">© 2025 Platformă de procesare AI. Toate drepturile rezervate.</div>
        <div className="text-gray-600 text-sm">Creat cu <span className="text-red-500">♥</span> pentru procesare multimedia</div>
      </div>
    </div>
  </footer>
);
