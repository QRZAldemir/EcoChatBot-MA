from sqlalchemy.orm import Session
from app.models import Menu, MenuOpcao
from app.schemas import MenuCreate, MenuUpdate, MenuOpcaoCreate, MenuOpcaoUpdate
from typing import List, Optional


class MenuService:

    @staticmethod
    def listar_menus(db: Session, canal_id: Optional[int] = None, apenas_ativos: bool = False) -> List[Menu]:
        query = db.query(Menu)
        if canal_id:
            query = query.filter(Menu.canal_id == canal_id)
        if apenas_ativos:
            query = query.filter(Menu.ativo == True)
        return query.all()

    @staticmethod
    def buscar_por_id(db: Session, menu_id: int) -> Optional[Menu]:
        return db.query(Menu).filter(Menu.id == menu_id).first()

    @staticmethod
    def criar_menu(db: Session, menu: MenuCreate) -> Menu:
        db_menu = Menu(
            titulo=menu.titulo,
            descricao=menu.descricao,
            rodape=menu.rodape,
            texto_botao=menu.texto_botao,
            canal_id=menu.canal_id,
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
        for campo, valor in menu.model_dump(exclude_unset=True).items():
            setattr(db_menu, campo, valor)
        db.commit()
        db.refresh(db_menu)
        return db_menu

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
        db_opcao = MenuOpcao(
            menu_id=menu_id,
            titulo=opcao.titulo,
            descricao=opcao.descricao,
            row_id=opcao.row_id,
            ordem=opcao.ordem,
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
