from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from numpy import fix
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import json, sys, io

# from services.whisper_ro import transcribe_ro_file #type: ignore
# from services.subtitle_attacher import attach_subtitle_soft, attach_subtitle_hard #type: ignore

# # Import servicii
# from services.document_parser import parse_document #type: ignore
# from services.vosk_transcriber import transcribe_and_generate_srt #type: ignore
# from services.translator import translate_text #type: ignore
# from services.subtitle_attacher import attach_subtitle_soft, attach_subtitle_hard, get_video_info #type: ignore
# from services.subtitle_attacher import attach_subtitle_soft, get_video_info #type: ignore
# from services.vosk_transcriber import transcribe_and_generate_srt, generate_srt #type: ignore
# from services.document_translator import translate_document #type: ignore
# from services.document_translator import translate_document #type: ignore


# Modificări pentru app.py - adaugă după importurile existente:

from backend.subtitles.sub import OptimizedSubtitleSystem

from pathlib import Path
import traceback

# Inițializează sistemul de subtitrare global (pentru a evita reîncărcarea modelelor)
subtitle_system = None

def get_subtitle_system():
    """Singleton pentru sistemul de subtitrare"""
    global subtitle_system
    if subtitle_system is None:
        subtitle_system = OptimizedSubtitleSystem(
            use_gpu=True,
            use_llm_validation=True  # Activează validarea LLM
        )
    return subtitle_system

# Modifică endpoint-ul /api/subtitles pentru a folosi noul sistem:



def fix_encoding():
    """Fix pentru encoding UTF-8 pe Windows - versiune sigură"""
    try:
        # Încearcă să seteze encoding doar dacă e necesar
        if sys.platform == 'win32':
            # Verifică dacă stdout/stderr au atributul buffer
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            else:
                # Fallback: setează encoding prin variabile de mediu
                import os
                os.environ['PYTHONIOENCODING'] = 'utf-8'
                print("[ENCODING] UTF-8 setat prin variabile de mediu")
            
            if hasattr(sys.stderr, 'buffer'):
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
            
            print("[ENCODING] ✅ UTF-8 encoding configurat pentru Windows")
    except Exception as e:
        print(f"[ENCODING] ⚠️ Nu s-a putut seta encoding: {e}")
        print("[ENCODING] Continuă cu encoding-ul default...")

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {
    'document-parse': {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png'},
    'translation': {'pdf', 'docx', 'pptx'},
    'audio-translation': {'mp3', 'wav', 'm4a', 'ogg'},
    'video-translation': {'mp4', 'avi', 'mov', 'mkv'},
    'video-subtitle': {'mp4', 'avi', 'mov', 'mkv'},
    'video-audio-replace': {'mp4', 'avi', 'mov', 'mkv'},
    'summary-generation': {'mp3', 'mp4', 'wav', 'avi', 'mov'}
}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 30000 * 1024 * 1024  # 30GB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def allowed_file(filename, service):
    if '.' not in filename:
        return False
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS.get(service, set())


# TO DO: Genereaza nume sugestive pentru fisierele uploadate
def generate_unique_filename(original_filename):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    name, ext = os.path.splitext(original_filename)
    return f"{timestamp}_{unique_id}_{secure_filename(name)}{ext}"

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'online',
        'message': 'Backend server is running',
        'timestamp': datetime.now().isoformat()
    }), 200

# Endpoint nou pentru validare separată a traducerilor existente
@app.route('/api/validate-translation', methods=['POST'])
def validate_translation():
    """
    Validează și îmbunătățește traduceri existente cu LLM
    """
    try:
        data = request.get_json()
        
        original_text = data.get('original_text', '')
        translated_text = data.get('translated_text', '')
        source_lang = data.get('source_lang', 'en')
        target_lang = data.get('target_lang', 'ro')
        
        if not original_text or not translated_text:
            return jsonify({'error': 'Missing text for validation'}), 400
        
        print(f"\n[API] Validare traducere cu LLM")
        print(f"[API] {source_lang} → {target_lang}")
        print(f"[API] Text original: {original_text[:100]}...")
        
        # Obține sistemul și validează
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
        
        print(f"[API] ✅ Validare completă")
        print(f"[API] Încredere: {result.confidence_score:.1%}")
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"[API] Eroare validare: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/llm-status', methods=['GET'])
def llm_status():
    """Verifică statusul serverului LLM"""
    try:
        import requests
        
        OLLAMA_URL = "http://86.126.134.77:11434"
        
        # Test conexiune Ollama
        response = requests.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=5
        )
        
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

# @app.route('/api/translation', methods=['POST'])
# def translation():
#     """Translate documents (PDF, Word, PowerPoint)"""
#     try:
#         if 'file' not in request.files:
#             return jsonify({'error': 'No file provided'}), 400
        
#         file = request.files['file']
#         service = request.form.get('service', 'translation')
        
#         if file.filename == '':
#             return jsonify({'error': 'No file selected'}), 400
        
#         if not allowed_file(file.filename, service):
#             return jsonify({'error': 'File type not allowed'}), 400
        
#         filename = generate_unique_filename(file.filename)
#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(filepath)
        
#         # Parametri traducere
#         src_lang = request.form.get('src_lang', 'en')  # en, zh, ru, ja
#         dest_lang = 'ro'  # Întotdeauna către română
        
#         print(f"\n{'='*60}")
#         print(f"[Translation] Processing: {filename}")
#         print(f"[Translation] Language: {src_lang} → {dest_lang}")
#         print(f"{'='*60}\n")
        
#         # Traduce documentul
#         result = translate_document(filepath, src_lang=src_lang, dest_lang=dest_lang)
        
#         # Info pentru frontend
#         file_ext = filename.rsplit('.', 1)[-1].lower()
#         output_name = os.path.basename(result['output_path'])
        
#         response = {
#             'originalLanguage': src_lang.upper(),
#             'translatedLanguage': dest_lang.upper(),
#             'originalFile': filename,
#             'translatedFile': output_name,
#             'fileType': file_ext,
#             'outputFileName': output_name,
#             'downloadUrl': output_name,
#             'status': 'success',
#             'timestamp': datetime.now().isoformat()
#         }
        
#         # Adaugă statistici specifice tipului de document
#         if 'translated_paragraphs' in result:
#             response['totalParagraphs'] = result['translated_paragraphs']
#         if 'translated_items' in result:
#             response['totalItems'] = result['translated_items']
#         if 'total_pages' in result:
#             response['totalPages'] = result['total_pages']
#         if 'total_slides' in result:
#             response['totalSlides'] = result['total_slides']
        
#         print(f"\n{'='*60}")
#         print(f"[Translation] SUCCESS")
#         print(f"[Translation] Output: {output_name}")
#         print(f"{'='*60}\n")
        
#         return jsonify(response), 200
        
#     except Exception as e:
#         import traceback
#         print(f"\n{'='*60}")
#         print(f"[Translation] ERROR")
#         print(f"[Translation] Error: {e}")
#         traceback.print_exc()
#         print(f"{'='*60}\n")
#         return jsonify({'error': str(e)}), 500

@app.route('/api/summarise', methods=['POST'])
def document_summarise():
    """Process and classify documents"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        service = request.form.get('service', 'document-parse')
        if not allowed_file(file.filename, service):
            return jsonify({'error': 'File type not allowed'}), 400

        filename = generate_unique_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        result = parse_document(filepath)
        result['outputFileName'] = f'parsed_{filename}'
        result['downloadUrl'] = filename
        result['status'] = 'success'
        result['timestamp'] = datetime.now().isoformat()

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/subtitles', methods=['POST'])
def subtitles():
    """
    Generare subtitrări cu validare LLM opțională
    Suportă: RO, EN, ZH, JA, RU
    """
    try:
        # 0) Upload & validări
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        service = request.form.get('service', 'video-subtitle')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename, service):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Salvare fișier
        filename = generate_unique_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Parametri subtitrare
        src_lang = request.form.get('src_lang', 'auto').lower()
        dest_lang = request.form.get('dest_lang', 'ro').lower()
        use_llm = request.form.get('use_llm', 'true').lower() == 'true'
        double_validation = request.form.get('double_validation', 'false').lower() == 'true'
        
        print(f"\n{'='*60}")
        print(f"[API] SUBTITRARE CU VALIDARE LLM")
        print(f"[API] Fișier: {filename}")
        print(f"[API] Limbă sursă: {src_lang}")
        print(f"[API] Limbă țintă: {dest_lang}")
        print(f"[API] Validare LLM: {use_llm}")
        print(f"[API] Validare dublă: {double_validation}")
        print(f"{'='*60}\n")
        
        # Obține sistemul de subtitrare
        system = get_subtitle_system()
        
        # Procesare video
        result = system.process_video_complete(
            video_path=filepath,
            source_lang=src_lang if src_lang != 'auto' else None,
            target_lang=dest_lang,
            output_dir=app.config['PROCESSED_FOLDER'],
            subtitle_format='srt',
            model_size='large-v3',
            auto_detect_language=(src_lang == 'auto'),
            use_llm_validation=use_llm,
            double_validation=double_validation
        )
        
        # Pregătește răspunsul
        subtitle_file = os.path.basename(result['output'])
        
        # Citește câteva linii din subtitrare pentru preview
        preview_lines = []
        try:
            with open(result['output'], 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
                # Ia primele 3 subtitrări pentru preview
                for i in range(min(12, len(lines))):  # 12 linii = ~3 subtitrări
                    if lines[i].strip():
                        preview_lines.append(lines[i].strip())
        except:
            preview_lines = []
        
        response = {
            'status': 'success',
            'originalLanguage': src_lang,
            'targetLanguage': dest_lang,
            'subtitleFile': subtitle_file,
            'downloadUrl': subtitle_file,
            'totalSegments': result['segments'],
            'processingTime': f"{result['time']:.1f}s",
            'llmValidated': result.get('llm_validated', False),
            'doubleValidated': result.get('double_validated', False),
            'preview': preview_lines[:9],  # Primele 3 subtitrări
            'outputFileName': subtitle_file,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\n{'='*60}")
        print(f"[API] SUCCES - Subtitrare generată")
        print(f"[API] Fișier: {subtitle_file}")
        print(f"[API] Segmente: {result['segments']}")
        print(f"[API] Timp procesare: {result['time']:.1f}s")
        if result.get('llm_validated'):
            print(f"[API] ✅ Validare LLM aplicată")
        print(f"{'='*60}\n")
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"[API] EROARE în generare subtitrări")
        print(f"[API] Eroare: {e}")
        traceback.print_exc()
        print(f"{'='*60}\n")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dubbing', methods=['POST'])
def video_dubbing():
    """
    Generează SRT românesc din Whisper și atașează subtitrarea în video.
    Răspunde cu numele FIȘIERULUI NOU din processed/, nu cu originalul.
    """
    try:
        # 0) Upload & validări
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        service = request.form.get('service', 'video-subtitle')

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # dacă ai un helper allowed_file(filename, service), păstrează-l:
        if not allowed_file(file.filename, service):
            return jsonify({'error': 'File type not allowed'}), 400

        filename = generate_unique_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        print(f"\n{'='*60}")
        print(f"[API] Video Subtitle - START")
        print(f"[API] Fișier salvat: {filepath}")
        print(f"{'='*60}\n")

       # Mod atașare: soft by default
        attach_mode = request.form.get('attach', 'soft')
        print(f"[API] Mod atașare: {attach_mode}")

        # Generează SRT cu Whisper RO
        print(f"[API] STEP 1: Generare SRT cu Whisper...")
        res = transcribe_ro_file(filepath)
        srt_path = res.get('srt_path')
        
        if not srt_path or not os.path.exists(srt_path):
            return jsonify({'error': 'Transcrierea nu a generat fișier SRT'}), 500
        
        print(f"[API] ✅ SRT generat: {srt_path}")

        # Atașează subtitrarea în video
        print(f"[API] STEP 2: Atașare subtitrare în video ({attach_mode})...")
        
        if attach_mode == 'hard':
            attach_result = attach_subtitle_hard(filepath, srt_path)
        else:
            attach_result = attach_subtitle_soft(filepath, srt_path, subtitle_lang="ro")

        out_path = attach_result.get("output_path")
        
        if not out_path or not os.path.exists(out_path):
            return jsonify({'error': f'Nu s-a generat fișierul video cu subtitrare. Path: {out_path}'}), 500
        
        out_name = os.path.basename(out_path)
        print(f"[API] ✅ Video cu subtitrare generat: {out_path}")
        print(f"[API] Nume fișier pentru download: {out_name}")

        # Info video (opțional)
        info = get_video_info(filepath) or {}

        # Răspuns: indică FIȘIERUL NOU din processed/
        response = {
            'duration': info.get('duration', 0),
            'resolution': info.get('resolution', 'unknown'),
            'subtitleFile': os.path.basename(srt_path),
            'subtitledVideo': out_name,
            'totalSubtitles': len(res.get('segments', [])),
            'outputFileName': out_name,
            'downloadUrl': out_name,  # CRITICAL: Numele fișierului din processed/
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\n{'='*60}")
        print(f"[API] Video Subtitle - SUCCESS")
        print(f"[API] downloadUrl: {response['downloadUrl']}")
        print(f"[API] Fișier procesat: {out_path}")
        print(f"{'='*60}\n")
        
        return jsonify(response), 200

    except Exception as e:
        import traceback
        print(f"\n{'='*60}")
        print(f"[API] Video Subtitle - ERROR")
        print(f"[API] Eroare: {e}")
        traceback.print_exc()
        print(f"{'='*60}\n")
        return jsonify({'error': str(e)}), 500


@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """Download processed file"""
    try:
        # Căutăm întâi în processed/, apoi în uploads/
        for folder in [app.config['PROCESSED_FOLDER'], app.config['UPLOAD_FOLDER']]:
            filepath = os.path.join(folder, filename)
            if os.path.exists(filepath):
                print(f"[DOWNLOAD] OK -> {filepath}")
                return send_file(filepath, as_attachment=True)

        print(f"[DOWNLOAD] 404 -> {filename}  (checked {app.config['PROCESSED_FOLDER']} and {app.config['UPLOAD_FOLDER']})")
        return jsonify({'error': 'File not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File is too large. Maximum size is 500MB'}), 413

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    fix_encoding()
    print("=" * 60)
    print("🚀 Document Processing Backend Server")
    print("=" * 60)
    print(f"📂 Upload folder: {UPLOAD_FOLDER}")
    print(f"📂 Processed folder: {PROCESSED_FOLDER}")
    print(f"🌐 Server running on: http://localhost:5000")
    print(f"✅ Health check: http://localhost:5000/api/health")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)