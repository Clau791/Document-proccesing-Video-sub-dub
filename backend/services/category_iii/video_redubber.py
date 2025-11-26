# pip install git+https://github.com/SWivid/F5-TTS.git

# # ce5. Alte dependențe
# pip install openai-whisper deep-translator pydub scipy soundfile numpy requests

import os
import sys
import subprocess
import requests
import json
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict, Any

import torch
import torchaudio
import whisper
from pydub import AudioSegment
import numpy as np

# === CONFIGURARE RTX 5090 ===
# Pe un 5090 (probabil 24GB+ VRAM), putem rula lejer 2-3 instanțe F5 simultan
# sau una singură extrem de rapidă. Recomand 1 worker pentru stabilitate maximă,
# deoarece F5 consumă mult VRAM per inferență lungă.
MAX_WORKERS = 1 
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:32b"  # Asigură-te că rulează în background
USE_QWEN_OPTIMIZATION = True  # True = Rescrie textul pentru a se potrivi la timp

# === IMPORTURI DIRECTE F5-TTS (Surgical Fix) ===
try:
    from f5_tts.model import DiT
    from f5_tts.infer.utils_infer import (
        load_vocoder,
        load_model,
        preprocess_ref_audio_text,
        infer_process
    )
    F5_AVAILABLE = True
except ImportError:
    print("CRITICAL: F5-TTS nu este instalat corect din sursă.")
    print("Rulează: pip install git+https://github.com/SWivid/F5-TTS.git")
    sys.exit(1)

PROCESSED_DIR = Path("processed_linux_pro")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


class LLMTranslator:
    """Optimizează textul pentru dublaj (Time-Constrained Translation)."""
    def __init__(self):
        self.api_url = OLLAMA_URL
        self.model = OLLAMA_MODEL

    def translate_smart(self, text: str, duration_sec: float) -> str:
        if not text.strip(): return ""
        
        # Prompt pentru Qwen: "Tradu, dar fii scurt!"
        system_prompt = (
            f"Translate English to Romanian for a dubbing script. "
            f"Target duration: approx {duration_sec:.1f} seconds. "
            "Constraints:\n"
            "1. Romanian tends to be longer. You MUST condense/paraphrase to fit the time.\n"
            "2. Be natural, colloquial (use 'tu' not 'dumneavoastră').\n"
            "3. Output ONLY the Romanian translation."
        )

        try:
            payload = {
                "model": self.model,
                "prompt": f"{system_prompt}\n\nInput: \"{text}\"\nTranslation:",
                "stream": False,
                "options": {"temperature": 0.3, "num_ctx": 4096}
            }
            resp = requests.post(self.api_url, json=payload, timeout=10)
            if resp.status_code == 200:
                return resp.json().get("response", "").strip().replace('"', '')
        except Exception as e:
            print(f"[LLM WARN] Qwen offline/error, falling back to literal translation. ({e})")
        
        # Fallback simplu dacă Qwen nu răspunde (pentru testare)
        return text 


class F5EngineCore:
    """
    Motor F5-TTS optimizat pentru Linux/CUDA.
    Încarcă modelul manual folosind utils_infer pentru control total.
    """
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[F5-TTS] Initializing on {self.device.upper()} (Target: RTX 5090)")
        
        if self.device == "cpu":
            print("[WARN] Running F5 on CPU is extremely slow!")

        # 1. Încărcare Vocoder (Vocos)
        self.vocoder = load_vocoder(is_local=False)

        # 2. Configurare Model DiT (Diffusion Transformer)
        # Aceștia sunt parametrii default pentru F5-TTS Base
        model_cls = DiT
        model_cfg = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)

        # 3. Încărcare Checkpoint
        # Va descărca automat de pe HuggingFace (~1GB) la prima rulare
        self.model = load_model(
            model_cls, 
            model_cfg, 
            ckpt_path="hf://SWivid/F5-TTS/F5TTS_Base/model_1200000.safetensors",
            mel_spec_type="vocos", 
            vocab_file="", 
            ode_method="euler", 
            use_ema=True, 
            device=self.device
        )
        self.lock = threading.Lock()

    def synthesize(self, text: str, ref_audio_path: Path, out_path: Path):
        """
        Generează audio folosind referința pentru clonare.
        """
        if not text: return False
        
        with self.lock:
            try:
                # Preprocesare (Ref Audio + Text)
                ref_audio_str = str(ref_audio_path)
                ref_text = "" # Lăsăm gol pentru zero-shot (modelul nu știe ce se zice în ref)
                
                main_process, final_sample_rate, _, _, _, _, _, _ = preprocess_ref_audio_text(
                    ref_audio_str, 
                    ref_text, 
                    text, 
                    show_info=False, 
                    device=self.device
                )

                # Inferență (Generarea efectivă)
                # nfe_step=32 este standard pentru calitate. Pe 5090 va zbura.
                generated_audio, sample_rate, _ = infer_process(
                    ref_audio_str, 
                    ref_text, 
                    text, 
                    self.model, 
                    self.vocoder, 
                    mel_spec_type="vocos", 
                    speed=1.0, 
                    device=self.device,
                    nfe_step=32, 
                    cfg_strength=2.0, 
                    sway_sampling_coef=-1.0, 
                    t_interpolator="Linear"
                )

                # Salvare
                torchaudio.save(str(out_path), generated_audio, sample_rate)
                return True
            except Exception as e:
                print(f"[F5 ERROR] Synthesis failed for '{text[:20]}...': {e}")
                import traceback
                traceback.print_exc()
                return False

class VideoRedubberPro:
    def __init__(self):
        print("[INIT] Loading Whisper (Large-v3)...")
        # Whisper Large-v3 consumă ~4GB VRAM. Pe 5090 e neglijabil.
        self.whisper = whisper.load_model("large-v3", device="cuda")
        self.llm = LLMTranslator()
        self.tts = None # Lazy load

    def _get_tts(self):
        if not self.tts:
            self.tts = F5EngineCore()
        return self.tts

    def process(self, video_path: str):
        video_path = Path(video_path)
        job_id = video_path.stem
        work_dir = PROCESSED_DIR / job_id
        work_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n=== START JOB: {video_path.name} ===")

        # 1. Extragere Resurse (Audio Full + Sample Voce)
        full_wav = work_dir / "full.wav"
        voice_ref = work_dir / "ref_voice.wav"
        
        # Audio full la 24k (F5 native SR)
        subprocess.run(["ffmpeg", "-y", "-i", str(video_path), "-vn", "-ac", "1", "-ar", "24000", str(full_wav)], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Extragem un sample curat (ex: secunda 30, timp de 5s)
        # Ideal: un algoritm care detectează voce, dar hardcoded e ok pentru test
        subprocess.run(["ffmpeg", "-y", "-ss", "00:00:30", "-t", "5", "-i", str(video_path), 
                        "-vn", "-ac", "1", "-ar", "24000", str(voice_ref)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if not voice_ref.exists() or voice_ref.stat().st_size < 1000:
            print("[WARN] Sample voce eșuat. Folosesc tot audio-ul (riscant).")
            voice_ref = full_wav

        # 2. Transcriere
        print("[STEP 1] Transcribing...")
        res = self.whisper.transcribe(str(full_wav))
        segments = res["segments"]
        
        # Eliberăm memoria Whisper pentru a face loc F5 (opțional pe 5090, dar good practice)
        del self.whisper
        torch.cuda.empty_cache()

        # 3. Procesare Segmente
        print(f"[STEP 2] Processing {len(segments)} segments...")
        tts_engine = self._get_tts()
        
        final_timeline = AudioSegment.silent(duration=0)
        cursor_ms = 0
        
        processed_data = []

        # Funcție helper pentru thread pool
        def process_single(idx, seg):
            start = seg['start']
            end = seg['end']
            duration = end - start
            text_en = seg['text'].strip()
            
            if duration < 0.5 or not text_en: return None

            # Traducere
            text_ro = text_en
            if USE_QWEN_OPTIMIZATION:
                text_ro = self.llm.translate_smart(text_en, duration)
            
            # TTS
            out_seg_path = work_dir / f"seg_{idx}.wav"
            if not out_seg_path.exists():
                tts_engine.synthesize(text_ro, voice_ref, out_seg_path)
            
            if out_seg_path.exists():
                return {"idx": idx, "start": start, "end": end, "path": out_seg_path, "text": text_ro}
            return None

        # Execuție
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(process_single, i, s) for i, s in enumerate(segments)]
            for f in as_completed(futures):
                res = f.result()
                if res:
                    processed_data.append(res)
                    print(f"   Done [{res['idx']}]: {res['text'][:30]}...")

        # Sortăm după index ca să refacem ordinea
        processed_data.sort(key=lambda x: x['idx'])

        # 4. Asamblare Timeline
        print("[STEP 3] Assembling Timeline...")
        for item in processed_data:
            start_ms = int(item['start'] * 1000)
            target_dur_ms = int((item['end'] - item['start']) * 1000)
            
            # Gestionare spațiu gol
            gap = start_ms - cursor_ms
            if gap > 0:
                final_timeline += AudioSegment.silent(duration=gap)
            
            # Încărcare audio generat
            seg_audio = AudioSegment.from_file(item['path'])
            
            # Smart Speed (dacă tot e prea lung, accelerăm puțin)
            curr_len = len(seg_audio)
            if curr_len > 0:
                ratio = curr_len / target_dur_ms
                if ratio > 1.3: ratio = 1.3 # Hard limit
                elif ratio < 0.8: ratio = 1.0
                
                if ratio > 1.05:
                    seg_audio = seg_audio.speedup(playback_speed=ratio)
            
            final_timeline += seg_audio
            cursor_ms = start_ms + len(seg_audio)

        # 5. Export Final
        print("[STEP 4] Muxing Video...")
        dub_track = work_dir / "dub_track.wav"
        final_timeline.export(dub_track, format="wav")
        
        final_video = PROCESSED_DIR / f"{job_id}_F5_RTX5090.mp4"
        subprocess.run([
            "ffmpeg", "-y", 
            "-i", str(video_path), 
            "-i", str(dub_track),
            "-map", "0:v:0", "-map", "1:a:0", # Video original + Audio Nou
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", 
            str(final_video)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"\n[SUCCESS] Video salvat: {final_video}")
        return str(final_video)

if __name__ == "__main__":
    # Testare
    # Asigură-te că ai fișierul input.mp4 în folder
    if len(sys.argv) > 1:
        vfile = sys.argv[1]
    else:
        vfile = "input.mp4" # Default

    if Path(vfile).exists():
        app = VideoRedubberPro()
        app.process(vfile)
    else:
        print(f"Fișierul {vfile} nu există.")