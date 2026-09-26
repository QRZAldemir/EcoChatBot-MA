"""
Testes do MenuService contra SQLite assíncrono.

O foco maior é o carregamento de `Menu.itens`: a relationship é `lazy="select"`,
e em sessão assíncrona tocar nela sem `await` levanta `MissingGreenlet`. Como o
`MenuResponse` do router serializa `itens`, todo método que devolve um `Menu`
precisa ter os itens já carregados — e isso só se prova executando de verdade.
"""
import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Departamento, Empresa, Menu
from app.schemas import (
    MenuCreate, MenuItemCreate, MenuItemUpdate, MenuItemUpsert, MenuUpdate,
)
from app.services.menu_service import MAX_ITENS_POR_MENU, MenuService


def _item(dep_id: int, titulo: str = "Falar com o financeiro", **kw) -> MenuItemCreate:
    return MenuItemCreate(titulo=titulo, departamento_id=dep_id, **kw)


def _menu(nome: str = "Menu inicial", **kw) -> MenuCreate:
    return MenuCreate(nome=nome, criado_em="2026-01-01T00:00:00Z", **kw)


def _upsert(id: int | None, titulo: str, departamento_id: int) -> MenuItemUpsert:
    """Item no contrato de upsert — o mesmo de create, mais `id`.

    `id=None` significa item novo; com `id`, o serviço atualiza o existente.
    `MenuUpdate.itens` é `List[MenuItemUpsert]`, então um `MenuItemCreate`
    seria recusado pelo pydantic.
    """
    return MenuItemUpsert(id=id, titulo=titulo, departamento_id=departamento_id)


# ══════════════════════════════════════════════════════════════════════════════
# CRIAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

class TestCriarMenu:
    async def test_cria_menu_com_itens(
        self,
        db_session: AsyncSession,
        empresa: Empresa,
        departamento: Departamento,
    ):
        menu = await MenuService.criar_menu(
            db_session, empresa.id, _menu(itens=[_item(departamento.id, "Financeiro")])
        )
        assert menu.id is not None
        assert menu.empresa_id == empresa.id
        assert [i.titulo for i in menu.itens] == ["Financeiro"]

    async def test_itens_ja_vem_carregados(
        self,
        db_session: AsyncSession,
        empresa: Empresa,
        departamento: Departamento,
    ):
        """Regressão de `MissingGreenlet`.

        Se `itens` fosse lazy, a linha abaixo levantaria `MissingGreenlet` em
        sessão async — e o `MenuResponse` do router quebraria em produção.
        """
        menu = await MenuService.criar_menu(
            db_session, empresa.id, _menu(itens=[_item(departamento.id)])
        )
        # Acesso síncrono, sem await: tem que funcionar.
        assert len(menu.itens) == 1
        assert menu.itens[0].departamento_id == departamento.id

    async def test_limite_de_itens(
        self,
        db_session: AsyncSession,
        empresa: Empresa,
        departamento: Departamento,
    ):
        itens = [_item(departamento.id, f"Opcao {i}") for i in range(MAX_ITENS_POR_MENU + 1)]
        with pytest.raises(HTTPException) as erro:
            await MenuService.criar_menu(db_session, empresa.id, _menu(itens=itens))
        assert erro.value.status_code == 400

    async def test_permite_ate_o_limite(
        self,
        db_session: AsyncSession,
        empresa: Empresa,
        departamento: Departamento,
    ):
        itens = [_item(departamento.id, f"Opcao {i}") for i in range(MAX_ITENS_POR_MENU)]
        menu = await MenuService.criar_menu(db_session, empresa.id, _menu(itens=itens))
        assert len(menu.itens) == MAX_ITENS_POR_MENU


# ══════════════════════════════════════════════════════════════════════════════
# UNICIDADE DE NOME — REGRESSÃO DO BUG CORRIGIDO
# ══════════════════════════════════════════════════════════════════════════════

class TestUnicidadeDeNome:
    async def test_menu_principal_duplicado_e_barrado(
        self, db_session: AsyncSession, empresa: Empresa
    ):
        """Regressão: a checagem antes rodava só quando havia canal.

        Menu principal tem `canal_contratado_id IS NULL` e passava sem nenhuma
        validação, permitindo dois "Menu inicial" na mesma empresa.
        """
        await MenuService.criar_menu(db_session, empresa.id, _menu("Menu inicial"))
        with pytest.raises(HTTPException) as erro:
            await MenuService.criar_menu(db_session, empresa.id, _menu("Menu inicial"))
        assert erro.value.status_code == 409
        assert "menu principal" in erro.value.detail

    async def test_menu_principal_e_de_canal_nao_colidem(
        self, db_session: AsyncSession, empresa: Empresa
    ):
        """Mesmo nome em escopos diferentes é válido.

        O menu principal é o hub; o do canal é específico dele. Podem usar o
        mesmo texto.
        """
        await MenuService.criar_menu(db_session, empresa.id, _menu("Menu inicial"))
        canal = await MenuService.criar_menu(
            db_session, empresa.id, _menu("Menu inicial", canal_contratado_id=1)
        )
        assert canal.canal_contratado_id == 1

    async def test_duplicado_no_mesmo_canal_e_barrado(
        self, db_session: AsyncSession, empresa: Empresa
    ):
        await MenuService.criar_menu(
            db_session, empresa.id, _menu("Menu inicial", canal_contratado_id=7)
        )
        with pytest.raises(HTTPException) as erro:
            await MenuService.criar_menu(
                db_session, empresa.id, _menu("Menu inicial", canal_contratado_id=7)
            )
        assert erro.value.status_code == 409
        assert "neste canal" in erro.value.detail

    async def test_mesmo_nome_em_outra_empresa_e_permitido(
        self, db_session: AsyncSession, empresa: Empresa, outra_empresa: Empresa
    ):
        await MenuService.criar_menu(db_session, empresa.id, _menu("Menu inicial"))
        outro = await MenuService.criar_menu(db_session, outra_empresa.id, _menu("Menu inicial"))
        assert outro.empresa_id == outra_empresa.id

    async def test_renomear_para_nome_ocupado_e_barrado(
        self, db_session: AsyncSession, empresa: Empresa
    ):
        await MenuService.criar_menu(db_session, empresa.id, _menu("Menu inicial"))
        alvo = await MenuService.criar_menu(db_session, empresa.id, _menu("Menu de suporte"))
        with pytest.raises(HTTPException) as erro:
            await MenuService.atualizar_menu(
                db_session, empresa.id, alvo.id, MenuUpdate(nome="Menu inicial")
            )
        assert erro.value.status_code == 409

    async def test_renomear_para_o_proprio_nome_passa(
        self, db_session: AsyncSession, empresa: Empresa
    ):
        """`ignorar_id` precisa excluir o proprio menu da checagem."""
        menu = await MenuService.criar_menu(db_session, empresa.id, _menu("Menu inicial"))
        mesmo = await MenuService.atualizar_menu(
            db_session, empresa.id, menu.id, MenuUpdate(nome="Menu inicial")
        )
        # `MenuCreate`/`MenuUpdate` normalizam o nome para MAIUSCULAS, então o
        # valor persistido e o esperado sao "MENU INICIAL", nao "Menu inicial".
        assert mesmo.nome == "MENU INICIAL"


# ══════════════════════════════════════════════════════════════════════════════
# ISOLAMENTO
# ══════════════════════════════════════════════════════════════════════════════

class TestIsolamento:
    async def test_outra_empresa_nao_enxerga_o_menu(
        self, db_session: AsyncSession, empresa: Empresa, outra_empresa: Empresa
    ):
        menu = await MenuService.criar_menu(db_session, empresa.id, _menu())
        assert await MenuService.buscar_por_id(db_session, empresa.id, menu.id)
        assert await MenuService.buscar_por_id(db_session, outra_empresa.id, menu.id) is None

    async def test_listagem_respeita_tenant(
        self, db_session: AsyncSession, empresa: Empresa, outra_empresa: Empresa
    ):
        await MenuService.criar_menu(db_session, empresa.id, _menu("A"))
        await MenuService.criar_menu(db_session, outra_empresa.id, _menu("B"))
        menus = await MenuService.listar_menus(db_session, empresa.id)
        assert [m.nome for m in menus] == ["A"]

    async def test_listagem_carrega_itens(
        self,
        db_session: AsyncSession,
        empresa: Empresa,
        departamento: Departamento,
    ):
        """A listagem também precisa vir com itens, senão o router quebra."""
        await MenuService.criar_menu(
            db_session, empresa.id, _menu(itens=[_item(departamento.id)])
        )
        menus = await MenuService.listar_menus(db_session, empresa.id)
        assert len(menus[0].itens) == 1

    async def test_outra_empresa_nao_apaga(
        self, db_session: AsyncSession, empresa: Empresa, outra_empresa: Empresa
    ):
        menu = await MenuService.criar_menu(db_session, empresa.id, _menu())
        assert await MenuService.deletar_menu(db_session, outra_empresa.id, menu.id) is False
        assert await MenuService.buscar_por_id(db_session, empresa.id, menu.id)

    async def test_outra_empresa_nao_altera_item(
        self,
        db_session: AsyncSession,
        empresa: Empresa,
        outra_empresa: Empresa,
        departamento: Departamento,
    ):
        menu = await MenuService.criar_menu(
            db_session, empresa.id, _menu(itens=[_item(departamento.id, "Original")])
        )
        item = menu.itens[0]
        assert await MenuService.atualizar_item(
            db_session, outra_empresa.id, item.id, MenuItemUpdate(titulo="Sequestrado")
        ) is None
        assert item.titulo == "Original"


# ══════════════════════════════════════════════════════════════════════════════
# SINCRONIZAÇÃO DE ITENS
# ══════════════════════════════════════════════════════════════════════════════

class TestSincronizarItens:
    async def test_atualiza_renomeia_e_remove_na_mesma_transacao(
        self,
        db_session: AsyncSession,
        empresa: Empresa,
        departamento: Departamento,
    ):
        menu = await MenuService.criar_menu(
            db_session,
            empresa.id,
            _menu(itens=[_item(departamento.id, "A"), _item(departamento.id, "B")]),
        )
        a, b = menu.itens[0], menu.itens[1]

        atualizado = await MenuService.atualizar_menu(
            db_session,
            empresa.id,
            menu.id,
            MenuUpdate(
                itens=[
                    _upsert(id=a.id, titulo="A renomeado", departamento_id=departamento.id),
                    # `b` não vem na lista: deve ser removido
                ]
            ),
        )
        assert [i.titulo for i in atualizado.itens] == ["A renomeado"]

    async def test_item_novo_e_adicionado(
        self,
        db_session: AsyncSession,
        empresa: Empresa,
        departamento: Departamento,
    ):
        menu = await MenuService.criar_menu(db_session, empresa.id, _menu())
        atualizado = await MenuService.atualizar_menu(
            db_session, empresa.id, menu.id,
            MenuUpdate(itens=[_upsert(None, "Novo", departamento.id)]),
        )
        assert len(atualizado.itens) == 1

    async def test_ordem_reindexada(
        self,
        db_session: AsyncSession,
        empresa: Empresa,
        departamento: Departamento,
    ):
        menu = await MenuService.criar_menu(
            db_session,
            empresa.id,
            _menu(itens=[_item(departamento.id, "A"), _item(departamento.id, "B")]),
        )
        b, a = menu.itens[1], menu.itens[0]
        atualizado = await MenuService.atualizar_menu(
            db_session, empresa.id, menu.id,
            MenuUpdate(itens=[
                _upsert(id=b.id, titulo="B", departamento_id=departamento.id),
                _upsert(id=a.id, titulo="A", departamento_id=departamento.id),
            ]),
        )
        assert [i.titulo for i in atualizado.itens] == ["B", "A"]
        assert [i.ordem for i in atualizado.itens] == [0, 1]


# ══════════════════════════════════════════════════════════════════════════════
# ITENS AVULSOS
# ══════════════════════════════════════════════════════════════════════════════

class TestItensAvulsos:
    async def test_adiciona_item(
        self, db_session: AsyncSession, empresa: Empresa, departamento: Departamento
    ):
        menu = await MenuService.criar_menu(db_session, empresa.id, _menu())
        item = await MenuService.adicionar_item(
            db_session, empresa.id, menu.id, _item(departamento.id)
        )
        assert item.id is not None and item.menu_id == menu.id

    async def test_adicionar_respeita_limite(
        self, db_session: AsyncSession, empresa: Empresa, departamento: Departamento
    ):
        menu = await MenuService.criar_menu(
            db_session, empresa.id,
            _menu(itens=[_item(departamento.id, f"O{i}") for i in range(MAX_ITENS_POR_MENU)]),
        )
        with pytest.raises(HTTPException) as erro:
            await MenuService.adicionar_item(
                db_session, empresa.id, menu.id, _item(departamento.id, "Extra")
            )
        assert erro.value.status_code == 400

    async def test_item_orfao_de_menu_inexistente(
        self, db_session: AsyncSession, empresa: Empresa, departamento: Departamento
    ):
        assert await MenuService.adicionar_item(
            db_session, empresa.id, 999_999, _item(departamento.id)
        ) is None

    async def test_atualiza_e_apaga_item(
        self, db_session: AsyncSession, empresa: Empresa, departamento: Departamento
    ):
        menu = await MenuService.criar_menu(db_session, empresa.id, _menu())
        item = await MenuService.adicionar_item(
            db_session, empresa.id, menu.id, _item(departamento.id, "Antes")
        )
        await MenuService.atualizar_item(
            db_session, empresa.id, item.id, MenuItemUpdate(titulo="Depois")
        )
        assert item.titulo == "Depois"
        assert await MenuService.deletar_item(db_session, empresa.id, item.id) is True
        assert await MenuService.deletar_item(db_session, empresa.id, item.id) is False

    async def test_apagar_menu_remove_itens(
        self, db_session: AsyncSession, empresa: Empresa, departamento: Departamento
    ):
        """`cascade="all, delete-orphan"` precisa valer no async também."""
        menu = await MenuService.criar_menu(
            db_session, empresa.id, _menu(itens=[_item(departamento.id)])
        )
        assert await MenuService.deletar_menu(db_session, empresa.id, menu.id) is True
        assert await MenuService.buscar_por_id(db_session, empresa.id, menu.id) is None
