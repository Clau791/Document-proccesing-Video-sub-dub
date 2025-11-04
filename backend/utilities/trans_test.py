"""
IMPLEMENTAT:
•  Traduce din engleza, chineza, rusa si japoneza in romana (documente scrise, audio, video)
'  Documentele vor fi traduse iar apoi rezultatul traducerii va fi prelucrat conform instructiunilor pentru cele in romana
---     Fisierele audio
'  Se va traduce audio-ul in romana si se vor genera fisiere audio noi cu numele original la care se va adauga sufixul RO
'  Se va genera un rezumat in romana al continutului
'  Rezumatul va fi prelucrat conform instructiunilor pentru documentele in romana
----    Fisiere video
'  Partea audio se va traduce in romana si se vor genera fisiere video noi cu audio-ul in romana avand numele original la care se va adauga sufixul RO
'  Se va genera un rezumat in romana al continutului
'  Rezumatul va fi prelucrat conform instructiunilor pentru documentele in romana

Script pentru procesarea fișierelor audio și video cu traducere în română
Autor: Claude
Versiune: 1.1 (cu sincronizare durată audio)

DEPENDENȚE NECESARE:
pip install openai ffmpeg-python gtts pydub python-dotenv

ALTE CERINȚE:
- FFmpeg + FFprobe instalate în sistem (și în PATH) (https://ffmpeg.org/download.html)
- API Key OpenAI pentru transcriere / TTS / rezumate (OPENAI_API_KEY)
- Conexiune la internet pentru servicii de traducere

WORKFLOW:
1. Detectare tip fișier (audio/video)
2. Extragere audio din video (dacă este video)
3. Transcriere audio (OpenAI Whisper)
4. Traducere text în română
5. Generare audio în română (OpenAI TTS)
6. 🔁 Sincronizare: potrivire durată audio RO la durata originalului (±0.1s)
7. Pentru video: combinare audio sincronizat cu video original
8. Generare rezumat inteligent în română
9. Salvare fișiere cu sufix "_RO"
"""

import os
import sys
from pathlib import Path
from typing import Tuple, Optional
import json
import subprocess

# Librării pentru procesare audio/video
import ffmpeg
from pydub import AudioSegment  # (opțional pentru alte prelucrări)

# Librării pentru AI și traducere
from openai import OpenAI
from gtts import gTTS  # listată în dependențe; nu este folosită direct aici

# Configurare
from dotenv import load_dotenv

import google.generativeai as genai
from google.cloud import texttospeech
from google.generativeai.types import GenerationConfig

import whisper
import torch

# Încarcă variabilele de mediu
load_dotenv()


class AudioVideoProcessor:
    """Clasă pentru procesarea fișierelor audio și video"""

    def __init__(self): # Am eliminat 'openai_api_key' din parametri
        """
        Inițializare procesor
        """
        self.api_key = os.getenv('VITE_GEMINI_API_KEY') 
        if not self.api_key:
            raise ValueError("GEMINI API key este necesară! Setează VITE_GEMINI_API_KEY în .env sau ca parametru.")

        # --- Codul tău existent pentru Google ---
        genai.configure(api_key=self.api_key)
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-lite')
        self.tts_client = texttospeech.TextToSpeechClient()
        # --- Sfârșit cod Google ---

        # Extensii suportate
        self.audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'}
        self.video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
        
        # --- ADAUGĂ ACEST BLOC PENTRU WHISPER LOCAL ---
        print("🚀 Se încarcă modelul Whisper local...")
        # Verifică dacă există GPU (CUDA)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Whisper va rula pe: {self.device.upper()}")
        
        # Alegem modelul "small" - e un echilibru bun viteză/acuratețe pentru multilingual
        # Vezi secțiunea de mai jos pentru alte opțiuni (tiny, base, medium, large)
        self.whisper_model = whisper.load_model("small", device=self.device)
        print("✓ Model Whisper local încărcat.")
        # --- SFÂRȘIT BLOC NOU ---
    # -----------------------
    # Detectare tip fișier
    # -----------------------
    def is_audio_file(self, filepath: str) -> bool:
        """Verifică dacă fișierul este audio"""
        return Path(filepath).suffix.lower() in self.audio_extensions

    def is_video_file(self, filepath: str) -> bool:
        """Verifică dacă fișierul este video"""
        return Path(filepath).suffix.lower() in self.video_extensions

    # -----------------------
    # Extragere / Mux
    # -----------------------
    def extract_audio_from_video(self, video_path: str, output_audio_path: str) -> str:
        """
        Extrage audio din fișier video

        Args:
            video_path: Calea către fișierul video
            output_audio_path: Calea pentru fișierul audio extras

        Returns:
            Calea către fișierul audio extras
        """
        print(f"📹 Extrag audio din video: {video_path}")

        try:
            (
                ffmpeg
                .input(video_path)
                .output(output_audio_path, acodec='libmp3lame', ac=2, ar='44100')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            print(f"✓ Audio extras: {output_audio_path}")
            return output_audio_path
        except ffmpeg.Error as e:
            print(f"✗ Eroare la extragerea audio: {e.stderr.decode()}")
            raise

    def combine_audio_with_video(self, video_path: str, audio_path: str, output_path: str) -> str:
        """
        Combină audio nou cu video original

        Args:
            video_path: Calea către fișierul video original
            audio_path: Calea către noul fișier audio (sincronizat)
            output_path: Calea pentru fișierul video final

        Returns:
            Calea către fișierul video final
        """
        print(f"🎬 Combin audio cu video...")

        try:
            video = ffmpeg.input(video_path)
            audio = ffmpeg.input(audio_path)

            # -shortest pentru a evita depășiri accidentale (ar trebui să fie egal oricum)
            (
                ffmpeg
                .output(video.video, audio.audio, output_path, vcodec='copy', acodec='aac', shortest=None)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            print(f"✓ Video final generat: {output_path}")
            return output_path
        except ffmpeg.Error as e:
            print(f"✗ Eroare la combinarea video: {e.stderr.decode()}")
            raise

    # -----------------------
    # Whisper / LLM / TTS
    # -----------------------
    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcrie audio folosind modelul Whisper LOCAL

        Args:
            audio_path: Calea către fișierul audio

        Returns:
            Textul transcris
        """
        print(f"🎤 (Whisper Local) Transcriu audio: {audio_path}")

        try:
            # Modelul este deja încărcat în self.whisper_model
            # Folosim fp16 (half-precision) dacă suntem pe GPU (CUDA) pentru viteză
            options = dict(fp16=torch.cuda.is_available())
            
            # Rulează transcrierea
            result = self.whisper_model.transcribe(audio_path, **options)
            
            transcript = result["text"].strip()
            
            print(f"✓ Audio transcris ({len(transcript)} caractere)")

            # Afișează limba detectată (util pentru debugging)
            detected_lang = result.get("language", "nedetectată")
            print(f"ℹ️ Limba detectată de Whisper: {detected_lang}")

            return transcript
            
        except Exception as e:
            print(f"✗ Eroare la transcriere (Whisper Local): {e}")
            raise
        

    def transcribe_audio_AI(self, audio_path: str) -> str:
        """
        Transcrie audio folosind Google Gemini (modelul generativ)

        Args:
            audio_path: Calea către fișierul audio

        Returns:
            Textul transcris
        """
        print(f"🎤 (Gemini) Transcriu audio: {audio_path}")
        
        audio_file_data = None
        try:
            # 1. Încărcăm fișierul audio la Google
            # Acest pas este necesar pentru a-l putea referenția în prompt
            print(f"📤 (Gemini) Încarc fișierul audio...")
            audio_file_data = genai.upload_file(path=audio_path)
            print(f"✓ Fișier încărcat: {audio_file_data.name}")

            # 2. Transcriem folosind modelul Gemini
            # Dăm modelului un prompt și fișierul audio
            prompt = "Transcrie acest fișier audio. Returnează doar textul transcris, fără absolut niciun alt comentariu."
            
            response = self.gemini_model.generate_content([prompt, audio_file_data])

            # Verificăm dacă răspunsul a fost blocat
            if not response.parts:
                raise ValueError(f"Eroare la transcriere (Gemini): Răspunsul a fost blocat. Feedback: {response.prompt_feedback}")

            transcript = response.text.strip()
            print(f"✓ Audio transcris ({len(transcript)} caractere)")
            return transcript
            
        except Exception as e:
            print(f"✗ Eroare la transcriere (Gemini): {e}")
            raise
        finally:
            # 3. Ștergem fișierul de pe serverele Google (important pentru curățenie)
            if audio_file_data:
                try:
                    print(f"🗑️ (Gemini) Șterg fișierul încărcat {audio_file_data.name}...")
                    genai.delete_file(audio_file_data.name)
                    print("✓ Fișier temporar șters.")
                except Exception as e_del:
                    # Aceasta nu este o eroare fatală, doar o avertizare
                    print(f"⚠️ Avertisment: Nu s-a putut șterge fișierul încărcat {audio_file_data.name}: {e_del}")


    def translate_to_romanian(self, text: str) -> str:
        """
        Traduce text în română folosind Google Gemini

        Args:
            text: Textul de tradus

        Returns:
            Textul tradus în română
        """
        print(f"🌍 (Gemini) Traduc text în română...")

        # Promptul pentru Gemini este mai direct
        system_prompt = "Ești un traducător profesionist. Traduce textul următor în limba română, păstrând sensul și tonul original. Returnează doar traducerea, fără comentarii suplimentare."
        full_prompt = f"{system_prompt}\n\nText de tradus:\n{text}"
        
        # Configurarea generării
        config = GenerationConfig(
            temperature=0.3
        )

        try:
            # Apelul API către Gemini
            response = self.gemini_model.generate_content(
                full_prompt,
                generation_config=config
            )

            # Extragerea textului este mai simplă
            translated_text = response.text.strip()
            print(f"✓ Text tradus ({len(translated_text)} caractere)")
            return translated_text
        except Exception as e:
            print(f"✗ Eroare la traducere (Gemini): {e}")
            # Poți inspecta 'response.prompt_feedback' pentru erori de siguranță
            # if response.prompt_feedback:
            #     print(f"Blocat de siguranță: {response.prompt_feedback}")
            raise

    def generate_audio_from_text(self, text: str, output_path: str, lang: str = 'ro') -> str:
        """
        Generează fișier audio din text folosind Google Cloud TTS

        Args:
            text: Textul pentru generare audio
            output_path: Calea pentru fișierul audio generat (ex. *.mp3)
            lang: Codul limbii (ex. 'ro' -> 'ro-RO')

        Returns:
            Calea către fișierul audio generat
        """
        print(f"🔊 (Google TTS) Generez audio în română...")
        
        # Converteste 'ro' în codul BCP-47 'ro-RO'
        language_code = "ro-RO" 

        try:
            # Setarea textului de intrare
            synthesis_input = texttospeech.SynthesisInput(text=text)

            # Alegerea vocii (WaveNet este calitatea premium)
            # 'alloy' (OpenAI) este înlocuit cu o voce specifică limbii române
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name="ro-RO-Wavenet-A"  # O voce feminină de înaltă calitate
            )

            # Selectarea tipului de fișier (MP3, ca în exemplul tău)
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )

            # Apelul API către Google Cloud TTS
            response = self.tts_client.synthesize_speech(
                input=synthesis_input, 
                voice=voice, 
                audio_config=audio_config
            )

            # Salvarea fișierului audio
            with open(output_path, "wb") as f:
                f.write(response.audio_content) # response.audio_content în loc de response.read()

            print(f"✅ Audio generat: {output_path}")
            return output_path

        except Exception as e:
            print(f"❌ Eroare la generarea audio (Google TTS): {e}")
            raise

    def generate_summary(self, text: str) -> str:
        """
        Generează un rezumat inteligent al conținutului folosind Google Gemini

        Args:
            text: Textul pentru rezumat

        Returns:
            Rezumatul generat
        """
        print(f"📝 (Gemini) Generez rezumat...")

        # Promptul de sistem este identic
        system_prompt = """Ești un asistent care creează rezumate concise și informative în limba română.
Creează un rezumat structurat cu următoarele secțiuni:

REZUMAT EXECUTIV:
- 2-3 propoziții care captează esența conținutului

PUNCTE CHEIE:
- Lista principalelor idei (3-7 puncte)

DETALII IMPORTANTE:
- Informații relevante suplimentare

CONCLUZII:
- Takeaway-uri finale
"""
        full_prompt = f"{system_prompt}\n\nCreează un rezumat detaliat pentru următorul conținut:\n\n{text}"
        
        config = GenerationConfig(
            temperature=0.5
        )
        
        try:
            # Apelul API către Gemini
            response = self.gemini_model.generate_content(
                full_prompt,
                generation_config=config
            )

            summary = response.text.strip()
            print(f"✓ Rezumat generat ({len(summary)} caractere)")
            return summary
        except Exception as e:
            print(f"✗ Eroare la generarea rezumatului (Gemini): {e}")
            raise

    def save_summary(self, summary: str, output_path: str) -> str:
        """
        Salvează rezumatul într-un fișier text

        Args:
            summary: Rezumatul de salvat
            output_path: Calea pentru fișierul de rezumat

        Returns:
            Calea către fișierul salvat
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"✓ Rezumat salvat: {output_path}")
        return output_path

    # -----------------------
    # 🔁 Sincronizare durată
    # -----------------------
    def _ffprobe_duration_seconds(self, path: str) -> float:
        """Returnează durata unui fișier media în secunde (float) cu ffprobe."""
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(res.stdout or "{}")
        return float(info["format"]["duration"])

    def _build_atempo_chain(self, factor: float) -> str:
        """
        Sparge factorul într-un lanț de atempo-uri în intervalul [0.5, 2.0] per filtru.
        Exemplu: 0.25 -> 'atempo=0.5,atempo=0.5' ; 3.2 -> 'atempo=2.0,atempo=1.6'
        """
        chain = []
        remaining = float(factor)

        while remaining > 2.0:
            chain.append("atempo=2.0")
            remaining /= 2.0

        while remaining < 0.5:
            chain.append("atempo=0.5")
            remaining /= 0.5  # (echivalent cu *2.0 asupra duratei)

        if abs(remaining - 1.0) > 1e-6:
            chain.append(f"atempo={remaining:.6f}")

        return ",".join(chain) if chain else "atempo=1.0"

    def sync_audio_length(self, original_path: str, translated_path: str, out_path: str, tolerance: float = 0.10):
        """
        Ajustează durata audio-ului tradus la durata originalului, păstrând pitch-ul.
        1) Calculează factorul atempo = dur_tradus / dur_orig
        2) Aplică lanțul de atempo în [0.5,2.0] per filtru
        3) Potrivește exact (pad/trim) dacă diferența > tolerance
        """
        orig = self._ffprobe_duration_seconds(original_path)
        trans = self._ffprobe_duration_seconds(translated_path)
        if orig <= 0 or trans <= 0:
            raise RuntimeError("Durate invalide detectate de ffprobe.")

        factor = trans / orig
        print(f"⏱️ Durate: original={orig:.3f}s | tradus={trans:.3f}s → atempo total={factor:.6f}")

        # Dacă deja e în toleranță, doar copiem
        if abs(trans - orig) <= tolerance:
            print(f"ℹ️ Durata este deja în toleranță (±{tolerance}s). Copiez fără ajustări.")
            subprocess.run(["ffmpeg", "-y", "-i", translated_path, out_path], check=True)
            return

        atempo_chain = self._build_atempo_chain(factor)
        print(f"🎛️ Lanț filtre: {atempo_chain}")

        # 1) Time-stretch păstrând pitch-ul
        subprocess.run([
            "ffmpeg", "-y", "-i", translated_path,
            "-af", atempo_chain,
            out_path
        ], check=True)

        # 2) Ajustare fină (pad/trim) dacă mai este nevoie
        new_dur = self._ffprobe_duration_seconds(out_path)
        diff = orig - new_dur  # >0: e mai scurt, <0: e mai lung
        print(f"🧪 După atempo: {new_dur:.3f}s (diff față de țintă: {diff:+.3f}s)")

        if abs(diff) <= tolerance:
            print(f"✅ Durata finală în toleranță (±{tolerance}s).")
            return

        tmp_fix = str(Path(out_path).with_suffix(".fix.mp3"))

        if diff > 0:  # prea scurt → pad cu tăcere până la orig
            pad_dur = f"{orig:.6f}"
            subprocess.run([
                "ffmpeg", "-y", "-i", out_path,
                "-af", f"apad=pad_dur={pad_dur}",
                tmp_fix
            ], check=True)
        else:  # prea lung → taie exact la orig
            subprocess.run([
                "ffmpeg", "-y", "-i", out_path,
                "-af", f"atrim=duration={orig:.6f}",
                tmp_fix
            ], check=True)

        Path(out_path).unlink(missing_ok=True)
        Path(tmp_fix).rename(out_path)

        final_dur = self._ffprobe_duration_seconds(out_path)
        print(f"🎯 Durată finală: {final_dur:.3f}s (țintă: {orig:.3f}s) — diferență {abs(final_dur - orig):.3f}s")

    # -----------------------
    # Pipeline AUDIO
    # -----------------------
    def process_audio_file(self, audio_path: str, output_dir: str = None) -> dict:
        """
        Procesează un fișier audio complet:
        - Transcriere → Traducere → TTS RO → 🔁 Sincronizare la durata originalului → Rezumat
        - Salvează rezultatul ca <nume>_RO.mp3 + <nume>_RO_rezumat.txt
        """
        print(f"\n{'='*60}")
        print(f"🎵 PROCESARE FIȘIER AUDIO")
        print(f"{'='*60}\n")

        audio_path = Path(audio_path)
        output_dir = Path(output_dir) if output_dir else audio_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        base_name = audio_path.stem

        # Definire căi pentru fișierele de ieșire
        output_audio_path = output_dir / f"{base_name}_RO.mp3"           # standardizăm pe .mp3
        output_summary_path = output_dir / f"{base_name}_RO_rezumat.txt"
        temp_audio_path = output_dir / f"{base_name}_temp.mp3"

        results = {}

        try:
            # 1. Transcriere audio original
            transcript = self.transcribe_audio_AI(str(audio_path))

            # 2. Traducere în română
            translated_text = self.translate_to_romanian(transcript)

            # 3. Generare audio în română (temporar)
            self.generate_audio_from_text(translated_text, str(temp_audio_path))

            # 4. 🔁 Sincronizare la durata originalului
            self.sync_audio_length(
                original_path=str(audio_path),
                translated_path=str(temp_audio_path),
                out_path=str(output_audio_path),
                tolerance=0.10  # ±0.10s
            )
            results['audio'] = str(output_audio_path)

            # 5. Generare rezumat
            summary = self.generate_summary(translated_text)
            self.save_summary(summary, str(output_summary_path))
            results['summary'] = str(output_summary_path)

            # 6. Curățare temporare
            Path(temp_audio_path).unlink(missing_ok=True)

            print(f"\n{'='*60}")
            print(f"✓ PROCESARE AUDIO COMPLETĂ")
            print(f"  Audio tradus (sincronizat): {output_audio_path}")
            print(f"  Rezumat: {output_summary_path}")
            print(f"{'='*60}\n")

            return results

        except Exception as e:
            print(f"\n✗ Eroare la procesarea fișierului audio: {e}")
            # cleanup temp
            Path(temp_audio_path).unlink(missing_ok=True)
            raise

    # -----------------------
    # Pipeline VIDEO
    # -----------------------
    def process_video_file(self, video_path: str, output_dir: str = None) -> dict:
        """
        Procesează un fișier video complet:
        - Extragere audio → Transcriere → Traducere → TTS RO
        - 🔁 Sincronizare audio RO la durata audio-ului original
        - Mux înapoi peste video → Rezumat → Cleanup
        """
        print(f"\n{'='*60}")
        print(f"🎬 PROCESARE FIȘIER VIDEO")
        print(f"{'='*60}\n")

        video_path = Path(video_path)
        output_dir = Path(output_dir) if output_dir else video_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        base_name = video_path.stem
        extension = video_path.suffix

        # Definire căi pentru fișierele de ieșire
        temp_audio_original = output_dir / f"{base_name}_audio_original.mp3"
        temp_audio_ro = output_dir / f"{base_name}_audio_ro.mp3"
        temp_audio_ro_synced = output_dir / f"{base_name}_audio_ro_synced.mp3"
        output_video_path = output_dir / f"{base_name}_RO{extension}"
        output_summary_path = output_dir / f"{base_name}_RO_rezumat.txt"

        results = {}

        try:
            # 1. Extragere audio din video
            self.extract_audio_from_video(str(video_path), str(temp_audio_original))

            # 2. Transcriere audio
            transcript = self.transcribe_audio(str(temp_audio_original))

            # 3. Traducere în română
            translated_text = self.translate_to_romanian(transcript)

            # 4. Generare audio în română
            self.generate_audio_from_text(translated_text, str(temp_audio_ro))

            # 4.5 🔁 Sincronizare durată audio RO la durata originalului
            self.sync_audio_length(
                original_path=str(temp_audio_original),
                translated_path=str(temp_audio_ro),
                out_path=str(temp_audio_ro_synced),
                tolerance=0.10  # ±0.10s
            )

            # 5. Combinare audio tradus (sincronizat) cu video original
            self.combine_audio_with_video(
                str(video_path),
                str(temp_audio_ro_synced),
                str(output_video_path)
            )
            results['video'] = str(output_video_path)

            # 6. Generare rezumat
            summary = self.generate_summary(translated_text)
            self.save_summary(summary, str(output_summary_path))
            results['summary'] = str(output_summary_path)

            # 7. Curățare fișiere temporare
            for p in (temp_audio_original, temp_audio_ro, temp_audio_ro_synced):
                Path(p).unlink(missing_ok=True)

            print(f"\n{'='*60}")
            print(f"✓ PROCESARE VIDEO COMPLETĂ")
            print(f"  Video tradus: {output_video_path}")
            print(f"  Rezumat: {output_summary_path}")
            print(f"{'='*60}\n")

            return results

        except Exception as e:
            print(f"\n✗ Eroare la procesarea fișierului video: {e}")
            # Curățare fișiere temporare în caz de eroare
            for p in (temp_audio_original, temp_audio_ro, temp_audio_ro_synced):
                Path(p).unlink(missing_ok=True)
            raise

    # -----------------------
    # Router generic
    # -----------------------
    def process_file(self, filepath: str, output_dir: str = None) -> dict:
        """
        Procesează automat un fișier (audio sau video)

        Args:
            filepath: Calea către fișier
            output_dir: Directorul pentru fișierele de ieșire

        Returns:
            Dicționar cu căile către fișierele generate
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Fișierul nu există: {filepath}")

        if self.is_audio_file(filepath):
            return self.process_audio_file(filepath, output_dir)
        elif self.is_video_file(filepath):
            return self.process_video_file(filepath, output_dir)
        else:
            raise ValueError(f"Tip de fișier nesuportat: {filepath}")


def main():
    """Funcție principală pentru utilizare din linia de comandă"""

    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║     PROCESOR AUDIO/VIDEO - TRADUCERE ÎN ROMÂNĂ            ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    if len(sys.argv) < 2:
        print("Utilizare: python script.py <cale_fisier> [director_iesire]")
        print("\nExemple:")
        print("  python script.py video.mp4")
        print("  python script.py audio.mp3 ./output")
        sys.exit(1)

    filepath = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        # Inițializare procesor
        processor = AudioVideoProcessor()

        # Procesare fișier
        results = processor.process_file(filepath, output_dir)

        print("\n✓ Procesare finalizată cu succes!")
        print(f"\nFișiere generate:")
        for key, value in results.items():
            print(f"  - {key}: {value}")

    except Exception as e:
        print(f"\n✗ Eroare: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
