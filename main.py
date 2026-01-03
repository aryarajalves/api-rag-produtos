from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import UserMessageRequest, ProductResponse, Product
from app.db.database import (
    get_all_products_async, 
    search_products_async, 
    get_memory_async, 
    save_memory_async, 
    get_all_categories_async
)
from app.core.ai import process_user_message
from app.utils import ensure_uuid
from app.core.embeddings import generate_query_embedding
from app.middleware import LoggingMiddleware
from app.logger import logger
import os
import asyncio


app = FastAPI(title="API RAG Produtos")

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adicionar middleware de logging
app.add_middleware(LoggingMiddleware)

logger.info("🚀 API RAG Produtos iniciada")

@app.get("/debug-env")
async def debug_env():
    import os
    from app.gemini_service import CHAT_MODEL_NAME
    key = os.environ.get("GEMINI_API_KEY", "NOT_FOUND")
    file_key = "NOT_CHECKED"
    try:
         with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("GEMINI_API_KEY="):
                    file_key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    except:
        file_key = "ERROR_READING_FILE"

    masked = f"{key[:5]}...{key[-5:]}" if len(key) > 10 else key
    masked_file = f"{file_key[:5]}...{file_key[-5:]}" if len(file_key) > 10 else file_key
    
    return {
        "env_var_status": "FOUND" if len(key) > 10 else "MISSING/INVALID",
        "env_var_masked": masked,
        "file_key_masked": masked_file,
        "model_name": CHAT_MODEL_NAME,
        "cwd": os.getcwd(),
        "env_file_exists": os.path.exists(".env")
    }


from app.core.security import get_api_key
from fastapi import Depends

@app.get("/")
async def read_root():
    return {"message": "API de Produtos Online"}

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker/Portainer"""
    return {
        "status": "healthy",
        "service": "rag-produtos-api",
        "version": "1.0.0"
    }

@app.post("/query", response_model=ProductResponse, dependencies=[Depends(get_api_key)])
async def query_products(request: UserMessageRequest):
    """
    Endpoint principal que gerencia o fluxo de conversação e busca.
    """
    try:
        # Coluna agora é text, aceita qualquer ID
        session_id = request.session_id
        user_msg = request.message
        
        # 0. Configurações
        limit = int(os.environ.get("PRODUCTS_LIMIT", 5))
        
        # 1. Recuperar contexto (Memoria + Categorias)
        memory_task = get_memory_async(session_id)
        categories_task = get_all_categories_async()
        
        # Executar em paralelo para ganhar tempo
        memory, categories = await asyncio.gather(memory_task, categories_task)
        
        # 2. Processar intenção com IA
        ai_response = await process_user_message(user_msg, memory, categories)
        
        intent_type = ai_response.get("type")
        
        # Checar se o servidor está ocupado
        if ai_response.get("server_busy"):
            return ProductResponse(
                interpreted_query="Servidor Ocupado",
                ai_message="Estamos com muitas requisições no momento. Por favor, tente novamente em alguns segundos.",
                is_category_list=False,
                has_more=False,
                server_busy=True,
                products=[]
            )
            
        term = ai_response.get("term")
        tag = ai_response.get("tag")
        
        # Filtros de Preço
        price_min = ai_response.get("price_min")
        price_max = ai_response.get("price_max")
        price_exact = ai_response.get("price_exact")
        min_exclusive = ai_response.get("price_min_exclusive", False)
        max_exclusive = ai_response.get("price_max_exclusive", False)
        sort_order = ai_response.get("sort")
        
        ai_reply = ai_response.get("ai_reply", "")
        # sort_order is already extracted above
        is_cat_list = ai_response.get("is_category_list", False)
        
        page = ai_response.get("page", 1)
        if isinstance(page, str) or page is None: page = 1 # Garantia
        
        # Calcular offset
        offset = (int(page) - 1) * limit
        
        print(f"Intenção: {intent_type} | Termo: {term} | Tag: {tag} | Preço: {price_min}-{price_max} (={price_exact}) | Excl: {min_exclusive}/{max_exclusive} | Pagina: {page}")

        # 3. Executar ações baseadas na intenção
        products_list = []
        has_more = False
        
        # Truque: buscar limit + 1 para saber se tem proxima pagina
        fetch_limit = limit + 1
        
        data = []
        if intent_type == "search_product":
            # --- BUSCA HÍBRIDA (EXATA + VETORIAL EM PARALELO) ---
            exact_data = []
            vector_data = []
            
            # 1. Sempre executar busca exata quando há filtros
            exact_task = search_products_async(
                query_term=term, 
                tag=tag, 
                limit=fetch_limit, 
                offset=offset,
                min_price=price_min,
                max_price=price_max,
                exact_price=price_exact,
                order_by=sort_order,
                min_price_exclusive=min_exclusive,
                max_price_exclusive=max_exclusive
            )
            
            # 2. Executar busca vetorial em paralelo (se não for busca muito específica)
            vector_task = None
            if not price_exact and user_msg:  # user_msg definido no início
                vector = generate_query_embedding(user_msg)
                if vector:
                    print(f"🔎 [RAG] Executando busca vetorial em paralelo...")
                    vector_task = search_products_async(
                        is_vector=True,
                        embedding=vector,
                        limit=fetch_limit
                    )
            
            # 3. Executar ambas em paralelo
            if vector_task:
                exact_data, vector_data = await asyncio.gather(exact_task, vector_task)
                print(f"📊 [RAG] Exata: {len(exact_data)} | Vetorial: {len(vector_data)}")
                # Combinar resultados
                data = merge_and_deduplicate(exact_data, vector_data, fetch_limit)
                print(f"✅ [RAG] Combinados: {len(data)} (após merge/dedup)")
            else:
                exact_data = await exact_task
                data = exact_data
            # -----------------------------------------------
        elif intent_type == "search_category" and term:
            # Mesma lógica híbrida para categorias
            exact_task = search_products_async(
                category=term, 
                tag=tag, 
                limit=fetch_limit, 
                offset=offset,
                min_price=price_min,
                max_price=price_max,
                exact_price=price_exact,
                order_by=sort_order,
                min_price_exclusive=min_exclusive,
                max_price_exclusive=max_exclusive
            )
            
            vector_task = None
            if not price_exact and user_msg:
                vector = generate_query_embedding(user_msg)
                if vector:
                    print(f"🔎 [RAG] Busca vetorial para categoria '{term}'...")
                    vector_task = search_products_async(
                        is_vector=True,
                        embedding=vector,
                        limit=fetch_limit
                    )
            
            if vector_task:
                exact_data, vector_data = await asyncio.gather(exact_task, vector_task)
                print(f"📊 [RAG] Categoria '{term}': Exata: {len(exact_data)} | Vetorial: {len(vector_data)}")
                data = merge_and_deduplicate(exact_data, vector_data, fetch_limit)
            else:
                data = await exact_task
            
        # Logica de Has More
        if len(data) > limit:
            has_more = True
            data = data[:limit] # Remove o excedente que usamos so pra checar
            
        products_list = _parse_products(data)
        
        # Ajuste Fino da Mensagem (Feedback de Fim de Lista)
        if intent_type in ["search_product", "search_category"]:
            if len(products_list) == 0 and page > 1:
                # Caso onde o usuário pediu "ver mais" mas não tem mais nada
                ai_reply = "Já mostrei todas as opções disponíveis nesta categoria."
            elif not has_more and len(products_list) > 0:
                 # Caso onde mostrou os últimos itens
                 ai_reply += " (Estas são todas as opções)."
            
        # (Se for 'conversation', products_list continua vazio)

        # 4. Salvar Memória (Msg Usuario + Resposta IA) - Em background para nao travar user
        # Poderiamos usar BackgroundTasks do FastAPI, mas await aqui é rapido o suficiente se for async
        await save_memory_async(session_id, "user", user_msg)
        await save_memory_async(session_id, "assistant", ai_reply)
        
        return ProductResponse(
            interpreted_query=f"{intent_type}: {term} (p{page})",
            ai_message=ai_reply,
            is_category_list=is_cat_list,
            has_more=has_more,
            products=products_list
        )
        
    except Exception as e:
        print(f"Erro CRÍTICO: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _parse_products(data):
    """Auxiliar para converter dict do supabase em modelo Pydantic"""
    parsed = []
    for item in data:
        try:
            prod = Product(
                id=item.get('id'),
                nome=item.get('nome', 'Sem nome'),
                descricao=item.get('descricao'),
                categoria=item.get('categoria'),
                tags=item.get('tags'),
                preco=item.get('preco')
            )
            parsed.append(prod)
        except:
            continue
    return parsed

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
