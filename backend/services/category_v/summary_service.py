"""
🔥 Serviciu de Rezumare Inteligentă
====================================
Generează rezumate semantice în română pentru orice tip de conținut
"""

import os
import requests
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

class SummaryService:
    """Serviciu pentru generarea de rezumate semantice adaptate"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inițializare serviciu de rezumare
        
        Args:
            api_key: API key pentru Google Gemini (opțional)
        """
        self.api_key = os.getenv("GEMINI_API_KEY") or "AIzaSyCrL0AA-rH5PYsGQ4F2OM1YjL8xtKn9K-I"
        self.output_dir = Path('processed')
        self.output_dir.mkdir(exist_ok=True)
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:32b")
        self.chunk_size = int(os.getenv("SUMMARY_CHUNK_SIZE", "3500"))
        
    def summarize_content(
        self, 
        content_id: str, 
        text: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generează rezumat semantic pentru un conținut
        
        Args:
            content_id: ID unic al conținutului
            text: Textul de rezumat
            metadata: Metadate despre conținut (tip, limbă, etc.)
            
        Returns:
            Dict cu rezumatul și metadate
        """
        try:
            # Prompt pentru rezumat semantic adaptat
            summary = self._generate_summary_gemini(text, metadata)
            
            # Salvare rezumat
            summary_file = self._save_summary(content_id, summary, metadata)
            
            return {
                'success': True,
                'content_id': content_id,
                'summary': summary,
                'summary_file': summary_file,
                'metadata': metadata
            }
            
        except Exception as e:
            print(f"[SUMMARY] ERROR: {e}")
            # Fallback la rezumat simplu
            summary = self._generate_simple_summary(text)
            summary_file = self._save_summary(content_id, summary, metadata)
            
            return {
                'success': False,
                'content_id': content_id,
                'summary': summary,
                'summary_file': summary_file,
                'error': str(e)
            }
    
    def _ollama_generate(self, prompt: str) -> str:
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

    def _gemini_generate(self, prompt: str) -> str:
        try:
            import google.generativeai as genai
            if not self.api_key:
                return ""
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content(prompt)
            return response.text.strip() if response and getattr(response, "text", "").strip() else ""
        except Exception as e:
            print(f"[SUMMARY] Gemini error: {e}")
            return ""

    def _llm_generate(self, prompt: str) -> str:
        out = self._ollama_generate(prompt)
        if out:
            return out
        return self._gemini_generate(prompt)

    def _chunk_text(self, text: str, chunk_size: int = None) -> List[str]:
        chunk_size = chunk_size or self.chunk_size
        chunks = []
        current = []
        length = 0
        for paragraph in text.split("\n"):
            p = paragraph.strip()
            if not p:
                continue
            if length + len(p) + 1 > chunk_size and current:
                chunks.append("\n".join(current))
                current = [p]
                length = len(p)
            else:
                current.append(p)
                length += len(p) + 1
        if current:
            chunks.append("\n".join(current))
        return chunks or [text]

    def _generate_summary_gemini(self, text: str, metadata: Dict[str, Any]) -> str:
        """Generează rezumat cu Ollama -> Gemini, cu suport pentru texte lungi (chunking + multi-pass)."""
        if not text:
            return ""

        source_type = metadata.get('source_type', 'document')
        domain = metadata.get('domain', '')

        def base_prompt(body: str) -> str:
            return f"""
Analizează conținutul și generează un REZUMAT EXECUTIV în limba română.

CONȚINUT (tip: {source_type}{', domeniu: ' + domain if domain else ''}):
{body}

CERINȚE:
1. REZUMAT EXECUTIV (2-3 paragrafe)
2. PUNCTE CHEIE (5-7 bullet-uri)
3. CUVINTE CHEIE (5-10, listă)

Format:
REZUMAT:
[text]

PUNCTE CHEIE:
• ...

CUVINTE CHEIE:
[cuvânt1, ...]
"""

        chunks = self._chunk_text(text, 3500)

        if len(chunks) == 1:
            out = self._llm_generate(base_prompt(chunks[0]))
            return out or self._generate_simple_summary(text)

        partials = []
        for idx, ch in enumerate(chunks, 1):
            prompt = f"Rezuma segmentul #{idx} în română (max 6-8 propoziții), păstrând ideile cheie.\n\n{ch}"
            part = self._llm_generate(prompt)
            if part:
                partials.append(part)

        if not partials:
            return self._generate_simple_summary(text)

        final_prompt = base_prompt("\n\n".join(partials))
        final_summary = self._llm_generate(final_prompt)
        return final_summary or "\n\n".join(partials) or self._generate_simple_summary(text)
    
    def _generate_simple_summary(self, text: str) -> str:
        """Fallback: rezumat simplu prin trunchiere"""
        lines = text.split('\n')
        
        # Extrage primele paragrafe non-goale
        summary_lines = []
        for line in lines[:20]:  # primele 20 linii
            if line.strip():
                summary_lines.append(line.strip())
            if len(summary_lines) >= 5:
                break
        
        summary = '\n\n'.join(summary_lines)
        
        # Extrage cuvinte cheie simple
        words = text.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 4:  # cuvinte semnificative
                word_freq[word] = word_freq.get(word, 0) + 1
        
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        keywords_str = ', '.join([w[0] for w in keywords])
        
        return f"""REZUMAT:
{summary[:500]}...

CUVINTE CHEIE:
{keywords_str}
"""
    
    def _save_summary(
        self, 
        content_id: str, 
        summary: str, 
        metadata: Dict[str, Any]
    ) -> str:
        """Salvează rezumatul într-un fișier"""
        # Crează nume de fișier bazat pe content_id
        base_name = content_id.replace('/', '_').replace('\\', '_')
        summary_file = self.output_dir / f"{base_name}_summary_ro.txt"
        
        # Adaugă metadate la rezumat
        full_content = f"""{'='*60}
REZUMAT GENERAT AUTOMAT
{'='*60}

METADATE:
- Content ID: {content_id}
- Tip sursă: {metadata.get('source_type', 'unknown')}
- Limbă: {metadata.get('lang', 'ro')}
- Domeniu: {metadata.get('domain', 'general')}
- Temă: {metadata.get('topic', 'N/A')}
- Data procesare: {metadata.get('timestamp', 'N/A')}

{'='*60}

{summary}

{'='*60}
"""
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        print(f"[SUMMARY] ✅ Saved: {summary_file}")
        return str(summary_file.name)
    
    def batch_summarize(
        self, 
        contents: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        """
        Rezumă mai multe conținuturi în batch
        
        Args:
            contents: Listă de dict-uri cu 'id', 'text', 'metadata'
            
        Returns:
            Listă de rezultate
        """
        results = []
        for i, content in enumerate(contents):
            print(f"[SUMMARY] Processing {i+1}/{len(contents)}: {content.get('id')}")
            result = self.summarize_content(
                content_id=content['id'],
                text=content['text'],
                metadata=content.get('metadata', {})
            )
            results.append(result)
        
        return results


# Test standalone
if __name__ == "__main__":
    service = SummaryService()
    
    test_text = """
    Inteligența artificială (AI) reprezintă una dintre cele mai importante 
    evoluții tehnologice ale secolului XXI. Aceasta include machine learning, 
    deep learning, natural language processing și computer vision.
    
    Aplicațiile AI sunt variate: de la asistente vocale și sisteme de recomandare,
    până la vehicule autonome și diagnosticare medicală avansată.
    """
    
    result = service.summarize_content(
        content_id='test_001',
        text=test_text,
        metadata={
            'source_type': 'document',
            'lang': 'ro',
            'domain': 'tehnologie'
        }
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
