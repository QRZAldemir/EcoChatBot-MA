"""
================================================================================
MÓDULO: app/models/canal.py
AUTOR: Aldemir Queiroz
DATA: 2026-09-16
VERSÃO: 2.1.0 (Integração Cross-Channel PABX/IPVoIP)
OBJETIVO: Define o modelo de dados para canais de comunicação omnichannel.
          Suporta múltiplos canais por tenant (WhatsApp, Telegram, Instagram,
          Discord, VoIP, Email, etc.) com configurações específicas e 
          rastreamento de bilhetagem (CDR) para canais de telefonia.
PASTA: backend/app/models/
================================================================================
"""
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Canal(Base):
    """
    Representa um canal de comunicação vinculado a um tenant (empresa).
    
    Cada empresa pode ter múltiplos canais de diferentes tipos:
    - WhatsApp (via Evolution API ou Meta Cloud API)
    - Telegram (via Bot API)
    - Instagram (via Meta Graph API)
    - Facebook Messenger
    - Discord (via Bot API)
    - VoIP/Telefonia (Integração Agnóstica com PABX/IPVoIP existente)
    - Email (via SMTP)
    """
    __tablename__ = "canais"

    # ======================================================================
    # Colunas Principais e Identificação
    # ======================================================================
    id = Column(Integer, primary_key=True, index=True)
    
    # Isolamento multi-tenant (obrigatório)
    cliente_id = Column(
        Integer, 
        ForeignKey("clientes.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True,
        comment="ID da empresa/tenant proprietária deste canal"
    )
    
    nome = Column(
        String(100), 
        nullable=False, 
        comment="Nome amigável do canal (ex: PABX Materno, WhatsApp Vendas)"
    )
    descricao = Column(
        String(300), 
        nullable=True, 
        comment="Descrição detalhada do canal"
    )
    
    # Tipo e identificador técnico
    tipo = Column(
        String(30), 
        nullable=False, 
        comment="Tipo do canal: whatsapp, telegram, instagram, facebook, discord, voip_telefonia, email, chat_web"
    )
    identificador = Column(
        String(255), 
        nullable=False, 
        comment="Identificador técnico: token do bot, número E.164, SIP URI, ramal, page_id, etc."
    )
    
    # Configurações específicas (JSON)
    # Para VoIP: Armazena pabx_type, api_base_url, api_user, api_secret, trunk_outbound, context_ura
    configuracao = Column(
        Text, 
        nullable=True, 
        comment="JSON com configurações específicas (WABA_ID, credenciais PABX, etc.)"
    )
    
    # ======================================================================
    # Webhook e Integração
    # ======================================================================
    webhook_url = Column(
        String(500), 
        nullable=True, 
        comment="URL para a qual o PABX/API externa deve enviar eventos"
    )
    webhook_verify_token = Column(
        String(255), 
        nullable=True, 
        comment="Token de segurança (X-PABX-TOKEN) para autenticação do PABX do cliente"
    )
    departamento_id = Column(
        Integer, 
        ForeignKey("departamentos.id", ondelete="SET NULL"), 
        nullable=True,
        comment="Departamento responsável por atender este canal"
    )
    
    # ======================================================================
    # Status e Timestamps
    # ======================================================================
    ativo = Column(
        Boolean, 
        default=True, 
        nullable=False,
        comment="Indica se o canal está ativo para recebimento de mensagens"
    )
    
    # Status de conexão para o Dashboard (Healthcheck do PABX)
    status_conexao = Column(
        String(30), 
        default="ativo", 
        nullable=False,
        comment="Status da conexão: ativo, inativo, pendente_configuracao, erro_conexao"
    )

    criado_em = Column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc),
        comment="Data e hora de criação do canal"
    )
    atualizado_em = Column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Data e hora da última atualização"
    )
    ultimo_sync = Column(
        DateTime, 
        nullable=True,
        comment="Data do último sync/heartbeat com a API externa ou PABX"
    )

    # ======================================================================
    # Relacionamentos
    # ======================================================================
    cliente = relationship("Cliente", back_populates="canais")
    departamento = relationship("Departamento", back_populates="canais")
    menus = relationship("Menu", back_populates="canal", cascade="all, delete-orphan")
    usuarios = relationship("Usuario", back_populates="canal")
    atendimentos = relationship("Atendimento", back_populates="canal")
    
    # Bilhetagem e Rastreamento de Chamadas PABX (CDR)
    chamadas_pabx = relationship(
        "ChamadaPabx", 
        back_populates="canal", 
        cascade="all, delete-orphan"
    )
    
    # ======================================================================
    # Constraints e Métodos Auxiliares
    # ======================================================================
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('whatsapp', 'telegram', 'instagram', 'facebook', "
            "'discord', 'voip_telefonia', 'email', 'chat_web')",
            name="chk_canal_tipo_valido"
        ),
    )

    def __repr__(self):
        """Representação string do objeto Canal."""
        return f"<Canal(id={self.id}, nome='{self.nome}', tipo='{self.tipo}', cliente_id={self.cliente_id})>"

    @property
    def configuracao_json(self) -> dict:
        """
        Retorna a configuração como dicionário Python.
        Essencial para ler as credenciais do PABX (trunk_outbound, context_ura, etc.)
        """
        import json
        if self.configuracao:
            try:
                return json.loads(self.configuracao)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    @property
    def pode_receber_mensagens(self) -> bool:
        """Verifica se o canal está configurado para receber mensagens/webhooks."""
        return self.ativo and bool(self.webhook_url)