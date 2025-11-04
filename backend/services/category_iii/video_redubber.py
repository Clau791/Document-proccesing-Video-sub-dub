
import shutil
from pathlib import Path

class VideoRedubber:
    """
    Minimal video redubber:
    - Simply copies the file and adds a suffix.
    """
    def __init__(self, processed_dir: str = "processed"):
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def redub(self, filepath: str, src_lang: str = "ro", dest_lang: str = "en"):
        path = Path(filepath)
        out_video = self.processed_dir / f"{path.stem}_{src_lang}-{dest_lang}{path.suffix}"
        shutil.copyfile(str(path), str(out_video))
        return {
            "video_file": f"/download/{out_video.name}",
            "note": "Placeholder redub (copied original)."
        }
