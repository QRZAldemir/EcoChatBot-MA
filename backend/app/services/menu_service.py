from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import Menu, MenuOpcao
from app.schemas import MenuCreate, MenuUpdate, MenuOpcaoCreate, MenuOpcaoUpdate
from typing import List, Optional

MAX_OPCOES_POR_MENU = 3


class MenuService:

    @staticmethod
    def _checar_titulo_duplicado(db: Session, titulo: str, ignorar_id: Optional[int] = None) -> None:
        query = db.query(Menu).filter(Menu.titulo == titulo)
        if ignorar_id is not None:
            query = query.filter(Menu.id != ignorar_id)
        if query.first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Já existe uma mensagem interativa com a descrição '{titulo}'")

    @staticmethod
    def listar_menus(db: Session, canal_id: Optional[int] = None, apenas_ativos: bool = False) -> List[Menu]:
        query = db.query(Menu)
        if canal_id is not None:
            query = query.filter(Menu.canal_id == canal_id)
        if apenas_ativos:
            query = query.filter(Menu.ativo == True)
        return query.all()

    @staticmethod
    def buscar_por_id(db: Session, menu_id: int) -> Optional[Menu]:
        return db.query(Menu).filter(Menu.id == menu_id).first()

    @staticmethod
    def criar_menu(db: Session, menu: MenuCreate) -> Menu:
        MenuService._checar_titulo_duplicado(db, menu.titulo)
        if len(menu.opcoes) > MAX_OPCOES_POR_MENU:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Máximo de {MAX_OPCOES_POR_MENU} opções por mensagem interativa")
        db_menu = Menu(
            titulo=menu.titulo,
            descricao=menu.descricao,
            cabecalho=menu.cabecalho,
            rodape=menu.rodape,
            texto_botao=menu.texto_botao,
            canal_id=menu.canal_id,
            usuario_vinculado_id=menu.usuario_vinculado_id,
            ativo=menu.ativo,
        )
        db.add(db_menu)
        db.flush()

        for opcao in menu.opcoes:
            db_opcao = MenuOpcao(
                menu_id=db_menu.id,
                titulo=opcao.titulo,
                descricao=opcao.descricao,
                row_id=opcao.row_id,
                ordem=opcao.ordem,
                cor=opcao.cor,
            )
            db.add(db_opcao)

        db.commit()
        db.refresh(db_menu)
        return db_menu

    @staticmethod
    def atualizar_menu(db: Session, menu_id: int, menu: MenuUpdate) -> Optional[Menu]:
        db_menu = db.query(Menu).filter(Menu.id == menu_id).first()
        if not db_menu:
            return None
        if menu.titulo is not None and menu.titulo != db_menu.titulo:
            MenuService._checar_titulo_duplicado(db, menu.titulo, ignorar_id=menu_id)

        dados = menu.model_dump(exclude_unset=True, exclude={"opcoes"})
        for campo, valor in dados.items():
            setattr(db_menu, campo, valor)

        if menu.opcoes is not None:
            if len(menu.opcoes) > MAX_OPCOES_POR_MENU:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Máximo de {MAX_OPCOES_POR_MENU} opções por mensagem interativa")
            MenuService._sincronizar_opcoes(db, db_menu, menu.opcoes)

        db.commit()
        db.refresh(db_menu)
        return db_menu

    @staticmethod
    def _sincronizar_opcoes(db: Session, db_menu: Menu, opcoes: List) -> None:
        """Aplica criação/atualização/remoção de opções na mesma transação do menu.

        Substitui o antigo fluxo de 3 chamadas HTTP separadas (criar/atualizar/deletar
        opção individualmente), que podia falhar no meio e deixar o menu com opções
        inconsistentes — aqui tudo é resolvido em memória e commitado de uma vez com
        o restante do menu.
        """
        existentes = {op.id: op for op in db_menu.opcoes}
        ids_enviados = {op.id for op in opcoes if op.id is not None}

        for opcao_id, db_opcao in existentes.items():
            if opcao_id not in ids_enviados:
                db.delete(db_opcao)

        for indice, opcao in enumerate(opcoes):
            if opcao.id is not None and opcao.id in existentes:
                db_opcao = existentes[opcao.id]
                db_opcao.titulo = opcao.titulo
                db_opcao.descricao = opcao.descricao
                db_opcao.row_id = opcao.row_id
                db_opcao.ordem = indice
                db_opcao.cor = opcao.cor
            else:
                db.add(MenuOpcao(
                    menu_id=db_menu.id,
                    titulo=opcao.titulo,
                    descricao=opcao.descricao,
                    row_id=opcao.row_id,
                    ordem=indice,
                    cor=opcao.cor,
                ))

    @staticmethod
    def deletar_menu(db: Session, menu_id: int) -> bool:
        db_menu = db.query(Menu).filter(Menu.id == menu_id).first()
        if not db_menu:
            return False
        db.delete(db_menu)
        db.commit()
        return True

    # ── Opções ──────────────────────────────────────────────

    @staticmethod
    def adicionar_opcao(db: Session, menu_id: int, opcao: MenuOpcaoCreate) -> Optional[MenuOpcao]:
        if not db.query(Menu).filter(Menu.id == menu_id).first():
            return None
        total_atual = db.query(MenuOpcao).filter(MenuOpcao.menu_id == menu_id).count()
        if total_atual >= MAX_OPCOES_POR_MENU:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Máximo de {MAX_OPCOES_POR_MENU} opções por mensagem interativa")
        db_opcao = MenuOpcao(
            menu_id=menu_id,
            titulo=opcao.titulo,
            descricao=opcao.descricao,
            row_id=opcao.row_id,
            ordem=opcao.ordem,
            cor=opcao.cor,
        )
        db.add(db_opcao)
        db.commit()
        db.refresh(db_opcao)
        return db_opcao

    @staticmethod
    def atualizar_opcao(db: Session, opcao_id: int, opcao: MenuOpcaoUpdate) -> Optional[MenuOpcao]:
        db_opcao = db.query(MenuOpcao).filter(MenuOpcao.id == opcao_id).first()
        if not db_opcao:
            return None
        for campo, valor in opcao.model_dump(exclude_unset=True).items():
            setattr(db_opcao, campo, valor)
        db.commit()
        db.refresh(db_opcao)
        return db_opcao

    @staticmethod
    def deletar_opcao(db: Session, opcao_id: int) -> bool:
        db_opcao = db.query(MenuOpcao).filter(MenuOpcao.id == opcao_id).first()
        if not db_opcao:
            return False
        db.delete(db_opcao)
        db.commit()
        return True
