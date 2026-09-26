"""
===============================================================================
MÓDULO: app/services/contato_service.py
AUTOR: Aldemir Queiroz
DATA: 2026-09-26
VERSÃO: 3.0.0
OBJETIVO: Regras de negócio do CONTATO (a pessoa) e da sua IDENTIDADE POR CANAL.
PASTA: backend/app/services/
===============================================================================

O QUE MUDOU NESTA VERSÃO (3.0.0)
-------------------------------
    1. `Contato` deixou de ser "um telefone". É a PESSOA, e uma pessoa tem
       N identidades — uma por canal contratado. O serviço ganhou o par
       `Contato` + `ContatoCanal`, copiando o desenho do Chatwoot
       (Contact + ContactInbox) e do Evolution (identidade = remoteJid por
       instance).

    2. A unicidade mudou de lugar. Antes o banco garantia
       `UNIQUE(empresa, canal_tipo, canal_identificador)`, o que proibia a
       MESMA pessoa de estar em dois canais — exatamente o que uma empresa
       com WhatsApp E Telegram precisa. Agora a regra é
       `UNIQUE(canal_contratado_id, identificador)`: um número por canal, a
       mesma pessoa em quantos canais quiser.

    3. O Tenant passou a ser obrigatório e explícito. Antes
       `listar(db)` devolvia a agenda inteira; agora todo método exige
       `empresa_id` e filtra por ele. Sem isso, uma empresa veria a agenda da
       outra.

    4. `canal_tipo` e `canal_identificador` viraram ATALHO DE LEITURA. A
       fonte da verdade é `contato_canais`. Eles são mantidos em sincronia
       para o código legado e para relatórios, e podem ser nulos — um lead
       criado por campanha não tem canal nenhum.

    5. DELETAR é SOFT DELETE. O contato é a origem do histórico de
       atendimento; apagá-lo deixaria conversas órfãs.

    6. Tudo virou `async` com `AsyncSession`.

SEGURODANÇA
-----------
    • `contato_canais` NÃO tem `empresa_id`. Todo acesso a ela passa por um
      JOIN em `contatos`, e é esse JOIN que carrega o tenant. Sem ele, um
      `SELECT` sem filtro leria o identificador de qualquer empresa.
    • `buscar_por_id` filtra por `empresa_id` no MESMO WHERE do id. Consultar
      por id apenas devolveria 404 para contato de outra empresa, o que ainda
      é preferível a devolvê-lo — mas a checagem fica explícita e testável.
===============================================================================
"""
import logging
from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import (
    ContatoCanalDuplicadoError,
    ContatoNaoEncontradoError,
    RecursoInvalidoError,
)
from app.models import CanalContratado, Contato, ContatoCanal
from app.schemas import ContatoCanalCreate, ContatoCreate, ContatoUpdate

logger = logging.getLogger(__name__)


class ContatoService:
    """Regras de negócio do contato (pessoa) e de suas identidades por canal.

    Responsabilidades:
        - CRUD de contatos, com soft delete
        - Isolamento multi-tenant por `empresa_id`
        - Vínculo e desvinculo de identidades por canal
        - Resolução de uma mensagem recebida -> contato + empresa
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==========================================================================
    # LEITURA
    # ==========================================================================
    async def listar(
        self,
        empresa_id: int,
        page: int = 1,
        limit: int = 50,
        busca: Optional[str] = None,
        apenas_com_canal: bool = False,
    ) -> Tuple[List[Contato], int]:
        """Lista os contatos da empresa, com busca e paginação.

        `apenas_com_canal` filtra quem tem identidade vinculada — é o que a tela
        de conversas precisa, porque contato sem canal não recebe mensagem.
        """
        filtros = [
            Contato.empresa_id == empresa_id,
            Contato.deleted_at.is_(None),
        ]

        if busca:
            # ILIKE não existe no SQLite (usado nos testes). `func.lower` +
            # `like` com o termo já em minúsculas funciona nos dois.
            alvo = f"%{busca.strip().lower()}%"
            filtros.append(
                or_(
                    func.lower(Contato.nome).like(alvo),
                    func.lower(Contato.telefone).like(alvo),
                    func.lower(Contato.email).like(alvo),
                )
            )

        if apenas_com_canal:
            filtros.append(Contato.canais.any(ContatoCanal.deleted_at.is_(None)))

        total = await self.db.scalar(select(func.count(Contato.id)).where(*filtros))
        offset = max(page - 1, 0) * limit

        contatos = (
            (
                await self.db.execute(
                    select(Contato)
                    .where(*filtros)
                    # `selectinload` e obrigatorio: acesso lazy a `canais` em
                    # async dispara MissingGreenlet, porque o objeto foi
                    # construido numa sessao que ja saiu do contexto.
                    .options(selectinload(Contato.canais))
                    .order_by(Contato.criado_em.desc())
                    .offset(offset)
                    .limit(limit)
                )
            )
            .scalars()
            .unique()
            .all()
        )
        return list(contatos), total or 0

    async def buscar_por_id(self, contato_id: int, empresa_id: int) -> Contato:
        """Busca um contato da empresa. 404 se não existir ou for de outra."""
        contato = await self.db.scalar(
            select(Contato)
            .where(
                Contato.id == contato_id,
                Contato.empresa_id == empresa_id,
                Contato.deleted_at.is_(None),
            )
            .options(selectinload(Contato.canais))
        )
        if contato is None:
            raise ContatoNaoEncontradoError(contato_id)
        return contato

    # ==========================================================================
    # ESCRITA
    # ==========================================================================
    async def criar(self, dto: ContatoCreate, empresa_id: int) -> Contato:
        """Cria o contato e vincula os canais enviados no corpo.

        Os canais vêm junto porque contato sem `ContatoCanal` é invisível para
        o webhook: quando a mensagem chega, não há como saber a que contato
        ela pertence.
        """
        contato = Contato(
            nome=dto.nome,
            telefone=dto.telefone,
            email=dto.email,
            notas=dto.notas,
            tags=dto.tags,
            apelido=dto.apelido,
            canal_tipo=dto.canal_tipo,
            canal_identificador=dto.canal_identificador,
            empresa_id=empresa_id,
        )
        self.db.add(contato)
        await self.db.flush()

        for canal_dto in dto.canais:
            await self._vincular(contato, canal_dto, empresa_id)

        self._sincronizar_atalho(contato)
        await self.db.commit()
        await self.db.refresh(contato, ["canais"])

        logger.info(
            "Contato criado: ID=%s empresa=%s canais=%s",
            contato.id, empresa_id, len(contato.canais),
        )
        return contato

    async def atualizar(
        self, contato_id: int, dto: ContatoUpdate, empresa_id: int
    ) -> Contato:
        """Atualização parcial dos campos da pessoa.

        NÃO mexe em `canal_tipo`/`canal_identificador` aqui: esses dois são
        atalho de `contato_canais`, e mexer neles por fora deixaria o atalho
        mentindo. Para trocar de canal, use `vincular_canal`.
        """
        contato = await self.buscar_por_id(contato_id, empresa_id)

        dados = dto.model_dump(exclude_unset=True)
        for campo, valor in dados.items():
            setattr(contato, campo, valor)

        await self.db.commit()
        await self.db.refresh(contato, ["canais"])
        return contato

    async def deletar(self, contato_id: int, empresa_id: int) -> bool:
        """Soft delete do contato e das suas identidades.

        Apagar fisicamente o contato deixaria todo o histórico de atendimento
        apontando para um id que não existe mais.
        """
        contato = await self.buscar_por_id(contato_id, empresa_id)

        contato.soft_delete()
        for vinculo in contato.canais:
            vinculo.soft_delete()
        await self.db.commit()

        logger.info("Contato desativado (soft delete): ID=%s", contato_id)
        return True

    async def restaurar(self, contato_id: int, empresa_id: int) -> Contato:
        """Desfaz o soft delete, junto com as identidades."""
        contato = await self.db.scalar(
            select(Contato)
            .where(Contato.id == contato_id, Contato.empresa_id == empresa_id)
            .options(selectinload(Contato.canais))
        )
        if contato is None:
            raise ContatoNaoEncontradoError(contato_id)

        contato.restore()
        for vinculo in contato.canais:
            vinculo.restore()
        await self.db.commit()
        await self.db.refresh(contato, ["canais"])
        return contato

    # ==========================================================================
    # IDENTIDADE POR CANAL
    # ==========================================================================
    async def vincular_canal(
        self, contato_id: int, canal_dto: ContatoCanalCreate, empresa_id: int
    ) -> ContatoCanal:
        """Vincula uma identidade `(canal, identificador)` ao contato."""
        contato = await self.buscar_por_id(contato_id, empresa_id)
        vinculo = await self._vincular(contato, canal_dto, empresa_id)
        self._sincronizar_atalho(contato)
        await self.db.commit()
        await self.db.refresh(vinculo)
        return vinculo

    async def desvincular_canal(
        self, contato_id: int, vinculo_id: int, empresa_id: int
    ) -> bool:
        """Desvincula uma identidade. Soft delete, pelo mesmo motivo do contato."""
        contato = await self.buscar_por_id(contato_id, empresa_id)

        vinculo = next((c for c in contato.canais if c.id == vinculo_id), None)
        if vinculo is None:
            raise RecursoInvalidoError(
                f'A identidade {vinculo_id} não pertence ao contato {contato_id}'
            )

        vinculo.soft_delete()
        self._sincronizar_atalho(contato)
        await self.db.commit()
        return True

    async def resolver_por_identificador(
        self, canal_contratado_id: int, identificador: str
    ) -> Optional[Contato]:
        """Caminho do WEBHOOK: mensagem recebida -> contato.

        Não recebe `empresa_id` de propósito: quem chama é o webhook, que não
        tem sessão de usuário. O tenant é descoberto pelo próprio dado — o
        `JOIN` em `contatos` é o que garante que o contato devolvido é o
        dono daquele canal, e não o de outra empresa.

        Retorna `None` (e não levanta 404) porque "chegou mensagem de número
        desconhecido" é rotina no webhook, não erro.
        """
        return await self.db.scalar(
            select(Contato)
            .join(ContatoCanal, ContatoCanal.contato_id == Contato.id)
            .where(
                ContatoCanal.canal_contratado_id == canal_contratado_id,
                ContatoCanal.identificador == identificador,
                ContatoCanal.deleted_at.is_(None),
                Contato.deleted_at.is_(None),
            )
            # Canal inativo não deve receber mensagem nova: o webhook ignoraria
            # a entrega depois de gravar. Melhor nem resolver.
            .join(CanalContratado, CanalContratado.id == ContatoCanal.canal_contratado_id)
            .where(CanalContratado.deleted_at.is_(None), CanalContratado.ativo.is_(True))
        )

    # ==========================================================================
    # INTERNOS
    # ==========================================================================
    async def _vincular(
        self, contato: Contato, dto: ContatoCanalCreate, empresa_id: int
    ) -> ContatoCanal:
        """Cria a identidade, validando dono do canal e unicidade.

        Falha ANTES do commit, para o chamador receber 409/422 em vez de um
        `IntegrityError` estourando como 500.
        """
        # O canal TEM de ser desta empresa. Sem esta checagem, uma empresa
        # escreveria o identificador do contato dentro do canal da outra.
        canal = await self.db.scalar(
            select(CanalContratado).where(
                CanalContratado.id == dto.canal_contratado_id,
                CanalContratado.empresa_id == empresa_id,
                CanalContratado.deleted_at.is_(None),
            )
        )
        if canal is None:
            raise RecursoInvalidoError(
                f'Canal {dto.canal_contratado_id} não existe nesta empresa'
            )

        # Já existe identidade ativa com esse identificador NESTE canal?
        # Pode ser outro contato da mesma empresa — o que é conflictante — ou o
        # mesmo contato (idempotência). Nos dois casos devolvemos o existente
        # em vez de criar duplicata.
        existente = await self.db.scalar(
            select(ContatoCanal).where(
                ContatoCanal.canal_contratado_id == dto.canal_contratado_id,
                ContatoCanal.identificador == dto.identificador,
                ContatoCanal.deleted_at.is_(None),
            )
        )
        if existente is not None:
            if existente.contato_id == contato.id:
                if dto.push_name and existente.push_name != dto.push_name:
                    existente.push_name = dto.push_name
                return existente
            raise ContatoCanalDuplicadoError(
                identificador=dto.identificador,
                canal_contratado_id=dto.canal_contratado_id,
                detail=(
                    'O identificador já pertence a outro contato desta empresa. '
                    'Se é a mesma pessoa, use PUT /contatos/{id}/canais para '
                    'vincular o canal a este contato.'
                ),
            )

        vinculo = ContatoCanal(
            contato_id=contato.id,
            canal_contratado_id=dto.canal_contratado_id,
            identificador=dto.identificador,
            push_name=dto.push_name,
        )
        self.db.add(vinculo)
        try:
            await self.db.flush()
        except IntegrityError as exc:
            # Corre: a UNIQUE do banco é a última rede. Duas requisições
            # simultâneas passam ambas pelo SELECT acima; só uma vence aqui.
            await self.db.rollback()
            raise ContatoCanalDuplicadoError(
                identificador=dto.identificador,
                canal_contratado_id=dto.canal_contratado_id,
            ) from exc
        return vinculo

    @staticmethod
    def _sincronizar_atalho(contato: Contato) -> None:
        """Mantém `canal_tipo`/`canal_identificador` batendo com a identidade.

        Se houver mais de uma identidade, o atalho reflete a MENOR id — é
        arbitrário por construção, e o campo está documentado como atalho. Se
        não houver nenhuma, os dois vão a None (lead sem canal).
        """
        ativos = sorted(
            (c for c in contato.canais if not c.is_deleted()), key=lambda c: c.id
        )
        if not ativos:
            contato.canal_tipo = None
            contato.canal_identificador = None
            return
        primeiro = ativos[0]
        contato.canal_tipo = primeiro.canal_contratado.tipo if primeiro.canal_contratado else None
        contato.canal_identificador = primeiro.identificador
