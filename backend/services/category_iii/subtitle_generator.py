
from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path
from typing import List, Tuple
import requests

import ffmpeg
import pysubs2
import whisper
from deep_translator import GoogleTranslator

from services.progress_bar import send_task_progress
from services.category_v.summary_service import SummaryService


class SubtitleGenerator:
    """
    Flux complet de subtitrare:
    1) Transcriere video cu Whisper (auto detectează limba).
    2) Traducere segment-cu-segment în română (GoogleTranslator).
    3) Scriere SRT în 'processed/'.
    4) Dacă attach_mode == 'hard', arde subtitrarea în video cu ffmpeg.
    """

    def __init__(
        self,
        processed_dir: str = "processed",
        whisper_model: str = "small",
    ):
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.whisper_model_name = whisper_model
        self._model = None
        self._global_start = None
        self._total_expected = None
        self._summary_service = SummaryService()
        self._ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        self._ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:32b")

    # ------------ Internals ------------
    def _load_model(self):
        if self._model is None:
            # Lazy loading pentru a evita costul la import
            self._model = whisper.load_model(self.whisper_model_name)
        return self._model

    def _transcribe(self, filepath: str):
        model = self._load_model()
        result = model.transcribe(filepath, task="transcribe", verbose=False)
        segments = result.get("segments", [])
        language = result.get("language", "auto")
        return segments, language

    def _translate_ollama(self, text: str, target_lang: str) -> str:
        try:
            import requests
            system_prompt = (
                f"Ești un traducător profesionist. Tradu textul EXACT în limba {target_lang}. "
                f"Păstrează sensul, numele proprii și ordinea logică. "
                f"Nu adăuga comentarii, note, explicații sau text suplimentar. "
                f"Output-ul trebuie să conțină DOAR traducerea în {target_lang}."
            )
            user_prompt = f"Text: {text}\nTraducere:"
            resp = requests.post(
                f"{self._ollama_host}/v1/completions",
                json={
                    "model": self._ollama_model,
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "options": {"temperature": 0.2},
                },
                timeout=60,
            )
            if resp.ok:
                data = resp.json()
                return (data.get("choices") or [{}])[0].get("text", "").strip()
        except Exception as e:
            logging.warning("[SUBTITLE] Ollama translate fallback: %s", e)
        return ""

    def _translate_segments(self, segments: List[dict], target_lang: str, mode: str = "cloud") -> Tuple[List[str], List[str]]:
        """
        Returnează (texte_traduse, texte_originale).
        În caz de eroare de traducere, întoarce textul original pentru acel segment.
        """
        translator = GoogleTranslator(source="auto", target=target_lang) if mode == "cloud" else None
        translated, originals = [], []
        for seg in segments:
            orig = (seg.get("text") or "").strip()
            originals.append(orig)
            if not orig:
                translated.append("")
                continue
            try:
                if mode == "cloud" and translator:
                    translated.append(translator.translate(orig))
                else:
                    # Pas 1: traducere strictă
                    local = self._translate_ollama(orig, target_lang)
                    first_pass = local or orig
                    # Pas 2: validare/QA cu același model, prompt strict
                    check_prompt = (
                        "Ești un verificator de traduceri. Primești textul sursă și traducerea în română. "
                        "Verifici fidelitatea și corectezi doar dacă e nevoie. "
                        "Nu adăuga explicații sau note. Output = fie „OK” dacă e corect, "
                        "fie traducerea corectată în română (DOAR textul)."
                        f"\n\nSursă: {orig}\nTraducere: {first_pass}\nRăspuns:"
                    )
                    qa_resp = ""
                    try:
                        qa = requests.post(
                            f"{self._ollama_host}/v1/completions",
                            json={
                                "model": self._ollama_model,
                                "prompt": check_prompt,
                                "options": {"temperature": 0.2},
                            },
                            timeout=60,
                        )
                        if qa.ok:
                            qa_data = qa.json()
                            qa_resp = (qa_data.get("choices") or [{}])[0].get("text", "").strip()
                    except Exception as e:
                        logging.warning("[SUBTITLE] QA fallback: %s", e)

                    if qa_resp and qa_resp.upper() != "OK":
                        translated.append(qa_resp)
                    else:
                        translated.append(first_pass)
            except Exception as e:  # pragma: no cover - doar log, nu vrem să spargem fluxul
                logging.warning("Traducere eșuată pentru segment: %s", e)
                translated.append(orig)
        return translated, originals

    def _write_srt(self, segments: List[dict], texts: List[str], srt_path: Path):
        subs = pysubs2.SSAFile()
        for seg, txt in zip(segments, texts):
            start_ms = int(float(seg.get("start", 0)) * 1000)
            end_ms = int(float(seg.get("end", 0)) * 1000)
            event = pysubs2.SSAEvent(start=start_ms, end=end_ms, text=txt)
            subs.append(event)
        subs.save(str(srt_path), encoding="utf-8")

    def _burn_subtitles(self, video_path: Path, srt_path: Path, output_path: Path):
        """
        Arde SRT-ul în video folosind ffmpeg. Video-ul rezultat este salvat în processed/.
        """
        # Quote SRT path to tolerate spații/caractere speciale în căi
        srt_escaped = srt_path.as_posix().replace("'", r"\\'")

        (
            ffmpeg
            .input(str(video_path))
            .output(
                str(output_path),
                vf=f"subtitles='{srt_escaped}'",
                acodec="copy",
                vcodec="libx264",
                preset="fast",
                crf=18,
            )
            .overwrite_output()
            .run(quiet=True)
        )

    def _probe_duration(self, video_path: Path) -> float:
        try:
            meta = ffmpeg.probe(str(video_path))
            for stream in meta.get("streams", []):
                if stream.get("codec_type") == "video" and stream.get("duration"):
                    return float(stream["duration"])
            if "format" in meta and meta["format"].get("duration"):
                return float(meta["format"]["duration"])
        except Exception as e:
            logging.warning("Nu pot obține durata video: %s", e)
        return 0.0

    def _estimate_timeline(self, duration: float, attach_mode: str):
        # Factori configurabili (fallback la valori sigure)
        rt_factor = float(os.getenv("SUBTITLE_RT_FACTOR", "1.2"))  # cât de rapid e whisper vs realtime
        translate_factor = float(os.getenv("SUBTITLE_TRANSLATE_FACTOR", "0.25"))  # procent din durată
        burn_factor = float(os.getenv("SUBTITLE_BURN_FACTOR", "0.5"))  # cât durează burn ca fracție din durată
        summary_factor = float(os.getenv("SUBTITLE_SUMMARY_FACTOR", "0.15"))  # procent din durată pentru rezumat

        duration = max(duration, 60.0)  # evită zero; consideră minim 1 minut

        est_transcribe = duration * rt_factor
        est_translate = duration * translate_factor
        est_burn = duration * burn_factor if attach_mode == "hard" else 0.0
        est_summary = duration * summary_factor
        est_overhead = 8.0  # inițializare/model load

        total = est_transcribe + est_translate + est_burn + est_summary + est_overhead
        return {
            "transcribe": est_transcribe,
            "translate": est_translate,
            "burn": est_burn,
            "summary": est_summary,
            "overhead": est_overhead,
            "total": total,
        }

    def _run_stage(self, label: str, expected_seconds: float, base_percent: float, weight_percent: float, func):
        """
        Rulează o etapă lungă cu ticker de progres bazat pe timp estimat.
        """
        start = time.time()
        done = threading.Event()

        def ticker():
            while not done.is_set():
                elapsed = time.time() - start
                ratio = min(1.0, elapsed / max(expected_seconds, 0.1))
                percent = base_percent + ratio * weight_percent
                eta = max(0.0, (self._total_expected or expected_seconds) - (time.time() - self._global_start))
                send_task_progress(percent=percent, eta_seconds=eta, stage=label, detail="în curs")
                time.sleep(1.0)

        t = threading.Thread(target=ticker, daemon=True)
        t.start()
        try:
            result = func()
        finally:
            done.set()
            t.join(timeout=0.2)

        # Final tick for the stage
        percent = base_percent + weight_percent
        eta = max(0.0, (self._total_expected or expected_seconds) - (time.time() - self._global_start))
        send_task_progress(percent=percent, eta_seconds=eta, stage=label, detail="finalizat")
        return result

    # ------------ API publică ------------
    def generate(self, filepath: str, lang: str = "ro", attach_mode: str = "soft", detail_level: str = "medium", translator_mode: str = "cloud"):
        """
        Generează subtitrare în română pentru videoclipul dat.

        Args:
            filepath: calea către fișierul video încărcat.
            lang: limba țintă (implicit română).
            attach_mode: 'soft' -> returnează SRT; 'hard' -> arde subtitrarea în video.
            detail_level: nivelul de detaliu al rezumatului (brief/medium/deep)
        """
        video_path = Path(filepath)
        attach_mode = (attach_mode or "soft").lower()
        translator_mode = (translator_mode or "cloud").lower()
        print(f"[SUBTITLE] attach_mode={attach_mode}, detail_level={detail_level}, translator_mode={translator_mode}")
        self._global_start = time.time()

        duration = self._probe_duration(video_path)
        timeline = self._estimate_timeline(duration, attach_mode)
        self._total_expected = timeline["total"]

        # Configurăm ponderi pentru progres (sumează la 100)
        pct_transcribe = 55.0
        pct_translate = 25.0 if attach_mode != "hard" else 20.0
        pct_summary = 10.0
        pct_burn = 0.0 if attach_mode != "hard" else 8.0
        pct_finalize = 100.0 - (pct_transcribe + pct_translate + pct_burn)

        send_task_progress(percent=1.0, eta_seconds=timeline["total"], stage="init", detail="pregătire")

        print(f"[SUBTITLE] Transcriere start: {video_path.name}")
        segments, detected_lang = self._run_stage(
            "transcriere",
            expected_seconds=timeline["transcribe"],
            base_percent=0.0,
            weight_percent=pct_transcribe,
            func=lambda: self._transcribe(str(video_path)),
        )
        print(f"[SUBTITLE] Transcriere completă ({len(segments)} segmente), limbă detectată: {detected_lang}")

        print("[SUBTITLE] Traducere segmente...")
        translated_texts, originals = self._run_stage(
            "traducere",
            expected_seconds=timeline["translate"],
            base_percent=pct_transcribe,
            weight_percent=pct_translate,
            func=lambda: self._translate_segments(segments, target_lang=lang, mode=translator_mode),
        )
        print(f"[SUBTITLE] Traducere completă ({len(translated_texts)} segmente)")

        srt_path = self.processed_dir / f"{video_path.stem}_{lang}.srt"
        self._write_srt(segments, translated_texts, srt_path)
        send_task_progress(
            percent=pct_transcribe + pct_translate,
            eta_seconds=max(0.0, timeline["total"] - (time.time() - self._global_start)),
            stage="srt",
            detail="fișier SRT generat",
        )

        # Rezumat video (folosește textul tradus concatenat)
        full_text = "\n".join(translated_texts)
        print("[SUBTITLE] Rezumat video...")
        summary_result = self._run_stage(
            "rezumat",
            expected_seconds=timeline.get("summary", max(8.0, duration * 0.1)),
            base_percent=pct_transcribe + pct_translate,
            weight_percent=pct_summary,
            func=lambda: self._summary_service.summarize_content(
                content_id=video_path.stem,
                text=full_text,
                metadata={
                    "source_type": "video",
                    "lang": lang,
                    "detail": detail_level,
                },
            ),
        )

        response = {
            "attach_mode": attach_mode,
            "subtitle_file": f"/download/{srt_path.name}",
            "subtitle_language": lang,
            "detected_language": detected_lang,
            "segments": len(segments),
            "note": "Subtitrare generată cu Whisper + traducere automată",
            "summary": summary_result.get("summary"),
            "summary_file": f"/download/{summary_result.get('summary_file')}" if summary_result.get("summary_file") else None,
        }

        if attach_mode == "hard":
            output_video = self.processed_dir / f"{video_path.stem}_{lang}_subtitled.mp4"
            self._run_stage(
                "burn",
                expected_seconds=timeline["burn"],
                base_percent=pct_transcribe + pct_translate + pct_summary,
                weight_percent=pct_burn,
                func=lambda: self._burn_subtitles(video_path, srt_path, output_video),
            )
            response["video_file"] = f"/download/{output_video.name}"
        else:
            # Soft attach -> frontend descarcă SRT și îl atașează sau oferă direct link
            response["video_file"] = f"/download/{srt_path.name}"

        send_task_progress(percent=100.0, eta_seconds=0.0, stage="gata", detail="complet")
        print(f"[SUBTITLE] Finalizat. SRT: {srt_path.name}, Video out: {response.get('video_file')}")
        return response
