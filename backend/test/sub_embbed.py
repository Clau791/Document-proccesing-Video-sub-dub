"""
Extensie pentru a include subtitrări direct în video
Adaugă această clasă la proiectul existent sub.py
"""

from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip
import subprocess
from pathlib import Path
from typing import List, Optional, Dict
import pysubs2


from pathlib import Path
import platform
import pysubs2

def _ffmpeg_filter_escape(p: str) -> str:
    """
    Escape pentru argumente de filtru FFmpeg pe Windows.
    Se aplică DOAR în partea de -vf (nu și la -i).
    """
    p = str(Path(p).resolve())
    # În filtergraph, trebuie scăpate \, :, , și ' (apostrof)
    p = p.replace('\\', '\\\\')  # \  -> \\
    p = p.replace(':', '\\:')    # :  -> \:
    p = p.replace(',', '\\,')    # ,  -> \,
    p = p.replace("'", r"\'")    # '  -> \'
    return f"'{p}'"  # închidem în ghilimele simple ca să păstrăm spațiile

def _srt_to_ass(srt_path: str) -> str:
    subs = pysubs2.load(srt_path)
    if 'Default' not in subs.styles:
        subs.styles['Default'] = pysubs2.SSAStyle(
            fontname="Arial", fontsize=24, outline=2, shadow=1, alignment=2, marginv=50
        )
    out = str(Path(srt_path).with_suffix(".ass"))
    subs.save(out)
    return out

class VideoSubtitleEmbedder:
    """Clasă pentru încorporarea subtitrărilor în video"""
    
    def __init__(self):
        self.default_style = {
            'fontsize': 24,
            'font': 'Arial-Bold',
            'color': 'white',
            'stroke_color': 'black',
            'stroke_width': 2,
            'method': 'caption',
            'align': 'center'
        }
        
    def embed_subtitles_moviepy(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: str,
        style: Optional[Dict] = None,
        position: str = 'bottom'
    ) -> str:
        """
        Încorporează subtitrări folosind MoviePy (mai lent dar mai flexibil)
        
        Args:
            video_path: Calea către video
            subtitle_path: Calea către fișierul de subtitrări
            output_path: Calea pentru output
            style: Dicționar cu stiluri personalizate
            position: Poziția subtitrărilor ('bottom', 'top', 'center')
            
        Returns:
            Calea către video-ul final
        """
        print(f"🎬 Încorporare subtitrări cu MoviePy...")
        
        # Încarcă video
        video = VideoFileClip(video_path)
        
        # Merge stilurile
        subtitle_style = {**self.default_style, **(style or {})}
        
        # Funcție pentru a genera TextClip pentru fiecare subtitrare
        def make_textclip(txt):
            return TextClip(
                txt,
                fontsize=subtitle_style['fontsize'],
                font=subtitle_style['font'],
                color=subtitle_style['color'],
                stroke_color=subtitle_style['stroke_color'],
                stroke_width=subtitle_style['stroke_width'],
                method=subtitle_style['method'],
                size=(video.w * 0.9, None),
                align='center'
            )
        
        # Creează SubtitlesClip
        generator = lambda txt: make_textclip(txt)
        subtitles = SubtitlesClip(subtitle_path, generator)
        
        # Calculează poziția
        if position == 'bottom':
            subtitles = subtitles.set_position(('center', video.h * 0.85))
        elif position == 'top':
            subtitles = subtitles.set_position(('center', video.h * 0.05))
        else:  # center
            subtitles = subtitles.set_position('center')
        
        # Combină video cu subtitrări
        final = CompositeVideoClip([video, subtitles])
        
        # Salvează
        final.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            fps=video.fps
        )
        
        video.close()
        print(f"✅ Video cu subtitrări salvat: {output_path}")
        return output_path
    
    def embed_subtitles_ffmpeg(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: str,
        subtitle_format: str = 'srt',
        style_override: Optional[str] = None
    ) -> str:
        print("⚡ Încorporare subtitrări cu FFmpeg (rapid)...")

        # Căi absolute pentru siguranță
        v_abs = str(Path(video_path).resolve())
        s_abs = str(Path(subtitle_path).resolve())
        o_abs = str(Path(output_path).resolve())

        if not Path(v_abs).exists():
            raise FileNotFoundError(f"Video inexistent: {v_abs}")
        if not Path(s_abs).exists():
            raise FileNotFoundError(f"Subtitrare inexistentă: {s_abs}")

        # Convertim SRT/VTT -> ASS (recomandat) înainte de filtrul ass=
        if Path(s_abs).suffix.lower() != ".ass":
            s_ass = _srt_to_ass(s_abs)
        else:
            s_ass = s_abs

        vf = f"ass={_ffmpeg_filter_escape(s_ass)}"

        cmd = [
            "ffmpeg",
            "-y",
            "-i", v_abs,              # atenție: aici NU scăpăm backslash/colon
            "-vf", vf,                # aici folosim variabila escapata
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            o_abs
        ]

        try:
            subprocess.run(cmd, text=True, capture_output=True, check=True)
            print(f"✅ Video cu subtitrări salvat: {o_abs}")
            return o_abs
        except subprocess.CalledProcessError as e:
            print("❌ Eroare FFmpeg:\n", e.stderr)
            raise

        
        
        def embed_subtitles_hardcoded(
            self,
            video_path: str,
            subtitle_path: str,
            output_path: str,
            font_name: str = 'Arial',
            font_size: int = 24,
            font_color: str = 'white',
            border_color: str = 'black',
            border_width: int = 2,
            position: str = 'bottom',
            margin_v: int = 50
        ) -> str:
            """
            Hardcodează subtitrări cu stil personalizat folosind FFmpeg
            
            Args:
                video_path: Calea către video
                subtitle_path: Calea către subtitrări
                output_path: Calea pentru output
                font_name: Numele fontului
                font_size: Dimensiunea fontului
                font_color: Culoarea textului (white, yellow, etc.)
                border_color: Culoarea marginii
                border_width: Grosimea marginii
                position: Poziția ('bottom', 'top', 'center')
                margin_v: Margine verticală în pixeli
                
            Returns:
                Calea către video-ul final
            """
            print(f"🎨 Hardcodare subtitrări cu stil personalizat...")
            
            # Creează un fișier ASS cu stiluri personalizate
            ass_path = self._create_styled_ass(
                subtitle_path,
                font_name,
                font_size,
                font_color,
                border_color,
                border_width,
                position,
                margin_v
            )
            
            # Folosește FFmpeg pentru a aplica
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f"ass={ass_path}",
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            
            try:
                subprocess.run(cmd, capture_output=True, text=True, check=True)
                print(f"✅ Video cu subtitrări hardcodate salvat: {output_path}")
                
                # Curăță fișierul ASS temporar
                if ass_path != subtitle_path:
                    Path(ass_path).unlink()
                    
                return output_path
            except subprocess.CalledProcessError as e:
                print(f"❌ Eroare FFmpeg: {e.stderr}")
                raise
        
        def _create_styled_ass(
            self,
            subtitle_path: str,
            font_name: str,
            font_size: int,
            font_color: str,
            border_color: str,
            border_width: int,
            position: str,
            margin_v: int
        ) -> str:
            """Creează fișier ASS cu stiluri personalizate"""
            
            # Încarcă subtitrările existente
            subs = pysubs2.load(subtitle_path)
            
            # Definește stilul
            color_map = {
                'white': '&H00FFFFFF',
                'yellow': '&H0000FFFF',
                'cyan': '&H00FFFF00',
                'green': '&H0000FF00',
                'red': '&H000000FF',
                'black': '&H00000000'
            }
            
            primary_color = color_map.get(font_color.lower(), '&H00FFFFFF')
            outline_color = color_map.get(border_color.lower(), '&H00000000')
            
            # Determină alinierea bazată pe poziție
            if position == 'bottom':
                alignment = 2  # Bottom center
            elif position == 'top':
                alignment = 8  # Top center
            else:
                alignment = 5  # Middle center
            
            # Creează stil ASS
            style = pysubs2.SSAStyle()
            style.fontname = font_name
            style.fontsize = font_size
            style.primarycolor = primary_color
            style.outlinecolor = outline_color
            style.outline = border_width
            style.shadow = 1
            style.alignment = alignment
            style.marginv = margin_v
            
            # Aplică stilul
            subs.styles['Default'] = style
            
            # Salvează ca ASS
            output_ass = subtitle_path.replace('.srt', '.ass').replace('.vtt', '.ass')
            if output_ass == subtitle_path:
                output_ass = subtitle_path + '.ass'
                
            subs.save(output_ass)
            return output_ass
        
        def _convert_to_styled_ass(
            self,
            subtitle_path: str,
            format: str,
            style_override: str
        ) -> str:
            """Convertește subtitrări în ASS cu stil personalizat"""
            subs = pysubs2.load(subtitle_path)
            output_ass = subtitle_path.replace(f'.{format}', '.ass')
            
            # Aplică stil personalizat dacă este furnizat
            if style_override:
                # Parse și aplică stilul
                # Implementare simplificată
                pass
                
            subs.save(output_ass)
            return output_ass
        
        def create_dual_subtitle_video(
            self,
            video_path: str,
            subtitle_path1: str,
            subtitle_path2: str,
            output_path: str,
            lang1_position: str = 'bottom',
            lang2_position: str = 'top'
        ) -> str:
            """
            Creează video cu două seturi de subtitrări (ex: original + traducere)
            
            Args:
                video_path: Calea către video
                subtitle_path1: Prima subtitrare (ex: română)
                subtitle_path2: A doua subtitrare (ex: japoneză)
                output_path: Calea pentru output
                lang1_position: Poziția primei subtitrări
                lang2_position: Poziția celei de-a doua subtitrări
                
            Returns:
                Calea către video-ul final
            """
            print(f"🌐 Creare video cu subtitrări duble...")
            
            # Creează două fișiere ASS cu poziții diferite
            ass1 = self._create_styled_ass(
                subtitle_path1,
                font_name='Arial',
                font_size=22,
                font_color='white',
                border_color='black',
                border_width=2,
                position=lang1_position,
                margin_v=50 if lang1_position == 'bottom' else 30
            )
            
            ass2 = self._create_styled_ass(
                subtitle_path2,
                font_name='Arial',
                font_size=20,
                font_color='yellow',
                border_color='black',
                border_width=2,
                position=lang2_position,
                margin_v=30 if lang2_position == 'top' else 50
            )
            
            # Aplică ambele subtitrări cu FFmpeg
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f"ass={ass1},ass={ass2}",
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            
            try:
                subprocess.run(cmd, capture_output=True, text=True, check=True)
                print(f"✅ Video cu subtitrări duble salvat: {output_path}")
                
                # Curăță fișierele temporare
                if ass1 != subtitle_path1:
                    Path(ass1).unlink()
                if ass2 != subtitle_path2:
                    Path(ass2).unlink()
                    
                return output_path
            except subprocess.CalledProcessError as e:
                print(f"❌ Eroare FFmpeg: {e.stderr}")
                raise


# Extensie pentru clasa AdvancedSubtitleSystem
def add_video_embedding_to_system():
    """
    Adaugă aceste metode la clasa AdvancedSubtitleSystem
    Copiază în fișierul sub.py original
    """
    
    def __init_embedder__(self):
        """Adaugă la __init__ al AdvancedSubtitleSystem"""
        self.embedder = VideoSubtitleEmbedder()
    
    def process_video_with_embedded_subs(
        self,
        video_path: str,
        source_lang: str,
        target_lang: str,
        output_dir: str = "output",
        subtitle_format: str = 'srt',
        enable_lip_sync: bool = True,
        embed_method: str = 'ffmpeg',  # 'ffmpeg' sau 'moviepy'
        embed_style: Optional[Dict] = None
    ) -> Dict:
        """
        Procesează video cu subtitrări încorporate
        
        Args:
            video_path: Calea către video
            source_lang: Limba sursă
            target_lang: Limba țintă
            output_dir: Director output
            subtitle_format: Format subtitrare
            enable_lip_sync: Activează lip sync
            embed_method: Metoda de încorporare ('ffmpeg' sau 'moviepy')
            embed_style: Stil personalizat pentru subtitrări
            
        Returns:
            Dicționar cu informații despre procesare
        """
        # 1. Generează subtitrările (folosește metoda existentă)
        report = self.process_video(
            video_path,
            source_lang,
            target_lang,
            output_dir,
            subtitle_format,
            enable_lip_sync
        )
        
        # 2. Încorporează subtitrările în video
        subtitle_file = report['output_file']
        video_name = Path(video_path).stem
        output_video = f"{output_dir}/{video_name}_with_subs.mp4"
        
        if embed_method == 'ffmpeg':
            self.embedder.embed_subtitles_ffmpeg(
                video_path,
                subtitle_file,
                output_video,
                subtitle_format
            )
        else:
            self.embedder.embed_subtitles_moviepy(
                video_path,
                subtitle_file,
                output_video,
                embed_style
            )
        
        report['embedded_video'] = output_video
        return report


# Exemplu de utilizare
if __name__ == "__main__":
    embedder = VideoSubtitleEmbedder()
    
    # Metodă 1: FFmpeg (rapid)
    embedder.embed_subtitles_ffmpeg(
        'C:\\Users\\klau2\\OneDrive\\Desktop\\Text,Video procces\\backend\\test\\input_videos\\WhatsApp Video 2025-10-08 at 19.46.01_35af4fd5.mp4',
        'C:\\Users\\klau2\\OneDrive\\Desktop\\Text,Video procces\\backend\\test\\output\\WhatsApp Video 2025-10-08 at 19.46.01_35af4fd5_ro_to_en.srt',
        'output_with_subs.mp4'
    )
    
    # Metodă 2: Stil personalizat
    # embedder.embed_subtitles_hardcoded(
    #     'input_video.mp4',
    #     'subtitles.srt',
    #     'output_styled.mp4',
    #     font_name='Arial-Bold',
    #     font_size=28,
    #     font_color='yellow',
    #     border_width=3
    # )
    
    # # Metodă 3: Subtitrări duble
    # embedder.create_dual_subtitle_video(
    #     'input_video.mp4',
    #     'subtitles_ro.srt',
    #     'subtitles_ja.srt',
    #     'output_dual.mp4'
    # )