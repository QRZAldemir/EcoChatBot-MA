from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services import audio_service

router = APIRouter()


class GerarAudioRequest(BaseModel):
    texto: str


class GerarAudioResponse(BaseModel):
    sucesso: bool
    arquivo: str
    url: str


@router.post("/gerar", response_model=GerarAudioResponse)
async def gerar_audio(body: GerarAudioRequest, request: Request):
    """
    Converte um texto (ex: conteúdo de um Memorando) em áudio MP3 via
    síntese de voz, para acessibilidade de usuários com deficiência
    visual ou motora.
    """
    try:
        resultado = await audio_service.gerar_audio(body.texto)
    except audio_service.TextoVazioError:
        raise HTTPException(status_code=400, detail="Texto vazio")
    except audio_service.TextoMuitoLongoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Falha ao gerar áudio")

    arquivo = resultado["arquivo"]
    return GerarAudioResponse(
        sucesso=True,
        arquivo=arquivo,
        url=str(request.base_url) + f"api/audio/audios/{arquivo}",
    )


@router.get("/audios/{nome_arquivo}")
def servir_audio(nome_arquivo: str):
    """Serve um arquivo de áudio previamente gerado por POST /gerar."""
    caminho = audio_service.caminho_audio(nome_arquivo)
    if not caminho:
        raise HTTPException(status_code=404, detail="Áudio não encontrado")
    return FileResponse(caminho, media_type="audio/mpeg")
