
import shutil
from pathlib import Path
from datetime import datetime

class AudioTranslator:
    """
    Minimal audio 'translator':
    - Does NOT perform real ASR/MT
    - Copies the input audio to processed with a new name
    - Generates a sidecar .txt with a placeholder translation
    """
    def __init__(self, processed_dir: str = "processed"):
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def translate(self, filepath: str, src_lang: str = "en", dest_lang: str = "ro"):
        path = Path(filepath)
        out_audio = self.processed_dir / f"{path.stem}_{dest_lang}{path.suffix}"
        shutil.copyfile(str(path), str(out_audio))

        transcript = self.processed_dir / f"{path.stem}_{dest_lang}.txt"
        transcript.write_text(
            f"# Pseudo translation for {path.name} ({src_lang}->{dest_lang})\n"
            f"# Generated: {datetime.now().isoformat()}\n\n"
            f"[This is a placeholder. Integrate ASR/MT for real results]\n",
            encoding="utf-8"
        )

        return {
            "audio_file": f"/download/{out_audio.name}",
            "transcript_file": f"/download/{transcript.name}",
            "note": "Copied audio; generated placeholder transcript."
        }
