from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Cliente(Base):
    """Cliente/tenant que contratou o sistema (isolamento multi-tenant)."""
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    cnpj = Column(String(20), unique=True, index=True)
    email = Column(String(150), index=True)
    telefone = Column(String(20))
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    usuarios = relationship("Usuario", back_populates="cliente")
    atendimentos = relationship("Atendimento", back_populates="cliente")

class Atendimento(Base):
    __tablename__ = "atendimentos"

    id = Column(Integer, primary_key=True, index=True)
    protocolo = Column(String(50), unique=True, index=True)
    telefone = Column(String(20), nullable=False)
    nome_contato = Column(String(100))
    cliente_id = Column(Integer, ForeignKey("clientes.id"), index=True)

    # Relacionamento com cliente/tenant
    cliente = relationship("Cliente", back_populates="atendimentos")

    # ==================================================================
    # CORRIGIDO (2026-07-05): Resolução de conflito de nome de atributo
    # ==================================================================
    # PROBLEMA: Havia dois atributos com o mesmo nome 'canal':
    #   1. canal = Column(Integer) - tipo do canal (1=WhatsApp, 2=Interno)
    #   2. canal = relationship("Canal") - objeto Canal relacionado
    # O segundo sobrescrevia o primeiro, causando conflito de tipos no
    # schema Pydantic. O schema esperava int, mas ORM retornava objeto.
    #
    # SOLUÇÃO: Renomear a coluna para 'tipo_canal', mantendo o
    # relacionamento como 'canal'. Agora não há conflito.
    #
    # IMPACTO:
    # - ORM: tipo_canal (int) + canal (relationship)
    # - Pydantic: tipo_canal (int) + canal_id (int)
    # - Service: filtros atualizados para Atendimento.tipo_canal
    # ==================================================================
    tipo_canal = Column(Integer, default=1)     # Tipo de canal: 1=WhatsApp, 2=Interno
    canal_id = Column(Integer, ForeignKey("canais.id"))
    conexao_id = Column(Integer, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    departamento_id = Column(Integer, ForeignKey("departamentos.id"))
    tipo = Column(Integer, default=1)            # Tipo de atendimento: 1=automático, 2=manual
    ativo = Column(Boolean, default=True)
    status = Column(String(30), default="aberto")  # Status: aberto, fila, em_atendimento, finalizado
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamento com tabela 'canais' (via canal_id)
    # Uso: atendimento.canal.nome retorna o nome do canal
    canal = relationship("Canal")
    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    departamento = relationship("Departamento")
    contextos = relationship("AtendimentoContext", back_populates="atendimento", cascade="all, delete-orphan")


class AtendimentoContext(Base):
    __tablename__ = "atendimento_contextos"

    id = Column(Integer, primary_key=True, index=True)
    atendimento_id = Column(Integer, ForeignKey("atendimentos.id"), nullable=False)
    context_key = Column(String(100), nullable=False)
    value = Column(Text, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    atendimento = relationship("Atendimento", back_populates="contextos")


class NivelUsuario(Base):
    __tablename__ = "nivel_usuario"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(50), unique=True, nullable=False)  # atendente, supervisor, gerente, administrador
    descricao = Column(String(200))
    
    # Relacionamento com usuários
    usuarios = relationship("Usuario", back_populates="nivel")

class Departamento(Base):
    __tablename__ = "departamentos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), unique=True, nullable=False)
    descricao = Column(String(300))
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    usuarios = relationship("Usuario", back_populates="departamento")
    canais = relationship("Canal", back_populates="departamento")

class Canal(Base):
    __tablename__ = "canais"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), unique=True, nullable=False)
    descricao = Column(String(300))
    arquivo_menu = Column(String(200), nullable=False)  # Ex: 7portaria-ma.html
    departamento_id = Column(Integer, ForeignKey("departamentos.id"))
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    departamento = relationship("Departamento", back_populates="canais")
    usuarios = relationship("Usuario", back_populates="canal")
    menus = relationship("Menu", back_populates="canal")

class MenuOpcao(Base):
    __tablename__ = "menu_opcoes"

    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=False)
    titulo = Column(String(100), nullable=False)
    descricao = Column(String(300))
    row_id = Column(String(50), nullable=False)
    ordem = Column(Integer, default=0)

    menu = relationship("Menu", back_populates="opcoes")


class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(100), nullable=False)
    descricao = Column(String(300))
    rodape = Column(String(100))
    texto_botao = Column(String(50), default="Ver opções")
    canal_id = Column(Integer, ForeignKey("canais.id"))
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    opcoes = relationship("MenuOpcao", back_populates="menu", order_by="MenuOpcao.ordem")
    canal = relationship("Canal", back_populates="menus")


class ModeloMensagem(Base):
    __tablename__ = "modelos_mensagem"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String(100), nullable=False)  # nome para identificar a mensagem
    corpo = Column(Text, nullable=False)              # texto principal (memorando)
    arquivo = Column(String(300))                     # URL pública de anexo, opcional
    departamento_id = Column(Integer, ForeignKey("departamentos.id"))
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    departamento = relationship("Departamento")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), index=True)  # tenant (nullable p/ compatibilidade)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    telefone = Column(String(20))
    
    nivel_id = Column(Integer, ForeignKey("nivel_usuario.id"), nullable=False)
    departamento_id = Column(Integer, ForeignKey("departamentos.id"))
    canal_id = Column(Integer, ForeignKey("canais.id"))
    
    ativo = Column(Boolean, default=True)
    status = Column(String(20), default="ativo")  # ativo | inativo | bloqueado | convidado
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    cliente = relationship("Cliente", back_populates="usuarios")
    nivel = relationship("NivelUsuario", back_populates="usuarios")
    departamento = relationship("Departamento", back_populates="usuarios")
    canal = relationship("Canal", back_populates="usuarios")


class Conexao(Base):
    """Número WhatsApp (WABA) vinculado ao sistema via Evolution API.

    'padrao' marca qual conexão é o número administrativo principal da
    empresa — só uma pode ser padrão por vez (ver ConexaoService.tornar_padrao).
    """
    __tablename__ = "conexoes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)          # rótulo exibido, ex: "67 3416-7800 - Oficial"
    telefone = Column(String(20))
    tipo = Column(String(20), default="whatsapp")        # whatsapp (reservado p/ outros canais futuros)
    conexao = Column(String(30), default="waba")          # waba | qrcode
    atendimento = Column(String(20), default="automatico")  # automatico | manual
    status = Column(String(20), default="desconectada")   # conectada | desconectada | aguardando
    padrao = Column(Boolean, default=False, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    evolution_instance_name = Column(String(100))
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Contato(Base):
    """Agenda de clientes WhatsApp — base usada para disparo de Campanhas."""
    __tablename__ = "contatos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    telefone = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(100))
    empresa = Column(String(100))
    observacao = Column(String(300))
    origem = Column(String(20), default="manual")   # manual | atendimento
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    campanhas = relationship("CampanhaContato", back_populates="contato")


class EmailEnviado(Base):
    """Histórico de e-mails avulsos enviados pelo sistema (central de E-mail)."""
    __tablename__ = "emails_enviados"

    id = Column(Integer, primary_key=True, index=True)
    contato_id = Column(Integer, ForeignKey("contatos.id"), nullable=True)
    destinatario = Column(String(150), nullable=False)
    assunto = Column(String(200), nullable=False)
    corpo = Column(Text, nullable=False)
    status = Column(String(20), default="pendente")   # enviado | erro | simulado
    erro_mensagem = Column(String(300))
    enviado_em = Column(DateTime)
    criado_em = Column(DateTime, default=datetime.utcnow)

    contato = relationship("Contato")


class Campanha(Base):
    """Disparo em massa de mensagens WhatsApp para uma lista de Contatos."""
    __tablename__ = "campanhas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    mensagem = Column(Text, nullable=False)
    conexao_id = Column(Integer, ForeignKey("conexoes.id"), nullable=False)
    status = Column(String(20), default="rascunho")   # rascunho | enviando | concluida | erro
    total_contatos = Column(Integer, default=0)
    enviados = Column(Integer, default=0)
    falhas = Column(Integer, default=0)
    criado_em = Column(DateTime, default=datetime.utcnow)
    enviado_em = Column(DateTime)

    conexao = relationship("Conexao")
    contatos = relationship("CampanhaContato", back_populates="campanha", cascade="all, delete-orphan")


class CampanhaContato(Base):
    """Associação Campanha × Contato — status individual do disparo por destinatário."""
    __tablename__ = "campanha_contatos"

    id = Column(Integer, primary_key=True, index=True)
    campanha_id = Column(Integer, ForeignKey("campanhas.id"), nullable=False, index=True)
    contato_id = Column(Integer, ForeignKey("contatos.id"), nullable=False, index=True)
    status = Column(String(20), default="pendente")   # pendente | enviado | erro | simulado
    erro_mensagem = Column(String(300))
    enviado_em = Column(DateTime)

    campanha = relationship("Campanha", back_populates="contatos")
    contato = relationship("Contato", back_populates="campanhas")


class TokenRevogado(Base):
    """JWTs invalidados antes do vencimento natural — suporta o /auth/logout real.

    JWT é stateless por natureza; sem isso, um token roubado continuaria
    válido até expirar mesmo depois do usuário fazer logout. 'jti' é o
    identificador único gravado no payload do token (ver security.py).
    """
    __tablename__ = "tokens_revogados"

    jti = Column(String(36), primary_key=True)
    expira_em = Column(DateTime, nullable=False)   # cópia do "exp" do token — permite podar linhas antigas
    criado_em = Column(DateTime, default=datetime.utcnow)


class Arquivo(Base):
    """Biblioteca de mídia do chat — arquivos trocados nos atendimentos, reutilizáveis em respostas."""
    __tablename__ = "arquivos"

    id = Column(Integer, primary_key=True, index=True)
    nome_original = Column(String(200), nullable=False)
    nome_arquivo = Column(String(200), nullable=False)   # nome único no disco (uploads/arquivos/)
    tipo_mime = Column(String(100))
    tamanho_bytes = Column(Integer)
    descricao = Column(String(300))
    atendimento_id = Column(Integer, ForeignKey("atendimentos.id"), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    atendimento = relationship("Atendimento")
