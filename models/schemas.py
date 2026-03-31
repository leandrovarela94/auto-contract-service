"""
Schemas Pydantic — Modelos de dados validados.
"""

from pydantic import BaseModel, Field


class CalculateRequest(BaseModel):
    variables: dict[str, str]
    calculations: list[dict[str, str]]


class GenerateRequest(BaseModel):
    session_id: str
    values: dict[str, str]
    calc_values: dict[str, str] = {}
    title: str = "Proposta de Serviço"


class MarketRefSaveRequest(BaseModel):
    password: str
    references: dict[str, str]

    @Field(min_length=4)
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v.strip()) < 4:
            raise ValueError("Senha deve ter no mínimo 4 caracteres")
        return v.strip()


class MarketRefLoadRequest(BaseModel):
    password: str


class SessionClearRequest(BaseModel):
    session_id: str


class TemplateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    document_type: str = "Contrato"
    sections: list[str] = []
    variables: list[dict[str, str]] = []
    calculations: list[dict[str, str]] = []
    original_text: str = ""


class TemplateUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    variables: list[dict[str, str]] | None = None
    calculations: list[dict[str, str]] | None = None


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    document_type: str
    variable_count: int
    created_at: str
    updated_at: str


class AnalyzeResponse(BaseModel):
    session_id: str
    document_type: str
    sections: list[str]
    variables: list[dict]
    calculations: list[dict]
    text_preview: str
