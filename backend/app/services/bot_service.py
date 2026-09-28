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
from typing import Optional
from uuid import uuid4

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import (
    BACKEND_URL,
    BOT_MENSAGEM_BOAS_VINDAS,
    EMPRESA_NOME,
    LGPD_URL,
)
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
from app.services import audio_service, evolution_service


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
        """
        self.db = db
        self.conexao = conexao
        self.redis = redis
        self._atendimento: Optional[Atendimento] = None  # setado depois

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
            await evolution_service.enviar_texto(
                instance=self.conexao.nome_instancia,
                number=ctx.telefone,
                text=(
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


       