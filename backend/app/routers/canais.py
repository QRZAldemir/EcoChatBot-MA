# ==============================================================================
# Autor: Aldemir Queiroz
# Data: 24/05/2024
# ==============================================================================
# Arquivo: canais.py (Pasta: app/routers)
#
# DESCRIÇÃO:
# Este arquivo define as rotas (endpoints) da API responsáveis pelas operações 
# de "Canal". Ele atua como a camada de apresentação (Router/Controller),
# recebendo as requisições HTTP, validando os dados de entrada (via Pydantic),
# delegando a lógica de negócios para a camada de Service (CanalService)
# e retornando as respostas padronizadas.
# ==============================================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services.canal_service import CanalService
from app.schemas import CanalCreate, CanalUpdate, CanalResponse

# Inicializa o roteador do FastAPI. 
# Todas as rotas definidas aqui serão registradas sob um prefixo no arquivo main.py
router = APIRouter()


# ==============================================================================
# ROTAS DE LEITURA / CONSULTA (GET)
# ==============================================================================

@router.get("/", response_model=List[CanalResponse])
def listar_canais(db: Session = Depends(get_db)):
    """
    Lista todos os canais cadastrados no sistema.
    
    Retorna:
    - List[CanalResponse]: Uma lista de todos os canais.
    """
    return CanalService.listar_canais(db)


@router.get("/{canal_id}", response_model=CanalResponse)
def buscar_canal(canal_id: int, db: Session = Depends(get_db)):
    """
    Busca um canal específico pelo seu ID.
    
    Parâmetros:
    - canal_id (int): O ID do canal a ser buscado.
    
    Retorna:
    - CanalResponse: O canal encontrado.
    
    Lança:
    - HTTPException: Se o canal não for encontrado (status 404).
    """
    canal = CanalService.buscar_por_id(db, canal_id)
    if not canal:
        raise HTTPException(status_code=404, detail="Canal não encontrado")
    return canal


# ==============================================================================
# ROTAS DE ESCRITA / AÇÃO (POST, PUT, DELETE)
# ==============================================================================

@router.post("/", response_model=CanalResponse, status_code=201)
def criar_canal(canal: CanalCreate, db: Session = Depends(get_db)):
    """
    Cria um novo canal no sistema.
    
    Parâmetros:
    - canal (CanalCreate): Dados do canal a ser criado.
    
    Retorna:
    - CanalResponse: O canal recém-criado.
    
    Lança:
    - HTTPException: Se já existir um canal com o mesmo nome (status 400).
    """
    try:
        # A verificação de duplicidade agora é feita internamente no CanalService
        return CanalService.criar_canal(db, canal)
    except ValueError as e:
        # Converte o ValueError em um HTTPException com status 400
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{canal_id}", response_model=CanalResponse)
def atualizar_canal(canal_id: int, canal: CanalUpdate, db: Session = Depends(get_db)):
    """
    Atualiza um canal existente no sistema.
    
    Parâmetros:
    - canal_id (int): O ID do canal a ser atualizado.
    - canal (CanalUpdate): Dados atualizados do canal.
    
    Retorna:
    - CanalResponse: O canal atualizado.
    
    Lança:
    - HTTPException: Se o canal não for encontrado (status 404) ou
                    se já existir um canal com o mesmo nome (status 400).
    """
    try:
        canal_atualizado = CanalService.atualizar_canal(db, canal_id, canal)
        if not canal_atualizado:
            raise HTTPException(status_code=404, detail="Canal não encontrado")
        return canal_atualizado
    except ValueError as e:
        # Converte o ValueError em um HTTPException com status 400
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{canal_id}", status_code=204)
def deletar_canal(canal_id: int, db: Session = Depends(get_db)):
    """
    Deleta um canal do sistema.
    
    Parâmetros:
    - canal_id (int): O ID do canal a ser deletado.
    
    Retorna:
    - None: Não há conteúdo para retornar após a exclusão (status 204).
    
    Lança:
    - HTTPException: Se o canal não for encontrado (status 404).
    """
    sucesso = CanalService.deletar_canal(db, canal_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Canal não encontrado")
    return None
