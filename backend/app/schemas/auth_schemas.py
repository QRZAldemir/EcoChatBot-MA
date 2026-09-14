"""
================================================================================
MÓDULO: app/schemas/auth.py
AUTOR: Aldemir Queiroz
DATA: 2026
VERSÃO: 1.0.0

DESCRIÇÃO:
    Define os contratos de dados (Schemas Pydantic) para os endpoints de 
    autenticação. O Pydantic atua como um validador rigoroso, garantindo que 
    os dados recebidos via HTTP (JSON) estejam no formato esperado antes de 
    chegarem à lógica de negócio, prevenindo erros de tipo e injeções.

PÚBLICO-ALVO DA DOCUMENTAÇÃO:
    Desenvolvedores que precisam entender a estrutura dos payloads de login 
    e como o FastAPI utiliza esses schemas para gerar a documentação Swagger.
================================================================================
"""

from pydantic import BaseModel, EmailStr, Field


# ==============================================================================
# SCHEMA DE ENTRADA: DADOS DE LOGIN
# ==============================================================================
class LoginRequest(BaseModel):
    """
    Schema para a requisição de login (POST /api/auth/login).
    
    O FastAPI usará este schema para:
    1. Validar se o JSON enviado pelo cliente contém os campos obrigatórios.
    2. Validar se o campo 'email' possui um formato de e-mail válido.
    3. Gerar automaticamente a documentação no Swagger UI (/docs).
    """
    email: EmailStr = Field(
        ..., 
        description="E-mail do usuário para autenticação.", 
        examples=["admin@empresa.com"]
    )
    senha: str = Field(
        ..., 
        min_length=6, 
        description="Senha em texto puro (será comparada com o hash no banco).", 
        examples=["MinhaSenhaForte123!"]
    )


# ==============================================================================
# SCHEMA DE SAÍDA: RESPOSTA DO TOKEN
# ==============================================================================
class TokenResponse(BaseModel):
    """
    Schema para a resposta de sucesso do login.
    
    Segue o padrão OAuth2 para que bibliotecas de frontend e ferramentas 
    como Postman reconheçam automaticamente o token retornado.
    """
    access_token: str = Field(
        ..., 
        description="Token JWT assinado. Deve ser enviado no header 'Authorization: Bearer <token>'."
    )
    token_type: str = Field(
        default="bearer", 
        description="Tipo do token (padrão OAuth2)."
    )
    user_id: int = Field(
        ..., 
        description="ID do usuário autenticado (útil para o frontend armazenar o contexto)."
    )
    empresa_id: int | None = Field(
        default=None, 
        description="ID da empresa (tenant) do usuário. None se for super_admin."
    )