# API RAG de Produtos 🛒

Este projeto é uma API Backend desenvolvida em Python (FastAPI) que consulta produtos em um banco de dados **Supabase** e utiliza inteligência artificial (**Gemini 3.0 Flash**) para processar as intenções de busca do usuário.

## 📋 Pré-requisitos

- Python 3.10 ou superior
- Conta no Supabase (URL e Key)
- Chave de API do Google Gemini

## 🚀 Instalação

1. **Clone ou baixe o repositório.**

2. **Instale as dependências:**
   Abra o terminal na pasta do projeto e execute:
   ```bash
   pip install -r requirements.txt
   ```
   *Caso tenha erro com o comando `pip`, tente `python -m pip install -r requirements.txt`.*

3. **Configure as Variáveis de Ambiente:**
   - Crie um arquivo chamado `.env` na raiz do projeto (use o `.env.example` como base se houver, ou crie do zero).
   - Adicione suas chaves:
     ```env
     SUPABASE_URL="sua_url_do_supabase"
     SUPABASE_KEY="sua_anon_key_do_supabase"
     GEMINI_API_KEY="sua_api_key_do_google"
     ```

## ⚡ Como Ativar/Executar a API

Devido a configurações de ambiente do Windows, recomenda-se iniciar o servidor executando o módulo do Uvicorn através do Python:

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- `main:app`: Refere-se ao arquivo `main.py` e à instância `app` do FastAPI.
- `--reload`: Reinicia o servidor automaticamente se você alterar o código.
- `--host 0.0.0.0`: Permite acesso externo (opcional).

Se tudo der certo, você verá uma mensagem como:
> `INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)`

## 📡 Como Usar

A API possui um endpoint principal para consulta.

### Consultar Produtos

**Rota:** `POST /query`

**Exemplo de Corpo da Requisição (JSON):**
```json
{
  "message": "Gostaria de ver produtos baratos"
}
```

**Exemplo de Resposta:**
```json
{
  "products": [
    {
      "id": 1,
      "nome": "Camiseta Básica",
      "descricao": "100% Algodão",
      "preco": 29.90
    },
    ...
  ]
}
```

### Testando via Swagger UI

O FastAPI gera uma documentação interativa automaticamente.
1. Com a API rodando, acesse no navegador: [http://localhost:8000/docs](http://localhost:8000/docs)
2. Clique em `POST /query` -> `Try it out`.
3. Preencha o Request Body e clique em `Execute`.

## 🛠️ Tecnologias

- **FastAPI**: Framework web moderno e rápido.
- **Supabase**: Banco de dados Postgres e autenticação.
- **Google Gemini 3.0 Flash**: IA generativa para entendimento de linguagem natural.
