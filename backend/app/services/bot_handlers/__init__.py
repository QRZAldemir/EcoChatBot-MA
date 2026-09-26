"""
================================================================================
PROJETO.......: EcoChatBot-MA — Sistema de Atendimento Digital Configurável
ARQUIVO.......: bot_handlers/__init__.py
AUTOR.........: Aldemir Queiroz
DATA..........: 08/09/2026
VERSÃO........: 1.0.0

DESCRIÇÃO
Módulo de handlers do bot de atendimento. Este arquivo é o ponto de entrada
do pacote bot_handlers e expõe as classes e funções principais para uso
externo, mantendo o encapsulamento e a organização modular.

CONCEITO PYTHON - PACOTES:
Em Python, um diretório com __init__.py é considerado um "pacote" (package).
Isso permite importar múltiplos módulos como uma unidade coesa:

    from bot_handlers import DepartamentoHandler, HandlerFactory
    
Sem __init__.py, o Python não reconheceria o diretório como pacote importável.

RESPONSABILIDADE
Este arquivo define a API pública do módulo — o que outros arquivos do
projeto podem importar e usar. Tudo que NÃO estiver aqui fica "escondido"
(encapsulado) dentro do pacote.
================================================================================
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTAÇÕES PÚBLICAS
# ─────────────────────────────────────────────────────────────────────────────
# "from .modulo import Classe" → importa do próprio pacote (ponto = relativo)
# 
# Isso permite que outros arquivos do projeto façam:
#   from bot_handlers import DepartamentoHandler
#   from bot_handlers import HandlerFactory
#
# Em vez de:
#   from bot_handlers.core import DepartamentoHandler
#   from bot_handlers.factory import HandlerFactory
# ─────────────────────────────────────────────────────────────────────────────

from .core import DepartamentoHandler
from .factory import HandlerFactory

# ─────────────────────────────────────────────────────────────────────────────
# __all__ — LISTA DE EXPORTAÇÕES PÚBLICAS
# ─────────────────────────────────────────────────────────────────────────────
# Quando alguém fizer: from bot_handlers import *
# Apenas os nomes listados em __all__ serão importados.
#
# Isso é uma convenção Python para controlar a API pública do módulo.
# Similar ao "exports" no Node.js ou "public" em outras linguagens.
# ─────────────────────────────────────────────────────────────────────────────

__all__ = [
    "DepartamentoHandler",  # Classe base abstrata para todos os handlers
    "HandlerFactory"        # Fábrica para criar handlers dinamicamente
]