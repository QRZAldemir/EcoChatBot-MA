import re

from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Literal, Optional
from datetime import datetime

from app.models.enums import TipoMensagem

CorOpcao = Literal["verde", "azul", "vermelho", "amarelo", "roxo", "cinza"]


def _normalizar_descricao(cls, v: Optional[str]) -> Optional[str]:
    """Uppercase + trim; aceita apenas letras/números/espaço/underscore (com acentos)."""
    if v is None:
        return v
    v = v.strip().upper()
    if v and not re.match(r'^[\w\s]+$', v, re.UNICODE):
        raise ValueError('Descrição deve conter apenas letras, números, espaços e underscore')
    return v

def _normalizar_chave(cls, v: Optional[str]) -> Optional[str]:
    """Uppercase + trim; aceita letras/números/ponto/hífen/underscore.

    Própria, e não `_normalizar_descricao`: aquela restringe a `\w`+espaço e a
    mensagem de erro diz "Descrição", que mentiria ao validar uma chave.
    """
    if v is None:
        return v
    v = v.strip().upper()
    if v and not re.match(r'^[\w.\-]+$', v, re.UNICODE):
        raise ValueError(
            'Chave deve conter apenas letras, números, ponto, hífen ou underscore'
        )
    return v

_RE_E164 = re.compile(r"^\+[1-9]\d{1,14}$")


def _validar_e164(cls, v: Optional[str]) -> Optional[str]:
    """E.164 estrito, como o Chatwoot faz: `+`, 1-9, ate 15 digitos.

    Sem o `+` ou com `00`/`(11)` nao entra: o identificador do canal e a chave
    de deduplicacao do contato, e `1199999999` e `+5511999999999` seriam duas
    pessoas diferentes no mesmo numero.
    """
    if v is None or v == "":
        return v
    v = v.strip()
    if not _RE_E164.match(v):
        raise ValueError(
            f"'{v}' nao e E.164. Use +<pais><numero>, ex: +5511988887777"
        )
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
# Contato (agenda de clientes WhatsApp)
# ALINHADO AO MODEL CANONICO `Contato`.
#   Sai `empresa` (str): colidia com o TENANT `Empresa`; o tenant vem do token.
#   Sai `ativo`: `Contato` nao tem essa coluna - desativar e soft delete
#   (`deleted_at`).
#   Sai `observacao`: a coluna chama `notas`.
#   Sai `origem` (so no Response): nao existe no model.
class ContatoBase(BaseModel):
    nome: str
    telefone: Optional[str] = None
    email: Optional[str] = None
    notas: Optional[str] = None
    tags: Optional[str] = None
    apelido: Optional[str] = None
    # Identidade canonica por canal esta em `ContatoCanal`; estes dois sao so
    # atalho de leitura. Contato SEM canal e valido (lead de campanha).
    canal_tipo: Optional[str] = None
    canal_identificador: Optional[str] = None

    _e164 = field_validator("telefone", "canal_identificador")(_validar_e164)


class ContatoCanalBase(BaseModel):
    canal_contratado_id: int
    identificador: str
    push_name: Optional[str] = None

    _e164 = field_validator("identificador")(_validar_e164)


class ContatoCanalCreate(ContatoCanalBase):
    pass

class ContatoCanalResponse(ContatoCanalBase):
    id: int
    contato_id: int

    class Config:
        from_attributes = True

class ContatoCreate(ContatoBase):
    """`empresa_id` NAO e campo: o tenant vem do token.

    `canais` vincula o contato a um ou mais canais contratados ja na criacao.
    Sem isso todo contato nasceria orfao e o webhook nao saberia onde grava-lo.
    """
    canais: List[ContatoCanalCreate] = []

class ContatoUpdate(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    notas: Optional[str] = None
    tags: Optional[str] = None
    apelido: Optional[str] = None

class ContatoResponse(ContatoBase):
    id: int
    empresa_id: int
    criado_em: datetime
    ultima_interacao: Optional[datetime] = None
    canais: List[ContatoCanalResponse] = []

    class Config:
        from_attributes = True

class ContatoCanalResolvido(BaseModel):
    """Contato localizado a partir de uma mensagem recebida num canal.

    E o que o webhook precisa: dado `canal_contratado_id` + `identificador`,
    devolve o contato e a empresa dona. O escopo vem SEMPRE por
    `contatos.empresa_id` (join) - `contato_canais` nao tem `empresa_id` de
    proposito, e por isso todo acesso a esta tabela precisa passar por ele.
    """
    contato_id: int
    empresa_id: int
    nome: Optional[str] = None


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
# Modelo de Mensagem (mensagem padrao / memorando)
# ALINHADO AO MODEL CANONICO `ModeloMensagem`.
#   Sai `corpo`: o model chama `conteudo` (e NOT NULL).
#   Sai `arquivo`: nao existe no model.
#   Sai `departamento_id` / `departamento`: nao existe no model. Departamento e
#   do MENU ITEM (`MenuItem.departamento_id`), nao do modelo de mensagem.
#   Entra `chave` (NOT NULL, e por ela que a campanha acha o modelo), `nome`
#   (NOT NULL) e `tipo` (NOT NULL, enum `TipoMensagem`).
class ModeloMensagemBase(BaseModel):
    chave: str
    nome: str
    conteudo: str
    descricao: Optional[str] = None
    tipo: TipoMensagem = TipoMensagem.TEXTO
    variaveis: Optional[str] = None
    canal_tipo: Optional[str] = None
    ativo: bool = True

    # A chave e normalizada em maiusculo: e por ela que `Campanha` faz lookup
    # (`modelo_mensagem_chave="promo_black_friday"`), entao "Promo" e
    # "PROMO" precisam colidir no mesmo lugar.
    _normalizar_chave = field_validator("chave")(_normalizar_chave)

class ModeloMensagemCreate(ModeloMensagemBase):
    pass

class ModeloMensagemUpdate(BaseModel):
    chave: Optional[str] = None
    nome: Optional[str] = None
    conteudo: Optional[str] = None
    descricao: Optional[str] = None
    tipo: Optional[TipoMensagem] = None
    variaveis: Optional[str] = None
    canal_tipo: Optional[str] = None
    ativo: Optional[bool] = None

    _normalizar_chave = field_validator("chave")(_normalizar_chave)

class ModeloMensagemResponse(ModeloMensagemBase):
    id: int
    empresa_id: int
    criado_em: datetime

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
