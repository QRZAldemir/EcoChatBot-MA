"""
================================================================================
MÓDULO: app/services/bot_handlers/mensagem_payload.py
AUTOR: Aldemir Queiroz
DATA: 2026-09-26
VERSÃO: 0.1.0
OBJETIVO: DTO em memória para o payload de mensagem trocado entre a máquina de
          estados e os handlers do bot. NÃO é entidade ORM e NÃO possui tabela:
          substitui o antigo model `Mensagem`, que nunca existiu na camada
          moderna e bloqueava o carregamento deste pacote.
PASTA: backend/app/services/bot_handlers/
================================================================================
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class MensagemPayload:
    tipo: str = "text"
    conteudo: str = ""
    remetente: Optional[str] = None
    destino: Optional[str] = None
    identificador: Optional[str] = None
    bruto: Dict[str, Any] = field(default_factory=dict)
