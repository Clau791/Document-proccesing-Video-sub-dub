# progress.py
from flask import Blueprint, Response, stream_with_context
from queue import Queue, Empty
import json, time

# Coada globală pentru evenimente SSE (un singur canal)
_events = Queue()
progress_bp = Blueprint("progress", __name__)

@progress_bp.route("/events")
def sse_events():
    """Endpoint SSE simplu: frontend-ul ascultă aici."""
    @stream_with_context
    def stream():
        # handshake + heartbeat
        yield "event: open\ndata: {}\n\n"
        while True:
            try:
                payload = _events.get(timeout=25)
                yield f"data: {json.dumps(payload)}\n\n"
            except Empty:
                # menține conexiunea vie
                yield ": keep-alive\n\n"

    return Response(
        stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"  # oprește buffering (nginx etc.)
        },
    )

def send_pages_progress(done: int, total: int):
    """
    Trimite progresul paginilor către frontend (fără job id).
    - done: număr pagini procesate (1..total)
    - total: număr total pagini
    """
    percent = int(done * 100 / total) if total else 0
    _events.put({
        "pages_done": int(done),
        "pages_total": int(total),
        "percent": max(0, min(100, percent)),
        "ts": time.time()
    })
