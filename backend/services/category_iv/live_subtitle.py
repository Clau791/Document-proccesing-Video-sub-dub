
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

@dataclass
class Session:
    session_id: str
    participants: List[str]
    started_at: datetime = field(default_factory=datetime.utcnow)
    stopped_at: datetime | None = None

class LiveSubtitleEngine:
    """
    In-memory live session manager (no audio pipeline).
    Provides start/stop bookkeeping so the Flask endpoints function.
    """
    def __init__(self):
        self.sessions: Dict[str, Session] = {}

    def start_session(self, session_id: str, participants: list[str] | None = None):
        sess = Session(session_id=session_id, participants=participants or [])
        self.sessions[session_id] = sess
        return {
            "session": {
                "id": sess.session_id,
                "participants": sess.participants,
                "started_at": sess.started_at.isoformat() + "Z"
            }
        }

    def stop_session(self, session_id: str):
        sess = self.sessions.get(session_id)
        if not sess:
            return {"warning": "unknown session"}
        sess.stopped_at = datetime.utcnow()
        dur = (sess.stopped_at - sess.started_at).total_seconds()
        return {
            "session": {
                "id": sess.session_id,
                "participants": sess.participants,
                "started_at": sess.started_at.isoformat() + "Z",
                "stopped_at": sess.stopped_at.isoformat() + "Z",
                "duration_seconds": dur
            }
        }
