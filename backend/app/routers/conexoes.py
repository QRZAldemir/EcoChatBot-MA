# ==============================================================================
# Autor: Aldemir Queiroz
# ==============================================================================
# Arquivo: conexoes.py (Pasta: app/routers)
#
# DESCRIÇÃO:
# Rotas do painel "Conexões" — gerencia números WhatsApp (WABA) vinculados ao
# sistema via Evolution API. Ver docs/Painel de Controle com vinculo da
# empresa que contratou  o sistema.png para o desenho de referência.
# ==============================================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.services.conexao_service import ConexaoService
from app.schemas import (
    ConexaoCreate,
    ConexaoUpdate,
    ConexaoResponse,
    ConexaoQRCodeResponse,
)

router = APIRouter()


# ==============================================================================
# LEITURA / CONSULTA
# ==============================================================================

@router.get("/", response_model=List[ConexaoResponse])
def listar_conexoes(db: Session = Depends(get_db)):
    """Lista todas as conexões WhatsApp cadastradas ('Conexões cadastradas')."""
    return ConexaoService.listar(db)


@router.get("/{conexao_id}", response_model=ConexaoResponse)
def buscar_conexao(conexao_id: int, db: Session = Depends(get_db)):
    conexao = ConexaoService.buscar_por_id(db, conexao_id)
    if not conexao:
        raise HTTPException(status_code=404, detail="Conexão não encontrada")
    return conexao


# ==============================================================================
# CRIAÇÃO / EDIÇÃO / REMOÇÃO
# ==============================================================================

@router.post("/", response_model=ConexaoQRCodeResponse, status_code=201)
async def criar_conexao(dto: ConexaoCreate, db: Session = Depends(get_db)):
    """'+ Nova conexão' — cadastra o número e devolve o QR Code de pareamento."""
    conexao, qrcode_info = await ConexaoService.criar(db, dto)
    return _resposta_qrcode(conexao, qrcode_info)


@router.put("/{conexao_id}", response_model=ConexaoResponse)
def atualizar_conexao(conexao_id: int, dto: ConexaoUpdate, db: Session = Depends(get_db)):
    conexao = ConexaoService.atualizar(db, conexao_id, dto)
    if not conexao:
        raise HTTPException(status_code=404, detail="Conexão não encontrada")
    return conexao


@router.delete("/{conexao_id}", status_code=204)
async def deletar_conexao(conexao_id: int, db: Session = Depends(get_db)):
    sucesso = await ConexaoService.deletar(db, conexao_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Conexão não encontrada")
    return None


# ==============================================================================
# AÇÕES DO PAINEL DE CONTROLE
# ==============================================================================

@router.post("/{conexao_id}/atualizar", response_model=ConexaoResponse)
async def atualizar_status(conexao_id: int, db: Session = Depends(get_db)):
    conexao = await ConexaoService.atualizar_status(db, conexao_id)
    if not conexao:
        raise HTTPException(status_code=404, detail="Conexão não encontrada")
    return conexao


@router.post("/{conexao_id}/desconectar", response_model=ConexaoResponse)
async def desconectar(conexao_id: int, db: Session = Depends(get_db)):
    conexao = await ConexaoService.desconectar(db, conexao_id)
    if not conexao:
        raise HTTPException(status_code=404, detail="Conexão não encontrada")
    return conexao


@router.post("/{conexao_id}/reconectar", response_model=ConexaoQRCodeResponse)
async def reconectar(conexao_id: int, db: Session = Depends(get_db)):
    conexao, qrcode_info = await ConexaoService.reconectar(db, conexao_id)
    if not conexao:
        raise HTTPException(status_code=404, detail="Conexão não encontrada")
    return _resposta_qrcode(conexao, qrcode_info)


@router.post("/{conexao_id}/limpar-fila", response_model=ConexaoResponse)
def limpar_fila(conexao_id: int, db: Session = Depends(get_db)):
    conexao = ConexaoService.limpar_fila(db, conexao_id)
    if not conexao:
        raise HTTPException(status_code=404, detail="Conexão não encontrada")
    return conexao


@router.post("/{conexao_id}/tornar-padrao", response_model=ConexaoResponse)
def tornar_padrao(conexao_id: int, db: Session = Depends(get_db)):
    conexao = ConexaoService.tornar_padrao(db, conexao_id)
    if not conexao:
        raise HTTPException(status_code=404, detail="Conexão não encontrada")
    return conexao


@router.post("/{conexao_id}/alternar-ativo", response_model=ConexaoResponse)
def alternar_ativo(conexao_id: int, db: Session = Depends(get_db)):
    """Botão 'Desativar' (e 'Ativar' quando já desativada)."""
    conexao = ConexaoService.alternar_ativo(db, conexao_id)
    if not conexao:
        raise HTTPException(status_code=404, detail="Conexão não encontrada")
    return conexao


# ==============================================================================
# HELPERS
# ==============================================================================

def _resposta_qrcode(conexao, qrcode_info: dict | None) -> ConexaoQRCodeResponse:
    if qrcode_info:
        return ConexaoQRCodeResponse(
            conexao=conexao,
            qrcode_base64=qrcode_info.get("base64") or qrcode_info.get("qrcode"),
            pairing_code=qrcode_info.get("pairingCode") or qrcode_info.get("code"),
            simulado=False,
        )
    return ConexaoQRCodeResponse(
        conexao=conexao,
        simulado=True,
        mensagem="Evolution API indisponível neste ambiente — vincule o número quando a integração estiver ativa.",
    )
