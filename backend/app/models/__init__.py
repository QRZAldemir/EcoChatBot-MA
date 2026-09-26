"""
================================================================================
EcoChatBot-MA · Pacote de Models
@author  Aldemir Queiroz
@since   2026
@version 3.0.0
================================================================================

SUMÁRIO
-------
[1] O QUE ESTE ARQUIVO É
[2] CONJUNTO DE MODELS
[3] TABELAS LEGADAS AINDA VIVAS
[4] O QUE FOI REMOVIDO E POR QUÊ
================================================================================

[1] O QUE ESTE ARQUIVO É
-----------------------
    Ponto único de importação dos models. NÃO define mais nenhuma entidade do
    domínio: todas moram nos módulos `*_models.py`. Este arquivo apenas
    reexporta, para o código legado continuar importando de um lugar só.

        from app.models import Usuario, CanalContratado   # funciona
        import app.models; app.models.Usuario              # funciona

[2] CONJUNTO DE MODELS
---------------------
    O domínio canônico está em `app/models/*_models.py`. Cada arquivo traz
    cabeçalho com FUNCIONALIDADE, EXEMPLO PRÁTICO, RELACIONAMENTO e
    REGRAS DE NEGÓCIO. aplication usa SQLAlchemy 2.0 (Mapped/mapped_column).

[3] TABELAS LEGADAS AINDA VIVAS
-------------------------------
    Três tabelas continuam em uso e por isso seguem declaradas aqui, com
    relacionamento unidirecional, porque suas ligações antigas apontam para
    colunas que não existem mais no conjunto canônico:

        Canal           ('canais')  — removido: ver [4]
        MenuOpcao       ('menu_opcoes') — removido: ver [4]
        EmailEnviado    ('emails_enviados') — e-mail avulso da central de e-mail
        CampanhaContato ('campanha_contatos') — status por destinatário
        Arquivo         ('arquivos') — mídia da biblioteca de chat

[4] O QUE FOI REMOVIDO E POR QUÊ
--------------------------------
    `Canal` — a tabela `canais` era o eixo do modelo antigo: `Usuario.canal_id`
    e `Menu.canal_id` apontavam para ela, o que amarrava o atendente a UM
    canal único e deixava o canal sem a dimensão do contrato. Hoje o canal é um
    ITEM DO CONTRATO (`canais_contratados`) e o vínculo atendente↔canal é
    N:M decidido pelo gestor (`usuarios_canais`). Manter `canais` obrigaria
    ressuscitar as duas colunas que acabamos de remover.

    `MenuOpcao` — substituída por `MenuItem` (`menu_itens`), que já é o modelo
    canônico de opção de menu.
================================================================================
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
from app.models.contato_models import Contato
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


class Arquivo(Base):
    """Biblioteca de mídia do chat — arquivos trocados nos atendimentos, reutilizáveis em respostas."""

    __tablename__ = "arquivos"

    id = Column(Integer, primary_key=True, index=True)
    nome_original = Column(String(200), nullable=False)
    nome_arquivo = Column(String(200), nullable=False)  # uploads/arquivos/
    tipo_mime = Column(String(100))
    tamanho_bytes = Column(Integer)
    descricao = Column(String(300))
    atendimento_id = Column(Integer, ForeignKey("atendimentos.id"), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    atendimento = relationship("Atendimento")


__all__ = [
    # conjunto canônico
    "Atendimento", "AtendimentoContexto", "Assinatura", "Base", "Campanha",
    "CanalContratado", "ChamadaPABX", "Cliente", "Conexao", "Contato",
    "Departamento", "EmailLog", "EmailTemplate", "Empresa", "InstanciaChatbot",
    "Menu", "MenuItem", "ModeloMensagem", "NivelUsuario", "Pedido", "PedidoItem",
    "Roteiro", "Telefone", "TokenRevogado", "Transferencia", "Usuario",
    "UsuarioCanal",
    # legadas ainda em uso
    "Arquivo", "CampanhaContato", "EmailEnviado",
]
