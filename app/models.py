from pydantic import BaseModel
from typing import List, Optional, Any

class UserMessageRequest(BaseModel):
    session_id: str
    message: str

class Product(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None
    categoria: Optional[str] = None
    tags: Optional[List[str]] = None
    preco: Optional[float] = None 

class ProductResponse(BaseModel):
    interpreted_query: str 
    ai_message: str # Mensagem da IA
    is_category_list: bool = False # Indica se a IA listou as categorias disponíveis
    has_more: bool = False # Indica se existem mais produtos nessa categoria/busca
    server_busy: bool = False # Indica se o servidor estava ocupado (fila cheia)
    products: List[Product]
