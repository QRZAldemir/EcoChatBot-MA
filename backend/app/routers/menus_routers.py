"""Rotas de menus interativos.

Escopo de tenant: todo menu é filtrado por `empresa_id`, derivado do token do
usuário via `get_current_empresa`. Sem isso, um tenant que adivinhasse um
`menu_id` conseguiria ler, alterar e apagar o menu de outro.

Convertido para async (frente C): as 8 rotas e o `menu_service` agora usam
`AsyncSession` e `await`. Antes importavam sem erro e falhavam em tempo de
execução, porque `get_db` já entregava `AsyncSession`.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
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
async def listar_menus(
    canal_contratado_id: Optional[int] = Query(None),
    apenas_ativos: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa),
):
    return await MenuService.listar_menus(
        db,
        empresa_id=empresa.id,
        canal_contratado_id=canal_contratado_id,
        apenas_ativos=apenas_ativos,
    )


@router.get("/{menu_id}", response_model=MenuResponse)
async def buscar_menu(
    menu_id: int,
    db: AsyncSession = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa),
):
    menu = await MenuService.buscar_por_id(db, empresa_id=empresa.id, menu_id=menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu não encontrado")
    return menu


@router.post("/", response_model=MenuResponse, status_code=201, dependencies=[Depends(exigir_nivel_minimo("gerente"))])
async def criar_menu(
    menu: MenuCreate,
    db: AsyncSession = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa),
):
    return await MenuService.criar_menu(db, empresa_id=empresa.id, menu=menu)


@router.put("/{menu_id}", response_model=MenuResponse, dependencies=[Depends(exigir_nivel_minimo("gerente"))])
async def atualizar_menu(
    menu_id: int,
    menu: MenuUpdate,
    db: AsyncSession = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa),
):
    atualizado = await MenuService.atualizar_menu(
        db, empresa_id=empresa.id, menu_id=menu_id, menu=menu
    )
    if not atualizado:
        raise HTTPException(status_code=404, detail="Menu não encontrado")
    return atualizado


@router.delete("/{menu_id}", status_code=204, dependencies=[Depends(exigir_nivel("administrador"))])
async def deletar_menu(
    menu_id: int,
    db: AsyncSession = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa),
):
    if not await MenuService.deletar_menu(db, empresa_id=empresa.id, menu_id=menu_id):
        raise HTTPException(status_code=404, detail="Menu não encontrado")


# ── Itens do menu ────────────────────────────────────────────

@router.post("/{menu_id}/itens", response_model=MenuItemResponse, status_code=201, dependencies=[Depends(exigir_nivel_minimo("gerente"))])
async def adicionar_item(
    menu_id: int,
    item: MenuItemCreate,
    db: AsyncSession = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa),
):
    criado = await MenuService.adicionar_item(
        db, empresa_id=empresa.id, menu_id=menu_id, item=item
    )
    if not criado:
        raise HTTPException(status_code=404, detail="Menu não encontrado")
    return criado


@router.put("/itens/{item_id}", response_model=MenuItemResponse, dependencies=[Depends(exigir_nivel_minimo("gerente"))])
async def atualizar_item(
    item_id: int,
    item: MenuItemUpdate,
    db: AsyncSession = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa),
):
    atualizado = await MenuService.atualizar_item(
        db, empresa_id=empresa.id, item_id=item_id, item=item
    )
    if not atualizado:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return atualizado


@router.delete("/itens/{item_id}", status_code=204, dependencies=[Depends(exigir_nivel("administrador"))])
async def deletar_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    empresa: Empresa = Depends(get_current_empresa),
):
    if not await MenuService.deletar_item(db, empresa_id=empresa.id, item_id=item_id):
        raise HTTPException(status_code=404, detail="Item não encontrado")
