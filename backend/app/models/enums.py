"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Enumerações do Domínio
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     enums.py
@module   Backend / App / Models / Enums
@author   Aldemir Queiroz
@since    2026
@version  2.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Centraliza TODOS os enums do domínio. Cada enum herda de `BaseStrEnum`
(str, Enum), o que permite:

    • Serialização direta em JSON (vira string)
    • Comparação com strings ("aguardando" == StatusAtendimento.AGUARDANDO)
    • Uso em colunas VARCHAR (sem criar TYPE no PostgreSQL)

POR QUE UM ARQUIVO ÚNICO?
─────────────────────────
Evita o problema clássico de importação circular: `atendimento_models`
precisa de `StatusAtendimento`, `campanha_models` precisa de
`StatusCampanha`, e ambos podem precisar um do outro no futuro.

USO
───
    from app.models.enums import StatusAtendimento
    atendimento.status = StatusAtendimento.EM_ANDAMENTO.value  # "em_andamento"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations

from enum import Enum


class BaseStrEnum(str, Enum):
    """Enum base que serializa como string em JSON e aceita comparação direta."""

    def __str__(self) -> str:  # pragma: no cover
        return self.value


# ═══════════════════════════════════════════════════════════════════════════
# 1. TENANT / EMPRESA / USUÁRIO
# ═══════════════════════════════════════════════════════════════════════════

class StatusTenant(BaseStrEnum):
    """Situação do Cliente (tenant raiz) na plataforma."""
    ATIVO    = "ativo"
    INATIVO  = "inativo"
    TRIAL    = "trial"
    SUSPENSO = "suspenso"
    CANCELADO = "cancelado"


class PlanoTenant(BaseStrEnum):
    """Plano comercial do tenant."""
    FREE       = "free"
    BASIC      = "basic"
    PRO        = "pro"
    ENTERPRISE = "enterprise"


class PerfilUsuario(BaseStrEnum):
    """Perfil de acesso no sistema."""
    SUPER_ADMIN = "super_admin"   # dono da plataforma
    ADMIN       = "admin"         # admin do tenant/empresa
    GESTOR      = "gestor"        # supervisor de departamento
    ATENDENTE   = "atendente"     # operador de chat
    BOT         = "bot"           # instância automatizada
    API         = "api"           # integração externa


# ═══════════════════════════════════════════════════════════════════════════
# 2. CANAIS DE MENSAGERIA (transporte: por onde a mensagem chega)
# ═══════════════════════════════════════════════════════════════════════════

class TipoCanalMensageria(BaseStrEnum):
    """
    ⚠️ IMPORTANTE: NÃO confundir com `TipoAtendimento` (menu).

    Este enum representa o TRANSPORTE da mensagem — o "cano" físico.
    """
    WHATSAPP  = "whatsapp"
    TELEGRAM  = "telegram"
    DISCORD   = "discord"
    INSTAGRAM = "instagram"
    FACEBOOK  = "facebook"
    PABX      = "pabx"       # VoIP / Asterisk / MicroSIP
    EMAIL     = "email"
    WEBCHAT   = "webchat"
    SMS       = "sms"


class StatusConexao(BaseStrEnum):
    """Estado do socket/sessão com o provedor do canal."""
    DESCONECTADO = "desconectado"
    CONECTANDO   = "conectando"
    CONECTADO    = "conectado"
    RECONECTANDO = "reconectando"
    ERRO         = "erro"
    BLOQUEADO    = "bloqueado"


# ═══════════════════════════════════════════════════════════════════════════
# 3. ATENDIMENTO
# ═══════════════════════════════════════════════════════════════════════════

class StatusAtendimento(BaseStrEnum):
    """Ciclo de vida do atendimento no painel."""
    AGUARDANDO   = "aguardando"     # sem atendente designado
    EM_ANDAMENTO = "em_andamento"   # atendente conduzindo
    PAUSADO      = "pausado"
    TRANSFERIDO  = "transferido"
    FINALIZADO   = "finalizado"
    CANCELADO    = "cancelado"


class PrioridadeAtendimento(BaseStrEnum):
    BAIXA   = "baixa"
    NORMAL  = "normal"
    ALTA    = "alta"
    URGENTE = "urgente"


class OrigemAtendimento(BaseStrEnum):
    """Como o atendimento foi iniciado."""
    BOT      = "bot"        # fluxo automático do menu
    USUARIO  = "usuario"    # cliente procurou diretamente
    API      = "api"        # integração externa
    CAMPANHA = "campanha"   # disparo de marketing


class MotivoAlerta(BaseStrEnum):
    """
    Alertas exibidos no painel analítico (conforme README, seção 10).
    """
    FORA_EXPEDIENTE   = "fora_expediente"
    SEM_ROTEAMENTO    = "sem_roteamento"
    PENDENCIA_24H     = "pendencia_24h"
    SEM_RESPONSAVEL   = "sem_responsavel"


# ═══════════════════════════════════════════════════════════════════════════
# 4. MENSAGEM
# ═══════════════════════════════════════════════════════════════════════════

class TipoMensagem(BaseStrEnum):
    TEXTO       = "texto"
    IMAGEM      = "imagem"
    AUDIO       = "audio"
    VIDEO       = "video"
    DOCUMENTO   = "documento"
    LOCALIZACAO = "localizacao"
    BOTAO       = "botao"
    LISTA       = "lista"
    TEMPLATE    = "template"


class DirecaoMensagem(BaseStrEnum):
    ENTRADA = "entrada"   # recebida do cliente
    SAIDA   = "saida"     # enviada pelo bot/atendente


class StatusMensagem(BaseStrEnum):
    PENDENTE = "pendente"
    ENVIADA  = "enviada"
    ENTREGUE = "entregue"
    LIDA     = "lida"
    FALHA    = "falha"


# ═══════════════════════════════════════════════════════════════════════════
# 5. ROTEIRO / MENU
# ═══════════════════════════════════════════════════════════════════════════

class TipoPergunta(BaseStrEnum):
    """Tipo de campo extraído do HTML do roteiro."""
    TEXTO     = "texto"
    NUMERO    = "numero"
    EMAIL     = "email"
    TELEFONE  = "telefone"
    DATA      = "data"
    SELECT    = "select"
    MULTIPLA  = "multipla"
    SIM_NAO   = "sim_nao"
    ARQUIVO   = "arquivo"


class StatusRoteiro(BaseStrEnum):
    RASCUNHO = "rascunho"
    ATIVO    = "ativo"
    INATIVO  = "inativo"
    ARQUIVADO = "arquivado"


# ═══════════════════════════════════════════════════════════════════════════
# 6. CHAMADA PABX
# ═══════════════════════════════════════════════════════════════════════════

class StatusChamada(BaseStrEnum):
    # O primeiro valor PRECISA ser "iniciando": é o DEFAULT da coluna no banco
    # (migration 004). Antes o enum começava em "iniciada", e qualquer INSERT
    # que não informasse status recebia "iniciando" do Postgres — valor que
    # não existia aqui. O registro ficava gravado, ninguém via erro, e toda
    # consulta filtrando por INICIADA não encontrava a linha.
    INICIANDO   = "iniciando"
    TOCANDO     = "tocando"
    ATENDIDA    = "atendida"
    PERDIDA     = "perdida"
    TRANSFERIDA = "transferida"
    FINALIZADA  = "finalizada"
    FALHA       = "falha"


class TipoChamada(BaseStrEnum):
    ENTRADA = "entrada"
    SAIDA   = "saida"
    INTERNA = "interna"


# ═══════════════════════════════════════════════════════════════════════════
# 7. CAMPANHA / PEDIDO
# ═══════════════════════════════════════════════════════════════════════════

class StatusCampanha(BaseStrEnum):
    RASCUNHO    = "rascunho"
    AGENDADA    = "agendada"
    EM_EXECUCAO = "em_execucao"
    PAUSADA     = "pausada"
    CONCLUIDA   = "concluida"
    CANCELADA   = "cancelada"


class StatusPedido(BaseStrEnum):
    CRIADO     = "criado"
    CONFIRMADO = "confirmado"
    EM_PREPARO = "em_preparo"
    ENVIADO    = "enviado"
    ENTREGUE   = "entregue"
    CANCELADO  = "cancelado"


# ═══════════════════════════════════════════════════════════════════════════
# 8. E-MAIL
# ═══════════════════════════════════════════════════════════════════════════

class StatusEmail(BaseStrEnum):
    PENDENTE = "pendente"
    ENVIADO  = "enviado"
    ENTREGUE = "entregue"
    ABERTO   = "aberto"
    CLICADO  = "clicado"
    BOUNCE   = "bounce"
    FALHA    = "falha"


# ═══════════════════════════════════════════════════════════════════════════
# 9. TOKEN REVOGADO (blacklist JWT)
# ═══════════════════════════════════════════════════════════════════════════

class MotivoRevogacao(BaseStrEnum):
    LOGOUT    = "logout"
    EXPIRADO  = "expirado"
    ROTACAO   = "rotacao"
    SEGURANCA = "seguranca"
    ADMIN     = "admin"


# ═══════════════════════════════════════════════════════════════════════════
# 9. CONTRATAÇÃO
# ═══════════════════════════════════════════════════════════════════════════

class StatusAssinatura(BaseStrEnum):
    """
    Situação comercial da assinatura da Empresa.

    ⚠️ ESTRUTURA SEM REGRA DE COBRANÇA: os valores monetários e o cálculo
    de mensalidade por canal contratado ainda NÃO foram definidos pelo
    negócio. O que existe aqui é o espaço para registrar o contrato.
    """
    TRIAL      = "trial"
    ATIVA      = "ativa"
    INADIMPLENTE = "inadimplente"
    SUSPENSA   = "suspensa"
    CANCELADA  = "cancelada"


class TipoTransferencia(BaseStrEnum):
    """
    O que originou a transferência do atendimento.

    MENU     → o cliente escolheu uma opção do MenuItem (pode ter errado)
    ATENDENTE → o atendente redirecionou para outro departamento
    RAMAL    → transferência para um ramal (VoIP/PABX)
    SISTEMA  → regra automática (fila, horário, fallback do menu)
    """
    MENU      = "menu"
    ATENDENTE = "atendente"
    RAMAL     = "ramal"
    SISTEMA   = "sistema"


__all__ = [
    "BaseStrEnum",
    # Tenant/Empresa
    "StatusTenant", "PlanoTenant", "PerfilUsuario",
    # Canais
    "TipoCanalMensageria", "StatusConexao",
    # Atendimento
    "StatusAtendimento",
    "StatusAssinatura",
    "TipoTransferencia", "PrioridadeAtendimento",
    "OrigemAtendimento", "MotivoAlerta",
    # Mensagem
    "TipoMensagem", "DirecaoMensagem", "StatusMensagem",
    # Roteiro/Menu
    "TipoPergunta", "StatusRoteiro",
    # PABX
    "StatusChamada", "TipoChamada",
    # Campanha/Pedido
    "StatusCampanha", "StatusPedido",
    # Email
    "StatusEmail",
    # Token
    "MotivoRevogacao",
]