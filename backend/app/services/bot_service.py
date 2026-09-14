"""
app/services/bot_service.py
──────────────────────────────────────────────────────────────────
Máquina de estados da conversa WhatsApp (plataforma SaaS genérica).
Fluxos de departamento NÃO são hardcoded: o hub e as telas de cada
canal vêm do cadastro (Menu / MenuOpcao / Canal). Qualquer opção após
a 1ª tela do canal encaminha para atendimento humano (fila).

BOOT → AGUARDAR_LGPD → AGUARDAR_NOME → AGUARDAR_HUB
└─► DEPTO_DINAMICO (menu do canal) → EM_ATENDIMENTO
FINALIZADO — reinicia no próximo contato

Identidade da empresa (nome, rodapé, saudação, URL da LGPD) vem de
variáveis de ambiente — o mesmo código atende qualquer vertical.
Acessibilidade por voz: o cliente liga/desliga com ÁUDIO / TEXTO.
"""
import contextvars
import logging
import os
import re
import unicodedata
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from app.models import Atendimento, AtendimentoContext, Canal, Menu, Usuario
from app.services import audio_service, evolution_service

logger = logging.getLogger(__name__)

EMPRESA_NOME = os.getenv("EMPRESA_NOME", "EcoChat Marcx")
RODAPE = os.getenv("EMPRESA_RODAPE", EMPRESA_NOME)
LGPD_URL = os.getenv("LGPD_URL", "").strip()
BOT_MENSAGEM_BOAS_VINDAS = os.getenv("BOT_MENSAGEM_BOAS_VINDAS", "").strip()

_MESES_PT = [" ", "jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

# URL pública pela qual o Evolution API busca os áudios gerados
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000").rstrip("/")

# Contexto ambiente (por requisição/atendimento)
_ctx_db: contextvars.ContextVar[Session] = contextvars.ContextVar("_ctx_db")
_ctx_at: contextvars.ContextVar[Atendimento] = contextvars.ContextVar("_ctx_at")

# ══════════════════════════════════════════════════════════════
# CONSTANTES DE STEP
# ══════════════════════════════════════════════════════════════
BOOT           = "BOOT"
AGUARDAR_LGPD  = "AGUARDAR_LGPD"
AGUARDAR_NOME  = "AGUARDAR_NOME"
AGUARDAR_HUB   = "AGUARDAR_HUB"
EM_ATENDIMENTO = "EM_ATENDIMENTO"
FINALIZADO     = "FINALIZADO"
DEPTO_DINAMICO = "DEPTO_DINAMICO"

# ══════════════════════════════════════════════════════════════
# UTILIDADES
# ══════════════════════════════════════════════════════════════
def _substituir_variaveis(texto: Optional[str], nome_cliente: str = " ") -> Optional[str]:
    """Expande [NOME_CLIENTE]/[DATA]/[HORA] no corpo de mensagens."""
    if not texto:
        return texto
    agora = datetime.now()
    substituicoes = {
        "[NOME_CLIENTE]": nome_cliente or "cliente",
        "[DATA]": f"{agora.day:02d}/{_MESES_PT[agora.month]}/{agora.year}",
        "[HORA]": agora.strftime("%H:%M"),
    }
    for chave, valor in substituicoes.items():
        texto = texto.replace(chave, valor)
    return texto

def _protocolo(prefixo: str = "WP") -> str:
    return f"{prefixo}-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

def _tel(remote_jid: str) -> str:
    return remote_jid.split("@")[0]

def _get(db: Session, atendimento_id: int, key: str) -> Optional[str]:
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
    db: Session, telefone: str, instance: str, push_name: Optional[str]
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
_FRASES_ATIVAR_AUDIO = {"audio", "ouvir", "escutar", "voz", "ouvir audio", "modo audio", "quero ouvir"}
_FRASES_DESATIVAR_AUDIO = {"texto", "escrita", "modo texto", "parar audio", "sem audio", "desativar audio"}

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
    """minúsculas, sem acento, sem espaços nas pontas."""
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
    """Monta o roteiro falado de um menu."""
    partes = [_limpar_para_fala(title)]
    if desc:
        partes.append(_limpar_para_fala(desc))
    for i, row in enumerate(rows, start=1):
        linha = _limpar_para_fala(row["title"])
        descricao = row.get("description")
        if descricao:
            linha += f", {_limpar_para_fala(descricao)}"
        partes.append(f"Opção {i}: {linha}.")
    return ". ".join(partes)

def _modo_audio_ativo() -> bool:
    db = _ctx_db.get(None)
    at = _ctx_at.get(None)
    if db is None or at is None:
        return False
    return _get(db, at.id, "modo_audio") == "1"

def _guardar_texto_falado(texto: str) -> None:
    db = _ctx_db.get(None)
    at = _ctx_at.get(None)
    if db is None or at is None:
        return
    _set(db, at.id, "ultimo_texto_falado", _limpar_para_fala(texto))

async def _enviar_audio(inst: str, tel: str, texto: str) -> None:
    """Converte texto em MP3 e envia como nota de voz."""
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
            "🔊 Modo áudio ativado! A partir de agora também vou te enviar "
            "as mensagens faladas.\n\nPara voltar ao modo texto, responda "
            "TEXTO a qualquer momento."
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
            "⌨️ Modo texto ativado. Para voltar a ouvir as mensagens em "
            "áudio, responda ÁUDIO a qualquer momento."
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
    if at.canal_id is not None and _atendentes_disponiveis(db, at.canal_id) <= 0:
        msg = MSG_FILA_OCUPADA
    await _txt(inst, tel, msg)
    
    at.status = "fila"
    db.commit()
    _step(db, at, EM_ATENDIMENTO)

async def _voltar_hub(
    db: Session, at: Atendimento, inst: str, tel: str
) -> None:
    await _txt(inst, tel, "🔙 Retornando ao Menu Principal...")
    await _enviar_hub(db, inst, tel, at)
    _step(db, at, AGUARDAR_HUB)

# ══════════════════════════════════════════════════════════════
# PONTO DE ENTRADA
# ══════════════════════════════════════════════════════════════
async def processar_mensagem_recebida(
    db: Session,
    instance_nome: str,
    remote_jid: str,
    push_name: Optional[str],
    msg_type: str,
    content: str,
) -> None:
    if remote_jid.endswith("@g.us"):
        return
        
    telefone = _tel(remote_jid)
    at, _ = _buscar_ou_criar(db, telefone, instance_nome, push_name)
    step = _get(db, at.id, "step") or BOOT
    
    _ctx_db.set(db)
    _ctx_at.set(at)
    
    logger.info("step=%s tel=%s type=%s content=%r prot=%s",
                step, telefone, msg_type, content, at.protocolo)
                
    if step != EM_ATENDIMENTO and msg_type != "list_response":
        if _pedido_ativar_audio(content):
            return await _ativar_modo_audio(db, at, instance_nome, telefone)
        if _pedido_desativar_audio(content):
            return await _desativar_modo_audio(db, at, instance_nome, telefone)
            
    try:
        if step in (BOOT, FINALIZADO):
            await _boot(db, at, instance_nome, telefone)
        elif step == AGUARDAR_LGPD:
            await _lgpd(db, at, instance_nome, telefone, msg_type, content)
        elif step == AGUARDAR_NOME:
            await _nome(db, at, instance_nome, telefone, content)
        elif step == AGUARDAR_HUB:
            await _hub(db, at, instance_nome, telefone, msg_type, content)
        elif step == EM_ATENDIMENTO:
            pass
        elif step == "EM_BREVE_MENU":
            await _em_breve_menu(db, at, instance_nome, telefone, msg_type, content)
        elif step == DEPTO_DINAMICO:
            await _departamento_dinamico(db, at, instance_nome, telefone, msg_type, content)
        else:
            await _voltar_hub(db, at, instance_nome, telefone)
    except Exception:
        logger.exception("Erro step=%s prot=%s", step, at.protocolo)

async def _em_breve_menu(db, at, inst, tel, msg_type, content):
    row = content.strip().upper() if msg_type == "list_response" else ""
    if row == "FALAR":
        return await _transferir(db, at, inst, tel)
    if row == "VOLTAR_HUB":
        return await _voltar_hub(db, at, inst, tel)
        
    nome_canal = _get(db, at.id, "canal_selecionado") or "este módulo"
    await _lista(inst, tel,
        f"🔧 {nome_canal}",
        f"O módulo de {nome_canal} está em processo de implantação. Em breve estará disponível!",
        "O que deseja?",
        [
            {"title": "🗣️ Falar com Atendente", "description": "", "rowId": "FALAR"},
            {"title": "🔙 Menu Principal", "description": "", "rowId": "VOLTAR_HUB"},
        ],
    )

# ══════════════════════════════════════════════════════════════
# FLUXO HUB
# ══════════════════════════════════════════════════════════════
def _mensagem_boas_vindas() -> str:
    if BOT_MENSAGEM_BOAS_VINDAS:
        return BOT_MENSAGEM_BOAS_VINDAS
    return (
        f"👋 Olá! Seja bem-vindo ao \n"
        f"{EMPRESA_NOME}\n\n"
        "Sou seu assistente virtual e estou aqui para iniciar "
        "seu atendimento com agilidade. 🤝\n\n"
        "💡 Se preferir ouvir em vez de ler, responda ÁUDIO a qualquer "
        "momento (e TEXTO para voltar)."
    )

def _texto_lgpd() -> str:
    politica = f"📄 Leia nossa Política:\n🔗 {LGPD_URL}\n\n" if LGPD_URL else ""
    return (
        "Para continuarmos com segurança precisamos do seu consentimento "
        f"para tratamento de dados, conforme a LGPD.\n\n"
        f"{politica}"
        "Você declara que leu e CONCORDA com os termos?"
    )

def _hub_rows_de_canais(db: Session) -> list[dict]:
    canais = db.query(Canal).filter(Canal.ativo == True).order_by(Canal.nome).all()
    return [
        {"title": c.nome, "description": c.descricao or "", "rowId": f"CANAL_{c.id}"}
        for c in canais
    ]

def resolver_canal_do_hub(db: Session, row: str) -> Optional[Canal]:
    if row.startswith("CANAL_") and row[len("CANAL_"):].isdigit():
        return db.query(Canal).filter(
            Canal.id == int(row[len("CANAL_"):]), Canal.ativo == True
        ).first()
    return db.query(Canal).filter(Canal.nome.ilike(row), Canal.ativo == True).first()

async def _boot(db: Session, at: Atendimento, inst: str, tel: str) -> None:
    if at.status == "finalizado":
        at.status = "aberto"
        at.ativo = True
        db.commit()
        
    await _txt(inst, tel, _mensagem_boas_vindas())
    await _lista(inst, tel,
        "🔒 Política de Privacidade (LGPD)",
        _texto_lgpd(),
        "Responder",
        [
            {"title": "✅ Sim, Li e Concordo", "description": "", "rowId": "LGPD_ACEITO"},
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
        
    await _txt(inst, tel, "Obrigado pela confiança! 🙏\n\nPor gentileza, informe seu nome completo:")
    _step(db, at, AGUARDAR_NOME)

async def _nome(db, at, inst, tel, content):
    nome = content.strip().title()
    if len(nome) < 2:
        await _txt(inst, tel, "Não consegui identificar seu nome. Por favor, tente novamente:")
        return
    at.nome_contato = nome
    db.commit()
    _set(db, at.id, "nome", nome)
    await _txt(inst, tel, f"Obrigado, {nome}! Seja muito bem-vindo(a). 😊")
    await _enviar_hub(db, inst, tel, at)
    _step(db, at, AGUARDAR_HUB)

async def _hub(db, at, inst, tel, msg_type, content):
    if msg_type != "list_response":
        nome = _get(db, at.id, "nome") or "cliente"
        await _txt(inst, tel, f"Olá, {nome}! Por favor, utilize o menu abaixo:")
        await _enviar_hub(db, inst, tel, at)
        return
        
    canal = resolver_canal_do_hub(db, content.strip().upper())
    if canal:
        return await _entrar_departamento_dinamico(db, at, inst, tel, canal)
        
    await _txt(inst, tel, "Opção não reconhecida. Utilize o menu abaixo:")
    await _enviar_hub(db, inst, tel, at)

async def _entrar_departamento_dinamico(db, at, inst, tel, canal: Canal) -> None:
    _set(db, at.id, "canal_selecionado", canal.nome)
    at.canal_id = canal.id
    at.departamento_id = canal.departamento_id
    db.commit()
    
    menu = (
        db.query(Menu)
        .filter(Menu.canal_id == canal.id, Menu.ativo == True)
        .order_by(Menu.criado_em)
        .first()
    )
    if menu and menu.opcoes:
        rows = [{"title": op.titulo, "description": op.descricao or "", "rowId": op.row_id} for op in menu.opcoes]
        corpo = _substituir_variaveis(menu.descricao, at.nome_contato) or "Selecione uma opção:"
        await _lista(inst, tel, menu.titulo, corpo, menu.texto_botao or "Ver opções", rows, menu.rodape)
        _step(db, at, DEPTO_DINAMICO)
    else:
        await _transferir(db, at, inst, tel)

async def _departamento_dinamico(db, at, inst, tel, msg_type, content) -> None:
    row = content.strip().upper() if msg_type == "list_response" else ""
    if row == "VOLTAR_HUB":
        return await _voltar_hub(db, at, inst, tel)
    await _transferir(db, at, inst, tel)

async def _enviar_hub(db: Session, inst: str, tel: str, at: Optional[Atendimento] = None) -> None:
    hub = db.query(Menu).filter(Menu.canal_id == None, Menu.ativo == True).order_by(Menu.criado_em).first()
    nome_cliente = at.nome_contato if at else ""
    
    if hub and hub.opcoes:
        rows = [{"title": op.titulo, "description": op.descricao or "", "rowId": op.row_id} for op in hub.opcoes]
        corpo = _substituir_variaveis(hub.descricao, nome_cliente) or "Selecione o departamento:"
        await _lista(inst, tel, hub.titulo, corpo, hub.texto_botao or "Ver departamentos", rows, hub.rodape or RODAPE)
        return
        
    rows = _hub_rows_de_canais(db)
    if not rows:
        await _txt(inst, tel, "Nenhum canal de atendimento está ativo no momento. Tente novamente mais tarde.")
        return
        
    await _lista(
        inst, tel,
        f"Central de Atendimento — {EMPRESA_NOME}",
        "Selecione o departamento com o qual deseja falar:",
        "Ver departamentos",
        rows,
    )