"""
===============================================================================
MÓDULO: app/services/departamento_service.py
AUTOR: Aldemir Queiroz
DATA: 2026-09-26
VERSÃO: 3.0.0
OBJETIVO: Regras de negócio do DEPARTAMENTO — quem atende o quê.
PASTA: backend/app/services/
===============================================================================

O QUE MUDOU NESTA VERSÃO (3.0.0)
-------------------------------
    1. `empresa_id` deixou de ser opcional. Antes o serviço aceitava criar
       departamento sem dono, e `listar_departamentos(db)` devolvia a lista
       inteira. O departamento é configuração de ROTEAMENTO do bot: ele decide
       qual fila recebe a mensagem. Sem tenant, uma empresa rotearia para a
       fila da outra.

    2. `departamento_id` NÃO vem mais do corpo da requisição. O frontend
       mandava um id no JSON e o serviço confiava nele — o que permitia criar
       um departamento apontando para o id de outra empresa. Agora vem do
       token, via `get_current_empresa`.

    3. DELETAR virou SOFT DELETE, e é recusado se houver item de menu ou
       usuário vinculado. Item de menu apontando para departamento sumido
       quebraria o roteamento na hora de atender.

    4. Tudo virou `async` com `AsyncSession`.

NOTA DE MODELO
--------------
    O model tem colunas que o schema ainda não expõe (`cor`, `horario_inicio`,
    `horario_fim`, `dias_semana`). Elas existem no banco e são lidas por
    relatórios; o CRUD de agora mantém o contrato antigo (`nome`,
    `descricao`, `ativo`) e não as exõe até o frontend precisar. Apagá-las do
    model seria o erro oposto.
===============================================================================
"""
import logging
from typing import List, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import DepartamentoEmUsoError, DepartamentoNaoEncontradoError
from app.models import Departamento, MenuItem, Usuario
from app.schemas import DepartamentoCreate, DepartamentoUpdate

logger = logging.getLogger(__name__)


class DepartamentoService:
    """Regras de negócio do departamento.

    Responsabilidades:
        - CRUD de departamentos, com soft delete
        - Isolamento multi-tenant por `empresa_id`
        - Recusa de desativação enquanto houver menu item ou usuário vinculado
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
        apenas_ativos: bool = False,
    ) -> Tuple[List[Departamento], int]:
        """Lista os departamentos da empresa, com paginação."""
        filtros = [
            Departamento.empresa_id == empresa_id,
            Departamento.deleted_at.is_(None),
        ]
        if apenas_ativos:
            filtros.append(Departamento.ativo.is_(True))

        total = await self.db.scalar(
            select(func.count(Departamento.id)).where(*filtros)
        )
        offset = max(page - 1, 0) * limit

        departamentos = (
            (
                await self.db.execute(
                    select(Departamento)
                    .where(*filtros)
                    .order_by(Departamento.nome.asc())
                    .offset(offset)
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )
        return list(departamentos), total or 0

    async def buscar_por_id(
        self, depto_id: int, empresa_id: int
    ) -> Departamento:
        """Busca um departamento da empresa. 404 se não existir ou for de outra."""
        departamento = await self.db.scalar(
            select(Departamento).where(
                Departamento.id == depto_id,
                Departamento.empresa_id == empresa_id,
                Departamento.deleted_at.is_(None),
            )
        )
        if departamento is None:
            raise DepartamentoNaoEncontradoError(depto_id)
        return departamento

    # ==========================================================================
    # ESCRITA
    # ==========================================================================
    async def criar(
        self, dto: DepartamentoCreate, empresa_id: int
    ) -> Departamento:
        """Cria o departamento no tenant do token.

        `empresa_id` NÃO é lido do DTO: `DepartamentoCreate` não tem o campo,
        e mesmo que tivesse o valor do corpo perderia para o do token.
        """
        existente = await self.db.scalar(
            select(Departamento).where(
                Departamento.empresa_id == empresa_id,
                func.lower(Departamento.nome) == dto.nome.strip().lower(),
                Departamento.deleted_at.is_(None),
            )
        )
        if existente is not None:
            raise DepartamentoEmUsoError(
                f'Já existe um departamento ativo chamado {dto.nome!r} nesta empresa'
            )

        departamento = Departamento(
            nome=dto.nome.strip(),
            descricao=dto.descricao,
            ativo=dto.ativo,
            empresa_id=empresa_id,
        )
        self.db.add(departamento)
        await self.db.commit()
        await self.db.refresh(departamento)

        logger.info("Departamento criado: ID=%s empresa=%s", departamento.id, empresa_id)
        return departamento

    async def atualizar(
        self, depto_id: int, dto: DepartamentoUpdate, empresa_id: int
    ) -> Departamento:
        """Atualização parcial. Renomear para um nome já usado é recusado."""
        departamento = await self.buscar_por_id(depto_id, empresa_id)

        dados = dto.model_dump(exclude_unset=True)

        if "nome" in dados and dados["nome"]:
            nome = dados["nome"].strip()
            conflito = await self.db.scalar(
                select(Departamento).where(
                    Departamento.empresa_id == empresa_id,
                    Departamento.id != depto_id,
                    func.lower(Departamento.nome) == nome.lower(),
                    Departamento.deleted_at.is_(None),
                )
            )
            if conflito is not None:
                raise DepartamentoEmUsoError(
                    f'Já existe um departamento ativo chamado {nome!r} nesta empresa'
                )
            dados["nome"] = nome

        for campo, valor in dados.items():
            setattr(departamento, campo, valor)

        await self.db.commit()
        await self.db.refresh(departamento)
        return departamento

    async def deletar(self, depto_id: int, empresa_id: int) -> bool:
        """Soft delete do departamento, recusado se algo ainda apontar para ele.

        Não é apagar físico: o departamento é a origem do histórico de
        atendimento e o destino do roteamento do menu.
        """
        departamento = await self.buscar_por_id(depto_id, empresa_id)

        itens = await self.db.scalar(
            select(func.count(MenuItem.id)).where(
                MenuItem.departamento_id == depto_id,
                MenuItem.deleted_at.is_(None),
            )
        )
        usuarios = await self.db.scalar(
            select(func.count(Usuario.id)).where(
                Usuario.departamento_id == depto_id,
                Usuario.deleted_at.is_(None),
            )
        )

        vinculados = (itens or 0) + (usuarios or 0)
        if vinculados > 0:
            raise DepartamentoEmUsoError(
                f'Não é possível desativar: {itens or 0} item(ns) de menu e '
                f'{usuarios or 0} usuário(s) ainda apontam para este departamento',
                detail='Reatribua os vínculos antes de desativar.',
            )

        departamento.soft_delete()
        departamento.ativo = False
        await self.db.commit()

        logger.info("Departamento desativado (soft delete): ID=%s", depto_id)
        return True
