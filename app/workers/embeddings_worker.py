
import asyncio
import os
import sys
import time

# Adicionar raiz do projeto ao path para imports funcionarem
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.database import supabase, get_all_products_async
from app.core.embeddings import generate_embedding

async def sync_embeddings():
    """
    Sincroniza embeddings dos produtos.
    1. Busca todos os produtos.
    2. Verifica se já existe embedding atualizado na tabela `product_embeddings`.
    3. Se não existir OU produto foi modificado, gera e salva.
    """
    print("🔄 [WORKER] Iniciando sincronização de embeddings...")
    
    # 1. Buscar todos os produtos com data de atualização
    resp_prod = supabase.table("produtos").select("id, nome, descricao, categoria, tags, updated_at").execute()
    products = resp_prod.data
    
    # 2. Busca embeddings existentes com data de criação
    resp_emb = supabase.table("product_embeddings").select("product_id, created_at").execute()
    existing_embeddings = {item['product_id']: item.get('created_at') for item in resp_emb.data}
    
    print(f"📦 [WORKER] Total Produtos: {len(products)} | Total Embeddings: {len(existing_embeddings)}")
    
    count_new = 0
    count_updated = 0
    
    for prod in products:
        pid = prod['id']
        product_updated_at = prod.get('updated_at')
        
        should_regenerate = False
        reason = ""
        
        if pid not in existing_embeddings:
            # Produto novo sem embedding
            should_regenerate = True
            reason = "NOVO"
        elif product_updated_at and existing_embeddings[pid]:
            # Produto existe, verificar se foi modificado
            # Comparar datas (formato ISO: 2024-01-01T12:00:00+00:00)
            from datetime import datetime
            try:
                prod_date = datetime.fromisoformat(product_updated_at.replace('Z', '+00:00'))
                emb_date = datetime.fromisoformat(existing_embeddings[pid].replace('Z', '+00:00'))
                
                if prod_date > emb_date:
                    should_regenerate = True
                    reason = "MODIFICADO"
                    count_updated += 1
            except Exception as e:
                print(f"⚠️ [WORKER] Erro ao comparar datas para ID {pid}: {e}")
        
        if not should_regenerate:
            continue
            
        print(f"⭐ [WORKER] [{reason}] Gerando embedding para ID {pid}: {prod['nome']}")
        
        # Montar o texto rico para encapsular o significado do produto
        tags_str = ", ".join(prod.get('tags') or [])
        text_to_embed = f"Categoria: {prod.get('categoria')}. Produto: {prod.get('nome')}. Descrição: {prod.get('descricao')}. Tags: {tags_str}"
        
        vector = generate_embedding(text_to_embed)
        
        if vector:
            # Salvar ou atualizar no banco
            try:
                data = {
                    "product_id": pid,
                    "embedding": vector
                }
                
                if pid in existing_embeddings:
                    # Atualizar embedding existente
                    supabase.table("product_embeddings").update(data).eq("product_id", pid).execute()
                else:
                    # Inserir novo embedding
                    supabase.table("product_embeddings").insert(data).execute()
                    count_new += 1
                
                # Pequena pausa para respeitar Rate Limit da API do Gemini
                time.sleep(1) 
            except Exception as e:
                print(f"❌ [WORKER] Erro ao salvar ID {pid}: {e}")
        else:
            print(f"⚠️ [WORKER] Falha ao gerar vetor para ID {pid}")
            
    print(f"✅ [WORKER] Sincronização finalizada. {count_new} novos | {count_updated} atualizados.")

if __name__ == "__main__":
    # Loop infinito (simples)
    # Em produção, seria um cronjob ou serviço systemd ou container separado
    print("🚀 [WORKER] Worker de Embeddings Rodando... (Ctrl+C para parar)")
    try:
        while True:
            try:
                asyncio.run(sync_embeddings())
            except Exception as e:
                print(f"❌ [WORKER] Erro crítico no loop: {e}")
            
            # Espera X minutos antes de rodar de novo
            interval_minutes = int(os.environ.get("EMBEDDING_UPDATE_INTERVAL_MINUTES", 10))
            print(f"💤 [WORKER] Dormindo por {interval_minutes} minutos...")
            time.sleep(interval_minutes * 60)
            
    except KeyboardInterrupt:
        print("🛑 [WORKER] Parando worker...")
