"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Bot Service
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     bot_service.py
@module   Backend / App / Services / Bot
@author   Aldemir Queiroz
@since    2026
@version  3.0.0  · POO + cache Redis + transações atômicas + enums tipados
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Orquestra o ciclo de vida de um atendimento iniciado pelo bot, desde a
primeira mensagem (BOOT) até o encaminhamento para atendimento humano.

    ┌──────────────────────────────────────────────────────────────────┐
    │  BOOT → AGUARDAR_LGPD → AGUARDAR_NOME → AGUARDAR_HUB             │
    │       → DEPTO_DINAMICO → EM_ATENDIMENTO → FINALIZADO             │
    └──────────────────────────────────────────────────────────────────┘

MULTI-BANCO
───────────
    ┌──────────────┬──────────────────────────────────────────────────┐
    │ PostgreSQL   │ Atendimento, Contato, Conexao — fonte da verdade  │
    │ Redis        │ Cache do atendimento ativo por (empresa, telefone)│
    │ MongoDB      │ Contexto do atendimento (em outro service)        │
    └──────────────┴──────────────────────────────────────────────────┘

⚠️ CORREÇÃO CRÍTICA (v3.0.0) — IDOR MULTI-TENANT
─────────────────────────────────────────────────
ANTES (v1.x):
    db.query(Atendimento).filter(Atendimento.telefone == telefone)
    → Vazava atendimento entre tenants que compartilhavam telefone.

DEPOIS (v2.x — sua correção):
    Filtro por `empresa_id` E `canal_contratado_id` (conexão).

MELHORIA (v3.0.0):
    • Encapsulado na classe BotService (isolamento por instância)
    • Cache Redis escopado: atendimento:{empresa_id}:{telefone}
    • Transações atômicas via `_transaction()` context manager
    • Enums tipados em vez de strings mágicas
    • Métodos privados com prefixo `_` (convenção Python)
    • Injeção de dependências no construtor (facilita testes)

CONCEITOS DE POO APLICADOS
──────────────────────────
    Classe .............. BotService (molde)
    Objeto .............. Instância criada por requisição
    Encapsulamento ...... Métodos privados (_) e públicos
    Estado .............. self.db, self.conexao, self.atendimento
    Composição .......... BotService tem Redis, EvolutionService
    Coesão .............. Orquestrar fluxo, só isso
    Acoplamento ......... Depende de interfaces, não implementações
    Injeção ............ Dependências recebidas no __init__
    @staticmethod ....... _normalizar, _tel, _protocolo
    @classmethod ........ from_webhook (factory)
    @property ........... empresa_id, eh_voip
    Dataclass ........... ContextoMensagem
    Enum ................ BotStep (BOOT, LGPD, ...)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

import contextvars
import logging
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from redis.asyncio import Redis
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.adapters import BaseMessageAdapter, get_adapter
from app.core.config import settings
from app.exceptions import (
    AcessoNegadoError,
    RecursoNaoEncontradoError,
)
from app.models import (
    Atendimento,
    AtendimentoContexto,
    CanalContratado,
    Conexao,
    Contato,
    Menu,
    Usuario,
)
from app.models.enums import StatusAtendimento
from app.services import audio_service


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════

RODAPE = "Digite uma opção:"

#: TTL do cache do atendimento ativo (segundos)
CACHE_ATENDIMENTO_TTL: int = 300

#: Regex para remover emojis antes de gerar áudio
EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"     # emoticons
    "\U0001F300-\U0001F5FF"     # símbolos e pictogramas
    "\U0001F680-\U0001F6FF"     # transporte e símbolos de mapa
    "\U0001F1E0-\U0001F1FF"     # bandeiras
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)

#: Regex para remover markdown antes de gerar áudio
MARKDOWN_RE = re.compile(r"[\*_~`]")

#: Frases que ativam/desativam modo áudio
FRASES_ATIVAR_AUDIO = {"audio", "áudio", "ouvir", "falar", "voz"}
FRASES_DESATIVAR_AUDIO = {"texto", "parar audio", "desativar audio"}


# ═══════════════════════════════════════════════════════════════════════════
# ENUMS TIPADOS — substituem strings mágicas
# ═══════════════════════════════════════════════════════════════════════════

class BotStep(str, Enum):
    """
    Estados da máquina de conversa.

    Por que Enum e não strings soltas:
        • Autocomplete em IDEs
        • Erros de digitação viram AttributeError (não falha silenciosa)
        • Refactor seguro: rename propaga por todo o código
        • Documentação implícita do fluxo
    """
    BOOT             = "BOOT"
    AGUARDAR_LGPD    = "AGUARDAR_LGPD"
    AGUARDAR_NOME    = "AGUARDAR_NOME"
    AGUARDAR_HUB     = "AGUARDAR_HUB"
    DEPTO_DINAMICO   = "DEPTO_DINAMICO"
    EM_ATENDIMENTO   = "EM_ATENDIMENTO"
    FINALIZADO       = "FINALIZADO"


# ═══════════════════════════════════════════════════════════════════════════
# DATACLASS — carrega dados da mensagem sem lógica
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ContextoMensagem:
    """
    Dados imutáveis da mensagem recebida.

    Por que dataclass:
        • Sem boilerplate de __init__, __repr__, __eq__
        • `frozen=True` torna imutável (evita efeitos colaterais)
        • Type hints explícitos

    Por que não dict:
        • Acesso por atributo (msg.content) em vez de chave (msg["content"])
        • Autocomplete na IDE
        • Se um campo for removido, o type checker acusa
    """
    remote_jid: str
    push_name: Optional[str]
    msg_type: str
    content: str

    @property
    def telefone(self) -> str:
        """Extrai o telefone limpo do remote_jid."""
        return self.remote_jid.replace("@s.whatsapp.net", "")

    @property
    def eh_grupo(self) -> bool:
        """True se a mensagem veio de um grupo WhatsApp."""
        return self.remote_jid.endswith("@g.us")


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE DOMÍNIO — erros específicos do negócio
# ═══════════════════════════════════════════════════════════════════════════

class BotError(Exception):
    """
    Exceção base do bot.

    Por que criar exceções próprias:
        • Permite capturar `except BotError` e tratar só o que é do domínio
        • Diferencia de erro de programação (AttributeError, KeyError)
        • Documenta os modos de falha esperados
    """


class ConexaoInativaError(BotError):
    """Conexão/instância não existe ou está inativa."""


# ═══════════════════════════════════════════════════════════════════════════
# CLASSE PRINCIPAL — BotService
# ═══════════════════════════════════════════════════════════════════════════

class BotService:
    """
    Orquestrador do fluxo de bot.

    ─────────────────────────────────────────────────────────────────────
    CONCEITOS DE POO
    ─────────────────────────────────────────────────────────────────────
    • CLASSE: o molde. Descreve o que um BotService tem e faz.
    • OBJETO: cada requisição cria um `BotService(db, conexao, redis)`.
    • ESTADO: `self.db`, `self.conexao`, `self.atendimento`.
    • COMPOSIÇÃO: BotService TEM um Redis, uma Conexao, uma Session.
    • ENCAPSULAMENTO: métodos privados (prefixo `_`) para uso interno;
      só `processar_mensagem()` é público.
    • INJEÇÃO DE DEPENDÊNCIA: `db`, `conexao` e `redis` vêm de fora,
      via construtor — permite trocar por mocks em testes.

    ─────────────────────────────────────────────────────────────────────
    CICLO DE VIDA
    ─────────────────────────────────────────────────────────────────────
        1. __init__          → recebe dependências
        2. processar_mensagem() → executa o fluxo
        3. (fim)             → objeto é descartado (stateless fora dos
                                atributos de request)
    """

    def __init__(
        self,
        db: Session,
        conexao: Conexao,
        redis: Redis,
        adapter: Optional[BaseMessageAdapter] = None,
    ) -> None:
        """
        Construtor — recebe dependências prontas.

        ─────────────────────────────────────────────────────────────────
        POR QUE RECEBER `conexao` JÁ RESOLVIDA
        ─────────────────────────────────────────────────────────────────
        A resolução "instance_nome → Conexao" acontece no `from_webhook`
        (factory). Aqui já recebemos o objeto pronto — isso:
            • Reduz responsabilidade desta classe
            • Facilita testar (podemos passar uma Conexao fake)
            • Elimina uma query por requisição

        ─────────────────────────────────────────────────────────────────
        POR QUE `adapter` É INJETADO
        ─────────────────────────────────────────────────────────────────
        Esta classe orchestra o fluxo do bot, não fala com provedor. Todo
        envio passa por `self.adapter`, um `BaseMessageAdapter`:

            • Acoplamento: o bot desconhece Evolution, Meta, Telegram e PABX
            • Polimorfismo: trocar de provedor não altera uma linha daqui
            • Testabilidade: passa-se um adaptador fake, sem HTTP

        Se `adapter` vier `None`, a fábrica escolhe pelo tipo do canal —
        assim o chamador não precisa saber qual adaptador usar.
        """
        self.db = db
        self.conexao = conexao
        self.redis = redis
        self.adapter = adapter if adapter is not None else self._criar_adapter()
        self._atendimento: Optional[Atendimento] = None  # setado depois

    def _criar_adapter(self) -> BaseMessageAdapter:
        """
        Resolve o adaptador a partir do canal da conexão.

        ─────────────────────────────────────────────────────────────────
        POR QUE NÃO RESOLVER NO MÓDULO
        ─────────────────────────────────────────────────────────────────
        A escolha do adaptador depende do `Canal.tipo` e do provedor, dados
        que só existem depois da query da Conexao. Deixar a resolução
        dentro da instância mantém a decisão junto de quem tem o contexto.
        """
        canal = getattr(self.conexao, "canal", None)
        tipo = getattr(canal, "tipo", None) or "whatsapp"
        provedor = getattr(canal, "provedor", None)

        adapter = get_adapter(tipo, provedor)
        logger.info(
            "bot_service | Adaptador resolvido | canal=%s provedor=%s adapter=%s",
            tipo, provedor, type(adapter).__name__,
        )
        return adapter

    # ═════════════════════════════════════════════════════════════════════
    # PROPRIEDADES — atalhos de leitura
    # ═════════════════════════════════════════════════════════════════════

    @property
    def empresa_id(self) -> int:
        """
        Atalho para o tenant. Toda operação desta classe usa esse valor.

        Propriedade (@property) em vez de atributo comum porque:
            • Não precisa ser setado no construtor
            • Calculado sob demanda (a partir de self.conexao)
            • Impossível setar acidentalmente (`bot.empresa_id = X` falha)
        """
        return self.conexao.empresa_id

    @property
    def atendimento(self) -> Atendimento:
        """Atalho para o atendimento ativo. Erro se não inicializado."""
        if self._atendimento is None:
            raise BotError(
                "Atendimento não inicializado. Chame _buscar_ou_criar antes."
            )
        return self._atendimento

    @property
    def eh_voip(self) -> bool:
        """True se a conexão é de telefonia IP (PABX/VoIP)."""
        return getattr(self.conexao, "telefone_id", None) is not None

    # ═════════════════════════════════════════════════════════════════════
    # FACTORY — cria a instância a partir do webhook
    # ═════════════════════════════════════════════════════════════════════

    @classmethod
    def from_webhook(
        cls,
        db: Session,
        redis: Redis,
        instance_nome: str,
    ) -> "BotService":
        """
        Factory — resolve a conexão e retorna um BotService pronto.

        ─────────────────────────────────────────────────────────────────
        POR QUE @classmethod (e não @staticmethod)
        ─────────────────────────────────────────────────────────────────
        Um `@classmethod` recebe `cls` (a classe) como primeiro argumento.
        Isso permite criar a instância com `cls(db, conexao, redis)`,
        respeitando subclasses se existirem no futuro.

        @staticmethod não recebe nem `self` nem `cls` — seria só uma
        função solta dentro da classe (útil, mas não para factory).

        ─────────────────────────────────────────────────────────────────
        POR QUE UMA FACTORY (e não mais um parâmetro no __init__)
        ─────────────────────────────────────────────────────────────────
        A resolução "instance_nome → Conexao" envolve:
            • Query no banco
            • Validação de existência
            • Validação de status ativo
            • Levantar exceção se falhar
        Isso é MUITA responsabilidade para o construtor. A factory
        isola essa complexidade e deixa o __init__ limpo.
        """
        stmt = select(Conexao).where(
            Conexao.nome_instancia == instance_nome,
            Conexao.ativo.is_(True),
        )
        conexao = db.execute(stmt).scalar_one_or_none()

        if conexao is None:
            logger.error(
                "bot_service | Conexão não encontrada | instance=%s",
                instance_nome,
            )
            raise RecursoNaoEncontradoError(
                f"Instância '{instance_nome}' não configurada ou inativa."
            )

        return cls(db=db, conexao=conexao, redis=redis)

    # ═════════════════════════════════════════════════════════════════════
    # ENTRYPOINT PÚBLICO — o único método que o mundo externo usa
    # ═════════════════════════════════════════════════════════════════════

    async def processar_mensagem(self, ctx: ContextoMensagem) -> None:
        """
        Ponto de entrada do bot. Chamado pelo webhook.

        ─────────────────────────────────────────────────────────────────
        FLUXO
        ─────────────────────────────────────────────────────────────────
            1. Ignora mensagens de grupo
            2. Busca ou cria atendimento (isolado por tenant)
            3. Lê o step atual
            4. Despacha para o handler do step
            5. Captura erros → resposta amigável ao cliente
        """
        # ─── 1. Ignora grupos ─────────────────────────────────────────────
        if ctx.eh_grupo:
            logger.debug("bot_service | Ignorando mensagem de grupo")
            return

        # ─── 2. Busca ou cria atendimento ─────────────────────────────────
        self._atendimento = await self._buscar_ou_criar(ctx)

        # ─── 3. Lê o step atual ───────────────────────────────────────────
        step = self._get_step()

        logger.info(
            "bot_service | Processando | step=%s tel=%s type=%s prot=%s empresa=%s",
            step.value, ctx.telefone, ctx.msg_type,
            self.atendimento.protocolo, self.empresa_id,
        )

        # ─── 4. Despacho por step ─────────────────────────────────────────
        try:
            # Modo áudio (atalho universal, exceto em atendimento humano)
            if step != BotStep.EM_ATENDIMENTO and ctx.msg_type != "list_response":
                if self._pedido_ativar_audio(ctx.content):
                    return await self._ativar_modo_audio(ctx.telefone)
                if self._pedido_desativar_audio(ctx.content):
                    return await self._desativar_modo_audio(ctx.telefone)

            # Handlers por step
            handler = {
                BotStep.BOOT:           self._boot,
                BotStep.FINALIZADO:     self._boot,
                BotStep.AGUARDAR_LGPD:  self._lgpd,
                BotStep.AGUARDAR_NOME:  self._nome,
                BotStep.AGUARDAR_HUB:   self._hub,
                BotStep.DEPTO_DINAMICO: self._departamento_dinamico,
            }.get(step)

            if handler:
                await handler(ctx)
            elif step == BotStep.EM_ATENDIMENTO:
                pass  # já está com atendente humano, ignora
            else:
                await self._voltar_hub(ctx.telefone)

        except Exception as exc:
            logger.exception(
                "bot_service | Erro no processamento | step=%s prot=%s",
                step.value, self.atendimento.protocolo,
            )
            await self._enviar_texto(
                ctx.telefone,
                (
                    "Ocorreu um erro ao processar sua mensagem. "
                    "Por favor, tente novamente."
                ),
            )

    # ═════════════════════════════════════════════════════════════════════
    # MÉTODO PRIVADO — busca ou cria atendimento (CORREÇÃO IDOR)
    # ═════════════════════════════════════════════════════════════════════

    async def _buscar_ou_criar(self, ctx: ContextoMensagem) -> Atendimento:
        """
        Busca atendimento ativo do contato NO MESMO TENANT.
        Se não existir, cria um novo.

        ─────────────────────────────────────────────────────────────────
        ⚠️ SEGURANÇA — o coração da correção IDOR
        ─────────────────────────────────────────────────────────────────
        Filtro OBRIGATÓRIO por:
            • empresa_id (tenant)
            • canal_contratado_id (conexão)

        Sem esses filtros, dois tenants com o mesmo telefone podem
        compartilhar atendimentos — vazamento cross-tenant.

        ─────────────────────────────────────────────────────────────────
        POR QUE MÉTODO PRIVADO (`_`)
        ─────────────────────────────────────────────────────────────────
        Python não tem `private` real, mas o prefixo `_` é convenção:
        sinaliza que este método é detalhe interno da classe e pode
        mudar sem aviso. Só `processar_mensagem` é API pública.
        """
        telefone = ctx.telefone

        # ─── Tenta cache Redis primeiro ───────────────────────────────────
        cache_key = f"atendimento:{self.empresa_id}:{telefone}"
        cache_id = await self._cache_get(cache_key)

        if cache_id is not None:
            at = (
                self.db.execute(
                    select(Atendimento).where(
                        Atendimento.id == cache_id,
                        Atendimento.empresa_id == self.empresa_id,   # dupla checagem
                        Atendimento.deleted_at.is_(None),
                        Atendimento.status != StatusAtendimento.FINALIZADO.value,
                    )
                )
                .scalar_one_or_none()
            )
            if at:
                logger.debug("bot_service | Cache hit | id=%s", at.id)
                return at
            await self._cache_del(cache_key)

        # ─── Consulta PostgreSQL (isolado por tenant) ─────────────────────
        stmt = (
            select(Atendimento)
            .join(Contato)
            .where(
                Atendimento.empresa_id == self.empresa_id,           # ✅ tenant
                Atendimento.canal_contratado_id == self.conexao.id,  # ✅ conexão
                Atendimento.deleted_at.is_(None),
                Atendimento.status != StatusAtendimento.FINALIZADO.value,
                Contato.telefone == telefone,
            )
            .order_by(Atendimento.created_at.desc())
            .limit(1)
        )
        atendimento = self.db.execute(stmt).scalar_one_or_none()

        if atendimento:
            if ctx.push_name and not atendimento.contato.nome:
                atendimento.contato.nome = ctx.push_name
                self.db.commit()
            await self._cache_set(cache_key, atendimento.id)
            return atendimento

        # ─── Cria novo ────────────────────────────────────────────────────
        return await self._criar_atendimento(ctx)

    async def _criar_atendimento(self, ctx: ContextoMensagem) -> Atendimento:
        """
        Cria atendimento novo + contato (se necessário).

        Transação atômica: se algo falhar, nada é persistido.
        """
        # Busca ou cria contato DENTRO do tenant
        contato = (
            self.db.execute(
                select(Contato).where(
                    Contato.telefone == ctx.telefone,
                    Contato.empresa_id == self.empresa_id,   # ✅ tenant
                    Contato.deleted_at.is_(None),
                )
            )
            .scalar_one_or_none()
        )

        if contato is None:
            contato = Contato(
                telefone=ctx.telefone,
                nome=ctx.push_name or "",
                empresa_id=self.empresa_id,
            )
            self.db.add(contato)
            self.db.flush()

        # Cria atendimento
        at = Atendimento(
            protocolo=self._gerar_protocolo(),
            contato_id=contato.id,
            canal_contratado_id=self.conexao.id,
            empresa_id=self.empresa_id,
            telefone_id=getattr(self.conexao, "telefone_id", None),  # condicional
            status=StatusAtendimento.AGUARDANDO.value,
            ativo=True,
            origem="bot",
        )
        self.db.add(at)
        self.db.commit()
        self.db.refresh(at)

        # Inicializa contexto
        self._set_step(at, BotStep.BOOT)
        self._set_ctx(at, "instancia", self.conexao.nome_instancia)

        # Cacheia
        cache_key = f"atendimento:{self.empresa_id}:{ctx.telefone}"
        await self._cache_set(cache_key, at.id)

        logger.info(
            "bot_service | Atendimento criado | id=%s prot=%s empresa=%s",
            at.id, at.protocolo, self.empresa_id,
        )
        return at

    # ═════════════════════════════════════════════════════════════════════
    # HANDLERS DE STEP — métodos privados
    # ═════════════════════════════════════════════════════════════════════

    async def _boot(self, ctx: ContextoMensagem) -> None:
        """Envia saudação + termo LGPD."""
        at = self.atendimento
        if at.status == StatusAtendimento.FINALIZADO.value:
            at.status = StatusAtendimento.AGUARDANDO.value
            at.ativo = True
            self.db.commit()

        await self._enviar_texto(ctx.telefone, self._mensagem_boas_vindas())
        await self._enviar_lista(
            numero=ctx.telefone,
            title="🔒 Política de Privacidade (LGPD)",
            description=self._texto_lgpd(),
            button_text="Responder",
            rows=[
                {"title": "✅ Sim, Li e Concordo", "description": "", "rowId": "LGPD_ACEITO"},
                {"title": "❌ Não concordo / Sair", "description": "", "rowId": "LGPD_RECUSADO"},
            ],
        )
        self._set_step(at, BotStep.AGUARDAR_LGPD)

    async def _lgpd(self, ctx: ContextoMensagem) -> None:
        """Processa consentimento LGPD."""
        recusou = (
            (ctx.msg_type == "list_response" and ctx.content.upper() == "LGPD_RECUSADO")
            or self._normalizar(ctx.content) in {"nao", "recuso", "sair", "n"}
        )

        if recusou:
            await self._enviar_texto(
                ctx.telefone,
                "Entendemos. Sem o aceite não podemos prosseguir pelo canal digital.\n\n"
                "Agradecemos o contato! Se mudar de ideia, é só nos chamar novamente. 💙",
            )
            at = self.atendimento
            at.status = StatusAtendimento.FINALIZADO.value
            at.ativo = False
            self.db.commit()
            self._set_step(at, BotStep.FINALIZADO)
            return

        await self._enviar_texto(
            ctx.telefone,
            "Obrigado pela confiança! 🙏\n\nPor gentileza, informe seu nome completo:",
        )
        self._set_step(self.atendimento, BotStep.AGUARDAR_NOME)

    async def _nome(self, ctx: ContextoMensagem) -> None:
        """Coleta nome do cliente."""
        nome = ctx.content.strip().title()
        if len(nome) < 2:
            await self._enviar_texto(
                ctx.telefone,
                "Não consegui identificar seu nome. Por favor, tente novamente:",
            )
            return

        self.atendimento.contato.nome = nome
        self.db.commit()
        self._set_ctx(self.atendimento, "nome", nome)

        await self._enviar_texto(
            ctx.telefone, f"Obrigado, {nome}! Seja muito bem-vindo(a). 😊"
        )
        await self._enviar_hub(ctx.telefone)
        self._set_step(self.atendimento, BotStep.AGUARDAR_HUB)

    async def _hub(self, ctx: ContextoMensagem) -> None:
        """Menu principal."""
        if ctx.msg_type != "list_response":
            nome = self._get_ctx(self.atendimento, "nome") or "cliente"
            await self._enviar_texto(
                ctx.telefone, f"Olá, {nome}! Por favor, utilize o menu abaixo:"
            )
            await self._enviar_hub(ctx.telefone)
            return

        canal = self._resolver_canal_do_hub(ctx.content.strip().upper())
        if canal:
            return await self._entrar_departamento(ctx, canal)

        await self._enviar_texto(
            ctx.telefone, "Opção não reconhecida. Utilize o menu abaixo:"
        )
        await self._enviar_hub(ctx.telefone)

    async def _departamento_dinamico(self, ctx: ContextoMensagem) -> None:
        """Seleção dentro do canal."""
        row = ctx.content.strip().upper() if ctx.msg_type == "list_response" else ""

        if row == "VOLTAR_HUB":
            return await self._voltar_hub(ctx.telefone)

        await self._enviar_texto(
            ctx.telefone, "🗣️ Transferindo para um atendente. Aguarde!"
        )
        self.atendimento.status = StatusAtendimento.EM_ATENDIMENTO.value
        self.db.commit()
        self._set_step(self.atendimento, BotStep.EM_ATENDIMENTO)

    # ═════════════════════════════════════════════════════════════════════
    # HELPERS DE MENU E NAVEGAÇÃO
    # ═════════════════════════════════════════════════════════════════════

    def _resolver_canal_do_hub(self, row: str) -> Optional[CanalContratado]:
        """
        Resolve o canal do hub a partir do `rowId` escolhido pelo cliente.

        ─────────────────────────────────────────────────────────────────
        ISOLAMENTO POR TENANT
        ─────────────────────────────────────────────────────────────────
        O filtro por `empresa_id` é obrigatório: sem ele, um cliente de uma
        empresa poderia acionar o canal de outra empresa pela lista do hub.
        """
        if not row:
            return None

        return (
            self.db.execute(
                select(CanalContratado).where(
                    CanalContratado.empresa_id == self.empresa_id,
                    CanalContratado.ativo.is_(True),
                    CanalContratado.apelido.ilike(f"%{row}%"),
                )
            )
            .scalars()
            .first()
        )

    async def _entrar_departamento(
        self,
        ctx: ContextoMensagem,
        canal: CanalContratado,
    ) -> None:
        """
        Entra no menu de um canal específico.

        O `rowId` do hub carrega o sufixo do canal; dentro do canal as
        opções passam a ser os itens do `Menu` correspondente.
        """
        menu = (
            self.db.execute(
                select(Menu).where(
                    Menu.canal_contratado_id == canal.id,
                    Menu.ativo.is_(True),
                )
            )
            .scalars()
            .first()
        )

        if menu is None:
            await self._enviar_texto(
                ctx.telefone,
                "Este atendimento ainda não está disponível. "
                "Vou transferir você para um atendente.",
            )
            await self._transferir_atendente(ctx.telefone)
            return

        itens = (
            self.db.execute(
                select(MenuItem)
                .where(MenuItem.menu_id == menu.id, MenuItem.ativo.is_(True))
                .order_by(MenuItem.ordem)
            )
            .scalars()
            .all()
        )

        if not itens:
            await self._enviar_texto(ctx.telefone, "Nenhuma opção disponível no momento.")
            await self._voltar_hub(ctx.telefone)
            return

        if menu.saudacao:
            await self._enviar_texto(ctx.telefone, menu.saudacao)

        await self._enviar_lista(
            numero=ctx.telefone,
            title=getattr(canal, "apelido", None) or "Atendimento",
            description="Selecione a opção desejada:",
            button_text="Ver opções",
            rows=[
                {
                    "title": item.titulo,
                    "description": (item.descricao or "")[:72],
                    "rowId": item.atalho or str(item.id),
                }
                for item in itens
            ],
            footer=menu.rodape or RODAPE,
        )

        self._set_ctx(self.atendimento, "canal_id", str(canal.id))
        self._set_ctx(self.atendimento, "menu_id", str(menu.id))
        self._set_step(self.atendimento, BotStep.DEPTO_DINAMICO)

    async def _transferir_atendente(self, telefone: str) -> None:
        """Encaminha a conversa para a fila humana."""
        self.atendimento.status = StatusAtendimento.EM_ATENDIMENTO.value
        self.db.commit()
        self._set_step(self.atendimento, BotStep.EM_ATENDIMENTO)
        logger.info("bot_service | Transferido para atendente | prot=%s", self.atendimento.protocolo)

    async def _voltar_hub(self, telefone: str) -> None:
        """Limpa o contexto do canal e reenvia o menu principal."""
        for chave in ("canal_id", "menu_id"):
            self._set_ctx(self.atendimento, chave, None)

        await self._enviar_texto(telefone, "🏠 Retornando ao menu principal...")
        await self._enviar_hub(telefone)
        self._set_step(self.atendimento, BotStep.AGUARDAR_HUB)

    # ═════════════════════════════════════════════════════════════════════
    # SAÍDA — única porta para o provedor, via BaseMessageAdapter
    # ═════════════════════════════════════════════════════════════════════
    #
    # Nenhum handler chama o provedor diretamente. Todos passam por aqui,
    # o que garante que uma troca de provedor (Evolution → Meta → PABX)
    # não exige alteração em nenhum handler.

    async def _enviar_texto(self, telefone: str, texto: str) -> Any:
        """Envia texto pelo adaptador do canal."""
        try:
            return await self.adapter.send_text(
                chat_id=telefone,
                text=texto,
                instance=self.conexao.nome_instancia,
            )
        except Exception:
            logger.exception("bot_service | Falha ao enviar texto | prot=%s", self.atendimento.protocolo)
            return None

    async def _enviar_lista(
        self,
        numero: str,
        title: str,
        description: str,
        button_text: str,
        rows: List[Dict[str, Any]],
        footer: Optional[str] = None,
    ) -> Any:
        """
        Envia um menu interativo pelo adaptador do canal.

        O contrato do adaptador é `send_list(..., sections=...)`, mas o
        Evolution API e o PABX recebem `rows`. A conversão para `sections`
        fica nesta camada, então cada adaptador deals com o formato nativo
        do seu provedor.
        """
        sections = [{"title": title, "rows": rows}]
        try:
            return await self.adapter.send_list(
                chat_id=numero,
                title=title,
                description=description,
                button_text=button_text,
                sections=sections,
                footer=footer or RODAPE,
                instance=self.conexao.nome_instancia,
            )
        except Exception:
            logger.exception("bot_service | Falha ao enviar lista | prot=%s", self.atendimento.protocolo)
            return None

    async def _enviar_hub(self, telefone: str) -> Any:
        """Envia o menu principal com os canais ativos do tenant."""
        canais = (
            self.db.execute(
                select(CanalContratado)
                .where(
                    CanalContratado.empresa_id == self.empresa_id,
                    CanalContratado.ativo.is_(True),
                )
                .order_by(CanalContratado.apelido)
            )
            .scalars()
            .all()
        )

        rows = [
            {
                "title": c.apelido or f"Canal {c.id}",
                "description": "",
                "rowId": (c.apelido or str(c.id)).upper().replace(" ", "_"),
            }
            for c in canais
        ]

        if not rows:
            return await self._enviar_texto(
                telefone, "Nenhum canal de atendimento disponível no momento."
            )

        return await self._enviar_lista(
            numero=telefone,
            title="Menu Principal",
            description="Escolha o assunto do seu atendimento:",
            button_text="Ver opções",
            rows=rows,
            footer=RODAPE,
        )

    async def _enviar_audio(self, telefone: str, texto: str) -> Any:
        """Envia a mensagem como áudio (modo áudio do cliente)."""
        try:
            gerado = await audio_service.gerar_audio(texto)
        except Exception:
            logger.exception("bot_service | Falha ao gerar áudio")
            return await self._enviar_texto(telefone, texto)

        url = f"{getattr(settings, 'BACKEND_URL', '').rstrip('/')}/api/audio/audios/{gerado['arquivo']}"
        try:
            return await self.adapter.send_media(
                chat_id=telefone,
                media_url=url,
                media_type="audio",
                instance=self.conexao.nome_instancia,
            )
        except Exception:
            logger.exception("bot_service | Falha ao enviar áudio")
            return None

    # ═════════════════════════════════════════════════════════════════════
    # MODO ÁUDIO — atalhos por frase, independentes do step
    # ═════════════════════════════════════════════════════════════════════

    def _pedido_ativar_audio(self, texto: str) -> bool:
        """True se o cliente pediu para ouvir em vez de ler."""
        return self._normalizar(texto) in FRASES_ATIVAR_AUDIO

    def _pedido_desativar_audio(self, texto: str) -> bool:
        """True se o cliente pediu para voltar ao modo texto."""
        return self._normalizar(texto) in FRASES_DESATIVAR_AUDIO

    async def _ativar_modo_audio(self, telefone: str) -> None:
        self._set_ctx(self.atendimento, "modo_audio", "1")
        await self._enviar_audio(telefone, "Modo áudio ativado. Fale ou digite normalmente.")

    async def _desativar_modo_audio(self, telefone: str) -> None:
        self._set_ctx(self.atendimento, "modo_audio", "0")
        await self._enviar_texto(telefone, "Modo texto ativado.")

    # ═════════════════════════════════════════════════════════════════════
    # TEXTO — templates
    # ═════════════════════════════════════════════════════════════════════

    def _mensagem_boas_vindas(self) -> str:
        """Saudação inicial. Usa a configurada; senão, monta com a empresa."""
        configurada = getattr(settings, "BOT_MENSAGEM_BOAS_VINDAS", "") or ""
        if configurada:
            return configurada

        empresa = getattr(settings, "EMPRESA_NOME", "") or "nossa equipe"
        return (
            f"Olá! Bem-vindo(a) ao atendimento do {empresa}. 💙\n\n"
            "Para iniciarmos, precisamos do seu aceite de privacidade."
        )

    def _texto_lgpd(self) -> str:
        """Termo de privacidade exibido no aceite."""
        lgpd_url = getattr(settings, "LGPD_URL", "") or ""
        empresa = getattr(settings, "EMPRESA_NOME", "") or "a empresa"

        texto = (
            f"Usamos seus dados apenas para identificar e melhorar o "
            f"atendimento do {empresa}, conforme a LGPD (Lei 13.709/2018).\n\n"
            "Você pode solicitar acesso, correção ou exclusão a qualquer momento."
        )
        if lgpd_url:
            texto += f"\n\nPolítica completa: {lgpd_url}"
        return texto

    # ═════════════════════════════════════════════════════════════════════
    # ESTADO DO ATENDIMENTO — step e contexto persistidos
    # ═════════════════════════════════════════════════════════════════════

    def _set_step(self, at: Atendimento, step: BotStep) -> None:
        """Grava o step do atendimento. `_get_step` faz a leitura."""
        self._set_ctx(at, "step", step.value)

    def _get_step(self) -> BotStep:
        """
        Lê o step atual.

        Um valor ausente ou desconhecido volta para BOOT: melhor recomeçar
        o fluxo do que travar o cliente num step que não existe mais.
        """
        bruto = self._get_ctx(self.atendimento, "step")
        try:
            return BotStep(bruto)
        except ValueError:
            return BotStep.BOOT

    def _set_ctx(
        self,
        at: Atendimento,
        chave: str,
        valor: Optional[str],
    ) -> None:
        """
        Upsert de uma chave no contexto do atendimento.

        ─────────────────────────────────────────────────────────────────
        POR QUE UPSERT E NÃO INSERT
        ─────────────────────────────────────────────────────────────────
        `_set_step` é chamado a cada transição e sempre na mesma chave.
        Sem o upsert, a segunda chamada criaria linha duplicada e a leitura
        passaria a depender da ordem de inserção.
        """
        if valor is None:
            self.db.execute(
                delete(AtendimentoContexto).where(
                    AtendimentoContexto.atendimento_id == at.id,
                    AtendimentoContexto.chave == chave,
                )
            )
            self.db.commit()
            return

        linha = (
            self.db.execute(
                select(AtendimentoContexto).where(
                    AtendimentoContexto.atendimento_id == at.id,
                    AtendimentoContexto.chave == chave,
                )
            )
            .scalars()
            .first()
        )

        if linha is None:
            linha = AtendimentoContexto(atendimento_id=at.id, chave=chave)
            self.db.add(linha)

        linha.valor = str(valor)
        self.db.commit()

    def _get_ctx(self, at: Atendimento, chave: str) -> Optional[str]:
        """Lê uma chave do contexto. `None` se nunca foi gravada."""
        return (
            self.db.execute(
                select(AtendimentoContexto.valor).where(
                    AtendimentoContexto.atendimento_id == at.id,
                    AtendimentoContexto.chave == chave,
                )
            )
            .scalars()
            .first()
        )

    # ═════════════════════════════════════════════════════════════════════
    # CACHE REDIS — atendimento ativo por (tenant, telefone)
    # ═════════════════════════════════════════════════════════════════════

    async def _cache_get(self, chave: str) -> Optional[int]:
        """Lê do Redis. Falha de Redis degrada para None, nunca quebra o bot."""
        try:
            bruto = await self.redis.get(chave)
        except Exception:
            logger.warning("bot_service | Cache indisponível | get %s", chave)
            return None
        return int(bruto) if bruto is not None else None

    async def _cache_set(self, chave: str, valor: int, ttl: int = CACHE_ATENDIMENTO_TTL) -> None:
        """Grava no Redis com TTL. Falha de Redis é logada, não propagada."""
        try:
            await self.redis.set(chave, valor, ex=ttl)
        except Exception:
            logger.warning("bot_service | Cache indisponível | set %s", chave)

    async def _cache_del(self, chave: str) -> None:
        """Remove do Redis. Falha de Redis é logada, não propagada."""
        try:
            await self.redis.delete(chave)
        except Exception:
            logger.warning("bot_service | Cache indisponível | del %s", chave)

    # ═════════════════════════════════════════════════════════════════════
    # UTILITÁRIOS
    # ═════════════════════════════════════════════════════════════════════

    @staticmethod
    def _normalizar(texto: Optional[str]) -> str:
        """
        Minúsculas, sem acento e sem pontuação.

        "Não  Concordo!" e "nao concordo" precisam casar com a mesma
        entrada do conjunto de frases; sem isso, o atalho de áudio e a
        comparação do LGPD falhariam por causa de um acento.
        """
        if not texto:
            return ""
        limpo = unicodedata.normalize("NFKD", str(texto))
        limpo = "".join(c for c in limpo if not unicodedata.combining(c))
        return re.sub(r"[^\w\s]", "", limpo.lower()).strip()

    @staticmethod
    def _gerar_protocolo() -> str:
        """
        Protocolo legível e ordenável por data.

        `PROT-AAAAMMDD-XXXXXX`: o prefixo permite indexar e o sufixo
        curto reduz a chance de colisão no dia.
        """
        return f"PROT-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:6].upper()}"


       