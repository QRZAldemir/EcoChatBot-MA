"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Config (ponto único de settings)
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     config.py
@module   Backend / App / Core
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
    Reexporta `Settings` e `settings` a partir de `app/config.py`.

    37 arquivos fazem `from app.core.config import settings`, mas só
    `app/config.py` existia. Este módulo é um adaptador: NÃO duplica a
    definição de Settings, apenas aponta para ela. Assim a configuração
    continua tendo uma fonte única de verdade.

RELACIONAMENTO
──────────────
    app.config  (fonte única de Settings)
    app.core.security  (bcrypt síncrono)
    Consumidores: app/services/usuario_service.py, app/routers/usuario_routers.py,
                  app/services/webhook_service.py, app/integrations/*.py

REGRAS DE NEGÓCIO
─────────────────
    • A definição de Settings fica em `app/config.py`. Este arquivo é apenas
      façade — se uma variável de ambiente mudar, muda em um lugar só.
    • `settings` é instanciado na importação do módulo. Sem as variáveis de
      ambiente obrigatórias, o import falha — comportamento esperado e
      desejável: a aplicação não sobe com configuração incompleta.
"""


from app.config import Settings, settings  # noqa: F401

__all__ = ["Settings", "settings"]
