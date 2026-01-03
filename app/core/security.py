from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    """
    Dependência para validar a API Key enviada no cabeçalho X-API-Key.
    """
    # Se a API_KEY não estiver configurada no ambiente, permite acesso (opcional)
    # ou você pode exigir que sempre esteja configurada.
    if not settings.API_KEY:
        return None
        
    if api_key_header == settings.API_KEY:
        return api_key_header
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate API Key"
    )
