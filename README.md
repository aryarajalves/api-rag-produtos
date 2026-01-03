# 🛒 API RAG de Produtos

API Backend inteligente para busca de produtos usando **RAG (Retrieval-Augmented Generation)** com busca híbrida (exata + vetorial), autenticação via API Key, e deploy automatizado via Docker Swarm.

[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://hub.docker.com/r/aryarajalves/rag-produtos)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-green)](https://github.com/aryarajalves/api-rag-produtos/actions)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow)](https://www.python.org/)

---

## 🎯 Funcionalidades

### ✅ Implementado

- **🔍 Busca Híbrida Inteligente**
  - Busca exata por nome, categoria e tags
  - Busca semântica via embeddings (Gemini AI)
  - Merge automático de resultados com deduplicação
  - Filtros de preço (mín, máx, exato) com suporte a operadores exclusivos
  - Ordenação por preço (crescente/decrescente)

- **🤖 Processamento de Linguagem Natural**
  - Interpretação de intenção do usuário via Gemini 3.0 Flash
  - Memória de conversação por sessão
  - Paginação automática de resultados
  - Listagem dinâmica de categorias disponíveis

- **🔒 Segurança**
  - Autenticação via API Key (Header `X-API-Key`)
  - Configurável via variável de ambiente
  - Proteção contra requisições não autorizadas

- **� Logging Estruturado**
  - Logs em formato JSON para produção
  - Request ID único para rastreamento
  - Captura automática de erros e exceções
  - Métricas de tempo de resposta

- **⚙️ Worker de Embeddings**
  - Geração automática de embeddings para produtos novos
  - Re-geração para produtos modificados
  - Execução em background (intervalo configurável)

- **🐳 Deploy Production-Ready**
  - Docker Compose para Swarm/Portainer
  - Integração com Traefik (HTTPS automático)
  - Health checks configurados
  - Scaling horizontal (réplicas configuráveis)
  - CI/CD via GitHub Actions (build e push automático)

---

## 📋 Pré-requisitos

- **Python 3.10+** (desenvolvimento local)
- **Docker** (produção)
- **Conta Supabase** (banco de dados + vetores)
- **Chave API Google Gemini** ([aistudio.google.com](https://aistudio.google.com))

---

## 🚀 Instalação Local

### 1. Clone o repositório

```bash
git clone https://github.com/aryarajalves/api-rag-produtos.git
cd api-rag-produtos
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto (use `.env.example` como base):

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key_here

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# API Configuration
PRODUCTS_LIMIT=5
MAX_CONCURRENT_AI_REQUESTS=5
AI_QUEUE_TIMEOUT=30

# API Key Authentication (opcional)
API_KEY=your_secret_password

# Worker
EMBEDDING_UPDATE_INTERVAL_MINUTES=10
```

### 4. Inicie a API

```bash
python -m uvicorn main:app --reload
```

A API estará disponível em: **http://localhost:8000**

### 5. Inicie o Worker (opcional)

Em outro terminal:

```bash
python -m app.workers.embeddings_worker
```

---

## 📡 Como Usar

### Endpoint Principal

**`POST /query`**

#### Request

```json
{
  "session_id": "user123",
  "message": "Quero produtos veganos até 50 reais"
}
```

#### Headers (se API_KEY estiver configurada)

```
X-API-Key: your_secret_password
```

#### Response

```json
{
  "interpreted_query": "Produtos veganos até R$50",
  "ai_message": "Encontrei opções veganas dentro do seu orçamento!",
  "is_category_list": false,
  "has_more": false,
  "server_busy": false,
  "products": [
    {
      "id": 42,
      "nome": "Hambúrguer Vegano",
      "descricao": "100% plant-based",
      "categoria": "Alimentos",
      "tags": ["Vegano", "Sem Glúten"],
      "preco": 35.90
    }
  ]
}
```

### Documentação Interativa

Acesse: **http://localhost:8000/docs**

---

## 🐳 Deploy em Produção

### Pré-requisitos

- Servidor com Docker Swarm inicializado
- Portainer instalado (opcional, mas recomendado)
- Traefik configurado para HTTPS automático

### Passos

1. **Configure os Secrets no GitHub**
   - `DOCKERHUB_USERNAME`: seu usuário do Docker Hub
   - `DOCKERHUB_TOKEN`: token de acesso do Docker Hub

2. **Faça Push para o GitHub**
   ```bash
   git push origin main
   ```
   O GitHub Actions irá automaticamente:
   - Buildar a imagem Docker
   - Fazer push para `aryarajalves/rag-produtos:latest` e `:1.0.0`

3. **Deploy no Portainer**
   - Acesse Portainer → Stacks → Add Stack
   - Cole o conteúdo do `docker-compose.yml`
   - Configure as variáveis de ambiente (veja `.env.portainer`)
   - Deploy!

Para instruções detalhadas, consulte: **[DEPLOY.md](./DEPLOY.md)** (no diretório de artifacts)

---

## 🏗️ Arquitetura

```
api-rag-produtos/
├── app/
│   ├── api/              # Endpoints da API
│   ├── core/             # Lógica central (AI, embeddings, segurança)
│   ├── db/               # Conexão com Supabase
│   ├── workers/          # Background workers
│   ├── config.py         # Configurações centralizadas
│   ├── logger.py         # Sistema de logging
│   ├── middleware.py     # Middlewares FastAPI
│   └── models.py         # Modelos Pydantic
├── tests/                # Testes unitários
├── scripts/              # Scripts auxiliares
├── .github/workflows/    # CI/CD GitHub Actions
├── docker-compose.yml    # Stack para produção
├── Dockerfile            # Imagem Docker
├── main.py               # Entry point da API
└── requirements.txt      # Dependências Python
```

---

## 🛠️ Tecnologias

- **[FastAPI](https://fastapi.tiangolo.com/)** - Framework web moderno e rápido
- **[Supabase](https://supabase.com/)** - Banco de dados Postgres + Vector Store
- **[Google Gemini](https://ai.google.dev/)** - IA generativa (NLP + Embeddings)
- **[Docker](https://www.docker.com/)** - Containerização
- **[Traefik](https://traefik.io/)** - Reverse proxy com HTTPS automático
- **[GitHub Actions](https://github.com/features/actions)** - CI/CD

---

## 📊 Logging

A API utiliza logging estruturado em JSON para facilitar monitoramento em produção:

```json
{
  "timestamp": "2026-01-03T15:30:00Z",
  "level": "INFO",
  "request_id": "abc123",
  "method": "POST",
  "path": "/query",
  "status_code": 200,
  "duration_ms": 245,
  "client_ip": "192.168.1.1"
}
```

Logs podem ser visualizados via:
- Portainer (Logs do container)
- SSH: `docker service logs rag-produtos-api_rag-api`

---

## � Segurança

- **API Key**: Protege endpoints sensíveis
- **Service Role Key**: Supabase com permissões completas (não expor publicamente)
- **HTTPS**: Certificados automáticos via Let's Encrypt (Traefik)
- **Firewall**: Recomendado bloquear portas não essenciais no servidor

---

## 🚧 Roadmap

- [ ] Busca por imagem (Gemini Vision API)
- [ ] Cache Redis para melhor performance
- [ ] Testes automatizados (pytest)
- [ ] Monitoramento com Prometheus/Grafana
- [ ] Rate limiting por IP
- [ ] Suporte a múltiplos idiomas

---

## 📝 Licença

Este projeto é de uso privado.

---

## 👤 Autor

**Arya Raj Alves**

- GitHub: [@aryarajalves](https://github.com/aryarajalves)
- Docker Hub: [aryarajalves/rag-produtos](https://hub.docker.com/r/aryarajalves/rag-produtos)

---

## 🤝 Contribuindo

Este é um projeto privado, mas sugestões são bem-vindas via Issues.
