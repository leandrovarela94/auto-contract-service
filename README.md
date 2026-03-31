# Auto Contract Service

Gerador de propostas e contratos com IA usando **Ollama Cloud**.

## Estrutura do Projeto

```
auto-contract-service/
├── main.py                  # Entry point FastAPI
├── config.py               # Configurações
├── adapters/
│   └── ollama_client.py   # Client Ollama Cloud
├── models/
│   └── schemas.py        # Schemas Pydantic
├── routes/
│   ├── analyze.py        # Rotas de análise PDF
│   └── templates.py      # Rotas de templates
├── services/
│   └── template_service.py
├── static/
│   └── index.html       # Frontend SPA
├── data/                # Templates salvos
├── test_ollama.py       # Teste do client
└── README.md
```

## Configuração

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Edite o `.env`:
```env
PORT=8080
OLLAMA_API_KEY=sua_chave_aqui
OLLAMA_BASE_URL=https://api.ollama.com
OLLAMA_MODEL=gpt-oss:120b-cloud
```

### 3. Obter API Key

1. Acesse [ollama.com/cloud](https://ollama.com/cloud)
2. Crie uma conta
3. Copie sua API key

## Teste Rápido

```bash
python test_ollama.py
```

## Rodar

```bash
uvicorn main:app --host 127.0.0.1 --port 8080
```

Acesse: **http://127.0.0.1:8080**

Docs (Swagger): **http://127.0.0.1:8080/docs**

## API Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/analyze` | Upload PDF + detecção de variáveis |
| `POST` | `/api/generate` | Gera PDF |
| `GET` | `/api/templates` | Lista templates |
| `POST` | `/api/templates` | Cria template |
| `GET` | `/api/templates/{id}` | Detalhes |
| `DELETE` | `/api/templates/{id}` | Remove |
| `GET` | `/api/templates/{id}/export` | Exporta JSON |
| `POST` | `/api/templates/import` | Importa JSON |

## Fluxo de Uso

1. **Upload PDF** → Analise um contrato existente
2. **Identificação** → IA detecta campos mutáveis
3. **Salvar Template** → Guarde para reutilização
4. **Preencher** → Complete os valores
5. **Exportar** → Baixe em PDF
