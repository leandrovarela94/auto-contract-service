"""
Teste rápido do Ollama Client.
"""

from adapters.ollama_client import ollama_client

print("Testando Ollama Client...")

try:
    response = ollama_client.generate(
        system_instruction="Você é um assistente útil.",
        user_prompt="Diga 'Olá, funciona!' em português.",
        temperature=0.7,
    )
    print(f"✅ Resposta: {response}")
except Exception as e:
    print(f"❌ Erro: {e}")
