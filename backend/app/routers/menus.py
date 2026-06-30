from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.services.menu_service import MenuService
from app.schemas import (
    MenuCreate, MenuUpdate, MenuResponse,
    MenuOpcaoCreate, MenuOpcaoUpdate, MenuOpcaoResponse,
)

router = APIRouter()

# ── Menus ────────────────────────────────────────────────────

@router.get("/", response_model=List[MenuResponse])
def listar_menus(
    canal_id: Optional[int] = Query(None),
    apenas_ativos: bool = Query(False),
    db: Session = Depends(get_db),
):
    return MenuService.listar_menus(db, canal_id=canal_id, apenas_ativos=apenas_ativos)


@router.get("/{menu_id}", response_model=MenuResponse)
def buscar_menu(menu_id: int, db: Session = Depends(get_db)):
    menu = MenuService.buscar_por_id(db, menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu não encontrado")
    return menu


@router.post("/", response_model=MenuResponse, status_code=201)
def criar_menu(menu: MenuCreate, db: Session = Depends(get_db)):
    return MenuService.criar_menu(db, menu)


@router.put("/{menu_id}", response_model=MenuResponse)
def atualizar_menu(menu_id: int, menu: MenuUpdate, db: Session = Depends(get_db)):
    atualizado = MenuService.atualizar_menu(db, menu_id, menu)
    if not atualizado:
        raise HTTPException(status_code=404, detail="Menu não encontrado")
    return atualizado


@router.delete("/{menu_id}", status_code=204)
def deletar_menu(menu_id: int, db: Session = Depends(get_db)):
    if not MenuService.deletar_menu(db, menu_id):
        raise HTTPException(status_code=404, detail="Menu não encontrado")


# ── Opções do menu ───────────────────────────────────────────

@router.post("/{menu_id}/opcoes", response_model=MenuOpcaoResponse, status_code=201)
def adicionar_opcao(menu_id: int, opcao: MenuOpcaoCreate, db: Session = Depends(get_db)):
    criada = MenuService.adicionar_opcao(db, menu_id, opcao)
    if not criada:
        raise HTTPException(status_code=404, detail="Menu não encontrado")
    return criada


@router.put("/opcoes/{opcao_id}", response_model=MenuOpcaoResponse)
def atualizar_opcao(opcao_id: int, opcao: MenuOpcaoUpdate, db: Session = Depends(get_db)):
    atualizada = MenuService.atualizar_opcao(db, opcao_id, opcao)
    if not atualizada:
        raise HTTPException(status_code=404, detail="Opção não encontrada")
    return atualizada


@router.delete("/opcoes/{opcao_id}", status_code=204)
def deletar_opcao(opcao_id: int, db: Session = Depends(get_db)):
    if not MenuService.deletar_opcao(db, opcao_id):
        raise HTTPException(status_code=404, detail="Opção não encontrada")
