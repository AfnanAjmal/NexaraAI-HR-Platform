import os
from dotenv import load_dotenv

load_dotenv()

# -------------------
# 1. LLM
# -------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL_NAME   = "llama-3.1-8b-instant"

# -------------------
# 2. Embeddings
# -------------------
EMBED_MODEL  = "BAAI/bge-small-en-v1.5"
CHROMA_DIR   = os.getenv("CHROMA_DIR", "chroma-db")
TOP_K        = 5

# -------------------
# 3. Database
# -------------------
MONGODB_URI  = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME      = os.getenv("DB_NAME", "nexara_hr")

# -------------------
# 4. App
# -------------------
BASE_URL         = os.getenv("BASE_URL", "http://localhost:8000")
HR_PASSCODE      = os.getenv("HR_PASSCODE", "1234")
SCORE_THRESHOLD  = float(os.getenv("SCORE_THRESHOLD", "6.0"))

# -------------------
# 5. Email (Resend)
# -------------------
RESEND_API_KEY      = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM          = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
# Force all emails to this address (required for Resend free plan)
RESEND_TO_OVERRIDE  = os.getenv("RESEND_TO_OVERRIDE", "")
CONTACT_EMAIL       = os.getenv("CONTACT_EMAIL", "hr@nexaraai.com")

# -------------------
# 6. Voice (Deepgram)
# -------------------
DEEPGRAM_API_KEY    = os.getenv("DEEPGRAM_API_KEY", "")

# -------------------
# 7. ElevenLabs TTS
# -------------------
ELEVENLABS_API_KEY  = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")

# -------------------
# 8. D-ID lip sync
# -------------------
DID_API_KEY         = os.getenv("DID_API_KEY", "")
# Must be a public URL (use ngrok for local dev — see did_service.py)
SARAH_PHOTO_URL     = os.getenv("SARAH_PHOTO_URL", "http://localhost:8000/static/sarah.jpg")
