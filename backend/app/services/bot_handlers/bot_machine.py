"""
================================================================================
PROJETO.......: EcoChatBotMarcx — Sistema de Atendimento Digital Configurável
ARQUIVO.......: bot_handlers/bot_machine.py
AUTOR.........: Aldemir Queiroz
DATA..........: 08/09/2026
VERSÃO........: 1.0.0

PROPÓSITO:
Orquestrador principal da máquina de estados do bot.
Recebe o webhook, identifica o estado atual e despacha para o handler correto.

EVOLUÇÃO ARQUITETURAL:
  ANTES (Anti-pattern): Lógica procedural gigante, contexto global (ContextVar).
  DEPOIS (OOP Puro): Classe que encapsula estado, injeção de dependência (DI),
                     totalmente testável e extensível (White-Label).

CONCEITOS PYTHON APLICADOS:
  1. Type Hinting: Documenta o tipo de variáveis (como no Delphi moderno).
  2. Async/Await: Programação assíncrona não-bloqueante.
  3. Dependency Injection: Receber dependências no construtor.
  4. Tuplas de Retorno: Retornar múltiplos valores (sucesso + mensagem de erro).
================================================================================
"""

import logging
import traceback
from datetime import datetime
import uuid
from typing import Optional, Dict, Any, Tuple

from sqlalchemy.orm import Session

from app.models import Atendimento, AtendimentoContext, Mensagem
from .core import DepartamentoHandler
from .evolution_client import EvolutionApiClient

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES DE ESTADO (MÁQUINA DE ESTADOS)
# ═══════════════════════════════════════════════════════════════════════════════
ESTADO_BOOT = "BOOT"
ESTADO_AGUARDAR_LGPD = "AGUARDAR_LGPD"
ESTADO_AGUARDAR_NOME = "AGUARDAR_NOME"
ESTADO_AGUARDAR_HUB = "AGUARDAR_HUB"
ESTADO_EM_ATENDIMENTO = "EM_ATENDIMENTO"
ESTADO_FINALIZADO = "FINALIZADO"


class BotMaquinaEstados:
    """
    CLASSE PRINCIPAL: Orquestra toda a máquina de estados.
    """

    def __init__(
        self,
        db: Session,
        evolution_client: EvolutionApiClient,
        handlers: Optional[Dict[str, DepartamentoHandler]] = None,
    ):
        self._db = db
        self._evolution = evolution_client
        self._handlers = handlers or {}

        logger.info(
            "BotMaquinaEstados inicializado | handlers_registrados=%s",
            list(self._handlers.keys()),
        )

    # ═══════════════════════════════════════════════════════════════════════════════
    # PONTO DE ENTRADA PÚBLICO
    # ═══════════════════════════════════════════════════════════════════════════════

    async def processar_mensagem_recebida(
        self,
        instance_nome: str,
        remote_jid: str,
        push_name: Optional[str],
        msg_type: str,
        content: str,
    ) -> None:
        """
        Ponto de entrada chamado pelo Webhook da Evolution API.
        """
        if remote_jid.endswith("@g.us"):
            logger.debug("Mensagem de grupo ignorada: %s", remote_jid)
            return

        telefone = self._extrair_telefone(remote_jid)
        atendimento, eh_novo = self._buscar_ou_criar_atendimento(
            telefone, instance_nome, push_name
        )

        estado_atual = self._obter_estado(atendimento.id) or ESTADO_BOOT

        logger.info(
            "processar_mensagem | estado=%s | telefone=%s | tipo=%s | protocolo=%s",
            estado_atual,
            telefone,
            msg_type,
            atendimento.protocolo,
        )

        # TRATAMENTO DE ERROS ROBUSTO (Fail-Safe)
        try:
            await self._despachar_estado(atendimento, estado_atual, msg_type, content)
        except ValueError as e:
            # Erro de validação de dados (ex: nome inválido, formato errado)
            logger.warning("Erro de validação no fluxo | protocolo=%s | erro=%s", atendimento.protocolo, str(e))
            await self._evolution.enviar_texto(instance_nome, telefone, f"⚠️ {str(e)}")
        except KeyError as e:
            # Erro de configuração ou chave de contexto faltando
            logger.error("Chave de configuração ou contexto faltando | protocolo=%s | chave=%s", atendimento.protocolo, str(e))
            await self._evolution.enviar_texto(
                instance_nome,
                telefone,
                "⚠️ Ocorreu um erro de configuração no sistema. Por favor, tente novamente mais tarde.",
            )
        except Exception as e:
            # Catch-all: Garante que o bot NUNCA trave silenciosamente
            logger.exception("Erro crítico inesperado no processamento | protocolo=%s", atendimento.protocolo)
            await self._evolution.enviar_texto(
                instance_nome,
                telefone,
                "Desculpe, ocorreu um erro interno inesperado. Tente novamente ou digite *MENU* para reiniciar.",
            )

    # ═══════════════════════════════════════════════════════════════════════════════
    # ROTEADOR DE ESTADOS
    # ═══════════════════════════════════════════════════════════════════════════════

    async def _despachar_estado(
        self,
        atendimento: Atendimento,
        estado: str,
        msg_type: str,
        content: str,
    ) -> None:
        if estado in (ESTADO_BOOT, ESTADO_FINALIZADO):
            await self._handler_boot(atendimento)
            return

        if estado == ESTADO_AGUARDAR_LGPD:
            await self._handler_lgpd(atendimento, msg_type, content)
            return

        if estado == ESTADO_AGUARDAR_NOME:
            await self._handler_nome(atendimento, content)
            return

        if estado == ESTADO_AGUARDAR_HUB:
            await self._handler_hub(atendimento, msg_type, content)
            return

        if estado == ESTADO_EM_ATENDIMENTO:
            logger.info("Atendimento em modo humano. Bot ignorando mensagem.")
            return

        # Despacho para Handlers de Departamento (White-Label)
        prefixo = estado.split(":")[0]
        handler = self._handlers.get(prefixo)

        if handler:
            msg_obj = Mensagem(tipo=msg_type, conteudo=content)
            await handler.processar(atendimento, estado, msg_obj)
        else:
            logger.warning("Handler não encontrado para o prefixo: %s. Retornando ao Hub.", prefixo)
            await self._handler_hub(atendimento, msg_type, "HUB_VOLTAR")

    # ═══════════════════════════════════════════════════════════════════════════════
    # HANDLERS DO FLUXO INICIAL
    # ═══════════════════════════════════════════════════════════════════════════════

    async def _handler_boot(self, atendimento: Atendimento) -> None:
        instancia = self._obter_instancia(atendimento)
        telefone = atendimento.telefone
        nome_empresa = "Nossa Empresa" # TODO: Buscar dinamicamente da config do tenant

        await self._evolution.enviar_texto(
            instancia,
            telefone,
            f"👋 *Olá! Seja bem-vindo(a) ao*\n*{nome_empresa}*\nSou seu assistente virtual. 🤖",
        )

        await self._evolution.enviar_lista(
            instancia,
            telefone,
            "🔒 Política de Privacidade (LGPD)",
            "Para continuar, você declara que leu e concorda com nossa política de tratamento de dados?",
            "Responder",
            [
                {"title": "✅ Sim, concordo", "description": "Aceitar e continuar", "rowId": "LGPD_ACEITO"},
                {"title": "❌ Não concordo", "description": "Encerrar atendimento", "rowId": "LGPD_RECUSADO"},
            ],
        )
        self._avancar_estado(atendimento, ESTADO_AGUARDAR_LGPD)

    async def _handler_lgpd(self, atendimento: Atendimento, msg_type: str, content: str) -> None:
        instancia = self._obter_instancia(atendimento)
        telefone = atendimento.telefone

        recusou = (
            (msg_type == "list_response" and content.upper() == "LGPD_RECUSADO")
            or content.strip().lower() in ("não", "nao", "n", "cancelar")
        )

        if recusou:
            await self._evolution.enviar_texto(
                instancia,
                telefone,
                "Entendemos. Seus dados não serão processados. Se mudar de ideia, nos chame novamente. 💙",
            )
            atendimento.status = "finalizado"
            atendimento.ativo = False
            self._db.commit()
            self._avancar_estado(atendimento, ESTADO_FINALIZADO)
            return

        await self._evolution.enviar_texto(
            instancia, telefone, "Obrigado! 🙏\n\nPara melhor atendê-lo(a), por favor, informe seu *nome completo*:"
        )
        self._avancar_estado(atendimento, ESTADO_AGUARDAR_NOME)

    async def _handler_nome(self, atendimento: Atendimento, content: str) -> None:
        instancia = self._obter_instancia(atendimento)
        telefone = atendimento.telefone

        # Validação robusta (A solução que o CodeGeex sugeriu já está aqui!)
        valido, erro = self._validar_nome(content)
        if not valido:
            await self._evolution.enviar_texto(instancia, telefone, f"⚠️ {erro}\n\nPor favor, digite seu nome completo:")
            return # Sai do método, mantendo o estado em AGUARDAR_NOME

        nome_formatado = content.strip().title()
        atendimento.nome_contato = nome_formatado
        self._db.commit()
        
        self._guardar_contexto(atendimento.id, "nome", nome_formatado)

        await self._evolution.enviar_texto(
            instancia, telefone, f"Obrigado, *{nome_formatado}*! É um prazer atendê-lo(a). 😊"
        )

        await self._enviar_hub(atendimento)
        self._avancar_estado(atendimento, ESTADO_AGUARDAR_HUB)

    async def _handler_hub(self, atendimento: Atendimento, msg_type: str, content: str) -> None:
        instancia = self._obter_instancia(atendimento)
        telefone = atendimento.telefone

        if msg_type != "list_response" or not content.startswith("HUB_"):
            nome = self._obter_contexto(atendimento.id, "nome") or "cliente"
            await self._evolution.enviar_texto(instancia, telefone, f"Por favor, *{nome}*, selecione uma das opções abaixo:")
            await self._enviar_hub(atendimento)
            return

        prefixo_departamento = content.replace("HUB_", "")
        novo_estado = f"{prefixo_departamento}:MENU"

        logger.info("Transição de Hub para Departamento: %s", novo_estado)
        
        self._avancar_estado(atendimento, novo_estado)
        await self._despachar_estado(atendimento, novo_estado, msg_type, content)

    async def _enviar_hub(self, atendimento: Atendimento) -> None:
        instancia = self._obter_instancia(atendimento)
        telefone = atendimento.telefone

        hub_rows = [
            {"title": "1️⃣ Atendimento Geral", "description": "Dúvidas e informações", "rowId": "HUB_AT"},
            {"title": "2️⃣ Agendamentos", "description": "Marcar ou cancelar", "rowId": "HUB_AG"},
            {"title": "3️⃣ Financeiro", "description": "2ª via de boletos", "rowId": "HUB_FIN"},
            {"title": "4️⃣ Ouvidoria", "description": "Elogios e reclamações", "rowId": "HUB_OV"},
        ]

        await self._evolution.enviar_lista(
            instancia,
            telefone,
            "Central de Atendimento",
            "Selecione o departamento desejado:",
            "Ver departamentos",
            hub_rows,
        )

    # ═══════════════════════════════════════════════════════════════════════════════
    # UTILITÁRIOS E VALIDAÇÕES
    # ═══════════════════════════════════════════════════════════════════════════════

    def _validar_nome(self, nome: str) -> Tuple[bool, Optional[str]]:
        """
        Valida se o nome fornecido é aceitável.
        RETORNO: Tupla (Sucesso: bool, Mensagem_de_Erro: str ou None)
        
        NOTA DELPHI: Isso equivale a usar parâmetros 'out' ou 'var' no Delphi 
        para retornar múltiplos valores de uma função.
        """
        nome_limpo = nome.strip()
        if len(nome_limpo) < 3:
            return False, "O nome parece muito curto. Por favor, digite seu nome completo."
        if len(nome_limpo) > 100:
            return False, "O nome parece muito longo. Verifique se não houve erro de digitação."
        
        if not nome_limpo.replace(" ", "").replace("-", "").isalpha():
            return False, "O nome deve conter apenas letras. Evite números ou símbolos."
            
        return True, None

    def _buscar_ou_criar_atendimento(
        self, telefone: str, instancia: str, push_name: Optional[str]
    ) -> Tuple[Atendimento, bool]:
        at = (
            self._db.query(Atendimento)
            .filter(
                Atendimento.telefone == telefone,
                Atendimento.ativo == True,
                Atendimento.status != "finalizado",
            )
            .order_by(Atendimento.criado_em.desc())
            .first()
        )

        if at:
            if push_name and not at.nome_contato:
                at.nome_contato = push_name
                self._db.commit()
            return at, False

        at = Atendimento(
            protocolo=self._gerar_protocolo(),
            telefone=telefone,
            nome_contato=push_name or "Desconhecido",
            tipo=1,
            ativo=True,
            status="aberto",
        )
        self._db.add(at)
        self._db.commit()
        self._db.refresh(at)

        self._guardar_contexto(at.id, "instancia", instancia)
        self._guardar_contexto(at.id, "step", ESTADO_BOOT)

        return at, True

    def _obter_estado(self, atendimento_id: int) -> Optional[str]:
        return self._obter_contexto(atendimento_id, "step")

    def _obter_contexto(self, atendimento_id: int, chave: str) -> Optional[str]:
        row = (
            self._db.query(AtendimentoContext)
            .filter(
                AtendimentoContext.atendimento_id == atendimento_id,
                AtendimentoContext.context_key == chave,
            )
            .first()
        )
        return row.value if row else None

    def _guardar_contexto(self, atendimento_id: int, chave: str, valor: str) -> None:
        row = (
            self._db.query(AtendimentoContext)
            .filter(
                AtendimentoContext.atendimento_id == atendimento_id,
                AtendimentoContext.context_key == chave,
            )
            .first()
        )
        
        if row:
            row.value = valor
        else:
            self._db.add(
                AtendimentoContext(
                    atendimento_id=atendimento_id,
                    context_key=chave,
                    value=valor,
                )
            )
        self._db.commit()

    def _avancar_estado(self, atendimento: Atendimento, novo_estado: str) -> None:
        self._guardar_contexto(atendimento.id, "step", novo_estado)
        logger.debug("Transição de estado | protocolo=%s | novo_estado=%s", atendimento.protocolo, novo_estado)

    @staticmethod
    def _extrair_telefone(remote_jid: str) -> str:
        return remote_jid.split("@")[0]

    @staticmethod
    def _obter_instancia(atendimento: Atendimento) -> str:
        return getattr(atendimento, "instancia", "default")

    @staticmethod
    def _gerar_protocolo(prefixo: str = "WP") -> str:
        data_str = datetime.utcnow().strftime('%Y%m%d')
        uuid_curto = uuid.uuid4().hex[:6].upper()
        return f"{prefixo}-{data_str}-{uuid_curto}"