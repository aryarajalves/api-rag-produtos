import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

class CacheManager:
    def __init__(self):
        self.use_redis = False
        self.local_cache = {}
        self.redis_client = None
        
        # Tenta conectar ao Redis se as variáveis estiverem presentes
        redis_url = os.environ.get("REDIS_URL")
        redis_host = os.environ.get("REDIS_HOST")
        
        if redis_url or redis_host:
            try:
                import redis
                if redis_url:
                    self.redis_client = redis.from_url(redis_url)
                else:
                    self.redis_client = redis.Redis(
                        host=redis_host, 
                        port=int(os.environ.get("REDIS_PORT", 6379)),
                        password=os.environ.get("REDIS_PASSWORD"),
                        decode_responses=True
                    )
                
                # Teste de conexão
                self.redis_client.ping()
                self.use_redis = True
                print("✅ [CACHE] Conectado ao Redis com sucesso.")
            except Exception as e:
                print(f"⚠️ [CACHE] Falha ao conectar no Redis ({e}). Usando Memória Local.")
                self.use_redis = False
        else:
            print("ℹ️ [CACHE] Variáveis do Redis não encontradas. Usando Memória Local.")

    def get_cache(self, key: str):
        """Recupera valor do cache."""
        if self.use_redis:
            try:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
                return None
            except Exception as e:
                print(f"❌ [CACHE] Erro ao ler do Redis: {e}")
                return None
        else:
            # Lógica simples de expiração em memória
            entry = self.local_cache.get(key)
            if not entry:
                return None
                
            if entry['expires_at'] < time.time():
                del self.local_cache[key]
                return None
                
            return entry['value']

    def set_cache(self, key: str, value, ttl_seconds: int = 3600):
        """Salva valor no cache com tempo de vida (TTL)."""
        if self.use_redis:
            try:
                json_val = json.dumps(value)
                self.redis_client.setex(key, ttl_seconds, json_val)
            except Exception as e:
                print(f"❌ [CACHE] Erro ao salvar no Redis: {e}")
        else:
            self.local_cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl_seconds
            }

# Instância global para ser importada
cache = CacheManager()
