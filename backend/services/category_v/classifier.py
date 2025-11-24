"""
🔥 Serviciu de Clasificare Inteligentă
=======================================
Clasifică conținutul după domeniu, temă și nivel informațional
"""

import os
import requests
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

class ContentClassifier:
    """Clasificator semantic pentru conținut"""
    
    # Domenii posibile (extins)
    DOMAINS = [
        'medical', 'educational', 'scientific', 'business', 'technology',
        'legal', 'finance', 'arts', 'sports', 'politics', 'general'
    ]
    
    # Niveluri informaționale
    INFO_LEVELS = ['superficial', 'detailed', 'technical', 'expert']
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inițializare clasificator
        
        Args:
            api_key: API key pentru Google Gemini (opțional)
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY', '')
        self.output_dir = Path('processed')
        self.output_dir.mkdir(exist_ok=True)
    
    def classify_content(
        self, 
        content_id: str, 
        text: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Clasifică conținutul după domeniu, temă și nivel
        
        Args:
            content_id: ID unic al conținutului
            text: Textul de clasificat
            metadata: Metadate despre conținut
            
        Returns:
            Dict cu clasificarea
        """
        try:
            # Clasificare inteligentă cu Gemini
            classification = self._classify_with_gemini(text, metadata)
            
            # Salvare clasificare
            class_file = self._save_classification(content_id, classification)
            
            return {
                'success': True,
                'content_id': content_id,
                'domain': classification['domain'],
                'topic': classification['topic'],
                'subtopic': classification['subtopic'],
                'info_level': classification['info_level'],
                'confidence': classification.get('confidence', 0.0),
                'classification_file': class_file
            }
            
        except Exception as e:
            print(f"[CLASSIFIER] ERROR: {e}")
            # Fallback la clasificare simplă
            classification = self._simple_classification(text, metadata)
            class_file = self._save_classification(content_id, classification)
            
            return {
                'success': False,
                'content_id': content_id,
                **classification,
                'classification_file': class_file,
                'error': str(e)
            }
    
    def _classify_with_gemini(
        self, 
        text: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Clasificare inteligentă cu Ollama (qwen32b) -> fallback Gemini"""
        # Ollama first
        try:
            host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
            model = os.getenv("OLLAMA_MODEL", "qwen2.5:32b")
            prompt = f"""
Analizează conținutul și întoarce DOAR un JSON cu câmpurile:
{{"domain": "...", "topic": "...", "subtopic": "...", "info_level": "...", "confidence": 0.0-1.0}}
text:
{text[:3000]}
"""
            resp = requests.post(
                f"{host}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=60,
            )
            if resp.ok:
                data = resp.json()
                cand = (data.get("response") or data.get("output") or "").strip()
                if cand:
                    parsed = self._parse_json_safe(cand)
                    if parsed:
                        return parsed
        except Exception:
            pass

        # Gemini fallback
        try:
            import google.generativeai as genai
            
            if not self.api_key:
                return self._simple_classification(text, metadata)
            
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            source_type = metadata.get('source_type', 'document')
            
            prompt = f"""
Analizează următorul conținut și clasifică-l în mod structurat.

CONȚINUT (tip: {source_type}):
{text[:3000]}

CLASIFICĂ CONȚINUTUL:

1. DOMENIU (alege unul dintre):
   - medical, educational, scientific, business, technology, legal, finance, arts, sports, politics, general

2. TEMĂ PRINCIPALĂ:
   - O frază scurtă (5-10 cuvinte) care descrie tema principală

3. SUB-TEMĂ:
   - O frază care detaliază aspecte specifice

4. NIVEL INFORMAȚIONAL (alege unul):
   - superficial: informații generale, overview
   - detailed: informații detaliate, explicații extinse
   - technical: conținut tehnic, terminologie specializată
   - expert: nivel avansat, pentru specialiști

5. ÎNCREDERE (0.0 - 1.0):
   - Cât de sigur ești de clasificare

Răspunde DOAR în format JSON:
{{
  "domain": "...",
  "topic": "...",
  "subtopic": "...",
  "info_level": "...",
  "confidence": 0.0-1.0
}}
"""
            
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Extrage JSON din răspuns
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0]
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0]
            
            classification = json.loads(result_text)
            
            # Validare
            if classification['domain'] not in self.DOMAINS:
                classification['domain'] = 'general'
            if classification['info_level'] not in self.INFO_LEVELS:
                classification['info_level'] = 'detailed'
            
            return classification
            
        except Exception as e:
            print(f"[CLASSIFIER] Gemini error: {e}, using fallback")
            return self._simple_classification(text, metadata)
    
    def _simple_classification(
        self, 
        text: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback: clasificare simplă bazată pe keywords"""
        text_lower = text.lower()
        
        # Detectare domeniu prin keywords
        domain_keywords = {
            'medical': ['medical', 'sănătate', 'boală', 'tratament', 'diagnostic', 'pacient'],
            'educational': ['educație', 'învățare', 'școală', 'student', 'curs', 'lecție'],
            'scientific': ['cercetare', 'experiment', 'teorie', 'știință', 'studiu', 'analiză'],
            'business': ['afaceri', 'companie', 'profit', 'management', 'strategie', 'piață'],
            'technology': ['tehnologie', 'software', 'hardware', 'AI', 'calculator', 'sistem'],
            'legal': ['lege', 'drept', 'juridic', 'contract', 'legalitate'],
            'finance': ['financiar', 'investiție', 'bancă', 'economie', 'buget'],
        }
        
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                domain_scores[domain] = score
        
        domain = max(domain_scores, key=domain_scores.get) if domain_scores else 'general'
        
        # Detectare nivel informațional
        technical_indicators = [
            'algoritm', 'protocol', 'metodologie', 'parametri', 'coeficient',
            'specificație', 'implementare', 'arhitectură'
        ]
        technical_count = sum(1 for ind in technical_indicators if ind in text_lower)
        
        if technical_count >= 3:
            info_level = 'technical'
        elif len(text) > 2000:
            info_level = 'detailed'
        else:
            info_level = 'superficial'
        
        # Extrage primele propoziții ca temă
        sentences = text.split('.')[:3]
        topic = ' '.join(s.strip() for s in sentences if s.strip())[:100]
        
        return {
            'domain': domain,
            'topic': topic,
            'subtopic': metadata.get('filename', 'N/A'),
            'info_level': info_level,
            'confidence': 0.6  # clasificare simplă are încredere mai mică
        }
    
    def _save_classification(
        self, 
        content_id: str, 
        classification: Dict[str, Any]
    ) -> str:
        """Salvează clasificarea într-un fișier JSON"""
        base_name = content_id.replace('/', '_').replace('\\', '_')
        class_file = self.output_dir / f"{base_name}_classification.json"
        
        with open(class_file, 'w', encoding='utf-8') as f:
            json.dump(classification, f, indent=2, ensure_ascii=False)
        
        print(f"[CLASSIFIER] ✅ Saved: {class_file}")
        return str(class_file.name)
    
    def batch_classify(
        self, 
        contents: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        """
        Clasifică mai multe conținuturi în batch
        
        Args:
            contents: Listă de dict-uri cu 'id', 'text', 'metadata'
            
        Returns:
            Listă de rezultate
        """
        results = []
        for i, content in enumerate(contents):
            print(f"[CLASSIFIER] Processing {i+1}/{len(contents)}: {content.get('id')}")
            result = self.classify_content(
                content_id=content['id'],
                text=content['text'],
                metadata=content.get('metadata', {})
            )
            results.append(result)
        
        return results


# Test standalone
if __name__ == "__main__":
    classifier = ContentClassifier()
    
    test_text = """
    Cancerul pulmonar este o boală gravă caracterizată prin creșterea 
    necontrolată a celulelor în plămâni. Principalele simptome includ 
    tuse persistentă, dureri toracice și dificultăți respiratorii.
    Diagnosticul se face prin radiografie, tomografie computerizată și biopsie.
    Tratamentul poate include chirurgie, chimioterapie, radioterapie sau 
    terapii țintite, în funcție de stadiul bolii.
    """
    
    result = classifier.classify_content(
        content_id='test_medical_001',
        text=test_text,
        metadata={
            'source_type': 'document',
            'filename': 'cancer_pulmonar.pdf'
        }
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
