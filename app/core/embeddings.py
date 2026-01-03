
import requests
import os
import time

def _get_api_key():
    """Lê a chave diretamente do arquivo .env ou ambiente."""
    c_key = None
    try:
         with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("GEMINI_API_KEY="):
                    c_key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    except:
        pass
    
    if not c_key:
        c_key = os.environ.get("GEMINI_API_KEY")
        
    if not c_key:
        return None
    return c_key

def _call_embedding_api(text: str, task_type: str = "retrieval_document"):
    api_key = _get_api_key()
    if not api_key:
        print("❌ [EMBEDDING] Sem API Key.")
        return None

    # URL correta para o modelo de embeddings
    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "models/text-embedding-004",
        "content": {
            "parts": [{"text": text}]
        },
        "taskType": task_type
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Erro Embedding HTTP ({response.status_code}): {response.text}")
            return None
            
        data = response.json()
        return data['embedding']['values']
    except Exception as e:
        print(f"❌ Erro Conexão Embedding: {e}")
        return None

def generate_embedding(text: str):
    """
    Gera o embedding (vetor) para o texto fornecido.
    Usa task_type="retrieval_document" para otimizar para armazenamento.
    """
    if not text or not isinstance(text, str):
        return None
    text = text.replace("\n", " ").strip()
    return _call_embedding_api(text, "retrieval_document")

def generate_query_embedding(text: str):
    """
    Gera embedding específico para queries de busca.
    """
    return _call_embedding_api(text, "retrieval_query")
