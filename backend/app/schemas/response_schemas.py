"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Schemas de Resposta Padronizados
───────────────────────────────────────────────────────────────────────────
@file     response_schemas.py
@module   Backend / App / Schemas
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Define os schemas Pydantic para respostas padronizadas da API, garantindo
consistência no formato de sucesso e erro em todos os endpoints.

REGRAS DE NEGÓCIO
─────────────────
    • Todas as respostas de erro seguem o formato: { "detail": { ... } }
    • Em produção, stack traces NUNCA são expostos ao cliente
    • Em desenvolvimento (DEBUG=True), detalhes técnicos são incluídos
    • Códigos de erro são padronizados para facilitar debugging no frontend
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponseDetail(BaseModel):
    """
    Detalhe estruturado de um erro.
    """
    codigo: str = Field(
        ...,
        description="Código único do erro para referência na documentação",
        examples=["VALIDATION_ERROR", "NOT_FOUND", "INTERNAL_ERROR"],
    )
    mensagem: str = Field(
        ...,
        description="Mensagem legível para o usuário final",
        examples=["Recurso não encontrado", "Dados inválidos no request body"],
    )
    detalhes: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = Field(
        default=None,
        description="Detalhes adicionais (ex: campos inválidos, stack trace em debug)",
    )


class ErrorResponse(BaseModel):
    """
    Schema padrão para respostas de erro da API.
    """
    detail: ErrorResponseDetail


class SuccessResponse(BaseModel, Generic[T]):
    """
    Schema padrão para respostas de sucesso da API.

    ─────────────────────────────────────────────────────────────────────
    POR QUE GENÉRICO
    ─────────────────────────────────────────────────────────────────────
    Para poder ser usado como `response_model=SuccessResponse[Canal]`.

    Sem o `[T]`, o FastAPI serializa o envelope mas joga o schema real
    fora: o OpenAPI mostraria `dados` sem tipo e o Swagger aceitaria
    qualquer objeto — a documentação mente sobre o que a rota devolve.

    ─────────────────────────────────────────────────────────────────────
    POR QUE `dados` E NÃO O NOME DO RECURSO
    ─────────────────────────────────────────────────────────────────────
    O envelope é o mesmo em toda a API. Se cada rota nomeasse o seu
    (`canal`, `mensagens`, `registros`), o frontend teria um `if` por
    endpoint. Com `dados`, uma tela nova consome qualquer rota sem
    bespoke.
    """
    mensagem: str = Field(
        ...,
        description="Mensagem de sucesso",
        examples=["Recurso criado com sucesso"],
    )
    dados: Optional[T] = Field(
        default=None,
        description="Dados retornados pela operação",
    )


class ValidationErrorDetail(BaseModel):
    """
    Detalhe de erro de validação de um campo específico.
    """
    loc: List[str] = Field(
        ...,
        description="Localização do erro (ex: ['body', 'email'])",
    )
    msg: str = Field(
        ...,
        description="Mensagem de erro",
    )
    type: str = Field(
        ...,
        description="Tipo do erro de validação",
    )


class ValidationErrorResponse(BaseModel):
    """
    Schema para respostas de erro de validação (422 Unprocessable Entity).
    """
    detail: ErrorResponseDetail = Field(
        ...,
        description="Detalhe do erro de validação",
    )