"""
Ponte entre as exceções de domínio e as respostas HTTP.

POR QUE ISTO EXISTE
-------------------
O serviço levanta `RecursoNaoEncontradoException` (404), `ConflictException`
(409) e `RecursoInvalidoError` (422). O FastAPI SÓ converte `HTTPException` e
`RequestValidationError` automaticamente — as demais viram 500 genérico.

Até aqui o padrão dos routers era:

    except HTTPException: raise
    except Exception as e:  raise HTTPException(500, str(e))

Esse `except Exception` é o que apaga o código certo: um "contato não
encontrado" (404) saía como 500. Este tradutor preserva o `status_code` que a
própria exceção carrega.

POR QUE NÃO É UM HANDLER GLOBAL
-------------------------------
`app/main.py` ainda não existe, então não há `FastAPI()` onde registrar
`@app.exception_handler`. Quando ele existir, este módulo deve virar handler
global e as chamadas nos routers podem sumir. O helper continua válido como
tradutor unitário.
"""
from contextlib import contextmanager

from fastapi import HTTPException

from app.exceptions import (
    ConflictException,
    EcoChatBotException,
    NegocioException,
)


@contextmanager
def traduzir_erro_de_negocio():
    """Converte exceção de domínio em `HTTPException` com o status original.

    Uso:

        with traduzir_erro_de_negocio():
            contato = await service.buscar_por_id(contato_id, empresa.id)
    """
    try:
        yield
    except HTTPException:
        # Já é HTTP (ex.: `Depends` de RBAC); preserva como está.
        raise
    except (NegocioException, ConflictException, EcoChatBotException) as exc:
        raise HTTPException(
            status_code=getattr(exc, 'status_code', 400),
            detail=exc.message,
        ) from exc
