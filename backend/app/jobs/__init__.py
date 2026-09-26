"""
================================================================================
Projeto: Sistema de Backups e Tarefas Agendadas (EcoChatBot-MA)
Autor: Aldemir Queiroz
Data: 24 de Maio de 2024
Funcionalidade: Inicialização do pacote `jobs`.

================================================================================
ESTADO ATUAL — LEIA ANTES DE USAR
--------------------------------------------------------------------------------
`app/jobs/celery_app.py` e `app/jobs/backup.py` estão com 0 bytes: não existe
nenhuma instância do Celery nem nenhuma tarefa de backup escritas neste
repositório.

Por isso este `__init__.py` NÃO importa `celery_app`. Antes ele fazia
`from .celery_app import celery_app`, o que derrubava o pacote `jobs` inteiro
(2 módulos) com `ImportError`, porque um módulo vazio não define esse nome.

Não foi criada uma instância de Celery provisória para "fazer o import
passar": broker, backend de resultados e serializador são decisões de
infraestrutura, e um Celery configurado pela metade falharia em produção de
forma mais difícil de diagnosticar.

Para usar workers futuramente, o caminho será:
    celery -A app.jobs.celery_app worker --loglevel=info
"""

__all__: list[str] = []
