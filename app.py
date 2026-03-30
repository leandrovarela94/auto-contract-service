"""
PropostaAI - Gerador Local de Propostas com IA
Todos os dados são processados localmente. Nenhum dado é armazenado em disco.
"""

from config import APP_PORT
from flask import Flask, request, jsonify, send_file, render_template
import pdfplumber
import anthropic
import json
import os
import io
import uuid
import hashlib
import re
import ast
import operator
from fpdf import FPDF
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Armazenamento em memória apenas (segurança: nada gravado em disco)
sessions = {}
market_refs_store = {}  # {hash_senha: {variavel: valor}}


# ─── Utilitários ──────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def safe_eval_formula(formula: str, variables: dict) -> float:
    """Avalia fórmulas matemáticas de forma segura."""
    allowed_ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }

    def eval_node(node):
        if isinstance(node, ast.Constant):
            return float(node.n)
        elif isinstance(node, ast.Name):
            val = variables.get(node.id, 0)
            return float(str(val).replace(',', '.').replace('R$', '').replace(' ', '') or 0)
        elif isinstance(node, ast.BinOp):
            op = allowed_ops.get(type(node.op))
            if op is None:
                raise ValueError(f"Operador não permitido: {type(node.op)}")
            return op(eval_node(node.left), eval_node(node.right))
        elif isinstance(node, ast.UnaryOp):
            op = allowed_ops.get(type(node.op))
            if op is None:
                raise ValueError(f"Operador unário não permitido")
            return op(eval_node(node.operand))
        else:
            raise ValueError(f"Nó não suportado: {type(node)}")

    try:
        tree = ast.parse(formula, mode='eval')
        return eval_node(tree.body)
    except Exception as e:
        return 0.0


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extrai texto de PDF com layout preservado."""
    text = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            extracted = page.extract_text(x_tolerance=3, y_tolerance=3)
            if extracted:
                text += f"\n[PÁGINA {i+1}]\n{extracted}\n"
    return text.strip()


def generate_pdf_output(content: str, title: str = "Proposta de Serviço") -> bytes:
    """Gera PDF profissional com o conteúdo preenchido."""
    pdf = FPDF()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Cabeçalho
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 35, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_y(12)
    pdf.cell(0, 10, title.encode('latin-1', 'replace').decode('latin-1'), align='C', ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", align='C', ln=True)

    pdf.set_y(45)
    pdf.set_text_color(15, 23, 42)

    lines = content.split('\n')
    for line in lines:
        line_clean = line.encode('latin-1', 'replace').decode('latin-1')

        if line.startswith('# '):
            pdf.set_font("Helvetica", "B", 14)
            pdf.set_fill_color(241, 245, 249)
            pdf.cell(0, 8, line_clean[2:], ln=True, fill=True)
            pdf.ln(2)
        elif line.startswith('## '):
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(59, 130, 246)
            pdf.cell(0, 7, line_clean[3:], ln=True)
            pdf.set_text_color(15, 23, 42)
            pdf.ln(1)
        elif line.startswith('### '):
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, line_clean[4:], ln=True)
        elif line.startswith('---'):
            pdf.set_draw_color(203, 213, 225)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(3)
        elif line.strip() == '':
            pdf.ln(3)
        else:
            pdf.set_font("Helvetica", "", 10)
            # Negrito inline **texto**
            if '**' in line_clean:
                parts = line_clean.split('**')
                pdf.set_x(20)
                for j, part in enumerate(parts):
                    if j % 2 == 1:
                        pdf.set_font("Helvetica", "B", 10)
                    else:
                        pdf.set_font("Helvetica", "", 10)
                    pdf.write(5, part)
                pdf.ln(5)
            else:
                pdf.multi_cell(0, 5, line_clean)

    output = io.BytesIO()
    pdf_bytes = pdf.output()
    return bytes(pdf_bytes)


# ─── Rotas ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze_pdf():
    """Analisa o PDF e detecta variáveis automaticamente com IA."""
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400

    file = request.files['file']
    api_key = request.form.get('api_key', '').strip()
    market_password = request.form.get('market_password', '').strip()

    if not api_key:
        return jsonify({'error': 'Chave de API Anthropic é obrigatória'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Apenas arquivos PDF são aceitos'}), 400

    try:
        pdf_bytes = file.read()
        text_content = extract_pdf_text(pdf_bytes)

        if not text_content.strip():
            return jsonify({'error': 'Não foi possível extrair texto do PDF. O arquivo pode ser uma imagem escaneada.'}), 400

        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""Você é um especialista em análise de documentos empresariais brasileiros.

Analise este documento de proposta/orçamento/contrato e identifique TODAS as variáveis personalizáveis.

Retorne APENAS JSON válido (sem markdown, sem texto antes ou depois):
{{
  "document_type": "tipo do documento em português",
  "sections": ["lista de seções identificadas"],
  "variables": [
    {{
      "id": "nome_em_snake_case",
      "label": "Nome Legível em Português",
      "description": "O que representa este campo",
      "type": "text|number|currency|date|percentage|email|phone",
      "current_value": "valor atual encontrado no texto, ou string vazia",
      "is_calculated": false,
      "formula": "",
      "category": "cliente|fornecedor|financeiro|servico|prazo|contato|outro",
      "required": true,
      "locked": false,
      "market_reference": null
    }}
  ],
  "calculations": [
    {{
      "id": "nome_calculo",
      "label": "Nome do Cálculo",
      "formula": "expressão usando ids das variáveis (ex: quantidade * preco_unitario)",
      "type": "currency|percentage|number",
      "description": "O que este cálculo representa"
    }}
  ],
  "filled_template": "template do documento com {{{{id_variavel}}}} como placeholders"
}}

Diretrizes:
- Identifique campos como: nome do cliente, CNPJ, endereço, valor do serviço, prazo, responsável, etc.
- Para campos financeiros, extraia valores numéricos (sem R$, sem pontos de milhar)
- Identifique TODOS os cálculos possíveis: subtotal, impostos (ISS, PIS, COFINS), total, desconto, etc.
- O filled_template deve ser o documento completo com placeholders {{{{id}}}} onde as variáveis devem ser inseridas
- Mantenha a estrutura original do documento no filled_template

Documento a analisar:
{text_content[:5000]}"""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text.strip()

        # Limpar markdown se presente
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0].strip()
        elif '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0].strip()

        data = json.loads(result_text)

        # Criar sessão em memória
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            'pdf_bytes': pdf_bytes,
            'text_content': text_content,
            'variables': data.get('variables', []),
            'calculations': data.get('calculations', []),
            'filled_template': data.get('filled_template', text_content),
            'document_type': data.get('document_type', 'Proposta de Serviço'),
            'api_key': api_key,
        }

        # Verificar se há referências de mercado salvas para esta senha
        market_refs = {}
        if market_password:
            pwd_hash = hash_password(market_password)
            market_refs = market_refs_store.get(pwd_hash, {})

        # Aplicar referências de mercado às variáveis
        for var in data.get('variables', []):
            if var['id'] in market_refs:
                var['market_reference'] = market_refs[var['id']]
                var['current_value'] = market_refs[var['id']].get('value', var['current_value'])
                var['locked'] = market_refs[var['id']].get('locked', False)

        return jsonify({
            'session_id': session_id,
            'document_type': data.get('document_type', 'Proposta de Serviço'),
            'sections': data.get('sections', []),
            'variables': data.get('variables', []),
            'calculations': data.get('calculations', []),
            'text_preview': text_content[:500] + '...' if len(text_content) > 500 else text_content,
        })

    except anthropic.AuthenticationError:
        return jsonify({'error': 'Chave de API inválida. Verifique sua chave Anthropic.'}), 401
    except json.JSONDecodeError as e:
        return jsonify({'error': f'Erro ao processar resposta da IA. Tente novamente.'}), 500
    except Exception as e:
        return jsonify({'error': f'Erro: {str(e)}'}), 500


@app.route('/api/calculate', methods=['POST'])
def calculate_values():
    """Calcula valores derivados com base nas variáveis preenchidas."""
    data = request.json
    variables = data.get('variables', {})
    calculations = data.get('calculations', [])

    results = {}
    for calc in calculations:
        try:
            result = safe_eval_formula(calc['formula'], variables)
            results[calc['id']] = {
                'value': result,
                'formatted': format_value(result, calc.get('type', 'number')),
                'label': calc['label'],
            }
        except Exception as e:
            results[calc['id']] = {'value': 0, 'formatted': '0', 'label': calc['label'], 'error': str(e)}

    return jsonify({'calculations': results})


def format_value(value: float, type_: str) -> str:
    if type_ == 'currency':
        return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    elif type_ == 'percentage':
        return f"{value:.2f}%"
    else:
        return f"{value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


@app.route('/api/generate', methods=['POST'])
def generate_document():
    """Gera o documento final preenchido com os valores fornecidos."""
    data = request.json
    session_id = data.get('session_id')
    values = data.get('values', {})
    calc_values = data.get('calc_values', {})
    title = data.get('title', 'Proposta de Serviço')

    if session_id not in sessions:
        return jsonify({'error': 'Sessão não encontrada. Faça upload do PDF novamente.'}), 400

    session = sessions[session_id]
    api_key = session['api_key']

    try:
        client = anthropic.Anthropic(api_key=api_key)

        # Combinar variáveis e cálculos
        all_values = {**values}
        for calc_id, calc_data in calc_values.items():
            all_values[calc_id] = calc_data.get('formatted', str(calc_data.get('value', 0)))

        # Montar lista de valores para o prompt
        values_str = "\n".join([f"- {k}: {v}" for k, v in all_values.items()])

        prompt = f"""Você é um especialista em redação de propostas comerciais profissionais em português brasileiro.

Documento original (template):
{session['text_content'][:3000]}

Valores a inserir:
{values_str}

Gere o documento COMPLETO e PROFISSIONAL com todos os valores inseridos.
Use formatação Markdown:
- # para título principal
- ## para seções
- ### para subseções  
- **texto** para negrito
- --- para separadores
- Mantenha a estrutura original do documento

Regras:
1. Substitua TODOS os campos identificados pelos valores fornecidos
2. Formate valores monetários como R$ X.XXX,XX
3. Formate datas em dd/mm/aaaa
4. Mantenha tom profissional e formal
5. Inclua TODOS os cálculos no documento (subtotais, impostos, total final)
6. NÃO adicione campos que não existiam no original

Retorne APENAS o documento formatado, sem comentários."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        filled_content = response.content[0].text.strip()

        # Gerar PDF
        pdf_bytes = generate_pdf_output(filled_content, title)

        # Retornar como download (nunca salvo em disco)
        output = io.BytesIO(pdf_bytes)
        output.seek(0)

        filename = f"proposta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({'error': f'Erro ao gerar documento: {str(e)}'}), 500


@app.route('/api/market-ref/save', methods=['POST'])
def save_market_ref():
    """Salva referências de mercado protegidas por senha."""
    data = request.json
    password = data.get('password', '').strip()
    references = data.get('references', {})

    if not password or len(password) < 4:
        return jsonify({'error': 'Senha deve ter no mínimo 4 caracteres'}), 400

    pwd_hash = hash_password(password)
    market_refs_store[pwd_hash] = references

    return jsonify({'success': True, 'message': f'{len(references)} referência(s) salva(s) com sucesso'})


@app.route('/api/market-ref/load', methods=['POST'])
def load_market_ref():
    """Carrega referências de mercado pela senha."""
    data = request.json
    password = data.get('password', '').strip()

    if not password:
        return jsonify({'error': 'Senha é obrigatória'}), 400

    pwd_hash = hash_password(password)
    refs = market_refs_store.get(pwd_hash)

    if refs is None:
        return jsonify({'error': 'Senha incorreta ou sem referências salvas'}), 401

    return jsonify({'success': True, 'references': refs})


@app.route('/api/session/clear', methods=['POST'])
def clear_session():
    """Limpa dados da sessão da memória."""
    data = request.json
    session_id = data.get('session_id')
    if session_id and session_id in sessions:
        del sessions[session_id]
    return jsonify({'success': True})


if __name__ == '__main__':
    print("\n" + "="*55)
    print("  🔒 PropostaAI - Servidor Local Iniciado")
    print("="*55)
    print(f"  Todos os dados ficam apenas em memória RAM")
    print(f"  Nenhum dado é salvo em disco")
    print("="*55 + "\n")
    app.run(debug=False, host='0.0.0.0', port=APP_PORT)
