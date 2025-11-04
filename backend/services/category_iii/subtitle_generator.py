
from pathlib import Path

class SubtitleGenerator:
    """
    Minimal subtitle generator:
    - Writes a canned .srt in 'processed'
    - For attach_mode='soft' returns the SRT URL under key 'video_file' (to fit existing endpoint)
    """
    def __init__(self, processed_dir: str = "processed"):
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, filepath: str, lang: str = "ro", attach_mode: str = "soft"):
        path = Path(filepath)
        srt = self.processed_dir / f"{path.stem}_{lang}.srt"
        srt.write_text(
            "1\n00:00:00,000 --> 00:00:02,000\n[Subtitlu de exemplu]\n\n"
            "2\n00:00:02,100 --> 00:00:04,000\nÎnlocuiește cu pipeline real.\n",
            encoding="utf-8"
        )
        # We return using key 'video_file' to align with the Flask endpoint's expectation
        return {
            "video_file": f"/download/{srt.name}",
            "attach_mode": attach_mode,
            "note": "Generated placeholder SRT (soft attach)."
        }
