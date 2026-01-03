import logging
import sys
import json
from datetime import datetime
from typing import Any

class StructuredLogger:
    """Logger estruturado para produção"""
    
    def __init__(self, name: str = "rag-api"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Handler para console (Docker logs)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        # Formato JSON estruturado
        formatter = JsonFormatter()
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
    
    def info(self, message: str, **kwargs):
        self.logger.info(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        self.logger.error(message, extra=kwargs, exc_info=True)
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra=kwargs)


class JsonFormatter(logging.Formatter):
    """Formata logs em JSON para facilitar parsing"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Adicionar campos extras
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName', 
                              'levelname', 'levelno', 'lineno', 'module', 'msecs', 
                              'pathname', 'process', 'processName', 'relativeCreated', 
                              'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info']:
                    try:
                        log_data[key] = value
                    except:
                        pass
        
        # Adicionar stack trace se erro
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


# Instância global
logger = StructuredLogger()
