"""
Script pentru procesarea fișierelor audio și video cu traducere în română
Integrare completă cu Google Gemini (google-generativeai)
Autor: StarTech Smarts
Versiune: 2.0 (Gemini)

IMPLEMENTAT:
• Traducere din engleză, chineză, rusă și japoneză în română (audio, video)
• Documentele/rezultatele se procesează apoi conform instrucțiunilor pentru cele în română
— Fișiere audio
  - Se transcrie audio-ul cu Gemini și se traduce în română
  - Se generează fișiere audio noi cu sufixul _RO (MP3)
  - Se generează un rezumat în română și se salvează .txt
— Fișiere video
  - Se extrage audio, se transcrie și se traduce în română (Gemini)
  - Se sintetizează audio în română și se combină înapoi peste video, cu sufixul _RO
  - Se generează un rezumat în română (.txt)

DEPENDENȚE NECESARE:
pip install google-generativeai ffmpeg-python gtts pydub python-dotenv

ALTE CERINȚE:
- FFmpeg instalat în sistem (https://ffmpeg.org/download.html)
- GOOGLE_API_KEY definit în .env sau variabile de mediu
- Conexiune la internet

WORKFLOW:
1. Detectare tip fișier (audio/video)
2. Extragere audio din video (dacă este video)
3. Transcriere audio folosind Google Gemini (upload media)
4. Traducere text în română cu Gemini
5. Generare audio în română folosind gTTS (MP3)
6. Pentru video: combinare audio tradus cu video original
7. Generare rezumat inteligent în română (Gemini)
8. Salvare fișiere cu sufix "_RO"
"""

import os
import sys
import time
import mimetypes
from pathlib import Path
from typing import Tuple, Optional

# Librării pentru procesare audio/video
import ffmpeg
from pydub import AudioSegment  # (poate fi utilă pentru conversii ulterioare)

# Librării pentru AI și sinteză voce
import google.generativeai as genai
from gtts import gTTS

# Configurare
from dotenv import load_dotenv

# Încarcă variabilele de mediu
load_dotenv()


# ———————————— Utilitare ————————————
SUPPORTED_AUDIO = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac"}
SUPPORTED_VIDEO = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"}


def guess_mime(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    # fallback-uri simple pentru unele extensii des întâlnite
    if not mime:
        ext = Path(path).suffix.lower()
        if ext in {".m4a", ".aac"}:
            return "audio/aac"
        if ext in {".flac"}:
            return "audio/flac"
        if ext in {".ogg"}:
            return "audio/ogg"
    return mime or "audio/mpeg"


class AudioVideoProcessor:
    """Clasă pentru procesarea fișierelor audio și video (Gemini)."""

    def __init__(self, google_api_key: Optional[str] = None, gemini_model: Optional[str] = None):
        """
        Inițializare procesor

        Args:
            google_api_key: Cheia API Google AI (sau setată în .env ca GOOGLE_API_KEY)
            gemini_model: ID model Gemini (ex: "gemini-1.5-flash" sau "gemini-1.5-pro")
        """
        self.api_key = 'AIzaSyCLj69fE4qI77BMap4hCBscIhzgrYKwuGA'
        if not self.api_key:
            raise ValueError("Google API key este necesară! Setează GOOGLE_API_KEY în .env sau ca parametru.")

        genai.configure(api_key=self.api_key)
        self.model_id = gemini_model or os.getenv("GEMINI_MODEL", 'gemini-2.0-flash-lite')
        self.model = genai.GenerativeModel(self.model_id)

        self.audio_extensions = SUPPORTED_AUDIO
        self.video_extensions = SUPPORTED_VIDEO

    # ———————————— Detectare fișier ————————————
    def is_audio_file(self, filepath: str) -> bool:
        return Path(filepath).suffix.lower() in self.audio_extensions

    def is_video_file(self, filepath: str) -> bool:
        return Path(filepath).suffix.lower() in self.video_extensions

    # ———————————— Media I/O ————————————
    def extract_audio_from_video(self, video_path: str, output_audio_path: str) -> str:
        """Extrage audio din fișier video (MP3 44.1kHz stereo)."""
        print(f"📹 Extrag audio din video: {video_path}")
        try:
            (
                ffmpeg
                .input(video_path)
                .output(output_audio_path, acodec="libmp3lame", ac=2, ar="44100")
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            print(f"✓ Audio extras: {output_audio_path}")
            return output_audio_path
        except ffmpeg.Error as e:
            msg = e.stderr.decode(errors="ignore") if e.stderr else str(e)
            print(f"✗ Eroare la extragerea audio: {msg}")
            raise

    # ———————————— Gemini: Transcriere ————————————
    def _upload_to_gemini(self, path: str):
        mime = guess_mime(path)
        print(f"⬆️  Încarc fișier la Gemini ({mime})…")
        file = genai.upload_file(path=path, mime_type=mime)
        # Așteaptă procesarea dacă este cazul
        while True:
            f = genai.get_file(file.name)
            if f.state.name == "ACTIVE":
                break
            if f.state.name == "FAILED":
                raise RuntimeError("Încărcarea la Gemini a eșuat.")
            time.sleep(1)
        return file

    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcrie audio folosind Google Gemini 1.5 (media understanding).
        Returnează doar textul transcris (fără timpi, fără formatare suplimentară).
        """
        print(f"🎤 Transcriu audio cu Gemini: {audio_path}")
        try:
            file = self._upload_to_gemini(audio_path)
            prompt = (
                "Transcrie fidel conținutul audio în limba vorbită. "
                "Returnează DOAR transcrierea ca text brut, fără explicații.")
            resp = self.model.generate_content([file, prompt], generation_config={"temperature": 0.1})
            transcript = resp.text.strip() if hasattr(resp, "text") else ""
            if not transcript:
                raise RuntimeError("Transcriere goală întoarsă de model.")
            print(f"✓ Audio transcris ({len(transcript)} caractere)")
            return transcript
        except Exception as e:
            print(f"✗ Eroare la transcriere: {e}")
            raise

    # ———————————— Gemini: Traducere ————————————
    def translate_to_romanian(self, text: str) -> str:
        """Traduce text în română folosind Gemini (temperatură mică)."""
        print("🌍 Traduc text în română (Gemini)…")
        try:
            system = (
                "Ești un traducător profesionist. Tradu în română textul dat, "
                "păstrând sensul, numele proprii și tonul. Returnează DOAR traducerea.")
            resp = self.model.generate_content(
                [system, text],
                generation_config={"temperature": 0.2}
            )
            translated = resp.text.strip() if hasattr(resp, "text") else ""
            if not translated:
                raise RuntimeError("Traducere goală întoarsă de model.")
            print(f"✓ Text tradus ({len(translated)} caractere)")
            return translated
        except Exception as e:
            print(f"✗ Eroare la traducere: {e}")
            raise

    # ———————————— TTS: gTTS ————————————
    def generate_audio_from_text(self, text: str, output_path: str, lang: str = "ro") -> str:
        """
        Generează fișier audio MP3 din text folosind gTTS.
        Notă: gTTS produce MP3; denumirea fișierului trebuie să aibă extensia .mp3
        """
        print("🔊 Generez audio în română (gTTS)…")
        try:
            out = Path(output_path)
            if out.suffix.lower() != ".mp3":
                out = out.with_suffix(".mp3")
            tts = gTTS(text=text, lang=lang)
            tts.save(str(out))
            print(f"✅ Audio generat: {out}")
            return str(out)
        except Exception as e:
            print(f"❌ Eroare la generarea audio: {e}")
            raise

    # ———————————— Combinare audio+video ————————————
    def combine_audio_with_video(self, video_path: str, audio_path: str, output_path: str) -> str:
        """Combină audio nou (română) cu video original (copie video, audio AAC)."""
        print("🎬 Combin audio cu video…")
        try:
            video = ffmpeg.input(video_path)
            audio = ffmpeg.input(audio_path)
            (
                ffmpeg
                .output(video.video, audio.audio, output_path, vcodec="copy", acodec="aac", shortest=None)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            print(f"✓ Video final generat: {output_path}")
            return output_path
        except ffmpeg.Error as e:
            msg = e.stderr.decode(errors="ignore") if e.stderr else str(e)
            print(f"✗ Eroare la combinarea video: {msg}")
            raise

    # ———————————— Gemini: Rezumat ————————————
    def generate_summary(self, text: str) -> str:
        """Generează un rezumat structurat în limba română (Gemini)."""
        print("📝 Generez rezumat (Gemini)…")
        try:
            system = (
                "Creează un rezumat concis și informativ în română, structurat astfel:\n\n"
                "REZUMAT EXECUTIV:\n- 2-3 propoziții esențiale\n\n"
                "PUNCTE CHEIE:\n- 3-7 bullet-uri\n\n"
                "DETALII IMPORTANTE:\n- informații relevante suplimentare\n\n"
                "CONCLUZII:\n- 1-3 takeaway-uri finale")
            resp = self.model.generate_content([system, f"Conținut de rezumat:\n\n{text}"], generation_config={"temperature": 0.3})
            summary = resp.text.strip() if hasattr(resp, "text") else ""
            if not summary:
                raise RuntimeError("Rezumat gol întors de model.")
            print(f"✓ Rezumat generat ({len(summary)} caractere)")
            return summary
        except Exception as e:
            print(f"✗ Eroare la generarea rezumatului: {e}")
            raise

    # ———————————— Persistență ————————————
    def save_summary(self, summary: str, output_path: str) -> str:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"✓ Rezumat salvat: {output_path}")
        return output_path

    # ———————————— Procesare AUDIO ————————————
    def process_audio_file(self, audio_path: str, output_dir: Optional[str] = None) -> dict:
        print(f"\n{'='*60}\n🎵 PROCESARE FIȘIER AUDIO\n{'='*60}\n")
        audio_path = Path(audio_path)
        output_dir = Path(output_dir) if output_dir else audio_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        base_name = audio_path.stem
        # ieșire standardizată la MP3 pentru TTS
        output_audio_path = output_dir / f"{base_name}_RO.mp3"
        output_summary_path = output_dir / f"{base_name}_RO_rezumat.txt"
        temp_tts_path = output_dir / f"{base_name}_tts_temp.mp3"

        results = {}
        try:
            # 1. Transcriere audio original (Gemini)
            transcript = self.transcribe_audio(str(audio_path))

            # 2. Traducere în română (Gemini)
            translated_text = self.translate_to_romanian(transcript)

            # 3. Generare audio în română (gTTS)
            tts_path = self.generate_audio_from_text(translated_text, str(temp_tts_path))
            os.replace(tts_path, output_audio_path)
            results["audio"] = str(output_audio_path)

            # 4. Generare rezumat (Gemini)
            summary = self.generate_summary(translated_text)
            self.save_summary(summary, str(output_summary_path))
            results["summary"] = str(output_summary_path)

            print(f"\n{'='*60}\n✓ PROCESARE AUDIO COMPLETĂ\n  Audio tradus: {output_audio_path}\n  Rezumat: {output_summary_path}\n{'='*60}\n")
            return results
        except Exception as e:
            print(f"\n✗ Eroare la procesarea fișierului audio: {e}")
            raise
        finally:
            # curățare
            try:
                Path(temp_tts_path).unlink(missing_ok=True)
            except Exception:
                pass

    # ———————————— Procesare VIDEO ————————————
    def process_video_file(self, video_path: str, output_dir: Optional[str] = None) -> dict:
        print(f"\n{'='*60}\n🎬 PROCESARE FIȘIER VIDEO\n{'='*60}\n")
        video_path = Path(video_path)
        output_dir = Path(output_dir) if output_dir else video_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        base_name = video_path.stem
        extension = video_path.suffix

        temp_audio_original = output_dir / f"{base_name}_audio_original.mp3"
        temp_audio_ro = output_dir / f"{base_name}_audio_ro.mp3"
        output_video_path = output_dir / f"{base_name}_RO{extension}"
        output_summary_path = output_dir / f"{base_name}_RO_rezumat.txt"

        results = {}
        try:
            # 1. Extragere audio din video
            self.extract_audio_from_video(str(video_path), str(temp_audio_original))

            # 2. Transcriere audio (Gemini)
            transcript = self.transcribe_audio(str(temp_audio_original))

            # 3. Traducere în română (Gemini)
            translated_text = self.translate_to_romanian(transcript)

            # 4. Generare audio în română (gTTS)
            self.generate_audio_from_text(translated_text, str(temp_audio_ro))

            # 5. Combinare audio tradus cu video original
            self.combine_audio_with_video(str(video_path), str(temp_audio_ro), str(output_video_path))
            results["video"] = str(output_video_path)

            # 6. Generare rezumat (Gemini)
            summary = self.generate_summary(translated_text)
            self.save_summary(summary, str(output_summary_path))
            results["summary"] = str(output_summary_path)

            print(f"\n{'='*60}\n✓ PROCESARE VIDEO COMPLETĂ\n  Video tradus: {output_video_path}\n  Rezumat: {output_summary_path}\n{'='*60}\n")
            return results
        except Exception as e:
            print(f"\n✗ Eroare la procesarea fișierului video: {e}")
            raise
        finally:
            # Curățare fișiere temporare
            try:
                Path(temp_audio_original).unlink(missing_ok=True)
                Path(temp_audio_ro).unlink(missing_ok=True)
            except Exception:
                pass

    # ———————————— Orchestrare ————————————
    def process_file(self, filepath: str, output_dir: Optional[str] = None) -> dict:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Fișierul nu există: {filepath}")
        if self.is_audio_file(filepath):
            return self.process_audio_file(filepath, output_dir)
        elif self.is_video_file(filepath):
            return self.process_video_file(filepath, output_dir)
        else:
            raise ValueError(f"Tip de fișier nesuportat: {filepath}")


# ———————————— CLI ————————————
def main():
    print(
        """
╔════════════════════════════════════════════════════════════╗
║   PROCESOR AUDIO/VIDEO - TRADUCERE ÎN ROMÂNĂ (GEMINI)      ║
╚════════════════════════════════════════════════════════════╝
        """
    )

    if len(sys.argv) < 2:
        print("Utilizare: python processor_gemini.py <cale_fisier> [director_iesire]")
        print("\nExemple:")
        print("  python processor_gemini.py video.mp4")
        print("  python processor_gemini.py audio.wav ./output")
        sys.exit(1)

    filepath = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        processor = AudioVideoProcessor()
        results = processor.process_file(filepath, output_dir)
        print("\n✓ Procesare finalizată cu succes!")
        print("\nFișiere generate:")
        for key, value in results.items():
            print(f"  - {key}: {value}")
    except Exception as e:
        print(f"\n✗ Eroare: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
