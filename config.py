import os
from dotenv import load_dotenv

# Load .env ngay khi import file này
load_dotenv()

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    NGROK_URL = os.getenv("NGROK_URL")
    DB_PATH = "dictionary_ALT.db"
    
    # Model Config
    GEMINI_MODEL = "gemini-2.5-flash"
    COMET_MODEL_NAME = "Unbabel/wmt22-comet-da"
    
    # Paths
    AUDIO_PATH = "static/audio"
    UPLOAD_PATH = "uploads"
    FEEDBACK_FILE = "feedback.json"