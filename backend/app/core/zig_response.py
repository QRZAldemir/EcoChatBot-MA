"""
================================================================================
MÓDULO: app/core/zig_response.py
AUTOR: Aldemir Queiroz
DATA: 2026-09-26
VERSÃO: 1.0.0
OBJETIVO: Envelope padrão de resposta da API, compatível com o ZigChat.
PASTA: backend/app/core/
================================================================================

POR QUE ESTE MÓDULO EXISTE
--------------------------
    O `ZigResponse` estava DEFINIDO DENTRO de dois routers — `mensagens_routers`
    e `atendimentos_routers` — e um terceiro (`canais_routers`) tentava
    importá-lo de `app.utils.zig_response`, que nunca existiu. Três cópias,
    uma delas quebrada, e o contrato de resposta dependia de qual arquivo o
   _request_ tivesse sido importado.

    Um envelope de resposta é contrato de API: precisa ter UM lugar só.

    `codigo` é 0 para sucesso e 1 para erro, e `dados` NUNCA é omitido — o
    front sempre recebe a mesma forma, mesmo no erro.
================================================================================
"""
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ZigResponse(BaseModel, Generic[T]):
    """
    Envelope padrão de resposta (compatível com ZigChat).

    É GENÉRICO de propósito: os routers declaram `ZigResponse[CanalContratadoResponse]`
    para que o OpenAPI descreva o tipo real de `dados`. Sem `Generic`, essa
    parametrização levanta `TypeError` na importação do router.

    `mensagem` existe porque TODOS os pontos de chamada passam `mensagem=`.
    Antes ela não estava no modelo, e o Pydantic v2 descarta campo extra em
    silêncio — ou seja, a API nunca devolvia a mensagem que o router jurava
    estar devolvendo. O front ficava sem ela sem nenhum erro visível.
    """

    codigo: int  # 0 = sucesso, 1 = erro
    mensagem: Optional[str] = None
    erro: Optional[str] = None
    dados: Optional[T] = None


__all__ = ["ZigResponse"]
