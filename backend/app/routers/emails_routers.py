# ==============================================================================
# Arquivo: email.py (Pasta: app/routers)
#
# DESCRIÇÃO:
# Rotas da central de E-mail ("E-mail" na sidebar, ver docs/Barra Menu.png)
# — compõe/envia e-mails avulsos e mantém o histórico.
# ==============================================================================

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import EmailEnviarDTO, EmailResponse
from app.services.email_service import EmailService

router = APIRouter()


@router.get("/", response_model=List[EmailResponse])
def listar_emails(db: Session = Depends(get_db)):
    """Histórico de e-mails enviados."""
    return EmailService.listar(db)


@router.get("/{email_id}", response_model=EmailResponse)
def buscar_email(email_id: int, db: Session = Depends(get_db)):
    email = EmailService.buscar_por_id(db, email_id)
    if not email:
        raise HTTPException(status_code=404, detail="E-mail não encontrado")
    return email


@router.post("/", response_model=EmailResponse, status_code=201)
def enviar_email(dto: EmailEnviarDTO, db: Session = Depends(get_db)):
    """'Novo e-mail' — envia (ou simula, se SMTP não configurado) e registra no histórico."""
    return EmailService.enviar(db, dto)


@router.delete("/{email_id}", status_code=204)
def deletar_email(email_id: int, db: Session = Depends(get_db)):
    sucesso = EmailService.deletar(db, email_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="E-mail não encontrado")
    return None
