from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import uuid
from app.logger import logger
import json

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para logging detalhado de todas as requisições.
    Registra: Request ID, tempo de resposta, IP, método, path, status, erros
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Gerar ID único para a requisição
        request_id = str(uuid.uuid4())
        
        # Informações da requisição
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        
        # Log início da requisição
        logger.info(
            "Request started",
            request_id=request_id,
            method=method,
            path=path,
            client_ip=client_ip,
            query_params=dict(request.query_params)
        )
        
        # Tentar capturar body (se não for muito grande)
        body_logged = False
        if method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if len(body) < 10000:  # Max 10KB para log
                    try:
                        body_json = json.loads(body)
                        logger.info(
                            "Request body",
                            request_id=request_id,
                            body=body_json
                        )
                        body_logged = True
                    except:
                        pass
                
                # Re-criar request para não consumir o body
                async def receive():
                    return {"type": "http.request", "body": body}
                
                request._receive = receive
            except:
                pass
        
        # Processar requisição
        try:
            response = await call_next(request)
            
            # Calcular tempo de resposta
            duration_ms = (time.time() - start_time) * 1000
            
            # Log sucesso
            logger.info(
                "Request completed",
                request_id=request_id,
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                client_ip=client_ip
            )
            
            # Adicionar request_id no header da resposta
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calcular tempo até o erro
            duration_ms = (time.time() - start_time) * 1000
            
            # Log erro detalhado
            logger.error(
                "Request failed",
                request_id=request_id,
                method=method,
                path=path,
                duration_ms=round(duration_ms, 2),
                client_ip=client_ip,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            
            # Re-lançar exceção
            raise
