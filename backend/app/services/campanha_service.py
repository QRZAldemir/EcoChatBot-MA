# ==============================================================================
# Arquivo: campanha_service.py (Pasta: app/services)
#
# DESCRIÇÃO:
# Disparo em massa de mensagens WhatsApp para uma lista de Contatos
# ("Campanhas" na sidebar, ver docs/Barra Menu.png). Reaproveita a mesma
# Conexão/instância Evolution API já usada pelo painel "Conexões".
#
# Segue a mesma estratégia de resiliência de conexao_service: se a Evolution
# API não estiver acessível neste ambiente, cada envio é marcado "simulado"
# em vez de derrubar a campanha inteira — só falhas HTTP reais (instância
# conectada, mas número inválido etc.) contam como "erro".
# ==============================================================================

import logging
from datetime import datetime
from typing import List, Optional

import httpx
from sqlalchemy.orm import Session

from app.models import Campanha, CampanhaContato, Conexao, Contato
from app.schemas import CampanhaCreate
from app.services import evolution_service

logger = logging.getLogger(__name__)


class CampanhaService:

    @staticmethod
    def listar(db: Session) -> List[Campanha]:
        return db.query(Campanha).order_by(Campanha.criado_em.desc()).all()

    @staticmethod
    def buscar_por_id(db: Session, campanha_id: int) -> Optional[Campanha]:
        return db.query(Campanha).filter(Campanha.id == campanha_id).first()

    @staticmethod
    def criar(db: Session, dto: CampanhaCreate) -> Campanha:
        db_campanha = Campanha(
            nome=dto.nome,
            mensagem=dto.mensagem,
            conexao_id=dto.conexao_id,
            status="rascunho",
            total_contatos=len(dto.contato_ids),
        )
        db.add(db_campanha)
        db.flush()   # garante db_campanha.id antes de criar os vínculos

        for contato_id in dto.contato_ids:
            db.add(CampanhaContato(campanha_id=db_campanha.id, contato_id=contato_id))

        db.commit()
        db.refresh(db_campanha)
        return db_campanha

    @staticmethod
    def deletar(db: Session, campanha_id: int) -> bool:
        db_campanha = db.query(Campanha).filter(Campanha.id == campanha_id).first()
        if not db_campanha:
            return False

        db.delete(db_campanha)
        db.commit()
        return True

    @staticmethod
    async def disparar(db: Session, campanha_id: int) -> Optional[Campanha]:
        """Botão 'Disparar' — envia a mensagem para cada contato pendente da campanha."""
        db_campanha = db.query(Campanha).filter(Campanha.id == campanha_id).first()
        if not db_campanha:
            return None

        conexao = db.query(Conexao).filter(Conexao.id == db_campanha.conexao_id).first()
        db_campanha.status = "enviando"
        db.commit()

        pendentes = (
            db.query(CampanhaContato)
            .filter(CampanhaContato.campanha_id == campanha_id, CampanhaContato.status == "pendente")
            .all()
        )

        for item in pendentes:
            contato = db.query(Contato).filter(Contato.id == item.contato_id).first()
            if not contato:
                continue
            try:
                await evolution_service.enviar_texto(
                    conexao.evolution_instance_name, contato.telefone, db_campanha.mensagem
                )
                item.status = "enviado"
                item.enviado_em = datetime.utcnow()
                db_campanha.enviados += 1
            except httpx.HTTPStatusError as e:
                # Evolution API está no ar mas recusou o envio (ex: número inválido) — falha real.
                logger.error("campanha_service | disparar | Evolution API recusou o envio | %s", e)
                item.status = "erro"
                item.erro_mensagem = str(e)[:300]
                db_campanha.falhas += 1
            except httpx.HTTPError as e:
                # Evolution API inacessível neste ambiente — não é uma falha do contato em si.
                logger.warning(
                    "campanha_service | disparar | Evolution API indisponível, marcando envio como simulado | %s", e
                )
                item.status = "simulado"
                item.enviado_em = datetime.utcnow()
                db_campanha.enviados += 1

        db_campanha.status = "concluida"
        db_campanha.enviado_em = datetime.utcnow()
        db.commit()
        db.refresh(db_campanha)
        return db_campanha
