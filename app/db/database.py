import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key)

import asyncio

def get_all_products():
    """Busca todos os produtos da tabela 'produtos'."""
    response = supabase.table("produtos").select("*").execute()
    return response.data

async def get_all_products_async():
    return await asyncio.to_thread(get_all_products)


def search_products(query_term: str = None, category: str = None, limit: int = 5, offset: int = 0, tag: str = None, min_price: float = None, max_price: float = None, exact_price: float = None, order_by: str = None, min_price_exclusive: bool = False, max_price_exclusive: bool = False):
    """
    Busca produtos com filtros opcionais de nome, categoria, tag e preço.
    Suporta paginação via limit/offset.
    """
    query = supabase.table("produtos").select("*")
    
    if category:
        query = query.eq("categoria", category)

    if tag:
        # Filtra se o array 'tags' contem a tag especificada
        query = query.contains("tags", [tag])
    
    if min_price is not None:
        if min_price_exclusive:
            query = query.gt("preco", min_price)
        else:
            query = query.gte("preco", min_price)
        
    if max_price is not None:
        if max_price_exclusive:
            query = query.lt("preco", max_price)
        else:
            query = query.lte("preco", max_price)
        
    if exact_price is not None:
        query = query.eq("preco", exact_price)
        
    if query_term:
        # Busca no nome OU na descrição (case insensitive)
        query = query.or_(f"nome.ilike.%{query_term}%,descricao.ilike.%{query_term}%")
        
    # Ordenação
    if order_by == "price_asc":
        query = query.order("preco", desc=False)
    elif order_by == "price_desc":
        query = query.order("preco", desc=True)
        # Se não tiver ordenação explicita, o Supabase já ordena por ID por padrão geralmente,
        # ou podemos forçar uma ordem se quisermos.
        
    # Limita a quantidade de resultados e aplica offset
    # Limita a quantidade de resultados e aplica offset
    # range no supabase é (start, end) inclusive.
    # Ex: limit=5, offset=0 -> range(0, 4)
    # Ex: limit=5, offset=5 -> range(5, 9)
    response = query.range(offset, offset + limit - 1).execute()
    return response.data

def search_products_by_vector(query_embedding: list, match_threshold: float = 0.3, limit: int = 5):
    """
    Busca produtos usando similaridade de cosseno (RPC match_products).
    """
    try:
        params = {
            "query_embedding": query_embedding,
            "match_threshold": match_threshold,
            "match_count": limit
        }
        response = supabase.rpc("match_products", params).execute()
        return response.data
    except Exception as e:
        print(f"❌ [DB] Erro na busca vetorial: {e}")
        return []

async def search_products_async(*args, **kwargs):
    if kwargs.get("is_vector"):
        # Remove argumento que não é da função original se necessário ou trata diferente
        embedding = kwargs.get("embedding")
        limit = kwargs.get("limit", 5)
        # thresholds podem ser ajustes finos futuros
        return await asyncio.to_thread(search_products_by_vector, embedding, 0.3, limit)
        
    return await asyncio.to_thread(search_products, *args, **kwargs)


from app.core.cache import cache

def get_all_categories():
    """Retorna lista de categorias únicas existentes."""
    
    # 1. Tentar pegar do Cache
    cached_categories = cache.get_cache("categories_list")
    if cached_categories:
        print("⚡ [DB] Recuperado categorias do Cache.")
        return cached_categories

    # 2. Se não, pegar do Banco
    print("🐢 [DB] Consultando categorias no Supabase...")
    response = supabase.table("produtos").select("categoria").execute()
    categories = set()
    for item in response.data:
        if item.get("categoria"):
            categories.add(item.get("categoria"))
    
    final_list = list(categories)
    
    # 3. Salvar no Cache (TTL 1 hora)
    cache.set_cache("categories_list", final_list, ttl_seconds=3600)
    
    return final_list

async def get_all_categories_async():
    return await asyncio.to_thread(get_all_categories)


def save_memory(session_id: str, role: str, content: str):
    """Salva uma mensagem na tabela de memória."""
    try:
        data = {
            "session_id": session_id,
           "role": role, # 'user' ou 'assistant'
           "content": content
        }
        supabase.table("memoria_chat").insert(data).execute()
    except Exception as e:
        print(f"Erro ao salvar memoria: {e}")

async def save_memory_async(session_id: str, role: str, content: str):
    return await asyncio.to_thread(save_memory, session_id, role, content)


def get_memory(session_id: str, limit: int = 10):
    """Recupera as últimas mensagens do usuário."""
    try:
        response = supabase.table("memoria_chat")\
            .select("*")\
            .eq("session_id", session_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        # Inverter para ordem cronológica (msg antiga -> msg nova)
        return response.data[::-1]
    except Exception as e:
        print(f"Erro ao ler memoria: {e}")
        return []

async def get_memory_async(session_id: str, limit: int = 10):
    return await asyncio.to_thread(get_memory, session_id, limit)

