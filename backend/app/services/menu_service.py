"""Serviço de menus interativos (mensagem interativa + itens de ação).

Convertido para async (frente C): `AsyncSession` + `select()`.

CARGA DE RELACIONAMENTO
-----------------------
`Menu.itens` é `lazy="select"`. Em sessão assíncrona, tocar numa relationship
lazy fora de `await` levanta `MissingGreenlet` — e o `MenuResponse` do router
serializa `itens`. Por isso toda leitura que devolve um `Menu` usa
`selectinload(Menu.itens)`, que dispara um segundo SELECT em vez de um JOIN
(um JOIN multiplicaria as linhas do menu pelo número de itens).
"""

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Menu, MenuItem
from app.schemas import MenuCreate, MenuItemCreate, MenuItemUpdate, MenuUpdate
from typing import List, Optional

MAX_ITENS_POR_MENU = 3


class MenuService:

    # ── Leitura ───────────────────────────────────────────────

    @staticmethod
    async def _buscar_por_id(
        db: AsyncSession,
        empresa_id: int,
        menu_id: int,
        *,
        com_itens: bool = True,
        recarregar: bool = False,
    ) -> Optional[Menu]:
        """Busca um menu, opcionalmente com os itens já carregados.

        `recarregar=True` força `populate_existing`. Sem isso, um SELECT com
        `selectinload` sobre um relationship JÁ carregado na identity map não
        sobrescreve a coleção: o `order_by="MenuItem.ordem"` só valeria no
        primeiro load. Depois de `_sincronizar_itens` reordenar os itens, a
        coleção em memória continuaria na ordem antiga e o `MenuResponse`
        devolveria os itens fora de ordem.
        """
        query = select(Menu).where(Menu.id == menu_id, Menu.empresa_id == empresa_id)
        if com_itens:
            query = query.options(selectinload(Menu.itens))
        if recarregar:
            query = query.execution_options(populate_existing=True)
        resultado = await db.execute(query)
        return resultado.scalars().first()

    @staticmethod
    async def listar_menus(
        db: AsyncSession,
        empresa_id: int,
        canal_contratado_id: Optional[int] = None,
        apenas_ativos: bool = False,
    ) -> List[Menu]:
        query = select(Menu).where(Menu.empresa_id == empresa_id)
        if canal_contratado_id is not None:
            query = query.where(Menu.canal_contratado_id == canal_contratado_id)
        if apenas_ativos:
            query = query.where(Menu.ativo.is_(True))
        # Sem isto, o `MenuResponse` do router dispara lazy-load e quebra.
        resultado = await db.execute(query.options(selectinload(Menu.itens)))
        return list(resultado.scalars().all())

    @staticmethod
    async def buscar_por_id(db: AsyncSession, empresa_id: int, menu_id: int) -> Optional[Menu]:
        return await MenuService._buscar_por_id(db, empresa_id, menu_id)

    @staticmethod
    async def _buscar_item(
        db: AsyncSession, empresa_id: int, item_id: int
    ) -> Optional[MenuItem]:
        """Item escopado pela empresa, via o menu dono.

        Filtrar só por `MenuItem.id` deixaria o item de uma empresa visível
        para qualquer tenant que adivinhasse o id.
        """
        resultado = await db.execute(
            select(MenuItem)
            .join(Menu, Menu.id == MenuItem.menu_id)
            .where(MenuItem.id == item_id, Menu.empresa_id == empresa_id)
        )
        return resultado.scalars().first()

    # ── Regras ────────────────────────────────────────────────

    @staticmethod
    async def _checar_nome_duplicado(
        db: AsyncSession,
        nome: str,
        empresa_id: int,
        canal_contratado_id: Optional[int] = None,
        ignorar_id: Optional[int] = None,
    ) -> None:
        """Unicidade por (empresa, canal, nome) — não global, e não só com canal.

        Dois canais diferentes podem ter um menu chamado "Menu inicial"; o que
        não pode é o MESMO canal ter dois menus com o mesmo nome. A versão
        antiga comparava só o título e, depois da tenantização, barraria canais
        distintos que usam o mesmo texto.

        O filtro de canal é aplicado SEMPRE, inclusive quando é `None`: o menu
        principal (`canal_contratado_id IS NULL`) também precisa ser único, e
        precisa colidir só com outros menus principais. Antes desta conversão a
        checagem rodava apenas quando havia canal, o que deixava menu principal
        duplicado passar. Em SQLAlchemy, `== None` gera `IS NULL`, então o
        filtro behaves corretamente para o menu principal.
        """
        query = select(Menu).where(
            Menu.nome == nome,
            Menu.empresa_id == empresa_id,
            Menu.canal_contratado_id == canal_contratado_id,
        )
        if ignorar_id is not None:
            query = query.where(Menu.id != ignorar_id)
        resultado = await db.execute(query)
        if resultado.scalars().first():
            escopo = "neste canal" if canal_contratado_id else "como menu principal"
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Já existe uma mensagem interativa com o nome '{nome}' "
                    f"{escopo}"
                ),
            )

    @staticmethod
    def _novo_item(db_menu: Menu, item, ordem: int) -> MenuItem:
        """Constrói um MenuItem no contrato canônico.

        `row_id` virou `atalho`: é a chave curta que o canal devolve quando o
        usuário toca no item. `cor` foi REMOVIDO — não existe no modelo e o
        WhatsApp não aceita cor em botão de lista interativa; o valor era
        ignorado na entrega. `departamento_id` é obrigatório no modelo
        (ON DELETE RESTRICT): todo item precisa saber para onde encaminhar.
        """
        return MenuItem(
            menu_id=db_menu.id,
            departamento_id=item.departamento_id,
            roteiro_id=item.roteiro_id,
            titulo=item.titulo,
            descricao=item.descricao,
            atalho=item.atalho,
            transfere_direto=item.transfere_direto,
            ordem=ordem,
        )

    @staticmethod
    def _limitar_itens(itens) -> None:
        if len(itens) > MAX_ITENS_POR_MENU:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Máximo de {MAX_ITENS_POR_MENU} itens por mensagem interativa",
            )

    # ── Escrita ───────────────────────────────────────────────

    @staticmethod
    async def criar_menu(db: AsyncSession, empresa_id: int, menu: MenuCreate) -> Menu:
        await MenuService._checar_nome_duplicado(
            db, menu.nome, empresa_id, menu.canal_contratado_id
        )
        MenuService._limitar_itens(menu.itens)

        db_menu = Menu(
            empresa_id=empresa_id,
            nome=menu.nome,
            saudacao=menu.saudacao,
            rodape=menu.rodape,
            tempo_espera_seg=menu.tempo_espera_seg,
            tentativas_max=menu.tentativas_max,
            canal_contratado_id=menu.canal_contratado_id,
            fallback_departamento_id=menu.fallback_departamento_id,
            ativo=menu.ativo,
        )
        db.add(db_menu)
        # `flush` e não `commit`: os itens precisam do `menu_id`, que só existe
        # depois do INSERT, mas tudo deve entrar na MESMA transação.
        await db.flush()

        for indice, item in enumerate(menu.itens):
            db.add(MenuService._novo_item(db_menu, item, indice))

        await db.commit()
        return await MenuService._buscar_por_id(db, empresa_id, db_menu.id)

    @staticmethod
    async def atualizar_menu(
        db: AsyncSession, empresa_id: int, menu_id: int, menu: MenuUpdate
    ) -> Optional[Menu]:
        # `com_itens=True` porque `_sincronizar_itens` lê `db_menu.itens`.
        db_menu = await MenuService._buscar_por_id(db, empresa_id, menu_id, com_itens=True)
        if not db_menu:
            return None

        if menu.nome is not None and menu.nome != db_menu.nome:
            canal_id = menu.canal_contratado_id or db_menu.canal_contratado_id
            await MenuService._checar_nome_duplicado(
                db, menu.nome, empresa_id, canal_id, ignorar_id=menu_id
            )

        dados = menu.model_dump(exclude_unset=True, exclude={"itens"})
        for campo, valor in dados.items():
            setattr(db_menu, campo, valor)

        if menu.itens is not None:
            MenuService._limitar_itens(menu.itens)
            MenuService._sincronizar_itens(db_menu, menu.itens)

        await db.commit()
        # `recarregar=True`: a coleção em memória ainda está na ordem anterior a
        # `_sincronizar_itens`, e o banco é a fonte da verdade depois do commit.
        return await MenuService._buscar_por_id(
            db, empresa_id, menu_id, recarregar=True
        )

    @staticmethod
    def _sincronizar_itens(db_menu: Menu, itens: List) -> None:
        """Aplica criação/atualização/remoção de itens na mesma transação do menu.

        Substitui o antigo fluxo de 3 chamadas HTTP separadas (criar/atualizar/
        deletar item individualmente), que podia falhar no meio e deixar o menu
        com itens inconsistentes — aqui tudo é resolvido em memória e commitado
        de uma vez com o restante do menu.

        Não faz I/O: só `add`/`delete` na sessão, que são síncronos. Os itens já
        estão carregados pelo `selectinload` do chamador.
        """
        existentes = {it.id: it for it in db_menu.itens}
        ids_enviados = {it.id for it in itens if it.id is not None}

        for item_id, db_item in existentes.items():
            if item_id not in ids_enviados:
                db_menu.itens.remove(db_item)

        for indice, item in enumerate(itens):
            if item.id is not None and item.id in existentes:
                db_item = existentes[item.id]
                db_item.departamento_id = item.departamento_id
                db_item.roteiro_id = item.roteiro_id
                db_item.titulo = item.titulo
                db_item.descricao = item.descricao
                db_item.atalho = item.atalho
                db_item.transfere_direto = item.transfere_direto
                db_item.ordem = indice
            else:
                db_menu.itens.append(MenuService._novo_item(db_menu, item, indice))

    @staticmethod
    async def deletar_menu(db: AsyncSession, empresa_id: int, menu_id: int) -> bool:
        db_menu = await MenuService._buscar_por_id(db, empresa_id, menu_id, com_itens=False)
        if not db_menu:
            return False
        await db.delete(db_menu)
        await db.commit()
        return True

    # ── Itens ────────────────────────────────────────────────

    @staticmethod
    async def adicionar_item(
        db: AsyncSession, empresa_id: int, menu_id: int, item: MenuItemCreate
    ) -> Optional[MenuItem]:
        db_menu = await MenuService._buscar_por_id(db, empresa_id, menu_id, com_itens=False)
        if not db_menu:
            return None

        resultado = await db.execute(
            select(func.count()).select_from(MenuItem).where(MenuItem.menu_id == menu_id)
        )
        total_atual = resultado.scalar_one()
        if total_atual >= MAX_ITENS_POR_MENU:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Máximo de {MAX_ITENS_POR_MENU} itens por mensagem interativa",
            )

        db_item = MenuService._novo_item(db_menu, item, total_atual)
        db.add(db_item)
        await db.commit()
        await db.refresh(db_item)
        return db_item

    @staticmethod
    async def atualizar_item(
        db: AsyncSession, empresa_id: int, item_id: int, item: MenuItemUpdate
    ) -> Optional[MenuItem]:
        db_item = await MenuService._buscar_item(db, empresa_id, item_id)
        if not db_item:
            return None
        for campo, valor in item.model_dump(exclude_unset=True).items():
            setattr(db_item, campo, valor)
        await db.commit()
        await db.refresh(db_item)
        return db_item

    @staticmethod
    async def deletar_item(db: AsyncSession, empresa_id: int, item_id: int) -> bool:
        db_item = await MenuService._buscar_item(db, empresa_id, item_id)
        if not db_item:
            return False
        await db.delete(db_item)
        await db.commit()
        return True
