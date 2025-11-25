"""
🔥 SISTEM AI INTEGRAT - Backend Principal
==========================================
Rute directe pentru fiecare serviciu - SIMPLIFICAT
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import os
import sys
import io
import uuid
import re
from datetime import datetime
from pathlib import Path

# Import servicii direct
from services.category_i.ppt_analyzer import PPTAnalyzer  
from services.category_i.document_parser import DocumentParser
from services.category_i.image_ocr import ImageOCR
from services.category_ii.document_translator import translate_document
from services.category_ii.audio_translator import AudioTranslator
from services.category_ii.video_translator import VideoTranslator
from services.category_iii.subtitle_generator import SubtitleGenerator
from services.category_iii.video_redubber import VideoRedubber
from services.category_iv.live_subtitle import LiveSubtitleEngine
from services.progress_bar import progress_bp
from history import add_history, get_history, search_history
import yt_dlp
# Import sistemul optimizat de subtitrare
# from backend.subtitles.sub import OptimizedSubtitleSystem

# ============================================
# CONFIGURARE
# ============================================

# Configuration inline (fără dependency de config.py)
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
CACHE_FOLDER = 'cache'
MAX_CONTENT_LENGTH = 30 * 1024 * 1024 * 1024  # 30GB

ALLOWED_EXTENSIONS = {
    'ppt': {'ppt', 'pptx'},
    'document': {'doc', 'docx', 'pdf', 'epub'},
    'image': {'jpg', 'jpeg', 'png', 'tiff', 'bmp'},
    'translate-doc': {'pdf', 'docx', 'pptx'},
    'translate-audio': {'mp3', 'wav', 'm4a', 'ogg', 'flac'},
    'translate-video': {'mp4', 'avi', 'mov', 'mkv', 'webm', 'mpeg', 'mpg'},
    'subtitle': {'mp4', 'avi', 'mov', 'mkv', 'webm', 'mpeg', 'mpg'},
    'redub': {'mp4', 'avi', 'mov', 'mkv', 'webm', 'mpeg', 'mpg'},
}

# Acceptă youtube.com cu orice parametri ce includ v=, plus youtu.be și rutube.ru
YOUTUBE_RUTUBE_REGEX = re.compile(r"(youtube\.com/.*[?&]v=|youtu\.be/|rutube\.ru/)", re.IGNORECASE)

# ============================================
# UTILITY FUNCTIONS
# ============================================

def fix_encoding():
    """Fix pentru encoding UTF-8 pe Windows"""
    try:
        if sys.platform == 'win32':
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            else:
                os.environ['PYTHONIOENCODING'] = 'utf-8'
            
            if hasattr(sys.stderr, 'buffer'):
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
            
            print("[ENCODING] ✅ UTF-8 encoding configurat")
    except Exception as e:
        print(f"[ENCODING] ⚠️ Nu s-a putut seta encoding: {e}")

def validate_file(file, service_type):
    """Validează tip fișier"""
    if not file or file.filename == '':
        return False
    if '.' not in file.filename:
        return False
    extension = file.filename.rsplit('.', 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS.get(service_type, set())

def validate_video_url(url: str) -> bool:
    return bool(url and YOUTUBE_RUTUBE_REGEX.search(url))


def download_video_from_url(url: str, target_dir: str, prefix: str = "yt") -> str:
    """Descarcă video (YouTube/Rutube) cu yt_dlp, returnează calea fișierului mp4."""
    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)
    out_tmpl = str(target / f"{prefix}_%(id)s.%(ext)s")

    def try_download(opts):
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
            merged = Path(filepath).with_suffix(".mp4")
            if merged.exists():
                filepath = str(merged)
            fp = Path(filepath)
            if fp.exists() and fp.stat().st_size > 0:
                return filepath
        return ""

    po_token = os.getenv("YT_PO_TOKEN") or os.getenv("YTDLP_PO_TOKEN")
    android_po = [f"android+{po_token}"] if po_token else []

    common = {
        'outtmpl': out_tmpl,
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True,
        'ignoreerrors': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0',
        },
        'geo_bypass': True,
        'concurrent_fragment_downloads': 4,
    }

    attempts = [
        # default web client
        {**common, 'format': 'bv*+ba/best', 'extractor_args': {'youtube': {'player_client': []}}},
        {**common, 'format': 'best', 'extractor_args': {'youtube': {'player_client': []}}},
        # iOS fallback
        {**common, 'format': 'bv*+ba/best', 'extractor_args': {'youtube': {'player_client': ['ios']}}},
        {**common, 'format': 'best', 'extractor_args': {'youtube': {'player_client': ['ios']}}},
        # Android client (needs PO token for some formats)
        {**common, 'format': 'bv*+ba/best', 'extractor_args': {'youtube': {'player_client': ['android'], 'po_token': android_po}}},
        {**common, 'format': 'best', 'extractor_args': {'youtube': {'player_client': ['android'], 'po_token': android_po}}},
    ]

    # dacă avem cookies yt-dlp, adaugă cookiefile
    cookiefile = os.getenv("YTDLP_COOKIES") or os.getenv("YT_COOKIES")
    if cookiefile and Path(cookiefile).exists():
        for opt in attempts:
            opt['cookiefile'] = cookiefile

    last_error = None
    for opts in attempts:
        try:
            fp = try_download(opts)
            if fp:
                return fp
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"Download video eșuat (yt_dlp). {last_error or ''}. "
                       f"Încearcă să setezi YT_PO_TOKEN/ YTDLP_COOKIES pentru linkuri protejate.")

def generate_unique_filename(original_filename):
    """Generează nume unic pentru fișier"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    name, ext = os.path.splitext(original_filename)
    return f"{timestamp}_{unique_id}_{secure_filename(name)}{ext}"

# ============================================
# INIȚIALIZARE FLASK
# ============================================

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Creare directoare
for directory in [UPLOAD_FOLDER, PROCESSED_FOLDER, CACHE_FOLDER]:
    Path(directory).mkdir(parents=True, exist_ok=True)

# Progres SSE
app.register_blueprint(progress_bp)

# Inițializare servicii
# live_engine = LiveSubtitleEngine()

# Singleton pentru sistemul de subtitrare optimizat
subtitle_system = None

# def get_subtitle_system():
#     """Singleton pentru sistemul de subtitrare"""
#     global subtitle_system
#     if subtitle_system is None:
#         subtitle_system = OptimizedSubtitleSystem(
#             use_gpu=True,
#             use_llm_validation=True
#         )
#     return subtitle_system

# ============================================
# HEALTH CHECK & LLM STATUS
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'online',
        'message': 'Backend server is running',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    }), 200

@app.route('/api/llm-status', methods=['GET'])
def llm_status():
    """Verifică statusul serverului LLM"""
    try:
        import requests
        
        OLLAMA_URL = "http://86.126.134.77:11434"
        
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            
            return jsonify({
                'status': 'online',
                'server': OLLAMA_URL,
                'available_models': models,
                'gemma3_available': any('gemma3:27b' in m for m in models),
                'mistral_available': any('mistral' in m for m in models),
                'total_models': len(models)
            }), 200
        else:
            return jsonify({
                'status': 'offline',
                'error': f'Ollama returned status {response.status_code}'
            }), 503
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/history', methods=['GET'])
def history():
    """Istoric operațiuni recente"""
    try:
        limit = int(request.args.get('limit', 50))
        data = get_history(limit=limit)
        return jsonify({'items': data}), 200
    except Exception as e:
        print(f"[HISTORY] ERROR: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/search', methods=['GET'])
def history_search():
    """Căutare full-text în istoric (FTS5 sau fallback LIKE)"""
    try:
        q = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 30))
        data = search_history(q, limit=limit)
        return jsonify({'items': data}), 200
    except Exception as e:
        print(f"[HISTORY SEARCH] ERROR: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/validate-translation', methods=['POST'])
def validate_translation():
    """Validează și îmbunătățește traduceri existente cu LLM"""
    try:
        data = request.get_json()
        
        original_text = data.get('original_text', '')
        translated_text = data.get('translated_text', '')
        source_lang = data.get('source_lang', 'en')
        target_lang = data.get('target_lang', 'ro')
        
        if not original_text or not translated_text:
            return jsonify({'error': 'Missing text for validation'}), 400
        
        print(f"\n[VALIDATE] {source_lang} → {target_lang}")
        print(f"[VALIDATE] Text: {original_text[:100]}...")
        
        system = get_subtitle_system()
        
        if not system.llm_validator:
            return jsonify({'error': 'LLM validator not available'}), 503
        
        result = system.llm_validator.validate_translation(
            original_text=original_text,
            translated_text=translated_text,
            source_lang=source_lang,
            target_lang=target_lang,
            use_streaming=False
        )
        
        response = {
            'status': 'success',
            'original': result.original_text,
            'initial_translation': result.initial_translation,
            'validated_translation': result.validated_translation,
            'confidence': result.confidence_score,
            'model_used': result.model_used,
            'validation_time': f"{result.validation_time:.2f}s"
        }
        
        print(f"[VALIDATE] ✅ Complete - Confidence: {result.confidence_score:.1%}")
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"[VALIDATE] ERROR: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================
# CATEGORIA I: ANALIZĂ DOCUMENTE
# ============================================

@app.route('/api/ppt-analysis', methods=['POST'])
def ppt_analysis():
    """I.1: Analiză PowerPoint"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not validate_file(file, 'ppt'):
            return jsonify({'error': 'Invalid file type'}), 400
        
        filename = generate_unique_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        print(f"\n[PPT] Processing: {filename}")
        
        analyzer = PPTAnalyzer()
        result = analyzer.analyze(filepath)
        
        response_payload = {
            'service': 'PowerPoint Analysis',
            'originalFile': filename,
            'downloadUrl': result.get('output_file', ''),
            'status': 'success',
            **result
        }
        add_history('ppt-analysis', filename, response_payload.get('downloadUrl'))
        return jsonify(response_payload), 200
        
    except Exception as e:
        print(f"[PPT] ERROR: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/document-analysis', methods=['POST'])
def document_analysis():
    """I.2: Analiză Word/PDF/eBook"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not validate_file(file, 'document'):
            return jsonify({'error': 'Invalid file type'}), 400
        
        filename = generate_unique_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        print(f"\n[DOC] Processing: {filename}")
        
        parser = DocumentParser()
        result = parser.parse(filepath)
        
        response_payload = {
            'service': 'Document Analysis',
            'originalFile': filename,
            'downloadUrl': result.get('output_file', ''),
            'status': 'success',
            **result
        }
        add_history('document-analysis', filename, response_payload.get('downloadUrl'))
        return jsonify(response_payload), 200
        
    except Exception as e:
        print(f"[DOC] ERROR: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/image-ocr', methods=['POST'])
def image_ocr():
    """I.3: OCR Imagini"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not validate_file(file, 'image'):
            return jsonify({'error': 'Invalid file type'}), 400
        
        filename = generate_unique_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        print(f"\n[OCR] Processing: {filename}")
        
        ocr = ImageOCR()
        result = ocr.extract_text(filepath)
        
        response_payload = {
            'service': 'Image OCR',
            'originalFile': filename,
            'downloadUrl': result.get('output_file', ''),
            'status': 'success',
            **result
        }
        add_history('image-ocr', filename, response_payload.get('downloadUrl'))
        return jsonify(response_payload), 200
        
    except Exception as e:
        print(f"[OCR] ERROR: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================
# CATEGORIA II: TRADUCERE
# ============================================

@app.route('/api/translate-document', methods=['POST'])
def translate_doc():
    """II.1: Traducere Documente"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        src_lang = request.form.get('src_lang', 'auto').lower()
        
        if not validate_file(file, 'translate-doc'):
            return jsonify({'error': 'Invalid file type'}), 400
        
        filename = generate_unique_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        print(f"\n[TRANSLATE DOC] {src_lang.upper()} → RO: {filename}")

        result = translate_document(filepath, src_lang=src_lang, dest_lang='ro')

        # --- 👇 CORECȚIE APLICATĂ 👇 ---
        
        # 1. Obține calea completă din cheia corectă
        output_path = result.get('output_path', '') 
        
        # 2. Extrage doar numele fișierului
        output_filename = os.path.basename(output_path)
        
        # 3. Construiește URL-ul relativ pentru download
        download_url = f"/download/{output_filename}" if output_filename else ""

        # 4. Trimite un JSON curat
        response_data = {
            'service': 'Document Translation',
            'originalFile': filename,
            'originalLanguage': src_lang.upper(),
            'translatedLanguage': 'RO',
            'downloadUrl': download_url, # <-- Aici este URL-ul corect
            'status': 'success',
            # Adaugă alte chei utile din 'result'
            'total_pages': result.get('total_pages'),
            'translated_blocks': result.get('translated_blocks')
        }

        add_history('translate-document', filename, response_data.get('downloadUrl'), meta={'source_lang': src_lang, 'target_lang': 'ro'})
        return jsonify(response_data), 200
        # --- 👆 Sfârșitul corecției 👆 ---
        
    except Exception as e:
        print(f"[TRANSLATE DOC] ERROR: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/translate-audio', methods=['POST'])
def translate_audio():
    """II.2: Traducere Audio"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        src_lang = request.form.get('src_lang', 'auto').lower()
        
        if not validate_file(file, 'translate-audio'):
            return jsonify({'error': 'Invalid file type'}), 400
        
        filename = generate_unique_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        print(f"\n[TRANSLATE AUDIO] {src_lang.upper()} → RO: {filename}")
        
        translator = AudioTranslator()
        result = translator.translate(filepath, src_lang=src_lang, dest_lang='ro')
        
        response_payload = {
            'service': 'Audio Translation',
            'originalFile': filename,
            'originalLanguage': src_lang.upper(),
            'translatedLanguage': 'RO',
            'downloadUrl': result.get('audio_file', ''),
            'summaryUrl': result.get('summary_file', ''),
            'status': 'success',
            **result
        }
        add_history(
            'translate-audio',
            filename,
            response_payload.get('downloadUrl'),
            meta={'detected': result.get('detected_lang'), 'target_lang': 'ro'},
            summary_url=response_payload.get('summaryUrl') or result.get('summary_file'),
            summary_text=result.get('summary_text') or ""
        )
        return jsonify(response_payload), 200
        
    except Exception as e:
        print(f"[TRANSLATE AUDIO] ERROR: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/translate-video', methods=['POST'])
def translate_video():
    """II.3: Traducere Video"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        src_lang = request.form.get('src_lang', 'en').lower()
        
        if not validate_file(file, 'translate-video'):
            return jsonify({'error': 'Invalid file type'}), 400
        
        filename = generate_unique_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        print(f"\n[TRANSLATE VIDEO] {src_lang.upper()} → RO: {filename}")
        
        translator = VideoTranslator()
        result = translator.translate(filepath, src_lang=src_lang, dest_lang='ro')
        
        response_payload = {
            'service': 'Video Translation',
            'originalFile': filename,
            'originalLanguage': src_lang.upper(),
            'translatedLanguage': 'RO',
            'downloadUrl': result.get('download_url') or result.get('video_file', ''),
            'transcript': result.get('transcript', ''),
            'insight': result.get('insight', ''),
            'summary': result.get('summary', ''),
            'status': 'success',
            **result
        }
        add_history(
            'translate-video',
            filename,
            response_payload.get('downloadUrl'),
            meta={'target_lang': 'ro'},
            summary_url=response_payload.get('downloadUrl'),
            summary_text=result.get('summary') or result.get('insight') or result.get('transcript', "")
        )
        return jsonify(response_payload), 200
    
    except Exception as e:
        print(f"[TRANSLATE VIDEO] ERROR: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/translate-video-url', methods=['POST'])
def translate_video_url():
    """II.3: Traducere Video din link (YouTube/Rutube)"""
    try:
        data = request.get_json()
        url = data.get('url')
        if not url or not validate_video_url(url):
            return jsonify({'error': 'Link invalid (acceptat: youtube sau rutube)'}), 400

        try:
            filepath = download_video_from_url(url, UPLOAD_FOLDER, prefix="transvid")
        except Exception as e:
            return jsonify({'error': f'Eșec descărcare: {e}'}), 400
        filename = Path(filepath).name

        print(f"\n[TRANSLATE VIDEO URL] AUTO → RO: {url}")

        translator = VideoTranslator()
        result = translator.translate(filepath, src_lang='auto', dest_lang='ro')

        response_payload = {
            'service': 'Video Translation',
            'originalFile': filename,
            'originalLanguage': result.get('detected_language', 'auto').upper() if 'detected_language' in result else 'AUTO',
            'translatedLanguage': 'RO',
            'downloadUrl': result.get('download_url') or result.get('video_file', ''),
            'transcript': result.get('transcript', ''),
            'insight': result.get('insight', ''),
            'summary': result.get('summary', ''),
            'status': 'success',
            **result
        }
        add_history(
            'translate-video',
            filename,
            response_payload.get('downloadUrl'),
            meta={'target_lang': 'ro', 'url': url},
            summary_url=response_payload.get('downloadUrl'),
            summary_text=result.get('summary') or result.get('insight') or result.get('transcript', "")
        )
        return jsonify(response_payload), 200

    except Exception as e:
        print(f"[TRANSLATE VIDEO URL] ERROR: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================
# CATEGORIA III: SUBTITRARE
# ============================================

@app.route('/api/subtitle-ro', methods=['POST'])
def subtitle_ro():
    """III.1: Subtitrare RO"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        attach_mode = request.form.get('attach', 'soft')
        detail_level = request.form.get('detail_level', 'medium')
        translator_mode = request.form.get('translator_mode', 'cloud')
        
        if not validate_file(file, 'subtitle'):
            return jsonify({'error': 'Invalid file type'}), 400
        
        filename = generate_unique_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        print(f"\n[SUBTITLE] Mode: {attach_mode}, Detail: {detail_level}, File: {filename}")
        
        generator = SubtitleGenerator()
        result = generator.generate(filepath, lang='ro', attach_mode=attach_mode, detail_level=detail_level, translator_mode=translator_mode)
        
        response_payload = {
            'service': 'Subtitle Generation',
            'originalFile': filename,
            'downloadUrl': result.get('video_file', ''),
            'summaryUrl': result.get('summary_file', ''),
            'subtitleUrl': result.get('subtitle_file', ''),
            'status': 'success',
            **result
        }
        add_history(
            'subtitle-ro',
            filename,
            response_payload.get('downloadUrl'),
            meta={
                'attach': attach_mode,
                'detail': detail_level,
                'translator_mode': translator_mode,
                'subtitle_url': response_payload.get('subtitleUrl')
            },
            summary_url=response_payload.get('summaryUrl') or result.get('summary_file'),
            summary_text=result.get('summary_text') or ""
        )
        return jsonify(response_payload), 200
        
    except Exception as e:
        print(f"[SUBTITLE] ERROR: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/redub-video', methods=['POST'])
def redub_video():
    """III.2: Redublare Video cu detectare automată a limbii și TTS local (RTX-ready)."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        voice_sample = request.files.get('voice_sample')  # opțional pentru voice cloning
        dest_lang = request.form.get('dest_lang', 'ro').lower()
        translator_mode = request.form.get('translator_mode', 'cloud').lower()
        detail_level = request.form.get('detail_level', 'medium')
        
        if not validate_file(file, 'redub'):
            return jsonify({'error': 'Invalid file type'}), 400
        
        filename = generate_unique_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        speaker_wav_path = None
        if voice_sample:
            speaker_name = f"{Path(filename).stem}_voice.wav"
            speaker_wav_path = os.path.join(UPLOAD_FOLDER, speaker_name)
            voice_sample.save(speaker_wav_path)
        
        print(f"\n[REDUB] AUTO → {dest_lang.upper()}: {filename}")
        
        redubber = VideoRedubber()
        result = redubber.redub(filepath, dest_lang=dest_lang, speaker_wav=speaker_wav_path, translator_mode=translator_mode)
        
        response_payload = {
            'service': 'Video Redub',
            'originalFile': filename,
            'originalLanguage': result.get('detected_language', 'auto').upper(),
            'targetLanguage': dest_lang.upper(),
            'downloadUrl': result.get('video_file', ''),
            'subtitleUrl': result.get('subtitle_file', ''),
            'summaryUrl': result.get('summary_file', ''),
            'detailLevel': detail_level,
            'status': 'success',
            **result
        }
        add_history(
            'redub-video',
            filename,
            response_payload.get('downloadUrl'),
            meta={
                'target_lang': dest_lang,
                'translator_mode': translator_mode,
                'detail_level': detail_level,
                'subtitle_url': response_payload.get('subtitleUrl')
            },
            summary_url=response_payload.get('summaryUrl') or result.get('summary_file'),
            summary_text=result.get('summary_text') or ""
        )
        return jsonify(response_payload), 200
        
    except Exception as e:
        print(f"[REDUB] ERROR: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/redub-video-url', methods=['POST'])
def redub_video_url():
    """III.2: Redublare Video din link (YouTube/Rutube)"""
    try:
        data = request.get_json()
        url = data.get('url')
        dest_lang = data.get('dest_lang', 'ro').lower()
        translator_mode = data.get('translator_mode', 'cloud').lower()
        detail_level = data.get('detail_level', 'medium')
        if not url or not validate_video_url(url):
            return jsonify({'error': 'Link invalid (acceptat: youtube sau rutube)'}), 400
        try:
            filepath = download_video_from_url(url, UPLOAD_FOLDER, prefix="redub")
        except Exception as e:
            return jsonify({'error': f'Eșec descărcare: {e}'}), 400
        filename = Path(filepath).name

        print(f"\n[REDUB URL] AUTO → {dest_lang.upper()}: {url}")

        redubber = VideoRedubber()
        result = redubber.redub(filepath, dest_lang=dest_lang, speaker_wav=None, translator_mode=translator_mode)

        response_payload = {
            'service': 'Video Redub',
            'originalFile': filename,
            'originalLanguage': result.get('detected_language', 'auto').upper(),
            'targetLanguage': dest_lang.upper(),
            'downloadUrl': result.get('video_file', ''),
            'subtitleUrl': result.get('subtitle_file', ''),
            'summaryUrl': result.get('summary_file', ''),
            'detailLevel': detail_level,
            'status': 'success',
            **result
        }
        add_history(
            'redub-video',
            filename,
            response_payload.get('downloadUrl'),
            meta={
                'target_lang': dest_lang,
                'url': url,
                'translator_mode': translator_mode,
                'detail_level': detail_level,
                'subtitle_url': response_payload.get('subtitleUrl')
            },
            summary_url=response_payload.get('summaryUrl') or result.get('summary_file'),
            summary_text=result.get('summary_text') or ""
        )
        return jsonify(response_payload), 200
    except Exception as e:
        print(f"[REDUB URL] ERROR: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================
# CATEGORIA IV: LIVE SUBTITLE
# ============================================

@app.route('/api/live-start', methods=['POST'])
def live_start():
    """IV: Start Live Session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        participants = data.get('participants', [])
        
        if not session_id:
            return jsonify({'error': 'session_id required'}), 400
        
        print(f"\n[LIVE] Starting: {session_id}")
        
        # result = live_engine.start_session(session_id, participants)
        
        return jsonify({
            'service': 'Live Subtitle',
            'sessionId': session_id,
            'status': 'started',
            # **result
        }), 200
        
    except Exception as e:
        print(f"[LIVE] ERROR: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/live-stop', methods=['POST'])
def live_stop():
    """IV: Stop Live Session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'session_id required'}), 400
        
        print(f"\n[LIVE] Stopping: {session_id}")
        
        # result = live_engine.stop_session(session_id)
        
        return jsonify({
            'service': 'Live Subtitle',
            'sessionId': session_id,
            'status': 'stopped',
            # **result
        }), 200
        
    except Exception as e:
        print(f"[LIVE] ERROR: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================
# DOWNLOAD
# ============================================

@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """Download fișier procesat"""
    try:
        for folder in [PROCESSED_FOLDER, UPLOAD_FOLDER]:
            filepath = os.path.join(folder, filename)
            if os.path.exists(filepath):
                print(f"[DOWNLOAD] ✅ {filepath}")
                return send_file(filepath, as_attachment=True)
        
        print(f"[DOWNLOAD] ❌ 404 -> {filename}")
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        print(f"[DOWNLOAD] ERROR: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Max 30GB'}), 413

@app.errorhandler(500)
def internal_error(e):
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/subtitle-ro-url', methods=['POST'])
def subtitle_ro_url():
    """III.1: Subtitrare RO din link (YouTube/Rutube)"""
    try:
        data = request.get_json()
        url = data.get('url')
        attach_mode = data.get('attach', 'soft')
        detail_level = data.get('detail_level', 'medium')
        translator_mode = data.get('translator_mode', 'cloud')
        if not url or not validate_video_url(url):
            return jsonify({'error': 'Link invalid (acceptat: youtube sau rutube)'}), 400
        try:
            filepath = download_video_from_url(url, UPLOAD_FOLDER, prefix="subtitle")
        except Exception as e:
            return jsonify({'error': f'Eșec descărcare: {e}'}), 400
        filename = Path(filepath).name
        print(f"\n[SUBTITLE URL] Mode: {attach_mode}, Detail: {detail_level}, URL: {url}")

        generator = SubtitleGenerator()
        result = generator.generate(filepath, lang='ro', attach_mode=attach_mode, detail_level=detail_level, translator_mode=translator_mode)

        response_payload = {
            'service': 'Subtitle Generation',
            'originalFile': filename,
            'downloadUrl': result.get('video_file', ''),
            'summaryUrl': result.get('summary_file', ''),
            'subtitleUrl': result.get('subtitle_file', ''),
            'status': 'success',
            **result
        }
        add_history(
            'subtitle-ro',
            filename,
            response_payload.get('downloadUrl'),
            meta={
                'attach': attach_mode,
                'detail': detail_level,
                'url': url,
                'translator_mode': translator_mode,
                'subtitle_url': response_payload.get('subtitleUrl')
            },
            summary_url=response_payload.get('summaryUrl') or result.get('summary_file'),
            summary_text=result.get('summary_text') or ""
        )
        return jsonify(response_payload), 200
    except Exception as e:
        print(f"[SUBTITLE URL] ERROR: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

# ============================================
# PORNIRE SERVER
# ============================================

if __name__ == '__main__':
    fix_encoding()
    
    print("\n" + "="*60)
    print("🚀 SISTEM AI INTEGRAT v2.0")
    print("="*60)
    print(f"📂 Upload: {UPLOAD_FOLDER}")
    print(f"📂 Processed: {PROCESSED_FOLDER}")
    print(f"🌐 Server: http://localhost:5000")
    print(f"✅ Health: http://localhost:5000/api/health")
    print("\n📋 Endpoints:")
    print("   • /api/health               - Health check")
    print("   • /api/llm-status           - LLM server status")
    print("   • /api/validate-translation - LLM validation")
    print("   • /api/ppt-analysis         - PowerPoint")
    print("   • /api/document-analysis    - Word/PDF/eBook")
    print("   • /api/image-ocr            - OCR Imagini")
    print("   • /api/translate-document   - Traducere Doc")
    print("   • /api/translate-audio      - Traducere Audio")
    print("   • /api/translate-video      - Traducere Video")
    print("   • /api/subtitle-ro          - Subtitrare RO")
    print("   • /api/redub-video          - Redublare Video")
    print("   • /api/live-start           - Live Start")
    print("   • /api/live-stop            - Live Stop")
    print("="*60 + "\n")

    socketio.run(
        app,
        debug=True,
        host='0.0.0.0',
        port=5000,
        allow_unsafe_werkzeug=True
    )
