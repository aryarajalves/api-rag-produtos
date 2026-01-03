
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Force load configuration
load_dotenv(override=True)

def get_key_from_file():
    """Manual fallback to read key directly from file to avoid env var caching issues."""
    try:
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("GEMINI_API_KEY="):
                    # Remove "GEMINI_API_KEY=" and quotes
                    key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                    return key
    except Exception:
        return None
    return None

# Try env first, then file fallback
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY or "YOUR_KEY" in API_KEY:
    # Fallback manual
    manual_key = get_key_from_file()
    if manual_key:
        print(f"⚠️ [GEMINI SERVICE] Usando chave lida manualmente do .env (Environment falhou/inválido)")
        API_KEY = manual_key

if not API_KEY:
    print("❌ [GEMINI SERVICE] API Key not found in environment!")
else:
    print(f"🔑 [GEMINI SERVICE] Key Loaded: {API_KEY[:5]}...{API_KEY[-5:]}")

# Configure globally once
genai.configure(api_key=API_KEY)

# Constants
CHAT_MODEL_NAME = "gemini-3-flash-preview"  # As requested by user
EMBEDDING_MODEL_NAME = "models/text-embedding-004"

def get_chat_model():
    """Returns the configured GenerativeModel for chat."""
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    
    print(f"⚡ [GEMINI SERVICE] Instantiating Chat Model: {CHAT_MODEL_NAME}")
    return genai.GenerativeModel(
        model_name=CHAT_MODEL_NAME,
        generation_config=generation_config,
    )

def get_embedding_model_name():
    return EMBEDDING_MODEL_NAME
