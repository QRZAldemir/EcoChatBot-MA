"""
================================================================================
MÓDULO: app/routers/audio.py
AUTOR: Aldemir Queiroz
DATA: 2026
VERSÃO: 1.1.0 (Refatorado para segurança, logging e robustez)

DESCRIÇÃO:
    Endpoints para síntese de voz (Text-to-Speech) e servimento de arquivos 
    de áudio. Permite que usuários convertam textos (ex: Memorandos) em áudio 
    MP3 para acessibilidade de usuários com deficiência visual ou motora.

ARQUITETURA:
    - POST /api/audio/gerar: Converte texto em áudio MP3 via audio_service.
    - GET /api/audio/audios/{nome_arquivo}: Serve arquivos de áudio gerados.
    
    Ambos os endpoints exigem autenticação (JWT válido) e o nível mínimo 
    "atendente" para acesso.

SEGURANÇA:
    - Validação rigorosa do nome do arquivo para prevenir Path Traversal.
    - Controle de acesso em todos os endpoints (exigir_nivel_minimo).
    - Logs de auditoria para geração e acesso a áudios.

REGISTRO EM main.py:
    app.include_router(audio.router, prefix="/api/audio", tags=["Áudio"])
================================================================================
"""

import logging
import os
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.security import exigir_nivel_minimo, obter_usuario_atual
from app.services import audio_service

router = APIRouter()
logger = logging.getLogger(__name__)

# ==============================================================================
# CONSTANTES DE SEGURANÇA E VALIDAÇÃO
# ==============================================================================

# Regex para validar nomes de arquivo seguros (apenas alfanuméricos, hífens e underscores)
# Previne Path Traversal e injeção de caracteres especiais
_NOME_ARQUIVO_REGEX = re.compile(r'^[a-zA-Z0-9_\-]+\.mp3$')

# Tamanho máximo do texto para conversão (em caracteres)
# Deve ser consistente com o limite do audio_service
MAX_TEXTO_CARACTERES = 5000


# ==============================================================================
# SCHEMAS PYDANTIC (CONTRATOS DE DADOS)
# ==============================================================================

class GerarAudioRequest(BaseModel):
    """
    Schema de entrada para geração de áudio.
    
    Validações:
    - texto: obrigatório, entre 1 e MAX_TEXTO_CARACTERES caracteres.
    """
    texto: str = Field(
        ...,
        min_length=1,
        max_length=MAX_TEXTO_CARACTERES,
        description="Texto a ser convertido em áudio (entre 1 e 5000 caracteres).",
        examples=["Este é um memorando importante sobre as novas políticas da empresa."]
    )


class GerarAudioResponse(BaseModel):
    """Schema de saída com informações do áudio gerado."""
    sucesso: bool = Field(..., description="Indica se a geração foi bem-sucedida.")
    arquivo: str = Field(..., description="Nome do arquivo de áudio gerado.")
    url: str = Field(..., description="URL completa para acessar o áudio gerado.")


# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================

def _validar_nome_arquivo(nome_arquivo: str) -> bool:
    """
    Valida se o nome do arquivo é seguro (previne Path Traversal).
    
    Regras:
    - Deve conter apenas caracteres alfanuméricos, hífens e underscores.
    - Deve terminar com a extensão .mp3.
    - Não pode conter barras, pontos duplos ou outros caracteres especiais.
    
    Args:
        nome_arquivo (str): Nome do arquivo a ser validado.
        
    Returns:
        bool: True se o nome for seguro, False caso contrário.
    """
    if not nome_arquivo:
        return False
    
    # Verifica se o nome corresponde ao regex seguro
    if not _NOME_ARQUIVO_REGEX.match(nome_arquivo):
        return False
    
    # Verificação adicional: garante que não há traversal de diretórios
    # (mesmo que o regex já previna, é uma defesa em profundidade)
    caminho_normalizado = os.path.normpath(nome_arquivo)
    if caminho_normalizado.startswith('..') or os.sep in caminho_normalizado:
        return False
    
    return True


# ==============================================================================
# ENDPOINT: GERAR ÁUDIO (TEXT-TO-SPEECH)
# ==============================================================================

@router.post(
    "/gerar",
    response_model=GerarAudioResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exigir_nivel_minimo("atendente"))]
)
async def gerar_audio(
    body: GerarAudioRequest,
    request: Request,
    usuario=Depends(obter_usuario_atual)
):
    """
    Converte um texto em áudio MP3 via síntese de voz.
    
    Este endpoint é útil para acessibilidade, permitindo que usuários com 
    deficiência visual ou motora ouçam o conteúdo de Memorandos e outros 
    documentos em vez de lê-los.
    
    Fluxo:
    1. Valida o texto de entrada (tamanho, conteúdo).
    2. Chama o audio_service para gerar o MP3.
    3. Retorna o nome do arquivo e a URL para acesso.
    
    Args:
        body (GerarAudioRequest): Texto a ser convertido.
        request (Request): Objeto de requisição do FastAPI (para construir URL).
        usuario (Usuario): Usuário autenticado (injetado pela dependência).
        
    Returns:
        GerarAudioResponse: Contém o nome do arquivo e a URL de acesso.
        
    Raises:
        HTTPException 400: Se o texto estiver vazio ou for muito longo.
        HTTPException 500: Se houver falha interna na geração do áudio.
    """
    logger.info(
        "audio | Geração de áudio solicitada | user_id=%s | texto_length=%d",
        usuario.id, len(body.texto)
    )
    
    try:
        resultado = await audio_service.gerar_audio(body.texto)
    except audio_service.TextoVazioError:
        logger.warning("audio | Texto vazio recebido | user_id=%s", usuario.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O texto não pode estar vazio."
        )
    except audio_service.TextoMuitoLongoError as e:
        logger.warning(
            "audio | Texto muito longo | user_id=%s | length=%d | max=%d",
            usuario.id, len(body.texto), MAX_TEXTO_CARACTERES
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Log detalhado no servidor para depuração
        logger.exception(
            "audio | Falha interna ao gerar áudio | user_id=%s | erro=%s",
            usuario.id, str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha interna ao gerar o áudio. Tente novamente mais tarde."
        )
    
    arquivo = resultado["arquivo"]
    
    # CORREÇÃO: Usa request.url_for para construir a URL de forma robusta
    # Em vez de concatenação de string, que pode quebrar se o prefixo mudar
    try:
        url_audio = str(request.url_for("servir_audio", nome_arquivo=arquivo))
    except Exception:
        # Fallback caso a rota não seja encontrada (ex: teste sem prefixo)
        url_audio = f"{str(request.base_url).rstrip('/')}/api/audio/audios/{arquivo}"
    
    logger.info(
        "audio | Áudio gerado com sucesso | user_id=%s | arquivo=%s",
        usuario.id, arquivo
    )
    
    return GerarAudioResponse(
        sucesso=True,
        arquivo=arquivo,
        url=url_audio,
    )


# ==============================================================================
# ENDPOINT: SERVIR ARQUIVO DE ÁUDIO
# ==============================================================================

@router.get(
    "/audios/{nome_arquivo}",
    name="servir_audio",  # Nome da rota para uso em url_for
    dependencies=[Depends(exigir_nivel_minimo("atendente"))]  # CORREÇÃO: Adicionado controle de acesso
)
async def servir_audio(
    nome_arquivo: str,
    usuario=Depends(obter_usuario_atual)
) -> FileResponse:
    """
    Serve um arquivo de áudio previamente gerado por POST /gerar.
    
    SEGURANÇA:
    - Valida o nome do arquivo para prevenir Path Traversal.
    - Exige autenticação (JWT válido) e nível mínimo "atendente".
    - Verifica se o arquivo existe e é um MP3 válido.
    
    Args:
        nome_arquivo (str): Nome do arquivo de áudio (ex: "memorando_123.mp3").
        usuario (Usuario): Usuário autenticado (injetado pela dependência).
        
    Returns:
        FileResponse: O arquivo de áudio com Content-Type audio/mpeg.
        
    Raises:
        HTTPException 400: Se o nome do arquivo for inválido (Path Traversal).
        HTTPException 404: Se o arquivo não for encontrado.
    """
    # ── 1. VALIDAÇÃO DE SEGURANÇA (PREVENÇÃO DE PATH TRAVERSAL) ──
    if not _validar_nome_arquivo(nome_arquivo):
        logger.warning(
            "audio | Tentativa de acesso com nome de arquivo inválido | user_id=%s | nome=%s",
            usuario.id, nome_arquivo
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de arquivo inválido."
        )
    
    # ── 2. BUSCA DO ARQUIVO ──
    caminho = audio_service.caminho_audio(nome_arquivo)
    
    if not caminho:
        logger.warning(
            "audio | Áudio não encontrado | user_id=%s | arquivo=%s",
            usuario.id, nome_arquivo
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Áudio não encontrado."
        )
    
    # ── 3. VERIFICAÇÃO DE EXISTÊNCIA E TIPO ──
    caminho_path = Path(caminho)
    if not caminho_path.exists() or not caminho_path.is_file():
        logger.error(
            "audio | Arquivo não existe no disco | user_id=%s | caminho=%s",
            usuario.id, caminho
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Áudio não encontrado."
        )
    
    # Verificação adicional: garante que é um arquivo MP3
    if caminho_path.suffix.lower() != '.mp3':
        logger.error(
            "audio | Arquivo não é MP3 | user_id=%s | caminho=%s",
            usuario.id, caminho
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de arquivo não suportado."
        )
    
    logger.info(
        "audio | Áudio servido | user_id=%s | arquivo=%s",
        usuario.id, nome_arquivo
    )
    
    # ── 4. RESPOSTA COM CACHE CONTROL ──
    # Áudios gerados são imutáveis, então podemos usar cache agressivo
    return FileResponse(
        path=caminho,
        media_type="audio/mpeg",
        filename=nome_arquivo,
        headers={
            "Cache-Control": "public, max-age=86400",  # Cache por 24 horas
            "X-Content-Type-Options": "nosniff",  # Previne MIME sniffing
        }
    )