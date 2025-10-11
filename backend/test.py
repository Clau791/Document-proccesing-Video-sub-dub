from flask import Flask, request, jsonify
from flask_cors import CORS
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)

def log(message, data=None):
    """Helper pentru logging formatat"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n{'='*60}")
    print(f"[{timestamp}] {message}")
    if data:
        for key, value in data.items():
            print(f"  {key}: {value}")
    print(f"{'='*60}\n")

@app.route('/api/health', methods=['GET'])
def health_check():
    log(" HEALTH CHECK")
    return jsonify({"status": "online"}), 200

@app.route('/api/summarize', methods=['POST'])
def summarize():
    file = request.files.get('file')
    log(" SUMMARIZE REQUEST", {
        "file": file.filename if file else "None",
        "service": request.form.get('service'),
        "src_lang": request.form.get('src_lang'),
        "dest_lang": request.form.get('dest_lang'),
        "detail_level": request.form.get('detail_level'),
        "youtube_link": request.form.get('youtube_link', 'None')
    })
    
    time.sleep(1)
    return jsonify({
        "summary": f"Rezumat pentru {file.filename if file else 'document'}",
        "bullets": ["Punct 1", "Punct 2", "Punct 3"]
    }), 200

@app.route('/api/translation', methods=['POST'])
def translation():
    file = request.files.get('file')
    log(" TRANSLATION REQUEST", {
        "file": file.filename if file else "None",
        "service": request.form.get('service'),
        "src_lang": request.form.get('src_lang'),
        "dest_lang": request.form.get('dest_lang'),
        "detail_level": request.form.get('detail_level')
    })
    
    time.sleep(2)
    return jsonify({
        "downloadUrl": f"translated_{file.filename}" if file else "translated.pdf",
        "file_path": f"translated_{file.filename}" if file else "translated.pdf"
    }), 200

@app.route('/api/subtitles', methods=['POST'])
def subtitles():
    file = request.files.get('file')
    log(" SUBTITLES REQUEST", {
        "file": file.filename if file else "None",
        "service": request.form.get('service'),
        "src_lang": request.form.get('src_lang'),
        "dest_lang": request.form.get('dest_lang')
    })
    
    time.sleep(2)
    return jsonify({
        "jobId": f"sub_{int(time.time())}",
        "status": "done",
        "resultUrl": "http://localhost:5000/result.srt",
        "downloadUrl": "subtitles.srt"
    }), 200

@app.route('/api/dubbing', methods=['POST'])
def dubbing():
    file = request.files.get('file')
    log(" DUBBING REQUEST", {
        "file": file.filename if file else "None"
    })
    
    time.sleep(3)
    return jsonify({
        "jobId": f"dub_{int(time.time())}",
        "status": "done",
        "resultUrl": "http://localhost:5000/result.mp4",
        "downloadUrl": "dubbed_video.mp4"
    }), 200

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    log(" DOWNLOAD REQUEST", {"filename": filename})
    return jsonify({"message": "Download simulat", "file": filename}), 200

if __name__ == '__main__':
    print("\n" + "="*60)
    print(" BACKEND DEBUG SERVER PORNIT")
    print("="*60)
    print(" http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)