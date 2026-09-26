"""
================================================================================
NÚCLEO DO SISTEMA - CLASSE BASE
================================================================================
Arquivo: bot_handlers/core.py
DESENVOLVEDOR: Aldemir Queiroz
DATA: 2026-08-16

CONCEITOS OOP:
  1. HERANÇA: Todos os handlers herdam desta classe base
  2. POLIMORFISMO: Cada handler implementa processar() de forma diferente
  3. ENCAPSULAMENTO: Métodos protegidos (_) para uso interno
  4. ABSTRAÇÃO: Interface comum para todos os departamentos (via ABC)

PRIVACIDADE E LGPD/GDPR:
  - NUNCA logar dados pessoais. Logar apenas IDs e metadados.
================================================================================
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
import logging

# Imports internos do projeto
from app.models import Atendimento
from app.services.bot_handlers.mensagem_payload import MensagemPayload
from .privacy import hash_telefone, is_chave_sensivel, detectar_tipo_arquivo
from .validators import validar_campo
from .utils import gerar_protocolo

logger = logging.getLogger(__name__)


class DepartamentoHandler(ABC):
    """
    CLASSE BASE ABSTRATA: Handler de Departamento
    Não deve ser instanciada diretamente.
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.contexto_cache: Dict[int, Dict[str, Any]] = {}
        
    @abstractmethod
    async def processar(
        self,
        atendimento: Atendimento,
        step: str,
        mensagem: MensagemPayload,
    ) -> None:
        """
        MÉTODO ABSTRATO: Processa mensagem do departamento.
        Deve ser implementado por todas as classes filhas.
        """
        pass
    
    # ══════════════════════════════════════════════════════════════
    # COMUNICAÇÃO (Com Tratamento de Erros Seguro)
    # ══════════════════════════════════════════════════════════════
    
    async def _enviar_texto(self, atendimento: Atendimento, texto: str) -> bool:
        try:
            # TODO: Integrar com Evolution API
            # await self.evolution.send_text(atendimento.numero, texto)
            
            logger.info(
                "mensagem_texto_enviada",
                atendimento_id=atendimento.id,
                tamanho_texto=len(texto),
                telefone_hash=hash_telefone(getattr(atendimento, 'numero', ''))
            )
            return True
        except Exception as e:
            logger.error(
                "erro_ao_enviar_texto",
                atendimento_id=atendimento.id,
                erro=str(e),
                exc_info=True # Registra o stack trace completo para depuração
            )
            return False

    async def _enviar_lista(self, atendimento: Atendimento, titulo: str, descricao: str, rows: List[Dict[str, str]], botao_texto: str = "Ver opções") -> bool:
        try:
            # TODO: Integrar com Evolution API
            logger.info("lista_enviada", atendimento_id=atendimento.id, qtd_opcoes=len(rows))
            return True
        except Exception as e:
            logger.error("erro_ao_enviar_lista", atendimento_id=atendimento.id, erro=str(e))
            return False

    # ══════════════════════════════════════════════════════════════
    # GERENCIAMENTO DE ESTADO E CONTEXTO
    # ══════════════════════════════════════════════════════════════
    
    def _avancar_step(self, atendimento: Atendimento, novo_step: str) -> None:
        atendimento.step = novo_step
        # TODO: self.session.commit()
        logger.debug("step_avancado", atendimento_id=atendimento.id, novo_step=novo_step)
    
    def _guardar_contexto(self, atendimento_id: int, chave: str, valor: Any) -> None:
        if atendimento_id not in self.contexto_cache:
            self.contexto_cache[atendimento_id] = {}
        self.contexto_cache[atendimento_id][chave] = valor
        
        # Log seguro sem expor o valor
        valor_info = f"{type(valor).__name__}({len(valor)} items)" if isinstance(valor, (dict, list, str)) else type(valor).__name__
        
        logger.debug(
            "contexto_salvo",
            atendimento_id=atendimento_id,
            chave=chave,
            tipo_valor=valor_info,
            eh_sensivel=is_chave_sensivel(chave)
        )
    
    def _obter_contexto(self, atendimento_id: int, chave: str) -> Optional[Any]:
        # NOTA: Não usamos @lru_cache aqui pois o contexto é mutável. 
        # O cache em memória (self.contexto_cache) é mais seguro para o ciclo de vida da requisição.
        return self.contexto_cache.get(atendimento_id, {}).get(chave)

    def _limpar_contexto_completo(self, atendimento_id: int) -> None:
        if atendimento_id in self.contexto_cache:
            del self.contexto_cache[atendimento_id]
        logger.debug("contexto_limpo", atendimento_id=atendimento_id)

    # ══════════════════════════════════════════════════════════════
    # UTILITÁRIOS EXPOSTOS
    # ══════════════════════════════════════════════════════════════
    
    def validar(self, valor: str, tipo: str = "texto", **kwargs) -> tuple[bool, Optional[str]]:
        """Atalho para o módulo de validação."""
        return validar_campo(valor, tipo, **kwargs)

    def gerar_protocolo(self, prefixo: str = "PROT") -> str:
        return gerar_protocolo(prefixo)