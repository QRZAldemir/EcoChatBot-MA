"""Rotas de menus interativos.

Escopo de tenant: todo menu é filtrado por `empresa_id`, derivado do token do
usuário via `get_current_empresa`. Sem isso, um tenant que adivinhasse um
`menu_id` conseguiria ler, alterar e apagar o menu de outro.

ATENÇÃO — defeito conhecido, ainda não corrigido: as rotas e o
`menu_service` usam a API síncrona (`db: Session`, `db.query`) enquanto
`get_db` entrega `AsyncSession`. Importam sem erro e falham em tempo de
execução. Conversão para async está na fila, junto com os demais serviços.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.deps import get_current_empresa
from app.models import Empresa
from app.security import exigir_nivel, exigir_nivel_minimo
from app.services.menu_service import MenuService
from app.schemas import (
    MenuCreate, MenuItemCreate, MenuItemResponse, MenuItemUpdate,
    MenuResponse, MenuUpdate,
)

router = APIRouter()


# ── Menus ────────────────────────────────────────────────────

@router.get("/", response_model=List[MenuResponse])
def listar_menus(
    canal_contratado_id: Optional[int] = Query(None),
    apenas_ativos: bool = Query(False),
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa),
):
    return MenuService.listar_menus(
        db,
        empresa_id=empresa.id,
        canal_contratado_id=canal_contratado_id,
        apenas_ativos=apenas_ativos,
    )


@router.get("/{menu_id}", response_model=MenuResponse)
def buscar_menu(
    menu_id: int,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa),
):
    menu = MenuService.buscar_por_id(db, empresa_id=empresa.id, menu_id=menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu não encontrado")
    return menu


@router.post("/", response_model=MenuResponse, status_code=201, dependencies=[Depends(exigir_nivel_minimo("gerente"))])
def criar_menu(
    menu: MenuCreate,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa),
):
    return MenuService.criar_menu(db, empresa_id=empresa.id, menu=menu)


@router.put("/{menu_id}", response_model=MenuResponse, dependencies=[Depends(exigir_nivel_minimo("gerente"))])
def atualizar_menu(
    menu_id: int,
    menu: MenuUpdate,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa),
):
    atualizado = MenuService.atualizar_menu(
        db, empresa_id=empresa.id, menu_id=menu_id, menu=menu
    )
    if not atualizado:
        raise HTTPException(status_code=404, detail="Menu não encontrado")
    return atualizado


@router.delete("/{menu_id}", status_code=204, dependencies=[Depends(exigir_nivel("administrador"))])
def deletar_menu(
    menu_id: int,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa),
):
    if not MenuService.deletar_menu(db, empresa_id=empresa.id, menu_id=menu_id):
        raise HTTPException(status_code=404, detail="Menu não encontrado")


# ── Itens do menu ────────────────────────────────────────────

@router.post("/{menu_id}/itens", response_model=MenuItemResponse, status_code=201, dependencies=[Depends(exigir_nivel_minimo("gerente"))])
def adicionar_item(
    menu_id: int,
    item: MenuItemCreate,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa),
):
    criado = MenuService.adicionar_item(
        db, empresa_id=empresa.id, menu_id=menu_id, item=item
    )
    if not criado:
        raise HTTPException(status_code=404, detail="Menu não encontrado")
    return criado


@router.put("/itens/{item_id}", response_model=MenuItemResponse, dependencies=[Depends(exigir_nivel_minimo("gerente"))])
def atualizar_item(
    item_id: int,
    item: MenuItemUpdate,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa),
):
    atualizado = MenuService.atualizar_item(
        db, empresa_id=empresa.id, item_id=item_id, item=item
    )
    if not atualizado:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return atualizado


@router.delete("/itens/{item_id}", status_code=204, dependencies=[Depends(exigir_nivel("administrador"))])
def deletar_item(
    item_id: int,
    db: Session = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa),
):
    if not MenuService.deletar_item(db, empresa_id=empresa.id, item_id=item_id):
        raise HTTPException(status_code=404, detail="Item não encontrado")
