# ==============================================================================
# Autor: Aldemir Queiroz
# Data: 24/05/2024
# Arquivo: exceptions.py
# ==============================================================================
# DESCRIÇÃO:
# Exceções customizadas para tratamento diferenciado de erros de negócio
# versus erros inesperados de infraestrutura.
# ==============================================================================


class NegocioException(Exception):
    """
    Exceção base para erros de regra de negócio.
    
    Utilizada quando uma operação falha devido a uma violação de regra
    de negócio (ex.: recurso não encontrado, validação de domínio, etc.).
    
    A mensagem é segura para exposição ao cliente da API.
    """
    def __init__(self, mensagem: str):
        self.mensagem = mensagem
        super().__init__(mensagem)


class RecursoNaoEncontradoException(NegocioException):
    """Recurso solicitado não existe no sistema."""
    pass


class ValidacaoNegocioException(NegocioException):
    """Violação de regra de negócio (ex.: transferência sem destino)."""
    pass


class ErroIntegracaoException(Exception):
    """
    Falha em integração externa (ex.: Evolution API, WhatsApp).
    
    NÃO deve ser exposta ao cliente — apenas logada internamente.
    """
    pass