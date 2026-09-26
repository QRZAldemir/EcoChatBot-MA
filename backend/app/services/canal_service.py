"""
================================================================================
MÓDULO: app/services/canal_service.py
AUTOR: Aldemir Queiroz
DATA: 2026-09-26
VERSÃO: 3.0.0
OBJETIVO: Regras de negócio do canal CONTRATADO — CRUD, validações, webhooks
          e métricas.
PASTA: backend/app/services/
================================================================================

O QUE MUDOU NESTA VERSÃO (3.0.0)
-------------------------------
    O canal deixou de ser um registro solto (`Canal`) e virou um ITEM DO
    CONTRATO (`CanalContratado`). As consequences no serviço:

    1. O Tenant é a EMPRESA. Toda query filtra por `empresa_id`. Não existe
       mais `cliente_id` aqui.

    2. A UNICIDADE mudou de lugar. Antes era "o nome do canal é único na
       empresa" — validado no código, sem proteção do banco. Agora a regra
       real é "um tipo por telefone": a empresa não pode ter dois WhatsApp no
       mesmo número, e PODE ter dois WhatsApp em números diferentes. Essa
       regra está no banco (`uq_canais_contratados_telefone_tipo`), e o
       serviço só a traduz em erro de negócio.

    3. `identificador` e `configuracao` viraram `credenciais` (JSON). Os
       valores sensíveis saem de lá por `_credencial()`, e NUNCA voltam em
       claro na resposta — a ofuscação é garantida pelo schema.

    4. DELETAR passou a ser SOFT DELETE. O canal é a memória do histórico de
       atendimento: apagar o registro perderia a origem das conversas. O
       modelo tem `SoftDeleteMixin`, e apagar físico não é mais aceitável.

    5. As métricas passaram a usar o ENUM de status (`aguardando`,
       `em_andamento`, `pausado`, `transferido`) em vez dos literais
       `aberto`/`fila`/`em_atendimento`, que não existem no domínio. E o
       tempo de resposta passou a ser REAL, lendo `primeira_resposta_em` —
       a coluna existe e antes era ignorada.

SEGURODANÇA
-----------
    • `webhook_token` é gerado com `secrets.token_urlsafe` quando não
      informado. É ele que valida a origem do webhook recebido; sem ele,
      qualquer um poderia injetar mensagem falsa na fila.
    • `credenciais` é serializado com `ensure_ascii=False`.
================================================================================
"""
import json
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Atendimento, CanalContratado, Telefone
from app.models.enums import StatusAtendimento
from app.schemas.canal_schemas import (
    CHAVE_IDENTIFICADOR,
    CanalContratadoCreate,
    CanalContratadoUpdate,
)
from app.exceptions import (
    CanalNaoEncontradoError,
    CanalNomeDuplicadoError,
    CanalTipoInvalidoError,
    RecursoInvalidoError,
)

logger = logging.getLogger(__name__)

#: Status que contam como "atendimento em aberto" (para bloquear exclusão).
STATUS_ABERTOS = [
    StatusAtendimento.AGUARDANDO.value,
    StatusAtendimento.EM_ANDAMENTO.value,
    StatusAtendimento.PAUSADO.value,
    StatusAtendimento.TRANSFERIDO.value,
]


class CanalService:
    """
    Regras de negócio do canal contratado.

    Responsabilidades:
        - CRUD de canais contratados, com soft delete
        - Isolamento multi-tenant por `empresa_id`
        - Unicidade "um tipo por telefone"
        - Configuração de webhook por tipo de canal
        - Métricas de uso para o dashboard
    """

    def __init__(self, db: Session):
        self.db = db

    # ==============================================================================
    # LEITURA DE CREDENCIAIS
    # ==============================================================================
    @staticmethod
    def _credenciais(canal: CanalContratado) -> Dict[str, Any]:
        """Devolve `credenciais` como dict, mesmo que o banco traga string."""
        bruto = canal.credenciais
        if not bruto:
            return {}
        if isinstance(bruto, dict):
            return bruto
        try:
            return json.loads(bruto)
        except (TypeError, ValueError):
            logger.warning("credenciais do canal %s não é JSON válido", canal.id)
            return {}

    def _credencial(self, canal: CanalContratado, chave: str) -> Optional[str]:
        """Lê uma credencial específica do canal."""
        return self._credenciais(canal).get(chave)

    @staticmethod
    def _serializar_credenciais(credenciais: Optional[Dict[str, Any]]) -> Optional[str]:
        """Serializa o dict de credenciais para TEXT no banco."""
        if not credenciais:
            return None
        try:
            return json.dumps(credenciais, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            raise RecursoInvalidoError("Credenciais em formato inválido") from e

    # ==============================================================================
    # CRUD
    # ==============================================================================
    def criar_canal(self, data: CanalContratadoCreate, empresa_id: int) -> CanalContratado:
        """
        Contrata um novo canal para a empresa.

        Fluxo:
            1. Valida que o telefone existe, é ativo e é da MESMA empresa
            2. Valida "um tipo por telefone"
            3. Valida o tipo de canal
            4. Valida o apelido é único na empresa (evita confusão na tela)
            5. Dobra o identificador dentro de `credenciais`
            6. Gera `webhook_token` se não informado
            7. Persiste e tenta configurar o webhook no provedor
        """
        # 1. O telefone precisa ser DA EMPRESA — é o que impede um canal de
        #    apontar para o número de outro tenant.
        self._validar_telefone(data.telefone_id, empresa_id)

        # 2. Regra real de unicidade: um tipo por telefone.
        self._validar_tipo_por_telefone(data.telefone_id, data.tipo)

        # 3. Tipo suportado.
        self._validar_tipo_canal(data.tipo)

        # 4. Apelido único dentro da empresa (usabilidade, não integridade).
        if data.apelido:
            self._validar_apelido_unico(data.apelido, empresa_id)

        # 5. O identificador validado pelo schema entra em `credenciais`.
        credenciais: Dict[str, Any] = dict(data.credenciais or {})
        if data.identificador:
            chave = CHAVE_IDENTIFICADOR.get(data.tipo, "identificador")
            credenciais[chave] = data.identificador

        # 6. Token de webhook: sem ele, qualquer um injeta mensagem na fila.
        webhook_token = data.webhook_token or secrets.token_urlsafe(32)

        canal = CanalContratado(
            empresa_id=empresa_id,
            telefone_id=data.telefone_id,
            tipo=data.tipo,
            apelido=data.apelido,
            credenciais=self._serializar_credenciais(credenciais),
            webhook_token=webhook_token,
            webhook_url=data.webhook_url,
            horario_inicio=data.horario_inicio,
            horario_fim=data.horario_fim,
            dias_semana=data.dias_semana,
            ativo=data.ativo,
        )

        self.db.add(canal)
        self.db.commit()
        self.db.refresh(canal)

        logger.info(
            "Canal contratado: ID=%s tipo=%s telefone=%s empresa=%s",
            canal.id, canal.tipo, canal.telefone_id, empresa_id,
        )

        # 7. Falha de webhook NÃO pode derrubar a contratação: o canal já é
        #    válido, e o provedor pode estar momentaneamente fora.
        try:
            self._configurar_webhook(canal)
        except Exception as e:
            logger.warning("Webhook não configurado para o canal %s: %s", canal.id, e)

        return canal

    def buscar_por_id(
        self, canal_id: int, empresa_id: int, incluir_excluidos: bool = False
    ) -> CanalContratado:
        """
        Busca o canal pela empresa.

        O filtro por `empresa_id` faz o isolamento: um canal de outra empresa
        simplesmente não é encontrado, e a mensagem de erro não diz se ele
        existe — não entrega informação de outro tenant.

        `incluir_excluidos` existe para o `restaurar_canal`: um canal que já
        foi soft-deletado SOME deste método por padrão, então restaurá-lo
        exigiria um caminho que o ignorasse esse filtro. Passar o parâmetro é
        mais explícito do que criar uma segunda query quase igual.
        """
        query = self.db.query(CanalContratado).filter(
            CanalContratado.id == canal_id,
            CanalContratado.empresa_id == empresa_id,
        )
        if not incluir_excluidos:
            query = query.filter(CanalContratado.deleted_at.is_(None))

        canal = query.first()
        if not canal:
            raise CanalNaoEncontradoError(
                f"Canal {canal_id} não encontrado ou você não tem permissão"
            )
        return canal

    def listar_canais(
        self,
        empresa_id: int,
        page: int = 1,
        limit: int = 50,
        tipo: Optional[str] = None,
        ativo: Optional[bool] = None,
        telefone_id: Optional[int] = None,
    ) -> Tuple[List[CanalContratado], int]:
        """Lista os canais contratados da empresa, com filtros e paginação."""
        query = self.db.query(CanalContratado).filter(
            CanalContratado.empresa_id == empresa_id,
            CanalContratado.deleted_at.is_(None),
        )
        if tipo:
            query = query.filter(CanalContratado.tipo == tipo)
        if ativo is not None:
            query = query.filter(CanalContratado.ativo == ativo)
        if telefone_id is not None:
            query = query.filter(CanalContratado.telefone_id == telefone_id)

        total = query.count()
        offset = max(page - 1, 0) * limit
        canais = (
            query.order_by(CanalContratado.criado_em.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return canais, total

    def atualizar_canal(
        self, canal_id: int, empresa_id: int, data: CanalContratadoUpdate
    ) -> CanalContratado:
        """Atualização parcial do canal, revalidando as regras afetadas."""
        canal = self.buscar_por_id(canal_id, empresa_id)
        mudancas = data.model_dump(exclude_unset=True)
        if not mudancas:
            return canal

        if "telefone_id" in mudancas or "tipo" in mudancas:
            novo_telefone = mudancas.get("telefone_id", canal.telefone_id)
            novo_tipo = mudancas.get("tipo", canal.tipo)
            if novo_telefone != canal.telefone_id:
                self._validar_telefone(novo_telefone, empresa_id)
            if (novo_telefone, novo_tipo) != (canal.telefone_id, canal.tipo):
                self._validar_tipo_por_telefone(novo_telefone, novo_tipo, exclude_id=canal_id)
            if "tipo" in mudancas:
                self._validar_tipo_canal(novo_tipo)

        if mudancas.get("apelido") and mudancas["apelido"] != canal.apelido:
            self._validar_apelido_unico(mudancas["apelido"], empresa_id, exclude_id=canal_id)

        if "credenciais" in mudancas and mudancas["credenciais"] is not None:
            # Mescla: um update parcial de credenciais não pode apagar as
            # chaves que o frontend não mandou.
            merged = self._credenciais(canal)
            merged.update(mudancas["credenciais"])
            canal.credenciais = self._serializar_credenciais(merged)
            mudancas.pop("credenciais")

        for chave, valor in mudancas.items():
            setattr(canal, chave, valor)

        self.db.commit()
        self.db.refresh(canal)
        logger.info("Canal atualizado: ID=%s", canal.id)
        return canal

    def deletar_canal(self, canal_id: int, empresa_id: int) -> bool:
        """
        Soft delete do canal.

        NÃO é apagar físico: o canal é a origem do histórico de atendimento.
        Se o canal sumisse, as conversas antigas ficariam sem procedência.
        Se houver atendimento em aberto, nem o soft delete é aceito.
        """
        canal = self.buscar_por_id(canal_id, empresa_id)

        abertos = (
            self.db.query(Atendimento)
            .filter(
                Atendimento.canal_contratado_id == canal_id,
                Atendimento.status.in_(STATUS_ABERTOS),
                Atendimento.deleted_at.is_(None),
            )
            .count()
        )
        if abertos > 0:
            raise RecursoInvalidoError(
                f"Não é possível desativar o canal: há {abertos} atendimento(s) em aberto"
            )

        canal.soft_delete()
        canal.ativo = False
        self.db.commit()

        logger.info("Canal desativado (soft delete): ID=%s", canal_id)
        return True

    def restaurar_canal(self, canal_id: int, empresa_id: int) -> CanalContratado:
        """Desfaz o soft delete e reativa o canal."""
        canal = self.buscar_por_id(canal_id, empresa_id, incluir_excluidos=True)
        canal.restore()
        canal.ativo = True
        self.db.commit()
        self.db.refresh(canal)
        return canal

    # ==============================================================================
    # VALIDAÇÕES
    # ==============================================================================
    def _validar_telefone(self, telefone_id: int, empresa_id: int) -> Telefone:
        """
        Valida que o telefone existe, está ativo e é da mesma empresa.

        É aqui que se fecha o isolamento do canal: sem esta checagem, uma
        empresa poderia contratar um canal em cima do número de outra.
        """
        telefone = (
            self.db.query(Telefone)
            .filter(
                Telefone.id == telefone_id,
                Telefone.empresa_id == empresa_id,
                Telefone.deleted_at.is_(None),
            )
            .first()
        )
        if not telefone:
            raise RecursoInvalidoError(
                f"Telefone {telefone_id} não encontrado para esta empresa"
            )
        if not telefone.ativo:
            raise RecursoInvalidoError(
                f"Telefone {telefone.numero} está inativo e não pode sustentar um canal"
            )
        return telefone

    def _validar_tipo_por_telefone(
        self, telefone_id: int, tipo: str, exclude_id: Optional[int] = None
    ) -> None:
        """
        Garante UM TIPO por telefone.

        É a regra que define a contratação: um WhatsApp por número. Para ter
        um segundo WhatsApp, a empresa cadastra um segundo telefone — e a
        mensalidade é duplicada, que é exatamente como um plano por número
        funciona.
        """
        query = self.db.query(CanalContratado).filter(
            CanalContratado.telefone_id == telefone_id,
            CanalContratado.tipo == tipo,
            CanalContratado.deleted_at.is_(None),
        )
        if exclude_id:
            query = query.filter(CanalContratado.id != exclude_id)
        if query.first():
            raise CanalTipoInvalidoError(
                f"Este telefone já possui um canal do tipo '{tipo}'. "
                "Cada tipo de canal só pode existir uma vez por telefone."
            )

    def _validar_apelido_unico(
        self, apelido: str, empresa_id: int, exclude_id: Optional[int] = None
    ) -> None:
        """Apelido único na empresa — evita dois canais iguais na tela."""
        query = self.db.query(CanalContratado).filter(
            CanalContratado.empresa_id == empresa_id,
            func.lower(CanalContratado.apelido) == apelido.lower().strip(),
            CanalContratado.deleted_at.is_(None),
        )
        if exclude_id:
            query = query.filter(CanalContratado.id != exclude_id)
        if query.first():
            raise CanalNomeDuplicadoError(
                f"Já existe um canal com o nome '{apelido}' para esta empresa"
            )

    def _validar_tipo_canal(self, tipo: str) -> None:
        """Valida se o tipo de canal é suportado."""
        tipos_validos = list(CHAVE_IDENTIFICADOR.keys()) + [
            "pabx", "voip_telefonia", "chat_web",
        ]
        if tipo not in tipos_validos:
            raise CanalTipoInvalidoError(
                f"Tipo de canal '{tipo}' não é suportado. "
                f"Tipos válidos: {', '.join(sorted(tipos_validos))}"
            )

    # ==============================================================================
    # WEBHOOKS
    # ==============================================================================
    def _url_publica(self) -> str:
        return os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000").rstrip("/")

    def _configurar_webhook(self, canal: CanalContratado) -> bool:
        """
        Registra o webhook do canal na API do provedor.

        A URL carrega o `webhook_token`: é ele que permite ao backend
        recusar webhook de origem desconhecida, em vez de acreditar em
        qualquer POST que chegue.
        """
        if canal.tipo in ("pabx", "voip_telefonia", "email", "chat_web"):
            logger.debug("Webhook não aplicável ao tipo %s", canal.tipo)
            return True

        url = f"{self._url_publica()}/api/webhook/{canal.tipo}/{canal.id}"
        url = f"{url}?token={canal.webhook_token}" if canal.webhook_token else url

        try:
            if canal.tipo == "telegram":
                return self._configurar_webhook_telegram(canal, url)
            if canal.tipo == "whatsapp":
                return self._configurar_webhook_whatsapp(canal, url)
            if canal.tipo in ("instagram", "facebook"):
                return self._configurar_webhook_meta(canal, url)
            if canal.tipo == "discord":
                return self._configurar_webhook_discord(canal, url)
            return True
        except Exception as e:
            logger.error("Erro ao configurar webhook do canal %s: %s", canal.id, e)
            return False

    def _configurar_webhook_telegram(self, canal: CanalContratado, webhook_url: str) -> bool:
        """setWebhook do Telegram Bot API."""
        import httpx

        token = self._credencial(canal, "bot_token")
        if not token:
            logger.warning("Canal Telegram %s sem bot_token em credenciais", canal.id)
            return False

        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(
                    f"https://api.telegram.org/bot{token}/setWebhook",
                    json={"url": webhook_url, "allowed_updates": ["message", "callback_query"]},
                )
                resp.raise_for_status()
            canal.webhook_url = webhook_url
            self.db.commit()
            logger.info("Webhook Telegram configurado: canal=%s", canal.id)
            return True
        except httpx.HTTPError as e:
            logger.error("Webhook Telegram falhou (canal %s): %s", canal.id, e)
            return False

    def _configurar_webhook_whatsapp(self, canal: CanalContratado, webhook_url: str) -> bool:
        """
        WhatsApp depende de duas credenciais: o ID do número de telefone
        (`phone_number_id`) e o token da conta (`access_token`). Sem as duas,
        a Meta recusa — por isso a validação é explícita.
        """
        import httpx

        phone_number_id = self._credencial(canal, "phone_number_id")
        access_token = self._credencial(canal, "access_token")
        if not phone_number_id or not access_token:
            logger.warning(
                "Canal WhatsApp %s sem phone_number_id/access_token em credenciais", canal.id
            )
            return False

        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(
                    f"https://graph.facebook.com/v19.0/{phone_number_id}/subscribed_apps",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                resp.raise_for_status()
            canal.webhook_url = webhook_url
            self.db.commit()
            logger.info("Webhook WhatsApp configurado: canal=%s", canal.id)
            return True
        except httpx.HTTPError as e:
            logger.error("Webhook WhatsApp falhou (canal %s): %s", canal.id, e)
            return False

    def _configurar_webhook_meta(self, canal: CanalContratado, webhook_url: str) -> bool:
        """Instagram/Facebook pela Meta Graph API."""
        import httpx

        page_id = self._credencial(canal, "page_id")
        access_token = self._credencial(canal, "access_token")
        if not page_id or not access_token:
            logger.warning("Canal Meta %s sem page_id/access_token", canal.id)
            return False

        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(
                    f"https://graph.facebook.com/v19.0/{page_id}/subscribed_apps",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                resp.raise_for_status()
            canal.webhook_url = webhook_url
            self.db.commit()
            logger.info("Webhook Meta configurado: canal=%s", canal.id)
            return True
        except httpx.HTTPError as e:
            logger.error("Webhook Meta falhou (canal %s): %s", canal.id, e)
            return False

    def _configurar_webhook_discord(self, canal: CanalContratado, webhook_url: str) -> bool:
        """Discord:_channels_webhook."""
        import httpx

        token = self._credencial(canal, "bot_token")
        guild_id = self._credencial(canal, "guild_id")
        channel_id = self._credencial(canal, "discord_channel_id")
        if not (token and guild_id and channel_id):
            logger.warning("Canal Discord %s sem bot_token/guild_id/channel_id", canal.id)
            return False

        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(
                    f"https://discord.com/api/v10/guilds/{guild_id}/channels/{channel_id}",
                    headers={"Authorization": f"Bot {token}"},
                    json={"type": 0, "name": "atendimento"},
                )
                resp.raise_for_status()
            canal.webhook_url = webhook_url
            self.db.commit()
            logger.info("Webhook Discord configurado: canal=%s", canal.id)
            return True
        except httpx.HTTPError as e:
            logger.error("Webhook Discord falhou (canal %s): %s", canal.id, e)
            return False

    # ==============================================================================
    # MÉTRICAS
    # ==============================================================================
    def obter_metricas_canal(self, canal_id: int, empresa_id: int) -> Dict[str, Any]:
        """
        Métricas do canal para o dashboard.

        Sobre "mensagens": o repositório não tem log de mensagens em SQL — as
        mensagens ficam no MongoDB. Não existe fonte confiável aqui para
        contá-las, então os campos de mensagem são PROXY de atendimento e estão
        nomeados como tal no dicionário (`atendimentos_hoje`,
        `atendimentos_com_atendente`). Se o Mongo passar a ser consultado aqui,
        estes campos devem ser trocados pela contagem real.

        O tempo de resposta é REAL: sai de `primeira_resposta_em`.
        """
        canal = self.buscar_por_id(canal_id, empresa_id)
        hoje = datetime.now(timezone.utc).date()

        atendimentos_hoje = (
            self.db.query(func.count(Atendimento.id))
            .filter(
                Atendimento.canal_contratado_id == canal_id,
                func.date(Atendimento.criado_em) == hoje,
                Atendimento.deleted_at.is_(None),
            )
            .scalar()
            or 0
        )

        atendimentos_ativos = (
            self.db.query(func.count(Atendimento.id))
            .filter(
                Atendimento.canal_contratado_id == canal_id,
                Atendimento.status.in_(STATUS_ABERTOS),
                Atendimento.deleted_at.is_(None),
            )
            .scalar()
            or 0
        )

        atendimentos_com_atendente = (
            self.db.query(func.count(Atendimento.id))
            .filter(
                Atendimento.canal_contratado_id == canal_id,
                func.date(Atendimento.criado_em) == hoje,
                Atendimento.atendente_id.isnot(None),
            )
            .scalar()
            or 0
        )

        # Tempo de primeira resposta: só dos atendimentos que JÁ responderam.
        respondidos = (
            self.db.query(Atendimento.iniciado_em, Atendimento.primeira_resposta_em)
            .filter(
                Atendimento.canal_contratado_id == canal_id,
                Atendimento.primeira_resposta_em.isnot(None),
                Atendimento.iniciado_em.isnot(None),
                Atendimento.deleted_at.is_(None),
            )
            .all()
        )
        if respondidos:
            segundos = [
                (r - i).total_seconds() for i, r in respondidos if r >= i
            ]
            tempo_medio_min = round(sum(segundos) / len(segundos) / 60, 2) if segundos else None
        else:
            tempo_medio_min = None

        return {
            "canal_id": canal.id,
            "canal_apelido": canal.apelido,
            "tipo": canal.tipo,
            "status": "ativo" if canal.ativo else "inativo",
            "atendimentos_hoje": atendimentos_hoje,
            "atendimentos_ativos": atendimentos_ativos,
            "atendimentos_com_atendente_hoje": atendimentos_com_atendente,
            "tempo_medio_primeira_resposta_min": tempo_medio_min,
            "proximo": (
                "Para contagem real de mensagens, consultar o MongoDB. "
                "Estes campos são contagem de atendimentos."
            ),
        }

    def contar_canais_por_tipo(self, empresa_id: int) -> Dict[str, int]:
        """Conta canais ativos por tipo — base do faturamento por canal."""
        resultados = (
            self.db.query(CanalContratado.tipo, func.count(CanalContratado.id))
            .filter(
                CanalContratado.empresa_id == empresa_id,
                CanalContratado.ativo.is_(True),
                CanalContratado.deleted_at.is_(None),
            )
            .group_by(CanalContratado.tipo)
            .all()
        )
        return {tipo: qtd for tipo, qtd in resultados}
