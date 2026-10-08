"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Models · Índice do pacote
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     __init__.py
@module   Backend / app/models
@author   Aldemir Queiroz
@since    2026
@version  3.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Ponto único de importação dos models do domínio. Este arquivo não cria
entidades novas: ele reexporta as classes dos 24 módulos `*_models.py` do
pacote e declara duas tabelas legadas que ainda escrevem no banco.

O QUE ESTE ARQUIVO É
───────────────────
O índice do pacote `app.models`. A lista `__all__` com 31 nomes é o contrato
público: define o que `from app.models import X` aceita. Os serviços e
routers importam por aqui; ninguém importa `atendimento_models` diretamente
quando só quer a classe.

OS OBJETOS REEXPORTADOS
───────────────────────
Os 24 `from app.models.<modulo> import ...` trazem o conjunto canônico:
Atendimento, AtendimentoContexto, Assinatura, Base, Campanha, CanalContratado,
ChamadaPABX, Cliente, Conexao, Contato, ContatoCanal, Departamento, EmailLog,
EmailTemplate, Empresa, InstanciaChatbot, Menu, MenuItem, ModeloMensagem,
NivelUsuario, Pedido, PedidoItem, Roteiro, Telefone, TokenRevogado,
Transferencia, Usuario e UsuarioCanal.

DUAS CLASSES DECLARADAS AQUI
────────────────────────────
    EmailEnviado    — tabela `emails_enviados`: histórico do e-mail avulso
                      enviado pela central de e-mail. Colunas: contato_id,
                      destinatario, assunto, corpo, status, erro_mensagem,
                      enviado_em, criado_em.
    CampanhaContato — tabela `campanha_contatos`: o status individual do
                      disparo para cada destinatário de uma campanha.
As duas usam o estilo antigo (`Column`), relationship unidirecional e nenhum
mixin: foram preservadas porque `email_service` e `campanha_service` ainda as
consomem como estão.

POR QUE OS RE-EXPORTS EXISTEM
─────────────────────────────
Para quebrar o import circular. Os módulos de model referenciam uns aos
outros em `relationship(back_populates=...)`, e os services importam o
domínio inteiro de um lugar só. Concentrar aqui quebra o ciclo: o
`app.models` é a folha, ninguém precisa voltar a ele.

O IMPORT DE `app.models` É OBRIGATÓRIO PARA O ALEMBIC
─────────────────────────────────────────────────────
`alembic/env.py` faz `import app.models` de propósito. Um model que existe no
arquivo mas não foi importado não entra no `Base.metadata`, e o autogenerate
então produz uma migration vazia — que apaga coluna em produção.

RELACIONAMENTO
──────────────
    ↓ importa        app/models/*_models.py (24 módulos canônicos)
    ↓ consumido por   app/services/*, app/security.py, app/database.py,
                     app/routers/tenant/atendimentos.py
    ↓ exige          alembic/env.py (metadata completa), init_db.py
    ↑ importa        app/models/base.py (Base) — a raiz do metadata
"""

# ══════════════════════════════════════════════════════════════════════════
# REEXPORTAÇÃO DO CONJUNTO CANÔNICO
# ══════════════════════════════════════════════════════════════════════════
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.atendimento_context_models import AtendimentoContexto
from app.models.atendimento_models import Atendimento
from app.models.assinatura_models import Assinatura
from app.models.base import Base
from app.models.campanha_models import Campanha
from app.models.canal_models import CanalContratado
from app.models.chamada_pabx_models import ChamadaPABX
from app.models.cliente_models import Cliente
from app.models.conexao_models import Conexao
from app.models.contato_models import Contato, ContatoCanal
from app.models.arquivo_models import Arquivo
from app.models.departamento_models import Departamento
from app.models.email_models import EmailLog, EmailTemplate
from app.models.empresa_models import Empresa, InstanciaChatbot
from app.models.menu_models import Menu, MenuItem
from app.models.modelo_mensagem_models import ModeloMensagem
from app.models.nivel_usuario_models import NivelUsuario
from app.models.pedido_models import Pedido, PedidoItem
from app.models.roteiro_models import Roteiro
from app.models.telefone_models import Telefone
from app.models.token_revogado_models import TokenRevogado
from app.models.transferencia_models import Transferencia
from app.models.usuario_canal_models import UsuarioCanal
from app.models.usuario_models import Usuario


# ══════════════════════════════════════════════════════════════════════════
# TABELAS LEGADAS AINDA EM USO —relationship unidirecional
# ══════════════════════════════════════════════════════════════════════════
class EmailEnviado(Base):
    """Histórico de e-mails avulsos enviados pelo sistema (central de E-mail)."""

    __tablename__ = "emails_enviados"

    id = Column(Integer, primary_key=True, index=True)
    contato_id = Column(Integer, ForeignKey("contatos.id"), nullable=True)
    destinatario = Column(String(150), nullable=False)
    assunto = Column(String(200), nullable=False)
    corpo = Column(Text, nullable=False)
    status = Column(String(20), default="pendente")  # enviado | erro | simulado
    erro_mensagem = Column(String(300))
    enviado_em = Column(DateTime)
    criado_em = Column(DateTime, default=datetime.utcnow)

    contato = relationship("Contato")


class CampanhaContato(Base):
    """Associação Campanha × Contato — status individual do disparo por destinatário."""

    __tablename__ = "campanha_contatos"

    id = Column(Integer, primary_key=True, index=True)
    campanha_id = Column(Integer, ForeignKey("campanhas.id"), nullable=False, index=True)
    contato_id = Column(Integer, ForeignKey("contatos.id"), nullable=False, index=True)
    status = Column(String(20), default="pendente")  # pendente | enviado | erro | simulado
    erro_mensagem = Column(String(300))
    enviado_em = Column(DateTime)

    campanha = relationship("Campanha")
    contato = relationship("Contato")




__all__ = [
    # conjunto canônico
    "Atendimento", "AtendimentoContexto", "Assinatura", "Base", "Campanha",
    "CanalContratado", "ChamadaPABX", "Cliente", "Conexao", "Contato",
      "ContatoCanal",
    "Departamento", "EmailLog", "EmailTemplate", "Empresa", "InstanciaChatbot",
    "Menu", "MenuItem", "ModeloMensagem", "NivelUsuario", "Pedido", "PedidoItem",
    "Roteiro", "Telefone", "TokenRevogado", "Transferencia", "Usuario",
    "UsuarioCanal",
    # legadas ainda em uso
    "Arquivo", "CampanhaContato", "EmailEnviado",
]
