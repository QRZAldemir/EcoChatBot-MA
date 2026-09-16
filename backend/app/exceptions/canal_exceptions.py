"""
================================================================================
MÓDULO: app/exceptions/canal_exceptions.py
AUTOR: Aldemir Queiroz
DATA: 2026-09-16
VERSÃO: 1.0.0
OBJETIVO: Define exceções específicas para domínio de canais.
PASTA: backend/app/exceptions/
================================================================================
"""


class CanalException(Exception):
    """Classe base para exceções de canal."""
    pass


class CanalNaoEncontradoError(CanalException):
    """Canal não encontrado ou sem permissão de acesso."""
    pass


class CanalNomeDuplicadoError(CanalException):
    """Nome de canal já existe para este tenant."""
    pass


class CanalTipoInvalidoError(CanalException):
    """Tipo de canal não é suportado."""
    pass


class CanalConfiguracaoInvalidaError(CanalException):
    """Configurações do canal estão em formato inválido."""
    pass


class CanalWebhookError(CanalException):
    """Erro ao configurar webhook do canal."""
    pass