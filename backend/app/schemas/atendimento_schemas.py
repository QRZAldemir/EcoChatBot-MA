"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Schemas · Atendimento
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     atendimento_schemas.py
@module   Backend / app/schemas
@author   Aldemir Queiroz
@since    2026
@version  3.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Contratos Pydantic do atendimento: filtro de listagem, criação, atualização
parcial, transferência, finalização com avaliação, resposta, indicadores e
o contexto de conversa da URA.

O QUE ESTE ARQUIVO É
───────────────────
O contrato entre os dois routers de atendimento e o `AtendimentoService`.
Ele é importado por módulo (`from app.schemas.atendimento_schemas import
...`), e não pelo pacote `app.schemas` — é uma das duas exceções do
projeto, junto com `auth_schemas`.

OS OBJETOS
──────────
    StatusAtendimento       enum str: ABERTO, FILA, EM_ATENDIMENTO,
                            FINALIZADO
    FiltroAtendimento       listagem: id, status, tipo_canal, departamento_id,
                            usuario_id, cliente_whatsapp, protocolo,
                            data_inicio, data_fim, ativo (default True).
                            `parse_date` converte texto ISO em datetime
    AtendimentoCreate       telefone_id, contato_id, canal_contratado_id e
                            protocolo obrigatórios; menu_item_id,
                            departamento_id, assunto, prioridade, origem,
                            resumo, observacoes opcionais
    AtendimentoUpdate       patch parcial; aceita `atendente_id`
    TransferenciaRequest    destino: usuario_id, departamento_id, canal_id,
                            menu_item_id, ramal_destino, mensagem, motivo
    AtendimentoTransferir   alias histórico de TransferenciaRequest
    AtendimentoFinalizar    avaliacao (1 a 5) e feedback
    AtendimentoResponse     contrato de saída + from_atendimento()
    AtendimentoDetalhado    response + tempo_espera_minutos e
                            tempo_atendimento_minutos
    AtendimentoIndicadores  contagens (total, aberto, fila, em_atendimento,
                            finalizado_humano, finalizado_sem_atendente),
                            por_departamento e dois tempos médios
    ContextoCreate           context_key + value (upsert de estado da URA)
    ContextoResponse         espelha as colunas do model: chave, valor,
                            pergunta, tipo, origem, ordem, obrigatorio,
                            validado, criado_em

O OBJETO MAIS IMPORTANTE: `from_atendimento`
────────────────────────────────────────────
    `AtendimentoResponse.from_atendimento(at)` monta o DTO na mão. Os nomes
    do DTO são os que o frontend já consome em
    `atendimento.service.ts::_normalizar` (`nome_contato`, `telefone`,
    `usuario_id`, `canal_id`), e vários não são colunas: vêm de
    relacionamento (`contato.nome`, `contato.telefone`) ou foram renomeados
    na modelagem (`atendente_id` → `usuario_id`).

POR QUE NÃO `model_validate(atendimento)`
─────────────────────────────────────────
O ORM não tem `telefone`, `nome_contato`, `usuario_id` nem `canal_id`. Com
`from_attributes=True` o Pydantic lê atributo por atributo e levanta
ValidationError no primeiro campo ausente — a lista inteira de atendimentos
quebraria. Por isso o acesso é `getattr(..., None)`: relacionamento lazy não
carregado não pode derrubar a listagem. Numa lista de 50, 50 queries a mais
(N+1) é lento; 50 exceções é indisponível.

POR QUE OS NOMES DE `AtendimentoCreate` SÃO EXATOS
──────────────────────────────────────────────────
O router faz `service.criar(**payload.model_dump())`, e a assinatura de
`AtendimentoService.criar` exige `telefone_id`, `contato_id`,
`canal_contratado_id` e `protocolo`. Qualquer outro nome aqui vira TypeError
na hora de criar, não na de documentar. Daí `tipo_canal` e `paciente_*` não
existirem mais: canal virou `CanalContratado` e cliente virou `Contato`.

POR QUE DOIS NOMES PARA TRANSFERIR
──────────────────────────────────
`AtendimentoTransferir` é alias de `TransferenciaRequest`: `tenant/
atendimentos.py` importa o primeiro, `atendimentos_routers.py` usa o segundo.
Manter os dois evita um segundo ciclo de import quebrado quando alguém tocar
no router do tenant.

POR QUE CONTEXTO USA DOIS IDIOMAS
────────────────────────────────
O model `AtendimentoContexto` chama as colunas de `chave` e `valor`, mas o
contrato HTTP de entrada usa `context_key` e `value` — é o que a tela envia.
A tradução fica no service. Nenhum dos lados foi renomeado: forçar um a usar
a palavra do outro só espalharia a divergência.

RELACIONAMENTO
──────────────
    app/routers/atendimentos_routers.py   AtendimentoCreate, AtendimentoResponse,
                                          AtendimentoUpdate, ContextoCreate,
                                          ContextoResponse, TransferenciaRequest
    app/routers/tenant/atendimentos.py     FiltroAtendimento, AtendimentoTransferir,
                                          AtendimentoFinalizar,
                                          AtendimentoDetalhado,
                                          AtendimentoIndicadores
    app/services/atendimento_service.py   implementa criar/atualizar/finalizar
    app/models/atendimento_models.py      colunas do ORM
    app/models/enums.py                   TipoCanalMensageria
    app/models/atendimento_context_models.py  colunas chave/valor
"""

from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import TipoCanalMensageria


# ============================================
# ENUMS LOCAIS
# ============================================

class StatusAtendimento(str, Enum):
    ABERTO = "aberto"
    FILA = "fila"
    EM_ATENDIMENTO = "em_atendimento"
    FINALIZADO = "finalizado"


# ============================================
# SCHEMAS DE FILTRO
# ============================================

class FiltroAtendimento(BaseModel):
    """
    Filtros para listagem de atendimentos.

    Usado por `app/routers/tenant/atendimentos.py`. O router principal
    (`atendimentos_routers.py`) declara `Query(...)` direto, porque os
    filtros dele são outro conjunto — são os que `AtendimentoService.listar`
    realmente aceita.
    """
    id: Optional[int] = None
    status: Optional[StatusAtendimento] = None
    tipo_canal: Optional[TipoCanalMensageria] = None
    departamento_id: Optional[int] = None
    usuario_id: Optional[int] = None
    cliente_whatsapp: Optional[str] = None
    protocolo: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    ativo: Optional[bool] = True

    @field_validator("data_inicio", "data_fim", mode="before")
    @classmethod
    def parse_date(cls, v):
        # Query string chega como texto. Sem isto, `data_inicio=2026-10-01`
        # derrubaria a requisição com 422 em vez de filtrar.
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v


# ============================================
# SCHEMAS DE CRIAÇÃO
# ============================================

class AtendimentoCreate(BaseModel):
    """
    Criação de atendimento.

    ─────────────────────────────────────────────────────────────────────
    POR QUE NÃO TEM `tipo_canal` NEM `paciente_*`
    ─────────────────────────────────────────────────────────────────────
    A versão 2.1.0 deste schema aceitava `tipo_canal`, `paciente_telefone`,
    `paciente_nome`, `paciente_email`. Nenhum desses existe mais: o canal
    virou `CanalContratado` e o cliente virou `Contato`.

    E o que decide é o service, não o histórico: `AtendimentoService.criar`
    exige, por assinatura, `telefone_id`, `contato_id`, `canal_contratado_id`
    e `protocolo`. Como o router faz `service.criar(**payload.model_dump())`,
    o schema precisa ter exatamente esses nomes — qualquer outro nome aqui
    vira `TypeError` na hora de criar, não na de documentar.
    """
    telefone_id: int = Field(..., description="Telefone que originou o contato")
    contato_id: int = Field(..., description="Contato que está sendo atendido")
    canal_contratado_id: int = Field(..., description="Canal contratado usado")
    protocolo: str = Field(..., min_length=1, max_length=40)

    menu_item_id: Optional[int] = Field(
        None, description="Opção de menu escolhida pelo cliente"
    )
    departamento_id: Optional[int] = Field(
        None, description="Departamento de destino"
    )
    assunto: Optional[str] = Field(None, max_length=200)
    prioridade: Optional[str] = None
    origem: Optional[str] = None
    resumo: Optional[str] = None
    observacoes: Optional[str] = None


# ============================================
# SCHEMAS DE ATUALIZAÇÃO
# ============================================

class AtendimentoUpdate(BaseModel):
    """
    Atualização parcial.

    `exclude_unset=True` no router faz o patch virar "só o que veio". Os
    nomes seguem as colunas de `Atendimento`; `atualizar()` recusa `id`,
    `empresa_id`, `created_at` e `deleted_at` no próprio service.
    """
    departamento_id: Optional[int] = None
    atendente_id: Optional[int] = None
    status: Optional[StatusAtendimento] = None
    assunto: Optional[str] = Field(None, max_length=200)
    prioridade: Optional[str] = None
    origem: Optional[str] = None
    resumo: Optional[str] = None
    observacoes: Optional[str] = None
    tags: Optional[str] = None


class TransferenciaRequest(BaseModel):
    """
    Destino de uma transferência.

    ─────────────────────────────────────────────────────────────────────
    POR QUE ESTE SCHEMA EXISTE SEPARADO
    ─────────────────────────────────────────────────────────────────────
    Porque `atendimentos_routers.transferir_atendimento` depende deste
    nome — e ele não estava importado. O módulo quebrava no import com
    `NameError`, muito depois de o `ImportError` do `FiltroAtendimento`
    ser resolvido.

    Os nomes seguem a coluna do model: o atendente é `atendente_id` no ORM,
    mas o contrato HTTP é `usuario_id`, e é o que a tela envia.
    """
    usuario_id: Optional[int] = Field(
        None, description="Atendente que recebe o atendimento"
    )
    departamento_id: Optional[int] = Field(
        None, description="Departamento de destino"
    )
    canal_id: Optional[int] = Field(
        None, description="Canal de destino"
    )
    menu_item_id: Optional[int] = Field(
        None, description="Opção de menu que originou a transferência"
    )
    ramal_destino: Optional[str] = Field(
        None, max_length=20, description="Ramal de destino em transferências VoIP"
    )
    mensagem: Optional[str] = Field(
        None, description="Mensagem enviada ao cliente ao mudar de atendente"
    )
    motivo: Optional[str] = Field(
        None, description="Justificativa — obrigatória quando quem redireciona é o atendente"
    )


class AtendimentoTransferir(TransferenciaRequest):
    """
    Alias histórico. `tenant/atendimentos.py` importa este nome; o router
    principal usa `TransferenciaRequest`. Manter os dois evita um segundo
    ciclo de import quebrado quando alguém tocar no router do tenant.
    """


class AtendimentoFinalizar(BaseModel):
    avaliacao: Optional[int] = Field(None, ge=1, le=5)
    feedback: Optional[str] = None


# ============================================
# SCHEMAS DE RESPOSTA
# ============================================

class AtendimentoResponse(BaseModel):
    """
    Contrato de resposta da API.

    ─────────────────────────────────────────────────────────────────────
    POR QUE OS NOMES NÃO SÃO OS DO ORM
    ─────────────────────────────────────────────────────────────────────
    Porque o frontend já consome estes nomes em `_normalizar`:

        nome_contato, telefone, usuario_id, canal_id, criado_em, atualizado_em

    Renomear para `atendente_id`/`contato_id` faria a tela mostrar `undefined`
    em toda coluna. O DTO é a fronteira: nomes da API de um lado, colunas
    do banco do outro, e a tradução em `from_atendimento`.
    """
    id: int
    protocolo: str
    status: str
    criado_em: datetime

    tipo_canal: Optional[TipoCanalMensageria] = None
    nome_contato: Optional[str] = None
    telefone: Optional[str] = None
    canal_id: Optional[int] = None
    departamento_id: Optional[int] = None
    usuario_id: Optional[int] = None
    assunto: Optional[str] = None
    prioridade: Optional[str] = None
    atualizado_em: Optional[datetime] = None
    iniciado_em: Optional[datetime] = None
    finalizado_em: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_atendimento(cls, at: Any) -> "AtendimentoResponse":
        """
        Monta o DTO a partir do ORM.

        ─────────────────────────────────────────────────────────────────────
        POR QUE NÃO `model_validate(atendimento)`
        ─────────────────────────────────────────────────────────────────────
        Porque `Atendimento` não tem `telefone`, `nome_contato`, `usuario_id`
        nem `canal_id` — ele tem `contato`, `atendente_id` e
        `canal_contratado_id`. Com `from_attributes=True`, o Pydantic lê
        atributo por atributo e estoura ValidationError no primeiro campo
        ausente — ou seja, a lista inteira de atendimentos quebraria.

        O acesso é por `getattr(..., None)` de propósito: relacionamento
        lazy não carregado não pode derrubar a listagem. Numa lista de 50
        atendimentos, 50 queries a mais (N+1) é lento; 50 exceções é
        indisponível. O relatório mostra o que houver.
        """
        contato = getattr(at, "contato", None)
        canal = getattr(at, "canal_contratado", None)
        return cls(
            id=at.id,
            protocolo=at.protocolo,
            status=at.status,
            criado_em=at.criado_em,
            tipo_canal=getattr(canal, "tipo", None),
            nome_contato=getattr(contato, "nome", None),
            telefone=getattr(contato, "telefone", None),
            canal_id=getattr(at, "canal_contratado_id", None),
            departamento_id=getattr(at, "departamento_id", None),
            usuario_id=getattr(at, "atendente_id", None),
            assunto=getattr(at, "assunto", None),
            prioridade=getattr(at, "prioridade", None),
            atualizado_em=getattr(at, "atualizado_em", None),
            iniciado_em=getattr(at, "iniciado_em", None),
            finalizado_em=getattr(at, "finalizado_em", None),
        )


class AtendimentoDetalhado(AtendimentoResponse):
    tempo_espera_minutos: Optional[float] = None
    tempo_atendimento_minutos: Optional[float] = None


class AtendimentoIndicadores(BaseModel):
    total: int
    aberto: int
    fila: int
    em_atendimento: int
    finalizado_humano: int
    finalizado_sem_atendente: int
    por_departamento: List[dict]
    tempo_medio_espera: Optional[float] = None
    tempo_medio_atendimento: Optional[float] = None

# ============================================
# CONTEXTO DA CONVERSA / URA
# ============================================
# O model `AtendimentoContexto` chama as colunas de `chave` e `valor`, mas o
# contrato HTTP usa `context_key` e `value` — é o que a tela envia. A tradução
# acontece no service, que recebe os nomes do HTTP e escreve os do banco.
# Nenhum dos dois lados foi renomeado: são idiomas diferentes, e forçar um a
# usar a palavra do outro só espalharia a divergência.

class ContextoCreate(BaseModel):
    """Upsert de uma variável de contexto (estado de URA, dado coletado)."""
    context_key: str = Field(..., min_length=1, max_length=80)
    value: Optional[str] = None


class ContextoResponse(BaseModel):
    """Contexto como sai da API, espelhando as colunas do model."""
    id: int
    atendimento_id: int
    chave: str
    valor: Optional[str] = None
    pergunta: Optional[str] = None
    tipo: Optional[str] = None
    origem: Optional[str] = None
    ordem: int = 0
    obrigatorio: bool = False
    validado: bool = False
    criado_em: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
