"""
================================================================================
MÁQUINA DE ESTADOS DA CONVERSA (ENCAPSULADA EM CLASSE OOP)
================================================================================
Arquivo: bot_handlers/bot_machine.py
Propósito: Orquestrador principal da máquina de estados

ANTES (Anti-pattern):
  - bot_service.py tinha 1692 linhas procedurais
  - Contexto global via ContextVar (anti-pattern)
  - Sem encapsulamento de estado

DEPOIS (OOP Puro):
  - BotMáquinaEstados como classe que encapsula tudo
  - Estado do bot é atributo privado (_handlers, _db)
  - Cada handler é uma instância injetada (Dependency Injection)
  - Totalmente testável e extensível
================================================================================
"""

import logging
from datetime import datetime
import uuid
from typing import Optional, Dict

from sqlalchemy.orm import Session

from app.models import Atendimento, AtendimentoContext, Canal, Menu, Mensagem
from .base_handler import DepartamentoHandler
from .evolution_client import EvolutionApiClient

logger = logging.getLogger(__name__)

# Constantes de Estado (Enum melhorado)
# Em Delphi seria: type TEstadoBot = (BOOT, AGUARDAR_LGPD, ...)
ESTADO_BOOT = "BOOT"
ESTADO_AGUARDAR_LGPD = "AGUARDAR_LGPD"
ESTADO_AGUARDAR_NOME = "AGUARDAR_NOME"
ESTADO_AGUARDAR_HUB = "AGUARDAR_HUB"
ESTADO_EM_ATENDIMENTO = "EM_ATENDIMENTO"
ESTADO_FINALIZADO = "FINALIZADO"


class BotMáquinaEstados:
    """
    CLASSE PRINCIPAL: Orquestra toda a máquina de estados

    Responsabilidades (SRP):
      1. Gerenciar transições de estado
      2. Despachar mensagens para handlers apropriados
      3. Persistir contexto do atendimento
      4. Integrar com Evolution API

    Equivalente em Delphi:
        type
          TBotMaquinaEstados = class(TObject)
          private
            FDb: TDataset;
            FEvolution: TEvolutionApiClient;
            FHandlers: TDictionary<string, IDepartamentoHandler>;
            procedure TransicionarEstado(...);
          public
            procedure ProcessarMensagem(...);
          end;
    """

    # ──────────────────────────────────────────────────────────────────────────
    # ENCAPSULAMENTO: Atributos privados
    # ──────────────────────────────────────────────────────────────────────────

    def __init__(
        self,
        db: Session,
        evolution_client: EvolutionApiClient,
        handlers: Optional[Dict[str, DepartamentoHandler]] = None,
    ):
        """
        DEPENDENCY INJECTION: Recebe dependências no construtor

        Args:
            db: Sessão do banco (injetada)
            evolution_client: Cliente Evolution API (injetado)
            handlers: Dicionário de handlers por prefixo (ex: {"AT": AtendimentoHandler(...)})
        """
        self._db = db
        self._evolution = evolution_client
        self._handlers = handlers or {}

        logger.info(
            "BotMáquinaEstados inicializado | handlers=%s",
            list(self._handlers.keys()),
        )

    # ──────────────────────────────────────────────────────────────────────────
    # MÉTODO PRINCIPAL (Ponto de entrada)
    # ──────────────────────────────────────────────────────────────────────────

    async def processar_mensagem_recebida(
        self,
        instance_nome: str,
        remote_jid: str,
        push_name: Optional[str],
        msg_type: str,
        content: str,
    ) -> None:
        """
        ABSTRAÇÃO PÚBLICA: Processa mensagem recebida do webhook

        Args:
            instance_nome: Nome da instância WhatsApp
            remote_jid: JID do remetente (ex: "67999999999@s.whatsapp.net")
            push_name: Nome do contato (opcional)
            msg_type: Tipo de mensagem ("text", "list_response", etc)
            content: Conteúdo da mensagem

        Notas:
          - Ignora mensagens de grupo (@g.us)
          - Busca ou cria atendimento
          - Recupera estado atual
          - Despacha para handler apropriado
        """
        # Ignora grupos
        if remote_jid.endswith("@g.us"):
            return

        # Extrai telefone e busca/cria atendimento
        telefone = self._extrair_telefone(remote_jid)
        atendimento, eh_novo = self._buscar_ou_criar_atendimento(
            telefone, instance_nome, push_name
        )

        # Recupera estado atual
        estado_atual = self._obter_estado(atendimento.id) or ESTADO_BOOT

        logger.info(
            "bot_machine | processar | estado=%s | telefone=%s | tipo=%s | protocolo=%s",
            estado_atual,
            telefone,
            msg_type,
            atendimento.protocolo,
        )

        try:
            # DESPACHA para handler apropriado (pattern matching em estado)
            await self._despachar_estado(
                atendimento, estado_atual, msg_type, content
            )

        except Exception as e:
            logger.exception("bot_machine | erro | protocolo=%s", atendimento.protocolo)
            await self._evolution.enviar_texto(
                instance_nome,
                telefone,
                "Desculpe, ocorreu um erro. Tente novamente.",
            )

    # ──────────────────────────────────────────────────────────────────────────
    # DESPACHO DE ESTADO (Pattern Matching)
    # ──────────────────────────────────────────────────────────────────────────

    async def _despachar_estado(
        self,
        atendimento: Atendimento,
        estado: str,
        msg_type: str,
        content: str,
    ) -> None:
        """
        ABSTRAÇÃO INTERNA: Despacha para handler baseado no estado

        Args:
            atendimento: Objeto atendimento
            estado: Estado atual (ex: "AT:MENU")
            msg_type: Tipo de mensagem
            content: Conteúdo
        """
        # Estados do hub (pré-departamento)
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
            # Bot silencioso, humano atendendo
            return

        # Despacha para handlers de departamento
        prefixo = estado.split(":")[0]  # Extrai "AT", "AG", etc
        handler = self._handlers.get(prefixo)

        if handler:
            await handler.processar(atendimento, estado, None)  # TODO: passar Mensagem
        else:
            logger.warning("bot_machine | handler não encontrado | prefixo=%s", prefixo)

    # ──────────────────────────────────────────────────────────────────────────
    # HANDLERS DO HUB (Boot, LGPD, Nome, Menu)
    # ──────────────────────────────────────────────────────────────────────────

    async def _handler_boot(self, atendimento: Atendimento) -> None:
        """Boot: Mensagem inicial + LGPD"""
        telefone = atendimento.telefone
        instancia = self._obter_instancia(atendimento)

        await self._evolution.enviar_texto(
            instancia,
            telefone,
            "👋 *Olá! Seja bem-vindo ao*\n"
            "*Hospital Presbiteriano Mackenzie*\n"
            "Sou seu assistente virtual. 🤖",
        )

        await self._evolution.enviar_lista(
            instancia,
            telefone,
            "🔒 Política de Privacidade (LGPD)",
            "Você declara que leu e concorda?",
            "Responder",
            [
                {"title": "✅ Sim, concordo", "description": "", "rowId": "LGPD_ACEITO"},
                {"title": "❌ Não concordo", "description": "", "rowId": "LGPD_RECUSADO"},
            ],
        )

        self._avancar_estado(atendimento, ESTADO_AGUARDAR_LGPD)

    async def _handler_lgpd(
        self, atendimento: Atendimento, msg_type: str, content: str
    ) -> None:
        """LGPD: Validar aceite"""
        telefone = atendimento.telefone
        instancia = self._obter_instancia(atendimento)

        recusou = (
            (msg_type == "list_response" and content.upper() == "LGPD_RECUSADO")
            or content.strip().lower() in ("não", "nao", "n")
        )

        if recusou:
            await self._evolution.enviar_texto(
                instancia,
                telefone,
                "Entendemos. Se mudar de ideia, nos chame novamente. 💙",
            )
            atendimento.status = "finalizado"
            atendimento.ativo = False
            self._db.commit()
            self._avancar_estado(atendimento, ESTADO_FINALIZADO)
            return

        await self._evolution.enviar_texto(
            instancia, telefone, "Obrigado! 🙏\n\nInforme seu nome completo:"
        )
        self._avancar_estado(atendimento, ESTADO_AGUARDAR_NOME)

    async def _handler_nome(self, atendimento: Atendimento, content: str) -> None:
        """Nome: Coleta nome do usuário"""
        nome = content.strip().title()
        if len(nome) < 2:
            return

        atendimento.nome_contato = nome
        self._db.commit()
        self._guardar_contexto(atendimento.id, "nome", nome)

        telefone = atendimento.telefone
        instancia = self._obter_instancia(atendimento)

        await self._evolution.enviar_texto(
            instancia, telefone, f"Obrigado, *{nome}*! Bem-vindo(a). 😊"
        )

        # Envia hub e avança estado
        await self._enviar_hub(atendimento)
        self._avancar_estado(atendimento, ESTADO_AGUARDAR_HUB)

    async def _handler_hub(
        self, atendimento: Atendimento, msg_type: str, content: str
    ) -> None:
        """Hub: Menu principal de departamentos"""
        if msg_type != "list_response":
            nome = self._obter_contexto(atendimento.id, "nome") or "cliente"
            await self._evolution.enviar_texto(
                self._obter_instancia(atendimento),
                atendimento.telefone,
                f"Olá, *{nome}*!",
            )
            await self._enviar_hub(atendimento)
            return

        # Processa seleção de departamento
        # TODO: Implementar mapeamento de departamentos

    async def _enviar_hub(self, atendimento: Atendimento) -> None:
        """Envia menu hub personalizado"""
        hub_rows = [
            {"title": "1️⃣ Atendimento", "description": "Info e guias", "rowId": "HUB_AT"},
            {"title": "2️⃣ Agendamentos", "description": "Marcar consulta", "rowId": "HUB_AG"},
            {"title": "3️⃣ Exames", "description": "Agendar exames", "rowId": "HUB_EX"},
            {"title": "4️⃣ Portaria", "description": "Visitas", "rowId": "HUB_PO"},
            {"title": "5️⃣ Ouvidoria", "description": "Sugestões", "rowId": "HUB_OV"},
        ]

        await self._evolution.enviar_lista(
            self._obter_instancia(atendimento),
            atendimento.telefone,
            "Central de Atendimento",
            "Selecione o departamento:",
            "Ver departamentos",
            hub_rows,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # UTILITÁRIOS PRIVADOS (Implementação interna)
    # ──────────────────────────────────────────────────────────────────────────

    def _buscar_ou_criar_atendimento(
        self, telefone: str, instancia: str, push_name: Optional[str]
    ) -> tuple[Atendimento, bool]:
        """
        ABSTRAÇÃO: Busca atendimento ativo ou cria novo

        Returns:
            (atendimento, eh_novo)
        """
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

        # Cria novo atendimento
        at = Atendimento(
            protocolo=self._gerar_protocolo(),
            telefone=telefone,
            nome_contato=push_name or "",
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
        """Recupera estado atual do atendimento"""
        return self._obter_contexto(atendimento_id, "step")

    def _obter_contexto(self, atendimento_id: int, chave: str) -> Optional[str]:
        """Recupera valor do contexto"""
        row = (
            self._db.query(AtendimentoContext)
            .filter(
                AtendimentoContext.atendimento_id == atendimento_id,
                AtendimentoContext.context_key == chave,
            )
            .first()
        )
        return row.value if row else None

    def _guardar_contexto(
        self, atendimento_id: int, chave: str, valor: str
    ) -> None:
        """Persiste valor no contexto"""
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
        """Transiciona para novo estado"""
        self._guardar_contexto(atendimento.id, "step", novo_estado)

    @staticmethod
    def _extrair_telefone(remote_jid: str) -> str:
        """Extrai número do JID (ex: "67999@s.whatsapp.net" -> "67999")"""
        return remote_jid.split("@")[0]

    @staticmethod
    def _obter_instancia(atendimento: Atendimento) -> str:
        """Obtém instância WhatsApp (nome ou default)"""
        return getattr(atendimento, "instancia", "default")

    @staticmethod
    def _gerar_protocolo(prefixo: str = "WP") -> str:
        """Gera ID único para rastreamento"""
        return f"{prefixo}-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
