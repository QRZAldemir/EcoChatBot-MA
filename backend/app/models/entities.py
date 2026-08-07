"""
app/models/entities.py
─────────────────────────────────────────────────────────────────
Define todas as tabelas do banco de dados usando SQLAlchemy ORM.

Entidades:
    Usuario         — usuários do sistema (atendentes, supervisores, admins)
    Instancia       — conexões WhatsApp registradas na Evolution API
    Mensagem        — mensagens enviadas e recebidas via WhatsApp
    MenuOpcao       — opções individuais de um menu interativo
    Menu            — menus interativos (listas) enviados via WhatsApp
    Modelo          — configurações de modelos de IA (DeepSeek, OpenAI, etc.)
    MensagemSistema — prompts de sistema usados para contextualizar a IA

Uso:
    from app.models.entities import Usuario, Instancia, Mensagem
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey,
    Integer, String, Text, Float,
)
from sqlalchemy.orm import relationship

# Base declarativa importada de database.py
from app.models.database import Base


# ══════════════════════════════════════════════════════════════
# ENUMS
# ══════════════════════════════════════════════════════════════

class NivelUsuarioEnum(str, enum.Enum):
    """Nível de acesso do usuário no sistema."""
    atendente   = "atendente"
    supervisor  = "supervisor"
    gerente     = "gerente"
    administrador = "administrador"


class StatusInstanciaEnum(str, enum.Enum):
    """Estado da conexão WhatsApp na Evolution API."""
    conectada     = "conectada"
    desconectada  = "desconectada"
    aguardando    = "aguardando"  # QR Code pendente


class DirecaoMensagemEnum(str, enum.Enum):
    """Indica se a mensagem foi enviada ou recebida."""
    entrada = "entrada"   # recebida do cliente
    saida   = "saida"     # enviada pelo sistema


class TipoMensagemEnum(str, enum.Enum):
    """Tipo de conteúdo da mensagem."""
    texto     = "texto"
    imagem    = "imagem"
    audio     = "audio"
    video     = "video"
    documento = "documento"
    menu      = "menu"
    template  = "template"


class StatusMensagemEnum(str, enum.Enum):
    """Status de entrega da mensagem."""
    pendente  = "pendente"
    enviada   = "enviada"
    entregue  = "entregue"
    lida      = "lida"
    erro      = "erro"


class ProvedorModeloEnum(str, enum.Enum):
    """Provedor do modelo de IA."""
    deepseek  = "deepseek"
    openai    = "openai"
    anthropic = "anthropic"


# ══════════════════════════════════════════════════════════════
# ENTIDADE: Usuario
# ══════════════════════════════════════════════════════════════

class Usuario(Base):
    """
    Representa um usuário do sistema EcoChatBot.

    Atendentes, supervisores e administradores que operam
    os atendimentos via WhatsApp.
    """
    __tablename__ = "usuarios"

    # ── Chave primária ────────────────────────────────────────
    id = Column(Integer, primary_key=True, index=True)

    # ── Dados pessoais ────────────────────────────────────────
    nome     = Column(String(100), nullable=False)
    email    = Column(String(100), unique=True, nullable=False, index=True)
    telefone = Column(String(20))

    # ── Autenticação ──────────────────────────────────────────
    senha_hash = Column(String(255), nullable=False)  # bcrypt hash

    # ── Controle de acesso ────────────────────────────────────
    nivel = Column(
        Enum(NivelUsuarioEnum),
        default=NivelUsuarioEnum.atendente,
        nullable=False,
    )

    # ── Status ───────────────────────────────────────────────
    ativo = Column(Boolean, default=True, nullable=False)

    # ── Timestamps ───────────────────────────────────────────
    criado_em     = Column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Usuario id={self.id} email={self.email} nivel={self.nivel}>"


# ══════════════════════════════════════════════════════════════
# ENTIDADE: Instancia
# ══════════════════════════════════════════════════════════════

class Instancia(Base):
    """
    Representa uma conexão WhatsApp registrada na Evolution API.

    Cada instância corresponde a um número de WhatsApp conectado.
    O campo 'nome' é o identificador usado nas chamadas à Evolution API.
    """
    __tablename__ = "instancias"

    # ── Chave primária ────────────────────────────────────────
    id = Column(Integer, primary_key=True, index=True)

    # ── Identificação ─────────────────────────────────────────
    nome      = Column(String(100), unique=True, nullable=False, index=True)  # nome na Evolution API
    descricao = Column(String(300))
    telefone  = Column(String(20))   # número WhatsApp associado (preenchido após conexão)

    # ── Configuração Evolution API ────────────────────────────
    evolution_instance_name = Column(String(100), nullable=False)  # nome exato na Evolution
    webhook_url = Column(String(500))   # URL que receberá os eventos desta instância

    # ── Estado da conexão ─────────────────────────────────────
    status = Column(
        Enum(StatusInstanciaEnum),
        default=StatusInstanciaEnum.desconectada,
        nullable=False,
    )

    # ── Status ───────────────────────────────────────────────
    ativo = Column(Boolean, default=True, nullable=False)

    # ── Timestamps ───────────────────────────────────────────
    criado_em     = Column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Relacionamentos ───────────────────────────────────────
    mensagens         = relationship("Mensagem", back_populates="instancia")
    menus             = relationship("Menu", back_populates="instancia")
    mensagens_sistema = relationship("MensagemSistema", back_populates="instancia")

    def __repr__(self) -> str:
        return f"<Instancia id={self.id} nome={self.nome} status={self.status}>"


# ══════════════════════════════════════════════════════════════
# ENTIDADE: Mensagem
# ══════════════════════════════════════════════════════════════

class Mensagem(Base):
    """
    Registra cada mensagem trafegada pelo sistema.

    Armazena tanto mensagens recebidas (entrada) quanto
    mensagens enviadas (saída) via Evolution API.
    O campo 'conteudo' armazena o payload em texto (JSON string
    para mensagens estruturadas como menus e templates).
    """
    __tablename__ = "mensagens"

    # ── Chave primária ────────────────────────────────────────
    id = Column(Integer, primary_key=True, index=True)

    # ── Instância de origem/destino ───────────────────────────
    instancia_id = Column(Integer, ForeignKey("instancias.id"), nullable=False, index=True)

    # ── Contato ───────────────────────────────────────────────
    telefone     = Column(String(20), nullable=False, index=True)
    nome_contato = Column(String(100))   # nome do contato no WhatsApp

    # ── Conteúdo ──────────────────────────────────────────────
    direcao  = Column(Enum(DirecaoMensagemEnum), nullable=False)
    tipo     = Column(Enum(TipoMensagemEnum), default=TipoMensagemEnum.texto, nullable=False)
    conteudo = Column(Text, nullable=False)   # texto ou JSON serializado

    # ── Rastreamento Evolution API ────────────────────────────
    evolution_message_id = Column(String(100), index=True)  # ID retornado pela Evolution

    # ── Status de entrega ─────────────────────────────────────
    status = Column(
        Enum(StatusMensagemEnum),
        default=StatusMensagemEnum.pendente,
        nullable=False,
    )

    # ── Timestamps ───────────────────────────────────────────
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # ── Relacionamentos ───────────────────────────────────────
    instancia = relationship("Instancia", back_populates="mensagens")

    def __repr__(self) -> str:
        return f"<Mensagem id={self.id} tipo={self.tipo} direcao={self.direcao} status={self.status}>"


# ══════════════════════════════════════════════════════════════
# ENTIDADE: MenuOpcao  (tabela de suporte para Menu)
# ══════════════════════════════════════════════════════════════

class MenuOpcao(Base):
    """
    Uma opção dentro de um menu interativo.

    Cada opção aparece como uma linha na lista enviada ao cliente.
    O campo 'row_id' é o identificador retornado quando o cliente
    seleciona a opção na conversa.
    """
    __tablename__ = "menu_opcoes"

    # ── Chave primária ────────────────────────────────────────
    id = Column(Integer, primary_key=True, index=True)

    # ── Vínculo com o menu pai ────────────────────────────────
    menu_id = Column(Integer, ForeignKey("menus.id", ondelete="CASCADE"), nullable=False)

    # ── Conteúdo da opção ─────────────────────────────────────
    titulo    = Column(String(100), nullable=False)
    descricao = Column(String(300))
    row_id    = Column(String(50), nullable=False)   # ID único retornado ao usuário selecionar

    # ── Ação associada (opcional) ─────────────────────────────
    acao = Column(String(200))   # ex: transferir_departamento:3, enviar_menu:5

    # ── Ordenação ─────────────────────────────────────────────
    ordem = Column(Integer, default=0, nullable=False)

    # ── Relacionamentos ───────────────────────────────────────
    menu = relationship("Menu", back_populates="opcoes")

    def __repr__(self) -> str:
        return f"<MenuOpcao id={self.id} row_id={self.row_id} titulo={self.titulo}>"


# ══════════════════════════════════════════════════════════════
# ENTIDADE: Menu
# ══════════════════════════════════════════════════════════════

class Menu(Base):
    """
    Menu interativo enviado ao cliente via WhatsApp.

    Utiliza o endpoint /message/sendList da Evolution API.
    Cada menu pode ter N opções (MenuOpcao) agrupadas em seções.
    O vínculo com Instancia é opcional — um menu pode ser
    reutilizado em múltiplas instâncias.
    """
    __tablename__ = "menus"

    # ── Chave primária ────────────────────────────────────────
    id = Column(Integer, primary_key=True, index=True)

    # ── Identificação interna ─────────────────────────────────
    nome = Column(String(100), nullable=False, unique=True)   # identificador interno

    # ── Conteúdo exibido ao cliente ───────────────────────────
    titulo      = Column(String(100), nullable=False)    # título do menu (header)
    descricao   = Column(String(300))                    # corpo da mensagem
    rodape      = Column(String(100))                    # rodapé exibido abaixo das opções
    texto_botao = Column(String(50), default="Ver opções")  # texto do botão que abre a lista

    # ── Instância vinculada (opcional) ───────────────────────
    instancia_id = Column(Integer, ForeignKey("instancias.id"), nullable=True)

    # ── Status ───────────────────────────────────────────────
    ativo     = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relacionamentos ───────────────────────────────────────
    instancia = relationship("Instancia", back_populates="menus")
    opcoes    = relationship(
        "MenuOpcao",
        back_populates="menu",
        order_by="MenuOpcao.ordem",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Menu id={self.id} nome={self.nome} opcoes={len(self.opcoes)}>"


# ══════════════════════════════════════════════════════════════
# ENTIDADE: Modelo
# ══════════════════════════════════════════════════════════════

class Modelo(Base):
    """
    Configuração de um modelo de IA utilizado pelo EcoChatBot.

    Permite cadastrar e alternar entre diferentes modelos e
    provedores (DeepSeek, OpenAI, Anthropic) sem alterar código.
    O campo 'modelo_id' é o identificador do modelo na API do provedor
    (ex: 'deepseek-chat', 'gpt-4o', 'claude-sonnet-4-6').
    """
    __tablename__ = "modelos"

    # ── Chave primária ────────────────────────────────────────
    id = Column(Integer, primary_key=True, index=True)

    # ── Identificação ─────────────────────────────────────────
    nome      = Column(String(100), nullable=False, unique=True)   # nome amigável interno
    provedor  = Column(Enum(ProvedorModeloEnum), nullable=False)   # deepseek | openai | anthropic
    modelo_id = Column(String(100), nullable=False)                # ex: "deepseek-chat"

    # ── Parâmetros de geração ─────────────────────────────────
    temperatura  = Column(Float, default=0.7)     # criatividade: 0.0 (preciso) a 1.0 (criativo)
    max_tokens   = Column(Integer, default=500)   # limite de tokens na resposta

    # ── Status ───────────────────────────────────────────────
    ativo     = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relacionamentos ───────────────────────────────────────
    mensagens_sistema = relationship("MensagemSistema", back_populates="modelo")

    def __repr__(self) -> str:
        return f"<Modelo id={self.id} provedor={self.provedor} modelo_id={self.modelo_id}>"


# ══════════════════════════════════════════════════════════════
# ENTIDADE: MensagemSistema
# ══════════════════════════════════════════════════════════════

class MensagemSistema(Base):
    """
    Prompt de sistema (system message) usado para contextualizar a IA.

    Cada MensagemSistema define o comportamento e a personalidade
    da IA em um determinado contexto (ex: triagem, agendamento, FAQ).
    É vinculada a um Modelo de IA e opcionalmente a uma Instância,
    permitindo comportamentos diferentes por canal de atendimento.

    Exemplo de conteúdo:
        'Você é um assistente virtual do Hospital Marcx.
         Responda sempre em português, de forma profissional e empática.
         Canal: Portaria. Não forneça diagnósticos médicos.'
    """
    __tablename__ = "mensagens_sistema"

    # ── Chave primária ────────────────────────────────────────
    id = Column(Integer, primary_key=True, index=True)

    # ── Identificação ─────────────────────────────────────────
    nome = Column(String(100), nullable=False, unique=True)   # ex: "triagem-portaria"

    # ── Conteúdo do prompt ────────────────────────────────────
    conteudo = Column(Text, nullable=False)   # system prompt completo enviado à IA

    # ── Modelo de IA vinculado ────────────────────────────────
    modelo_id = Column(Integer, ForeignKey("modelos.id"), nullable=False)

    # ── Instância vinculada (opcional) ───────────────────────
    # Se nulo, o prompt é global e pode ser usado em qualquer instância
    instancia_id = Column(Integer, ForeignKey("instancias.id"), nullable=True)

    # ── Status ───────────────────────────────────────────────
    ativo     = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relacionamentos ───────────────────────────────────────
    modelo    = relationship("Modelo", back_populates="mensagens_sistema")
    instancia = relationship("Instancia", back_populates="mensagens_sistema")

    def __repr__(self) -> str:
        return f"<MensagemSistema id={self.id} nome={self.nome} modelo_id={self.modelo_id}>"
