# ==============================================================================
# Arquivo: arquivo_service.py (Pasta: app/services)
#
# DESCRIÇÃO:
# Biblioteca de mídia do chat ("Arquivos" na sidebar, ver docs/Barra Menu.png)
# — imagens/PDFs/áudios trocados nos atendimentos, reutilizáveis em respostas
# futuras (ex: reenviar um folder em PDF sem precisar subir de novo).
#
# Os arquivos ficam em disco, em UPLOAD_DIR; só os metadados vão para o banco.
# ==============================================================================

import logging
import os
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models import Arquivo

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads/arquivos"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class ArquivoService:

    @staticmethod
    def listar(db: Session) -> List[Arquivo]:
        return db.query(Arquivo).order_by(Arquivo.criado_em.desc()).all()

    @staticmethod
    def buscar_por_id(db: Session, arquivo_id: int) -> Optional[Arquivo]:
        return db.query(Arquivo).filter(Arquivo.id == arquivo_id).first()

    @staticmethod
    async def salvar_upload(
        db: Session,
        upload: UploadFile,
        descricao: Optional[str],
        atendimento_id: Optional[int]
    ) -> Arquivo:
        extensao = Path(upload.filename or "").suffix
        nome_arquivo = f"{uuid.uuid4().hex}{extensao}"
        destino = UPLOAD_DIR / nome_arquivo

        conteudo = await upload.read()
        destino.write_bytes(conteudo)

        db_arquivo = Arquivo(
            nome_original=upload.filename or nome_arquivo,
            nome_arquivo=nome_arquivo,
            tipo_mime=upload.content_type,
            tamanho_bytes=len(conteudo),
            descricao=descricao,
            atendimento_id=atendimento_id,
        )
        db.add(db_arquivo)
        db.commit()
        db.refresh(db_arquivo)
        return db_arquivo

    @staticmethod
    def caminho_no_disco(arquivo: Arquivo) -> Path:
        return UPLOAD_DIR / arquivo.nome_arquivo

    @staticmethod
    def deletar(db: Session, arquivo_id: int) -> bool:
        db_arquivo = db.query(Arquivo).filter(Arquivo.id == arquivo_id).first()
        if not db_arquivo:
            return False

        caminho = ArquivoService.caminho_no_disco(db_arquivo)
        try:
            caminho.unlink(missing_ok=True)
        except OSError as e:
            logger.warning("arquivo_service | deletar | falha ao remover arquivo do disco | %s", e)

        db.delete(db_arquivo)
        db.commit()
        return True
