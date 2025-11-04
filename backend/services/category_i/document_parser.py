
from pathlib import Path
import zipfile, re
from xml.etree import ElementTree as ET
from datetime import datetime

try:
    import PyPDF2  # optional
except Exception:
    PyPDF2 = None

class DocumentParser:
    """
    Minimal document parser for .docx/.pdf/.epub/.txt.
    - DOCX: extracts plain text from document.xml
    - PDF:   uses PyPDF2 if available, else returns empty text + note
    - EPUB:  extracts text from common XHTML files
    Writes a .txt to the 'processed' folder and returns its /download URL.
    """
    def __init__(self, processed_dir: str = "processed"):
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def _parse_docx(self, path: Path) -> str:
        text_parts = []
        with zipfile.ZipFile(str(path)) as z:
            with z.open("word/document.xml") as f:
                tree = ET.parse(f)
                root = tree.getroot()
                # Namespaces
                ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                for p in root.findall(".//w:p", ns):
                    runs = []
                    for r in p.findall(".//w:r/w:t", ns):
                        runs.append(r.text or "")
                    line = "".join(runs).strip()
                    if line:
                        text_parts.append(line)
        return "\n".join(text_parts)

    def _parse_epub(self, path: Path) -> str:
        text_parts = []
        with zipfile.ZipFile(str(path)) as z:
            for name in z.namelist():
                if name.lower().endswith((".xhtml", ".html")):
                    try:
                        with z.open(name) as f:
                            data = f.read().decode("utf-8", errors="ignore")
                            # very rough tag strip
                            text = re.sub(r"<[^>]+>", " ", data)
                            text = re.sub(r"\s+", " ", text)
                            if text:
                                text_parts.append(text.strip())
                    except Exception:
                        pass
        return "\n".join(text_parts)

    def _parse_pdf(self, path: Path) -> str:
        if PyPDF2 is None:
            return ""
        try:
            out = []
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    try:
                        out.append(page.extract_text() or "")
                    except Exception:
                        out.append("")
            return "\n".join(out)
        except Exception:
            return ""

    def parse(self, filepath: str):
        path = Path(filepath)
        ext = path.suffix.lower()
        text = ""
        notes = []
        if ext == ".docx":
            try:
                text = self._parse_docx(path)
            except Exception as e:
                notes.append(f"DOCX parse error: {e}")
        elif ext == ".pdf":
            text = self._parse_pdf(path)
            if not text:
                notes.append("PyPDF2 unavailable or failed; extracted no text.")
        elif ext == ".epub":
            try:
                text = self._parse_epub(path)
            except Exception as e:
                notes.append(f"EPUB parse error: {e}")
        else:
            # naive text read as fallback
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                text = ""

        if not text:
            text = "[No text extracted]"

        outname = f"{path.stem}_parsed.txt"
        outpath = self.processed_dir / outname
        header = f"# Parsed: {path.name}\n# Generated: {datetime.now().isoformat()}\n\n"
        outpath.write_text(header + text, encoding="utf-8")

        return {
            "output_file": f"/download/{outname}",
            "characters": len(text),
            "notes": notes,
        }
