"""Serviço de menus interativos (mensagem interativa + itens de ação).

ATENÇÃO — defeito conhecido, ainda não corrigido:
os métodos recebem `db: Session` e usam `db.query(...)`, mas `app.database.get_db`
entrega `AsyncSession` (async-only). Estes métodos importam sem erro e falham em
tempo de execução com AttributeError. A conversão para `await db.execute(select(...))`
está na fila, junto com `menus_routers.py`, `atendimento_service.py` e `bot_service.py`,
que são o mesmo defeito. Não expor estas rotas em produção antes disso.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import Menu, MenuItem
from app.schemas import MenuCreate, MenuItemCreate, MenuItemUpdate, MenuUpdate
from typing import List, Optional

MAX_ITENS_POR_MENU = 3


class MenuService:

    @staticmethod
    def _checar_nome_duplicado(
        db: Session,
        nome: str,
        empresa_id: int,
        canal_contratado_id: Optional[int] = None,
        ignorar_id: Optional[int] = None,
    ) -> None:
        """Unicidade por CANAL, não global.

        Dois canais diferentes podem ter um menu chamado "Menu inicial"; o que
        não pode é o mesmo canal ter dois menus com o mesmo nome. A verificação
        antiga comparava só o título e, depois da tenantização, barraria canais
        distintos que usam o mesmo texto de menu.
        """
        query = db.query(Menu).filter(
            Menu.nome == nome, Menu.empresa_id == empresa_id
        )
        if canal_contratado_id is not None:
            query = query.filter(Menu.canal_contratado_id == canal_contratado_id)
        if ignorar_id is not None:
            query = query.filter(Menu.id != ignorar_id)
        if query.first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Já existe uma mensagem interativa com o nome '{nome}' neste canal",
            )

    @staticmethod
    def listar_menus(
        db: Session,
        empresa_id: int,
        canal_contratado_id: Optional[int] = None,
        apenas_ativos: bool = False,
    ) -> List[Menu]:
        query = db.query(Menu).filter(Menu.empresa_id == empresa_id)
        if canal_contratado_id is not None:
            query = query.filter(Menu.canal_contratado_id == canal_contratado_id)
        if apenas_ativos:
            query = query.filter(Menu.ativo == True)  # noqa: E712
        return query.all()

    @staticmethod
    def buscar_por_id(db: Session, empresa_id: int, menu_id: int) -> Optional[Menu]:
        return (
            db.query(Menu)
            .filter(Menu.id == menu_id, Menu.empresa_id == empresa_id)
            .first()
        )

    @staticmethod
    def _buscar_item(db: Session, empresa_id: int, item_id: int) -> Optional[MenuItem]:
        """Item escopado pela empresa, via o menu dono.

        Filtrar só por `MenuItem.id` deixaria o item de uma empresa visível
        para qualquer tenant que adivinhasse o id.
        """
        return (
            db.query(MenuItem)
            .join(Menu, Menu.id == MenuItem.menu_id)
            .filter(MenuItem.id == item_id, Menu.empresa_id == empresa_id)
            .first()
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
    def criar_menu(db: Session, empresa_id: int, menu: MenuCreate) -> Menu:
        if menu.canal_contratado_id is not None:
            MenuService._checar_nome_duplicado(
                db, menu.nome, empresa_id, menu.canal_contratado_id
            )
        if len(menu.itens) > MAX_ITENS_POR_MENU:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Máximo de {MAX_ITENS_POR_MENU} itens por mensagem interativa",
            )

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
        db.flush()

        for indice, item in enumerate(menu.itens):
            db.add(MenuService._novo_item(db_menu, item, indice))

        db.commit()
        db.refresh(db_menu)
        return db_menu

    @staticmethod
    def atualizar_menu(
        db: Session, empresa_id: int, menu_id: int, menu: MenuUpdate
    ) -> Optional[Menu]:
        db_menu = MenuService.buscar_por_id(db, empresa_id, menu_id)
        if not db_menu:
            return None

        if menu.nome is not None and menu.nome != db_menu.nome:
            canal_id = menu.canal_contratado_id or db_menu.canal_contratado_id
            MenuService._checar_nome_duplicado(
                db, menu.nome, empresa_id, canal_id, ignorar_id=menu_id
            )

        dados = menu.model_dump(exclude_unset=True, exclude={"itens"})
        for campo, valor in dados.items():
            setattr(db_menu, campo, valor)

        if menu.itens is not None:
            if len(menu.itens) > MAX_ITENS_POR_MENU:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Máximo de {MAX_ITENS_POR_MENU} itens por mensagem interativa",
                )
            MenuService._sincronizar_itens(db, db_menu, menu.itens)

        db.commit()
        db.refresh(db_menu)
        return db_menu

    @staticmethod
    def _sincronizar_itens(db: Session, db_menu: Menu, itens: List) -> None:
        """Aplica criação/atualização/remoção de itens na mesma transação do menu.

        Substitui o antigo fluxo de 3 chamadas HTTP separadas (criar/atualizar/
        deletar item individualmente), que podia falhar no meio e deixar o menu
        com itens inconsistentes — aqui tudo é resolvido em memória e commitado
        de uma vez com o restante do menu.
        """
        existentes = {it.id: it for it in db_menu.itens}
        ids_enviados = {it.id for it in itens if it.id is not None}

        for item_id, db_item in existentes.items():
            if item_id not in ids_enviados:
                db.delete(db_item)

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
                db.add(MenuService._novo_item(db_menu, item, indice))

    @staticmethod
    def deletar_menu(db: Session, empresa_id: int, menu_id: int) -> bool:
        db_menu = MenuService.buscar_por_id(db, empresa_id, menu_id)
        if not db_menu:
            return False
        db.delete(db_menu)
        db.commit()
        return True

    # ── Itens ────────────────────────────────────────────────

    @staticmethod
    def adicionar_item(
        db: Session, empresa_id: int, menu_id: int, item: MenuItemCreate
    ) -> Optional[MenuItem]:
        db_menu = MenuService.buscar_por_id(db, empresa_id, menu_id)
        if not db_menu:
            return None
        total_atual = (
            db.query(MenuItem).filter(MenuItem.menu_id == menu_id).count()
        )
        if total_atual >= MAX_ITENS_POR_MENU:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Máximo de {MAX_ITENS_POR_MENU} itens por mensagem interativa",
            )
        db_item = MenuService._novo_item(db_menu, item, total_atual)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    @staticmethod
    def atualizar_item(
        db: Session, empresa_id: int, item_id: int, item: MenuItemUpdate
    ) -> Optional[MenuItem]:
        db_item = MenuService._buscar_item(db, empresa_id, item_id)
        if not db_item:
            return None
        for campo, valor in item.model_dump(exclude_unset=True).items():
            setattr(db_item, campo, valor)
        db.commit()
        db.refresh(db_item)
        return db_item

    @staticmethod
    def deletar_item(db: Session, empresa_id: int, item_id: int) -> bool:
        db_item = MenuService._buscar_item(db, empresa_id, item_id)
        if not db_item:
            return False
        db.delete(db_item)
        db.commit()
        return True
