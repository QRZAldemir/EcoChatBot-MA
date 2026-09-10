"""
Serviço de Tenant (Cliente) — isolamento multi-tenant.

Fornece acesso e resolução do cliente/tenant a partir da sessão do
usuário autenticado, bem como operações básicas de cadastro.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models import Cliente, Usuario


class TenantService:
    """Operações sobre o tenant (Cliente)."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def get_by_id(self, db: Session, cliente_id: int) -> Optional[Cliente]:
        return db.query(Cliente).filter(Cliente.id == cliente_id).first()

    def get_by_usuario(self, db: Session, usuario: Usuario) -> Optional[Cliente]:
        """Resolve o Cliente do usuário (via usuario.cliente_id)."""
        if not usuario or not usuario.cliente_id:
            return None
        return self.get_by_id(db, usuario.cliente_id)

    async def get_by_usuario_email(self, db: Session, email: str) -> Optional[Cliente]:
        """Resolve o Cliente a partir do email de um usuário."""
        usuario = db.query(Usuario).filter(Usuario.email == email).first()
        if not usuario or not usuario.cliente_id:
            return None
        return self.get_by_id(db, usuario.cliente_id)

    def criar(self, db: Session, nome: str, cnpj: Optional[str] = None,
              email: Optional[str] = None, telefone: Optional[str] = None) -> Cliente:
        cliente = Cliente(nome=nome, cnpj=cnpj, email=email, telefone=telefone, ativo=True)
        db.add(cliente)
        db.commit()
        db.refresh(cliente)
        return cliente
        # backend/app/services/tenant_service.py
class TenantService:
    def get_config(self, tenant_id: int) -> Dict[str, Any]:
        # Busca configuração do tenant no banco
        pass
    
    def get_departments(self, tenant_id: int) -> Dict[str, Any]:
        # Busca departamentos customizados
        pass
# Exemplo de modelo para configurações
class TenantConfig(Base):
    __tablename__ = "tenant_configs"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, unique=True)
    footer_text = Column(String)
    hub_menu = Column(JSON)
    # Outras configurações

