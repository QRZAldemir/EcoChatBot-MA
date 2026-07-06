"""
app/services/bot_service.py
──────────────────────────────────────────────────────────────────
Máquina de estados completa da conversa WhatsApp.

Fluxo de alto nível:
  BOOT → AGUARDAR_LGPD → AGUARDAR_NOME → AGUARDAR_HUB
    ├─► AT:*  — Atendimento ao Cliente
    ├─► AG:*  — Agendamentos
    ├─► EX:*  — Exames e Diagnósticos
    ├─► PO:*  — Portaria e Recepção
    └─► OV:*  — Ouvidoria
  EM_ATENDIMENTO — bot silencioso, humano atendendo
  FINALIZADO     — reinicia no próximo contato

Acessibilidade por voz:
  O paciente pode alternar livremente entre modo texto e modo áudio a
  qualquer momento, respondendo *ÁUDIO* ou *TEXTO* (ver _pedido_ativar_audio
  / _pedido_desativar_audio). Com o modo áudio ligado, toda mensagem que o
  bot envia (menus via _lista e textos via _txt) também é convertida em
  áudio e enviada como nota de voz, sem precisar tocar nas dezenas de
  funções de menu individuais — a conversão acontece nesses dois pontos
  únicos de saída de mensagem.
"""

import contextvars
import logging
import os
import re
import unicodedata
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Atendimento, AtendimentoContext, Canal, Menu, Usuario
from app.services import audio_service, evolution_service

logger = logging.getLogger(__name__)

RODAPE = "Hospital Presbiteriano Mackenzie — Dourados/MS"

# URL pública pela qual o Evolution API busca os áudios gerados (ver
# app/routers/audio.py). Precisa ser alcançável pela instância da Evolution,
# não apenas pelo backend — configure o domínio real em produção.
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000").rstrip("/")

# Contexto ambiente (por requisição/atendimento) usado pelos helpers de
# envio (_txt/_lista) para persistir o modo de áudio e o último texto falado
# sem precisar alterar a assinatura das ~130 chamadas existentes a eles.
_ctx_db: contextvars.ContextVar[Session] = contextvars.ContextVar("_ctx_db")
_ctx_at: contextvars.ContextVar[Atendimento] = contextvars.ContextVar("_ctx_at")

# ══════════════════════════════════════════════════════════════
# CONSTANTES DE STEP
# ══════════════════════════════════════════════════════════════

# Hub
BOOT           = "BOOT"
AGUARDAR_LGPD  = "AGUARDAR_LGPD"
AGUARDAR_NOME  = "AGUARDAR_NOME"
AGUARDAR_HUB   = "AGUARDAR_HUB"
EM_ATENDIMENTO = "EM_ATENDIMENTO"
FINALIZADO     = "FINALIZADO"

# Atendimento ao Cliente
AT_MENU        = "AT:MENU"
AT_GUIA_PAC    = "AT:GUIA_PAC"
AT_OUTRAS_INFO = "AT:OUTRAS_INFO"
AT_DOC_MEDICO  = "AT:DOC:MEDICO"
AT_DOC_DATA    = "AT:DOC:DATA"
AT_DOC_MOTIVO  = "AT:DOC:MOTIVO"
AT_DOC_CPF     = "AT:DOC:CPF"
AT_DOC_NASC    = "AT:DOC:NASC"

# Agendamentos
AG_MENU          = "AG:MENU"
AG_COL_NOME      = "AG:COL_NOME"
AG_COL_NASC      = "AG:COL_NASC"
AG_COL_PARA_QUEM = "AG:COL_PARA_QUEM"
AG_COL_RESPONSAVEL = "AG:COL_RESPONSAVEL"
AG_COL_CONVENIO  = "AG:COL_CONVENIO"
AG_COL_CONV_NOME = "AG:COL_CONV_NOME"
AG_COL_MEDICO    = "AG:COL_MEDICO"
AG_COL_MED_NOME  = "AG:COL_MED_NOME"
AG_CHECKLIST     = "AG:CHECKLIST"

# Exames
EX_MENU          = "EX:MENU"
EX_AG_NOME       = "EX:AG_NOME"
EX_AG_NASC       = "EX:AG_NASC"
EX_AG_PARA_QUEM  = "EX:AG_PARA_QUEM"
EX_AG_RESPONSAVEL= "EX:AG_RESPONSAVEL"
EX_AG_EXAME      = "EX:AG_EXAME"
EX_AG_PEDIDO     = "EX:AG_PEDIDO"
EX_AG_CATEGORIA  = "EX:AG_CATEGORIA"
EX_AG_MODALIDADE = "EX:AG_MODALIDADE"
EX_AG_PLANO      = "EX:AG_PLANO"
EX_AG_CHECKLIST  = "EX:AG_CHECKLIST"

# Portaria
PO_MENU            = "PO:MENU"
PO_VISITAS_MENU    = "PO:VISITAS"
PO_CADASTRO_NOME   = "PO:CAD:NOME"
PO_CADASTRO_CPF    = "PO:CAD:CPF"
PO_CADASTRO_NASC   = "PO:CAD:NASC"
PO_CADASTRO_SEXO   = "PO:CAD:SEXO"
PO_CADASTRO_TIPO   = "PO:CAD:TIPO"
PO_CADASTRO_CONF   = "PO:CAD:CONF"
PO_ACHADOS_TIPO    = "PO:ACHADOS"

# Ouvidoria
OV_MENU        = "OV:MENU"
OV_EXP_MENU    = "OV:EXP"
OV_RECLAMACAO  = "OV:RECLAMACAO"
OV_ELOGIO      = "OV:ELOGIO"
OV_SUGESTAO    = "OV:SUGESTAO"
OV_DEN_SIGILO  = "OV:DEN_SIGILO"
OV_DENUNCIA    = "OV:DENUNCIA"
OV_PRON_TIPO   = "OV:PRON_TIPO"
OV_PRON_DADOS  = "OV:PRON_DADOS"
OV_PRON_FORMATO= "OV:PRON_FMT"
OV_PROTOCOLO   = "OV:PROTOCOLO"

# ── Mapa hub row_id → (nome do Canal, step de destino) ────────
HUB_MAPA: dict[str, tuple[str, str]] = {
    "HUB_ATENDIMENTO": ("Atendimento ao Cliente",  AT_MENU),
    "HUB_AGENDAMENTO": ("Agendamentos",             AG_MENU),
    "HUB_EXAMES":      ("Exames e Diagnósticos",    EX_MENU),
    "HUB_TESOURARIA":  ("Tesouraria",               "EM_BREVE"),
    "HUB_ORCAMENTOS":  ("Orçamentos e Internação",  "EM_BREVE"),
    "HUB_PORTARIA":    ("Portaria e Recepção",       PO_MENU),
    "HUB_INFORMACOES": ("Outras Informações",        "EM_BREVE"),
    "HUB_OUVIDORIA":   ("Ouvidoria",                OV_MENU),
}

# Hub menu estático — usado quando não há registro no banco
_HUB_ROWS = [
    {"title": "1️⃣ Atendimento ao Cliente",  "description": "Informações, Guias, Quadro Médico",      "rowId": "HUB_ATENDIMENTO"},
    {"title": "2️⃣ Agendamentos",            "description": "Marcar, Confirmar, Remarcar, Cancelar", "rowId": "HUB_AGENDAMENTO"},
    {"title": "3️⃣ Exames e Diagnósticos",   "description": "Resultados, Preparos, Agendamentos",    "rowId": "HUB_EXAMES"},
    {"title": "4️⃣ Tesouraria",             "description": "Financeiro, Pagamentos, Notas Fiscais", "rowId": "HUB_TESOURARIA"},
    {"title": "5️⃣ Orçamentos/Internação",   "description": "Cirurgias, Procedimentos, Valores",     "rowId": "HUB_ORCAMENTOS"},
    {"title": "6️⃣ Portaria e Recepção",     "description": "Visitas, Localização, Pronto Socorro",  "rowId": "HUB_PORTARIA"},
    {"title": "7️⃣ Outras Informações",      "description": "Manual do Paciente, Dúvidas",           "rowId": "HUB_INFORMACOES"},
    {"title": "8️⃣ Ouvidoria",              "description": "Elogios, Sugestões, Reclamações",       "rowId": "HUB_OUVIDORIA"},
]


# ══════════════════════════════════════════════════════════════
# UTILIDADES
# ══════════════════════════════════════════════════════════════

def _protocolo(prefixo: str = "WP") -> str:
    return f"{prefixo}-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


def _tel(remote_jid: str) -> str:
    return remote_jid.split("@")[0]


def _get(db: Session, atendimento_id: int, key: str) -> str | None:
    row = (
        db.query(AtendimentoContext)
        .filter(
            AtendimentoContext.atendimento_id == atendimento_id,
            AtendimentoContext.context_key == key,
        )
        .first()
    )
    return row.value if row else None


def _set(db: Session, atendimento_id: int, key: str, value: str) -> None:
    row = (
        db.query(AtendimentoContext)
        .filter(
            AtendimentoContext.atendimento_id == atendimento_id,
            AtendimentoContext.context_key == key,
        )
        .first()
    )
    if row:
        row.value = value
    else:
        db.add(AtendimentoContext(atendimento_id=atendimento_id, context_key=key, value=value))
    db.commit()


def _step(db: Session, atendimento: Atendimento, novo_step: str) -> None:
    _set(db, atendimento.id, "step", novo_step)


def _buscar_ou_criar(
    db: Session, telefone: str, instance: str, push_name: str | None
) -> tuple[Atendimento, bool]:
    at = (
        db.query(Atendimento)
        .filter(
            Atendimento.telefone == telefone,
            Atendimento.ativo == True,
            Atendimento.status != "finalizado",
        )
        .order_by(Atendimento.criado_em.desc())
        .first()
    )
    if at:
        if push_name and not at.nome_contato:
            at.nome_contato = push_name
            db.commit()
        return at, False

    at = Atendimento(
        protocolo=_protocolo(),
        telefone=telefone,
        nome_contato=push_name or "",
        tipo=1,
        ativo=True,
        status="aberto",
    )
    db.add(at)
    db.commit()
    db.refresh(at)
    _set(db, at.id, "instancia", instance)
    _set(db, at.id, "step", BOOT)
    return at, True


# ══════════════════════════════════════════════════════════════
# ACESSIBILIDADE POR VOZ (MODO ÁUDIO)
# ══════════════════════════════════════════════════════════════
# O paciente liga/desliga o modo áudio a qualquer momento digitando ÁUDIO
# ou TEXTO. O estado fica salvo em AtendimentoContext (chave "modo_audio"),
# então persiste entre mensagens. Enquanto ligado, _txt e _lista — os dois
# únicos pontos por onde o bot inteiro envia mensagem — também mandam uma
# nota de voz com o mesmo conteúdo, então todo menu e todo memorando de
# texto do bot passam a ficar disponíveis em áudio automaticamente, sem
# precisar alterar as dezenas de funções de menu individuais.

# Frases (já normalizadas: minúsculas e sem acento) que ligam/desligam o modo áudio.
_FRASES_ATIVAR_AUDIO = {"audio", "ouvir", "escutar", "voz", "ouvir audio", "modo audio", "quero ouvir"}
_FRASES_DESATIVAR_AUDIO = {"texto", "escrita", "modo texto", "parar audio", "sem audio", "desativar audio"}

# Remove emojis (incluindo emojis-número como "1️⃣") e marcações do WhatsApp
# (*negrito*, _itálico_, ~tachado~) para que o texto fique limpo antes de
# virar fala — gTTS lê mal esses símbolos.
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002B00-\U00002BFF"
    "\U0000FE0F"
    "\U000020E3"
    "]+",
    flags=re.UNICODE,
)
_MARKDOWN_RE = re.compile(r"[*_~`]")


def _normalizar(texto: str) -> str:
    """minúsculas, sem acento, sem espaços nas pontas — para comparar palavras-chave com tolerância."""
    texto = texto.strip().lower()
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def _pedido_ativar_audio(content: str) -> bool:
    return _normalizar(content) in _FRASES_ATIVAR_AUDIO


def _pedido_desativar_audio(content: str) -> bool:
    return _normalizar(content) in _FRASES_DESATIVAR_AUDIO


def _limpar_para_fala(texto: str) -> str:
    texto = _EMOJI_RE.sub("", texto)
    texto = _MARKDOWN_RE.sub("", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _texto_falado_menu(title: str, desc: str, rows: list[dict]) -> str:
    """Monta o roteiro falado de um menu: título, descrição e cada opção numerada."""
    partes = [_limpar_para_fala(title)]
    if desc:
        partes.append(_limpar_para_fala(desc))
    for i, row in enumerate(rows, start=1):
        linha = _limpar_para_fala(row["title"])
        descricao = row.get("description")
        if descricao:
            linha += f", {_limpar_para_fala(descricao)}"
        partes.append(f"Opção {i}: {linha}.")
    return " ".join(partes)


def _modo_audio_ativo() -> bool:
    db = _ctx_db.get(None)
    at = _ctx_at.get(None)
    if db is None or at is None:
        return False
    return _get(db, at.id, "modo_audio") == "1"


def _guardar_texto_falado(texto: str) -> None:
    """Guarda a última mensagem enviada (já limpa) para poder relê-la em áudio sob demanda."""
    db = _ctx_db.get(None)
    at = _ctx_at.get(None)
    if db is None or at is None:
        return
    _set(db, at.id, "ultimo_texto_falado", _limpar_para_fala(texto))


async def _enviar_audio(inst: str, tel: str, texto: str) -> None:
    """Converte texto em MP3 (audio_service) e envia como nota de voz via Evolution API."""
    texto = _limpar_para_fala(texto)
    if not texto:
        return
    try:
        resultado = await audio_service.gerar_audio(texto)
    except (audio_service.TextoVazioError, audio_service.TextoMuitoLongoError):
        return
    except Exception:
        logger.exception("bot_service | falha ao gerar áudio | tel=%s", tel)
        return

    media_url = f"{BACKEND_PUBLIC_URL}/api/audio/audios/{resultado['arquivo']}"
    try:
        await evolution_service.enviar_midia(
            instance=inst, number=tel, media_url=media_url, mediatype="audio",
        )
    except Exception:
        logger.exception("bot_service | falha ao enviar nota de voz | tel=%s", tel)


async def _ativar_modo_audio(db: Session, at: Atendimento, inst: str, tel: str) -> None:
    _set(db, at.id, "modo_audio", "1")
    await evolution_service.enviar_texto(
        instance=inst, number=tel,
        text=(
            "🔊 *Modo áudio ativado!* A partir de agora também vou te enviar "
            "as mensagens faladas.\n\nPara voltar ao modo texto, responda "
            "*TEXTO* a qualquer momento."
        ),
    )
    ultimo = _get(db, at.id, "ultimo_texto_falado")
    if ultimo:
        await _enviar_audio(inst, tel, ultimo)


async def _desativar_modo_audio(db: Session, at: Atendimento, inst: str, tel: str) -> None:
    _set(db, at.id, "modo_audio", "0")
    await evolution_service.enviar_texto(
        instance=inst, number=tel,
        text=(
            "⌨️ *Modo texto ativado.* Para voltar a ouvir as mensagens em "
            "áudio, responda *ÁUDIO* a qualquer momento."
        ),
    )


# ══════════════════════════════════════════════════════════════
# HELPERS COMPARTILHADOS
# ══════════════════════════════════════════════════════════════

async def _lista(
    inst: str, tel: str,
    title: str, desc: str, button: str,
    rows: list[dict], footer: str = RODAPE
) -> None:
    await evolution_service.enviar_lista(
        instance=inst, number=tel,
        title=title, description=desc,
        button_text=button,
        sections=[{"title": title, "rows": rows}],
        footer=footer,
    )
    texto_falado = _texto_falado_menu(title, desc, rows)
    _guardar_texto_falado(texto_falado)
    if _modo_audio_ativo():
        await _enviar_audio(inst, tel, texto_falado)


async def _txt(inst: str, tel: str, msg: str) -> None:
    await evolution_service.enviar_texto(instance=inst, number=tel, text=msg)
    _guardar_texto_falado(msg)
    if _modo_audio_ativo():
        await _enviar_audio(inst, tel, msg)


MSG_FILA_OCUPADA = (
    "Pedimos desculpa, mas todos os nossos agentes estão ocupados neste "
    "momento. Por favor, aguarde alguns minutos e estaremos com você em breve."
)


def _atendentes_disponiveis(db: Session, canal_id: int) -> int:
    """
    Capacidade livre de atendentes de um canal (MVP: 1 atendimento
    simultâneo por atendente). Um atendente conta como ocupado quando já
    tem algum Atendimento em_atendimento atribuído a ele (usuario_id).
    Atendimentos em_atendimento ainda sem atendente atribuído (na fila,
    aguardando alguém puxar) não contam como ocupando ninguém.
    """
    total_atendentes = (
        db.query(Usuario)
        .filter(Usuario.canal_id == canal_id, Usuario.ativo == True)
        .count()
    )
    ocupados = (
        db.query(Atendimento)
        .filter(
            Atendimento.canal_id == canal_id,
            Atendimento.status == "em_atendimento",
            Atendimento.usuario_id.isnot(None),
        )
        .count()
    )
    return total_atendentes - ocupados


async def _transferir(
    db: Session, at: Atendimento, inst: str, tel: str,
    msg: str = "🗣️ Transferindo para um atendente. Aguarde! 😊"
) -> None:
    # Se não há atendente livre no canal do atendimento, avisa que está na
    # fila em vez da mensagem de "transferindo" (que sugeriria atendimento
    # imediato). Sem canal_id definido (departamentos "em breve", sem Canal
    # cadastrado) não dá para checar capacidade, então mantém o texto padrão.
    if at.canal_id is not None and _atendentes_disponiveis(db, at.canal_id) <= 0:
        msg = MSG_FILA_OCUPADA

    await _txt(inst, tel, msg)
    at.status = "em_atendimento"
    db.commit()
    _step(db, at, EM_ATENDIMENTO)


async def _voltar_hub(
    db: Session, at: Atendimento, inst: str, tel: str
) -> None:
    await _txt(inst, tel, "🔙 Retornando ao Menu Principal...")
    await _enviar_hub(db, inst, tel)
    _step(db, at, AGUARDAR_HUB)


# ══════════════════════════════════════════════════════════════
# PONTO DE ENTRADA
# ══════════════════════════════════════════════════════════════

async def processar_mensagem_recebida(
    db: Session,
    instance_nome: str,
    remote_jid: str,
    push_name: str | None,
    msg_type: str,
    content: str,
) -> None:
    if remote_jid.endswith("@g.us"):
        return

    telefone = _tel(remote_jid)
    at, _ = _buscar_ou_criar(db, telefone, instance_nome, push_name)
    step = _get(db, at.id, "step") or BOOT

    # Disponibiliza db/at para _txt e _lista (ver seção "ACESSIBILIDADE POR
    # VOZ") sem precisar alterar a assinatura das dezenas de chamadas a eles.
    _ctx_db.set(db)
    _ctx_at.set(at)

    logger.info("step=%s tel=%s type=%s content=%r prot=%s",
                step, telefone, msg_type, content, at.protocolo)

    # Alternância de modo texto/áudio: funciona em qualquer step (exceto com
    # o bot silenciado durante atendimento humano) e não avança a máquina de
    # estados — o paciente continua exatamente de onde parou depois de trocar.
    if step != EM_ATENDIMENTO and msg_type != "list_response":
        if _pedido_ativar_audio(content):
            return await _ativar_modo_audio(db, at, instance_nome, telefone)
        if _pedido_desativar_audio(content):
            return await _desativar_modo_audio(db, at, instance_nome, telefone)

    try:
        # Hub e fluxo inicial
        if step in (BOOT, FINALIZADO):
            await _boot(db, at, instance_nome, telefone)
        elif step == AGUARDAR_LGPD:
            await _lgpd(db, at, instance_nome, telefone, msg_type, content)
        elif step == AGUARDAR_NOME:
            await _nome(db, at, instance_nome, telefone, content)
        elif step == AGUARDAR_HUB:
            await _hub(db, at, instance_nome, telefone, msg_type, content)
        elif step == EM_ATENDIMENTO:
            pass  # humano atendendo
        elif step == "EM_BREVE_MENU":
            await _em_breve_menu(db, at, instance_nome, telefone, msg_type, content)
        # Departamentos
        elif step.startswith("AT:"):
            await _atendimento(db, at, instance_nome, telefone, step, msg_type, content)
        elif step.startswith("AG:"):
            await _agendamento(db, at, instance_nome, telefone, step, msg_type, content)
        elif step.startswith("EX:"):
            await _exames(db, at, instance_nome, telefone, step, msg_type, content)
        elif step.startswith("PO:"):
            await _portaria(db, at, instance_nome, telefone, step, msg_type, content)
        elif step.startswith("OV:"):
            await _ouvidoria(db, at, instance_nome, telefone, step, msg_type, content)
    except Exception:
        logger.exception("Erro step=%s prot=%s", step, at.protocolo)


async def _em_breve_menu(db, at, inst, tel, msg_type, content):
    row = content.strip().upper() if msg_type == "list_response" else ""
    if row == "FALAR":
        return await _transferir(db, at, inst, tel)
    if row == "VOLTAR_HUB":
        return await _voltar_hub(db, at, inst, tel)
    # qualquer outra mensagem: reexibe o aviso
    nome_canal = _get(db, at.id, "canal_selecionado") or "este módulo"
    await _lista(inst, tel,
        f"🔧 {nome_canal}",
        f"O módulo de *{nome_canal}* está em processo de implantação. "
        "Em breve estará disponível!",
        "O que deseja?",
        [
            {"title": "🗣️ Falar com Atendente", "description": "", "rowId": "FALAR"},
            {"title": "🔙 Menu Principal",       "description": "", "rowId": "VOLTAR_HUB"},
        ],
    )


# ══════════════════════════════════════════════════════════════
# FLUXO HUB
# ══════════════════════════════════════════════════════════════

async def _boot(db: Session, at: Atendimento, inst: str, tel: str) -> None:
    if at.status == "finalizado":
        at.status = "aberto"
        at.ativo = True
        db.commit()

    await _txt(inst, tel,
        "👋 *Olá! Seja bem-vindo ao*\n"
        "*Hospital Presbiteriano Mackenzie*\n"
        "_Dr. e Sra. Goldsby King — Dourados/MS_\n\n"
        "Sou seu assistente virtual e estou aqui para iniciar "
        "seu atendimento com agilidade. 🤝\n\n"
        "💡 Se preferir ouvir em vez de ler, responda *ÁUDIO* a qualquer "
        "momento (e *TEXTO* para voltar)."
    )
    await _lista(inst, tel,
        "🔒 Política de Privacidade (LGPD)",
        "Para continuarmos com segurança precisamos do seu consentimento "
        "para tratamento de dados, conforme a *LGPD*.\n\n"
        "📄 Leia nossa Política:\n🔗 https://bit.ly/3QJXkWw\n\n"
        "Você declara que leu e *CONCORDA* com os termos?",
        "Responder",
        [
            {"title": "✅ Sim, Li e Concordo",  "description": "", "rowId": "LGPD_ACEITO"},
            {"title": "❌ Não concordo / Sair", "description": "", "rowId": "LGPD_RECUSADO"},
        ],
    )
    _step(db, at, AGUARDAR_LGPD)


async def _lgpd(db, at, inst, tel, msg_type, content):
    recusou = (
        (msg_type == "list_response" and content.upper() == "LGPD_RECUSADO")
        or content.strip().lower() in ("não", "nao", "recuso", "sair", "n")
    )
    if recusou:
        await _txt(inst, tel,
            "Entendemos. Sem o aceite não podemos prosseguir pelo canal digital.\n\n"
            "Agradecemos o contato! Se mudar de ideia, é só nos chamar novamente. 💙"
        )
        at.status = "finalizado"
        at.ativo = False
        db.commit()
        _step(db, at, FINALIZADO)
        return
    await _txt(inst, tel, "Obrigado pela confiança! 🙏\n\nPor gentileza, informe seu *nome completo*:")
    _step(db, at, AGUARDAR_NOME)


async def _nome(db, at, inst, tel, content):
    nome = content.strip().title()
    if len(nome) < 2:
        await _txt(inst, tel, "Não consegui identificar seu nome. Por favor, tente novamente:")
        return
    at.nome_contato = nome
    db.commit()
    _set(db, at.id, "nome", nome)
    await _txt(inst, tel, f"Obrigado, *{nome}*! Seja muito bem-vindo(a). 😊")
    await _enviar_hub(db, inst, tel)
    _step(db, at, AGUARDAR_HUB)


async def _hub(db, at, inst, tel, msg_type, content):
    if msg_type != "list_response":
        nome = _get(db, at.id, "nome") or "cliente"
        await _txt(inst, tel, f"Olá, *{nome}*! Por favor, utilize o menu abaixo:")
        await _enviar_hub(db, inst, tel)
        return

    row = content.strip().upper()
    mapa = HUB_MAPA.get(row)
    if not mapa:
        await _txt(inst, tel, "Opção não reconhecida. Utilize o menu abaixo:")
        await _enviar_hub(db, inst, tel)
        return

    nome_canal, dest_step = mapa

    if dest_step == "EM_BREVE":
        await _lista(inst, tel,
            f"🔧 {nome_canal}",
            f"O módulo de *{nome_canal}* está em processo de implantação "
            "e em breve estará disponível!",
            "O que deseja?",
            [
                {"title": "🗣️ Falar com Atendente", "description": "", "rowId": "FALAR"},
                {"title": "🔙 Menu Principal",       "description": "", "rowId": "VOLTAR_HUB"},
            ],
        )
        _set(db, at.id, "canal_selecionado", nome_canal)
        _step(db, at, "EM_BREVE_MENU")
        return

    _set(db, at.id, "canal_selecionado", nome_canal)
    canal = db.query(Canal).filter(Canal.nome == nome_canal, Canal.ativo == True).first()
    if canal:
        at.canal_id = canal.id
        db.commit()

    _step(db, at, dest_step)
    await _despachar_menu_dept(db, at, inst, tel, dest_step, msg_type, content)


async def _enviar_hub(db: Session, inst: str, tel: str) -> None:
    hub = db.query(Menu).filter(Menu.canal_id == None, Menu.ativo == True).order_by(Menu.criado_em).first()
    if hub and hub.opcoes:
        rows = [{"title": op.titulo, "description": op.descricao or "", "rowId": op.row_id} for op in hub.opcoes]
        await _lista(inst, tel, hub.titulo, hub.descricao or "Selecione o departamento:", hub.texto_botao or "Ver departamentos", rows, hub.rodape or RODAPE)
    else:
        await _lista(inst, tel, "Central de Atendimento Mackenzie", "Selecione o departamento com o qual deseja falar:", "Ver departamentos", _HUB_ROWS)


async def _despachar_menu_dept(db, at, inst, tel, step, msg_type, content):
    """Chama o handler correto após definir o step do departamento."""
    if step.startswith("AT:"):
        await _atendimento(db, at, inst, tel, step, msg_type, content)
    elif step.startswith("AG:"):
        await _agendamento(db, at, inst, tel, step, msg_type, content)
    elif step.startswith("EX:"):
        await _exames(db, at, inst, tel, step, msg_type, content)
    elif step.startswith("PO:"):
        await _portaria(db, at, inst, tel, step, msg_type, content)
    elif step.startswith("OV:"):
        await _ouvidoria(db, at, inst, tel, step, msg_type, content)


# ══════════════════════════════════════════════════════════════
# ATENDIMENTO AO CLIENTE
# ══════════════════════════════════════════════════════════════

_AT_MENU_ROWS = [
    {"title": "1️⃣ Guia de Pacientes",         "description": "Regras, horários, serviços",          "rowId": "AT_GUIA_PAC"},
    {"title": "2️⃣ Guia Maternidade",           "description": "Informações de maternidade",          "rowId": "AT_MATERNIDADE"},
    {"title": "3️⃣ Outras Orientações",         "description": "Plantão, 2ª via, contato, convênios","rowId": "AT_OUTRAS_INFO"},
    {"title": "4️⃣ Falar com nossa equipe",     "description": "Transferir para atendente",           "rowId": "AT_FALAR"},
    {"title": "5️⃣ Voltar ao Menu Principal",   "description": "",                                    "rowId": "AT_VOLTAR_HUB"},
]

_AT_GUIA_ROWS = [
    {"title": "🛏️ Regras e Horários de Visita", "description": "", "rowId": "AT_GP_VISITAS"},
    {"title": "💼 Objetos de Valor",            "description": "", "rowId": "AT_GP_OBJETOS"},
    {"title": "🚗 Estacionamento",              "description": "", "rowId": "AT_GP_ESTAC"},
    {"title": "🏥 Serviços do Hospital",        "description": "", "rowId": "AT_GP_SERVICOS"},
    {"title": "📞 Falar com equipe",            "description": "", "rowId": "AT_FALAR"},
    {"title": "🔙 Voltar",                      "description": "", "rowId": "AT_VOLTAR_AT"},
]

_AT_INFO_ROWS = [
    {"title": "🩺 Médicos Plantonistas 24h",  "description": "", "rowId": "AT_OI_PLANTAO"},
    {"title": "📄 2ª Via de Documentos",      "description": "", "rowId": "AT_OI_DOC"},
    {"title": "📞 Informações de Contato",    "description": "", "rowId": "AT_OI_CONTATO"},
    {"title": "💳 Convênios e Pagamentos",    "description": "", "rowId": "AT_OI_CONVENIOS"},
    {"title": "🗣️ Falar com Especialista",    "description": "", "rowId": "AT_FALAR"},
    {"title": "🔙 Voltar",                    "description": "", "rowId": "AT_VOLTAR_AT"},
]

_AT_NAV = [
    {"title": "📞 Falar com equipe", "description": "", "rowId": "AT_FALAR"},
    {"title": "🔙 Menu Atendimento", "description": "", "rowId": "AT_VOLTAR_AT"},
    {"title": "🏠 Menu Principal",   "description": "", "rowId": "AT_VOLTAR_HUB"},
]


async def _atendimento(db, at, inst, tel, step, msg_type, content):
    row = content.strip().upper() if msg_type == "list_response" else ""

    # Ações globais do departamento
    if row == "AT_FALAR":
        return await _transferir(db, at, inst, tel)
    if row == "AT_VOLTAR_HUB":
        return await _voltar_hub(db, at, inst, tel)
    if row == "AT_VOLTAR_AT":
        _step(db, at, AT_MENU)
        return await _atendimento(db, at, inst, tel, AT_MENU, "reset", "")

    if step == AT_MENU:
        if msg_type != "list_response":
            await _lista(inst, tel, "📞 Atendimento ao Cliente", "Selecione uma opção:", "Ver opções", _AT_MENU_ROWS)
            return
        if row == "AT_GUIA_PAC":
            _step(db, at, AT_GUIA_PAC)
            await _lista(inst, tel, "📋 Guia de Pacientes", "O que você precisa saber?", "Ver opções", _AT_GUIA_ROWS)
        elif row == "AT_MATERNIDADE":
            await _txt(inst, tel,
                "🤱 *Guia de Maternidade — H. P. Mackenzie*\n\n"
                "• *Pré-internação:* Realize o pré-cadastro com 48h de antecedência.\n"
                "• *Acomodações:* Quartos individuais com acompanhante 24h.\n"
                "• *Visitas:* Somente cônjuge/parceiro(a) como acompanhante fixo.\n"
                "• *Alta:* Aguarde liberação médica antes de sair.\n\n"
                "Para mais informações, fale com nossa equipe!"
            )
            await _lista(inst, tel, "Maternidade", "O que deseja?", "Opções", _AT_NAV)
        elif row == "AT_OUTRAS_INFO":
            _step(db, at, AT_OUTRAS_INFO)
            await _lista(inst, tel, "ℹ️ Outras Orientações", "Selecione:", "Ver opções", _AT_INFO_ROWS)
        else:
            await _lista(inst, tel, "📞 Atendimento ao Cliente", "Selecione uma opção:", "Ver opções", _AT_MENU_ROWS)

    elif step == AT_GUIA_PAC:
        respostas = {
            "AT_GP_VISITAS": (
                "🛏️ *Regras e Horários de Visita*\n\n"
                "• Horário: *14h às 20h* (dias úteis) | *10h às 20h* (fins de semana)\n"
                "• Máximo *2 visitantes* por vez no quarto.\n"
                "• Crianças até 12 anos não podem visitar (exceto filhos do paciente).\n"
                "• Uso de máscaras é recomendado em UTIs e setores especiais."
            ),
            "AT_GP_OBJETOS": (
                "💼 *Objetos de Valor e Pertences*\n\n"
                "• O hospital *não se responsabiliza* por objetos de valor não depositados.\n"
                "• Solicite o cofre com a recepção no momento da internação.\n"
                "• Documentos importantes: guarde uma cópia e deixe os originais com familiar."
            ),
            "AT_GP_ESTAC": (
                "🚗 *Estacionamento*\n\n"
                "• Estacionamento gratuito para pacientes e acompanhantes.\n"
                "• Acesso pela Rua Principal — Portaria Sul.\n"
                "• Vagas para PCD disponíveis próximo à entrada principal.\n"
                "• Capacidade: *200 vagas*."
            ),
            "AT_GP_SERVICOS": (
                "🏥 *Serviços do Hospital*\n\n"
                "• 🍽️ Restaurante e lanchonete (7h–22h)\n"
                "• 💊 Farmácia interna (24h)\n"
                "• 📡 Wi-Fi gratuito em todos os andares\n"
                "• 🙏 Capelania e apoio espiritual (sob demanda)\n"
                "• 📋 Assistência Social (seg–sex, 8h–17h)"
            ),
        }
        texto = respostas.get(row)
        if texto:
            await _txt(inst, tel, texto)
            await _lista(inst, tel, "Guia de Pacientes", "O que mais posso ajudar?", "Opções", _AT_GUIA_ROWS)
        else:
            await _lista(inst, tel, "📋 Guia de Pacientes", "Selecione:", "Ver opções", _AT_GUIA_ROWS)

    elif step == AT_OUTRAS_INFO:
        if row == "AT_OI_PLANTAO":
            await _txt(inst, tel,
                "🩺 *Médicos Plantonistas 24h*\n\n"
                "Nossa central de plantão opera 24 horas por dia, 7 dias por semana.\n\n"
                "Para consultar o médico de plantão atual, entre em contato:\n"
                "📞 *(67) 3416-8000* — Ramal 100\n\n"
                "Em emergências, dirija-se diretamente ao *Pronto Socorro*."
            )
            await _lista(inst, tel, "Outras Orientações", "O que mais posso ajudar?", "Opções", _AT_INFO_ROWS)
        elif row == "AT_OI_DOC":
            await _txt(inst, tel,
                "📄 *Solicitação de 2ª Via de Documentos*\n\n"
                "Para iniciar seu pedido, precisarei de algumas informações. "
                "Vou guiá-lo(a) passo a passo.\n\n"
                "Primeiramente, informe o *nome do médico ou especialidade* "
                "do atendimento em questão:"
            )
            _set(db, at.id, "at_doc_protocolo", _protocolo("DOC"))
            _step(db, at, AT_DOC_MEDICO)
        elif row == "AT_OI_CONTATO":
            await _txt(inst, tel,
                "📞 *Informações de Contato*\n\n"
                "🏥 *Hospital Presbiteriano Mackenzie*\n"
                "Rua Hayel Bon Faker, 3797 — Dourados/MS\n\n"
                "📞 Central: *(67) 3416-8000*\n"
                "📞 Pronto Socorro: *(67) 3416-8010*\n"
                "📧 E-mail: contato@mackenzie.org.br\n"
                "⏰ Funcionamento: *24h / 7 dias*"
            )
            await _lista(inst, tel, "Outras Orientações", "O que mais posso ajudar?", "Opções", _AT_INFO_ROWS)
        elif row == "AT_OI_CONVENIOS":
            await _txt(inst, tel,
                "💳 *Convênios e Formas de Pagamento*\n\n"
                "Trabalhamos com os principais planos de saúde:\n"
                "• Unimed · Bradesco Saúde · SulAmérica\n"
                "• Cassi · Geap · Postal Saúde\n"
                "• E demais convênios com contrato ativo.\n\n"
                "💰 *Particular:* Aceitamos cartões de débito, crédito e PIX.\n\n"
                "Para verificar a cobertura do seu plano, entre em contato com a Tesouraria:\n"
                "📞 *(67) 3416-8020*"
            )
            await _lista(inst, tel, "Outras Orientações", "O que mais posso ajudar?", "Opções", _AT_INFO_ROWS)
        else:
            await _lista(inst, tel, "ℹ️ Outras Orientações", "Selecione:", "Ver opções", _AT_INFO_ROWS)

    elif step in (AT_DOC_MEDICO, AT_DOC_DATA, AT_DOC_MOTIVO, AT_DOC_CPF, AT_DOC_NASC):
        await _at_doc_coleta(db, at, inst, tel, step, content)

    else:
        _step(db, at, AT_MENU)
        await _lista(inst, tel, "📞 Atendimento ao Cliente", "Selecione uma opção:", "Ver opções", _AT_MENU_ROWS)


async def _at_doc_coleta(db, at, inst, tel, step, content):
    txt = content.strip()
    if not txt:
        return

    proximos = {
        AT_DOC_MEDICO:  (AT_DOC_DATA,   "at_doc_medico",  "Informe a *data do atendimento* (ex: 15/06/2025):"),
        AT_DOC_DATA:    (AT_DOC_MOTIVO, "at_doc_data",    "Informe o *motivo da solicitação*:"),
        AT_DOC_MOTIVO:  (AT_DOC_CPF,    "at_doc_motivo",  "Informe o *CPF* do paciente (somente números):"),
        AT_DOC_CPF:     (AT_DOC_NASC,   "at_doc_cpf",     "Informe a *data de nascimento* do paciente (DD/MM/AAAA):"),
    }

    if step in proximos:
        prox_step, ctx_key, prox_prompt = proximos[step]
        _set(db, at.id, ctx_key, txt)
        _step(db, at, prox_step)
        await _txt(inst, tel, prox_prompt)
        return

    if step == AT_DOC_NASC:
        _set(db, at.id, "at_doc_nasc", txt)
        prot = _get(db, at.id, "at_doc_protocolo") or _protocolo("DOC")
        resumo = (
            f"📋 *Resumo da Solicitação de 2ª Via*\n\n"
            f"👨‍⚕️ Médico/Especialidade: {_get(db, at.id, 'at_doc_medico') or '—'}\n"
            f"📅 Data do atendimento: {_get(db, at.id, 'at_doc_data') or '—'}\n"
            f"📝 Motivo: {_get(db, at.id, 'at_doc_motivo') or '—'}\n"
            f"🪪 CPF: {_get(db, at.id, 'at_doc_cpf') or '—'}\n"
            f"🎂 Nascimento: {_get(db, at.id, 'at_doc_nasc') or '—'}\n\n"
            f"🔖 Protocolo: *{prot}*\n\n"
            "Sua solicitação foi registrada! Um atendente entrará em contato em breve. 📩"
        )
        await _txt(inst, tel, resumo)
        await _transferir(db, at, inst, tel, "Transferindo para finalizar sua solicitação. Aguarde! 📋")


# ══════════════════════════════════════════════════════════════
# AGENDAMENTOS
# ══════════════════════════════════════════════════════════════

_AG_MENU_ROWS = [
    {"title": "1️⃣ Marcar Consulta",         "description": "Nova consulta",                   "rowId": "AG_MARCAR"},
    {"title": "2️⃣ Confirmar Agendamento",   "description": "Verificar consulta marcada",      "rowId": "AG_CONFIRMAR"},
    {"title": "3️⃣ Remarcar Consulta",       "description": "Alterar data de consulta",        "rowId": "AG_REMARCAR"},
    {"title": "4️⃣ Cancelar Consulta",       "description": "Cancelar consulta marcada",       "rowId": "AG_CANCELAR"},
    {"title": "5️⃣ Exames Cardiológicos",    "description": "Ergometria, Holter, Mapa",        "rowId": "AG_CARDIOLOGIA"},
    {"title": "6️⃣ Falar com Atendente",     "description": "",                                "rowId": "AG_FALAR"},
    {"title": "7️⃣ Menu Principal",          "description": "",                                "rowId": "AG_VOLTAR_HUB"},
]

_AG_PARA_QUEM_ROWS = [
    {"title": "1️⃣ Sim, sou eu mesmo(a)",      "description": "", "rowId": "AG_PARA_MIM"},
    {"title": "2️⃣ Não, é para outra pessoa",  "description": "", "rowId": "AG_PARA_OUTRO"},
]

_AG_CONVENIO_ROWS = [
    {"title": "1️⃣ Sim, tenho plano de saúde", "description": "Informar nome do plano", "rowId": "AG_TEM_CONVENIO"},
    {"title": "2️⃣ Não — Particular",          "description": "",                       "rowId": "AG_PARTICULAR"},
]

_AG_MEDICO_ROWS = [
    {"title": "1️⃣ Sim, informar médico", "description": "", "rowId": "AG_TEM_MEDICO"},
    {"title": "2️⃣ Não tenho preferência", "description": "", "rowId": "AG_SEM_MEDICO"},
]

_AG_CHECKLIST_ROWS = [
    {"title": "✅ Confirmar e transferir", "description": "Encaminhar para atendente",  "rowId": "AG_CONFIRMAR_OK"},
    {"title": "✏️ Corrigir informações",  "description": "Recomeçar coleta",           "rowId": "AG_CORRIGIR"},
    {"title": "🔙 Menu Agendamentos",     "description": "",                           "rowId": "AG_VOLTAR_AG"},
]


async def _agendamento(db, at, inst, tel, step, msg_type, content):
    row = content.strip().upper() if msg_type == "list_response" else ""

    if row == "AG_FALAR":
        return await _transferir(db, at, inst, tel)
    if row == "AG_VOLTAR_HUB":
        return await _voltar_hub(db, at, inst, tel)
    if row in ("AG_VOLTAR_AG", "AG_CORRIGIR"):
        _step(db, at, AG_MENU)
        return await _agendamento(db, at, inst, tel, AG_MENU, "reset", "")

    if step == AG_MENU:
        if msg_type != "list_response":
            await _lista(inst, tel, "📅 Agendamentos", "Selecione uma opção:", "Ver opções", _AG_MENU_ROWS)
            return
        fluxo_map = {
            "AG_MARCAR":     "MARCAR",
            "AG_CONFIRMAR":  "CONFIRMAR",
            "AG_REMARCAR":   "REMARCAR",
            "AG_CANCELAR":   "CANCELAR",
        }
        if row == "AG_CARDIOLOGIA":
            await _txt(inst, tel,
                "🫀 *Exames Cardiológicos*\n\n"
                "Realizamos:\n• Ergometria • Ecocardiograma • Holter 24h\n"
                "• MAPA • Teste de Esforço\n\n"
                "Para agendar, entre em contato:\n"
                "📞 *(67) 3416-8030* — Cardiologia"
            )
            await _lista(inst, tel, "Agendamentos", "O que deseja?", "Opções", [
                {"title": "🗣️ Falar com Atendente", "description": "", "rowId": "AG_FALAR"},
                {"title": "🔙 Menu Agendamentos",   "description": "", "rowId": "AG_VOLTAR_AG"},
            ])
            return
        fluxo = fluxo_map.get(row)
        if fluxo:
            _set(db, at.id, "ag_fluxo", fluxo)
            _set(db, at.id, "ag_protocolo", _protocolo("AG"))
            _step(db, at, AG_COL_NOME)
            label = {"MARCAR": "marcar", "CONFIRMAR": "confirmar", "REMARCAR": "remarcar", "CANCELAR": "cancelar"}[fluxo]
            await _txt(inst, tel,
                f"📋 *{fluxo.title()} Consulta*\n\n"
                f"Vou precisar de algumas informações para {label} sua consulta.\n\n"
                "Qual é o *nome completo* do paciente?"
            )
        else:
            await _lista(inst, tel, "📅 Agendamentos", "Selecione:", "Ver opções", _AG_MENU_ROWS)

    elif step == AG_COL_NOME:
        if not content.strip():
            return
        _set(db, at.id, "ag_nome", content.strip().title())
        _step(db, at, AG_COL_NASC)
        await _txt(inst, tel, "Qual é a *data de nascimento* do paciente? (DD/MM/AAAA)")

    elif step == AG_COL_NASC:
        if not content.strip():
            return
        _set(db, at.id, "ag_nasc", content.strip())
        _step(db, at, AG_COL_PARA_QUEM)
        await _lista(inst, tel, "Agendamento", "O agendamento é para você?", "Responder", _AG_PARA_QUEM_ROWS)

    elif step == AG_COL_PARA_QUEM:
        if msg_type != "list_response":
            await _lista(inst, tel, "Agendamento", "O agendamento é para você?", "Responder", _AG_PARA_QUEM_ROWS)
            return
        if row == "AG_PARA_MIM":
            _set(db, at.id, "ag_para_quem", "O_MESMO")
            _step(db, at, AG_COL_CONVENIO)
            await _lista(inst, tel, "Agendamento", "Possui plano de saúde?", "Responder", _AG_CONVENIO_ROWS)
        elif row == "AG_PARA_OUTRO":
            _set(db, at.id, "ag_para_quem", "OUTRO")
            _step(db, at, AG_COL_RESPONSAVEL)
            await _txt(inst, tel, "Qual é o *nome completo do responsável* pelo agendamento?")

    elif step == AG_COL_RESPONSAVEL:
        if not content.strip():
            return
        _set(db, at.id, "ag_responsavel", content.strip().title())
        _step(db, at, AG_COL_CONVENIO)
        await _lista(inst, tel, "Agendamento", "Possui plano de saúde?", "Responder", _AG_CONVENIO_ROWS)

    elif step == AG_COL_CONVENIO:
        if msg_type != "list_response":
            await _lista(inst, tel, "Agendamento", "Possui plano de saúde?", "Responder", _AG_CONVENIO_ROWS)
            return
        if row == "AG_TEM_CONVENIO":
            _step(db, at, AG_COL_CONV_NOME)
            await _txt(inst, tel, "Qual é o *nome do plano de saúde*?")
        elif row == "AG_PARTICULAR":
            _set(db, at.id, "ag_convenio", "PARTICULAR")
            _step(db, at, AG_COL_MEDICO)
            await _lista(inst, tel, "Agendamento", "Possui médico de preferência?", "Responder", _AG_MEDICO_ROWS)

    elif step == AG_COL_CONV_NOME:
        if not content.strip():
            return
        _set(db, at.id, "ag_convenio", content.strip().title())
        _step(db, at, AG_COL_MEDICO)
        await _lista(inst, tel, "Agendamento", "Possui médico de preferência?", "Responder", _AG_MEDICO_ROWS)

    elif step == AG_COL_MEDICO:
        if msg_type != "list_response":
            await _lista(inst, tel, "Agendamento", "Possui médico de preferência?", "Responder", _AG_MEDICO_ROWS)
            return
        if row == "AG_TEM_MEDICO":
            _step(db, at, AG_COL_MED_NOME)
            await _txt(inst, tel, "Qual é o *nome do médico* de sua preferência?")
        elif row == "AG_SEM_MEDICO":
            _set(db, at.id, "ag_medico", "SEM_PREFERENCIA")
            await _ag_mostrar_checklist(db, at, inst, tel)

    elif step == AG_COL_MED_NOME:
        if not content.strip():
            return
        _set(db, at.id, "ag_medico", content.strip().title())
        await _ag_mostrar_checklist(db, at, inst, tel)

    elif step == AG_CHECKLIST:
        if row == "AG_CONFIRMAR_OK":
            fluxo = _get(db, at.id, "ag_fluxo") or "Agendamento"
            prot  = _get(db, at.id, "ag_protocolo") or "—"
            await _transferir(db, at, inst, tel,
                f"✅ *{fluxo.title()} registrado!*\n\n"
                f"🔖 Protocolo: *{prot}*\n\n"
                "Transferindo para um atendente para concluir. Aguarde! 📞"
            )
        elif row in ("AG_CORRIGIR", "AG_VOLTAR_AG"):
            _step(db, at, AG_MENU)
            await _lista(inst, tel, "📅 Agendamentos", "Selecione:", "Ver opções", _AG_MENU_ROWS)
        else:
            await _ag_mostrar_checklist(db, at, inst, tel)

    else:
        _step(db, at, AG_MENU)
        await _lista(inst, tel, "📅 Agendamentos", "Selecione:", "Ver opções", _AG_MENU_ROWS)


async def _ag_mostrar_checklist(db, at, inst, tel):
    fluxo     = _get(db, at.id, "ag_fluxo") or "Agendamento"
    nome      = _get(db, at.id, "ag_nome") or "—"
    nasc      = _get(db, at.id, "ag_nasc") or "—"
    para_quem = _get(db, at.id, "ag_para_quem") or "—"
    responsavel = _get(db, at.id, "ag_responsavel") or ""
    convenio  = _get(db, at.id, "ag_convenio") or "—"
    medico    = _get(db, at.id, "ag_medico") or "—"
    prot      = _get(db, at.id, "ag_protocolo") or "—"

    resp_linha = f"\n👤 Responsável: {responsavel}" if responsavel else ""
    med_label  = "Sem preferência" if medico == "SEM_PREFERENCIA" else medico

    await _txt(inst, tel,
        f"📋 *Resumo — {fluxo.title()} de Consulta*\n\n"
        f"👤 Paciente: {nome}\n"
        f"🎂 Nascimento: {nasc}{resp_linha}\n"
        f"💳 Convênio: {convenio}\n"
        f"🩺 Médico: {med_label}\n"
        f"🔖 Protocolo: *{prot}*\n\n"
        "As informações estão corretas?"
    )
    _step(db, at, AG_CHECKLIST)
    await _lista(inst, tel, "Confirmar", "Deseja confirmar?", "Responder", _AG_CHECKLIST_ROWS)


# ══════════════════════════════════════════════════════════════
# EXAMES E DIAGNÓSTICOS
# ══════════════════════════════════════════════════════════════

_EX_MENU_ROWS = [
    {"title": "1️⃣ Agendar Exames",          "description": "Solicitar novo exame",           "rowId": "EX_AGENDAR"},
    {"title": "2️⃣ Resultados e Laudos",      "description": "Consultar resultado de exame",   "rowId": "EX_RESULTADOS"},
    {"title": "3️⃣ Orçamentos e Valores",     "description": "Consultar preços de exames",     "rowId": "EX_ORCAMENTOS"},
    {"title": "4️⃣ Preparo e Orientações",    "description": "Como se preparar para exames",   "rowId": "EX_PREPARO"},
    {"title": "5️⃣ Falar com Atendente",      "description": "",                               "rowId": "EX_FALAR"},
    {"title": "6️⃣ Menu Principal",           "description": "",                               "rowId": "EX_VOLTAR_HUB"},
]

_EX_PEDIDO_ROWS = [
    {"title": "1️⃣ Sim, vou enviar agora",   "description": "Envie a foto do pedido",  "rowId": "EX_PEDIDO_ENV"},
    {"title": "2️⃣ Sim, mas envio depois",   "description": "Continuar sem enviar",    "rowId": "EX_PEDIDO_DEPOIS"},
    {"title": "3️⃣ Não tenho pedido médico", "description": "",                        "rowId": "EX_SEM_PEDIDO"},
]

_EX_CATEGORIA_ROWS = [
    {"title": "1️⃣ Laboratório",  "description": "Exames de sangue, urina etc.", "rowId": "EX_CAT_LAB"},
    {"title": "2️⃣ Ultrassom",    "description": "",                             "rowId": "EX_CAT_ULTRA"},
    {"title": "3️⃣ Tomografia",   "description": "",                             "rowId": "EX_CAT_TOMO"},
    {"title": "4️⃣ Raio-X",       "description": "",                             "rowId": "EX_CAT_RAIO"},
    {"title": "5️⃣ Ressonância",  "description": "",                             "rowId": "EX_CAT_RESSO"},
    {"title": "6️⃣ Outro",        "description": "Não sei / outro tipo",         "rowId": "EX_CAT_OUTRO"},
]

_EX_MODAL_ROWS = [
    {"title": "1️⃣ Convênio / Plano",  "description": "", "rowId": "EX_MOD_CONVENIO"},
    {"title": "2️⃣ Particular",        "description": "", "rowId": "EX_MOD_PARTICULAR"},
]

_EX_CHECKLIST_ROWS = [
    {"title": "✅ Confirmar e transferir", "description": "", "rowId": "EX_CONFIRMAR_OK"},
    {"title": "✏️ Corrigir informações",  "description": "", "rowId": "EX_CORRIGIR"},
    {"title": "🔙 Menu Exames",           "description": "", "rowId": "EX_VOLTAR_EX"},
]

_EX_NAV = [
    {"title": "🗣️ Falar com Atendente", "description": "", "rowId": "EX_FALAR"},
    {"title": "🔙 Menu Exames",         "description": "", "rowId": "EX_VOLTAR_EX"},
    {"title": "🏠 Menu Principal",      "description": "", "rowId": "EX_VOLTAR_HUB"},
]


async def _exames(db, at, inst, tel, step, msg_type, content):
    row = content.strip().upper() if msg_type == "list_response" else ""

    if row == "EX_FALAR":
        return await _transferir(db, at, inst, tel)
    if row == "EX_VOLTAR_HUB":
        return await _voltar_hub(db, at, inst, tel)
    if row in ("EX_VOLTAR_EX", "EX_CORRIGIR"):
        _step(db, at, EX_MENU)
        return await _exames(db, at, inst, tel, EX_MENU, "reset", "")

    if step == EX_MENU:
        if msg_type != "list_response":
            await _lista(inst, tel, "🔬 Exames e Diagnósticos", "Selecione:", "Ver opções", _EX_MENU_ROWS)
            return
        if row == "EX_AGENDAR":
            _set(db, at.id, "ex_protocolo", _protocolo("EX"))
            _step(db, at, EX_AG_NOME)
            await _txt(inst, tel, "📅 *Agendamento de Exame*\n\nQual é o *nome completo do paciente*?")
        elif row == "EX_RESULTADOS":
            await _txt(inst, tel,
                "📄 *Resultados e Laudos*\n\n"
                "Para obter seu resultado, acesse:\n"
                "🔗 *portal.mackenzie.ms.br/resultados*\n\n"
                "Ou entre em contato:\n"
                "📞 *(67) 3416-8040* — Laboratório\n"
                "⏰ Retirada presencial: seg–sex 7h–18h | sáb 7h–12h"
            )
            await _lista(inst, tel, "Exames", "O que mais posso ajudar?", "Opções", _EX_NAV)
        elif row == "EX_ORCAMENTOS":
            await _txt(inst, tel,
                "💰 *Orçamentos e Valores*\n\n"
                "Os valores variam conforme o tipo de exame e modalidade de pagamento.\n\n"
                "Para um orçamento preciso, entre em contato:\n"
                "📞 *(67) 3416-8040* — Diagnósticos por Imagem\n"
                "📞 *(67) 3416-8050* — Laboratório\n\n"
                "Ou um atendente pode te ajudar agora!"
            )
            await _lista(inst, tel, "Exames", "O que mais posso ajudar?", "Opções", _EX_NAV)
        elif row == "EX_PREPARO":
            await _txt(inst, tel,
                "🧪 *Preparo e Orientações para Exames*\n\n"
                "• *Laboratório (sangue)*: Jejum de 8–12h. Pode beber água.\n"
                "• *Ultrassom abdominal*: Jejum de 4h e bexiga cheia.\n"
                "• *Tomografia*: Depende do tipo. Confirme com a clínica.\n"
                "• *Ressonância*: Retire metais. Informe marcapasso ou implantes.\n"
                "• *Raio-X*: Sem preparo especial na maioria dos casos.\n\n"
                "Dúvidas sobre seu exame específico? Fale conosco!"
            )
            await _lista(inst, tel, "Exames", "O que mais posso ajudar?", "Opções", _EX_NAV)
        else:
            await _lista(inst, tel, "🔬 Exames e Diagnósticos", "Selecione:", "Ver opções", _EX_MENU_ROWS)

    elif step == EX_AG_NOME:
        if not content.strip():
            return
        _set(db, at.id, "ex_nome", content.strip().title())
        _step(db, at, EX_AG_NASC)
        await _txt(inst, tel, "Qual é a *data de nascimento* do paciente? (DD/MM/AAAA)")

    elif step == EX_AG_NASC:
        if not content.strip():
            return
        _set(db, at.id, "ex_nasc", content.strip())
        _step(db, at, EX_AG_PARA_QUEM)
        await _lista(inst, tel, "Agendamento de Exame", "O exame é para você?", "Responder",
            [{"title": "1️⃣ Sim, para mim",       "description": "", "rowId": "EX_PARA_MIM"},
             {"title": "2️⃣ Para outra pessoa",    "description": "", "rowId": "EX_PARA_OUTRO"}])

    elif step == EX_AG_PARA_QUEM:
        if msg_type != "list_response":
            return
        if row == "EX_PARA_OUTRO":
            _step(db, at, EX_AG_RESPONSAVEL)
            await _txt(inst, tel, "Qual é o *nome do responsável* pelo agendamento?")
        else:
            _set(db, at.id, "ex_responsavel", "O_PROPRIO")
            _step(db, at, EX_AG_EXAME)
            await _txt(inst, tel, "Qual o *nome do exame* a ser realizado?")

    elif step == EX_AG_RESPONSAVEL:
        if not content.strip():
            return
        _set(db, at.id, "ex_responsavel", content.strip().title())
        _step(db, at, EX_AG_EXAME)
        await _txt(inst, tel, "Qual o *nome do exame* a ser realizado?")

    elif step == EX_AG_EXAME:
        if not content.strip():
            return
        _set(db, at.id, "ex_exame", content.strip())
        _step(db, at, EX_AG_PEDIDO)
        await _lista(inst, tel, "Pedido Médico", "Possui pedido médico para este exame?", "Responder", _EX_PEDIDO_ROWS)

    elif step == EX_AG_PEDIDO:
        if msg_type != "list_response":
            await _lista(inst, tel, "Pedido Médico", "Possui pedido médico?", "Responder", _EX_PEDIDO_ROWS)
            return
        _set(db, at.id, "ex_pedido", row)
        if row == "EX_PEDIDO_ENV":
            await _txt(inst, tel, "📎 Envie a *foto ou PDF* do pedido médico agora.")
            _step(db, at, EX_AG_CATEGORIA)
        else:
            _step(db, at, EX_AG_CATEGORIA)
            await _lista(inst, tel, "Categoria do Exame", "Qual categoria melhor descreve o exame?", "Selecionar", _EX_CATEGORIA_ROWS)

    elif step == EX_AG_CATEGORIA:
        if msg_type == "list_response" and row.startswith("EX_CAT_"):
            labels = {"EX_CAT_LAB": "Laboratório", "EX_CAT_ULTRA": "Ultrassom",
                      "EX_CAT_TOMO": "Tomografia", "EX_CAT_RAIO": "Raio-X",
                      "EX_CAT_RESSO": "Ressonância", "EX_CAT_OUTRO": "A Verificar"}
            _set(db, at.id, "ex_categoria", labels.get(row, "A Verificar"))
            _step(db, at, EX_AG_MODALIDADE)
            await _lista(inst, tel, "Forma de Pagamento", "Como será o pagamento?", "Responder", _EX_MODAL_ROWS)
        else:
            await _lista(inst, tel, "Categoria", "Selecione a categoria:", "Selecionar", _EX_CATEGORIA_ROWS)

    elif step == EX_AG_MODALIDADE:
        if msg_type != "list_response":
            await _lista(inst, tel, "Forma de Pagamento", "Como será o pagamento?", "Responder", _EX_MODAL_ROWS)
            return
        if row == "EX_MOD_CONVENIO":
            _step(db, at, EX_AG_PLANO)
            await _txt(inst, tel, "Qual é o *nome do plano de saúde*?")
        else:
            _set(db, at.id, "ex_modalidade", "PARTICULAR")
            await _ex_checklist(db, at, inst, tel)

    elif step == EX_AG_PLANO:
        if not content.strip():
            return
        _set(db, at.id, "ex_plano", content.strip().title())
        _set(db, at.id, "ex_modalidade", "CONVENIO")
        await _ex_checklist(db, at, inst, tel)

    elif step == EX_AG_CHECKLIST:
        if row == "EX_CONFIRMAR_OK":
            prot = _get(db, at.id, "ex_protocolo") or "—"
            await _transferir(db, at, inst, tel,
                f"✅ *Agendamento de Exame registrado!*\n\n"
                f"🔖 Protocolo: *{prot}*\n\n"
                "Transferindo para confirmar data e hora. Aguarde! 📞"
            )
        else:
            _step(db, at, EX_MENU)
            await _lista(inst, tel, "🔬 Exames e Diagnósticos", "Selecione:", "Ver opções", _EX_MENU_ROWS)

    else:
        _step(db, at, EX_MENU)
        await _lista(inst, tel, "🔬 Exames e Diagnósticos", "Selecione:", "Ver opções", _EX_MENU_ROWS)


async def _ex_checklist(db, at, inst, tel):
    nome      = _get(db, at.id, "ex_nome") or "—"
    nasc      = _get(db, at.id, "ex_nasc") or "—"
    responsavel = _get(db, at.id, "ex_responsavel") or "—"
    exame     = _get(db, at.id, "ex_exame") or "—"
    categoria = _get(db, at.id, "ex_categoria") or "—"
    modalidade= _get(db, at.id, "ex_modalidade") or "—"
    plano     = _get(db, at.id, "ex_plano") or ("—" if modalidade == "CONVENIO" else "Particular")
    prot      = _get(db, at.id, "ex_protocolo") or "—"

    resp_label = "O Próprio Paciente" if responsavel == "O_PROPRIO" else responsavel

    await _txt(inst, tel,
        f"🔬 *Resumo — Agendamento de Exame*\n\n"
        f"👤 Paciente: {nome}\n"
        f"🎂 Nascimento: {nasc}\n"
        f"👥 Responsável: {resp_label}\n"
        f"🧪 Exame: {exame}\n"
        f"📂 Categoria: {categoria}\n"
        f"💳 Pagamento: {modalidade} — {plano}\n"
        f"🔖 Protocolo: *{prot}*\n\n"
        "As informações estão corretas?"
    )
    _step(db, at, EX_AG_CHECKLIST)
    await _lista(inst, tel, "Confirmar Agendamento", "Confirmar?", "Responder", _EX_CHECKLIST_ROWS)


# ══════════════════════════════════════════════════════════════
# PORTARIA E RECEPÇÃO
# ══════════════════════════════════════════════════════════════

_PO_MENU_ROWS = [
    {"title": "🟢 Visitas e Acompanhantes",  "description": "Regras e acesso",               "rowId": "PO_VISITAS"},
    {"title": "🔵 Localização",              "description": "Endereço e estacionamento",     "rowId": "PO_LOCALIZACAO"},
    {"title": "🔴 Achados e Perdidos",       "description": "Objetos esquecidos",            "rowId": "PO_ACHADOS"},
    {"title": "🟡 Pronto Socorro",           "description": "Como chegar ao PS",             "rowId": "PO_PS"},
    {"title": "🟣 Menu Principal",           "description": "",                              "rowId": "PO_VOLTAR_HUB"},
]

_PO_VISITAS_ROWS = [
    {"title": "📝 Fazer cadastro de visitante", "description": "Adiantar meu cadastro",    "rowId": "PO_CAD_INICIAR"},
    {"title": "❓ Dúvidas sobre visitas",        "description": "Regras, horários, acesso", "rowId": "PO_DUVIDAS"},
    {"title": "📞 Falar com atendente",          "description": "",                         "rowId": "PO_FALAR"},
    {"title": "🔙 Menu Portaria",                "description": "",                         "rowId": "PO_VOLTAR_PO"},
]

_PO_SEXO_ROWS = [
    {"title": "1️⃣ Masculino", "description": "", "rowId": "PO_SEX_M"},
    {"title": "2️⃣ Feminino",  "description": "", "rowId": "PO_SEX_F"},
    {"title": "3️⃣ Outro",     "description": "", "rowId": "PO_SEX_O"},
]

_PO_TIPO_ROWS = [
    {"title": "1️⃣ Visitante",    "description": "", "rowId": "PO_TIPO_VIS"},
    {"title": "2️⃣ Acompanhante", "description": "", "rowId": "PO_TIPO_ACOMP"},
]

_PO_NAV = [
    {"title": "🔙 Menu Portaria", "description": "", "rowId": "PO_VOLTAR_PO"},
    {"title": "📞 Falar com atendente", "description": "", "rowId": "PO_FALAR"},
]


async def _portaria(db, at, inst, tel, step, msg_type, content):
    row = content.strip().upper() if msg_type == "list_response" else ""

    if row == "PO_FALAR":
        return await _transferir(db, at, inst, tel)
    if row == "PO_VOLTAR_HUB":
        return await _voltar_hub(db, at, inst, tel)
    if row == "PO_VOLTAR_PO":
        _step(db, at, PO_MENU)
        return await _portaria(db, at, inst, tel, PO_MENU, "reset", "")

    if step == PO_MENU:
        if msg_type != "list_response":
            await _lista(inst, tel, "🏢 Portaria e Recepção", "Selecione:", "Ver opções", _PO_MENU_ROWS)
            return
        if row == "PO_VISITAS":
            _step(db, at, PO_VISITAS_MENU)
            await _lista(inst, tel, "🟢 Visitas e Acompanhantes", "O que deseja?", "Ver opções", _PO_VISITAS_ROWS)
        elif row == "PO_LOCALIZACAO":
            await _txt(inst, tel,
                "🔵 *Localização e Acesso*\n\n"
                "🏥 *Hospital Presbiteriano Mackenzie*\n"
                "Rua Hayel Bon Faker, 3797\n"
                "Jardim Caramuru — Dourados/MS\n\n"
                "🗺️ *Como chegar:*\n"
                "• Da BR-163: siga pela Av. Marcelino Pires, vire na Rua Hayel Bon Faker.\n"
                "• Ponto de ônibus: Linha 05 — parada em frente ao hospital.\n\n"
                "🚗 *Estacionamento:* Entrada pela Portaria Sul. Gratuito."
            )
            await _lista(inst, tel, "Portaria", "O que mais posso ajudar?", "Opções", _PO_NAV)
        elif row == "PO_ACHADOS":
            _step(db, at, PO_ACHADOS_TIPO)
            await _lista(inst, tel, "🔴 Achados e Perdidos", "Você é:", "Selecionar",
                [{"title": "👤 Paciente",     "description": "", "rowId": "PO_AP_PAC"},
                 {"title": "👥 Visitante",    "description": "", "rowId": "PO_AP_VIS"},
                 {"title": "🤝 Acompanhante", "description": "", "rowId": "PO_AP_ACOMP"}])
        elif row == "PO_PS":
            await _txt(inst, tel,
                "🟡 *Chegada ao Pronto Socorro*\n\n"
                "• Acesso pela *Portaria Norte* (Rua lateral, 24h).\n"
                "• Entrada exclusiva para PS — siga as placas amarelas.\n"
                "• Na chegada, informe nome e motivo ao enfermeiro.\n"
                "• Triagem por ordem de urgência (Manchester).\n\n"
                "🚨 *Emergências graves:* SAMU *192* ou Bombeiros *193*."
            )
            await _lista(inst, tel, "Portaria", "O que mais posso ajudar?", "Opções", _PO_NAV)
        else:
            await _lista(inst, tel, "🏢 Portaria e Recepção", "Selecione:", "Ver opções", _PO_MENU_ROWS)

    elif step == PO_VISITAS_MENU:
        if msg_type != "list_response":
            await _lista(inst, tel, "🟢 Visitas e Acompanhantes", "O que deseja?", "Ver opções", _PO_VISITAS_ROWS)
            return
        if row == "PO_CAD_INICIAR":
            _step(db, at, PO_CADASTRO_NOME)
            await _txt(inst, tel,
                "📝 *Cadastro de Visitante*\n\n"
                "Vou coletar seus dados para agilizar na entrada.\n\n"
                "Qual é o seu *nome completo*?"
            )
        elif row == "PO_DUVIDAS":
            await _txt(inst, tel,
                "❓ *Dúvidas Frequentes — Visitas*\n\n"
                "🕐 *Horários:*\n"
                "• Dias úteis: 14h às 20h\n"
                "• Fins de semana: 10h às 20h\n\n"
                "👥 *Limite:* 2 visitantes por vez no quarto.\n\n"
                "📋 *Documentos:* RG ou CNH obrigatório.\n\n"
                "🚫 *Crianças:* Não permitidas (exceto filhos do paciente).\n\n"
                "😷 *Máscaras:* Obrigatórias em UTI e setores especiais."
            )
            await _lista(inst, tel, "Visitas", "O que mais posso ajudar?", "Opções", _PO_VISITAS_ROWS)
        else:
            await _lista(inst, tel, "🟢 Visitas e Acompanhantes", "O que deseja?", "Ver opções", _PO_VISITAS_ROWS)

    elif step == PO_CADASTRO_NOME:
        if not content.strip():
            return
        _set(db, at.id, "po_vis_nome", content.strip().title())
        _step(db, at, PO_CADASTRO_CPF)
        await _txt(inst, tel, "Qual é o seu *CPF* (somente números)?")

    elif step == PO_CADASTRO_CPF:
        if not content.strip():
            return
        _set(db, at.id, "po_vis_cpf", content.strip())
        _step(db, at, PO_CADASTRO_NASC)
        await _txt(inst, tel, "Qual é a sua *data de nascimento*? (DD/MM/AAAA)")

    elif step == PO_CADASTRO_NASC:
        if not content.strip():
            return
        _set(db, at.id, "po_vis_nasc", content.strip())
        _step(db, at, PO_CADASTRO_SEXO)
        await _lista(inst, tel, "Cadastro", "Sexo:", "Selecionar", _PO_SEXO_ROWS)

    elif step == PO_CADASTRO_SEXO:
        if msg_type != "list_response":
            await _lista(inst, tel, "Cadastro", "Sexo:", "Selecionar", _PO_SEXO_ROWS)
            return
        sexo_map = {"PO_SEX_M": "Masculino", "PO_SEX_F": "Feminino", "PO_SEX_O": "Outro"}
        _set(db, at.id, "po_vis_sexo", sexo_map.get(row, "Não informado"))
        _step(db, at, PO_CADASTRO_TIPO)
        await _lista(inst, tel, "Cadastro", "Você virá como:", "Selecionar", _PO_TIPO_ROWS)

    elif step == PO_CADASTRO_TIPO:
        if msg_type != "list_response":
            await _lista(inst, tel, "Cadastro", "Você virá como:", "Selecionar", _PO_TIPO_ROWS)
            return
        tipo_map = {"PO_TIPO_VIS": "Visitante", "PO_TIPO_ACOMP": "Acompanhante"}
        _set(db, at.id, "po_vis_tipo", tipo_map.get(row, "Visitante"))
        nome = _get(db, at.id, "po_vis_nome") or "—"
        cpf  = _get(db, at.id, "po_vis_cpf") or "—"
        nasc = _get(db, at.id, "po_vis_nasc") or "—"
        sexo = _get(db, at.id, "po_vis_sexo") or "—"
        tipo = tipo_map.get(row, "Visitante")
        await _txt(inst, tel,
            f"📝 *Resumo do Cadastro*\n\n"
            f"👤 Nome: {nome}\n"
            f"🪪 CPF: {cpf}\n"
            f"🎂 Nascimento: {nasc}\n"
            f"⚥ Sexo: {sexo}\n"
            f"🏷️ Tipo: {tipo}\n\n"
            "Os dados estão corretos?"
        )
        _step(db, at, PO_CADASTRO_CONF)
        await _lista(inst, tel, "Confirmar", "Confirmar cadastro?", "Responder",
            [{"title": "✅ Sim, transferir!", "description": "", "rowId": "PO_CAD_OK"},
             {"title": "❌ Corrigir dados",   "description": "", "rowId": "PO_CAD_CORRIGIR"}])

    elif step == PO_CADASTRO_CONF:
        if msg_type != "list_response":
            return
        if row == "PO_CAD_OK":
            await _transferir(db, at, inst, tel,
                "✅ *Cadastro de visitante recebido!*\n\n"
                "Um atendente irá confirmar seus dados em breve. Aguarde! 🏢"
            )
        else:
            _step(db, at, PO_VISITAS_MENU)
            await _lista(inst, tel, "🟢 Visitas e Acompanhantes", "O que deseja?", "Ver opções", _PO_VISITAS_ROWS)

    elif step == PO_ACHADOS_TIPO:
        if msg_type != "list_response":
            return
        tipo_map = {"PO_AP_PAC": "Paciente", "PO_AP_VIS": "Visitante", "PO_AP_ACOMP": "Acompanhante"}
        tipo = tipo_map.get(row, "Visitante")
        await _txt(inst, tel,
            f"🔴 *Achados e Perdidos — {tipo}*\n\n"
            "Para localizar ou registrar um objeto perdido, entre em contato com a Portaria:\n"
            "📞 *(67) 3416-8000* — Ramal Portaria\n"
            "⏰ Disponível 24h\n\n"
            "Guarde este número para agilizar seu atendimento!"
        )
        await _lista(inst, tel, "Portaria", "O que mais posso ajudar?", "Opções", _PO_NAV)
        _step(db, at, PO_MENU)

    else:
        _step(db, at, PO_MENU)
        await _lista(inst, tel, "🏢 Portaria e Recepção", "Selecione:", "Ver opções", _PO_MENU_ROWS)


# ══════════════════════════════════════════════════════════════
# OUVIDORIA
# ══════════════════════════════════════════════════════════════

_OV_MENU_ROWS = [
    {"title": "1️⃣ Reclamação/Elogio/Sugestão","description": "Compartilhe sua experiência",    "rowId": "OV_EXPERIENCIA"},
    {"title": "2️⃣ Canal de Denúncia",          "description": "Sigilo garantido",              "rowId": "OV_DENUNCIA_MENU"},
    {"title": "3️⃣ Cópia de Prontuário",        "description": "Solicitar prontuário médico",  "rowId": "OV_PRONTUARIO"},
    {"title": "4️⃣ Consultar Protocolo",        "description": "Acompanhar sua solicitação",   "rowId": "OV_PROTOCOLO_MENU"},
    {"title": "5️⃣ Falar com Atendente",        "description": "",                             "rowId": "OV_FALAR"},
    {"title": "6️⃣ Menu Principal",             "description": "",                             "rowId": "OV_VOLTAR_HUB"},
]

_OV_EXP_ROWS = [
    {"title": "😤 Reclamação",    "description": "Relatar insatisfação",    "rowId": "OV_RECLAMACAO_SEL"},
    {"title": "🌟 Elogio",        "description": "Compartilhar elogio",     "rowId": "OV_ELOGIO_SEL"},
    {"title": "💡 Sugestão",      "description": "Enviar sugestão",         "rowId": "OV_SUGESTAO_SEL"},
    {"title": "🔙 Voltar",        "description": "",                        "rowId": "OV_VOLTAR_OV"},
]

_OV_PRON_TIPO_ROWS = [
    {"title": "1️⃣ Sou o próprio paciente",    "description": "", "rowId": "OV_PRON_PAC"},
    {"title": "2️⃣ Sou responsável legal",     "description": "", "rowId": "OV_PRON_RESP"},
    {"title": "🔙 Voltar ao Menu",            "description": "", "rowId": "OV_VOLTAR_OV"},
]

_OV_PRON_FMT_ROWS = [
    {"title": "📧 Digital — PDF por e-mail", "description": "", "rowId": "OV_PRON_DIGITAL"},
    {"title": "📄 Físico — retirar impresso","description": "", "rowId": "OV_PRON_FISICO"},
]

_OV_NAV = [
    {"title": "🔙 Menu Ouvidoria", "description": "", "rowId": "OV_VOLTAR_OV"},
    {"title": "🏠 Menu Principal", "description": "", "rowId": "OV_VOLTAR_HUB"},
]


async def _ouvidoria(db, at, inst, tel, step, msg_type, content):
    row = content.strip().upper() if msg_type == "list_response" else ""

    if row == "OV_FALAR":
        return await _transferir(db, at, inst, tel)
    if row == "OV_VOLTAR_HUB":
        return await _voltar_hub(db, at, inst, tel)
    if row == "OV_VOLTAR_OV":
        _step(db, at, OV_MENU)
        return await _ouvidoria(db, at, inst, tel, OV_MENU, "reset", "")

    if step == OV_MENU:
        if msg_type != "list_response":
            await _lista(inst, tel, "📢 Ouvidoria", "Selecione:", "Ver opções", _OV_MENU_ROWS)
            return
        if row == "OV_EXPERIENCIA":
            _step(db, at, OV_EXP_MENU)
            await _lista(inst, tel, "💬 Sua Experiência", "O que deseja registrar?", "Selecionar", _OV_EXP_ROWS)
        elif row == "OV_DENUNCIA_MENU":
            _step(db, at, OV_DEN_SIGILO)
            await _txt(inst, tel,
                "🔒 *Canal de Denúncia*\n\n"
                "Garantimos total sigilo sobre sua identidade.\n"
                "Sua denúncia será tratada com seriedade e confidencialidade.\n\n"
                "Como deseja se identificar?"
            )
            await _lista(inst, tel, "Canal de Denúncia", "Identificação:", "Selecionar",
                [{"title": "👤 Quero me identificar", "description": "", "rowId": "OV_DEN_IDENT"},
                 {"title": "🕵️ Quero anonimato",     "description": "", "rowId": "OV_DEN_ANON"},
                 {"title": "🔙 Voltar",               "description": "", "rowId": "OV_VOLTAR_OV"}])
        elif row == "OV_PRONTUARIO":
            _step(db, at, OV_PRON_TIPO)
            await _lista(inst, tel, "📋 Cópia de Prontuário", "Você é:", "Selecionar", _OV_PRON_TIPO_ROWS)
        elif row == "OV_PROTOCOLO_MENU":
            _step(db, at, OV_PROTOCOLO)
            await _txt(inst, tel, "🔍 *Consultar Protocolo*\n\nInforme o *número do protocolo* que deseja consultar:")
        else:
            await _lista(inst, tel, "📢 Ouvidoria", "Selecione:", "Ver opções", _OV_MENU_ROWS)

    elif step == OV_EXP_MENU:
        if msg_type != "list_response":
            await _lista(inst, tel, "💬 Sua Experiência", "O que deseja registrar?", "Selecionar", _OV_EXP_ROWS)
            return
        prompts = {
            "OV_RECLAMACAO_SEL": (OV_RECLAMACAO, "ov_tipo", "RECLAMACAO",
                "😤 *Reclamação*\n\nLamentamos que sua experiência não tenha sido satisfatória.\n\n"
                "Por favor, descreva o ocorrido com o máximo de detalhes (setor, data, nome do profissional, etc.):"),
            "OV_ELOGIO_SEL": (OV_ELOGIO, "ov_tipo", "ELOGIO",
                "🌟 *Elogio*\n\nQue ótimo! Ficamos felizes em receber seu elogio. 😊\n\n"
                "Descreva o que lhe agradou (setor, nome do profissional, data do atendimento):"),
            "OV_SUGESTAO_SEL": (OV_SUGESTAO, "ov_tipo", "SUGESTAO",
                "💡 *Sugestão*\n\nSua opinião é muito importante para nós!\n\n"
                "Descreva sua sugestão de melhoria:"),
        }
        p = prompts.get(row)
        if p:
            next_step, ctx_key, ctx_val, prompt = p
            _set(db, at.id, ctx_key, ctx_val)
            _set(db, at.id, "ov_protocolo", _protocolo("OV"))
            _step(db, at, next_step)
            await _txt(inst, tel, prompt)
        else:
            await _lista(inst, tel, "💬 Sua Experiência", "O que deseja registrar?", "Selecionar", _OV_EXP_ROWS)

    elif step in (OV_RECLAMACAO, OV_ELOGIO, OV_SUGESTAO):
        if not content.strip():
            return
        _set(db, at.id, "ov_texto", content.strip())
        tipo  = _get(db, at.id, "ov_tipo") or "Manifestação"
        prot  = _get(db, at.id, "ov_protocolo") or _protocolo("OV")
        labels = {"RECLAMACAO": "Reclamação", "ELOGIO": "Elogio", "SUGESTAO": "Sugestão"}
        await _txt(inst, tel,
            f"✅ *{labels.get(tipo, tipo)} registrada com sucesso!*\n\n"
            f"🔖 Protocolo: *{prot}*\n\n"
            "Nossa equipe analisará sua manifestação e entrará em contato em até *5 dias úteis*. 📩"
        )
        await _transferir(db, at, inst, tel,
            "Transferindo para um atendente que pode complementar seu registro. Aguarde! 🗣️"
        )

    elif step == OV_DEN_SIGILO:
        if msg_type != "list_response":
            return
        if row == "OV_DEN_IDENT":
            _set(db, at.id, "ov_den_anon", "NAO")
        else:
            _set(db, at.id, "ov_den_anon", "SIM")
        _set(db, at.id, "ov_protocolo", _protocolo("DEN"))
        _step(db, at, OV_DENUNCIA)
        await _txt(inst, tel,
            "🔒 *Canal de Denúncia*\n\n"
            "Pode escrever sua denúncia com segurança. Todas as informações são tratadas "
            "com absoluto sigilo pela nossa equipe de compliance.\n\n"
            "Descreva o ocorrido:"
        )

    elif step == OV_DENUNCIA:
        if not content.strip():
            return
        _set(db, at.id, "ov_denuncia_texto", content.strip())
        prot = _get(db, at.id, "ov_protocolo") or "—"
        await _txt(inst, tel,
            f"✅ *Denúncia registrada!*\n\n"
            f"🔖 Protocolo: *{prot}*\n\n"
            "Sua denúncia foi encaminhada ao setor responsável com total sigilo. "
            "Acompanhe com o protocolo acima. 🔒"
        )
        await _lista(inst, tel, "Ouvidoria", "O que mais posso ajudar?", "Opções", _OV_NAV)
        _step(db, at, OV_MENU)

    elif step == OV_PRON_TIPO:
        if msg_type != "list_response":
            await _lista(inst, tel, "📋 Cópia de Prontuário", "Você é:", "Selecionar", _OV_PRON_TIPO_ROWS)
            return
        tipo_map = {"OV_PRON_PAC": "Próprio Paciente", "OV_PRON_RESP": "Responsável Legal"}
        _set(db, at.id, "ov_pron_tipo", tipo_map.get(row, "Próprio Paciente"))
        _set(db, at.id, "ov_protocolo", _protocolo("PRON"))
        _step(db, at, OV_PRON_DADOS)
        await _txt(inst, tel,
            "📋 *Solicitação de Prontuário*\n\n"
            "Informe os dados do paciente:\n"
            "*Nome completo, CPF, data de nascimento e data do atendimento.*\n\n"
            "Exemplo:\n_João Silva, 123.456.789-00, 15/03/1985, 10/06/2025_"
        )

    elif step == OV_PRON_DADOS:
        if not content.strip():
            return
        _set(db, at.id, "ov_pron_dados", content.strip())
        _step(db, at, OV_PRON_FORMATO)
        await _lista(inst, tel, "Formato do Prontuário", "Como prefere receber?", "Selecionar", _OV_PRON_FMT_ROWS)

    elif step == OV_PRON_FORMATO:
        if msg_type != "list_response":
            await _lista(inst, tel, "Formato", "Como prefere receber?", "Selecionar", _OV_PRON_FMT_ROWS)
            return
        fmt_map = {"OV_PRON_DIGITAL": "Digital (PDF por e-mail)", "OV_PRON_FISICO": "Físico (impresso)"}
        formato = fmt_map.get(row, "Digital (PDF por e-mail)")
        _set(db, at.id, "ov_pron_formato", formato)
        prot  = _get(db, at.id, "ov_protocolo") or "—"
        tipo  = _get(db, at.id, "ov_pron_tipo") or "—"
        dados = _get(db, at.id, "ov_pron_dados") or "—"
        await _txt(inst, tel,
            f"📋 *Solicitação de Prontuário Registrada*\n\n"
            f"👤 Solicitante: {tipo}\n"
            f"📝 Dados: {dados}\n"
            f"📂 Formato: {formato}\n"
            f"🔖 Protocolo: *{prot}*\n\n"
            "Nossa equipe processará em até *10 dias úteis*. 📩"
        )
        await _transferir(db, at, inst, tel,
            "Transferindo para um atendente que complementará a solicitação. Aguarde! 📋"
        )

    elif step == OV_PROTOCOLO:
        if not content.strip():
            return
        prot_buscado = content.strip().upper()
        await _txt(inst, tel,
            f"🔍 *Consulta de Protocolo: {prot_buscado}*\n\n"
            "📌 Protocolo localizado. Status: *Em análise*\n\n"
            "Para mais detalhes ou se o protocolo não foi reconhecido, "
            "entre em contato com nossa equipe:\n"
            "📞 *(67) 3416-8060* — Ouvidoria\n"
            "⏰ Seg–Sex | 8h–17h"
        )
        await _lista(inst, tel, "Ouvidoria", "O que mais posso ajudar?", "Opções", _OV_NAV)
        _step(db, at, OV_MENU)

    else:
        _step(db, at, OV_MENU)
        await _lista(inst, tel, "📢 Ouvidoria", "Selecione:", "Ver opções", _OV_MENU_ROWS)
