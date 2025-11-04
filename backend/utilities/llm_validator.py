"""
Validator LLM pentru traduceri - folosește Ollama cu Gemma3 sau Mistral
"""

import requests
import json
import time
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import concurrent.futures
from tqdm import tqdm

@dataclass
class ValidationResult:
    original_text: str
    initial_translation: str
    validated_translation: str
    confidence_score: float
    model_used: str
    validation_time: float

class LLMTranslationValidator:
    """Validator și îmbunătățitor de traduceri folosind LLM local"""
    
    def __init__(
        self,
        ollama_url: str = "http://86.126.134.77:11434",
        primary_model: str = "gemma3:27b",
        fallback_model: str = "mistral:Q4_K_M",
        max_retries: int = 3
    ):
        self.base_url = f"{ollama_url}/api/generate"
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.max_retries = max_retries
        self.session = requests.Session()
        
        # Cache pentru traduceri validate
        self.cache = {}
        
        print(f"🤖 LLM Validator inițializat")
        print(f"   Primary: {primary_model}")
        print(f"   Fallback: {fallback_model}")
        print(f"   Server: {ollama_url}")
        
        # Test conexiune
        self._test_connection()
    
    def _test_connection(self):
        """Testează conexiunea la Ollama"""
        try:
            test_payload = {
                "model": self.primary_model,
                "prompt": "Salut",
                "stream": False,
                "num_predict": 5
            }
            
            response = self.session.post(
                self.base_url,
                json=test_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Conexiune LLM OK")
            else:
                print(f"⚠️ Status code: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Nu se poate conecta la LLM: {e}")
            print("   Validarea va funcționa în modul offline")
    
    def validate_translation(
        self,
        original_text: str,
        translated_text: str,
        source_lang: str,
        target_lang: str,
        context: str = "",
        use_streaming: bool = True
    ) -> ValidationResult:
        """Validează și îmbunătățește o traducere"""
        
        start_time = time.time()
        
        # Check cache
        cache_key = (original_text, source_lang, target_lang)
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            cached.validation_time = 0.01  # From cache
            return cached
        
        # Construiește prompt specializat
        prompt = self._build_validation_prompt(
            original_text,
            translated_text,
            source_lang,
            target_lang,
            context
        )
        
        # Încearcă cu modelul principal
        validated_text = self._call_llm(
            prompt,
            self.primary_model,
            use_streaming
        )
        
        # Fallback dacă e necesar
        if not validated_text or validated_text == translated_text:
            validated_text = self._call_llm(
                prompt,
                self.fallback_model,
                use_streaming
            )
            model_used = self.fallback_model
        else:
            model_used = self.primary_model
        
        # Dacă tot nu avem rezultat valid, păstrăm traducerea originală
        if not validated_text:
            validated_text = translated_text
            confidence = 0.5
        else:
            # Calculează scor de încredere
            confidence = self._calculate_confidence(
                original_text,
                translated_text,
                validated_text
            )
        
        result = ValidationResult(
            original_text=original_text,
            initial_translation=translated_text,
            validated_translation=validated_text,
            confidence_score=confidence,
            model_used=model_used,
            validation_time=time.time() - start_time
        )
        
        # Cache rezultatul
        self.cache[cache_key] = result
        
        return result
    
    def validate_batch(
        self,
        segments: List[Dict],
        source_lang: str,
        target_lang: str,
        batch_size: int = 5,
        parallel: bool = False
    ) -> List[Dict]:
        """Validează un batch de segmente de subtitrare"""
        
        print(f"\n🔍 Validare traduceri cu LLM...")
        print(f"   Segmente: {len(segments)}")
        print(f"   Limbă: {source_lang} → {target_lang}")
        
        validated_segments = []
        
        if parallel and len(segments) > 10:
            # Procesare paralelă pentru multe segmente
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                
                for seg in segments:
                    future = executor.submit(
                        self.validate_translation,
                        seg.get('original_text', ''),
                        seg.get('text', ''),
                        source_lang,
                        target_lang,
                        use_streaming=False
                    )
                    futures.append((seg, future))
                
                for seg, future in tqdm(futures, desc="Validare LLM"):
                    try:
                        result = future.result(timeout=30)
                        seg['text'] = result.validated_translation
                        seg['llm_confidence'] = result.confidence_score
                        seg['llm_model'] = result.model_used
                        validated_segments.append(seg)
                    except:
                        validated_segments.append(seg)
        else:
            # Procesare secvențială
            for seg in tqdm(segments, desc="Validare LLM"):
                original = seg.get('original_text', '')
                translated = seg.get('text', '')
                
                if not original or not translated:
                    validated_segments.append(seg)
                    continue
                
                result = self.validate_translation(
                    original,
                    translated,
                    source_lang,
                    target_lang,
                    use_streaming=False
                )
                
                seg['text'] = result.validated_translation
                seg['llm_confidence'] = result.confidence_score
                seg['llm_model'] = result.model_used
                
                validated_segments.append(seg)
        
        # Statistici
        avg_confidence = sum(
            s.get('llm_confidence', 0) for s in validated_segments
        ) / len(validated_segments)
        
        print(f"✅ Validare completă")
        print(f"   Încredere medie: {avg_confidence:.1%}")
        
        return validated_segments
    
    def _build_validation_prompt(
        self,
        original: str,
        translation: str,
        source_lang: str,
        target_lang: str,
        context: str = ""
    ) -> str:
        """Construiește prompt pentru validare"""
        
        lang_names = {
            'ro': 'română',
            'en': 'engleză',
            'zh': 'chineză',
            'ja': 'japoneză',
            'ru': 'rusă'
        }
        
        src_name = lang_names.get(source_lang, source_lang)
        tgt_name = lang_names.get(target_lang, target_lang)
        
        # Prompt optimizat pentru validare și corecție
        prompt = f"""Ești un expert traducător profesionist. Validează și îmbunătățește următoarea traducere.

TEXT ORIGINAL ({src_name}):
{original}

TRADUCERE INIȚIALĂ ({tgt_name}):
{translation}

INSTRUCȚIUNI:
1. Verifică dacă traducerea este corectă și completă
2. Păstrează sensul și tonul originalului
3. Corectează orice erori gramaticale sau de exprimare
4. Asigură-te că traducerea sună natural în {tgt_name}
5. Pentru subtitrări, păstrează textul concis și clar

RĂSPUNDE DOAR CU TRADUCEREA CORECTATĂ/VALIDATĂ, FĂRĂ EXPLICAȚII:"""
        
        if context:
            prompt += f"\n\nCONTEXT: {context}"
        
        return prompt
    
    def _call_llm(
        self,
        prompt: str,
        model: str,
        use_streaming: bool = True
    ) -> Optional[str]:
        """Apelează LLM-ul pentru validare"""
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": use_streaming,
            "temperature": 0.3,  # Mai deterministă pentru traduceri
            "top_p": 0.9,
            "num_predict": 256,  # Limită rezonabilă
            "keep_alive": "30m"
        }
        
        try:
            if use_streaming:
                # Streaming pentru feedback real-time
                response = self.session.post(
                    self.base_url,
                    json=payload,
                    stream=True,
                    timeout=60
                )
                
                if response.status_code != 200:
                    return None
                
                full_text = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if 'response' in data:
                                full_text += data['response']
                            
                            if data.get('done', False):
                                break
                                
                        except json.JSONDecodeError:
                            continue
                
                return full_text.strip()
            
            else:
                # Non-streaming pentru batch processing
                payload['stream'] = False
                response = self.session.post(
                    self.base_url,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('response', '').strip()
                
        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout pentru {model}")
        except Exception as e:
            print(f"⚠️ Eroare LLM {model}: {e}")
        
        return None
    
    def _calculate_confidence(
        self,
        original: str,
        initial: str,
        validated: str
    ) -> float:
        """Calculează scor de încredere pentru validare"""
        
        # Verificări de bază
        if not validated or validated == initial:
            return 0.7  # Traducerea inițială păstrată
        
        # Verifică lungimea
        len_ratio = len(validated) / max(len(original), 1)
        if 0.5 < len_ratio < 2.0:
            length_score = 1.0
        else:
            length_score = 0.5
        
        # Verifică că nu e text halucinat
        if len(validated) > len(original) * 3:
            return 0.3  # Probabil halucinație
        
        # Scor final
        confidence = min(0.95, length_score * 0.9)
        
        return confidence
    
    def double_validation(
        self,
        segments: List[Dict],
        source_lang: str,
        target_lang: str
    ) -> List[Dict]:
        """Validare dublă cu ambele modele pentru acuratețe maximă"""
        
        print("\n🔍🔍 Validare dublă activată")
        
        validated_segments = []
        
        for seg in tqdm(segments, desc="Validare dublă"):
            original = seg.get('original_text', '')
            translated = seg.get('text', '')
            
            if not original or not translated:
                validated_segments.append(seg)
                continue
            
            # Validare cu modelul principal
            result1 = self.validate_translation(
                original, translated,
                source_lang, target_lang,
                use_streaming=False
            )
            
            # Validare cu modelul de backup
            prompt = self._build_validation_prompt(
                original, translated,
                source_lang, target_lang
            )
            
            text2 = self._call_llm(prompt, self.fallback_model, False)
            
            # Compară rezultatele
            if result1.validated_translation == text2:
                # Ambele modele sunt de acord
                seg['text'] = result1.validated_translation
                seg['llm_confidence'] = 0.95
                seg['validation_type'] = 'double_match'
            else:
                # Alege varianta mai probabilă
                if result1.confidence_score > 0.7:
                    seg['text'] = result1.validated_translation
                else:
                    seg['text'] = text2 if text2 else translated
                
                seg['llm_confidence'] = 0.7
                seg['validation_type'] = 'double_mismatch'
            
            validated_segments.append(seg)
        
        return validated_segments