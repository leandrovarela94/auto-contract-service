# Auto Contract Service

Gerador de propostas e contratos com IA usando **Ollama Cloud**.

## Estrutura do Projeto

```
auto-contract-service/
├── main.py                 # Entry point FastAPI
├── config.py              # Configurações
├── adapters/
│   └── ollama_adapter.py  # Adapter para Ollama Cloud
├── models/
│   └── schemas.py         # Schemas Pydantic
├── routes/
│   ├── analyze.py         # Rotas de análise PDF
│   └── templates.py       # Rotas de templates
├── services/
│   └── template_service.py # Lógica de templates
├── static/
│   └── index.html         # Frontend SPA
├── data/                  # Templates salvos
└── README.md
```

## Configuração

1. Obtenha uma API key do [Ollama Cloud](https://ollama.com/cloud)
2. Edite o `.env`:

```env
PORT=8080
OLLAMA_API_KEY=sua_chave_aqui
OLLAMA_BASE_URL=https://api.ollama.com/v1
OLLAMA_MODEL=llama3.2
```

## Rodar

```bash
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8080
```

Acesse: **http://127.0.0.1:8080**
