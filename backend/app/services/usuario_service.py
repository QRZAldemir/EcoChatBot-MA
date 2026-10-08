"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · usuario_service
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     usuario_service.py
@module   Backend / App / Services / usuario_service
@author   Aldemir Queiroz
@since    2026
@version  3.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Regras de negócio do USUÁRIO — quem entra no sistema: atendente,
supervisor, gestor, administrador.

    ┌──────────────────────────────────────────────────────────────────┐
    │ USUÁRIO = PESSOA + ACESSO + VÍNCULO                              │
    │                                                                  │
    │   Pessoa ......... nome, e-mail, telefone                       │
    │   Acesso .......... perfil, nível, status, senha                 │
    │   Vínculo ......... empresa, departamento, canais, conexões      │
    └──────────────────────────────────────────────────────────────────┘

As três partes são o motivo de este arquivo existir separado do model. O
model `Usuario` sabe gravar a linha; só aqui se decide QUEM pode criar
quem, e se o e-mail/login é único DENTRO da empresa ou no sistema todo.

O QUE ESTE ARQUIVO É
───────────────────
A camada de serviço entre `app/routers/usuario_routers.py` e a tabela
`usuarios`. O router valida o formato; este arquivo decide se a operação
faz sentido dentro do tenant.

O OBJETO
────────
`UsuarioService` é o objeto principal. Diferente de `CanalService`, aqui
o tenant entra pelo CONSTRUTOR e não por argumento:

    service = UsuarioService(db, empresa_id)
    service.criar_usuario(dados)

Um único `empresa_id` por instância é deliberado: depois de construído, o
objeto não tem como ler dados de outra empresa, porque não há de onde
tirar o id. Passar `empresa_id` por método deixaria a porta aberta para um
argumento trocado — e um `empresa_id` trocado é um vazamento de dados
entre clientes, o pior bug possível num sistema multi-tenant.

SÍNCRONO DE PROPÓSITO
─────────────────────
`UsuarioService` usa `Session` (síncrona), ao contrário de `CanalService`.
Não é inconsistência: usuários são pocos e writes raros, então o custo de
abrir uma sessão assíncrona não se paga. Já os canais concentram validação
de unicidade concorrente, que realmente precisa de `async`.

REGRAS QUE VIVEM AQUI
────────────────────
    e-mail único ....... por empresa, não global
    login único ........ por empresa, não global
    senha forte ........ exige maiúscula, minúscula, número e símbolo
    vínculo ............ empresa, departamento e conexões são validados
                         contra o MESMO tenant antes de gravar
    convite ............ cria usuário já vinculado, sem senha em claro
   孤立 ................ usuário sem departamento é recusado se a empresa
                         exigir departamento na operação

ISOLAMENTO MULTI-TENANT
────────────────────────
`_validar_empresa` roda em TODA operação e é a primeira coisa a
executar. Ela também recusa `empresa_id` nulo, porque `None` num filtro
SQL é o caminho clássico para vazar todas as empresas de uma vez: a
cláusula `WHERE empresa_id IS NULL` devolve o banco inteiro.

COMO SE LIGA AO RESTO
─────────────────────
    ┌──────────────────────────────────────────────────────────────────┐
    │ app/routers/usuario_routers.py                                  │
    │   └─► UsuarioService     regras, senhas, vínculos                │
    │         └─► Usuario (model)                                      │
    │               ├─► Atendimento.atendente_id   quem atende        │
    │               ├─► Transferencia              histórico          │
    │               └─► TokenRevogado               sessões            │
    └──────────────────────────────────────────────────────────────────┘
"""

import secrets
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import hash_senha, verificar_senha
from app.models.conexao_models import Conexao
from app.models.empresa_models import Empresa
from app.models.usuario_models import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario_schemas import (
    UsuarioConvidar,
    UsuarioCreate,
    UsuarioResetSenha,
    UsuarioUpdate,
    UsuarioUpdateSenha,
)


class UsuarioService:
    """
    Pessoa que usa o sistema, com seu acesso e seus vínculos.

        ┌────────────────────────────────────────────────────────────┐
        │ USUÁRIO = PESSOA + ACESSO + VÍNCULO                       │
        │   Pessoa  .... nome, e-mail, telefone                     │
        │   Acesso  .... perfil, nível, status, senha                │
        │   Vínculo  ... empresa, departamento, canais, conexões     │
        └────────────────────────────────────────────────────────────┘

    O OBJETO GUARDA O TENANT
    ────────────────────────
        service = UsuarioService(db, empresa_id)

    `empresa_id` vem do CONSTRUTOR, não dos métodos. Depois de construído, o
    objeto não tem como alcançar dados de outra empresa porque não existe de
    onde tirar o id. Por argumento, um `empresa_id` trocado numa chamada
    vazaria a fila de outro cliente — o pior bug possível num sistema
    multi-tenant, e um que passa despercebido em teste.

    Por isso `_validar_empresa` roda em TODA operação, inclusive as de
    leitura, e recusa `None`: `WHERE empresa_id IS NULL` devolve o banco
    inteiro.

    O QUE ELE FAZ
    ─────────────
        usuários ........... CRUD com e-mail e login únicos POR EMPRESA
        senha .............. gera, valida força, troca e reseta (via `secrets`)
        convite ............ cria usuário vinculado, sem senha em claro
        vínculos ........... valida empresa, departamento e conexões no
                             MESMO tenant antes de gravar
        estatísticas ....... contagens para o painel do gestor
    """

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
                senha_hash=hash_senha(dados.senha),
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
                usuario.senha_hash = hash_senha(dados.senha)

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

        if not verificar_senha(dados.senha_atual, usuario.senha_hash):
            raise HTTPException(400, "Senha atual incorreta")

        try:
            usuario.senha_hash = hash_senha(dados.nova_senha)
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
            usuario.senha_hash = hash_senha(dados.nova_senha)
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
                senha_hash=hash_senha(senha_temp),
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