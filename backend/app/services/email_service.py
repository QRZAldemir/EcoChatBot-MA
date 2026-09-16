# ==============================================================================
# Arquivo: email_service.py (Pasta: app/services)
#
# DESCRIÇÃO:
# Central de E-mail — envia e-mails avulsos e mantém o histórico ("E-mail" na
# sidebar, ver docs/Barra Menu.png).
#
# Mesma estratégia de resiliência usada em evolution_service/conexao_service:
# se o SMTP não estiver configurado neste ambiente (SMTP_HOST vazio), o envio
# não quebra — o registro é salvo com status "simulado" e um aviso vai para o
# log. Quando as credenciais SMTP reais forem configuradas no .env, o mesmo
# código passa a enviar de verdade.
# Armazena uploads de imagens e documentos no diretório configurado em `UPLOAD_DIR` com nomes únicos via UUID e persiste os metadados no banco
#
# Variáveis de ambiente:
#     SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, SMTP_USE_TLS
# ==============================================================================

import logging
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import EmailEnviado
from app.schemas import EmailEnviarDTO

logger = logging.getLogger(__name__)

SMTP_HOST     = os.getenv("SMTP_HOST", "")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM     = os.getenv("SMTP_FROM", SMTP_USER)
SMTP_USE_TLS  = os.getenv("SMTP_USE_TLS", "true").lower() == "true"


class EmailService:

    @staticmethod
    def listar(db: Session) -> List[EmailEnviado]:
        return db.query(EmailEnviado).order_by(EmailEnviado.criado_em.desc()).all()

    @staticmethod
    def buscar_por_id(db: Session, email_id: int) -> Optional[EmailEnviado]:
        return db.query(EmailEnviado).filter(EmailEnviado.id == email_id).first()

    @staticmethod
    def enviar(db: Session, dto: EmailEnviarDTO) -> EmailEnviado:
        db_email = EmailEnviado(
            contato_id=dto.contato_id,
            destinatario=dto.destinatario,
            assunto=dto.assunto,
            corpo=dto.corpo,
            status="pendente",
        )
        db.add(db_email)
        db.commit()
        db.refresh(db_email)

        if not SMTP_HOST:
            logger.warning(
                "email_service | enviar | SMTP_HOST não configurado, seguindo com envio simulado | destinatario=%s",
                dto.destinatario,
            )
            db_email.status = "simulado"
            db_email.enviado_em = datetime.utcnow()
            db.commit()
            db.refresh(db_email)
            return db_email

        try:
            EmailService._enviar_smtp(dto.destinatario, dto.assunto, dto.corpo)
            db_email.status = "enviado"
            db_email.enviado_em = datetime.utcnow()
        except (smtplib.SMTPException, OSError) as e:
            logger.error("email_service | enviar | falha SMTP | %s", e)
            db_email.status = "erro"
            db_email.erro_mensagem = str(e)[:300]

        db.commit()
        db.refresh(db_email)
        return db_email

    @staticmethod
    def _enviar_smtp(destinatario: str, assunto: str, corpo: str) -> None:
        msg = EmailMessage()
        msg["From"] = SMTP_FROM
        msg["To"] = destinatario
        msg["Subject"] = assunto
        msg.set_content(corpo)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            if SMTP_USE_TLS:
                server.starttls()
            if SMTP_USER:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

    @staticmethod
    def send_invite_email(
        db: Session,
        to: str,
        nome: str,
        senha: str,
        link: str = "",
    ) -> EmailEnviado:
        """Email de convite para novo usuário (primeiro acesso)."""
        corpo = (
            f"Olá {nome},\n\n"
            f"Você foi convidado para o EcoChatBot.\n"
            f"Sua senha temporária é: {senha}\n"
            f"Acesse: {link or 'https://seu-dominio.com.br/login'}\n\n"
            "Recomendamos trocar a senha no primeiro acesso."
        )
        return EmailService.enviar(
            db,
            EmailEnviarDTO(destinatario=to, assunto="Convite de acesso - EcoChatBot", corpo=corpo),
        )

    @staticmethod
    def send_welcome_email(
        db: Session,
        to: str,
        nome: str,
        senha: str,
    ) -> EmailEnviado:
        """Email de boas-vindas (usuário criado pelo admin)."""
        corpo = (
            f"Olá {nome},\n\n"
            f"Sua conta no EcoChatBot foi criada.\n"
            f"Sua senha temporária é: {senha}\n"
            f"Acesse: https://seu-dominio.com.br/login\n\n"
            "Recomendamos trocar a senha no primeiro acesso."
        )
        return EmailService.enviar(
            db,
            EmailEnviarDTO(destinatario=to, assunto="Bem-vindo(a) ao EcoChatBot", corpo=corpo),
        )

    @staticmethod
    def send_reset_password_email(
        db: Session,
        to: str,
        nome: str,
        link: str = "",
    ) -> EmailEnviado:
        """Email de recuperação de senha."""
        corpo = (
            f"Olá {nome},\n\n"
            f"Recebemos uma solicitação para redefinir sua senha.\n"
            f"Clique no link abaixo (válido por 24h):\n"
            f"{link or 'https://seu-dominio.com.br/reset-password'}\n\n"
            "Se você não solicitou, ignore este email."
        )
        return EmailService.enviar(
            db,
            EmailEnviarDTO(destinatario=to, assunto="Recuperação de senha - EcoChatBot", corpo=corpo),
        )

    @staticmethod
    def deletar(db: Session, email_id: int) -> bool:
        db_email = db.query(EmailEnviado).filter(EmailEnviado.id == email_id).first()
        if not db_email:
            return False

        db.delete(db_email)
        db.commit()
        return True
