import re

from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Literal, Optional
from datetime import datetime

CorOpcao = Literal["verde", "azul", "vermelho", "amarelo", "roxo", "cinza"]


def _normalizar_descricao(cls, v: Optional[str]) -> Optional[str]:
    """Uppercase + trim; aceita apenas letras/números/espaço/underscore (com acentos)."""
    if v is None:
        return v
    v = v.strip().upper()
    if v and not re.match(r'^[\w\s]+$', v, re.UNICODE):
        raise ValueError('Descrição deve conter apenas letras, números, espaços e underscore')
    return v

# ━━━ Menu Item (opção do menu) ━━━━━━━━━━━━━━━━━━━━━━━━━━
# `row_id` do schema antigo virou `atalho`; `cor` saiu porque a cor passou a
# ser deduce da cor do botão desenhada no front, e `departamento_id` passou a
# ser obrigatório porque TODA opção do menu tem que dizer quem atende.
class MenuItemBase(BaseModel):
    titulo: str
    descricao: Optional[str] = None
    atalho: Optional[str] = None
    ordem: int = 0
    departamento_id: int
    roteiro_id: Optional[int] = None
    transfere_direto: bool = False
    ativo: bool = True

class MenuItemCreate(MenuItemBase):
    pass

class MenuItemUpsert(MenuItemBase):
    id: Optional[int] = None

class MenuItemUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    atalho: Optional[str] = None
    ordem: Optional[int] = None
    departamento_id: Optional[int] = None
    roteiro_id: Optional[int] = None
    transfere_direto: Optional[bool] = None
    ativo: Optional[bool] = None

class MenuItemResponse(MenuItemBase):
    id: int
    menu_id: int
    criado_em: datetime

    class Config:
        from_attributes = True

# ━━━ Menu ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Alinhado ao model canônico `Menu`: o menu pertence à EMPRESA e, quando há
# `canal_contratado_id`, é o menu específico daquele canal. Sem esse campo é
# o menu principal (hub). `usuario_vinculado_id` saiu: quem atende é sempre um
# DEPARTAMENTO, resolvido em `MenuItem.departamento_id`.
class MenuBase(BaseModel):
    nome: str
    saudacao: Optional[str] = None
    rodape: Optional[str] = None
    tempo_espera_seg: int = 300
    tentativas_max: int = 3
    canal_contratado_id: Optional[int] = None
    ativo: bool = True
    criado_em: datetime

    _normalizar_nome = field_validator('nome')(_normalizar_descricao)

class MenuCreate(MenuBase):
    itens: List[MenuItemCreate] = []
    fallback_departamento_id: Optional[int] = None

class MenuUpdate(BaseModel):
    nome: Optional[str] = None
    saudacao: Optional[str] = None
    rodape: Optional[str] = None
    tempo_espera_seg: Optional[int] = None
    tentativas_max: Optional[int] = None
    canal_contratado_id: Optional[int] = None
    fallback_departamento_id: Optional[int] = None
    ativo: Optional[bool] = None
    itens: Optional[List[MenuItemUpsert]] = None

    _normalizar_nome = field_validator('nome')(_normalizar_descricao)

class MenuResponse(MenuBase):
    id: int
    empresa_id: int
    itens: List[MenuItemResponse] = []

class NivelUsuarioBase(BaseModel):
    nome: str
    descricao: Optional[str] = None

class NivelUsuarioCreate(NivelUsuarioBase):
    pass

class NivelUsuarioResponse(NivelUsuarioBase):
    id: int

    class Config:
        from_attributes = True

# ━━━ Departamento ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class DepartamentoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    ativo: bool = True

class DepartamentoCreate(DepartamentoBase):
    pass

class DepartamentoUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    ativo: Optional[bool] = None

class DepartamentoResponse(DepartamentoBase):
    id: int
    criado_em: datetime

    class Config:
        from_attributes = True

# ━━━ Canal Contratado ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# O canal deixou de ser um registro solto: ele é um ITEM DO CONTRATO da
# empresa. Por isso `telefone_id` e `tipo` são obrigatórios — todo canal
# precisa de um telefone que o sustente, e o tipo é a escolha da empresa.
class CanalContratadoBase(BaseModel):
    tipo: str
    telefone_id: int
    apelido: Optional[str] = None
    credenciais: Optional[str] = None
    webhook_token: Optional[str] = None
    webhook_url: Optional[str] = None
    horario_inicio: Optional[str] = None
    horario_fim: Optional[str] = None
    dias_semana: Optional[str] = None
    ativo: bool = True

class CanalContratadoCreate(CanalContratadoBase):
    empresa_id: int

class CanalContratadoUpdate(BaseModel):
    tipo: Optional[str] = None
    telefone_id: Optional[int] = None
    apelido: Optional[str] = None
    credenciais: Optional[str] = None
    webhook_token: Optional[str] = None
    webhook_url: Optional[str] = None
    horario_inicio: Optional[str] = None
    horario_fim: Optional[str] = None
    dias_semana: Optional[str] = None
    ativo: Optional[bool] = None

class CanalContratadoResponse(CanalContratadoBase):
    id: int
    empresa_id: int
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True

# Resumo usado dentro do cadastro do atendente, onde a lista de canais é longa.
class CanalContratadoResumo(BaseModel):
    id: int
    tipo: str
    apelido: Optional[str] = None
    principal: bool = False

    class Config:
        from_attributes = True

# ━━━ Conexao (painel WhatsApp/WABA) ━━━━━━━━━━━━━━━━━━━━━━━
class ConexaoBase(BaseModel):
    nome: str
    telefone: Optional[str] = None
    tipo: str = "whatsapp"
    conexao: str = "waba"
    atendimento: str = "automatico"
    ativo: bool = True

class ConexaoCreate(ConexaoBase):
    pass

class ConexaoUpdate(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    atendimento: Optional[str] = None
    ativo: Optional[bool] = None

class ConexaoResponse(ConexaoBase):
    id: int
    status: str
    padrao: bool
    criado_em: datetime
    fila: int = 0
    recebimento_min: int = 0

    class Config:
        from_attributes = True

class ConexaoQRCodeResponse(BaseModel):
    conexao: ConexaoResponse
    qrcode_base64: Optional[str] = None
    pairing_code: Optional[str] = None
    simulado: bool = False
    mensagem: Optional[str] = None

# ━━━ Contato (agenda de clientes WhatsApp) ━━━━━━━━━━━━━━━━━
class ContatoBase(BaseModel):
    nome: str
    telefone: str
    email: Optional[str] = None
    empresa: Optional[str] = None
    observacao: Optional[str] = None
    ativo: bool = True

class ContatoCreate(ContatoBase):
    pass

class ContatoUpdate(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    empresa: Optional[str] = None
    observacao: Optional[str] = None
    ativo: Optional[bool] = None

class ContatoResponse(ContatoBase):
    id: int
    origem: str
    criado_em: datetime

    class Config:
        from_attributes = True

# ━━━ E-mail (central de e-mail — compõe e envia, guarda histórico) ━
class EmailEnviarDTO(BaseModel):
    destinatario: str
    assunto: str
    corpo: str
    contato_id: Optional[int] = None

class EmailResponse(BaseModel):
    id: int
    contato_id: Optional[int] = None
    destinatario: str
    assunto: str
    corpo: str
    status: str
    erro_mensagem: Optional[str] = None
    enviado_em: Optional[datetime] = None
    criado_em: datetime

    class Config:
        from_attributes = True

# ━━━ Campanha (disparo em massa WhatsApp) ━━━━━━━━━━━━━━━━━━
class CampanhaContatoResponse(BaseModel):
    id: int
    contato_id: int
    status: str
    erro_mensagem: Optional[str] = None
    enviado_em: Optional[datetime] = None
    contato: Optional[ContatoResponse] = None

    class Config:
        from_attributes = True

class CampanhaCreate(BaseModel):
    nome: str
    mensagem: str
    conexao_id: int
    contato_ids: List[int]

class CampanhaResponse(BaseModel):
    id: int
    nome: str
    mensagem: str
    conexao_id: int
    status: str
    total_contatos: int
    enviados: int
    falhas: int
    criado_em: datetime
    enviado_em: Optional[datetime] = None

    class Config:
        from_attributes = True

class CampanhaDetalheResponse(CampanhaResponse):
    contatos: List[CampanhaContatoResponse] = []

# ━━━ Arquivo (biblioteca de mídia do chat) ━━━━━━━━━━━━━━━━━
class ArquivoResponse(BaseModel):
    id: int
    nome_original: str
    tipo_mime: Optional[str] = None
    tamanho_bytes: Optional[int] = None
    descricao: Optional[str] = None
    atendimento_id: Optional[int] = None
    criado_em: datetime

    class Config:
        from_attributes = True

# ━━━ Modelo de Mensagem (mensagem padrão / memorando) ━━━━━━
class ModeloMensagemBase(BaseModel):
    descricao: str
    corpo: str
    arquivo: Optional[str] = None
    departamento_id: Optional[int] = None
    ativo: bool = True

    _normalizar_descricao = field_validator('descricao')(_normalizar_descricao)

class ModeloMensagemCreate(ModeloMensagemBase):
    pass

class ModeloMensagemUpdate(BaseModel):
    descricao: Optional[str] = None
    corpo: Optional[str] = None
    arquivo: Optional[str] = None
    departamento_id: Optional[int] = None
    ativo: Optional[bool] = None

    _normalizar_descricao = field_validator('descricao')(_normalizar_descricao)

class ModeloMensagemResponse(ModeloMensagemBase):
    id: int
    criado_em: datetime
    departamento: Optional[DepartamentoResponse] = None

    class Config:
        from_attributes = True

# ━━━ Usuario ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr
    telefone: Optional[str] = None
    nivel_id: int
    departamento_id: Optional[int] = None
    ativo: bool = True

class UsuarioCreate(UsuarioBase):
    senha: str

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    nivel_id: Optional[int] = None
    departamento_id: Optional[int] = None
    ativo: Optional[bool] = None
    senha: Optional[str] = None

class UsuarioResponse(UsuarioBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime
    nivel: Optional[NivelUsuarioResponse] = None
    departamento: Optional[DepartamentoResponse] = None

    class Config:
        from_attributes = True

class UsuarioListItem(BaseModel):
    id: int
    nome: str
    email: str
    telefone: Optional[str] = None
    ativo: bool
    nivel_nome: Optional[str] = None
    departamento_nome: Optional[str] = None

    class Config:
        from_attributes = True


# ══════════════════════════════════════════════════════════════════════════
# COMPATIBILIDADE
# `Canal*` e `MenuOpcao*` passaram a se chamar `CanalContratado*` e
# `MenuItem*`. Os nomes antigos ficam como apelido temporário para não quebrar
# imports de uma vez; podem ser removidos quando a migração terminar.
# ══════════════════════════════════════════════════════════════════════════
CanalBase = CanalContratadoBase
CanalCreate = CanalContratadoCreate
CanalUpdate = CanalContratadoUpdate
CanalResponse = CanalContratadoResponse
MenuOpcaoBase = MenuItemBase
MenuOpcaoCreate = MenuItemCreate
MenuOpcaoUpsert = MenuItemUpsert
MenuOpcaoUpdate = MenuItemUpdate
MenuOpcaoResponse = MenuItemResponse
