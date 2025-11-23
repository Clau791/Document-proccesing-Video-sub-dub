import React, { useState } from "react";
import { MessageSquare, Radio } from "lucide-react";

const LiveSubtitlePage: React.FC = () => {
  const [sessionId] = useState<string>(() => `session_${Date.now()}`);
  const [participants] = useState([
    { id: 'user1', name: 'Ion', language: 'ro' },
    { id: 'user2', name: 'Ivan', language: 'ru' }
  ]);
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startSession = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/live-start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, participants })
      });
      
      if (!response.ok) throw new Error('Failed to start session');
      
      setIsActive(true);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const stopSession = async () => {
    try {
      await fetch('http://localhost:5000/api/live-stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
      setIsActive(false);
      setError(null);
    } catch (err: any) {
      setError(err.message);
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
            <div className="bg-gradient-to-br from-orange-400 to-red-400 w-16 h-16 rounded-xl flex items-center justify-center shadow-lg">
              <MessageSquare className="w-8 h-8 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">IV - Subtitrare Bidirecțională Live (RO ↔ RU)</h2>
              <p className="text-gray-600 mb-2">Dialog în timp real între 2+ persoane cu subtitrări simultane</p>
              <p className="text-xs text-gray-400 font-mono">Endpoint: WebSocket /api/live-start</p>
            </div>
          </div>
        </div>
      </div>

      <div className="liquidGlass-wrapper liquidGlass-card rounded-3xl shadow-lg fade-up-delay-2" style={{padding: '2rem'}}>
        <div className="liquidGlass-effect" />
        <div className="liquidGlass-tint" />
        <div className="liquidGlass-shine" />
        <div className="liquidGlass-content">
          <div className="border-2 border-solid border-orange-300 rounded-xl p-12 text-center">
            <Radio className="w-16 h-16 mx-auto text-orange-400 mb-4" />
            
            <div className="mb-6 text-left bg-white/50 rounded-xl p-4">
              <p className="font-semibold mb-2">📋 Detalii sesiune:</p>
              <p><strong>Session ID:</strong> {sessionId}</p>
              <p><strong>Status:</strong> {isActive ? '🟢 Activ' : '🔴 Inactiv'}</p>
              <p className="mt-2"><strong>Participanți:</strong></p>
              <ul className="ml-4 mt-1">
                {participants.map(p => (
                  <li key={p.id}>• {p.name} ({p.language.toUpperCase()})</li>
                ))}
              </ul>
            </div>

            <p className="text-gray-600 mb-6">Funcționalitate în timp real - WebSocket</p>

            {!isActive ? (
              <button
                onClick={startSession}
                className="px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl font-medium hover:shadow-lg transition-all"
              >
                🎙️ Pornește Sesiune Live
              </button>
            ) : (
              <button
                onClick={stopSession}
                className="px-6 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-xl font-medium hover:shadow-lg transition-all"
              >
                ⏹️ Oprește Sesiune
              </button>
            )}

            {error && <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-600">{error}</div>}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveSubtitlePage;
