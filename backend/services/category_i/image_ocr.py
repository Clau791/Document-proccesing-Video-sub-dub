
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image
    import pytesseract
except Exception:
    Image = None
    pytesseract = None

class ImageOCR:
    """
    Minimal OCR wrapper.
    - Uses PIL + pytesseract if available
    - Otherwise, writes a placeholder result
    Output: .txt file in 'processed' and /download URL.
    """
    def __init__(self, processed_dir: str = "processed", lang: str = "eng"):
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.lang = lang

    def extract_text(self, filepath: str):
        path = Path(filepath)
        outname = f"{path.stem}_ocr.txt"
        outpath = self.processed_dir / outname

        if Image is not None and pytesseract is not None:
            try:
                img = Image.open(str(path))
                text = pytesseract.image_to_string(img, lang=self.lang)
            except Exception as e:
                text = f"[OCR error: {e}]"
        else:
            text = "[OCR unavailable] Install pillow + tesseract + pytesseract to enable."

        header = f"# OCR: {path.name}\n# Generated: {datetime.now().isoformat()}\n\n"
        outpath.write_text(header + (text or ""), encoding="utf-8")

        return {
            "output_file": f"/download/{outname}",
            "characters": len(text or ""),
            "engine": "tesseract" if pytesseract else "none",
        }
