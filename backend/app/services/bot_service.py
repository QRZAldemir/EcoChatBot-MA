"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Bot Service
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     bot_service.py
@module   Backend / App / Services / Bot
@author   Aldemir Queiroz
@since    2026
@version  3.1.0  · POO + cache Redis + transações atômicas + enums tipados
                  + isolamento multi-tenant reforçado (defesa em profundidade)
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

⚠️ CORREÇÕES MULTI-TENANT (v3.1.0)
──────────────────────────────────
Toda query desta classe carrega, OBRIGATORIAMENTE, o filtro por
`empresa_id`. Não confie em nenhum id vindo do cliente (WhatsApp):
o tenant sempre é derivado de `self.conexao.empresa_id`.

    • Atendimento ................ empresa_id + canal_contratado_id
    • Contato .................... empresa_id
    • CanalContratado (hub) ...... empresa_id + ativo
    • Menu / MenuItem ............ empresa_id + ativo  [NOVO]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

import logging
import re
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional
from uuid import uuid4

from redis.asyncio import Redis
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.adapters import BaseMessageAdapter, get_adapter
from app.core.config import settings
from app.exceptions import RecursoNaoEncontradoError
from app.models import (
    Atendimento,
    AtendimentoContexto,
    CanalContratado,
    Conexao,
    Contato,
    Menu,
    MenuItem,           # 🔧 FIX 1: importar MenuItem (antes faltava)
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

#: Prefixo usado no `rowId` dos canais do hub. Usar ID imutável evita
#: colisão entre apelidos parecidos ("Suporte" x "Suporte VIP") e também
#: evita que o cliente injete um apelido arbitrário no lugar do ID.
CANAL_ROW_PREFIX = "CANAL_"

#: Regex para remover emojis antes de gerar áudio
EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
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
# ENUMS TIPADOS
# ═══════════════════════════════════════════════════════════════════════════

class BotStep(str, Enum):
    """Estados da máquina de conversa."""
    BOOT             = "BOOT"
    AGUARDAR_LGPD    = "AGUARDAR_LGPD"
    AGUARDAR_NOME    = "AGUARDAR_NOME"
    AGUARDAR_HUB     = "AGUARDAR_HUB"
    DEPTO_DINAMICO   = "DEPTO_DINAMICO"
    EM_ATENDIMENTO   = "EM_ATENDIMENTO"
    FINALIZADO       = "FINALIZADO"


# ═══════════════════════════════════════════════════════════════════════════
# DATACLASS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ContextoMensagem:
    """Dados imutáveis da mensagem recebida."""
    remote_jid: str
    push_name: Optional[str]
    msg_type: str
    content: str

    @property
    def telefone(self) -> str:
        return self.remote_jid.replace("@s.whatsapp.net", "")

    @property
    def eh_grupo(self) -> bool:
        return self.remote_jid.endswith("@g.us")


# ═══════════════════════════════════════════════════════════════════════════
# EXCEÇÕES DE DOMÍNIO
# ═══════════════════════════════════════════════════════════════════════════

class BotError(Exception):
    """Exceção base do bot."""


class ConexaoInativaError(BotError):
    """Conexão/instância não existe ou está inativa."""


# ═══════════════════════════════════════════════════════════════════════════
# CLASSE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

class BotService:
    """
    Orquestrador do fluxo de bot.

    REGRA DE OURO DESTA CLASSE
    ──────────────────────────
    Nenhuma query pode omitir `empresa_id` (ou chegar a ele via join com
    uma entidade que já o possua). Todo acesso a dado multi-tenant passa
    por `self.empresa_id`, que por sua vez vem de `self.conexao` — nunca
    do payload do cliente.
    """

    def __init__(
        self,
        db: Session,
        conexao: Conexao,
        redis: Redis,
        adapter: Optional[BaseMessageAdapter] = None,
    ) -> None:
        self.db = db
        self.conexao = conexao
        self.redis = redis
        self.adapter = adapter if adapter is not None else self._criar_adapter()
        self._atendimento: Optional[Atendimento] = None

    def _criar_adapter(self) -> BaseMessageAdapter:
        """Resolve o adaptador a partir do canal da conexão."""
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
    # PROPRIEDADES
    # ═════════════════════════════════════════════════════════════════════

    @property
    def empresa_id(self) -> int:
        """Tenant da conexão. Fonte única de verdade do isolamento."""
        return self.conexao.empresa_id

    @property
    def atendimento(self) -> Atendimento:
        if self._atendimento is None:
            raise BotError(
                "Atendimento não inicializado. Chame _buscar_ou_criar antes."
            )
        return self._atendimento

    @property
    def eh_voip(self) -> bool:
        return getattr(self.conexao, "telefone_id", None) is not None

    # ═════════════════════════════════════════════════════════════════════
    # TRANSAÇÃO ATÔMICA  [🔧 FIX 6 — método citado no docstring mas ausente]
    # ═════════════════════════════════════════════════════════════════════

    @contextmanager
    def _transaction(self) -> Iterator[Session]:
        """
        Context manager que faz commit/rollback de bloco.

        Uso:
            with self._transaction():
                self.db.add(obj1)
                self.db.add(obj2)
            # commit automático

        Se algo falhar no bloco, faz rollback e propaga o erro.
        """
        try:
            yield self.db
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # ═════════════════════════════════════════════════════════════════════
    # FACTORY
    # ═════════════════════════════════════════════════════════════════════

    @classmethod
    def from_webhook(
        cls,
        db: Session,
        redis: Redis,
        instance_nome: str,
    ) -> "BotService":
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
    # ENTRYPOINT PÚBLICO
    # ═════════════════════════════════════════════════════════════════════

    async def processar_mensagem(self, ctx: ContextoMensagem) -> None:
        if ctx.eh_grupo:
            logger.debug("bot_service | Ignorando mensagem de grupo")
            return

        self._atendimento = await self._buscar_ou_criar(ctx)
        step = self._get_step()

        logger.info(
            "bot_service | Processando | step=%s tel=%s type=%s prot=%s empresa=%s",
            step.value, ctx.telefone, ctx.msg_type,
            self.atendimento.protocolo, self.empresa_id,
        )

        try:
            if step != BotStep.EM_ATENDIMENTO and ctx.msg_type != "list_response":
                if self._pedido_ativar_audio(ctx.content):
                    return await self._ativar_modo_audio(ctx.telefone)
                if self._pedido_desativar_audio(ctx.content):
                    return await self._desativar_modo_audio(ctx.telefone)

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
                pass
            else:
                await self._voltar_hub(ctx.telefone)

        except Exception:
            logger.exception(
                "bot_service | Erro no processamento | step=%s prot=%s",
                step.value, self.atendimento.protocolo,
            )
            await self._enviar_texto(
                ctx.telefone,
                "Ocorreu um erro ao processar sua mensagem. "
                "Por favor, tente novamente.",
            )

    # ═════════════════════════════════════════════════════════════════════
    # BUSCA / CRIA ATENDIMENTO — coração do isolamento multi-tenant
    # ═════════════════════════════════════════════════════════════════════

    async def _buscar_ou_criar(self, ctx: ContextoMensagem) -> Atendimento:
        telefone = ctx.telefone
        cache_key = f"atendimento:{self.empresa_id}:{telefone}"
        cache_id = await self._cache_get(cache_key)

        if cache_id is not None:
            at = (
                self.db.execute(
                    select(Atendimento).where(
                        Atendimento.id == cache_id,
                        Atendimento.empresa_id == self.empresa_id,
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

        stmt = (
            select(Atendimento)
            .join(Contato)
            .where(
                Atendimento.empresa_id == self.empresa_id,
                Atendimento.canal_contratado_id == self.conexao.id,
                Atendimento.deleted_at.is_(None),
                Atendimento.status != StatusAtendimento.FINALIZADO.value,
                Contato.telefone == telefone,
                Contato.empresa_id == self.empresa_id,   # 🔧 FIX: trava extra no join
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

        return await self._criar_atendimento(ctx)

    async def _criar_atendimento(self, ctx: ContextoMensagem) -> Atendimento:
        contato = (
            self.db.execute(
                select(Contato).where(
                    Contato.telefone == ctx.telefone,
                    Contato.empresa_id == self.empresa_id,
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

        at = Atendimento(
            protocolo=self._gerar_protocolo(),
            contato_id=contato.id,
            canal_contratado_id=self.conexao.id,
            empresa_id=self.empresa_id,
            telefone_id=getattr(self.conexao, "telefone_id", None),
            status=StatusAtendimento.AGUARDANDO.value,
            ativo=True,
            origem="bot",
        )
        self.db.add(at)
        self.db.commit()
        self.db.refresh(at)

        self._set_step(at, BotStep.BOOT)
        self._set_ctx(at, "instancia", self.conexao.nome_instancia)

        cache_key = f"atendimento:{self.empresa_id}:{ctx.telefone}"
        await self._cache_set(cache_key, at.id)

        logger.info(
            "bot_service | Atendimento criado | id=%s prot=%s empresa=%s",
            at.id, at.protocolo, self.empresa_id,
        )
        return at

    # ═════════════════════════════════════════════════════════════════════
    # HANDLERS DE STEP
    # ═════════════════════════════════════════════════════════════════════

    async def _boot(self, ctx: ContextoMensagem) -> None:
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
        Resolve o canal a partir do `rowId` escolhido.

        🔧 FIX 3+4: antes usava `apelido.ilike(%ROW%)`, que:
            • Colidia entre apelidos parecidos ("Suporte" x "Suporte VIP")
            • Dependia de apelido mutável
            • Podia casar com o canal de outra empresa se o apelido fosse igual

        Agora o `rowId` é `CANAL_{id}` e resolvemos por `id` + `empresa_id`.
        """
        if not row or not row.startswith(CANAL_ROW_PREFIX):
            return None

        try:
            canal_id = int(row.removeprefix(CANAL_ROW_PREFIX))
        except ValueError:
            return None

        return (
            self.db.execute(
                select(CanalContratado).where(
                    CanalContratado.id == canal_id,
                    CanalContratado.empresa_id == self.empresa_id,  # trava tenant
                    CanalContratado.ativo.is_(True),
                )
            )
            .scalar_one_or_none()
        )

    async def _entrar_departamento(
        self,
        ctx: ContextoMensagem,
        canal: CanalContratado,
    ) -> None:
        """
        Entra no menu de um canal específico.

        🔧 FIX 2: `Menu` e `MenuItem` agora filtram por `empresa_id`.
        Sem isso, mesmo que o `canal` esteja correto, um menu de outra
        empresa poderia ser exibido caso houvesse inconsistência de dados
        (defesa em profundidade).
        """

        # ─── Menu do canal, SEMPRE do tenant ─────────────────────────────
        menu = (
            self.db.execute(
                select(Menu).where(
                    Menu.canal_contratado_id == canal.id,
                    Menu.empresa_id == self.empresa_id,      # 🔧 FIX 2
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

        # ─── Itens do menu, SEMPRE do tenant ─────────────────────────────
        itens = (
            self.db.execute(
                select(MenuItem)
                .join(Menu, MenuItem.menu_id == Menu.id)     # 🔧 FIX 2
                .where(
                    MenuItem.menu_id == menu.id,
                    Menu.empresa_id == self.empresa_id,      # 🔧 FIX 2
                    MenuItem.ativo.is_(True),
                )
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
        self.atendimento.status = StatusAtendimento.EM_ATENDIMENTO.value
        self.db.commit()
        self._set_step(self.atendimento, BotStep.EM_ATENDIMENTO)
        logger.info("bot_service | Transferido para atendente | prot=%s", self.atendimento.protocolo)

    async def _voltar_hub(self, telefone: str) -> None:
        for chave in ("canal_id", "menu_id"):
            self._set_ctx(self.atendimento, chave, None)

        await self._enviar_texto(telefone, "🏠 Retornando ao menu principal...")
        await self._enviar_hub(telefone)
        self._set_step(self.atendimento, BotStep.AGUARDAR_HUB)

    # ═════════════════════════════════════════════════════════════════════
    # SAÍDA VIA ADAPTADOR
    # ═════════════════════════════════════════════════════════════════════

    async def _enviar_texto(self, telefone: str, texto: str) -> Any:
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

        # 🔧 FIX 3: rowId passa a ser CANAL_{id} — imune a colisão de apelido
        # e resistente a injeção de texto pelo cliente.
        rows = [
            {
                "title": c.apelido or f"Canal {c.id}",
                "description": "",
                "rowId": f"{CANAL_ROW_PREFIX}{c.id}",
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
    # MODO ÁUDIO
    # ═════════════════════════════════════════════════════════════════════

    def _pedido_ativar_audio(self, texto: str) -> bool:
        return self._normalizar(texto) in FRASES_ATIVAR_AUDIO

    def _pedido_desativar_audio(self, texto: str) -> bool:
        return self._normalizar(texto) in FRASES_DESATIVAR_AUDIO

    async def _ativar_modo_audio(self, telefone: str) -> None:
        self._set_ctx(self.atendimento, "modo_audio", "1")
        await self._enviar_audio(telefone, "Modo áudio ativado. Fale ou digite normalmente.")

    async def _desativar_modo_audio(self, telefone: str) -> None:
        self._set_ctx(self.atendimento, "modo_audio", "0")
        await self._enviar_texto(telefone, "Modo texto ativado.")

    # ═════════════════════════════════════════════════════════════════════
    # TEXTOS
    # ═════════════════════════════════════════════════════════════════════

    def _mensagem_boas_vindas(self) -> str:
        configurada = getattr(settings, "BOT_MENSAGEM_BOAS_VINDAS", "") or ""
        if configurada:
            return configurada

        empresa = getattr(settings, "EMPRESA_NOME", "") or "nossa equipe"
        return (
            f"Olá! Bem-vindo(a) ao atendimento do {empresa}. 💙\n\n"
            "Para iniciarmos, precisamos do seu aceite de privacidade."
        )

    def _texto_lgpd(self) -> str:
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
    # ESTADO DO ATENDIMENTO (step / contexto)
    # ═════════════════════════════════════════════════════════════════════

    def _set_step(self, at: Atendimento, step: BotStep) -> None:
        self._set_ctx(at, "step", step.value)

    def _get_step(self) -> BotStep:
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
    # CACHE REDIS
    # ═════════════════════════════════════════════════════════════════════

    async def _cache_get(self, chave: str) -> Optional[int]:
        try:
            bruto = await self.redis.get(chave)
        except Exception:
            logger.warning("bot_service | Cache indisponível | get %s", chave)
            return None
        return int(bruto) if bruto is not None else None

    async def _cache_set(self, chave: str, valor: int, ttl: int = CACHE_ATENDIMENTO_TTL) -> None:
        try:
            await self.redis.set(chave, valor, ex=ttl)
        except Exception:
            logger.warning("bot_service | Cache indisponível | set %s", chave)

    async def _cache_del(self, chave: str) -> None:
        try:
            await self.redis.delete(chave)
        except Exception:
            logger.warning("bot_service | Cache indisponível | del %s", chave)

    # ═════════════════════════════════════════════════════════════════════
    # UTILITÁRIOS
    # ═════════════════════════════════════════════════════════════════════

    @staticmethod
    def _normalizar(texto: Optional[str]) -> str:
        if not texto:
            return ""
        limpo = unicodedata.normalize("NFKD", str(texto))
        limpo = "".join(c for c in limpo if not unicodedata.combining(c))
        return re.sub(r"[^\w\s]", "", limpo.lower()).strip()

    @staticmethod
    def _gerar_protocolo() -> str:
        return f"PROT-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:6].upper()}"