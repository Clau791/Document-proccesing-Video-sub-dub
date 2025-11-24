
import os
import shutil
from pathlib import Path
from datetime import datetime
import subprocess
import torch
import whisper
import google.generativeai as genai
import requests

class VideoTranslator:
    """
    Video translator cu:
    - Extracție audio + transcriere (Whisper)
    - "Traducere" simplă (placeholder) + insight (primele fraze)
    - Returnează text + insight (nu produce video tradus)
    """
    def __init__(self, processed_dir: str = "processed"):
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self._whisper = None
        self.chunk_size = int(os.getenv("SUMMARY_CHUNK_SIZE", "3500"))

    def _get_whisper(self):
        if self._whisper is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._whisper = whisper.load_model("base", device=device)
        return self._whisper

    def _ollama_generate(self, prompt: str) -> str:
        """Încercă să genereze text folosind un model local (qwen32b) prin Ollama."""
        host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        model = os.getenv("OLLAMA_MODEL", "qwen2.5:32b")
        try:
            resp = requests.post(
                f"{host}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            if resp.ok:
                data = resp.json()
                text = data.get("response") or data.get("output") or ""
                return text.strip()
        except Exception:
            return ""
        return ""

    def _summarize(self, transcript: str, lang: str = "ro") -> str:
        """Returnează un rezumat concis folosind Ollama (qwen32b) cu fallback la Gemini."""
        if not transcript:
            return ""

        prompt = (
            "Realizează un rezumat concis (max 6-8 propoziții) în limba română al textului următor. "
            "Păstrează nume proprii și termeni tehnici.\n\n"
            f"Text:\n{transcript}"
        )

        # Chunking + multi-pass
        chunks = []
        current = []
        length = 0
        for sentence in transcript.split("."):
            s = sentence.strip()
            if not s:
                continue
            if length + len(s) + 1 > self.chunk_size and current:
                chunks.append(". ".join(current))
                current = [s]
                length = len(s)
            else:
                current.append(s)
                length += len(s) + 1
        if current:
            chunks.append(". ".join(current))

        def run_llm(body: str) -> str:
            # Ollama preferat
            out = self._ollama_generate(
                "Realizează un rezumat concis (max 6-8 propoziții) în limba română. "
                "Păstrează nume proprii și termeni tehnici.\n\n"
                f"Text:\n{body}"
            )
            if out:
                return out
            api_key = os.getenv("GEMINI_API_KEY") or "AIzaSyCrL0AA-rH5PYsGQ4F2OM1YjL8xtKn9K-I"
            if not api_key:
                return ""
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                resp = model.generate_content(
                    "Realizează un rezumat concis (max 6-8 propoziții) în limba română, păstrând nume proprii și termeni tehnici.\n\n"
                    f"Text:\n{body}"
                )
                return resp.text.strip() if resp and getattr(resp, "text", "").strip() else ""
            except Exception:
                return ""

        if len(chunks) == 1:
            return run_llm(chunks[0]) or ""

        partials = []
        for idx, ch in enumerate(chunks, 1):
            part = run_llm(ch)
            if part:
                partials.append(part)

        if not partials:
            return ""

        merged = run_llm("\n\n".join(partials))
        return merged or "\n\n".join(partials)

    def _extract_audio(self, video_path: Path, out_wav: Path, sr: int = 16000):
        cmd = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-vn", "-ac", "1", "-ar", str(sr),
            str(out_wav)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def translate(self, filepath: str, src_lang: str = "en", dest_lang: str = "ro"):
        path = Path(filepath)
        out_video = self.processed_dir / f"{path.stem}_{dest_lang}{path.suffix}"
        shutil.copyfile(str(path), str(out_video))
        print(f"[VIDEO TRANSLATE] Start {path.name} ({src_lang}→{dest_lang})")

        # Transcriere audio
        transcript = ""
        audio_path = None
        try:
            audio_path = self.processed_dir / f"{path.stem}_raw.wav"
            self._extract_audio(path, audio_path)
            print(f"[VIDEO TRANSLATE] Audio extras: {audio_path.name}")
            model = self._get_whisper()
            res = model.transcribe(str(audio_path), language=src_lang if src_lang != "auto" else None)
            transcript = res.get("text", "").strip()
            print(f"[VIDEO TRANSLATE] Transcriere completă, lungime {len(transcript)} caractere")
        except Exception as e:
            transcript = f"[Transcription failed: {e}]"
        finally:
            if audio_path:
                try:
                    Path(audio_path).unlink(missing_ok=True)
                except Exception:
                    pass

        # Insight simplu
        insight = ""
        if transcript:
            parts = [p.strip() for p in transcript.split(".") if p.strip()]
            insight = " / ".join(parts[:2]) if parts else transcript[:200]
        if insight:
            print(f"[VIDEO TRANSLATE] Insight generat: {insight[:120]}...")

        # Rezumat AI (dacă există cheie)
        summary = self._summarize(transcript)
        if summary:
            print(f"[VIDEO TRANSLATE] Rezumat generat (LLM): {summary[:120]}...")

        # Salvează transcript+insight într-un fișier text
        txt_path = self.processed_dir / f"{path.stem}_{dest_lang}.txt"
        txt_content = [
            "=== VIDEO TRANSLATION (TEXT ONLY) ===",
            f"Original file: {path.name}",
            f"Source lang: {src_lang}",
            f"Target lang: {dest_lang}",
            "",
            "AI Summary:",
            summary or insight or "[no summary]",
            "",
            "Insight:",
            insight or "[no insight]",
            "",
            "Transcript:",
            transcript or "[empty transcript]"
        ]
        txt_path.write_text("\n".join(txt_content), encoding="utf-8")

        return {
            "download_url": f"/download/{txt_path.name}",
            "transcript": transcript,
            "insight": insight,
            "summary": summary,
            "note": "Text only: transcript + insight. No translated video is produced."
        }
