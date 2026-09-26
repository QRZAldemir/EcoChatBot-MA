# ==============================================================================
# ARQUIVO.....: app/services/usuario_service.py
# AUTOR.......: Aldemir Queiroz
# EMAIL.......: queiroz@almarcx.com.br
# PROJETO.....: EcoChatBotMarcx - Sistema Multi-Tenant de Atendimento
# MÓDULO......: Service do Objeto Usuario (Regras de Negócio)
# VERSÃO......: 3.0.0
# CRIADO EM...: 2024-01-15
# ATUALIZADO..: 2026-09-19
# LINGUAGEM...: Python 3.12+
# FRAMEWORK...: FastAPI + SQLAlchemy 2.0
# ==============================================================================
# DESCRIÇÃO...:
# Camada de serviço que orquestra as regras de negócio do objeto Usuario.
# Centraliza validações complexas (empresa com conexões ativas, unicidade
# de email/login por tenant, conexões pertencentes à empresa) e controla
# o ciclo transacional (commit/rollback).
#
# FUNCIONALIDADES:
# 1. Validação de empresa (existência, status, conexões ativas)
# 2. Validação de conexões (pertencem à empresa, ativas)
# 3. Validação de unicidade de email POR EMPRESA
# 4. Validação de unicidade de login (usuario) POR EMPRESA
# 5. Validação de conexão padrão entre as vinculadas
# 6. CRUD completo com controle transacional
# 7. Soft delete
# 8. Gestão de senha (change, reset)
# 9. Convite de usuário (senha temporária)
# 10. Estatísticas agregadas
#
# REGRAS CRÍTICAS DE NEGÓCIO:
# - Todo usuário DEVE ter empresa_id (extraído do JWT)
# - Empresa DEVE ter ≥ 1 conexão ativa
# - Conexões selecionadas DEVEM pertencer à empresa
# - Conexão padrão DEVE estar entre as vinculadas
# - Email e login são únicos POR EMPRESA
# - empresa_id é IMUTÁVEL após criação
#
# DEPENDÊNCIAS:
# - app.repositories.usuario_repository.UsuarioRepository
# - app.core.security.get_password_hash / verify_password
# - app.models (Usuario, Empresa, Conexao)
# - app.schemas.usuario_schemas (DTOs)
#
# USADO POR:
# - app.routers.tenant.usuario_router (camada HTTP)
# ==============================================================================

import secrets
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import get_password_hash, verify_password
from app.models.conexao import Conexao
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario_schemas import (
    UsuarioConvidar,
    UsuarioCreate,
    UsuarioResetSenha,
    UsuarioUpdate,
    UsuarioUpdateSenha,
)


class UsuarioService:
    """Orquestra regras de negócio do objeto Usuario (multi-tenant)."""

    def __init__(self, db: Session, empresa_id: int) -> None:
        self.db = db
        self.empresa_id = empresa_id
        self.repo = UsuarioRepository(db, empresa_id)

    # ==========================================================================
    # VALIDAÇÕES PRIVADAS
    # ==========================================================================
    def _validar_empresa(self) -> Empresa:
        """Valida empresa (existe, ativa, com conexões ativas)."""
        empresa = self.db.query(Empresa).filter(
            Empresa.id == self.empresa_id
        ).first()

        if not empresa:
            raise HTTPException(404, "Empresa não encontrada")

        if not empresa.ativo:
            raise HTTPException(400, "Empresa inativa")

        qtd = self.db.query(Conexao).filter(
            Conexao.empresa_id == self.empresa_id,
            Conexao.ativo.is_(True),
        ).count()

        if qtd == 0:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Empresa não possui conexões ativas (telefones) configuradas",
            )

        return empresa

    def _validar_conexoes(self, ids: List[int]) -> List[Conexao]:
        """Valida que conexões pertencem à empresa e estão ativas."""
        if not ids:
            raise HTTPException(400, "Selecione ao menos uma conexão")

        conexoes = self.db.query(Conexao).filter(
            Conexao.id.in_(ids),
            Conexao.empresa_id == self.empresa_id,
            Conexao.ativo.is_(True),
        ).all()

        if len(conexoes) != len(ids):
            raise HTTPException(
                400,
                "Uma ou mais conexões não pertencem à empresa ou estão inativas",
            )

        return conexoes

    def _validar_email_unico(
        self, email: str, ignorar_id: Optional[int] = None,
    ) -> None:
        existente = self.repo.get_by_email_in_tenant(email)
        if existente and existente.id != ignorar_id:
            raise HTTPException(409, "E-mail já cadastrado nesta empresa")

    def _validar_login_unico(
        self, usuario: str, ignorar_id: Optional[int] = None,
    ) -> None:
        existente = self.repo.get_by_login_in_tenant(usuario)
        if existente and existente.id != ignorar_id:
            raise HTTPException(409, "Login já cadastrado nesta empresa")

    def _validar_conexao_padrao(
        self, padrao_id: Optional[int], conexoes: List[Conexao],
    ) -> None:
        if padrao_id and padrao_id not in [c.id for c in conexoes]:
            raise HTTPException(
                400, "Conexão padrão deve estar entre as conexões vinculadas"
            )

    # ==========================================================================
    # CREATE
    # ==========================================================================
    def criar_usuario(self, dados: UsuarioCreate) -> Usuario:
        """Cria usuário com validações completas."""
        self._validar_empresa()
        self._validar_email_unico(dados.email)
        self._validar_login_unico(dados.usuario)
        conexoes = self._validar_conexoes(dados.conexoes_ids)
        self._validar_conexao_padrao(dados.conexao_padrao_id, conexoes)

        try:
            usuario = Usuario(
                empresa_id=self.empresa_id,
                nome=dados.nome,
                usuario=dados.usuario,
                email=dados.email,
                telefone=dados.telefone,
                senha_hash=get_password_hash(dados.senha),
                foto=dados.foto,
                nivel_id=dados.nivel_id,
                departamento_id=dados.departamento_id,
                canal_id=dados.canal_id,
                turno_id=dados.turno_id,
                ativo=dados.ativo,
                status="ativo" if dados.ativo else "inativo",
                conexao_padrao_id=dados.conexao_padrao_id,
            )
            usuario.conexoes = conexoes
            self.repo.add(usuario)
            self.db.commit()
            self.db.refresh(usuario)
            return usuario
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(500, f"Erro ao criar usuário: {e}")

    # ==========================================================================
    # UPDATE
    # ==========================================================================
    def atualizar_usuario(
        self, usuario_id: int, dados: UsuarioUpdate,
    ) -> Usuario:
        """Atualização parcial. empresa_id é imutável."""
        usuario = self.repo.get_by_id_com_relacoes(usuario_id)

        if not usuario:
            raise HTTPException(404, "Usuário não encontrado")

        try:
            if dados.email and dados.email.lower() != usuario.email.lower():
                self._validar_email_unico(dados.email, ignorar_id=usuario_id)
                usuario.email = dados.email.lower()

            if dados.usuario and dados.usuario.lower() != usuario.usuario.lower():
                self._validar_login_unico(dados.usuario, ignorar_id=usuario_id)
                usuario.usuario = dados.usuario.lower()

            if dados.senha:
                usuario.senha_hash = get_password_hash(dados.senha)

            for campo in (
                "nome", "telefone", "foto", "nivel_id",
                "departamento_id", "canal_id", "turno_id", "ativo",
            ):
                valor = getattr(dados, campo, None)
                if valor is not None:
                    setattr(usuario, campo, valor)

            if dados.ativo is not None:
                usuario.status = "ativo" if dados.ativo else "inativo"

            if dados.conexoes_ids is not None:
                conexoes = self._validar_conexoes(dados.conexoes_ids)
                usuario.conexoes = conexoes

            if dados.conexao_padrao_id is not None:
                self._validar_conexao_padrao(
                    dados.conexao_padrao_id, list(usuario.conexoes),
                )
                usuario.conexao_padrao_id = dados.conexao_padrao_id

            self.db.commit()
            self.db.refresh(usuario)
            return usuario
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(500, f"Erro ao atualizar usuário: {e}")

    # ==========================================================================
    # DELETE (SOFT)
    # ==========================================================================
    def deletar_usuario(self, usuario_id: int) -> bool:
        usuario = self.repo.get_by_id(usuario_id)

        if not usuario:
            return False

        usuario.ativo = False
        usuario.status = "inativo"
        self.db.commit()
        return True

    # ==========================================================================
    # READ
    # ==========================================================================
    def listar_usuarios(
        self, page: int = 1, limit: int = 20, filtros: Optional[dict] = None,
    ) -> Tuple[int, List[Usuario]]:
        return self.repo.listar(page, limit, filtros)

    def buscar_por_id(self, usuario_id: int) -> Optional[Usuario]:
        return self.repo.get_by_id_com_relacoes(usuario_id)

    # ==========================================================================
    # SENHA
    # ==========================================================================
    def alterar_senha(
        self, usuario_id: int, dados: UsuarioUpdateSenha,
    ) -> bool:
        usuario = self.repo.get_by_id(usuario_id)

        if not usuario:
            raise HTTPException(404, "Usuário não encontrado")

        if not verify_password(dados.senha_atual, usuario.senha_hash):
            raise HTTPException(400, "Senha atual incorreta")

        try:
            usuario.senha_hash = get_password_hash(dados.nova_senha)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise HTTPException(500, f"Erro ao alterar senha: {e}")

    def resetar_senha(
        self, usuario_id: int, dados: UsuarioResetSenha,
    ) -> bool:
        usuario = self.repo.get_by_id(usuario_id)

        if not usuario:
            raise HTTPException(404, "Usuário não encontrado")

        try:
            usuario.senha_hash = get_password_hash(dados.nova_senha)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise HTTPException(500, f"Erro ao resetar senha: {e}")

    # ==========================================================================
    # CONVITE
    # ==========================================================================
    def convidar_usuario(self, dados: UsuarioConvidar) -> Usuario:
        self._validar_empresa()
        self._validar_email_unico(dados.email)
        self._validar_login_unico(dados.usuario)

        try:
            senha_temp = secrets.token_urlsafe(16)
            usuario = Usuario(
                empresa_id=self.empresa_id,
                nome=dados.nome,
                usuario=dados.usuario,
                email=dados.email.lower(),
                senha_hash=get_password_hash(senha_temp),
                nivel_id=dados.nivel_id,
                departamento_id=dados.departamento_id,
                canal_id=dados.canal_id,
                turno_id=dados.turno_id,
                ativo=False,
                status="pendente",
            )
            self.repo.add(usuario)
            self.db.commit()
            self.db.refresh(usuario)
            return usuario
        except Exception as e:
            self.db.rollback()
            raise HTTPException(500, f"Erro ao criar convite: {e}")

    # ==========================================================================
    # ESTATÍSTICAS
    # ==========================================================================
    def get_estatisticas(self) -> dict:
        total = self.db.query(Usuario).filter(
            Usuario.empresa_id == self.empresa_id
        ).count()

        ativos = self.db.query(Usuario).filter(
            Usuario.empresa_id == self.empresa_id,
            Usuario.ativo.is_(True),
        ).count()

        return {"total": total, "ativos": ativos, "inativos": total - ativos}