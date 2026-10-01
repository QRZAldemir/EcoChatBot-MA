"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Exception Handlers Globais
───────────────────────────────────────────────────────────────────────────
@file     exception_handlers.py
@module   Backend / App / Core
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Implementa handlers globais para capturar todas as exceções não tratadas
no FastAPI, retornando respostas JSON padronizadas e evitando vazamento
de stack traces em produção.

REGRAS DE NEGÓCIO
─────────────────
    • HTTPException: retorna o detail original (já padronizado)
    • RequestValidationError: retorna lista de campos inválidos
    • EcoChatBotException: retorna código e mensagem da exceção customizada
    • Exception genérica: retorna 500 com mensagem genérica (sem stack trace)
    • Em modo DEBUG, inclui detalhes técnicos para facilitar desenvolvimento
    • Todos os erros são logados com nível apropriado para monitoramento
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import logging
from typing import Union

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.config import settings
from app.core.exceptions import EcoChatBotException

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler para HTTPException (erros 4xx lançados manualmente).
    
    Exemplos:
        - raise HTTPException(status_code=404, detail="Recurso não encontrado")
        - raise HTTPException(status_code=401, detail="Token inválido")
    """
    from fastapi import HTTPException
    
    if not isinstance(exc, HTTPException):
        # Se não é HTTPException, delega para o handler genérico
        return await generic_exception_handler(request, exc)
    
    # Log do erro
    logger.warning(
        "HTTPException | method=%s | path=%s | status=%d | detail=%s",
        request.method,
        request.url.path,
        exc.status_code,
        exc.detail,
    )
    
    # Constrói resposta padronizada
    detail = {
        "codigo": f"HTTP_{exc.status_code}",
        "mensagem": exc.detail if isinstance(exc.detail, str) else "Erro na requisição",
    }
    
    # Em modo debug, inclui detalhes adicionais
    if settings.DEBUG and isinstance(exc.detail, dict):
        detail["detalhes"] = exc.detail
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detail},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handler para erros de validação do Pydantic/FastAPI (422 Unprocessable Entity).
    
    Captura erros como:
        - Campo obrigatório ausente
        - Tipo de dado incorreto
        - Validação de schema falhou
    """
    # Log detalhado do erro de validação
    logger.warning(
        "ValidationError | method=%s | path=%s | errors=%s",
        request.method,
        request.url.path,
        exc.errors(),
    )
    
    # Constrói lista de erros formatada
    erros_formatados = []
    for erro in exc.errors():
        erros_formatados.append({
            "loc": erro.get("loc", []),
            "msg": erro.get("msg", ""),
            "type": erro.get("type", ""),
        })
    
    # Resposta padronizada
    detail = {
        "codigo": "VALIDATION_ERROR",
        "mensagem": "Dados inválidos na requisição",
        "detalhes": erros_formatados,
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": detail},
    )


async def pydantic_validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    Handler para erros de validação do Pydantic (modelos de dados).
    """
    logger.warning(
        "PydanticValidationError | method=%s | path=%s | errors=%s",
        request.method,
        request.url.path,
        exc.errors(),
    )
    
    detail = {
        "codigo": "PYDANTIC_VALIDATION_ERROR",
        "mensagem": "Erro de validação nos dados",
        "detalhes": exc.errors(),
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": detail},
    )


async def ecochatbot_exception_handler(request: Request, exc: EcoChatBotException) -> JSONResponse:
    """
    Handler para exceções customizadas do EcoChatBot-MA.
    """
    # Log com nível apropriado baseado no status code
    if exc.status_code >= 500:
        logger.error(
            "EcoChatBotException | method=%s | path=%s | status=%d | codigo=%s | mensagem=%s",
            request.method,
            request.url.path,
            exc.status_code,
            exc.codigo,
            exc.mensagem,
        )
    else:
        logger.warning(
            "EcoChatBotException | method=%s | path=%s | status=%d | codigo=%s | mensagem=%s",
            request.method,
            request.url.path,
            exc.status_code,
            exc.codigo,
            exc.mensagem,
        )
    
    # Constrói resposta
    detail = {
        "codigo": exc.codigo,
        "mensagem": exc.mensagem,
    }
    
    # Em modo debug, inclui detalhes técnicos
    if settings.DEBUG and exc.detalhes:
        detail["detalhes"] = exc.detalhes
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detail},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler genérico para capturar TODAS as exceções não previstas.
    
    ⚠️ CRÍTICO: Este handler evita vazamento de stack traces em produção.
    """
    # Log completo do erro (stack trace) para debugging no servidor
    logger.exception(
        "UnhandledException | method=%s | path=%s | exception=%s | type=%s",
        request.method,
        request.url.path,
        str(exc),
        type(exc).__name__,
    )
    
    # Resposta segura para o cliente
    detail = {
        "codigo": "INTERNAL_SERVER_ERROR",
        "mensagem": "Erro interno do servidor. Tente novamente mais tarde.",
    }
    
    # Em modo debug, inclui detalhes técnicos (NUNCA em produção)
    if settings.DEBUG:
        import traceback
        detail["detalhes"] = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc(),
        }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": detail},
    )