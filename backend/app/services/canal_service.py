# ==============================================================================
# Autor: Aldemir Queiroz
# Data: 24/05/2024
# ==============================================================================
# Arquivo: canal_service.py (Pasta: app/services)
#
# DESCRIÇÃO:
# Este arquivo contém a classe CanalService, que atua como a camada de serviço 
# para a entidade Canal. Ele encapsula toda a lógica de negócio relacionada 
# aos canais, incluindo operações de CRUD (Criar, Ler, Atualizar, Deletar). 
# Essa camada serve de intermediário entre os controladores (routers) e o 
# acesso ao banco de dados, promovendo a separação de responsabilidades.
# ==============================================================================

from sqlalchemy.orm import Session
from app.models import Canal
from app.schemas import CanalCreate, CanalUpdate
from typing import List, Optional

class CanalService:
    """
    Classe de serviço para gerenciar operações relacionadas a canais.
    Implementa a lógica de negócio e interage com o banco de dados.
    """

    @staticmethod
    def _verificar_nome_duplicado(db: Session, nome: str, exclude_canal_id: Optional[int] = None) -> None:
        """
        Verifica se já existe um canal com o mesmo nome.
        Se exclude_canal_id for fornecido, ignora esse canal na verificação.

        Args:
            db (Session): Sessão do banco de dados.
            nome (str): Nome do canal a ser verificado.
            exclude_canal_id (Optional[int]): ID do canal a ser excluída da verificação.

        Raises:
            ValueError: Se já existir um canal com o mesmo nome.
        """
        query = db.query(Canal).filter(Canal.nome == nome)

        if exclude_canal_id is not None:
            query = query.filter(Canal.id != exclude_canal_id)

        if query.first():
            raise ValueError("Já existe um canal com este nome")

    @staticmethod
    def _validar_nome(nome: str) -> None:
        """
        Valida se o nome do canal é válido.

        Args:
            nome (str): Nome do canal a ser validado.

        Raises:
            ValueError: Se o nome for vazio ou contiver apenas espaços em branco.
        """
        if not nome:
            raise ValueError("O nome do canal não pode ser vazio")

        if not nome.strip():
            raise ValueError("O nome do canal não pode conter apenas espaços em branco")

    @staticmethod
    def listar_canais(db: Session) -> List[Canal]:
        """Lista todos os canais cadastrados no banco de dados."""
        return db.query(Canal).all()

    @staticmethod
    def buscar_por_id(db: Session, canal_id: int) -> Optional[Canal]:
        """Busca um canal específico pelo seu ID."""
        return db.query(Canal).filter(Canal.id == canal_id).first()

    @staticmethod
    def buscar_por_nome(db: Session, nome: str) -> Optional[Canal]:
        """Busca um canal pelo seu nome."""
        return db.query(Canal).filter(Canal.nome == nome).first()

    @staticmethod
    def criar_canal(db: Session, canal: CanalCreate) -> Canal:
        """
        Cria um novo canal no banco de dados.

        Args:
            db (Session): Sessão do banco de dados.
            canal (CanalCreate): Dados do canal a ser criado.

        Returns:
            Canal: O canal recém-criado.

        Raises:
            ValueError: Se já existir um canal com o mesmo nome ou se o nome for inválido.
        """
        # CORRIGIDO: Validação do nome ocorre ANTES de qualquer operação com BD
        # Impede que nomes inválidos chegem ao banco de dados
        CanalService._validar_nome(canal.nome)

        # CORRIGIDO: Verificação de duplicidade movida para ANTES de criar a instância
        # Falha cedo se nome já existe, sem tentar criar registro duplicado
        CanalService._verificar_nome_duplicado(db, canal.nome)

        db_canal = Canal(
            nome=canal.nome,
            descricao=canal.descricao,
            arquivo_menu=canal.arquivo_menu,
            departamento_id=canal.departamento_id,
            ativo=canal.ativo
        )

        # CORRIGIDO: Removido db.begin() - FastAPI/SQLAlchemy já gerencia transações automaticamente
        # Usar db.begin() aqui causaria InvalidRequestError
        # A sessão FastAPI já está em uma transação implícita
        db.add(db_canal)
        db.commit()

        # Atualizado com os dados mais recentes do banco (inclui ID auto-gerado)
        db.refresh(db_canal)

        return db_canal

    @staticmethod
    def atualizar_canal(db: Session, canal_id: int, canal: CanalUpdate) -> Optional[Canal]:
        """
        Atualiza um canal existente no banco de dados.

        Args:
            db (Session): Sessão do banco de dados.
            canal_id (int): ID do canal a ser atualizado.
            canal (CanalUpdate): Dados atualizados do canal.

        Returns:
            Optional[Canal]: O canal atualizado ou None se não existir.

        Raises:
            ValueError: Se o novo nome já existe em outro canal ou se o nome for inválido.
        """
        db_canal = db.query(Canal).filter(Canal.id == canal_id).first()
        if not db_canal:
            return None

        # CORRIGIDO: Removido db.begin() - FastAPI/SQLAlchemy já gerencia transações automaticamente
        # Usar db.begin() aqui causaria InvalidRequestError
        # A sessão FastAPI já está em uma transação implícita

        # CORRIGIDO: Validação de nome com check explícito "is not None"
        # Evita que strings vazias passem (falsy check causaria bypass)
        if canal.nome is not None and canal.nome != db_canal.nome:
            CanalService._validar_nome(canal.nome)

            # Verifica se já existe outro canal com o mesmo nome
            CanalService._verificar_nome_duplicado(
                db,
                canal.nome,
                exclude_canal_id=canal_id
            )

        # Atualiza apenas os campos que foram realmente enviados na requisição
        for campo, valor in canal.model_dump(exclude_unset=True).items():
            setattr(db_canal, campo, valor)

        db.commit()

        # Atualizado com os dados mais recentes do banco
        db.refresh(db_canal)

        return db_canal

    @staticmethod
    def deletar_canal(db: Session, canal_id: int) -> bool:
        """Deleta um canal do banco de dados."""
        db_canal = db.query(Canal).filter(Canal.id == canal_id).first()
        if not db_canal:
            return False

        db.delete(db_canal)
        db.commit()

        return True
