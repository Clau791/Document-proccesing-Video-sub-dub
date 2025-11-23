import React, { useEffect, useState } from "react";
import './styles/glass_buttons.css';

import ErrorBoundary from "./components/ErrorBoundary";
import { BackgroundFX, GlobalKeyframes } from "./components/Decor";
import { NavBar, Footer } from "./components/Layout";

import HomePage from "./pages/HomePage";
import PPTAnalysisPage from "./pages/PPTAnalysisPage";
import WordPDFAnalysisPage from "./pages/WordPDFAnalysisPage";
import ImageOCRPage from "./pages/ImageOCRPage";
import TranslateDocsPage from "./pages/TranslateDocsPage";
import TranslateAudioPage from "./pages/TranslateAudioPage";
import TranslateVideoPage from "./pages/TranslateVideoPage";
import SubtitleROPage from "./pages/SubtitleROPage";
import RedubVideoPage from "./pages/RedubVideoPage";
import LiveSubtitlePage from "./pages/LiveSubtitlePage";

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState("home");
  const [backendStatus, setBackendStatus] = useState<string>("checking");

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/health');
        setBackendStatus(response.ok ? "online" : "offline");
      } catch {
        setBackendStatus("offline");
      }
    };
    checkBackend();
    const interval = setInterval(checkBackend, 30000);
    return () => clearInterval(interval);
  }, []);

  const renderPage = () => {
    switch (currentPage) {
      case "ppt": return <PPTAnalysisPage />;
      case "word-pdf": return <WordPDFAnalysisPage />;
      case "image-ocr": return <ImageOCRPage />;
      case "translate-docs": return <TranslateDocsPage />;
      case "translate-audio": return <TranslateAudioPage />;
      case "translate-video": return <TranslateVideoPage />;
      case "subtitle-ro": return <SubtitleROPage />;
      case "redub-video": return <RedubVideoPage />;
      case "live-subtitle": return <LiveSubtitlePage />;
      default: return <HomePage onNavigate={setCurrentPage} />;
    }
  };

  return (
    <ErrorBoundary>
      <div className="min-h-screen flex flex-col relative">
        <GlobalKeyframes />
        <BackgroundFX />
        <NavBar currentPage={currentPage} onNavigate={setCurrentPage} backendStatus={backendStatus} />
        <main className="flex-1">{renderPage()}</main>
        <Footer />
      </div>
    </ErrorBoundary>
  );
};

export default App;
