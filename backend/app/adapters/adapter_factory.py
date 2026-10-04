# app/adapters/adapter_factory.py
"""
Módulo: adapter_factory.py

Explicação:
Fabrica de adaptadores de provedores de mensagem. Centraliza a criacao do
adaptador correto aplicando o padrao Factory Method, de modo que a camada de
negocio dependa apenas do contrato BaseMessageAdapter e nunca da
implementacao concreta do provedor.

O transporte vem de `Canal.tipo` (whatsapp, telegram, pabx, ...). Quando um
mesmo transporte atende mais de um fornecedor — WhatsApp e servido tanto
pela Evolution API quanto pela Meta Cloud API — o `provedor` desambigua.
A resolucao padrao de WhatsApp e Evolution API, que e o que o produto ja
usa hoje em producao.

Funcionalidades:
- `get_adapter`: devolve o adaptador para um canal e, opcionalmente, um provedor
- `registrar`: registra adaptador customizado em tempo de execucao
- `supported`: lista os transportes com adaptador registrado

EXEMPLO PRATICO
───────────────
    from app.adapters import get_adapter

    adapter = get_adapter("telegram")
    await adapter.send_text(chat_id="123", text="Ola")

    adapter = get_adapter("whatsapp", provedor="meta_cloud")
    await adapter.send_text(chat_id="5567...", text="Ola")

RELACIONAMENTO
──────────────
    Canal.tipo + Canal.provedor
        │
        └──► adapter_factory.get_adapter()
                  │
                  ├──► EvolutionAdapter      (whatsapp, padrao)
                  ├──► MetaCloudAdapter     (whatsapp + meta_cloud)
                  ├──► TelegramAdapter      (telegram)
                  └──► PABXVoIPAdapter      (pabx | voip | sms)
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, List

from app.adapters.base_message_adapter import BaseMessageAdapter
from app.adapters.providers.evolution_adapter import EvolutionAdapter
from app.adapters.providers.meta_cloud_adapter import MetaCloudAdapter
from app.adapters.providers.pabx_voip_adapter import PABXVoIPAdapter
from app.adapters.providers.telegram_adapter import TelegramAdapter

logger = logging.getLogger(__name__)


#: Provedor preferido quando o transporte nao informa qual usar.
PROVEDOR_PADRAO: Dict[str, str] = {
    "whatsapp": "evolution",
}


#: Registro de provedores: "transporte:provedor" -> construtor do adaptador.
#: A chave composta permite que dois fornecedores sirvam o mesmo transporte.
#: `pabx` e `sms` caem no mesmo `PABXVoIPAdapter` porque compartilham o
#: mesmo transporte HTTP do tronco VoIP.
_REGISTRO: Dict[str, Callable[[], BaseMessageAdapter]] = {
    "whatsapp:evolution": EvolutionAdapter,
    "whatsapp:meta_cloud": MetaCloudAdapter,
    "telegram:telegram": TelegramAdapter,
    "pabx:voip": PABXVoIPAdapter,
    "voip:voip": PABXVoIPAdapter,
    "sms:sms": PABXVoIPAdapter,
}

#: Atalho para as chaves nao-compostas, usadas por `registrar`.
_ALIASES: Dict[str, str] = {
    "whatsapp": "whatsapp:evolution",
    "meta_cloud": "whatsapp:meta_cloud",
    "meta": "whatsapp:meta_cloud",
    "cloud_api": "whatsapp:meta_cloud",
    "telegram": "telegram:telegram",
    "pabx": "pabx:voip",
    "voip": "voip:voip",
    "sms": "sms:sms",
}


def registrar(canal: str, construtor: Callable[[], BaseMessageAdapter]) -> None:
    """
    Registra um adaptador para um transporte.

    Permite que o produto plugue um provedor novo sem tocar na camada de
    negocio: basta fornecer um construtor que devolva BaseMessageAdapter.

    Args:
        canal: Transporte (ex: "signal", "matrix") ou chave composta
            (ex: "signal:signal").
        construtor: Fabrica que devolve uma BaseMessageAdapter.
    """
    chave = canal.strip().lower()
    _REGISTRO[_ALIASES.get(chave, chave)] = construtor
    logger.info("adapter_factory | provedor registrado: %s", chave)


def get_adapter(canal: str, provedor: str | None = None) -> BaseMessageAdapter:
    """
    Devolve o adaptador do canal solicitado.

    Args:
        canal: Transporte, aceitando o valor do enum `TipoCanalMensageria`
            (que herda de `str`) ou o proprio enum.
        provedor: Fornecedor quando o transporte tiver mais de um. Se
            ausente, usa `PROVEDOR_PADRAO`.

    Returns:
        Instancia de BaseMessageAdapter pronta para uso.

    Raises:
        ValueError: Se nao houver adaptador registrado para o par
            (canal, provedor).
    """
    transporte = str(getattr(canal, "value", canal)).strip().lower()
    fornecedor = (provedor or PROVEDOR_PADRAO.get(transporte) or transporte).strip().lower()

    # A chave e composta, mas pode ter sido registrada por atalho
    # ("pabx" em vez de "pabx:voip"). Resolve o atalho antes de desistir.
    chave = f"{transporte}:{fornecedor}"
    if chave not in _REGISTRO:
        chave = _ALIASES.get(transporte, chave)

    construtor = _REGISTRO.get(chave)
    if construtor is None:
        disponiveis = ", ".join(sorted(_REGISTRO))
        raise ValueError(
            f"Nenhum adaptador registrado para '{transporte}' / '{fornecedor}'. "
            f"Disponiveis: {disponiveis}"
        )

    return construtor()


def supported() -> List[str]:
    """Lista as chaves transporte:provedor com adaptador registrado."""
    return sorted(_REGISTRO)


__all__ = [
    "get_adapter",
    "registrar",
    "supported",
    "PROVEDOR_PADRAO",
    "BaseMessageAdapter",
]