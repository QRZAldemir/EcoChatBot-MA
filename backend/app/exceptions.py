"""
================================================================================
PROJETO: EcoChatBotMarcx - Omnichannel SaaS
MÓDULO: exceptions.py
AUTOR: Aldemir Queiroz
CONTATO: [Inserir E-mail] | [Inserir LinkedIn] | [Inserir GitHub]
DATA: 2024-05-20
================================================================================
PROPÓSITO:
Definir a hierarquia de exceções de domínio (Domain Errors). Garante que 
erros de regra de negócio sejam tratados de forma centralizada e retornem 
códigos HTTP adequados via Exception Handlers globais.

ARQUITETURA E INTEGRAÇÃO:
Camada de Domínio. Importada e lançada pelos Services (Unit of Work) e 
capturada pelos Exception Handlers na camada de apresentação.
================================================================================
"""
class DomainError(Exception):
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class CanalNaoEncontradoError(DomainError):
    def __init__(self): super().__init__("Canal não encontrado.", "CANAL_NOT_FOUND")

class CanalNomeDuplicadoError(DomainError):
    def __init__(self): super().__init__("Nome do canal já existe.", "CANAL_NAME_DUPLICATED")

class CanalTipoInvalidoError(DomainError):
    def __init__(self): super().__init__("Tipo de canal inválido.", "CANAL_INVALID_TYPE")

class CanalIdentificadorInvalidoError(DomainError):
    def __init__(self): super().__init__("Identificador do canal inválido.", "CANAL_INVALID_ID")

class RecursoInvalidoError(DomainError):
    def __init__(self): super().__init__("Recurso inválido ou malformado.", "INVALID_RESOURCE")

class AtendimentoNaoEncontradoError(DomainError):
    def __init__(self): super().__init__("Atendimento não encontrado.", "ATTENDANCE_NOT_FOUND")

class AtendimentoFinalizadoError(DomainError):
    def __init__(self): super().__init__("Atendimento já finalizado.", "ATTENDANCE_CLOSED")