# ==============================================================================
# Arquivo: arquivos.py (Pasta: app/routers)
#
# DESCRIÇÃO:
# Rotas da biblioteca de mídia do chat ("Arquivos" na sidebar, ver
# docs/Barra Menu.png).
# ==============================================================================

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ArquivoResponse
from app.services.arquivo_service import ArquivoService

router = APIRouter()


@router.get("/", response_model=List[ArquivoResponse])
def listar_arquivos(db: Session = Depends(get_db)):
    return ArquivoService.listar(db)


@router.post("/", response_model=ArquivoResponse, status_code=201)
async def enviar_arquivo(
    arquivo: UploadFile = File(...),
    descricao: Optional[str] = Form(None),
    atendimento_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    """'+ Enviar arquivo' — grava o arquivo em disco e registra os metadados."""
    return await ArquivoService.salvar_upload(db, arquivo, descricao, atendimento_id)


@router.get("/{arquivo_id}/download")
def baixar_arquivo(arquivo_id: int, db: Session = Depends(get_db)):
    db_arquivo = ArquivoService.buscar_por_id(db, arquivo_id)
    if not db_arquivo:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    caminho = ArquivoService.caminho_no_disco(db_arquivo)
    if not caminho.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no disco")

    return FileResponse(
        path=caminho,
        filename=db_arquivo.nome_original,
        media_type=db_arquivo.tipo_mime or "application/octet-stream",
    )


@router.delete("/{arquivo_id}", status_code=204)
def deletar_arquivo(arquivo_id: int, db: Session = Depends(get_db)):
    sucesso = ArquivoService.deletar(db, arquivo_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return None
