import os
import subprocess
import requests
import json
from pathlib import Path
from typing import List, Optional

import torch
import whisper
from pydub import AudioSegment

# === CONFIGURARE ===
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:32b"  # Asigură-te că ai tras modelul cu `ollama pull qwen2.5:32b`
os.environ["COQUI_TOS_AGREED"] = "1"
PROCESSED_DIR = Path("processed_dubbing_qwen")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

class AudioTools:
    @staticmethod
    def extract_wav(video_path: Path, out_path: Path, sr: int = 22050):
        cmd = ["ffmpeg", "-y", "-i", str(video_path), "-vn", "-ac", "1", "-ar", str(sr), "-f", "wav", str(out_path)]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @staticmethod
    def get_voice_sample(video_path: Path, out_sample_path: Path):
        # Extrage 8 secunde de la minutul 00:30 sau 20% din durată
        cmd = ["ffmpeg", "-y", "-ss", "00:00:15", "-t", "8", "-i", str(video_path),
               "-vn", "-ac", "1", "-ar", "22050", "-f", "wav", str(out_sample_path)]
        # Fallback simplu dacă ffmpeg dă eroare (ex: video prea scurt), nu oprim scriptul
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            print("[WARN] Nu s-a putut extrage sample voce, se va folosi default.")
        return out_sample_path

    @staticmethod
    def smart_stretch(audio_path: Path, target_duration_ms: float) -> AudioSegment:
        seg = AudioSegment.from_file(audio_path)
        if len(seg) < 100: return seg
        
        ratio = len(seg) / target_duration_ms
        # Qwen ar trebui să rezolve lungimea, deci permitem doar corecții fine (max 1.2x)
        if ratio > 1.25:
            ratio = 1.25 # Cap at 1.25x speedup
        elif ratio < 0.9:
            ratio = 1.0 # Nu încetinim dacă e prea scurt, lăsăm pauză

        if 0.95 <= ratio <= 1.05: return seg
        return seg.speedup(playback_speed=ratio)

class LLMTranslator:
    """Interfață cu Qwen2.5 via Ollama pentru traduceri optimizate de dublaj."""
    def __init__(self, model_name=OLLAMA_MODEL):
        self.model = model_name
        self.api_url = OLLAMA_URL

    def translate_for_dubbing(self, text: str) -> str:
        if not text.strip(): return ""
        
        # Prompt ingineresc pentru sincronizare labială (aproximativă) și durată
        system_prompt = (
            "You are a professional dubbing translator for movies. "
            "Translate the input text from English to Romanian. "
            "CRITICAL CONSTRAINTS:\n"
            "1. The Romanian translation MUST have roughly the same speaking duration as the English text.\n"
            "2. Be conversational and natural. Use 'tu' instead of 'dumneavoastră' unless strictly formal.\n"
            "3. If the direct translation is too long, shorten it by paraphrasing while keeping the meaning.\n"
            "4. Output ONLY the Romanian translation. No quotes, no explanations."
        )

        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\nInput: \"{text}\"\nTranslation:",
            "stream": False,
            "options": {
                "temperature": 0.3, # Mai creativ puțin pentru reformulări, dar stabil
                "num_ctx": 4096
            }
        }

        try:
            resp = requests.post(self.api_url, json=payload, timeout=30)
            if resp.status_code == 200:
                result = resp.json().get("response", "").strip()
                # Curățăm eventuale ghilimele adăugate de LLM
                return result.replace('"', '').replace("Translation:", "").strip()
        except Exception as e:
            print(f"[LLM Error] {e}")
            return text # Fallback: returnăm originalul sau folosim Google Translate
        return text

class XTTSEngine:
    def __init__(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[TTS] Loading XTTS v2 on {device}...")
        from TTS.api import TTS
        # Încărcare model. Prima rulare va dura (download ~2GB)
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

    def synthesize(self, text: str, speaker_wav: Path, out_path: Path):
        try:
            self.tts.tts_to_file(
                text=text, 
                file_path=str(out_path), 
                speaker_wav=str(speaker_wav), 
                language="ro"
            )
            return True
        except Exception as e:
            print(f"[TTS Error] {e}")
            return False

class DubbingPipeline:
    def __init__(self):
        # Inițializăm componentele
        print("[INIT] Loading Whisper...")
        self.whisper = whisper.load_model("medium", device="cuda" if torch.cuda.is_available() else "cpu")
        self.llm = LLMTranslator()
        # TTS se încarcă la cerere sau aici, atenție la VRAM!
        self.tts = XTTSEngine()

    def run(self, video_path: str):
        video_path = Path(video_path)
        job_id = video_path.stem
        work_dir = PROCESSED_DIR / job_id
        work_dir.mkdir(parents=True, exist_ok=True)

        # 1. Audio
        print("1. Extracting audio & voice sample...")
        full_wav = work_dir / "original.wav"
        voice_ref = work_dir / "voice_ref.wav"
        if not full_wav.exists():
            AudioTools.extract_wav(video_path, full_wav)
            AudioTools.get_voice_sample(video_path, voice_ref)

        # 2. Transcriere
        print("2. Transcribing with Whisper...")
        # Folosim word_timestamps pentru acuratețe mai mare
        transcription = self.whisper.transcribe(str(full_wav), word_timestamps=False)
        segments = transcription["segments"]

        # 3. Procesare Loop (Translate -> TTS -> Stretch)
        print(f"3. Processing {len(segments)} segments with Qwen2.5 & XTTS...")
        
        final_timeline = AudioSegment.silent(duration=0)
        cursor_ms = 0 # Unde suntem în timeline-ul final

        for i, seg in enumerate(segments):
            start_ms = int(seg['start'] * 1000)
            end_ms = int(seg['end'] * 1000)
            orig_duration = end_ms - start_ms
            text_en = seg['text'].strip()

            if not text_en or orig_duration < 500:
                continue

            # A. Traducere LLM
            text_ro = self.llm.translate_for_dubbing(text_en)
            print(f"   [{i}] EN: {text_en}\n       RO: {text_ro}")

            # B. TTS
            seg_file = work_dir / f"seg_{i}.wav"
            success = self.tts.synthesize(text_ro, voice_ref, seg_file)

            if success and seg_file.exists():
                # C. Smart Stretch
                audio_chunk = AudioTools.smart_stretch(seg_file, orig_duration)
            else:
                audio_chunk = AudioSegment.silent(duration=orig_duration)

            # D. Asamblare Timeline (Sync Logic)
            # Calculăm câtă liniște trebuie între segmentul anterior și acesta
            gap = start_ms - cursor_ms
            if gap > 0:
                final_timeline += AudioSegment.silent(duration=gap)
            elif gap < 0:
                # Overlap! Tăiem din pauza anterioară sau facem crossfade dacă e grav
                # Aici simplificăm: ignorăm suprapunerea mică, dar resetăm cursorul
                pass
            
            final_timeline += audio_chunk
            cursor_ms = start_ms + len(audio_chunk) # Actualizăm cursorul real

        # 4. Export
        print("4. Muxing final video...")
        dub_wav = work_dir / "dub_track.wav"
        final_timeline.export(dub_wav, format="wav")
        
        out_video = PROCESSED_DIR / f"{job_id}_RO_Qwen.mp4"
        cmd = [
            "ffmpeg", "-y", "-i", str(video_path), "-i", str(dub_wav),
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
            "-shortest", str(out_video)
        ]
        subprocess.run(cmd, check=True)
        print(f"DONE! Video: {out_video}")

if __name__ == "__main__":
    # Verifică să ai Ollama pornit!
    try:
        requests.get("http://localhost:11434")
    except:
        print("EROARE: Ollama nu pare să fie pornit. Rulează 'ollama serve' în alt terminal.")
        exit()

    pipeline = DubbingPipeline()
    pipeline.run("video_tau.mp4")