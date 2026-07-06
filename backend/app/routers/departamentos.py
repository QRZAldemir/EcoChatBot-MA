# ==============================================================================
# Autor: Aldemir Queiroz
# Data: 24/05/2024
# ==============================================================================
# Arquivo: departamentos.py (Pasta: app/routers)
#
# DESCRIÇÃO:
# Este arquivo define as rotas (endpoints) da API responsáveis pelas operações 
# de "Departamento". Ele atua como a camada de apresentação (Router/Controller),
# recebendo as requisições HTTP, validando os dados de entrada (via Pydantic),
# delegando a lógica de negócios para a camada de Service (DepartamentoService)
# e retornando as respostas padronizadas.
# ==============================================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services.departamento_service import DepartamentoService
from app.schemas import DepartamentoCreate, DepartamentoUpdate, DepartamentoResponse

# Inicializa o roteador do FastAPI. 
# Todas as rotas definidas aqui serão registradas sob um prefixo no arquivo main.py
router = APIRouter()


# ==============================================================================
# ROTAS DE LEITURA / CONSULTA (GET)
# ==============================================================================

@router.get("/", response_model=List[DepartamentoResponse])
def listar_departamentos(db: Session = Depends(get_db)):
    """
    Lista todos os departamentos cadastrados no sistema.
    
    Retorna:
    - List[DepartamentoResponse]: Uma lista de todos os departamentos.
    """
    # Explicação:
    # - @router.get("/"): Define uma rota HTTP GET no endpoint raiz ("/")
    # - response_model=List[DepartamentoResponse]: Define o formato da resposta como uma lista de objetos DepartamentoResponse
    # - db: Session = Depends(get_db): Injeta uma sessão do banco de dados usando a função get_db
    # - DepartamentoService.listar_departamentos(db): Chama o método de serviço para listar todos os departamentos
    
    return DepartamentoService.listar_departamentos(db)


@router.get("/{departamento_id}", response_model=DepartamentoResponse)
def buscar_departamento(departamento_id: int, db: Session = Depends(get_db)):
    """
    Busca um departamento específico pelo seu ID.
    
    Parâmetros:
    - departamento_id (int): O ID do departamento a ser buscado.
    
    Retorna:
    - DepartamentoResponse: O departamento encontrado.
    
    Lança:
    - HTTPException: Se o departamento não for encontrado (status 404).
    """
    # Explicação:
    # - @router.get("/{departamento_id}"): Define uma rota GET com parâmetro de caminho (path parameter)
    # - departamento_id: int: Define que o parâmetro deve ser um inteiro
    # - DepartamentoService.buscar_por_id(db, departamento_id): Busca o departamento pelo ID
    # - if not departamento: Verifica se o departamento foi encontrado
    # - raise HTTPException: Lança um erro 404 caso o departamento não exista
    
    departamento = DepartamentoService.buscar_por_id(db, departamento_id)
    if not departamento:
        raise HTTPException(status_code=404, detail="Departamento não encontrado")
    return departamento


# ==============================================================================
# ROTAS DE ESCRITA / AÇÃO (POST, PUT, DELETE)
# ==============================================================================

@router.post("/", response_model=DepartamentoResponse, status_code=201)
def criar_departamento(departamento: DepartamentoCreate, db: Session = Depends(get_db)):
    """
    Cria um novo departamento no sistema.
    
    Parâmetros:
    - departamento (DepartamentoCreate): Dados do departamento a ser criado.
    
    Retorna:
    - DepartamentoResponse: O departamento recém-criado.
    """
    # Explicação:
    # - @router.post("/"): Define uma rota HTTP POST no endpoint raiz ("/")
    # - status_code=201: Define o status code padrão como 201 (Created)
    # - departamento: DepartamentoCreate: Define que o corpo da requisição (body) deve seguir o schema DepartamentoCreate
    # - DepartamentoService.criar_departamento(db, departamento): Chama o método de serviço para criar um novo departamento
    
    return DepartamentoService.criar_departamento(db, departamento)


@router.put("/{departamento_id}", response_model=DepartamentoResponse)
def atualizar_departamento(departamento_id: int, departamento: DepartamentoUpdate, db: Session = Depends(get_db)):
    """
    Atualiza um departamento existente no sistema.
    
    Parâmetros:
    - departamento_id (int): O ID do departamento a ser atualizado.
    - departamento (DepartamentoUpdate): Dados atualizados do departamento.
    
    Retorna:
    - DepartamentoResponse: O departamento atualizado.
    
    Lança:
    - HTTPException: Se o departamento não for encontrado (status 404).
    """
    # Explicação:
    # - @router.put("/{departamento_id}"): Define uma rota PUT com parâmetro de caminho
    # - DepartamentoUpdate: Schema para validar os dados de atualização (pode ser parcial)
    # - DepartamentoService.atualizar_departamento(db, departamento_id, departamento): Chama o método de serviço
    # - if not depto_atualizado: Verifica se a atualização foi bem sucedida
    
    depto_atualizado = DepartamentoService.atualizar_departamento(db, departamento_id, departamento)
    if not depto_atualizado:
        raise HTTPException(status_code=404, detail="Departamento não encontrado")
    return depto_atualizado


@router.delete("/{departamento_id}", status_code=204)
def deletar_departamento(departamento_id: int, db: Session = Depends(get_db)):
    """
    Deleta um departamento do sistema.
    
    Parâmetros:
    - departamento_id (int): O ID do departamento a ser deletado.
    
    Retorna:
    - None: Não há conteúdo para retornar após a exclusão (status 204).
    
    Lança:
    - HTTPException: Se o departamento não for encontrado (status 404).
    """
    # Explicação:
    # - @router.delete("/{departamento_id}"): Define uma rota DELETE com parâmetro de caminho
    # - status_code=204: Define o status code como 204 (No Content)
    # - DepartamentoService.deletar_departamento(db, departamento_id): Chama o método de serviço para deletar
    # - if not sucesso: Verifica se a exclusão foi bem sucedida
    # - return None: Não retorna conteúdo (padrão para status 204)
    
    sucesso = DepartamentoService.deletar_departamento(db, departamento_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Departamento não encontrado")
    return None
