"""
================================================================================
SERVIÇO DE ÁUDIO (TEXTO → FALA) - ECOCHAT MARCX API
================================================================================
Autor: Aldemir Queiroz da Silva
Versão: 1.0.0
Data de Criação: 06 de Julho de 2026
================================================================================
FINALIDADE DO SCRIPT:
Este serviço é responsável pelo módulo de acessibilidade por voz do sistema
de Memorandos. Ele converte um texto (ex: o conteúdo de um memorando) em um
arquivo de áudio MP3, permitindo que usuários com deficiência visual,
motora, ou qualquer pessoa que prefira ouvir em vez de ler, acessem o
conteúdo de forma autônoma.

Suas responsabilidades incluem:
1. Validar o texto recebido (não vazio, dentro do limite de caracteres).
2. Converter o texto em áudio (síntese de voz) usando a biblioteca gTTS
   (Google Text-to-Speech), rodando a conversão em uma thread separada
   para não bloquear o event loop assíncrono do FastAPI.
3. Salvar o arquivo MP3 gerado em uma pasta local, com um nome único
   (UUID) para evitar colisões entre requisições simultâneas.
4. Limpar automaticamente arquivos antigos, para que a pasta de áudios
   não cresça indefinidamente com o tempo (nenhum processo externo os
   apaga).
5. Resolver com segurança o caminho de um arquivo já gerado, para que a
   rota de download (GET /api/audio/audios/{nome_arquivo}) não sirva
   nada fora da pasta de áudios nem arquivos que não sigam o padrão de
   nomes criado por este próprio serviço (proteção contra path
   traversal).

Este módulo NÃO define rotas HTTP — ele é consumido pelo router em
app/routers/audio.py, seguindo o mesmo padrão de separação de
responsabilidades (rota vs. regra de negócio) usado pelos demais serviços
do projeto (menu_service.py, evolution_service.py etc.).

Variáveis de ambiente:
    AUDIO_DIR           Pasta onde os MP3s gerados são salvos (padrão: audios_gerados)
    AUDIO_TTS_LANG      Idioma da síntese de voz (padrão: pt-br)
    AUDIO_MAX_CHARS     Tamanho máximo de texto aceito por requisição (padrão: 2000)
    AUDIO_TTL_MINUTES   Tempo de vida dos arquivos antes da limpeza automática (padrão: 60)
================================================================================
"""

import asyncio
import logging
import os
import re
import time
import uuid
from pathlib import Path
from typing import Optional

from gtts import gTTS
from gtts.tts import gTTSError

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. CONFIGURAÇÃO (VARIÁVEIS DE AMBIENTE)
# ==============================================================================
# Todos os parâmetros do serviço são configuráveis via .env, seguindo o mesmo
# padrão do restante do projeto (ex: evolution_service.py). Isso evita
# "hardcoding" e permite ajustar o comportamento por ambiente (dev/prod) sem
# alterar código.
AUDIO_DIR = Path(os.getenv("AUDIO_DIR", "audios_gerados"))     # pasta de destino dos MP3s
TTS_LANG = os.getenv("AUDIO_TTS_LANG", "pt-br")                # idioma da síntese de voz
MAX_CHARS = int(os.getenv("AUDIO_MAX_CHARS", "2000"))          # limite de caracteres por requisição
TTL_MINUTES = int(os.getenv("AUDIO_TTL_MINUTES", "60"))        # tempo de vida dos áudios gerados

# Padrão exato dos nomes de arquivo gerados por este serviço (ver gerar_audio).
# Usado por caminho_audio() para garantir que só arquivos criados por nós
# sejam servidos de volta ao cliente.
_NOME_ARQUIVO_RE = re.compile(r"^memorando_[0-9a-f]{8}\.mp3$")

# Garante que a pasta de áudios exista antes da primeira requisição.
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# 2. EXCEÇÕES DE VALIDAÇÃO
# ==============================================================================
# Exceções específicas para que o router (app/routers/audio.py) possa
# traduzi-las em códigos HTTP apropriados (400 Bad Request), em vez de
# devolver um genérico erro 500 para um problema de entrada do usuário.

class TextoVazioError(ValueError):
    """Texto informado está vazio ou contém apenas espaços."""


class TextoMuitoLongoError(ValueError):
    """Texto informado excede o limite definido em AUDIO_MAX_CHARS."""


# ==============================================================================
# 3. LIMPEZA AUTOMÁTICA DE ÁUDIOS ANTIGOS
# ==============================================================================

def _limpar_audios_antigos() -> None:
    """
    Remove arquivos gerados há mais de AUDIO_TTL_MINUTES.

    Como cada chamada a gerar_audio() cria um novo arquivo MP3 e nada os
    apaga automaticamente, a pasta cresceria para sempre sem esta rotina.
    É chamada no início de cada geração para manter a pasta sob controle
    sem depender de um job/cron externo.
    """
    limite = time.time() - (TTL_MINUTES * 60)
    for arquivo in AUDIO_DIR.glob("memorando_*.mp3"):
        try:
            if arquivo.stat().st_mtime < limite:
                arquivo.unlink()
        except OSError:
            logger.warning("audio_service | falha ao remover %s", arquivo.name)


# ==============================================================================
# 4. GERAÇÃO DO ÁUDIO (TEXTO → FALA)
# ==============================================================================

def _gerar_mp3_sync(texto: str, nome_arquivo: str) -> None:
    """
    Converte o texto em MP3 usando gTTS e salva no disco.

    Função síncrona/bloqueante de propósito: gTTS faz uma chamada de rede
    (Google Translate TTS) e escreve em disco, nenhuma das duas coisas é
    assíncrona nativamente. É executada via asyncio.to_thread() por quem
    a chama, para não travar o event loop do FastAPI.
    """
    tts = gTTS(text=texto, lang=TTS_LANG, slow=False)
    tts.save(str(AUDIO_DIR / nome_arquivo))


async def gerar_audio(texto: str) -> dict:
    """
    Converte um texto em áudio MP3 (síntese de voz) e retorna o nome do
    arquivo gerado, pronto para ser servido por
    GET /api/audio/audios/{nome_arquivo}.

    Levanta TextoVazioError ou TextoMuitoLongoError se a entrada for
    inválida, e gTTSError se a síntese de voz falhar (ex: serviço do
    Google indisponível).
    """
    # Validação de entrada: nunca chamamos a API externa com texto vazio
    # ou fora do limite aceitável.
    texto = (texto or "").strip()
    if not texto:
        raise TextoVazioError("Texto vazio")
    if len(texto) > MAX_CHARS:
        raise TextoMuitoLongoError(f"Texto excede o limite de {MAX_CHARS} caracteres")

    # Aproveita a chamada para manter a pasta de áudios enxuta.
    _limpar_audios_antigos()

    # Nome único por requisição (evita colisão entre gerações simultâneas).
    nome_arquivo = f"memorando_{uuid.uuid4().hex[:8]}.mp3"

    try:
        # gTTS é síncrono/bloqueante; roda em thread separada para não
        # travar o event loop enquanto espera a resposta do Google.
        await asyncio.to_thread(_gerar_mp3_sync, texto, nome_arquivo)
    except gTTSError as e:
        logger.error("audio_service | gerar_audio | falha na síntese de voz | %s", e)
        raise

    return {"arquivo": nome_arquivo}


# ==============================================================================
# 5. RESOLUÇÃO SEGURA DO CAMINHO DE UM ÁUDIO JÁ GERADO
# ==============================================================================

def caminho_audio(nome_arquivo: str) -> Optional[Path]:
    """
    Resolve o caminho de um arquivo de áudio já gerado.

    Valida o nome contra o padrão exato criado por gerar_audio
    (_NOME_ARQUIVO_RE) antes de tocar no sistema de arquivos. Isso evita
    path traversal (ex: "../../etc/passwd") e impede que a rota de
    download sirva qualquer outro arquivo que porventura exista dentro
    de AUDIO_DIR.

    Retorna None se o nome não bater com o padrão ou se o arquivo não
    existir; quem chama (o router) deve traduzir isso em um 404.
    """
    if not _NOME_ARQUIVO_RE.fullmatch(nome_arquivo):
        return None
    caminho = AUDIO_DIR / nome_arquivo
    return caminho if caminho.is_file() else None
