# ==============================================================================
# ARQUIVO.....: canal_repository.py
# AUTOR.......: Aldemir Queiroz
# EMAIL.......: queiroz@almarcx.com.br
# PROJETO.....: EcoChatBot-MA - Sistema Multi-Tenant de Atendimento
# MÓDULO......: Repositório de CanalContratado
# VERSÃO......: 1.0.0
# CRIADO EM...: 2026-10-07
# ATUALIZADO..: 2026-10-07
# LINGUAGEM...: Python 3.12+
# FRAMEWORK...: SQLAlchemy 2.0
# ==============================================================================
# DESCRIÇÃO...:
# Repositório para acesso a dados de `CanalContratado`.
#
# FUNCIONALIDADE:
#   - Garante escopo multi-tenant (sempre filtrado por cliente_id).
#   - Mantém unicidade lógica (telefone_id, tipo) por cliente.
#   - Métodos específicos: buscar_por_telefone_tipo, contratar, desativar, listar_por_empresa.
#
# DECISÕES DE ARQUITETURA:
#   - Herda de BaseRepository para reutilizar padrões e manter consistência.
#   - Usa flush() (não commit) nas operações de escrita (Unit of Work).
#   - Só devolve registros ativos quando não explicitado.
#
# RELACIONAMENTOS:
#   - models.canal_models.CanalContratado
#   - repositories.base_repository.BaseRepository
#   - services.canal_service.CanalService
#   - schemas.canal_schemas.CanalCreate
# ==============================================================================
"""
Repositório especializado em `CanalContratado` (conectores de canais contratados).

Responsável por isolar consultas e regras de unicidade por (telefone_id, tipo)
dentro do escopo multi-tenant. Todas as operações respeitam `cliente_id` como
filtro de tenant.

O repositório NÃO decide regras de negócio (quem pode contratar/desativar):
apenas executa acesso a dados com os filtros corretos.

Classes:
    CanalRepository: Métodos de consulta e persistência para CanalContratado.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.repositories.base_repository import BaseRepository
from app.models.canal_models import CanalContratado
from app.schemas.canal_schemas import CanalCreate

async def get_by_id(db: AsyncSession, canal_id: int) -> CanalContratado | None:
    """
    Busca um canal contratado pelo ID de forma assíncrona.
    """
    stmt = select(CanalContratado).where(CanalContratado.id == canal_id)
    result = await db.execute(stmt) #  Await na execução da query
    return result.scalar_one_or_none() #  Extração síncrona do resultado já em memória
    

class CanalRepository(BaseRepository[CanalContratado]):
    """
    Repositório de `CanalContratado`.

    O que este objeto é:
        Camada de acesso a dados para conectores (WhatsApp, Telegram, PABX).
        Garante que toda consulta seja limitada ao tenant (`cliente_id`).

    Regras aplicadas aqui:
        - Unicidade lógica: (telefone_id, tipo) deve ser único por cliente.
        - Listagens retornam, por padrão, canais ativos.
        - Escrita usa flush() (Unit of Work). O Service controla o commit.
    """

    def __init__(self, session: Session):
        """
        Inicializa o repositório com a sessão atual.

        :param session: Sessão SQLAlchemy (commit/rollback no escopo do Service).
        """
        super().__init__(session, CanalContratado)

    def buscar_por_telefone_tipo(
        self,
        telefone_id: int,
        tipo: str,
        cliente_id: int,
    ) -> Optional[CanalContratado]:
        """
        Busca um canal contratado por (telefone_id, tipo) dentro do tenant.

        O que serve:
            - Garante a restrição de unicidade `(telefone_id, tipo)` por cliente
              antes de criar um novo conector.
            - Evita duplicidade de integração para o mesmo número/tipo.

        Parâmetros:
            telefone_id (int): Identificador do telefone no provedor/legado.
            tipo (str): Tipo de canal (ex.: 'whatsapp', 'telegram', 'pabx', 'facebook', 'instagram').
            cliente_id (int): ID do cliente (tenant). Obrigatório para isolar dados.

        Retorno:
            CanalContratado | None: Instância encontrada, ou None se não existir
            no escopo do cliente informado.
        """
        stmt = select(CanalContratado).where(
            and_(
                CanalContratado.telefone_id == telefone_id,
                CanalContratado.tipo == tipo,
                CanalContratado.cliente_id == cliente_id,
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def contratar(self, dto: CanalCreate, cliente_id: int) -> CanalContratado:
        """
        Registra um novo ponto de entrada (contrata um canal).

        O que serve:
            - Cria um `CanalContratado` vinculado ao `cliente_id` (tenant).
            - Persiste com flush() para permitir validações/composições no Service
              antes do commit (Unit of Work).

        Parâmetros:
            dto (CanalCreate): Dados para criação do canal (nome, tipo, telefone_id,
                credenciais, configurações, etc.).
            cliente_id (int): Cliente proprietário do canal (tenant). Obrigatório.

        Retorno:
            CanalContratado: Instância persistida (em estado pendente de commit).
        """
        canal = CanalContratado(
            cliente_id=cliente_id,
            **dto.model_dump(),
        )
        self.session.add(canal)
        self.session.flush()
        return canal

    def desativar(self, canal_id: int, cliente_id: int) -> Optional[CanalContratado]:
        """
        Desativa o conector com trava de tenant.

        O que serve:
            - Realiza desativação lógica (soft disable): marca `ativo = False`.
            - Impõe trava de tenant: só desativa se o canal pertencer ao `cliente_id`.
            - Não remove fisicamente o registro (preserva histórico/auditoria).

        Parâmetros:
            canal_id (int): ID do canal contratado a desativar.
            cliente_id (int): Tenant do canal. Obrigatório (protege cross-tenant).

        Retorno:
            CanalContratado | None: Canal desativado, ou None caso não exista
            ou não pertença ao cliente informado.

        Observação:
            Esta operação não comita. Usa flush() via `add` implícito após alteração.
        """
        canal = self.get_by_id(canal_id, cliente_id)
        if canal is None:
            return None
        canal.ativo = False
        self.session.add(canal)
        self.session.flush()
        return canal

    def listar_por_empresa(self, cliente_id: int) -> List[CanalContratado]:
        """
        Retorna os conectores ativos (WhatsApp, Telegram, PABX) da empresa.

        O que serve:
            - Lista conectores disponíveis para atendimento no tenant.
            - Filtro padrão: apenas `ativo = True` (conectores operacionais).
            - Ordenado por ID para consistência de resposta.

        Parâmetros:
            cliente_id (int): Cliente/empresa (tenant). Obrigatório.

        Retorno:
            List[CanalContratado]: Lista de canais contratados ativos.
        """
        stmt = (
            select(CanalContratado)
            .where(
                and_(
                    CanalContratado.cliente_id == cliente_id,
                    CanalContratado.ativo.is_(True),
                )
            )
            .order_by(CanalContratado.id)
        )
        return list(self.session.execute(stmt).scalars())
