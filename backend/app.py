from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import json, sys, io
from services.whisper_ro import transcribe_ro_file
from services.subtitle_attacher import attach_subtitle_soft, attach_subtitle_hard

# Import servicii
from services.document_parser import parse_document
from services.vosk_transcriber import transcribe_and_generate_srt
from services.translator import translate_text
from services.subtitle_attacher import attach_subtitle_soft, attach_subtitle_hard, get_video_info
from services.subtitle_attacher import attach_subtitle_soft, get_video_info
from services.vosk_transcriber import transcribe_and_generate_srt, generate_srt
from services.document_translator import translate_document
from services.document_translator import translate_document

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


@app.route('/api/translation', methods=['POST'])
def translation():
    """Translate documents (PDF, Word, PowerPoint)"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        service = request.form.get('service', 'translation')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename, service):
            return jsonify({'error': 'File type not allowed'}), 400
        
        filename = generate_unique_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Parametri traducere
        src_lang = request.form.get('src_lang', 'en')  # en, zh, ru, ja
        dest_lang = 'ro'  # Întotdeauna către română
        
        print(f"\n{'='*60}")
        print(f"[Translation] Processing: {filename}")
        print(f"[Translation] Language: {src_lang} → {dest_lang}")
        print(f"{'='*60}\n")
        
        # Traduce documentul
        result = translate_document(filepath, src_lang=src_lang, dest_lang=dest_lang)
        
        # Info pentru frontend
        file_ext = filename.rsplit('.', 1)[-1].lower()
        output_name = os.path.basename(result['output_path'])
        
        response = {
            'originalLanguage': src_lang.upper(),
            'translatedLanguage': dest_lang.upper(),
            'originalFile': filename,
            'translatedFile': output_name,
            'fileType': file_ext,
            'outputFileName': output_name,
            'downloadUrl': output_name,
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        }
        
        # Adaugă statistici specifice tipului de document
        if 'translated_paragraphs' in result:
            response['totalParagraphs'] = result['translated_paragraphs']
        if 'translated_items' in result:
            response['totalItems'] = result['translated_items']
        if 'total_pages' in result:
            response['totalPages'] = result['total_pages']
        if 'total_slides' in result:
            response['totalSlides'] = result['total_slides']
        
        print(f"\n{'='*60}")
        print(f"[Translation] SUCCESS")
        print(f"[Translation] Output: {output_name}")
        print(f"{'='*60}\n")
        
        return jsonify(response), 200
        
    except Exception as e:
        import traceback
        print(f"\n{'='*60}")
        print(f"[Translation] ERROR")
        print(f"[Translation] Error: {e}")
        traceback.print_exc()
        print(f"{'='*60}\n")
        return jsonify({'error': str(e)}), 500

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
    Transcriere + (opțional) traducere audio în română.
    - RO: Whisper segmentat -> SRT + transcript TXT
    - EN/RU/JA/ZH: Vosk -> SRT original + segmente -> Translate -> SRT românesc
    Returnează un fișier REAL descărcabil din processed/.
    """
    try:
        # 0) Upload & validări
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        file = request.files['file']
        service = request.form.get('service', 'audio-translation')
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not allowed_file(file.filename, service):
            return jsonify({'error': 'File type not allowed'}), 400

        filename = generate_unique_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        src_lang = request.form.get('lang', 'en').lower()

        # 1) Cazul română: Whisper -> SRT + TXT
        if src_lang == 'ro':
            print("[API] Audio RO -> folosim Whisper")
            res = transcribe_ro_file(filepath)  # {"segments":[...], "srt_path":"..."}
            srt_path = res.get('srt_path')
            if not srt_path or not os.path.exists(srt_path):
                return jsonify({'error': 'Transcrierea nu a generat fișier SRT'}), 500

            # Transcript TXT
            base = os.path.splitext(os.path.basename(srt_path))[0]
            txt_path = os.path.join(app.config['PROCESSED_FOLDER'], f"{base}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                for seg in res.get('segments', []):
                    start = float(seg.get('start', 0))
                    end = float(seg.get('end', 0))
                    text = (seg.get('text') or '').strip()
                    f.write(f"[{start:.2f}-{end:.2f}] {text}\n")

            return jsonify({
                'originalLanguage': 'ro',
                'subtitleFile': os.path.basename(srt_path),
                'transcriptFile': os.path.basename(txt_path),
                'totalSegments': len(res.get('segments', [])),
                'downloadUrl': os.path.basename(srt_path),   # livrăm ceva real din processed/
                'outputFileName': os.path.basename(srt_path),
                'status': 'success'
            }), 200

        # 2) Alte limbi: Vosk -> segmente + SRT, apoi Translate -> SRT românesc
        if src_lang not in ['en', 'ru', 'ja', 'zh']:
            return jsonify({'error': f'Limba {src_lang} nu este suportată. Limbi: en, ru, ja, zh, ro'}), 400

        vosk_result = transcribe_and_generate_srt(filepath, lang=src_lang)
        segments = vosk_result.get('segments', [])

        translated_segments = []
        for seg in segments:
            txt = seg.get('text') or ''
            translated_segments.append({
                'start': float(seg.get('start', 0)),
                'end': float(seg.get('end', 0)),
                'text': translate_text(txt, src_lang, 'ro') if txt else ''
            })

        # Generăm SRT tradus
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        translated_srt = os.path.join(app.config['PROCESSED_FOLDER'], f"{base_name}_RO.srt")
        generate_srt(translated_segments, translated_srt)  # așteaptă [{start,end,text}, ...]

        return jsonify({
            'originalLanguage': src_lang,
            'translatedLanguage': 'ro',
            'originalSrt': os.path.basename(vosk_result.get('srt_path', '')),
            'translatedSrt': os.path.basename(translated_srt),
            'totalSegments': len(translated_segments),
            'downloadUrl': os.path.basename(translated_srt),
            'outputFileName': os.path.basename(translated_srt),
            'status': 'success'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dubbing', methods=['POST'])
def video_subtitle():
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
    print("=" * 60)
    print("🚀 Document Processing Backend Server")
    print("=" * 60)
    print(f"📂 Upload folder: {UPLOAD_FOLDER}")
    print(f"📂 Processed folder: {PROCESSED_FOLDER}")
    print(f"🌐 Server running on: http://localhost:5000")
    print(f"✅ Health check: http://localhost:5000/api/health")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)