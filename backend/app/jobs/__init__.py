"""
================================================================================
Projeto: Sistema de Backup de Dados (MongoDB -> PostgreSQL)
Autor: Aldemir Queiroz
Data: 24 de Maio de 2024
Funcionalidade: Inicialização do pacote Python 'jobs', expondo a instância 
                do Celery para descoberta por workers distribuídos.
================================================================================
"""

# Expõe a instância principal da aplicação Celery.
# Isso permite que o worker seja iniciado utilizando o comando:
# celery -A jobs worker --loglevel=info
from .celery_app import celery_app

__all__ = ['celery_app']