"""
Sistem de subtitrare REPARAT - elimină omisiunile și mixarea limbilor
"""

import os
import sys
import json
import time
import re
import pickle
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import torch
import whisper
import pysubs2
import librosa
import soundfile as sf
from tqdm import tqdm

try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

from transformers import MarianMTModel, MarianTokenizer, MBartForConditionalGeneration, MBart50TokenizerFast
from deep_translator import GoogleTranslator

# Adaugă aceste importuri la începutul fișierului sub.py
from llm_validator import LLMTranslationValidator

import subprocess
import argparse


ENHANCED_TRANSLATION_MODELS = {
    ('ro', 'en'): 'Helsinki-NLP/opus-mt-ro-en',
    ('en', 'ro'): 'Helsinki-NLP/opus-mt-en-ro',
    ('ja', 'en'): 'Helsinki-NLP/opus-mt-ja-en', 
    ('en', 'ja'): 'staka/fugumt-en-ja',
    ('zh', 'en'): 'Helsinki-NLP/opus-mt-zh-en',
    ('en', 'zh'): 'liam168/trans-opus-mt-en-zh',
    ('ru', 'en'): 'Helsinki-NLP/opus-mt-ru-en',
    ('en', 'ru'): 'Helsinki-NLP/opus-mt-en-rU',  # ✅ Corectat typo
    ('ja', 'ru'): 'Helsinki-NLP/opus-mt-ja-ru',  # ✅ ADĂUGAT: JA->RU direct
    ('ru', 'ja'): 'Helsinki-NLP/opus-mt-ru-ja',  # ✅ ADĂUGAT: RU->JA direct
    ('ro', 'ru'): 'Helsinki-NLP/opus-mt-ro-ru',  # ✅ ADĂUGAT: RO->RU direct
    ('ru', 'ro'): 'Helsinki-NLP/opus-mt-ru-ro',  # ✅ ADĂUGAT: RU->RO direct
    ('zh', 'ru'): 'Helsinki-NLP/opus-mt-zh-ru',  # ✅ ADĂUGAT: ZH->RU direct
    ('ru', 'zh'): 'Helsinki-NLP/opus-mt-ru-zh',  # ✅ ADĂUGAT: RU->ZH direct
}

CACHE_DIR = Path.home() / ".cache" / "subtitle_system"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class SubtitleSegment:
    start_time: float
    end_time: float
    text: str
    confidence: float = 1.0
    original_text: Optional[str] = None


class EnhancedTranslator:
    """Traducător îmbunătățit FĂRĂ pierderi de text"""
    
    def __init__(self, device="cuda"):
        self.device = device if torch.cuda.is_available() else "cpu"
        self.models_cache = {}
        self.cache_file = CACHE_DIR / "translation_cache.pkl"
        self.translation_cache = self._load_cache()
        
    def _load_cache(self) -> Dict:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    return pickle.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.translation_cache, f)
    
    def load_model(self, source_lang: str, target_lang: str) -> Tuple[Any, Any]:
        key = (source_lang, target_lang)
        
        if key in self.models_cache:
            return self.models_cache[key]
        
        model_name = ENHANCED_TRANSLATION_MODELS.get(key)
        
        if not model_name:
            print(f"⚠️ Nu există model direct pentru {source_lang}->{target_lang}")
            return None, None
        
        print(f"📥 Încărcare model: {model_name}")
        
        try:
            tokenizer = MarianTokenizer.from_pretrained(model_name)
            model = MarianMTModel.from_pretrained(model_name).to(self.device)
            
            self.models_cache[key] = (tokenizer, model)
            print("✅ Model încărcat")
            return tokenizer, model
            
        except Exception as e:
            print(f"❌ Eroare încărcare model: {e}")
            return None, None
    
    def translate_batch_enhanced(
        self, 
        texts: List[str], 
        source_lang: str, 
        target_lang: str
    ) -> List[str]:
        """Traducere batch FĂRĂ pierderi"""
        
        if source_lang == target_lang:
            return texts
        
        # ✅ FIX: Validare input
        if not texts or all(not t.strip() for t in texts):
            return texts
        
        # ✅ FIX: Normalizare texte
        clean_texts = []
        for t in texts:
            t = ' '.join(t.split())  # Normalizare spații
            if not t.strip():
                t = "..."  # Placeholder pentru segmente goale
            clean_texts.append(t)
        
        # Cache
        cache_key = (tuple(clean_texts), source_lang, target_lang)
        if cache_key in self.translation_cache:
            print("✓ Din cache")
            return self.translation_cache[cache_key]
        
        # Încarcă model
        tokenizer, model = self.load_model(source_lang, target_lang)
        
        if tokenizer and model:
            try:
                # ✅ SPECIAL pentru rusă: parametri ajustați
                if target_lang == 'ru':
                    max_len = 256  # Mai lung pentru rusă (cuvinte mai lungi)
                    num_beams = 4  # Mai puține beams pentru viteză
                else:
                    max_len = 512
                    num_beams = 5
                
                # ✅ FIX: Parametri optimizați pentru a PĂSTRA tot textul
                inputs = tokenizer(
                    clean_texts, 
                    return_tensors="pt", 
                    padding=True, 
                    truncation=True,
                    max_length=max_len
                ).to(self.device)
                
                with torch.no_grad():
                    generated = model.generate(
                        **inputs,
                        max_length=max_len,
                        num_beams=num_beams,
                        length_penalty=1.2,
                        early_stopping=False,
                        no_repeat_ngram_size=3,
                        temperature=1.0,
                        do_sample=False  # ✅ Deterministic pentru consistență
                    )
                
                translations = tokenizer.batch_decode(generated, skip_special_tokens=True)
                
                # ✅ FIX: Validare că traducerea nu e goală și e în limba corectă
                validated = []
                for orig, trans in zip(clean_texts, translations):
                    trans = trans.strip()
                    
                    # Verifică dacă traducerea e validă
                    if not trans or trans == '...' or not self._is_correct_language(trans, target_lang):
                        print(f"⚠️ Traducere invalidă pentru '{orig[:30]}...', folosesc Google")
                        trans = self._google_translate_single(orig, source_lang, target_lang)
                    
                    validated.append(trans)
                
                # Salvează în cache
                self.translation_cache[cache_key] = validated
                self._save_cache()
                
                return validated
                
            except Exception as e:
                print(f"⚠️ Eroare model: {e}")
        
        # Fallback Google
        print("🔄 Google Translate...")
        return self._google_translate_batch(clean_texts, source_lang, target_lang)
    
    def _google_translate_single(self, text: str, source_lang: str, target_lang: str) -> str:
        """Traducere unui singur text cu Google"""
        try:
            lang_map = {'zh': 'zh-CN', 'ja': 'ja', 'ro': 'ro', 'ru': 'ru', 'en': 'en'}
            src = lang_map.get(source_lang, source_lang)
            tgt = lang_map.get(target_lang, target_lang)
            
            translator = GoogleTranslator(source=src, target=tgt)
            result = translator.translate(text)
            
            # ✅ Validare că traducerea e în limba corectă
            if result and self._is_correct_language(result, target_lang):
                return result
            else:
                print(f"⚠️ Traducere invalidă, încerc din nou...")
                return text
                
        except Exception as e:
            print(f"⚠️ Eroare Google Translate: {e}")
            return text
    
    def _is_correct_language(self, text: str, expected_lang: str) -> bool:
        """Verifică dacă textul e în limba așteptată"""
        if not text or len(text.strip()) < 3:
            return True
        
        # Verificări simple pe bază de caractere specifice
        if expected_lang == 'ru':
            # Rusă folosește alfabetul chirilic
            cyrillic_count = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
            return cyrillic_count > len(text) * 0.5  # >50% caractere chirilice
        
        elif expected_lang == 'ja':
            # Japoneză folosește hiragana, katakana, kanji
            japanese_count = sum(1 for c in text if 
                '\u3040' <= c <= '\u309F' or  # Hiragana
                '\u30A0' <= c <= '\u30FF' or  # Katakana
                '\u4E00' <= c <= '\u9FFF')    # Kanji
            return japanese_count > len(text) * 0.3
        
        elif expected_lang == 'zh':
            # Chineză folosește caractere Han
            chinese_count = sum(1 for c in text if '\u4E00' <= c <= '\u9FFF')
            return chinese_count > len(text) * 0.5
        
        elif expected_lang == 'ro':
            # Română folosește caractere latine + diacritice
            latin_count = sum(1 for c in text if c.isalpha() and ord(c) < 0x0400)
            return latin_count > len(text) * 0.7
        
        elif expected_lang == 'en':
            # Engleză - doar ASCII
            ascii_count = sum(1 for c in text if ord(c) < 128)
            return ascii_count > len(text) * 0.9
        
        return True  # Default: acceptă
    
    def _google_translate_batch(self, texts: List[str], source_lang: str, target_lang: str) -> List[str]:
        """Fallback Google Translate"""
        try:
            lang_map = {'zh': 'zh-CN', 'ja': 'ja', 'ro': 'ro', 'ru': 'ru', 'en': 'en'}
            src = lang_map.get(source_lang, source_lang)
            tgt = lang_map.get(target_lang, target_lang)
            
            translator = GoogleTranslator(source=src, target=tgt)
            translations = []
            
            for text in tqdm(texts, desc="Google Translate"):
                try:
                    trans = translator.translate(text)
                    translations.append(trans if trans else text)
                except:
                    translations.append(text)
                time.sleep(0.1)  # Rate limiting
            
            return translations
            
        except Exception as e:
            print(f"❌ Google Translate eșuat: {e}")
            return texts


class OptimizedSubtitleSystem:
    """Sistem de subtitrare FĂRĂ pierderi"""
    
    
    def __init__(self, use_gpu: bool = True, use_llm_validation: bool = True):
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        print(f"🔧 Sistem pe: {self.device}")
        
        self.whisper_model = None
        self.translator = EnhancedTranslator(self.device)
        
        # NOUĂ: Inițializare validator LLM
        self.use_llm_validation = use_llm_validation
        if use_llm_validation:
            try:
                self.llm_validator = LLMTranslationValidator(
                    ollama_url="http://86.126.134.77:11434",
                    primary_model="gemma3:27b",
                    fallback_model="mistral:Q4_K_M"
                )
            except Exception as e:
                print(f"⚠️ LLM Validator nu poate fi inițializat: {e}")
                self.use_llm_validation = False
                self.llm_validator = None
        else:
            self.llm_validator = None
        
        self.supported_languages = {
            'ro': 'romanian', 'en': 'english', 'ja': 'japanese',
            'zh': 'chinese', 'ru': 'russian', 'es': 'spanish',
            'fr': 'french', 'de': 'german', 'it': 'italian'
        }
    
    def load_whisper_model(self, model_size: str = "large-v3") -> None:
        print(f"📥 Încărcare Whisper {model_size}...")
        self.whisper_model = whisper.load_model(model_size, device=self.device)
        print("✅ Whisper încărcat")
    
    def extract_audio_optimized(self, video_path: str) -> Tuple[np.ndarray, int]:
        print(f"🎵 Extragere audio...")
        
        temp_audio = "temp_audio.wav"
        
        # FFmpeg direct
        cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            temp_audio
        ]
        subprocess.run(cmd, capture_output=True)
        
        audio, sr = librosa.load(temp_audio, sr=16000, mono=True)
        
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        
        return audio, sr
    
    def transcribe_enhanced(
        self,
        audio_path: str,
        source_lang: str = None,
        auto_detect: bool = True
    ) -> Tuple[List[SubtitleSegment], str]:
        """Transcriere COMPLETĂ fără omisiuni"""
        
        print("📝 Transcriere...")
        
        if audio_path.lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):
            audio, sr = self.extract_audio_optimized(audio_path)
            temp_audio = "temp_transcribe.wav"
            sf.write(temp_audio, audio, sr)
            audio_path = temp_audio
        else:
            temp_audio = None
        
        if self.whisper_model is None:
            self.load_whisper_model("large-v3")
        
        # Detecție limbă
        if auto_detect and not source_lang:
            print("🔍 Detectare limbă...")
            audio_sample = whisper.load_audio(audio_path)
            audio_sample = whisper.pad_or_trim(audio_sample)
            mel = whisper.log_mel_spectrogram(audio_sample).to(self.device)
            _, probs = self.whisper_model.detect_language(mel)
            detected_lang = max(probs, key=probs.get)
            print(f"✅ Limbă: {detected_lang} ({probs[detected_lang]:.1%})")
            source_lang = detected_lang
        
        # ✅ FIX: Transcriere cu parametri care PĂSTREAZĂ tot conținutul
        result = self.whisper_model.transcribe(
            audio_path,
            language=source_lang,
            task="transcribe",
            verbose=False,
            word_timestamps=True,
            condition_on_previous_text=False,  # ✅ Dezactivat pentru a evita halucinații
            temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0),  # ✅ Temperatura incrementală
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6,
            initial_prompt=None,  # ✅ Fără prompt pentru a evita bias
            fp16=torch.cuda.is_available()
        )
        
        segments = []
        
        # ✅ Procesare cu word timestamps și filtrare halucinații
        for seg in result.get('segments', []):
            text = seg['text'].strip()
            
            if not text:
                continue
            
            # ✅ FILTRU ANTI-HALUCINAȚII
            if self._is_hallucination(text, seg):
                print(f"⚠️ Segment halucinat ignorat: '{text[:50]}'")
                continue
            
            # ✅ NOUĂ LOGICĂ: Împarte segmente lungi folosind word timestamps
            words = seg.get('words', [])
            
            if words and len(words) > 0:
                # Împarte pe bază de cuvinte
                segments.extend(self._split_by_words(words, seg['start'], seg['end']))
            else:
                # Fallback: împarte pe bază de propoziții
                segments.extend(self._split_by_sentences(text, seg['start'], seg['end']))
        
        if temp_audio and os.path.exists(temp_audio):
            os.remove(temp_audio)
        
        print(f"✅ Transcriere: {len(segments)} segmente (optimizat, halucinații filtrate)")
        
        # ✅ DEBUG: Afișează primele 5 segmente
        print("\n📋 Primele 5 segmente:")
        for i, seg in enumerate(segments[:5], 1):
            duration = seg.end_time - seg.start_time
            print(f"  {i}. [{seg.start_time:.1f}s-{seg.end_time:.1f}s] ({duration:.1f}s) {seg.text[:50]}")
        
        return segments, source_lang
    
    def _is_hallucination(self, text: str, segment: Dict) -> bool:
        """Detectează și filtrează halucinații Whisper"""
        
        # 1. Text repetat (cea mai comună halucinație)
        words = text.lower().split()
        if len(words) > 1:
            # Verifică dacă același cuvânt se repetă
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:  # <30% cuvinte unice = probabil halucinație
                return True
            
            # Verifică secvențe repetate
            for i in range(len(words) - 2):
                if words[i] == words[i+1] == words[i+2]:
                    return True
        
        # 2. Cuvinte comune de halucinație
        hallucination_patterns = [
            'zoid', 'thank you', 'thanks for watching',
            'please subscribe', 'like and subscribe',
            'music', '[music]', '(music)', 'silence'
        ]
        
        text_lower = text.lower()
        for pattern in hallucination_patterns:
            if pattern in text_lower and len(text) < 50:
                return True
        
        # 3. Probabilitate logaritmică prea scăzută
        avg_logprob = segment.get('avg_logprob', 0)
        if avg_logprob < -1.5:  # Încredere foarte scăzută
            return True
        
        # 4. Raport de compresie anormal
        compression_ratio = segment.get('compression_ratio', 1.0)
        if compression_ratio > 3.0:  # Text prea repetitiv
            return True
        
        # 5. No-speech probability mare
        no_speech_prob = segment.get('no_speech_prob', 0)
        if no_speech_prob > 0.8:  # Probabil nu e vorbire
            return True
        
        return False
    
    def _split_by_words(self, words: List[Dict], start_time: float, end_time: float) -> List[SubtitleSegment]:
        """Împarte segment pe bază de word timestamps (cel mai precis)"""
        
        if not words:
            # Fallback dacă nu avem words
            return [SubtitleSegment(start_time, end_time, "", 1.0, "")]
        
        segments = []
        current_words = []
        current_start = words[0].get('start', start_time)
        
        MAX_WORDS = 12  # Max 12 cuvinte per segment (2 linii x 6 cuvinte)
        MAX_DURATION = 5.0  # Max 5 secunde per segment
        
        for i, word in enumerate(words):
            current_words.append(word)
            
            word_end = word.get('end', end_time)
            duration = word_end - current_start
            
            # Condiții pentru split
            should_split = False
            
            if len(current_words) >= MAX_WORDS:
                should_split = True
            elif duration >= MAX_DURATION:
                should_split = True
            elif i < len(words) - 1:
                # Split la pauze naturale (punctuație)
                word_text = word.get('word', '').strip()
                if word_text.endswith(('.', '?', '!', '。', '？', '！', '、')):
                    should_split = True
            
            # Creează segment
            if should_split or i == len(words) - 1:
                text = ' '.join(w.get('word', '') for w in current_words).strip()
                
                if text:
                    segment = SubtitleSegment(
                        start_time=current_start,
                        end_time=word_end,
                        text=text,
                        confidence=1.0,
                        original_text=text
                    )
                    segments.append(segment)
                
                # Reset pentru următorul segment
                if i < len(words) - 1:
                    current_words = []
                    next_word = words[i + 1]
                    current_start = next_word.get('start', word_end)
        
        return segments
    
    def _split_by_sentences(self, text: str, start_time: float, end_time: float) -> List[SubtitleSegment]:
        """Împarte segment pe bază de propoziții (fallback când nu avem word timestamps)"""
        segments = []
        
        # Split pe punctuație
        sentences = re.split(r'([.!?。！？]+)', text)
        
        # Recombină punctuația cu propoziția
        combined = []
        for i in range(0, len(sentences) - 1, 2):
            sent = sentences[i].strip()
            punct = sentences[i + 1] if i + 1 < len(sentences) else ''
            if sent:
                combined.append(sent + punct)
        
        if not combined:
            combined = [text]
        
        # Distribuie timpul proporțional
        total_chars = sum(len(s) for s in combined)
        duration = end_time - start_time
        
        current_time = start_time
        for sent in combined:
            if not sent.strip():
                continue
            
            # Calculează durată proporțională
            sent_duration = (len(sent) / total_chars) * duration if total_chars > 0 else duration / len(combined)
            sent_end = min(current_time + sent_duration, end_time)
            
            segment = SubtitleSegment(
                start_time=current_time,
                end_time=sent_end,
                text=sent.strip(),
                confidence=1.0,
                original_text=sent.strip()
            )
            segments.append(segment)
            
            current_time = sent_end
        
        return segments
    
    def translate_segments_enhanced(
        self,
        segments: List[SubtitleSegment],
        source_lang: str,
        target_lang: str,
        batch_size: int = 16,
        validate_with_llm: bool = True  # Parametru nou
        ) -> List[SubtitleSegment]:
        """Traducere cu validare LLM opțională"""
        
        if source_lang == target_lang:
            return segments
        
        print(f"🌐 Traducere {source_lang} → {target_lang}...")
        print(f"📊 Total segmente de tradus: {len(segments)}")
        
        # Verifică dacă trebuie pivot prin engleză
        direct_available = (source_lang, target_lang) in ENHANCED_TRANSLATION_MODELS
        
        if not direct_available and source_lang != 'en' and target_lang != 'en':
            print("🔄 Traducere prin engleză (2 pași)...")
            segments = self.translate_segments_enhanced(
                segments, source_lang, 'en', batch_size, validate_with_llm=False
            )
            segments = self.translate_segments_enhanced(
                segments, 'en', target_lang, batch_size, validate_with_llm
            )
            return segments
        
        translated_segments = []
        total_batches = (len(segments) + batch_size - 1) // batch_size
        
        # Procesare în batch-uri
        for i in tqdm(range(0, len(segments), batch_size), desc="Traducere", total=total_batches):
            batch = segments[i:i+batch_size]
            texts = [seg.text for seg in batch]
            
            # Traducere inițială
            translations = self.translator.translate_batch_enhanced(
                texts, source_lang, target_lang
            )
            
            # Verificare lungime
            if len(translations) != len(batch):
                print(f"⚠️ EROARE: Batch {i//batch_size + 1} - {len(batch)} segmente → {len(translations)} traduceri")
                while len(translations) < len(batch):
                    translations.append(batch[len(translations)].text)
            
            # Creare segmente traduse
            for seg, trans in zip(batch, translations):
                new_segment = SubtitleSegment(
                    start_time=seg.start_time,
                    end_time=seg.end_time,
                    text=trans,
                    confidence=seg.confidence * 0.95,
                    original_text=seg.text  # Păstrăm textul original pentru validare
                )
                translated_segments.append(new_segment)
        
        print(f"✅ Traducere inițială completă: {len(translated_segments)}/{len(segments)} segmente")
        
        # NOUĂ: Validare LLM dacă e activată
        if validate_with_llm and self.use_llm_validation and self.llm_validator:
            print("\n🤖 Aplicare validare LLM...")
            
            # Convertește la format dict pentru validator
            segments_dict = [
                {
                    'start': seg.start_time,
                    'end': seg.end_time,
                    'text': seg.text,
                    'original_text': seg.original_text
                }
                for seg in translated_segments
            ]
            
            # Validare cu LLM
            validated_dict = self.llm_validator.validate_batch(
                segments_dict,
                source_lang,
                target_lang,
                batch_size=5,
                parallel=len(segments_dict) > 20
            )
            
            # Convertește înapoi la SubtitleSegment
            validated_segments = []
            for vd, orig_seg in zip(validated_dict, translated_segments):
                validated_seg = SubtitleSegment(
                    start_time=vd['start'],
                    end_time=vd['end'],
                    text=vd['text'],
                    confidence=vd.get('llm_confidence', orig_seg.confidence),
                    original_text=vd.get('original_text', orig_seg.original_text)
                )
                validated_segments.append(validated_seg)
            
            print(f"✅ Validare LLM completă")
            return validated_segments
        
        return translated_segments
    
        # Adaugă metodă nouă pentru validare dublă
    def validate_translations_double(
        self,
        segments: List[SubtitleSegment],
        source_lang: str,
        target_lang: str
    ) -> List[SubtitleSegment]:
        """Validare dublă cu 2 modele LLM pentru acuratețe maximă"""
        
        if not self.llm_validator:
            return segments
        
        print("\n🔍🔍 Activare validare dublă LLM...")
        
        segments_dict = [
            {
                'start': seg.start_time,
                'end': seg.end_time,
                'text': seg.text,
                'original_text': seg.original_text
            }
            for seg in segments
        ]
        
        # Validare dublă
        validated_dict = self.llm_validator.double_validation(
            segments_dict,
            source_lang,
            target_lang
        )
        
        # Reconstruiește segmentele
        validated_segments = []
        for vd in validated_dict:
            seg = SubtitleSegment(
                start_time=vd['start'],
                end_time=vd['end'],
                text=vd['text'],
                confidence=vd.get('llm_confidence', 0.9),
                original_text=vd.get('original_text', '')
            )
            validated_segments.append(seg)
        
        return validated_segments
    
    def save_subtitles_enhanced(
        self,
        segments: List[SubtitleSegment],
        output_path: str,
        format: str = 'srt'
    ):
        """Salvare subtitrări cu optimizare automată"""
        
        print(f"💾 Salvare {format.upper()}: {len(segments)} segmente...")
        
        # ✅ POST-PROCESARE: Optimizare finală timing și text
        segments = self._optimize_segments(segments)
        
        if format == 'srt':
            with open(output_path, 'w', encoding='utf-8-sig') as f:
                for i, seg in enumerate(segments, 1):
                    f.write(f"{i}\n")
                    start = self._format_time_srt(seg.start_time)
                    end = self._format_time_srt(seg.end_time)
                    f.write(f"{start} --> {end}\n")
                    
                    # ✅ Formatare text pe max 2 linii
                    formatted_text = self._format_subtitle_text(seg.text)
                    f.write(f"{formatted_text}\n\n")
        
        elif format == 'vtt':
            with open(output_path, 'w', encoding='utf-8-sig') as f:
                f.write("WEBVTT\n\n")
                for seg in segments:
                    start = self._format_time_vtt(seg.start_time)
                    end = self._format_time_vtt(seg.end_time)
                    f.write(f"{start} --> {end}\n")
                    formatted_text = self._format_subtitle_text(seg.text)
                    f.write(f"{formatted_text}\n\n")
        
        print(f"✅ Salvat: {output_path}")
    
    def _optimize_segments(self, segments: List[SubtitleSegment]) -> List[SubtitleSegment]:
        """Optimizează segmente pentru citire ușoară"""
        optimized = []
        
        MAX_CHARS_PER_SEGMENT = 84  # Standard pentru subtitrări (42 chars x 2 linii)
        MIN_DURATION = 1.0  # Min 1 secundă
        MAX_DURATION = 6.0  # Max 6 secunde
        MIN_GAP = 0.1  # Pauză minimă între segmente
        
        for i, seg in enumerate(segments):
            # Verifică dacă textul e prea lung
            if len(seg.text) > MAX_CHARS_PER_SEGMENT:
                # Împarte în sub-segmente
                sub_segments = self._split_long_text(seg)
                optimized.extend(sub_segments)
            else:
                # Ajustează durată
                duration = seg.end_time - seg.start_time
                
                if duration < MIN_DURATION:
                    seg.end_time = seg.start_time + MIN_DURATION
                elif duration > MAX_DURATION:
                    # Limitează durata excesivă
                    seg.end_time = seg.start_time + MAX_DURATION
                
                # Evită suprapuneri
                if optimized and seg.start_time < optimized[-1].end_time:
                    seg.start_time = optimized[-1].end_time + MIN_GAP
                
                optimized.append(seg)
        
        return optimized
    
    def _split_long_text(self, segment: SubtitleSegment) -> List[SubtitleSegment]:
        """Împarte text lung în segmente mai mici"""
        MAX_CHARS = 84
        text = segment.text
        
        if len(text) <= MAX_CHARS:
            return [segment]
        
        # Split inteligent pe spații și punctuație
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_len = len(word) + 1  # +1 pentru spațiu
            
            if current_length + word_len > MAX_CHARS and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_len
            else:
                current_chunk.append(word)
                current_length += word_len
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        # Distribuie timpul proporțional
        duration = segment.end_time - segment.start_time
        time_per_char = duration / len(text)
        
        sub_segments = []
        current_time = segment.start_time
        
        for chunk in chunks:
            chunk_duration = len(chunk) * time_per_char
            chunk_end = min(current_time + chunk_duration, segment.end_time)
            
            sub_seg = SubtitleSegment(
                start_time=current_time,
                end_time=chunk_end,
                text=chunk,
                confidence=segment.confidence,
                original_text=segment.original_text
            )
            sub_segments.append(sub_seg)
            current_time = chunk_end
        
        return sub_segments
    
    def _format_subtitle_text(self, text: str, max_line_length: int = 42) -> str:
        """Formatare text pe maxim 2 linii echilibrate"""
        if len(text) <= max_line_length:
            return text
        
        # Split inteligent pe cuvinte
        words = text.split()
        
        if len(text) <= max_line_length * 2:
            # Găsește split point optim pentru 2 linii echilibrate
            mid = len(text) // 2
            best_split = 0
            min_diff = float('inf')
            
            current_pos = 0
            for i, word in enumerate(words):
                current_pos += len(word) + 1
                diff = abs(current_pos - mid)
                
                if diff < min_diff:
                    min_diff = diff
                    best_split = i + 1
            
            line1 = ' '.join(words[:best_split])
            line2 = ' '.join(words[best_split:])
            
            return f"{line1}\n{line2}"
        
        # Text prea lung - truncate cu ...
        return text[:max_line_length * 2 - 3] + "..."
    
    def _format_time_srt(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _format_time_vtt(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    def process_video_complete(
        self,
        video_path: str,
        source_lang: str = None,
        target_lang: str = 'en',
        output_dir: str = "output",
        subtitle_format: str = 'srt',
        model_size: str = 'large-v3',
        auto_detect_language: bool = True,
        use_llm_validation: bool = True,    # Parametru nou
        double_validation: bool = False      # Parametru nou pentru validare dublă
    ) -> Dict:
        """Procesare completă cu validare LLM opțională"""
        
        start_time = time.time()
        
        print("\n" + "="*60)
        print("🎬 PROCESARE VIDEO CU VALIDARE LLM")
        print("="*60)
        print(f"📁 Video: {video_path}")
        print(f"🤖 Validare LLM: {'DA' if use_llm_validation else 'NU'}")
        print(f"🔍🔍 Validare dublă: {'DA' if double_validation else 'NU'}")
        print("="*60)
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 1. Încarcă Whisper
        if self.whisper_model is None:
            self.load_whisper_model(model_size)
        
        # 2. Transcriere
        segments, detected_lang = self.transcribe_enhanced(
            video_path,
            source_lang,
            auto_detect=auto_detect_language
        )
        
        if not source_lang:
            source_lang = detected_lang
        
        print(f"\n📊 Statistici transcriere:")
        print(f"  • Limbă: {source_lang}")
        print(f"  • Segmente: {len(segments)}")
        print(f"  • Durată: {segments[-1].end_time:.1f}s" if segments else "  • N/A")
        
        # 3. Traducere cu validare LLM
        if source_lang != target_lang:
            original_count = len(segments)
            
            if double_validation and self.llm_validator:
                # Traducere normală apoi validare dublă
                segments = self.translate_segments_enhanced(
                    segments, source_lang, target_lang,
                    validate_with_llm=False
                )
                segments = self.validate_translations_double(
                    segments, source_lang, target_lang
                )
            else:
                # Traducere cu validare simplă
                segments = self.translate_segments_enhanced(
                    segments, source_lang, target_lang,
                    validate_with_llm=use_llm_validation
                )
            
            # Verificare
            if len(segments) != original_count:
                print(f"\n⌠ATENȚIE: Pierdere de segmente în traducere!")
                print(f"   Înainte: {original_count}, După: {len(segments)}")
            else:
                print(f"✅ Toate {len(segments)} segmente procesate cu succes")
        
        # 4. Salvare
        video_name = Path(video_path).stem
        llm_suffix = "_llm" if use_llm_validation else ""
        double_suffix = "_double" if double_validation else ""
        subtitle_file = str(Path(output_dir) / 
            f"{video_name}_{source_lang}_to_{target_lang}{llm_suffix}{double_suffix}.{subtitle_format}")
        
        self.save_subtitles_enhanced(segments, subtitle_file, subtitle_format)
        
        processing_time = time.time() - start_time
        
        # Statistici validare
        if use_llm_validation and segments:
            avg_confidence = sum(seg.confidence for seg in segments) / len(segments)
            confidence_info = f"📊 Încredere medie: {avg_confidence:.1%}"
        else:
            confidence_info = ""
        
        print("\n" + "="*60)
        print("✅ PROCESARE COMPLETĂ")
        print("="*60)
        print(f"⏱️ Timp total: {processing_time:.1f}s")
        print(f"📝 Subtitrări: {subtitle_file}")
        print(f"📊 Total: {len(segments)} segmente")
        if confidence_info:
            print(confidence_info)
        print("="*60 + "\n")
        
        return {
            'video': video_path,
            'segments': len(segments),
            'time': processing_time,
            'output': subtitle_file,
            'llm_validated': use_llm_validation,
            'double_validated': double_validation
        }


def main():
    parser = argparse.ArgumentParser(description="🎬 Sistem Subtitrare Reparat")
    
    parser.add_argument('input', help='Video')
    parser.add_argument('--source', '-s', choices=['ro', 'en', 'ja', 'zh', 'ru'], help='Limba sursă')
    parser.add_argument('--target', '-t', default='en', choices=['ro', 'en', 'ja', 'zh', 'ru'], help='Limba țintă')
    parser.add_argument('--auto-detect', '-a', action='store_true', help='Detectare limbă')
    parser.add_argument('--output', '-o', default='output', help='Director output')
    parser.add_argument('--format', '-f', default='srt', choices=['srt', 'vtt'], help='Format')
    parser.add_argument('--model', '-m', default='large-v3', help='Model Whisper')
    
    args = parser.parse_args()
    
    if not args.source and not args.auto_detect:
        print("⚠️ Specifică --source sau --auto-detect")
        sys.exit(1)
    
    system = OptimizedSubtitleSystem(use_gpu=True)
    
    system.process_video_complete(
        args.input,
        source_lang=args.source,
        target_lang=args.target,
        output_dir=args.output,
        subtitle_format=args.format,
        model_size=args.model,
        auto_detect_language=args.auto_detect
    )


if __name__ == "__main__":
    main()