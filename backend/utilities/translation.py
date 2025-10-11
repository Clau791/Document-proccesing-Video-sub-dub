"""

IMPLEMENTAT:
•	Traduca din engleza, chineza, rusa si japoneza in romana (documente scrise, audio, video)
'	Documentele vor fi traduse iar apoi rezultatul traducerii va fi prelucrat conform instructionilor pentru cele in romana
---	    Fisierele audio
'	Se va traduce audio-ul in romana si se vor genera fisiere audio noi cu numele original la care se va adauga sufixul RO
'	Se va genera un rezumat in romana al continutului
'	Rezumatul va fi prelucrat conform instructionilor pentru documentele in romana
----	Fisiere video
'	Partea audio se va traduce in romana si se vor genera fisiere video noi cu audio-ul in romana avand numele original la care se va adauga sufixul RO
'	Se va genera un rezumat in romana al continutului
'	Rezumatul va fi prelucrat conform instructionilor pentru documentele in romana

Script pentru procesarea fișierelor audio și video cu traducere în română
Autor: Claude
Versiune: 1.0

DEPENDENȚE NECESARE:
pip install openai ffmpeg-python gtts pydub python-dotenv

ALTE CERINȚE:
- FFmpeg instalat în sistem (https://ffmpeg.org/download.html)
- API Key OpenAI pentru transcriere și generare rezumate
- Conexiune la internet pentru servicii de traducere

WORKFLOW:
1. Detectare tip fișier (audio/video)
2. Extragere audio din video (dacă este video)
3. Transcriere audio folosind OpenAI Whisper
4. Traducere text în română
5. Generare audio în română folosind gTTS
6. Pentru video: combinare audio tradus cu video original
7. Generare rezumat inteligent în română
8. Salvare fișiere cu sufix "_RO"
"""

import os
import sys
from pathlib import Path
from typing import Tuple, Optional
import json

# Librării pentru procesare audio/video
import ffmpeg
from pydub import AudioSegment

# Librării pentru AI și traducere
from openai import OpenAI
from gtts import gTTS

# Configurare
from dotenv import load_dotenv

# Încarcă variabilele de mediu
load_dotenv()


class AudioVideoProcessor:
    """Clasă pentru procesarea fișierelor audio și video"""
    
    def __init__(self, openai_api_key: str = None):
        """
        Inițializare procesor
        
        Args:
            openai_api_key: Cheia API OpenAI (sau setată în .env ca OPENAI_API_KEY)
        """
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key este necesară! Setează OPENAI_API_KEY în .env sau ca parametru.")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Extensii suportate
        self.audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'}
        self.video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv'}
    
    def is_audio_file(self, filepath: str) -> bool:
        """Verifică dacă fișierul este audio"""
        return Path(filepath).suffix.lower() in self.audio_extensions
    
    def is_video_file(self, filepath: str) -> bool:
        """Verifică dacă fișierul este video"""
        return Path(filepath).suffix.lower() in self.video_extensions
    
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
    
    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcrie audio folosind OpenAI Whisper
        
        Args:
            audio_path: Calea către fișierul audio
            
        Returns:
            Textul transcris
        """
        print(f"🎤 Transcriu audio: {audio_path}")
        
        try:
            with open(audio_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            print(f"✓ Audio transcris ({len(transcript)} caractere)")
            return transcript
        except Exception as e:
            print(f"✗ Eroare la transcriere: {e}")
            raise
    
    def translate_to_romanian(self, text: str) -> str:
        """
        Traduce text în română folosind OpenAI
        
        Args:
            text: Textul de tradus
            
        Returns:
            Textul tradus în română
        """
        print(f"🌍 Traduc text în română...")
        
        try:
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Ești un traducător profesionist. Traduce textul următor în limba română, păstrând sensul și tonul original. Returnează doar traducerea, fără comentarii suplimentare."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.3
            )
            
            translated_text = response.choices[0].message.content.strip()
            print(f"✓ Text tradus ({len(translated_text)} caractere)")
            return translated_text
        except Exception as e:
            print(f"✗ Eroare la traducere: {e}")
            raise
    
    def generate_audio_from_text(self, text: str, output_path: str, lang: str = 'ro') -> str:
        """
        Generează fișier audio din text folosind gTTS
        
        Args:
            text: Textul pentru generare audio
            output_path: Calea pentru fișierul audio generat
            lang: Limba (default: 'ro' pentru română)
            
        Returns:
            Calea către fișierul audio generat
        """
        print(f"🔊 Generez audio în română...")
        try:
            response = self.client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=text,
            )
            with open(output_path, "wb") as f:
                f.write(response.read())

            print(f"✅ Audio generat: {output_path}")
            return output_path

        except Exception as e:
            print(f"❌ Eroare la generarea audio: {e}")
            raise
    
    def combine_audio_with_video(self, video_path: str, audio_path: str, output_path: str) -> str:
        """
        Combină audio nou cu video original
        
        Args:
            video_path: Calea către fișierul video original
            audio_path: Calea către noul fișier audio
            output_path: Calea pentru fișierul video final
            
        Returns:
            Calea către fișierul video final
        """
        print(f"🎬 Combin audio cu video...")
        
        try:
            video = ffmpeg.input(video_path)
            audio = ffmpeg.input(audio_path)
            
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
    
    def generate_summary(self, text: str) -> str:
        """
        Generează un rezumat inteligent al conținutului
        
        Args:
            text: Textul pentru rezumat
            
        Returns:
            Rezumatul generat
        """
        print(f"📝 Generez rezumat...")
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """Ești un asistent care creează rezumate concise și informative în limba română.
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
                    },
                    {
                        "role": "user",
                        "content": f"Creează un rezumat detaliat pentru următorul conținut:\n\n{text}"
                    }
                ],
                temperature=0.5
            )
            
            summary = response.choices[0].message.content.strip()
            print(f"✓ Rezumat generat ({len(summary)} caractere)")
            return summary
        except Exception as e:
            print(f"✗ Eroare la generarea rezumatului: {e}")
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
    
    def process_audio_file(self, audio_path: str, output_dir: str = None) -> dict:
        """
        Procesează un fișier audio complet
        
        Args:
            audio_path: Calea către fișierul audio original
            output_dir: Directorul pentru fișierele de ieșire (default: același cu fișierul original)
            
        Returns:
            Dicționar cu căile către fișierele generate
        """
        print(f"\n{'='*60}")
        print(f"🎵 PROCESARE FIȘIER AUDIO")
        print(f"{'='*60}\n")
        
        audio_path = Path(audio_path)
        output_dir = Path(output_dir) if output_dir else audio_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        base_name = audio_path.stem
        extension = audio_path.suffix
        
        # Definire căi pentru fișierele de ieșire
        output_audio_path = output_dir / f"{base_name}_RO{extension}"
        output_summary_path = output_dir / f"{base_name}_RO_rezumat.txt"
        temp_audio_path = output_dir / f"{base_name}_temp.mp3"
        
        results = {}
        
        try:
            # 1. Transcriere audio original
            transcript = self.transcribe_audio(str(audio_path))
            
            # 2. Traducere în română
            translated_text = self.translate_to_romanian(transcript)
            
            # 3. Generare audio în română
            self.generate_audio_from_text(translated_text, str(temp_audio_path))
            
            # 4. Copiere audio generat la destinație finală
            os.replace(str(temp_audio_path), str(output_audio_path))
            results['audio'] = str(output_audio_path)
            
            # 5. Generare rezumat
            summary = self.generate_summary(translated_text)
            self.save_summary(summary, str(output_summary_path))
            results['summary'] = str(output_summary_path)
            
            print(f"\n{'='*60}")
            print(f"✓ PROCESARE AUDIO COMPLETĂ")
            print(f"  Audio tradus: {output_audio_path}")
            print(f"  Rezumat: {output_summary_path}")
            print(f"{'='*60}\n")
            
            return results
            
        except Exception as e:
            print(f"\n✗ Eroare la procesarea fișierului audio: {e}")
            raise
    
    def process_video_file(self, video_path: str, output_dir: str = None) -> dict:
        """
        Procesează un fișier video complet
        
        Args:
            video_path: Calea către fișierul video original
            output_dir: Directorul pentru fișierele de ieșire (default: același cu fișierul original)
            
        Returns:
            Dicționar cu căile către fișierele generate
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
            
            # 5. Combinare audio tradus cu video original
            self.combine_audio_with_video(
                str(video_path),
                str(temp_audio_ro),
                str(output_video_path)
            )
            results['video'] = str(output_video_path)
            
            # 6. Generare rezumat
            summary = self.generate_summary(translated_text)
            self.save_summary(summary, str(output_summary_path))
            results['summary'] = str(output_summary_path)
            
            # 7. Curățare fișiere temporare
            temp_audio_original.unlink(missing_ok=True)
            temp_audio_ro.unlink(missing_ok=True)
            
            print(f"\n{'='*60}")
            print(f"✓ PROCESARE VIDEO COMPLETĂ")
            print(f"  Video tradus: {output_video_path}")
            print(f"  Rezumat: {output_summary_path}")
            print(f"{'='*60}\n")
            
            return results
            
        except Exception as e:
            print(f"\n✗ Eroare la procesarea fișierului video: {e}")
            # Curățare fișiere temporare în caz de eroare
            temp_audio_original.unlink(missing_ok=True)
            temp_audio_ro.unlink(missing_ok=True)
            raise
    
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