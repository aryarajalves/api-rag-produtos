from app.core.gemini_service import get_chat_model
import os
import asyncio

# Instancia o modelo via serviço centralizado
model = get_chat_model()

# Configuração de Concorrência
MAX_CONCURRENT = int(os.environ.get("MAX_CONCURRENT_AI_REQUESTS", 10))
TIMEOUT_SECONDS = int(os.environ.get("AI_QUEUE_TIMEOUT", 30))
semaphore = asyncio.Semaphore(MAX_CONCURRENT)

# Nota: O User pediu Gemini 3.0 Flash, mas atualmente o disponível via API 
# pode ser o gemini-1.5-flash ou gemini-2.0-flash-exp. 
# Vou usar o gemini-2.0-flash-exp como proxy ou o mais recente disponível.
# Se der erro, fallback para gemini-1.5-flash.

import json

# ... (imports mantidos)

async def process_user_message(message: str, history: list, categories: list) -> dict:
    print("🚀 [DEBUG] process_user_message: USANDO VERSÃO HTTP REQUESTS")
    """
    Processa a mensagem com contexto (Versão Async).
    Retorna um dicionário com:
    - type: 'search_product' | 'search_category' | 'conversation'
    - term: termo de busca ou nome da categoria
    - ai_reply: resposta textual da IA para o usuário
    """
    
    # Formatar histórico para o prompt
    history_text = ""
    for h in history[-5:]: # Ultimas 5 interacoes
        role = "Usuário" if h['role'] == 'user' else "Assistente"
        history_text += f"{role}: {h['content']}\n"
        
    categories_text = ", ".join(categories)
    
    prompt = f"""
    Você é um assistente de e-commerce inteligente.
    
    CATEGORIAS DISPONÍVEIS NO BANCO: [{categories_text}]
    
    HISTÓRICO RECENTE:
    {history_text}
    
    MENSAGEM ATUAL DO USUÁRIO: "{message}"
    
    SUA TAREFA:
    1. Analise se o usuário quer um produto específico ou ver uma categoria.
    2. Se for categoria, verifique se ela existe na lista (ou algo próximo).
    3. Se o usuário disser "sim", "quero", "mais", "ver restante" ou "continuar", isso é paginação. Mantenha o termo da busca anterior e incremente a pagina mentalmente (ou apenas sinalize page: N).
    4. Se o usuário perguntar O QUE TEM, O QUE VENDE, QUAIS OPCOES (perguntas genéricas), sua resposta DEVE listar as categorias disponíveis separadas por vírgula e marcar "is_category_list": true.
    5. Se o usuário pedir uma CARACTERÍSTICA ESPECÍFICA (ex: vegano, sem glúten, fitness), extraia isso como 'tag'.
       - IMPORTANTE: Padronize a tag com a primeira letra maiúscula e o resto minúsculo (Title Case). 
       - CORRIJA GÊNERO E NÚMERO: Se o usuário falar "Vegana" ou "Veganas", converta para o padrão do banco que é singular masculino "Vegano". O mesmo para "Sem Glutens" -> "Sem Glúten".
    6. Se o usuário mencionar VALORES (preço), extraia:
       - 'price_min': Para "acima de", "partir de", "mais caro que", "maior que".
       - 'price_max': Para "até", "abaixo de", "mais barato que", "menos de", "menor que".
       - 'price_exact': Para "exatamente", "no valor de".
       - 'price_min_exclusive': true se for "maior que", "acima de". false se for "a partir de", "de".
       - 'price_max_exclusive': true se for "menor que", "abaixo de", "menos de". false se for "até", "no máximo".
    7. ORDENAÇÃO (Importante):
       - Se o usuário pedir "mais barato", "menor preço", "mais em conta" -> defina "sort": "price_asc".
       - Se o usuário pedir "mais caro", "maior preço", "luxuoso", "premium" -> defina "sort": "price_desc".
       - Se não especificar ordem, mantenha "sort": null.
    8. REGRA DE OURO PARA TERMOS:
       - Se o usuário NÃO disser explicitamente o nome de um produto ou categoria (ex: "algo barato", "presente até 50 reais"), o campo "term" DEVE SER NULL. NÃO INVENTE CATEGORIAS.

    RETORNE APENAS UM JSON VÁLIDO (sem markdown) no seguinte formato:
    {{
        "type": "search_product" OU "search_category" OU "conversation",
        "term": "termo de busca ou nome exato da categoria",
        "tag": "nome da tag (ex: vegano) ou null",
        "price_min": 10.50 ou null,
        "price_max": 50.00 ou null,
        "price_exact": null,
        "price_min_exclusive": true ou false,
        "price_max_exclusive": true ou false,
        "page": 1,
        "sort": "price_asc" OU "price_desc" OU null,
        "ai_reply": "Sua resposta curta.",
        "is_category_list": true ou false
    }}
    
    Exemplos:
    - User: "Tem algo vegano?" -> {{"type": "search_product", "term": null, "tag": "Vegano", "price_min": null, "price_max": null, "price_exact": null, "price_min_exclusive": false, "price_max_exclusive": false, "page": 1, "sort": null, "ai_reply": "Buscando opções veganas...", "is_category_list": false}}
    - User: "Doces sem açúcar até 20 reais" -> {{"type": "search_product", "term": "Doces", "tag": "Sem Açúcar", "price_min": null, "price_max": 20.00, "price_exact": null, "price_min_exclusive": false, "price_max_exclusive": false, "page": 1, "sort": null, "ai_reply": "Doces sem açúcar até R$20.", "is_category_list": false}}
    - User: "Algo para comer com menos de 20 reais" -> {{"type": "search_product", "term": null, "tag": null, "price_min": null, "price_max": 20.00, "price_exact": null, "price_min_exclusive": false, "price_max_exclusive": true, "page": 1, "sort": null, "ai_reply": "Opções por menos de R$20.", "is_category_list": false}}
    - User: "Fone mais caro que 100" -> {{"type": "search_product", "term": "Fone", "tag": null, "price_min": 100.00, "price_max": null, "price_exact": null, "price_min_exclusive": true, "price_max_exclusive": false, "page": 1, "sort": null, "ai_reply": "Fones acima de R$100.", "is_category_list": false}}
    - User: "Camisa de 50 reais" -> {{"type": "search_product", "term": "Camisa", "tag": null, "price_min": null, "price_max": null, "price_exact": 50.00, "price_min_exclusive": false, "price_max_exclusive": false, "page": 1, "sort": null, "ai_reply": "Camisas de R$50.", "is_category_list": false}}
    - User: "Mostre os mais baratos" -> {{"type": "search_product", "term": null, "tag": null, "price_min": null, "price_max": null, "price_exact": null, "page": 1, "sort": "price_asc", "ai_reply": "Aqui estão os produtos de menor preço.", "is_category_list": false}}
    - User: "Qual é o produto mais caro?" -> {{"type": "search_product", "term": null, "tag": null, "price_min": null, "price_max": null, "price_exact": null, "page": 1, "sort": "price_desc", "ai_reply": "Este é o nosso produto de maior valor.", "is_category_list": false}}
    - User: "O que voces tem?" -> {{"type": "conversation", "term": null, "tag": null, "price_min": null, "price_max": null, "price_exact": null, "page": 1, "ai_reply": "Temos: Frutas, Massas...", "is_category_list": true}}
    - User: "Quero abacate" -> {{"type": "search_product", "term": "Abacate", "tag": null, "price_min": null, "price_max": null, "price_exact": null, "page": 1, "ai_reply": "Busquei por abacate.", "is_category_list": false}}
    - User: "Quais frutas tem?" -> {{"type": "search_category", "term": "Frutas", "tag": null, "price_min": null, "price_max": null, "price_exact": null, "page": 1, "ai_reply": "Aqui estão frutas.", "is_category_list": false}}
    - User: "Ver mais" (contexto anterior era frutas) -> {{"type": "search_category", "term": "Frutas", "tag": null, "price_min": null, "price_max": null, "price_exact": null, "page": 2, "ai_reply": "Aqui estão mais opções.", "is_category_list": false}}
    - User: "Sim" (após ver frutas) -> {{"type": "search_category", "term": "Frutas", "tag": null, "price_min": null, "price_max": null, "price_exact": null, "ai_reply": "Entendido, buscando mais opções de frutas..."}}
    - User: "Oi" -> {{"type": "conversation", "term": null, "tag": null, "price_min": null, "price_max": null, "price_exact": null, "ai_reply": "Olá! Como posso ajudar na sua compra hoje?"}}
    """
    
    try:
        # Tenta pegar o semáforo com timeout
        async with asyncio.timeout(TIMEOUT_SECONDS):
            async with semaphore:
                # --- HARDCORE HTTP FIX ---
                # Bypass total do SDK do Google que está bugado no ambiente async
                import requests
                
                # Ler chave bruta (Garantia absoluta)
                c_key = None
                try:
                     with open(".env", "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip().startswith("GEMINI_API_KEY="):
                                c_key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                except:
                    c_key = os.environ.get("GEMINI_API_KEY")
                
                if not c_key:
                    raise Exception("Chave API não encontrada nem no .env nem no ambiente.")

                # Chamada REST Manual
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={c_key}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "response_mime_type": "text/plain",
                        "temperature": 1.0
                    }
                }
                
                def _do_request():
                    return requests.post(url, headers=headers, json=payload, timeout=60)
                
                # Executa requests em thread para não travar o loop
                response = await asyncio.to_thread(_do_request)
                
                if response.status_code != 200:
                    print(f"❌ Erro HTTP Gemini: {response.text}")
                    raise Exception(f"Erro na API do Google: {response.status_code} - {response.text}")
                    
                resp_json = response.json()
                try:
                    text_resp = resp_json['candidates'][0]['content']['parts'][0]['text']
                except Exception as e:
                    print(f"❌ Erro parse JSON Gemini: {resp_json}")
                    raise e

                text_resp = text_resp.replace("```json", "").replace("```", "").strip()
                data = json.loads(text_resp)
                return data
                # --------------------------
        
    except asyncio.TimeoutError:
        print(f"⚠️ [AI] Timeout de {TIMEOUT_SECONDS}s na fila.")
        return {"server_busy": True}
        
    except Exception as e:
        print(f"Erro AI: {e}")
        # Fallback
        return {
            "type": "conversation",
            "term": None,
            "tag": None,
            "page": 1,
            "ai_reply": "Desculpe, não entendi. Pode repetir?",
            "tag": None,
            "page": 1,
            "sort": None,
            "ai_reply": "Desculpe, não entendi. Pode repetir?",
            "is_category_list": False
        }
