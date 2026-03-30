# 🔒 PropostaAI — Gerador Local de Propostas com IA

Aplicação web local para preencher templates de propostas de serviço com IA.
Todos os dados ficam **apenas na memória RAM** — nada é salvo em disco.

---

## ✅ Requisitos

- Python 3.9 ou superior
- Chave de API da Anthropic (console.anthropic.com)

---

## 🚀 Instalação

### 1. Instale as dependências

```bash
pip install -r requirements.txt
```

### 2. Inicie o servidor

```bash
python app.py
```

### 3. Acesse no navegador

```
http://127.0.0.1:5000
```

---

## 📋 Como Usar

### Fluxo Principal (Usuário)

1. **Configurar** — Insira sua chave de API Anthropic e faça upload do PDF template
2. **Analisar** — A IA detecta automaticamente todas as variáveis do documento
3. **Preencher** — Complete os campos detectados (valores financeiros são calculados automaticamente)
4. **Gerar** — Baixe o PDF profissional preenchido

### Fluxo de Referências de Mercado (Criador de Template)

O criador do template pode definir valores de referência protegidos por senha:

1. Role até **"Gerenciar Referências de Mercado"** no rodapé da página
2. Crie as referências no formato JSON:
```json
{
  "preco_hora": {"value": "350", "locked": true, "label": "Preço/hora"},
  "taxa_iss": {"value": "5", "locked": true, "label": "ISS (%)"},
  "desconto_max": {"value": "15", "locked": false, "label": "Desconto Máximo"}
}
```
3. Defina uma senha e clique em **Salvar**
4. Compartilhe a senha apenas com usuários autorizados

Quando o usuário carregar o template com a senha correta, os valores protegidos serão pré-preenchidos e bloqueados.

---

## 🔐 Segurança

| Aspecto | Garantia |
|---|---|
| Dados do documento | Apenas em memória RAM, nunca em disco |
| Chave de API | Apenas em memória, não é logada |
| Referências de mercado | Apenas em memória, hash SHA-256 da senha |
| Tráfego | HTTPS com a API Anthropic apenas |
| Dados de terceiros | Zero — tudo local |

> ⚠️ **IMPORTANTE**: Ao fechar o servidor (`Ctrl+C`), todos os dados em memória são perdidos permanentemente. Isso é intencional para segurança.

---

## 📁 Estrutura do Projeto

```
proposta-app/
├── app.py              # Servidor Flask (backend)
├── requirements.txt    # Dependências Python
├── README.md           # Este arquivo
└── templates/
    └── index.html      # Interface web (frontend)
```

---

## 🛠️ Solução de Problemas

**Erro: "Não foi possível extrair texto do PDF"**
→ O PDF pode ser escaneado (imagem). Use um PDF com texto selecionável.

**Erro: "Chave de API inválida"**
→ Verifique se a chave começa com `sk-ant-` e está correta em console.anthropic.com

**Erro de porta em uso**
→ Mude a porta no final de `app.py`:
```python
app.run(debug=False, host='127.0.0.1', port=5001)  # porta diferente
```

**PDF com caracteres especiais incorretos**
→ O sistema usa encoding Latin-1 para PDF. Caracteres fora deste conjunto aparecem como `?`.

---

## 📝 Licença

Uso interno / proprietário. Não distribua sem autorização.
