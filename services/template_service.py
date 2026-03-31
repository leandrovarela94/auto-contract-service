"""
Template Service — Persistência e gerenciamento de templates de contratos.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


class TemplateService:
    """Serviço para gerenciar templates de contratos."""

    _TEMPLATES_DIR = Path(__file__).parent.parent / "data"

    @classmethod
    def _get_template_path(cls, template_id: str) -> Path:
        cls._TEMPLATES_DIR.mkdir(exist_ok=True)
        return cls._TEMPLATES_DIR / f"{template_id}.json"

    @classmethod
    def list_templates(cls) -> list[dict[str, Any]]:
        """Lista todos os templates salvos."""
        templates = []
        if not cls._TEMPLATES_DIR.exists():
            return templates
        for file in cls._TEMPLATES_DIR.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    templates.append(
                        {
                            "id": data.get("id", file.stem),
                            "name": data.get("name", "Sem nome"),
                            "description": data.get("description", ""),
                            "document_type": data.get("document_type", "Contrato"),
                            "variable_count": len(data.get("variables", [])),
                            "created_at": data.get("created_at", ""),
                            "updated_at": data.get("updated_at", ""),
                            "version": data.get("version", "1.0"),
                        }
                    )
            except Exception:
                continue
        return sorted(templates, key=lambda x: x.get("updated_at", ""), reverse=True)

    @classmethod
    def get_template(cls, template_id: str) -> dict[str, Any] | None:
        """Retorna um template pelo ID."""
        path = cls._get_template_path(template_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    @classmethod
    def save_template(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Salva um novo template."""
        cls._TEMPLATES_DIR.mkdir(exist_ok=True)
        template_id = data.get("id", str(uuid.uuid4()))
        data["id"] = template_id
        data["updated_at"] = datetime.now().isoformat()
        if not data.get("created_at"):
            data["created_at"] = datetime.now().isoformat()
        path = cls._get_template_path(template_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"id": template_id, "success": True}

    @classmethod
    def update_template(cls, template_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Atualiza um template existente."""
        existing = cls.get_template(template_id)
        if not existing:
            raise FileNotFoundError(f"Template {template_id} não encontrado")
        existing.update(data)
        existing["id"] = template_id
        existing["updated_at"] = datetime.now().isoformat()
        path = cls._get_template_path(template_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        return {"id": template_id, "success": True}

    @classmethod
    def delete_template(cls, template_id: str) -> dict[str, Any]:
        """Deleta um template."""
        path = cls._get_template_path(template_id)
        if path.exists():
            path.unlink()
            return {"id": template_id, "success": True}
        raise FileNotFoundError(f"Template {template_id} não encontrado")
