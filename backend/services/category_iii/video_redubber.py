"""
Video redubber orientat pe calitate.

Pipeline:
1) Extrage audio din video (wav 16k)
2) Transcrie cu Whisper (detectează limba)
3) Traduce segmentele în limba țintă cu GoogleTranslator (auto → dest_lang)
4) TTS local pe fiecare segment (model open-source, ex: Coqui XTTS v2)
5) Ajustează durata fiecărui segment la lungimea originală (atempo)
6) Concatenează pe o piesă audio silențioasă și înlocuiește audio-ul video cu FFmpeg

Nota: pentru TTS calitativ și multilingual, recomand modelul open-source
`tts_models/multilingual/multi-dataset/xtts_v2` (Coqui TTS).
Instalare: pip install TTS
Rulează local, necesită torch. Dacă TTS nu este instalat, vom ridica o eroare clară.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

import torch
import whisper
from deep_translator import GoogleTranslator
from pydub import AudioSegment

PROCESSED_DIR = Path("processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


class LocalTTSEngine:
    """Wrapper peste Coqui TTS (XTTS v2) cu voice cloning opțional și GPU suport."""

    def __init__(self, model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2", use_gpu: bool = False, speaker_wav: Optional[str] = None):
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.speaker_wav = speaker_wav
        try:
            from TTS.api import TTS  # type: ignore
            self.tts = TTS(model_name=model_name, progress_bar=False)
            # Mutăm explicit pe device; înlocuiește avertizarea tts.gpu
            device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
            try:
                self.tts.to(device)
            except Exception:
                # fallback silențios; Coqui poate ignora .to în funcție de versiune
                pass
        except ImportError as e:
            raise RuntimeError(
                "TTS nu este instalat. Instalează un model local calitativ cu `pip install TTS` "
                "și asigură-te că ai torch compatibil."
            ) from e

    def synthesize(self, text: str, language: str, out_path: Path) -> Path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        kwargs = {"language": language}
        if self.speaker_wav:
            kwargs["speaker_wav"] = self.speaker_wav
        self.tts.tts_to_file(text=text, file_path=str(out_path), **kwargs)
        return out_path


def run_cmd(cmd: List[str]) -> None:
    completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{completed.stderr.decode(errors='ignore')}")


def extract_audio(video_path: Path, out_wav: Path, sr: int = 48000) -> Path:
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn",
        "-ac", "1",
        "-ar", str(sr),
        "-f", "wav",
        str(out_wav)
    ]
    run_cmd(cmd)
    return out_wav


def stretch_to_duration(src_audio: Path, target_duration_ms: float) -> Path:
    """
    Ajustează durata prin atempo. Folosește ffmpeg pentru calitate mai bună.
    """
    tmp_out = src_audio.with_suffix(".stretched.wav")
    audio = AudioSegment.from_file(src_audio)
    current_ms = len(audio)
    if current_ms == 0:
        raise RuntimeError("Segment TTS gol.")
    ratio = target_duration_ms / current_ms
    # ffmpeg atempo permite 0.5–2.0 per filtru; lanțuim dacă e nevoie.
    tempos = []
    remaining = ratio
    while remaining < 0.5:
        tempos.append(0.5)
        remaining /= 0.5
    while remaining > 2.0:
        tempos.append(2.0)
        remaining /= 2.0
    tempos.append(remaining)

    filters = ",".join([f"atempo={t:.3f}" for t in tempos])
    cmd = ["ffmpeg", "-y", "-i", str(src_audio), "-filter:a", filters, str(tmp_out)]
    run_cmd(cmd)
    return tmp_out


def assemble_timeline(segments: List[Dict[str, Any]], total_ms: float, out_path: Path) -> Path:
    """
    Lipim segmentele sintetizate la start_time corespunzător.
    """
    base = AudioSegment.silent(duration=int(total_ms))
    for seg in segments:
        audio = AudioSegment.from_file(seg["audio_path"])
        start_ms = int(seg["start"] * 1000)
        base = base.overlay(audio, position=start_ms)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    base.export(out_path, format="wav")
    return out_path


def mux_audio_to_video(video_path: Path, audio_path: Path, out_video: Path) -> Path:
    out_video.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "320k",
        "-af", "loudnorm",
        "-shortest",
        str(out_video),
    ]
    run_cmd(cmd)
    return out_video


class VideoRedubber:
    def __init__(self, processed_dir: Path = PROCESSED_DIR, tts_model: str = "tts_models/multilingual/multi-dataset/xtts_v2"):
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.tts_model = tts_model
        self._ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        self._ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:32b")

        # Lazy init pentru Whisper și TTS (consumă memorie)
        self._whisper_model = None
        self._tts_engine = None

    def _get_whisper(self):
        if self._whisper_model is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._whisper_model = whisper.load_model("large-v3", device=device)
        return self._whisper_model

    def _get_tts(self, speaker_wav: Optional[str]):
        if self._tts_engine is None or (self._tts_engine.speaker_wav != speaker_wav):
            self._tts_engine = LocalTTSEngine(model_name=self.tts_model, use_gpu=torch.cuda.is_available(), speaker_wav=speaker_wav)
        return self._tts_engine

    def _translate_local(self, text: str, target_lang: str) -> str:
        try:
            import requests
            prompt = (
                f"Tradu în limba {target_lang} textul următor, păstrând sensul, timpii și numele proprii. "
                f"Returnează DOAR traducerea:\n\n{text}"
            )
            resp = requests.post(
                f"{self._ollama_host}/v1/completions",
                json={"model": self._ollama_model, "prompt": prompt},
                timeout=60,
            )
            if resp.ok:
                data = resp.json()
                return (data.get("choices") or [{}])[0].get("text", "").strip()
        except Exception as e:
            print(f"[REDUB] Ollama translate fallback: {e}")
        return ""

    def redub(self, video_path: str, dest_lang: str = "ro", speaker_wav: Optional[str] = None, translator_mode: str = "cloud") -> Dict[str, Any]:
        """
        Redublează video în limba dest_lang cu detectare automată a limbii sursă.
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        job_id = video_path.stem
        work_dir = self.processed_dir / job_id
        work_dir.mkdir(parents=True, exist_ok=True)
        print(f"[REDUB] Start {video_path.name} -> {dest_lang.upper()}")

        # 1) Extrage audio
        raw_audio = work_dir / f"{job_id}_raw.wav"
        extract_audio(video_path, raw_audio)
        print(f"[REDUB] Audio extras: {raw_audio.name}")

        # 2) Transcriere + detectare limbă
        model = self._get_whisper()
        print("[REDUB] Transcriere Whisper...")
        transcribed = model.transcribe(str(raw_audio), task="transcribe")
        segments = transcribed.get("segments", [])
        detected_lang = transcribed.get("language", "auto")
        print(f"[REDUB] Transcriere gata. Segmente: {len(segments)}, limbă detectată: {detected_lang}")

        if not segments:
            raise RuntimeError("Nu s-au găsit segmente în transcriere.")

        # 3) Traduce segmente
        translator = GoogleTranslator(source="auto", target=dest_lang) if translator_mode == "cloud" else None
        for seg in segments:
            if translator_mode == "cloud" and translator:
                seg["translated_text"] = translator.translate(seg["text"])
            else:
                seg["translated_text"] = self._translate_local(seg["text"], dest_lang) or seg["text"]
        print(f"[REDUB] Traducere mod={translator_mode}, segmente: {len(segments)}")
        print("[REDUB] Traducere segmente completă.")

        # 4) TTS pe fiecare segment cu ajustare durată
        tts = self._get_tts(speaker_wav=speaker_wav)
        tts_segments: List[Dict[str, Any]] = []
        for idx, seg in enumerate(segments):
            text = seg.get("translated_text", "").strip()
            if not text:
                continue
            start, end = seg.get("start", 0.0), seg.get("end", 0.0)
            target_ms = max((end - start) * 1000, 300)  # minim 0.3s

            tts_path = work_dir / f"seg_{idx:04d}.wav"
            tts.synthesize(text, language=dest_lang, out_path=tts_path)

            stretched = stretch_to_duration(tts_path, target_ms)
            tts_segments.append({
                "start": start,
                "end": end,
                "audio_path": stretched
            })

        if not tts_segments:
            raise RuntimeError("Nu s-au generat segmente TTS.")
        print(f"[REDUB] TTS generat pentru {len(tts_segments)} segmente.")

        total_ms = max(seg["end"] for seg in segments) * 1000 + 500
        dubbed_wav = work_dir / f"{job_id}_dubbed.wav"
        assemble_timeline(tts_segments, total_ms, dubbed_wav)
        print(f"[REDUB] Timeline audio asamblat: {dubbed_wav.name}")

        # 5) Mux audio în video
        out_video = self.processed_dir / f"{job_id}_{dest_lang}.mp4"
        mux_audio_to_video(video_path, dubbed_wav, out_video)
        print(f"[REDUB] Mux final: {out_video.name}")

        # 6) SRT tradus
        srt_path = self.processed_dir / f"{job_id}_{dest_lang}.srt"
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments, start=1):
                start = seg["start"]
                end = seg["end"]
                text = seg.get("translated_text", "").strip()
                f.write(f"{i}\n")
                f.write(f"{self._fmt_srt_time(start)} --> {self._fmt_srt_time(end)}\n")
                f.write(f"{text}\n\n")

        return {
            "video_file": f"/download/{out_video.name}",
            "subtitle_file": f"/download/{srt_path.name}",
            "detected_language": detected_lang,
            "note": (
                "Redublare efectuată cu Whisper + traducere GoogleTranslator + TTS local. "
                "Poți schimba modelul TTS în LocalTTSEngine."
            )
        }

    @staticmethod
    def _fmt_srt_time(t: float) -> str:
        hours = int(t // 3600)
        minutes = int((t % 3600) // 60)
        seconds = int(t % 60)
        millis = int((t - int(t)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"
