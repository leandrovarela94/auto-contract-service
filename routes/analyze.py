"""
Routes Analyze — Rotas para análise de PDF.
"""

from __future__ import annotations

import io
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import pdfplumber
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fpdf import FPDF

from adapters.ollama_client import ollama_client
from models.schemas import GenerateRequest

router = APIRouter(prefix="/api", tags=["analyze"])

_SYSTEM_ANALYSIS = """\
Você é um especialista em análise de documentos empresariais brasileiros. 
Identifique TODAS as variáveis personalizáveis incluindo dados de pessoas físicas/jurídicas.
Responda APENAS com JSON puro e válido, sem texto adicional, sem markdown."""

_SYSTEM_FILL = """\
Você é um especialista em redação de propostas comerciais profissionais em português brasileiro."""

_ANALYSIS_PROMPT = """\
Analise este documento e identifique TODAS as variáveis personalizáveis.

Retorne APENAS JSON válido:
{{
  "document_type": "tipo do documento em português",
  "sections": ["lista de seções identificadas"],
  "variables": [
    {{
      "id": "nome_em_snake_case",
      "label": "Nome Legível em Português",
      "description": "Descrição do campo",
      "type": "text|number|currency|date|percentage|email|phone|cnpj|cpf|address",
      "current_value": "valor atual no texto ou vazio",
      "is_calculated": false,
      "formula": "",
      "category": "cliente|fornecedor|financeiro|servico|prazo|contato|outro",
      "required": true,
      "locked": false,
      "placeholder": "exemplo de valor"
    }}
  ],
  "calculations": [
    {{
      "id": "nome_calculo",
      "label": "Nome do Cálculo",
      "formula": "expressão (ex: quantidade * preco_unitario)",
      "type": "currency|percentage|number",
      "description": "o que este cálculo representa"
    }}
  ]
}}

IDENTIFIQUE INCLUSIVE:
- Nomes completos de pessoas
- CPF, CNPJ, RG
- Endereços completos
- Datas de nascimento, início, término
- Valores monetários
- Percentuais (descontos, juros, taxas)
- E-mails e telefones
- Descrições de serviços
- Condições de pagamento
- Cláusulas e parágrafos

Documento:
{text}
"""

_FILL_PROMPT = """\
Template original:
{template}

Valores a inserir:
{values}

Gere o documento COMPLETO com todos os valores substituídos.
Use formatação Markdown (# título, ## seção, **negrito**, ---).

Regras:
1. Substitua TODOS os campos identificados
2. Valores monetários: R$ X.XXX,XX
3. Datas: dd/mm/aaaa
4. Tom profissional e formal
5. Inclua TODOS os cálculos automáticos
6. NÃO adicione informações inexistentes no template

Retorne APENAS o documento formatado em Markdown.
"""


_sessions: dict[str, dict[str, Any]] = {}


def _extract_text(pdf_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            chunk = page.extract_text(x_tolerance=3, y_tolerance=3)
            if chunk:
                text += f"\n[PÁGINA {i + 1}]\n{chunk}\n"
    return text.strip()


def _build_pdf(content: str, title: str = "Proposta de Serviço") -> bytes:
    pdf = FPDF()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 35, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_y(12)
    safe = lambda s: s.encode("latin-1", "replace").decode("latin-1")
    pdf.cell(0, 10, safe(title), align="C", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(
        0,
        5,
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y as %H:%M')}",
        align="C",
        ln=True,
    )
    pdf.set_y(45)
    pdf.set_text_color(15, 23, 42)

    for line in content.split("\n"):
        lc = safe(line)
        if line.startswith("# "):
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_fill_color(241, 245, 249)
            pdf.cell(0, 8, lc[2:], ln=True, fill=True)
            pdf.ln(2)
        elif line.startswith("## "):
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(59, 130, 246)
            pdf.cell(0, 7, lc[3:], ln=True)
            pdf.set_text_color(15, 23, 42)
            pdf.ln(1)
        elif line.startswith("### "):
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, lc[4:], ln=True)
        elif line.startswith("---"):
            pdf.set_draw_color(203, 213, 225)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(3)
        elif not line.strip():
            pdf.ln(3)
        elif "**" in lc:
            parts = lc.split("**")
            pdf.set_x(20)
            for j, part in enumerate(parts):
                pdf.set_font("Helvetica", "B" if j % 2 else "", 10)
                pdf.write(5, part)
            pdf.ln(5)
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 5, lc)

    return bytes(pdf.output())


@router.post("/analyze")
async def analyze_pdf(
    file: UploadFile = File(...),
    market_password: str = Form(""),
) -> dict[str, Any]:
    """Analisa o PDF e detecta variáveis automaticamente."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")

    pdf_bytes = await file.read()
    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="O arquivo enviado está vazio.")
    if len(pdf_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400, detail="Arquivo muito grande. Limite: 10 MB."
        )

    try:
        text_content = _extract_text(pdf_bytes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Falha ao extrair texto: {exc}")

    if not text_content.strip():
        raise HTTPException(status_code=400, detail="Não foi possível extrair texto.")

    try:
        raw_response = ollama_client.generate(
            system_instruction=_SYSTEM_ANALYSIS,
            user_prompt=_ANALYSIS_PROMPT.format(text=text_content[:5000]),
        )
        data = json.loads(raw_response)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="A IA retornou formato inesperado.")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erro ao consultar IA: {exc}")

    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "text_content": text_content,
        "variables": data.get("variables", []),
        "calculations": data.get("calculations", []),
        "document_type": data.get("document_type", "Proposta de Serviço"),
    }

    return {
        "session_id": session_id,
        "document_type": data.get("document_type", "Proposta de Serviço"),
        "sections": data.get("sections", []),
        "variables": data.get("variables", []),
        "calculations": data.get("calculations", []),
        "text_preview": text_content[:500] + ("..." if len(text_content) > 500 else ""),
    }


@router.post("/generate")
async def generate_pdf(body: GenerateRequest) -> Any:
    """Gera documento PDF."""
    session = _sessions.get(body.session_id)
    if session is None:
        raise HTTPException(status_code=400, detail="Sessão não encontrada.")

    all_values = dict(body.values)
    for cid, cdata in body.calc_values.items():
        all_values[cid] = cdata.get("formatted", str(cdata.get("value", 0)))

    values_str = "\n".join(f"- {k}: {v}" for k, v in all_values.items())

    try:
        filled = ollama_client.generate(
            system_instruction=_SYSTEM_FILL,
            user_prompt=_FILL_PROMPT.format(
                template=session["text_content"][:3000],
                values=values_str,
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Erro ao gerar: {exc}")

    pdf_bytes = _build_pdf(filled, body.title)
    filename = f"proposta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    from fastapi.responses import StreamingResponse

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/session/clear")
async def clear_session(session_id: str) -> dict[str, bool]:
    """Limpa sessão da memória."""
    _sessions.pop(session_id, None)
    return {"success": True}
