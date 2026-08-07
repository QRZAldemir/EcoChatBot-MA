# ==============================================================================
# Autor: Aldemir Queiroz
# ==============================================================================
# Arquivo: conexao_service.py (Pasta: app/services)
#
# DESCRIÇÃO:
# Camada de serviço para o painel "Conexões" (docs/Painel de Controle com
# vinculo da empresa que contratou  o sistema.png) — gerencia os números
# WhatsApp (WABA) vinculados ao sistema via Evolution API.
#
# Toda chamada à Evolution API é protegida: se o servidor Evolution não
# estiver acessível (ambiente sem a integração ligada), o serviço não quebra
# — ele registra um aviso no log e devolve/aplica um resultado simulado
# (status "aguardando", QR Code ausente) para que a tela continue utilizável.
# Quando a Evolution API estiver de fato no ar, as mesmas chamadas passam a
# valer de verdade, sem precisar trocar nenhum código aqui.
# ==============================================================================

import logging
import uuid
from typing import List, Optional

import httpx
from sqlalchemy.orm import Session

from app.models import Atendimento, Conexao
from app.schemas import ConexaoCreate, ConexaoUpdate
from app.services import evolution_service

logger = logging.getLogger(__name__)


class ConexaoService:

    # ── Consulta ─────────────────────────────────────────────────────────

    @staticmethod
    def _com_metricas(db: Session, conexao: Conexao) -> Conexao:
        """Anexa a contagem de fila em memória (não persistida) ao registro."""
        conexao.fila = (
            db.query(Atendimento)
            .filter(Atendimento.conexao_id == conexao.id, Atendimento.status == "fila")
            .count()
        )
        # Sem um log de mensagens em tempo real na base atual, o "recebimento
        # por minuto" fica 0 até essa telemetria existir — evita exibir
        # número fictício.
        conexao.recebimento_min = 0
        return conexao

    @staticmethod
    def listar(db: Session) -> List[Conexao]:
        conexoes = db.query(Conexao).order_by(Conexao.criado_em.desc()).all()
        return [ConexaoService._com_metricas(db, c) for c in conexoes]

    @staticmethod
    def buscar_por_id(db: Session, conexao_id: int) -> Optional[Conexao]:
        conexao = db.query(Conexao).filter(Conexao.id == conexao_id).first()
        if conexao:
            ConexaoService._com_metricas(db, conexao)
        return conexao

    # ── CRUD ─────────────────────────────────────────────────────────────

    @staticmethod
    async def criar(db: Session, dto: ConexaoCreate) -> tuple[Conexao, Optional[dict]]:
        """Cria a conexão localmente e tenta abrir a instância + QR na Evolution API."""
        instance_name = f"{dto.nome.lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}"

        db_conexao = Conexao(
            nome=dto.nome,
            telefone=dto.telefone,
            tipo=dto.tipo,
            conexao=dto.conexao,
            atendimento=dto.atendimento,
            ativo=dto.ativo,
            status="aguardando",
            evolution_instance_name=instance_name,
        )
        db.add(db_conexao)
        db.commit()
        db.refresh(db_conexao)

        qrcode_info: Optional[dict] = None
        try:
            resultado = await evolution_service.criar_instancia(instance_name)
            qrcode_info = resultado.get("qrcode") or resultado
        except httpx.HTTPError as e:
            logger.warning(
                "conexao_service | criar | Evolution API indisponível, seguindo com QR simulado | %s", e
            )

        ConexaoService._com_metricas(db, db_conexao)
        return db_conexao, qrcode_info

    @staticmethod
    def atualizar(db: Session, conexao_id: int, dto: ConexaoUpdate) -> Optional[Conexao]:
        db_conexao = db.query(Conexao).filter(Conexao.id == conexao_id).first()
        if not db_conexao:
            return None

        for campo, valor in dto.model_dump(exclude_unset=True).items():
            setattr(db_conexao, campo, valor)

        db.commit()
        db.refresh(db_conexao)
        ConexaoService._com_metricas(db, db_conexao)
        return db_conexao

    @staticmethod
    async def deletar(db: Session, conexao_id: int) -> bool:
        db_conexao = db.query(Conexao).filter(Conexao.id == conexao_id).first()
        if not db_conexao:
            return False

        try:
            await evolution_service.deletar_instancia(db_conexao.evolution_instance_name)
        except httpx.HTTPError as e:
            logger.warning("conexao_service | deletar | Evolution API indisponível | %s", e)

        db.delete(db_conexao)
        db.commit()
        return True

    # ── Ações do painel ─────────────────────────────────────────────────

    @staticmethod
    async def atualizar_status(db: Session, conexao_id: int) -> Optional[Conexao]:
        """Botão 'Atualizar' — reconsulta o estado real da sessão na Evolution API."""
        db_conexao = db.query(Conexao).filter(Conexao.id == conexao_id).first()
        if not db_conexao:
            return None

        try:
            resultado = await evolution_service.verificar_conexao(db_conexao.evolution_instance_name)
            estado = (resultado.get("state") or resultado.get("instance", {}).get("state") or "").lower()
            if estado == "open":
                db_conexao.status = "conectada"
            elif estado in ("connecting", "qrcode"):
                db_conexao.status = "aguardando"
            elif estado:
                db_conexao.status = "desconectada"
            db.commit()
            db.refresh(db_conexao)
        except httpx.HTTPError as e:
            logger.warning("conexao_service | atualizar_status | Evolution API indisponível | %s", e)

        ConexaoService._com_metricas(db, db_conexao)
        return db_conexao

    @staticmethod
    async def desconectar(db: Session, conexao_id: int) -> Optional[Conexao]:
        db_conexao = db.query(Conexao).filter(Conexao.id == conexao_id).first()
        if not db_conexao:
            return None

        try:
            await evolution_service.desconectar_instancia(db_conexao.evolution_instance_name)
        except httpx.HTTPError as e:
            logger.warning("conexao_service | desconectar | Evolution API indisponível | %s", e)

        db_conexao.status = "desconectada"
        db.commit()
        db.refresh(db_conexao)
        ConexaoService._com_metricas(db, db_conexao)
        return db_conexao

    @staticmethod
    async def reconectar(db: Session, conexao_id: int) -> tuple[Optional[Conexao], Optional[dict]]:
        db_conexao = db.query(Conexao).filter(Conexao.id == conexao_id).first()
        if not db_conexao:
            return None, None

        qrcode_info: Optional[dict] = None
        try:
            await evolution_service.reiniciar_instancia(db_conexao.evolution_instance_name)
            resultado = await evolution_service.obter_qrcode(db_conexao.evolution_instance_name)
            qrcode_info = resultado
        except httpx.HTTPError as e:
            logger.warning("conexao_service | reconectar | Evolution API indisponível | %s", e)

        db_conexao.status = "aguardando"
        db.commit()
        db.refresh(db_conexao)
        ConexaoService._com_metricas(db, db_conexao)
        return db_conexao, qrcode_info

    @staticmethod
    def limpar_fila(db: Session, conexao_id: int) -> Optional[Conexao]:
        """Botão 'Limpar fila' — encerra os atendimentos em espera desta conexão."""
        db_conexao = db.query(Conexao).filter(Conexao.id == conexao_id).first()
        if not db_conexao:
            return None

        db.query(Atendimento).filter(
            Atendimento.conexao_id == conexao_id, Atendimento.status == "fila"
        ).update({"status": "finalizado"}, synchronize_session=False)
        db.commit()

        ConexaoService._com_metricas(db, db_conexao)
        return db_conexao

    @staticmethod
    def tornar_padrao(db: Session, conexao_id: int) -> Optional[Conexao]:
        """Marca esta conexão como o número administrativo principal da empresa."""
        db_conexao = db.query(Conexao).filter(Conexao.id == conexao_id).first()
        if not db_conexao:
            return None

        db.query(Conexao).filter(Conexao.id != conexao_id).update(
            {"padrao": False}, synchronize_session=False
        )
        db_conexao.padrao = True
        db.commit()
        db.refresh(db_conexao)
        ConexaoService._com_metricas(db, db_conexao)
        return db_conexao

    @staticmethod
    def alternar_ativo(db: Session, conexao_id: int) -> Optional[Conexao]:
        """Botão 'Desativar' / 'Ativar' — alterna se a conexão participa do atendimento."""
        db_conexao = db.query(Conexao).filter(Conexao.id == conexao_id).first()
        if not db_conexao:
            return None

        db_conexao.ativo = not db_conexao.ativo
        db.commit()
        db.refresh(db_conexao)
        ConexaoService._com_metricas(db, db_conexao)
        return db_conexao
