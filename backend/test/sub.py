"""
Sistem Complet de Subtitrare Automată Multilingvă cu Lip Sync
Suportă: Română, Japoneză, Chineză, Rusă
Funcționare 100% locală, fără API-uri externe
"""

import os
import sys
import json
import time
import numpy as np
import torch
import whisper
import pysubs2
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from moviepy.editor import VideoFileClip
import librosa
import soundfile as sf
from transformers import (
    MarianMTModel, 
    MarianTokenizer,
    Wav2Vec2ForCTC,
    Wav2Vec2Processor
)
from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
# import webvtt  # Removed because it is not used and causes ImportError
import argparse
from tqdm import tqdm

@dataclass
class SubtitleSegment:
    """Clasă pentru stocarea unui segment de subtitrare"""
    start_time: float
    end_time: float
    text: str
    confidence: float = 1.0
    phonemes: Optional[List[str]] = None
    lip_sync_score: float = 0.0

class AdvancedSubtitleSystem:
    """Sistem avansat de subtitrare cu lip sync și traducere multilingvă"""
    
    def __init__(self, use_gpu: bool = True):
        """
        Inițializare sistem
        
        Args:
            use_gpu: Folosește GPU dacă este disponibil
        """
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        print(f"🔧 Sistem inițializat pe: {self.device}")
        
        # Modele pentru transcriere
        self.whisper_models = {}
        
        # Modele pentru traducere
        self.translation_models = {}
        
        # Model VAD pentru detecție voce
        self.vad_model = None
        
        # Configurare limbi suportate
        self.supported_languages = {
            'ro': 'romanian',
            'ja': 'japanese', 
            'zh': 'chinese',
            'ru': 'russian',
            'en': 'english'
        }
        
        # Mapping pentru traduceri
        self.translation_pairs = {
            ('ro', 'en'): 'Helsinki-NLP/opus-mt-roa-en',
            ('en', 'ro'): 'Helsinki-NLP/opus-mt-tc-big-en-ro',
            ('ro', 'ja'): 'Helsinki-NLP/opus-mt-tc-big-en-ja',
            ('ro', 'zh'): 'Helsinki-NLP/opus-mt-en-zh',
            ('ro', 'ru'): 'Helsinki-NLP/opus-mt-tc-big-en-ru',
            ('ja', 'ro'): 'Helsinki-NLP/opus-mt-ja-en',
            ('ja', 'zh'): 'Helsinki-NLP/opus-mt-ja-zh',
            ('ja', 'ru'): 'Helsinki-NLP/opus-mt-ja-en',
            ('zh', 'ro'): 'Helsinki-NLP/opus-mt-zh-en',
            ('zh', 'ja'): 'Helsinki-NLP/opus-mt-zh-ja',
            ('zh', 'ru'): 'Helsinki-NLP/opus-mt-zh-en',
            ('ru', 'ro'): 'Helsinki-NLP/opus-mt-ru-en',
            ('ru', 'ja'): 'Helsinki-NLP/opus-mt-ru-en',
            ('ru', 'zh'): 'Helsinki-NLP/opus-mt-ru-zh'
        }
        
    def load_whisper_model(self, model_size: str = "large-v3") -> None:
        """
        Încarcă modelul Whisper pentru transcriere
        
        Args:
            model_size: Dimensiunea modelului (tiny, base, small, medium, large, large-v3)
        """
        print(f"📥 Încărcare model Whisper {model_size}...")
        self.whisper_model = whisper.load_model(model_size, device=self.device)
        print("✅ Model Whisper încărcat cu succes")
        
    def load_vad_model(self) -> None:
        """Încarcă modelul VAD pentru detecție voce"""
        print("📥 Încărcare model VAD...")
        self.vad_model = load_silero_vad()
        print("✅ Model VAD încărcat")
        
    def load_translation_model(self, source_lang: str, target_lang: str) -> None:
        """
        Încarcă modelul de traducere pentru perechea de limbi
        
        Args:
            source_lang: Limba sursă (ro, ja, zh, ru)
            target_lang: Limba țintă (ro, ja, zh, ru)
        """
        pair_key = (source_lang, target_lang)
        if pair_key not in self.translation_pairs:
            print(f"⚠️ Traducere directă {source_lang}->{target_lang} indisponibilă")
            return
            
        model_name = self.translation_pairs[pair_key]
        print(f"📥 Încărcare model traducere {source_lang}->{target_lang}...")
        
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name).to(self.device)
        
        self.translation_models[pair_key] = {
            'tokenizer': tokenizer,
            'model': model
        }
        print("✅ Model traducere încărcat")
        
    def extract_audio(self, video_path: str) -> Tuple[np.ndarray, int]:
        """
        Extrage audio din video
        
        Args:
            video_path: Calea către fișierul video
            
        Returns:
            Tuple cu array audio și sample rate
        """
        print(f"🎵 Extragere audio din {video_path}...")
        
        video = VideoFileClip(video_path)
        temp_audio = "temp_audio.wav"
        video.audio.write_audiofile(temp_audio, verbose=False, logger=None)
        
        # Încarcă audio cu librosa pentru procesare
        audio, sr = librosa.load(temp_audio, sr=16000, mono=True)
        
        # Curăță fișierul temporar
        os.remove(temp_audio)
        video.close()
        
        return audio, sr
        
    def detect_voice_segments(self, audio: np.ndarray, sr: int) -> List[Dict]:
        """
        Detectează segmentele cu voce folosind VAD
        
        Args:
            audio: Array audio
            sr: Sample rate
            
        Returns:
            Listă de segmente detectate
        """
        if self.vad_model is None:
            self.load_vad_model()
            
        print("🎯 Detectare segmente voce...")
        
        # Convertește audio pentru VAD
        if sr != 16000:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
            sr = 16000
            
        # Detectează timestamp-uri voce
        speech_timestamps = get_speech_timestamps(
            audio, 
            self.vad_model,
            sampling_rate=sr,
            threshold=0.5,
            min_speech_duration_ms=250,
            max_speech_duration_s=30,
            min_silence_duration_ms=100
        )
        
        segments = []
        for ts in speech_timestamps:
            segments.append({
                'start': ts['start'] / sr,
                'end': ts['end'] / sr
            })
            
        print(f"✅ Detectate {len(segments)} segmente cu voce")
        return segments
        
    def transcribe_audio(
        self, 
        audio_path: str, 
        source_lang: str,
        use_vad: bool = True,
        enhance_timestamps: bool = True
    ) -> List[SubtitleSegment]:
        """
        Transcrie audio în limba specificată
        
        Args:
            audio_path: Calea către fișierul audio/video
            source_lang: Limba sursă (ro, ja, zh, ru)
            use_vad: Folosește VAD pentru segmentare îmbunătățită
            enhance_timestamps: Îmbunătățește timestamp-urile
            
        Returns:
            Listă de segmente de subtitrare
        """
        print(f"📝 Transcriere audio în {self.supported_languages[source_lang]}...")
        
        # Extrage audio dacă e video
        if audio_path.endswith(('.mp4', '.avi', '.mkv', '.mov')):
            audio, sr = self.extract_audio(audio_path)
            temp_audio = "temp_transcribe.wav"
            sf.write(temp_audio, audio, sr)
            audio_path = temp_audio
        
        # Transcrie cu Whisper
        result = self.whisper_model.transcribe(
            audio_path,
            language=source_lang,
            task="transcribe",
            word_timestamps=True,
            condition_on_previous_text=True,
            temperature=0.0,
            no_speech_threshold=0.6,
            logprob_threshold=-1.0
        )
        
        segments = []
        
        # Procesează segmente
        for segment in result['segments']:
            # Crează segment de subtitrare
            sub_segment = SubtitleSegment(
                start_time=segment['start'],
                end_time=segment['end'],
                text=segment['text'].strip(),
                confidence=segment.get('avg_logprob', 0) if 'avg_logprob' in segment else 1.0
            )
            
            # Adaugă informații despre cuvinte pentru lip sync
            if 'words' in segment:
                sub_segment.words = segment['words']
                
            segments.append(sub_segment)
        
        # Curăță fișier temporar
        if 'temp_transcribe.wav' in audio_path:
            os.remove(audio_path)
            
        print(f"✅ Transcriere completă: {len(segments)} segmente")
        return segments
        
    def calculate_lip_sync_score(
        self, 
        segment: SubtitleSegment, 
        audio_chunk: np.ndarray,
        sr: int = 16000
    ) -> float:
        """
        Calculează scorul de lip sync pentru un segment
        
        Args:
            segment: Segmentul de subtitrare
            audio_chunk: Porțiunea de audio corespunzătoare
            sr: Sample rate
            
        Returns:
            Scor lip sync (0-1)
        """
        # Analiză simplificată bazată pe energie și timing
        energy = np.sqrt(np.mean(audio_chunk**2))
        
        # Detectează vocalele (frecvențe fundamentale)
        if len(audio_chunk) > 0:
            # Analiza spectrală pentru vocale
            fft = np.fft.fft(audio_chunk)
            freqs = np.fft.fftfreq(len(fft), 1/sr)
            
            # Frecvențe vocale tipice (100-400 Hz pentru fundamental)
            vocal_mask = (np.abs(freqs) > 100) & (np.abs(freqs) < 400)
            vocal_energy = np.mean(np.abs(fft[vocal_mask]))
            
            # Calculează scor bazat pe potrivirea energie-text
            text_length = len(segment.text)
            duration = segment.end_time - segment.start_time
            expected_rate = text_length / duration if duration > 0 else 0
            
            # Scor combinat
            score = min(1.0, (vocal_energy / (energy + 1e-6)) * min(1.0, expected_rate / 10))
        else:
            score = 0.0
            
        return score
        
    def enhance_lip_sync(
        self, 
        segments: List[SubtitleSegment],
        audio_path: str
    ) -> List[SubtitleSegment]:
        """
        Îmbunătățește sincronizarea cu buzele
        
        Args:
            segments: Segmente de subtitrare
            audio_path: Calea către audio
            
        Returns:
            Segmente optimizate pentru lip sync
        """
        print("💋 Optimizare lip sync...")
        
        # Încarcă audio complet
        audio, sr = librosa.load(audio_path, sr=16000)
        
        enhanced_segments = []
        
        for segment in tqdm(segments, desc="Procesare segmente"):
            # Extrage porțiunea de audio
            start_sample = int(segment.start_time * sr)
            end_sample = int(segment.end_time * sr)
            audio_chunk = audio[start_sample:end_sample]
            
            # Calculează scor lip sync
            lip_sync_score = self.calculate_lip_sync_score(segment, audio_chunk, sr)
            segment.lip_sync_score = lip_sync_score
            
            # Ajustează timing-ul dacă e necesar
            if lip_sync_score < 0.5 and hasattr(segment, 'words'):
                # Reajustează pe baza cuvintelor individuale
                for word in segment.words:
                    word_start = word['start']
                    word_end = word['end']
                    
                    # Verifică alinierea cu energia audio
                    word_audio = audio[int(word_start*sr):int(word_end*sr)]
                    if len(word_audio) > 0:
                        word_energy = np.sqrt(np.mean(word_audio**2))
                        
                        # Ajustează dacă energia e prea mică
                        if word_energy < 0.01:
                            # Caută următorul peak de energie
                            search_window = audio[int(word_start*sr):int((word_end+0.5)*sr)]
                            if len(search_window) > 0:
                                peak_idx = np.argmax(np.abs(search_window))
                                word['start'] = word_start + peak_idx/sr
                                
            enhanced_segments.append(segment)
            
        print(f"✅ Lip sync optimizat. Scor mediu: {np.mean([s.lip_sync_score for s in enhanced_segments]):.2f}")
        return enhanced_segments
        
    def translate_segments(
        self,
        segments: List[SubtitleSegment],
        source_lang: str,
        target_lang: str,
        batch_size: int = 8
    ) -> List[SubtitleSegment]:
        """
        Traduce segmentele în limba țintă
        
        Args:
            segments: Segmente de tradus
            source_lang: Limba sursă
            target_lang: Limba țintă
            batch_size: Dimensiune batch pentru traducere
            
        Returns:
            Segmente traduse
        """
        if source_lang == target_lang:
            return segments
            
        # Verifică dacă avem model pentru această pereche
        pair_key = (source_lang, target_lang)
        if pair_key not in self.translation_models:
            self.load_translation_model(source_lang, target_lang)
            
        if pair_key not in self.translation_models:
            print(f"⚠️ Nu pot traduce {source_lang}->{target_lang}. Folosesc traducere prin engleză.")
            return self.translate_via_english(segments, source_lang, target_lang)
            
        print(f"🌐 Traducere {source_lang}->{target_lang}...")
        
        model_data = self.translation_models[pair_key]
        tokenizer = model_data['tokenizer']
        model = model_data['model']
        
        translated_segments = []
        
        # Procesează în batch-uri
        for i in tqdm(range(0, len(segments), batch_size), desc="Traducere"):
            batch = segments[i:i+batch_size]
            texts = [seg.text for seg in batch]
            
            # Tokenizare
            inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True).to(self.device)
            
            # Traducere
            with torch.no_grad():
                translated = model.generate(**inputs, max_length=512, num_beams=5)
            
            # Decodare
            translations = tokenizer.batch_decode(translated, skip_special_tokens=True)
            
            # Crează segmente noi
            for seg, trans in zip(batch, translations):
                new_segment = SubtitleSegment(
                    start_time=seg.start_time,
                    end_time=seg.end_time,
                    text=trans,
                    confidence=seg.confidence * 0.9,  # Reducere confidence pentru traduceri
                    lip_sync_score=seg.lip_sync_score
                )
                translated_segments.append(new_segment)
                
        print(f"✅ Traducere completă: {len(translated_segments)} segmente")
        return translated_segments
        
    def translate_via_english(
        self,
        segments: List[SubtitleSegment],
        source_lang: str,
        target_lang: str
    ) -> List[SubtitleSegment]:
        """
        Traduce prin engleză când nu există traducere directă
        
        Args:
            segments: Segmente de tradus
            source_lang: Limba sursă
            target_lang: Limba țintă
            
        Returns:
            Segmente traduse
        """
        print(f"🔄 Traducere prin engleză: {source_lang}->en->{target_lang}")
        
        # Primul pas: traduce în engleză
        if source_lang != 'en':
            segments = self.translate_to_english(segments, source_lang)
            
        # Al doilea pas: traduce din engleză în limba țintă
        if target_lang != 'en':
            segments = self.translate_from_english(segments, target_lang)
            
        return segments
        
    def save_subtitles(
        self,
        segments: List[SubtitleSegment],
        output_path: str,
        format: str = 'srt'
    ) -> None:
        """
        Salvează subtitrările în format specificat
        
        Args:
            segments: Segmente de subtitrare
            output_path: Calea de salvare
            format: Format subtitrare (srt, vtt, ass)
        """
        print(f"💾 Salvare subtitrări în format {format.upper()}...")
        
        if format == 'srt':
            self._save_srt(segments, output_path)
        elif format == 'vtt':
            self._save_vtt(segments, output_path)
        elif format == 'ass':
            self._save_ass(segments, output_path)
        else:
            raise ValueError(f"Format necunoscut: {format}")
            
        print(f"✅ Subtitrări salvate în {output_path}")
        
    def _save_srt(self, segments: List[SubtitleSegment], output_path: str) -> None:
        """Salvează în format SRT"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, 1):
                # Index
                f.write(f"{i}\n")
                
                # Timecode
                start = self._seconds_to_srt_time(segment.start_time)
                end = self._seconds_to_srt_time(segment.end_time)
                f.write(f"{start} --> {end}\n")
                
                # Text
                f.write(f"{segment.text}\n")
                
                # Linie goală între subtitrări
                f.write("\n")
                
    def _save_vtt(self, segments: List[SubtitleSegment], output_path: str) -> None:
        """Salvează în format WebVTT"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            
            for segment in segments:
                start = self._seconds_to_vtt_time(segment.start_time)
                end = self._seconds_to_vtt_time(segment.end_time)
                f.write(f"{start} --> {end}\n")
                f.write(f"{segment.text}\n\n")
                
    def _save_ass(self, segments: List[SubtitleSegment], output_path: str) -> None:
        """Salvează în format ASS (Advanced SubStation)"""
        with open(output_path, 'w', encoding='utf-8') as f:
            # Header ASS
            f.write("[Script Info]\n")
            f.write("Title: Generated Subtitles\n")
            f.write("ScriptType: v4.00+\n")
            f.write("Collisions: Normal\n")
            f.write("PlayDepth: 0\n\n")
            
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, ")
            f.write("OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ")
            f.write("ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, ")
            f.write("Alignment, MarginL, MarginR, MarginV, Encoding\n")
            f.write("Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,")
            f.write("0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1\n\n")
            
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            
            for segment in segments:
                start = self._seconds_to_ass_time(segment.start_time)
                end = self._seconds_to_ass_time(segment.end_time)
                f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{segment.text}\n")
                
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convertește secunde în format SRT"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
        
    def _seconds_to_vtt_time(self, seconds: float) -> str:
        """Convertește secunde în format WebVTT"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
        
    def _seconds_to_ass_time(self, seconds: float) -> str:
        """Convertește secunde în format ASS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int((seconds % 1) * 100)
        return f"{hours:01d}:{minutes:02d}:{secs:02d}.{centis:02d}"
        
    def process_video(
        self,
        video_path: str,
        source_lang: str,
        target_lang: str,
        output_dir: str = "output",
        subtitle_format: str = 'srt',
        enable_lip_sync: bool = True,
        model_size: str = 'large-v3'
    ) -> Dict:
        """
        Procesează complet un video
        
        Args:
            video_path: Calea către video
            source_lang: Limba sursă
            target_lang: Limba țintă
            output_dir: Director pentru output
            subtitle_format: Format subtitrare
            enable_lip_sync: Activează optimizare lip sync
            model_size: Dimensiune model Whisper
            
        Returns:
            Dicționar cu informații despre procesare
        """
        start_time = time.time()
        
        print(f"\n🎬 Procesare video: {video_path}")
        print(f"📤 Limba sursă: {self.supported_languages[source_lang]}")
        print(f"📥 Limba țintă: {self.supported_languages[target_lang]}")
        print("-" * 50)
        
        # Crează director output
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 1. Încarcă modelele necesare
        if not hasattr(self, 'whisper_model'):
            self.load_whisper_model(model_size)
            
        # 2. Transcrie audio
        segments = self.transcribe_audio(video_path, source_lang)
        
        # 3. Optimizare lip sync dacă e activată
        if enable_lip_sync:
            segments = self.enhance_lip_sync(segments, video_path)
            
        # 4. Traduce dacă e necesar
        if source_lang != target_lang:
            segments = self.translate_segments(segments, source_lang, target_lang)
            
        # 5. Salvează subtitrările
        video_name = Path(video_path).stem
        subtitle_file = f"{output_dir}/{video_name}_{source_lang}_to_{target_lang}.{subtitle_format}"
        self.save_subtitles(segments, subtitle_file, subtitle_format)
        
        # 6. Generează raport
        processing_time = time.time() - start_time
        report = {
            'video': video_path,
            'source_language': source_lang,
            'target_language': target_lang,
            'total_segments': len(segments),
            'processing_time': f"{processing_time:.2f} seconds",
            'average_confidence': np.mean([s.confidence for s in segments]),
            'average_lip_sync_score': np.mean([s.lip_sync_score for s in segments]) if enable_lip_sync else None,
            'output_file': subtitle_file
        }
        
        # Salvează raport JSON
        report_file = f"{output_dir}/{video_name}_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        print(f"\n✅ Procesare completă în {processing_time:.2f} secunde")
        print(f"📊 Raport salvat în: {report_file}")
        
        return report


class BatchProcessor:
    """Procesor pentru mai multe videoclipuri"""
    
    def __init__(self, system: AdvancedSubtitleSystem):
        self.system = system
        
    def process_directory(
        self,
        input_dir: str,
        source_lang: str,
        target_lang: str,
        output_dir: str = "batch_output",
        extensions: List[str] = ['.mp4', '.avi', '.mkv', '.mov']
    ) -> List[Dict]:
        """
        Procesează toate videoclipurile dintr-un director
        
        Args:
            input_dir: Director cu videoclipuri
            source_lang: Limba sursă
            target_lang: Limba țintă  
            output_dir: Director output
            extensions: Extensii acceptate
            
        Returns:
            Listă cu rapoarte pentru fiecare video
        """
        print(f"\n📁 Procesare batch pentru directorul: {input_dir}")
        
        # Găsește toate videoclipurile
        video_files = []
        for ext in extensions:
            video_files.extend(Path(input_dir).glob(f"*{ext}"))
            
        print(f"📹 Găsite {len(video_files)} videoclipuri")
        
        reports = []
        for i, video_file in enumerate(video_files, 1):
            print(f"\n[{i}/{len(video_files)}] Procesare: {video_file.name}")
            
            try:
                report = self.system.process_video(
                    str(video_file),
                    source_lang,
                    target_lang,
                    output_dir
                )
                reports.append(report)
            except Exception as e:
                print(f"❌ Eroare la procesarea {video_file.name}: {e}")
                reports.append({
                    'video': str(video_file),
                    'error': str(e)
                })
                
        # Salvează raport complet
        batch_report_file = f"{output_dir}/batch_report.json"
        with open(batch_report_file, 'w', encoding='utf-8') as f:
            json.dump(reports, f, indent=2, ensure_ascii=False)
            
        print(f"\n✅ Procesare batch completă")
        print(f"📊 Raport salvat în: {batch_report_file}")
        
        return reports


def main():
    """Funcție principală pentru CLI"""
    parser = argparse.ArgumentParser(description="Sistem avansat de subtitrare multilingvă")
    
    parser.add_argument('input', help='Video sau director cu videoclipuri')
    parser.add_argument('source_lang', choices=['ro', 'ja', 'zh', 'ru', 'en'], 
                       help='Limba sursă')
    parser.add_argument('target_lang', choices=['ro', 'ja', 'zh', 'ru', 'en'],
                       help='Limba țintă')
    
    parser.add_argument('--output', default='output', help='Director output')
    parser.add_argument('--format', default='srt', choices=['srt', 'vtt', 'ass'],
                       help='Format subtitrare')
    parser.add_argument('--model', default='large-v3', 
                       choices=['tiny', 'base', 'small', 'medium', 'large', 'large-v3'],
                       help='Dimensiune model Whisper')
    parser.add_argument('--no-lip-sync', action='store_true',
                       help='Dezactivează optimizarea lip sync')
    parser.add_argument('--batch', action='store_true',
                       help='Procesare batch pentru director')
    parser.add_argument('--gpu', action='store_true',
                       help='Folosește GPU dacă e disponibil')
    
    args = parser.parse_args()
    
    # Inițializare sistem
    system = AdvancedSubtitleSystem(use_gpu=args.gpu)
    
    # Procesare
    if args.batch:
        if not os.path.isdir(args.input):
            print(f"❌ Eroare: {args.input} nu este un director valid")
            sys.exit(1)
            
        processor = BatchProcessor(system)
        processor.process_directory(
            args.input,
            args.source_lang,
            args.target_lang,
            args.output
        )
    else:
        if not os.path.isfile(args.input):
            print(f"❌ Eroare: {args.input} nu este un fișier valid")
            sys.exit(1)
            
        system.process_video(
            args.input,
            args.source_lang,
            args.target_lang,
            args.output,
            args.format,
            enable_lip_sync=not args.no_lip_sync
        )


if __name__ == "__main__":
    main()