# -*- coding: utf-8 -*-
"""
Flask Web App for Translation, Style Editing, Text-to-Speech and Feedback
"""

import os
import sys
import json
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory
from gtts import gTTS
from model.thinking_service import gemini_service
from model.NMT_Service import MNT
from config import Config

# -------------------------------------------------------------------------
# INITIAL SETUP
# -------------------------------------------------------------------------
sys.stdout.reconfigure(encoding='utf-8')

# -------------------------------------------------------------------------
# LOAD LANGUAGE AND PROMPT DATA
# -------------------------------------------------------------------------
try:
    with open("language_code/NLLB200_language_code.json", "r", encoding="utf-8") as f:
        language_code_dict = json.load(f)
    with open("language_code/styte_prompt.json", "r", encoding="utf-8") as f:
        prompt_template = json.load(f)
    with open("language_code/gTT5_language_code.json", "r", encoding="utf-8") as f:
        gTT5_language_code = json.load(f)
except Exception as e:
    print(f"[ERROR] Lỗi khi load file ngôn ngữ hoặc style prompt: {e}", flush=True)
    language_code_dict = {}
    prompt_template = {}

# -------------------------------------------------------------------------
# PRE-CLEANUP (DELETE OLD AUDIO FILES)
# -------------------------------------------------------------------------
os.makedirs(Config.AUDIO_PATH, exist_ok=True)
for filename in os.listdir(Config.AUDIO_PATH):
    file_path = os.path.join(Config.AUDIO_PATH, filename)
    if os.path.isfile(file_path):
        os.remove(file_path)


# -------------------------------------------------------------------------
# ROUTES
# -------------------------------------------------------------------------

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    """Trang chính."""
    return render_template(
        "index.html",
        language_code_dict=language_code_dict,
        styte_list=list(prompt_template.keys())
    )


@app.route("/translate", methods=["POST"])
def handle_translate():
    """Dịch văn bản với model tương ứng."""
    data = request.get_json() or {}

    text = data.get("text", "").strip()
    src_language = data.get("src_language")
    fr_language = data.get("fr_language")
    styte = data.get("style", "None")
    THINKING = data.get('thinking', False)
    print(f"[INFO] THINKING mode: {THINKING}", flush=True)

    # Validate input
    if not text:
        return jsonify({"error": "Vui lòng nhập văn bản cần dịch"}), 400
    if not src_language:
        return jsonify({"error": "Vui lòng chọn ngôn ngữ nguồn"}), 400
    if not fr_language:
        return jsonify({"error": "Vui lòng chọn ngôn ngữ đích"}), 400

    try:
        src_code = language_code_dict.get(src_language)
        fr_code = language_code_dict.get(fr_language)

        if not src_code or not fr_code:
            return jsonify({"error": "Ngôn ngữ không hợp lệ"}), 400

        result = MNT.call_ngrok_model(
            text,
            fr_code=fr_code,
            src_code=src_code
        )


        result = gemini_service.call_gemini_edit(
            text, src_language, fr_language, result, prompt = prompt_template.get(styte), thinking=THINKING
            )
        
        return jsonify({"translation": result}), 200

    except Exception as e:
        return jsonify({"error": f"Lỗi khi dịch: {str(e)}"}), 500


@app.route("/feedback", methods=["POST"])
def save_feedback():
    """Lưu phản hồi người dùng."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Không nhận được dữ liệu"}), 400

    feedback_entry = {
        "src_language": data.get("src_language", ""),
        "src_text": data.get("text", ""),       
        "translate_text": data.get("translation", ""),
        "style": data.get("style", ""),
        "type": int(data.get("type", 0)),
    }

    try:
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs(os.path.dirname(Config.FEEDBACK_FILE), exist_ok=True)
        
        # Nếu file chưa tồn tại → tạo mới
        if not os.path.exists(Config.FEEDBACK_FILE):
            with open(Config.FEEDBACK_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)

        # Đọc dữ liệu cũ
        with open(Config.FEEDBACK_FILE, "r", encoding="utf-8") as f:
            feedback_data = json.load(f)

        # Thêm dữ liệu mới
        feedback_data.append(feedback_entry)

        # Ghi lại file
        with open(Config.FEEDBACK_FILE, "w", encoding="utf-8") as f:
            json.dump(feedback_data, f, ensure_ascii=False, indent=4)

        return jsonify({"message": "Feedback saved successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Lỗi khi lưu feedback: {str(e)}"}), 500


@app.route("/audio/<filename>")
def serve_audio(filename):
    """Serve audio files"""
    return send_from_directory(Config.AUDIO_PATH, filename)


@app.route("/speed2text", methods=["POST"])
def speed2text():
    """Chuyển văn bản thành giọng nói."""
    data = request.get_json() or {}
    text = data.get("translation", "").strip()
    speech_language = data.get("fr_language", None)

    if not text and not speech_language:
        return jsonify({"error": "No text provided"}), 400

    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(Config.AUDIO_PATH, filename)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    try:
        tts = gTTS(text=text, lang=gTT5_language_code.get(speech_language, "en"))
        tts.save(filepath)
    except Exception as e:
        return jsonify({"error": f"Lỗi khi tạo file âm thanh: {str(e)}"}), 500

    # ✅ FIX: Trả về URL đúng thay vì đường dẫn file
    return jsonify({"media": f"/audio/{filename}"}), 200


@app.route("/uploadfile", methods=["POST"])
def upload_file():
    """Xử lý tải file lên."""
    if "file" not in request.files:
        return jsonify({"error": "Không có file nào được gửi lên"}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "Vui lòng chọn một file để tải lên"}), 400

    ALLOWED_EXTENSIONS = {"txt", "pdf", "doc", "docx", "odt"}

    def allowed_file(filename: str) -> bool:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    if not allowed_file(file.filename):
        return jsonify({
            "error": "Định dạng file không được hỗ trợ. Chỉ chấp nhận: txt, pdf, doc, docx, odt"
        }), 400

    try:
        os.makedirs(Config.UPLOAD_PATH, exist_ok=True)
        unique_name = f"{uuid.uuid4().hex}_{file.filename}"
        filepath = os.path.join(Config.UPLOAD_PATH, unique_name)
        file.save(filepath)

        return jsonify({
            "message": "File đã được tải lên thành công",
            "filename": file.filename,
            "saved_path": filepath
        }), 200

    except Exception as e:
        return jsonify({"error": f"Lỗi khi tải file: {str(e)}"}), 500


# -------------------------------------------------------------------------
# MAIN ENTRY
# -------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
