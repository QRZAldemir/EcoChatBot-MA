from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# ━━━ Menu Opcao ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class MenuOpcaoBase(BaseModel):
    titulo: str
    descricao: Optional[str] = None
    row_id: str
    ordem: int = 0

class MenuOpcaoCreate(MenuOpcaoBase):
    pass

class MenuOpcaoUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    row_id: Optional[str] = None
    ordem: Optional[int] = None

class MenuOpcaoResponse(MenuOpcaoBase):
    id: int
    menu_id: int

    class Config:
        from_attributes = True

# ━━━ Menu ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class MenuBase(BaseModel):
    titulo: str
    descricao: Optional[str] = None
    rodape: Optional[str] = None
    texto_botao: str = "Ver opções"
    canal_id: Optional[int] = None
    ativo: bool = True

class MenuCreate(MenuBase):
    opcoes: List[MenuOpcaoCreate] = []

class MenuUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    rodape: Optional[str] = None
    texto_botao: Optional[str] = None
    canal_id: Optional[int] = None
    ativo: Optional[bool] = None

class MenuResponse(MenuBase):
    id: int
    criado_em: datetime
    opcoes: List[MenuOpcaoResponse] = []

    class Config:
        from_attributes = True

# ━━━ Nível Usuario ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

# ━━━ Canal ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class CanalBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    arquivo_menu: str
    departamento_id: Optional[int] = None
    ativo: bool = True

class CanalCreate(CanalBase):
    pass

class CanalUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    arquivo_menu: Optional[str] = None
    departamento_id: Optional[int] = None
    ativo: Optional[bool] = None

class CanalResponse(CanalBase):
    id: int
    criado_em: datetime
    departamento: Optional[DepartamentoResponse] = None

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

class ModeloMensagemCreate(ModeloMensagemBase):
    pass

class ModeloMensagemUpdate(BaseModel):
    descricao: Optional[str] = None
    corpo: Optional[str] = None
    arquivo: Optional[str] = None
    departamento_id: Optional[int] = None
    ativo: Optional[bool] = None

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
    canal_id: Optional[int] = None
    ativo: bool = True

class UsuarioCreate(UsuarioBase):
    senha: str

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    nivel_id: Optional[int] = None
    departamento_id: Optional[int] = None
    canal_id: Optional[int] = None
    ativo: Optional[bool] = None
    senha: Optional[str] = None

class UsuarioResponse(UsuarioBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime
    nivel: Optional[NivelUsuarioResponse] = None
    departamento: Optional[DepartamentoResponse] = None
    canal: Optional[CanalResponse] = None

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
    canal_nome: Optional[str] = None

    class Config:
        from_attributes = True
