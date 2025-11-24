"""
audio_translator.py

Adaptor pentru endpoint-ul:
    /api/translate-audio

Funcționalități:
- Primește un fișier audio (deja salvat în UPLOAD_FOLDER)
- Transcrie audio cu Google Gemini
- Traduce transcrierea în română
- Generează audio în română (MP3) cu gTTS, cu sufix _RO
- Generează un rezumat în română, salvat .txt cu sufix _RO_rezumat
- Întoarce un dict compatibil cu Flask view-ul:

    translator = AudioTranslator()
    result = translator.translate(filepath, src_lang=src_lang, dest_lang='ro')

    return jsonify({
        'service': 'Audio Translation',
        'originalFile': filename,
        'originalLanguage': src_lang.upper(),
        'translatedLanguage': 'RO',
        'downloadUrl': result.get('audio_file', ''),
        'status': 'success',
        **result
    })

Câmpuri în result:
- audio_file   -> URL către fișierul audio tradus (MP3), ex: /download/<fisier>
- summary_file -> URL către fișierul de rezumat (TXT), ex: /download/<fisier>
- note         -> mesaj informativ
"""

import os
import time
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any

import google.generativeai as genai
import requests
from gtts import gTTS
from dotenv import load_dotenv

# Încarcă variabilele de mediu (dacă există .env)
load_dotenv()

# Extensii audio suportate
SUPPORTED_AUDIO = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac"}


# ———————————— Utilitare ————————————
def guess_mime(path: str) -> str:
    """
    Ghicește MIME type pentru un fișier audio, cu câteva fallback-uri.
    """
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        ext = Path(path).suffix.lower()
        if ext in {".m4a", ".aac"}:
            return "audio/aac"
        if ext in {".flac"}:
            return "audio/flac"
        if ext in {".ogg"}:
            return "audio/ogg"
    return mime or "audio/mpeg"


# ———————————— Clasa principală ————————————
class AudioTranslator:
    """
    Traducător audio → română bazat pe Gemini + gTTS.
    Folosit de endpoint-ul /api/translate-audio.
    """

    def __init__(
        self,
        processed_dir: str = "processed",
        google_api_key: Optional[str] = "AIzaSyCrL0AA-rH5PYsGQ4F2OM1YjL8xtKn9K-I",
        gemini_model: Optional[str] = None,
    ) -> None:
        """
        Args:
            processed_dir: directorul în care salvăm fișierele rezultate (_RO.mp3, _RO_rezumat.txt)
            google_api_key: cheia Google AI; dacă nu se dă, se folosește .env/var de mediu
            gemini_model: ID model Gemini (ex: "gemini-1.5-flash", "gemini-2.0-flash-lite")
        """
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        # Cheia API – poți ajusta după cum vrei (env sau hard-coded)
        self.api_key = (
            google_api_key
            or os.getenv("GOOGLE_API_KEY")
            or "AIzaSyCLj69fE4qI77BMap4hCBscIhzgrYKwuGA"  # aceeași ca în translation.py
        )
        if not self.api_key:
            raise ValueError(
                "Google API key este necesară! Setează GOOGLE_API_KEY în .env "
                "sau trece-o ca parametru la AudioTranslator."
            )

        genai.configure(api_key=self.api_key)
        self.model_id = gemini_model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
        self.model = genai.GenerativeModel(self.model_id)
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:32b")
        self.chunk_size = int(os.getenv("SUMMARY_CHUNK_SIZE", "3500"))

    def _ollama_generate(self, prompt: str) -> str:
        """Folosește Ollama (qwen32b) pentru generare; întoarce text sau string gol."""
        try:
            resp = requests.post(
                f"{self.ollama_host}/api/generate",
                json={"model": self.ollama_model, "prompt": prompt, "stream": False},
                timeout=60,
            )
            if resp.ok:
                data = resp.json()
                return (data.get("response") or data.get("output") or "").strip()
        except Exception:
            return ""
        return ""

    def _llm_generate(self, prompt: str) -> str:
        out = self._ollama_generate(prompt)
        if out:
            return out
        try:
            resp = self.model.generate_content(prompt, generation_config={"temperature": 0.3})
            return resp.text.strip() if hasattr(resp, "text") else ""
        except Exception:
            return ""

    def _chunk_text(self, text: str) -> list[str]:
        chunks = []
        current = []
        length = 0
        for line in text.split("\n"):
            ln = line.strip()
            if not ln:
                continue
            if length + len(ln) + 1 > self.chunk_size and current:
                chunks.append("\n".join(current))
                current = [ln]
                length = len(ln)
            else:
                current.append(ln)
                length += len(ln) + 1
        if current:
            chunks.append("\n".join(current))
        return chunks or [text]

    # ———————————— Detectare fișier ————————————
    def is_audio_file(self, filepath: str) -> bool:
        return Path(filepath).suffix.lower() in SUPPORTED_AUDIO

    # ———————————— Integrare Gemini ————————————
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
        Transcrie audio folosind Google Gemini.
        Returnează doar textul transcris.
        """
        print(f"🎤 Transcriu audio cu Gemini: {audio_path}")
        try:
            file = self._upload_to_gemini(audio_path)
            prompt = (
                "Transcrie fidel conținutul audio în limba vorbită. "
                "Returnează DOAR transcrierea ca text brut, fără explicații."
            )
            resp = self.model.generate_content(
                [file, prompt],
                generation_config={"temperature": 0.1},
            )
            transcript = resp.text.strip() if hasattr(resp, "text") else ""
            if not transcript:
                raise RuntimeError("Transcriere goală întoarsă de model.")
            print(f"✓ Audio transcris ({len(transcript)} caractere)")
            return transcript
        except Exception as e:
            print(f"✗ Eroare la transcriere: {e}")
            raise

    def translate_to_romanian(self, text: str) -> str:
        """
        Traduce text în română: Ollama (qwen32b) ca primă opțiune, Gemini ca fallback.
        """
        print("🌍 Traduc text în română (Ollama -> Gemini fallback)…")
        try:
            prompt = (
                "Ești un traducător profesionist. Tradu în română textul dat, "
                "păstrând sensul, numele proprii și tonul. Returnează DOAR traducerea.\n\n"
                f"Text:\n{text}"
            )

            translated = self._ollama_generate(prompt)
            if not translated:
                resp = self.model.generate_content(
                    prompt,
                    generation_config={"temperature": 0.2},
                )
                translated = resp.text.strip() if hasattr(resp, "text") else ""
            if not translated:
                raise RuntimeError("Traducere goală întoarsă de modele.")
            print(f"✓ Text tradus ({len(translated)} caractere)")
            return translated
        except Exception as e:
            print(f"✗ Eroare la traducere: {e}")
            raise

    def generate_audio_from_text(self, text: str, output_path: str, lang: str = "ro") -> str:
        """
        Generează fișier audio MP3 din text folosind gTTS.
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

    def generate_summary(self, text: str) -> str:
        """
        Generează un rezumat structurat în limba română (Ollama, apoi Gemini) cu suport pentru texte lungi (chunking + multi-pass).
        """
        print("📝 Generez rezumat (Ollama -> Gemini fallback)…")
        try:
            chunks = self._chunk_text(text)

            def build_prompt(body: str) -> str:
                return (
                    "Creează un rezumat concis și informativ în română, bine structurat. "
                    "La începutul rezumatului, scoate în evidență tema generală și subtemele principale.\n\n"
                    "TEMA PRINCIPALĂ:\n"
                    "- 1 propoziție care descrie ideea centrală a materialului.\n\n"
                    "SUBTEME:\n"
                    "- 2–5 bullet-uri cu subtemele majore sau blocurile principale de idei.\n\n"
                    "REZUMAT EXECUTIV:\n"
                    "- 2–3 propoziții esențiale care sintetizează mesajul global.\n\n"
                    "PUNCTE CHEIE:\n"
                    "- 3–7 bullet-uri cu ideile principale. Dacă știi momentul din audio, notează [mm:ss]; altfel omite.\n\n"
                    "DETALII IMPORTANTE:\n"
                    "- informații relevante suplimentare, exemple, cifre, nume proprii sau contexte specifice, dacă există.\n\n"
                    "CONCLUZII:\n"
                    "- 1–3 takeaway-uri finale, formulate clar.\n\n"
                    "Returnează DOAR rezumatul în acest format, păstrând exact titlurile de secțiune.\n\n"
                    f"Text:\n{body}"
                )

            # Text scurt: un singur pas
            if len(chunks) == 1:
                prompt = build_prompt(chunks[0])
                summary = self._llm_generate(prompt)
                if not summary:
                    raise RuntimeError("Rezumat gol întors de modele.")
                print(f"✓ Rezumat generat ({len(summary)} caractere)")
                return summary

            # Multi-pass: rezumă segmentele, apoi rezumă rezumatele
            partials = []
            for idx, ch in enumerate(chunks, 1):
                prompt_part = f"Rezuma segmentul #{idx} în română (max 6-8 propoziții), păstrând ideile cheie.\n\n{ch}"
                part = self._llm_generate(prompt_part)
                if part:
                    partials.append(part)

            if not partials:
                raise RuntimeError("Nu am obținut rezumate parțiale.")

            merge_prompt = build_prompt("\n\n".join(partials))
            summary = self._llm_generate(merge_prompt)
            if not summary:
                # fallback: concatenăm parțialele
                summary = "\n\n".join(partials)
            print(f"✓ Rezumat generat ({len(summary)} caractere)")
            return summary
        except Exception as e:
            print(f"✗ Eroare la generarea rezumatului: {e}")
            raise

    def save_summary(self, summary: str, output_path: str) -> str:
        """
        Salvează rezumatul într-un fișier text.
        """
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"✓ Rezumat salvat: {output_path}")
        return output_path

    # ———————————— Pipeline AUDIO ————————————
    def process_audio_file(self, audio_path: str, output_dir: Optional[str] = None) -> Dict[str, str]:
        """
        Pipeline complet pentru un fișier audio:
        - transcriere
        - traducere în română
        - generare audio RO (MP3)
        - generare rezumat RO (TXT)
        """
        print(f"\n{'=' * 60}\n🎵 PROCESARE FIȘIER AUDIO\n{'=' * 60}\n")
        audio_path = Path(audio_path)
        output_dir = Path(output_dir) if output_dir else audio_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        base_name = audio_path.stem
        output_audio_path = output_dir / f"{base_name}_RO.mp3"
        output_summary_path = output_dir / f"{base_name}_RO_rezumat.txt"
        temp_tts_path = output_dir / f"{base_name}_tts_temp.mp3"

        results: Dict[str, str] = {}
        try:
            # 1. Transcriere audio original
            transcript = self.transcribe_audio(str(audio_path))

            # 2. Traducere în română
            translated_text = self.translate_to_romanian(transcript)

            # 3. Generare audio în română
            tts_path = self.generate_audio_from_text(translated_text, str(temp_tts_path))
            os.replace(tts_path, output_audio_path)
            results["audio"] = str(output_audio_path)

            # 4. Generare rezumat
            summary = self.generate_summary(translated_text)
            self.save_summary(summary, str(output_summary_path))
            results["summary"] = str(output_summary_path)

            print(
                f"\n{'=' * 60}\n✓ PROCESARE AUDIO COMPLETĂ\n"
                f"  Audio RO: {output_audio_path}\n"
                f"  Rezumat: {output_summary_path}\n{'=' * 60}\n"
            )
            return results
        except Exception as e:
            print(f"\n✗ Eroare la procesarea fișierului audio: {e}")
            raise
        finally:
            # Curățăm fișierul temporar, dacă există
            try:
                Path(temp_tts_path).unlink(missing_ok=True)
            except Exception:
                pass

    # ———————————— Interfață pentru endpoint ————————————
    def translate(
        self,
        filepath: str,
        src_lang: str = "en",
        dest_lang: str = "ro",
    ) -> Dict[str, Any]:
        """
        Metoda folosită de endpoint-ul /api/translate-audio.

        Args:
            filepath: cale către fișierul audio uploadat
            src_lang: limbă sursă declarată (doar informativ)
            dest_lang: limba țintă – momentan doar 'ro' este suportat

        Return:
            dict cu:
                - audio_file: /download/<fisier_mp3_tradus>
                - summary_file: /download/<fisier_rezumat_txt>
                - note: mesaj
        """
        if dest_lang.lower() != "ro":
            raise ValueError(
                "Acest serviciu suportă momentan doar traducerea în limba română (dest_lang='ro')."
            )

        audio_path = Path(filepath)
        if not audio_path.exists():
            raise FileNotFoundError(f"Fișierul nu există: {filepath}")

        if not self.is_audio_file(str(audio_path)):
            raise ValueError("Endpoint-ul /api/translate-audio acceptă doar fișiere audio.")

        # Procesez audio și pun rezultatele în processed_dir
        results = self.process_audio_file(str(audio_path), output_dir=str(self.processed_dir))

        response: Dict[str, Any] = {
            "note": (
                f"Audio tradus în română folosind Gemini. "
                f"Sursa: {audio_path.name}. Limba sursă declarată: {src_lang.upper()}."
            )
        }

        audio_out = results.get("audio")
        if audio_out:
            response["audio_file"] = f"/download/{Path(audio_out).name}"

        summary_out = results.get("summary")
        if summary_out:
            response["summary_file"] = f"/download/{Path(summary_out).name}"

        return response
