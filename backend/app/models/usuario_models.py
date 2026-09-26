# ==============================================================================
# ARQUIVO.....: app/models/usuario_models.py
# AUTOR.......: Aldemir Queiroz
# EMAIL.......: queiroz@almarcx.com.br
# PROJETO.....: EcoChatBot-MA - Sistema Multi-Tenant de Atendimento
# MÓDULO......: Modelo ORM do Objeto Usuario
# VERSÃO......: 3.0.0
# CRIADO EM...: 2024-01-15
# ATUALIZADO..: 2026-09-19
# LINGUAGEM...: Python 3.12+
# FRAMEWORK...: SQLAlchemy 2.0 + FastAPI
# ==============================================================================
# DESCRIÇÃO...:
# Define o modelo ORM do objeto Usuario em arquitetura SaaS Multi-Tenant.
# O Usuario representa um atendente/gestor vinculado obrigatoriamente a
# uma Empresa (tenant), com relacionamentos para Canal, NivelUsuario,
# Departamento, Turno, e relacionamento M:N com Conexao (telefones da empresa).
#
# FUNCIONALIDADES:
# 1. Vínculo obrigatório com Empresa (empresa_id NOT NULL)
# 2. Login único por empresa (usuario + empresa_id)
# 3. Email único por empresa (email + empresa_id)
# 4. Foto do atendente (base64 ou URL)
# 5. Relacionamento N:1 com Canal, NivelUsuario, Departamento, Turno
# 6. Relacionamento M:N com Conexao (telefones da empresa)
# 7. Conexão padrão (conexao_padrao_id)
# 8. Soft delete via ativo + status
#
# REGRAS DE NEGÓCIO:
# - Todo usuário DEVE ter empresa_id (imutável pós-criação)
# - Login e email são únicos POR EMPRESA
# - Conexão padrão DEVE estar entre as vinculadas (validado no Service)
# - Soft delete preserva histórico
#
# RELACIONAMENTOS:
# - Empresa (N:1)         — tenant obrigatório
# - Canal (N:1)           — canal principal do usuário
# - NivelUsuario (N:1)    — nível de acesso (atendente/gerente/etc)
# - Departamento (N:1)    — departamento organizacional
# - Turno (N:1)           — turno de trabalho (opcional)
# - Conexao (M:N)         — telefones da empresa vinculados
# - Conexao (N:1)         — conexão padrão (default)
#
# DEPENDÊNCIAS:
# - app.database.Base
# - app.models.empresa.Empresa
# - app.models.canal.Canal
# - app.models.nivel_usuario.NivelUsuario
# - app.models.departamento.Departamento
# - app.models.turno.Turno
# - app.models.conexao.Conexao
#
# USADO POR:
# - app.repositories.usuario_repository.UsuarioRepository
# - app.services.usuario_service.UsuarioService
# - app.routers.tenant.usuario_router (router REST)
# ==============================================================================

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer,
    String, Table, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.conexao_models import Conexao
    from app.models.departamento_models import Departamento
    from app.models.empresa_models import Empresa
    from app.models.nivel_usuario_models import NivelUsuario
    from app.models.usuario_canal_models import UsuarioCanal


# ==============================================================================
# TABELA ASSOCIATIVA M:N — USUARIOS <-> CONEXOES
# ------------------------------------------------------------------------------
# Vincula os telefones (conexões) da empresa que um usuário pode atender.
# ON DELETE CASCADE garante limpeza automática dos vínculos.
# ==============================================================================
usuarios_conexoes = Table(
    "usuarios_conexoes",
    Base.metadata,
    Column(
        "usuario_id", Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "conexao_id", Integer,
        ForeignKey("conexoes.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# ==============================================================================
# MODELO: USUARIO
# ------------------------------------------------------------------------------
# Representa o atendente/gestor do sistema. Vinculado obrigatoriamente a
# uma empresa (tenant). Possui relacionamentos com Canal, NivelUsuario,
# Departamento, Turno, e M:N com Conexao.
# ==============================================================================
class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("empresa_id", "email", name="uq_usuarios_empresa_email"),
        UniqueConstraint("empresa_id", "usuario", name="uq_usuarios_empresa_usuario"),
    )

    # --------------------------------------------------------------------------
    # IDENTIFICAÇÃO E VÍNCULO MULTI-TENANT
    # --------------------------------------------------------------------------
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    empresa_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("empresas.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    # --------------------------------------------------------------------------
    # DADOS PESSOAIS E AUTENTICAÇÃO
    # --------------------------------------------------------------------------
    nome: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    usuario: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True,
    )
    telefone: Mapped[Optional[str]] = mapped_column(String(20))
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    foto: Mapped[Optional[str]] = mapped_column(Text)

    # --------------------------------------------------------------------------
    # VÍNCULOS ORGANIZACIONAIS (N:1)
    # --------------------------------------------------------------------------
    nivel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("nivel_usuario.id"), nullable=False, index=True,
    )
    departamento_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("departamentos.id"), index=True,
    )

    # --------------------------------------------------------------------------
    # CONEXÃO PADRÃO (N:1 — deve estar entre as M:N)
    # --------------------------------------------------------------------------
    conexao_padrao_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("conexoes.id"),
    )

    # --------------------------------------------------------------------------
    # STATUS E TIMESTAMPS
    # --------------------------------------------------------------------------
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="ativo", nullable=False,
    )
    # `perfil` e `ultimo_login` vinham da segunda definicao de Usuario que
    # existia em empresa_models.py. Migrados aqui para que nenhuma coluna
    # seja perdida na consolidacao. `nivel_id` continua sendo o vinculo de
    # acesso; `perfil` e a chave textual legada (super_admin, admin,
    # gestor, atendente, bot, api).
    perfil: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    ultimo_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
    )

    # --------------------------------------------------------------------------
    # RELACIONAMENTOS
    # --------------------------------------------------------------------------
    empresa: Mapped["Empresa"] = relationship("Empresa")
    nivel: Mapped["NivelUsuario"] = relationship(back_populates="usuarios")
    departamento: Mapped[Optional["Departamento"]] = relationship("Departamento")
    vinculos_canal: Mapped[List["UsuarioCanal"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan", lazy="selectin",
    )
    conexao_padrao: Mapped[Optional["Conexao"]] = relationship(
        "Conexao", foreign_keys=[conexao_padrao_id],
    )
    conexoes: Mapped[List["Conexao"]] = relationship(
        "Conexao",
        secondary=usuarios_conexoes,
        lazy="selectin",
    )

    # --------------------------------------------------------------------------
    # MÉTODOS DE DOMÍNIO
    # --------------------------------------------------------------------------
    def pode_acessar_empresa(self, empresa_id: int) -> bool:
        """Anti-IDOR: valida se usuário pertence à empresa informada."""
        return self.empresa_id == empresa_id

    def tem_conexao_ativa(self) -> bool:
        """Retorna True se ao menos uma conexão vinculada está ativa."""
        return any(c.ativo for c in self.conexoes)