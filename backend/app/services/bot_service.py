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
<<<<<<< Updated upstream
=======
import json
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
from app.config import (
    BACKEND_URL,
    BOT_MENSAGEM_BOAS_VINDAS,
    EMPRESA_NOME,
    LGPD_URL,
)
=======
# A v3.0.0 abandonedada importava BACKEND_URL, BOT_MENSAGEM_BOAS_VINDAS,
# EMPRESA_NOME e LGPD_URL daqui. Nenhum dos quatro existe em `app.config` —
# `app.config.Settings` não os declara e nada mais no projeto os define.
# Pior: os quatro apareciam só nessa linha, sem nenhum uso no corpo.
# Os textos da saudação e do termo de LGPD ficaram em `_mensagem_boas_vindas`
# e `_texto_lgpd`, que são autocontidos. Se um dia a empresa quiser o nome
# dela no menu, o lugar é um campo novo em `Settings` — não um `os.getenv`
# espalhado, que é o que `deepseek_service` faz hoje.
>>>>>>> Stashed changes
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

def _resolver_canal_por_instancia(db: Session, instance_nome: str) -> CanalContratado:
    """
    Acha o `CanalContratado` cujo `credenciais["instance"]` é `instance_nome`.

    ─────────────────────────────────────────────────────────────────────
    POR QUE A BUSCA É EM PYTHON E NÃO EM SQL
    ─────────────────────────────────────────────────────────────────────
    `credenciais` é `Text` com JSON dentro — o Postgres não enxerga
    estrutura aí. Filtrar por chave exigiria `credenciais::jsonb ->>`, que
    não existe no SQLite do ambiente de teste. Optamos por filtrar em
    Python sobre os canais ativos de WhatsApp.

    O custo é proporcional ao número de canais de WhatsApp da base, e não
    ao de tenants: são ~1 linha por empresa conectada. Se isso virar
    gargalo, o caminho é um índice GIN em `jsonb_path_ops` com migration —
    não uma coluna nova, porque o dado já tem casa.

    ─────────────────────────────────────────────────────────────────────
    POR QUE O NOME DA INSTÂNCIA PRECISA SER ÚNICO
    ─────────────────────────────────────────────────────────────────────
    O webhook chega com o nome da instância e o autentica com um
    `WEBHOOK_SECRET` global. A LINEHA DE CONFIANÇA É O NOME: se dois
    tenantsRegistrarem a mesma instância, um webhooks inbound pode entrar
    na fila do outro. Detectamos isso e recusamos, em vez de escolher um
    dos dois — escolher seria o pior resultado possível aqui.
    """
    stmt = select(CanalContratado).where(
        CanalContratado.tipo == "whatsapp",
        CanalContratado.ativo.is_(True),
        CanalContratado.deleted_at.is_(None),
    )

    encontrados: list[tuple[CanalContratado, str]] = []
    for canal in db.execute(stmt).scalars():
        bruto = canal.credenciais
        if not bruto:
            continue
        try:
            dados = json.loads(bruto) if isinstance(bruto, str) else dict(bruto)
        except (ValueError, TypeError):
            logger.warning(
                "bot_service | credenciais não são JSON válido | canal=%s", canal.id
            )
            continue
        nome = dados.get("instance")
        if nome and str(nome).strip() == instance_nome.strip():
            encontrados.append((canal, str(nome)))

    if not encontrados:
        logger.error(
            "bot_service | Instância não encontrada | instance=%s", instance_nome
        )
        raise RecursoNaoEncontradoError(
            f"Instância '{instance_nome}' não pertence a nenhum canal ativo."
        )

    if len(encontrados) > 1:
        ids = [c.id for c, _ in encontrados]
        logger.error(
            "bot_service | Instância ambígua | instance=%s canais=%s",
            instance_nome, ids,
        )
        raise BotError(
            f"A instância '{instance_nome}' está registrada em {len(ids)} canais "
            f"({ids}). Recusando a mensagem: escolher um deles poderia atender "
            f"o cliente na fila do tenant errado."
        )

    return encontrados[0][0]


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
<<<<<<< Updated upstream
    def eh_voip(self) -> bool:
        """True se a conexão é de telefonia IP (PABX/VoIP)."""
        return getattr(self.conexao, "telefone_id", None) is not None

=======
    def _canal(self) -> CanalContratado:
        """Canal contratado da conversa. Toda envio sai por ele."""
        return self.conexao.canal_contratado

    @property
    def _nome_instancia(self) -> str:
        """
        Nome da instância na Evolution.

        ─────────────────────────────────────────────────────────────────
        `Conexao` não tem este campo: quem guarda é
        `CanalContratado.credenciais["instance"]`. Lemos de lá e NÃO
        aceitamos fallback silencioso — se o JSON não trouxer a chave,
        mandamos mensagem para a instância vazia e a Evolution devolve 404
        sem dizer por quê. Melhor falhar aqui, com nome de tenant.
        """
        bruto = self._canal.credenciais
        if not bruto:
            raise BotError(
                f"Canal {self._canal.id} sem credenciais: não há como saber "
                f"a instância da Evolution."
            )
        try:
            dados = json.loads(bruto) if isinstance(bruto, str) else dict(bruto)
        except (ValueError, TypeError):
            raise BotError(
                f"Canal {self._canal.id} tem credenciais em JSON inválido."
            ) from None

        nome = dados.get("instance")
        if not nome:
            raise BotError(
                f"Canal {self._canal.id} sem a chave 'instance' nas credenciais."
            )
        return str(nome)

    @property
    def _telefone_id(self) -> Optional[int]:
        """Telefone que sustenta o canal — via `Conexao -> CanalContratado`."""
        canal = self.conexao.canal_contratado
        return getattr(canal, "telefone_id", None) if canal else None

    @property
    def eh_voip(self) -> bool:
        """True se o canal é de telefonia IP (PABX/VoIP)."""
        return self._telefone_id is not None

>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
=======
        # ── Resolve o CANAL, não a Conexao ──────────────────────────────
        #
        # A v3.0.0 consultava `Conexao.nome_instancia` e filtrava por
        # `Conexao.ativo`. Nenhum dos dois campos existe no model canônico:
        # `Conexao` guarda só metadados de sessão (status, iniciada_em,
        # tentativas) e aponta para o canal via `canal_contratado_id`.
        # `nome_instancia` só aparecia numa segunda classe `Conexao`
        # declarativa e morta, no rodapé do arquivo — que não descrevia
        # nenhuma tabela real. Por isso a busca sai com
        # `AttributeError` em produção, na primeira mensagem.
        #
        # O nome da instância da Evolution fica em
        # `CanalContratado.credenciais`, na chave `"instance"` — é o que o
        # próprio model documenta no comment da coluna:
        #     comment='Ex.: {"instance": "ecochat", "api_key": "..."}'
        canal = _resolver_canal_por_instancia(db, instance_nome)

>>>>>>> Stashed changes
        stmt = select(Conexao).where(
            Conexao.canal_contratado_id == canal.id,
        )
        conexao = db.execute(stmt).scalars().first()

        if conexao is None:
            # Sem sessão, ainda dá para atender: o bot só precisa do canal
            # para saber o tenant e a instância. Não transformamos uma
            # sessão ainda não aberta em recusa de mensagem.
            logger.warning(
                "bot_service | Instância sem Conexao registrada | "
                "canal=%s instance=%s — seguindo pelo canal",
                canal.id, instance_nome,
            )
            conexao = Conexao(
                canal_contratado_id=canal.id,
                empresa_id=canal.empresa_id,
            )
            db.add(conexao)
            db.flush()

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
<<<<<<< Updated upstream
                instance=self.conexao.nome_instancia,
=======
                instance=self._nome_instancia,
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
                Atendimento.canal_contratado_id == self.conexao.id,  # ✅ conexão
=======
                Atendimento.canal_contratado_id == self.conexao.canal_contratado_id,  # ✅ canal
>>>>>>> Stashed changes
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
            canal_contratado_id=self.conexao.canal_contratado_id,
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
        self._set_ctx(at, "instancia", self._nome_instancia)

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

<<<<<<< Updated upstream
    def _resolver_canal_do_hub(self, row: str) -> Optional[CanalContratado]:


       
=======
# ═════════════════════════════════════════════════════════════════════
    # RESOLUÇÃO DE CANAL — hub → departamento
    # ═════════════════════════════════════════════════════════════════════

    def _menu_do_hub(self) -> Optional[Menu]:
        """
        Menu configurado para o canal desta conexão.

        `Menu` não tem coluna que aponte para `Conexao` — só
        `canal_contratado_id`. A ligação é por tenant: o menu do bot é o
        menu do canal contratado desta conversa.
        """
        stmt = select(Menu).where(
            Menu.empresa_id == self.empresa_id,
            Menu.deleted_at.is_(None),
        )
        if self._telefone_id:
            stmt = stmt.where(Menu.canal_contratado_id == self._telefone_id)
        return self.db.execute(stmt).scalars().first()

    def _canais_do_hub(self) -> list[CanalContratado]:
        """
        Canais contratados que o cliente pode escolher no menu.

        ─────────────────────────────────────────────────────────────────
        POR QUE FILTRAR POR `telefone_id` NO VOIP
        ─────────────────────────────────────────────────────────────────
        Numa conexão PABX o mesmo tenant pode ter vários telefones, e cada
        um atende um departments. Sem esse filtro, o ramal 1000 receberia o
        menu do ramal 2000.
        """
        stmt = select(CanalContratado).where(
            CanalContratado.empresa_id == self.empresa_id,
            CanalContratado.deleted_at.is_(None),
        )
        if self.eh_voip:
            stmt = stmt.where(
                CanalContratado.telefone_id == self._telefone_id
            )
        return list(self.db.execute(stmt).scalars())

    def _resolver_canal_do_hub(self, row: str) -> Optional[CanalContratado]:
        """
        Traduz o rowId escolhido na lista para um CanalContratado.

        Aceita três formatos porque o WhatsApp devolve a lista de três
        jeitos dependendo de como o cliente tocou:
            • `CANAL_12`     — rowId enviado por nós (toque na opção)
            • `12`           — id puro (digitação)
            • `suporte`      — apelido digitado (cliente preencheu)

        None devolve para o menu, não um canal: `_hub` já trata `None`
        reenviando o menu, e é isso que o cliente espera ao digitar algo sem
        correspondência.
        """
        alvo = self._normalizar(row or "")
        if not alvo or alvo in {"voltar hub", "menu", "hub"}:
            return None

        canais = self._canais_do_hub()

        # rowId: CANAL_<id>
        #
        # O separador é `_`, e o mesmo que `_enviar_hub` usa para montar a
        # lista. Antes era `canal ` com espaço: `_normalizar` não troca `_`
        # por espaço, então `CANAL_2` virava `canal_2`, não casava com
        # `canal `, e TODO toque no menu caía em "opção não reconhecida".
        if alvo.startswith("canal_"):
            digitos = alvo[len("canal_"):]
            for canal in canais:
                if str(canal.id) == digitos:
                    return canal
            return None

        for canal in canais:
            if str(canal.id) == alvo:
                return canal
            if self._normalizar(canal.apelido or "") == alvo:
                return canal
            if self._normalizar(canal.tipo or "") == alvo:
                return canal
        return None

    async def _enviar_hub(self, telefone: str) -> None:
        """Envia o menu principal do tenant."""
        menu = self._menu_do_hub()
        canais = self._canais_do_hub()

        if not canais:
            await self._enviar_texto(
                telefone,
                "⚠️ Nenhum canal disponível para atendimento no momento. "
                "Tente novamente mais tarde.",
            )
            return

        rows = [
            {
                "title": f"📞 {canal.apelido or canal.tipo}",
                "description": "",
                "rowId": f"CANAL_{canal.id}",
            }
            for canal in canais
        ]

        await self._enviar_lista(
            numero=telefone,
            title=menu.nome if menu else "Menu Principal",
            description=menu.saudacao or "Escolha o assunto que deseja tratar:",
            button_text="Ver opções",
            rows=rows,
            footer=menu.rodape or RODAPE,
        )

    async def _entrar_departamento(self, ctx: ContextoMensagem, canal: CanalContratado) -> None:
        """Entra no canal escolhido e abre a seleção interna dele."""
        nome = canal.apelido or canal.tipo
        self._set_ctx(self.atendimento, "canal_id", str(canal.id))
        self._set_ctx(self.atendimento, "canal", nome)

        await self._enviar_texto(
            ctx.telefone,
            f"📂 *{nome}*\n\n"
            f"Digite a sua solicitação e um atendente responderá em instantes.",
        )
        self._set_step(self.atendimento, BotStep.DEPTO_DINAMICO)

    async def _voltar_hub(self, telefone: str) -> None:
        """Volta ao menu principal."""
        self._set_step(self.atendimento, BotStep.AGUARDAR_HUB)
        await self._enviar_texto(telefone, "↩️ Voltando ao menu principal:")
        await self._enviar_hub(telefone)

    # ═════════════════════════════════════════════════════════════════════
    # MODO ÁUDIO — atalho universal de acessibilidade
    # ═════════════════════════════════════════════════════════════════════

    def _pedido_ativar_audio(self, conteudo: str) -> bool:
        """True se o cliente pediu para ouvir as respostas."""
        return self._normalizar(conteudo) in {
            self._normalizar(f) for f in FRASES_ATIVAR_AUDIO
        }

    def _pedido_desativar_audio(self, conteudo: str) -> bool:
        """True se o cliente pediu voltar para texto."""
        return self._normalizar(conteudo) in {
            self._normalizar(f) for f in FRASES_DESATIVAR_AUDIO
        }

    def _modo_ativo(self) -> bool:
        """True se este atendimento está em modo áudio."""
        return self._get_ctx(self.atendimento, "modo_audio") == "1"

    async def _ativar_modo_audio(self, telefone: str) -> None:
        """
        Ativa o modo áudio e confirma com uma faixa de voz.

        O MP3 já sai sem emoji e sem markdown: o gTTS soletra
        "arroba" e "asterisco" em voz alta, e um menu com emoji vira uma
        leitura sem sentido.
        """
        texto = "Modo áudio ativado. Vou te falar as respostas daqui em diante."
        self._set_ctx(self.atendimento, "modo_audio", "1")

        try:
            limpo = MARKDOWN_RE.sub("", EMOJI_RE.sub("", texto)).strip()
            gerado = await audio_service.gerar_audio(limpo)
            caminho = audio_service.caminho_audio(gerado["arquivo"])
            if caminho is not None:
                await evolution_service.enviar_midia(
                    instance=self._nome_instancia,
                    number=telefone,
                    media_url=str(caminho),
                    mediatype="audio",
                )
                return
        except Exception:
            # Falha de TTS não pode impedir o cliente de usar o bot:
            # cai para texto, que é o modo padrão.
            logger.warning(
                "bot_service | TTS indisponível, respondendo em texto | tel=%s",
                telefone,
            )

        await self._enviar_texto(telefone, "🔊 " + texto)

    async def _desativar_modo_audio(self, telefone: str) -> None:
        """Volta para respostas em texto."""
        self._set_ctx(self.atendimento, "modo_audio", "0")
        await self._enviar_texto(
            telefone, "🔇 Modo áudio desativado. Volto a responder por texto."
        )

    # ═════════════════════════════════════════════════════════════════════
    # ENVIO — casca o EvolutionService e centraliza a instância
    # ═════════════════════════════════════════════════════════════════════

    async def _enviar_texto(self, telefone: str, texto: str) -> None:
        """Envia texto. A instância vem sempre da conexão — nunca do cliente."""
        await evolution_service.enviar_texto(
            instance=self._nome_instancia,
            number=telefone,
            text=texto,
        )

    async def _enviar_lista(
        self,
        numero: str,
        title: str,
        description: str,
        button_text: str,
        rows: list[dict],
        footer: Optional[str] = None,
    ) -> None:
        """
        Envia lista interativa.

        A Evolution exige `sections`, e o WhatsApp mostra no máximo 10
        linhas por seção. Passamos uma seção só; se um dia o menu passar de
        10 itens, truncamos em vez de deixar a API recusar o envio — do
        contrário o cliente ficaria sem menu nenhum.
        """
        if len(rows) > 10:
            logger.warning(
                "bot_service | Menu com %d itens excede o limite de 10 do "
                "WhatsApp; truncando", len(rows),
            )
            rows = rows[:10]

        await evolution_service.enviar_lista(
            instance=self._nome_instancia,
            number=numero,
            title=title,
            description=description,
            button_text=button_text,
            sections=[{"title": title, "rows": rows}],
            footer=footer,
        )

    # ═════════════════════════════════════════════════════════════════════
    # STEP E CONTEXTO — persistidos em atendimento_contextos
    # ═════════════════════════════════════════════════════════════════════

    #: Chave reservada em `atendimento_contextos` para o step da máquina.
    CHAVE_STEP = "bot_step"

    def _get_step(self) -> BotStep:
        """
        Step atual. Assume BOOT quando não há contexto gravado.

        ─────────────────────────────────────────────────────────────────
        POR QUE O STEP FICA NO BANCO E NÃO NO REDIS
        ─────────────────────────────────────────────────────────────────
        O Redis guarda o *id* do atendimento (acelera a busca). O *step* é
        o estado da conversa: se ficar só no Redis, uma reinicialização do
        Redis joga o cliente de volta ao BOOT e ele recebe a saudação de
        novo, no meio de uma conversa. No banco, o estado sobrevive a
        qualquer restart — e `atendimento_contextos` já existe para isso.

        Note que `_get_step` é sync e o cache é async: é exatamente por
        isso que o step nunca passa pelo Redis.
        """
        at = self._atendimento
        if at is None:
            return BotStep.BOOT

        for ctx in (at.contextos or []):
            if ctx.chave != self.CHAVE_STEP:
                continue
            try:
                return BotStep(ctx.valor)
            except ValueError:
                # Valor gravado por versão futura do bot: não derruba a
                # conversa, reinicia o fluxo.
                logger.warning(
                    "bot_service | Step desconhecido no banco | valor=%r | "
                    "voltando para BOOT", ctx.valor,
                )
                return BotStep.BOOT
        return BotStep.BOOT

    def _set_step(self, at: Atendimento, step: BotStep) -> None:
        """Grava o step da máquina."""
        self._set_ctx(at, self.CHAVE_STEP, step.value)

    def _get_ctx(self, at: Atendimento, chave: str) -> Optional[str]:
        """Lê um valor do contexto do atendimento."""
        for ctx in (at.contextos or []):
            if ctx.chave == chave:
                return ctx.valor
        return None

    def _set_ctx(self, at: Atendimento, chave: str, valor: Optional[str]) -> None:
        """
        Upsert de uma chave de contexto.

        O contexto é EAV com `UNIQUE(atendimento_id, chave)`: buscar antes
        de inserir não é opcional, senão a segunda escrita estoura a
        constraint e derruba a mensagem inteira.
        """
        for ctx in (at.contextos or []):
            if ctx.chave == chave:
                ctx.valor = valor
                self.db.commit()
                return

        self.db.add(
            AtendimentoContexto(
                atendimento_id=at.id,
                chave=chave,
                valor=valor,
                origem="bot",
            )
        )
        self.db.commit()

    # ═════════════════════════════════════════════════════════════════════
    # CACHE REDIS — otimização, nunca caminho crítico
    # ═════════════════════════════════════════════════════════════════════

    async def _cache_get(self, chave: str) -> Optional[int]:
        """
        Lê um id do cache.

        Redis fora do ar NÃO pode derrubar o bot: a conversa inteira
        depende deste método e ele é chamado antes de qualquer query. Por
        isso toda falha vira `None`, e o chamador cai no banco.
        """
        try:
            bruto = await self.redis.get(chave)
        except Exception:
            logger.warning("bot_service | Redis indisponível (get)", exc_info=True)
            return None

        if bruto is None:
            return None
        try:
            return int(bruto)
        except (TypeError, ValueError):
            return None

    async def _cache_set(self, chave: str, valor: int) -> None:
        """Grava um id no cache com TTL."""
        try:
            await self.redis.set(
                chave, str(valor), ex=CACHE_ATENDIMENTO_TTL
            )
        except Exception:
            logger.warning("bot_service | Redis indisponível (set)", exc_info=True)

    async def _cache_del(self, chave: str) -> None:
        """Invalida uma chave do cache."""
        try:
            await self.redis.delete(chave)
        except Exception:
            logger.warning("bot_service | Redis indisponível (del)", exc_info=True)

    # ═════════════════════════════════════════════════════════════════════
    # UTILITÁRIOS
    # ═════════════════════════════════════════════════════════════════════

    def _gerar_protocolo(self) -> str:
        """
        Protocolo único do atendimento.

        Onde a data vem primeiro: o protocolo é o que o cliente lê em voz
        alta, e ordenar por ele deixa a conferência do dia óbvia.
        """
        hoje = datetime.now(timezone.utc).strftime("%Y%m%d")
        return f"PROT-{hoje}-{uuid4().hex[:6].upper()}"

    @staticmethod
    def _normalizar(texto: Optional[str]) -> str:
        """
        Minúsculas, sem acento, sem espaço duplo.

        A comparação do menu não pode falhar por causa de acento: o cliente
        digita "atendimento" e o `apelido` está "Atendimento". Com acento,
        `==` falha e o bot responde "opção não reconhecida" para uma opção
        que ele acabou de mostrar.
        """
        if not texto:
            return ""
        decomposto = unicodedata.normalize("NFKD", texto)
        sem_acento = "".join(c for c in decomposto if not unicodedata.combining(c))
        return re.sub(r"\s+", " ", sem_acento).strip().lower()

    @staticmethod
    def _mensagem_boas_vindas() -> str:
        """Saudação inicial. O nome vem depois do aceite de LGPD."""
        return (
            "Olá! 👋 Seja muito bem-vindo(a) ao nosso atendimento.\n\n"
            "Antes de começar, precisamos do seu consentimento para o "
            "tratamento dos seus dados, conforme a LGPD (Lei 13.709/2018).\n\n"
            "Ao prosseguir, você concorda com o uso dos seus dados "
            "exclusivamente para o atendimento deste conversation."
        )

    @staticmethod
    def _texto_lgpd() -> str:
        """Termo resumido exibido na lista interativa."""
        return (
            "Usamos seus dados apenas para este atendimento: nome, telefone "
            "e o histórico da conversa.\n\n"
            "Não vendemos, alugamos nem compartilhamos seus dados com "
            "terceiros para fins publicitários.\n\n"
            "Você pode pedir a exclusão dos seus dados a qualquer momento."
        )


# ═════════════════════════════════════════════════════════════════════
# ADAPTADOR — o contrato que o webhook já consome
# ═════════════════════════════════════════════════════════════════════

async def processar_mensagem_recebida(
    db: Session,
    instance_nome: str,
    remote_jid: str,
    push_name: Optional[str],
    msg_type: str,
    content: str,
) -> None:
    """
    Ponto de entrada chamado por `app/routers/webhook_routers.py`.

    ─────────────────────────────────────────────────────────────────────
    POR QUE ESTA FUNÇÃO AINDA EXISTE NA V3.0.0
    ─────────────────────────────────────────────────────────────────────
    A v3.0.0 transformou o bot em classe: o estado passa a viver em
    `self`, e cada requisição constrói um `BotService` novo. O webhook,
    porém, importa esta função — mudar a assinatura dele obrigaria a
    reescrever o roteador inteiro e o contrato com a Evolution API.

    Este adaptador é a costura: resolve as dependências, monta o objeto e
    delega. A forma como o webhook chama não muda.

    ─────────────────────────────────────────────────────────────────────
    MULTI-TENANT
    ─────────────────────────────────────────────────────────────────────
    A âncora de segurança é `instance_nome`. `from_webhook` resolve a
    conexão e REJEITA instância inexistente ou inativa — é essa validação
    que impede um webhook de Tenant A processar mensagens na conta do
    Tenant B só porque os dois têm um número igual.
    """
    if remote_jid.endswith("@g.us"):
        logger.debug("bot_service | Ignorando mensagem de grupo")
        return

    from app.redis_client import get_redis

    bot = BotService.from_webhook(
        db=db,
        redis=get_redis(),
        instance_nome=instance_nome,
    )

    await bot.processar_mensagem(
        ContextoMensagem(
            remote_jid=remote_jid,
            push_name=push_name,
            msg_type=msg_type,
            content=content,
        )
    )
>>>>>>> Stashed changes
