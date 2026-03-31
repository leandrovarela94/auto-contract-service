"""
Routes Templates — CRUD de templates.
"""

from __future__ import annotations

import io
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile

from services.template_service import TemplateService

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("")
async def list_templates() -> dict[str, Any]:
    """Lista todos os templates."""
    templates = TemplateService.list_templates()
    return {"templates": templates, "count": len(templates)}


@router.get("/{template_id}")
async def get_template(template_id: str) -> dict[str, Any]:
    """Retorna um template específico."""
    template = TemplateService.get_template(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    return template


@router.post("")
async def create_template(body: dict) -> dict[str, Any]:
    """Cria novo template."""
    if "name" not in body or not body["name"]:
        raise HTTPException(status_code=400, detail="Nome é obrigatório")
    result = TemplateService.save_template(body)
    return {"success": True, "template_id": result["id"]}


@router.put("/{template_id}")
async def update_template(template_id: str, body: dict) -> dict[str, Any]:
    """Atualiza template."""
    try:
        TemplateService.update_template(template_id, body)
        return {"success": True, "template_id": template_id}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Template não encontrado")


@router.delete("/{template_id}")
async def delete_template(template_id: str) -> dict[str, Any]:
    """Remove template."""
    try:
        TemplateService.delete_template(template_id)
        return {"success": True, "template_id": template_id}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Template não encontrado")


@router.get("/{template_id}/export")
async def export_template_file(template_id: str) -> Any:
    """Baixa template como JSON."""
    template = TemplateService.get_template(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template não encontrado")

    json_str = json.dumps(template, ensure_ascii=False, indent=2)
    filename = f"template_{template.get('name', template_id).replace(' ', '_')}.json"

    from fastapi.responses import StreamingResponse

    return StreamingResponse(
        io.BytesIO(json_str.encode("utf-8")),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import")
async def import_template(file: UploadFile = File(...)) -> dict[str, Any]:
    """Importa template de JSON."""
    if not file.filename or not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Apenas arquivos JSON são aceitos.")

    try:
        content = await file.read()
        template_data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Arquivo JSON inválido.")

    if "name" not in template_data:
        raise HTTPException(
            status_code=400, detail="Template inválido: nome é obrigatório."
        )

    result = TemplateService.save_template(template_data)
    return {
        "success": True,
        "template_id": result["id"],
        "name": template_data.get("name"),
    }
