"""
==============================================================================
PROJETO: EcoChatBotMarcx
MÓDULO: app/exceptions.py
AUTOR: Aldemir Queiroz
DATA: 2024-05-24
==============================================================================

DESCRIÇÃO:
Este módulo centraliza a hierarquia de exceções de domínio e de infraestrutura 
do sistema EcoChatBotMarcx. Ele define uma classe base (`AppError`) e suas 
respectivas subclasses, categorizadas por contexto de negócio (Canais, 
Atendimento, Usuário, Tenant) e camada de acesso a dados.

OBJETIVO:
Fornecer um mecanismo unificado e tipado para o tratamento de erros, permitindo 
que a camada de apresentação (FastAPI) capture exceções específicas e retorne 
respostas HTTP padronizadas, com códigos de status e mensagens amigáveis 
adequados, promovendo o desacoplamento entre as regras de negócio e a API.

INSTRUÇÕES DE USO:
1. Para criar uma nova exceção, herde de `AppError` (para erros de domínio) ou 
   de `RepositoryError` (para erros de infraestrutura).
2. Sobrescreva o método `__init__` para definir uma mensagem padrão e um 
   `status_code` HTTP apropriado.
3. Na camada de Serviço (Service), levante as exceções utilizando `raise`.
4. Registre as exceções no FastAPI utilizando `@app.exception_handler()` para 
   mapeá-las para `JSONResponse`.
==============================================================================
"""
from __future__ import annotations


class AppError(Exception):
    """Classe base para todas as exceções da aplicação."""
    
    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


# ==============================================================================
# Exceções de Infraestrutura / Acesso a Dados
# ==============================================================================

class RepositoryError(AppError):
    """Erro genérico de infraestrutura ou acesso a dados."""
    def __init__(self, message: str = "Erro interno no repositório de dados.") -> None:
        super().__init__(message, status_code=500)


class EntidadeNaoEncontradaError(RepositoryError):
    """Erro quando um registro não é encontrado na base de dados."""
    def __init__(self, message: str = "Entidade não encontrada.") -> None:
        super().__init__(message, status_code=404)


class ViolacaoDeUnicidadeError(RepositoryError):
    """Erro quando há violação de constraint de unicidade no banco de dados."""
    def __init__(self, message: str = "Violação de unicidade de dados.") -> None:
        super().__init__(message, status_code=409)


class ErroDeConexaoError(RepositoryError):
    """Erro de conexão com o banco de dados."""
    def __init__(self, message: str = "Falha na conexão com o banco de dados.") -> None:
        super().__init__(message, status_code=500)


# ==============================================================================
# Exceções de Domínio de Canais e Comunicação
# ==============================================================================

class CanalNaoEncontradoError(AppError):
    def __init__(self, message: str = "Canal de comunicação não encontrado.") -> None:
        super().__init__(message, status_code=404)

class CanalNomeDuplicadoError(AppError):
    def __init__(self, message: str = "Já existe um canal com este nome.") -> None:
        super().__init__(message, status_code=409)

class CanalTipoInvalidoError(AppError):
    def __init__(self, message: str = "O tipo do canal informado é inválido.") -> None:
        super().__init__(message, status_code=400)

class CanalIdentificadorInvalidoError(AppError):
    def __init__(self, message: str = "O identificador do canal é inválido.") -> None:
        super().__init__(message, status_code=400)

class RecursoInvalidoError(AppError):
    def __init__(self, message: str = "O recurso solicitado é inválido.") -> None:
        super().__init__(message, status_code=400)


# ==============================================================================
# Exceções de Atendimento e FSM (Finite State Machine)
# ==============================================================================

class AtendimentoNaoEncontradoError(AppError):
    def __init__(self, message: str = "Atendimento não encontrado.") -> None:
        super().__init__(message, status_code=404)

class AtendimentoFinalizadoError(AppError):
    def __init__(self, message: str = "O atendimento já foi finalizado.") -> None:
        super().__init__(message, status_code=400)

class AtendimentoInvalidStatusError(AppError):
    def __init__(self, message: str = "Transição de status do atendimento inválida.") -> None:
        super().__init__(message, status_code=400)

class AtendimentoPermissionDeniedError(AppError):
    def __init__(self, message: str = "Você não tem permissão para alterar este atendimento.") -> None:
        super().__init__(message, status_code=403)


# ==============================================================================
# Exceções de Usuário e Segurança
# ==============================================================================

class UsuarioNaoEncontradoError(AppError):
    def __init__(self, message: str = "Usuário não encontrado.") -> None:
        super().__init__(message, status_code=404)

class UsuarioAlreadyExistsError(AppError):
    def __init__(self, message: str = "Usuário já cadastrado.") -> None:
        super().__init__(message, status_code=409)

class UsuarioInvalidPasswordError(AppError):
    def __init__(self, message: str = "Senha inválida.") -> None:
        super().__init__(message, status_code=401)

class UsuarioInactiveError(AppError):
    def __init__(self, message: str = "Usuário inativo.") -> None:
        super().__init__(message, status_code=403)

class UsuarioPermissionDeniedError(AppError):
    def __init__(self, message: str = "Permissão negada para este usuário.") -> None:
        super().__init__(message, status_code=403)


# ==============================================================================
# Exceções de Tenant / Cliente (Multi-Tenant)
# ==============================================================================

class ClienteNaoEncontradoError(AppError):
    def __init__(self, message: str = "Cliente (Tenant) não encontrado.") -> None:
        super().__init__(message, status_code=404)

class ClientePermissionDeniedError(AppError):
    def __init__(self, message: str = "Acesso negado para este tenant.") -> None:
        super().__init__(message, status_code=403)