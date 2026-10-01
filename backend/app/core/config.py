"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Config Façade
Codinome: EcoChatBot-MA
────────────────────────────────────────────────────────────────────────────
@file     config.py
@module   Backend / App / Core
@author   Aldemir Queiroz
@since    2026
@version  1.1.0
────────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
Façade que reexporta `Settings` e `settings` a partir de `app.config`.

Por que este façade existe?
• Convenção de projeto: módulos de "core" ficam em `app.core.*`.
• Evita quebrar os 37+ módulos que já importam de `app.core.config`.
• Permite refatorar `app/config.py` no futuro sem impacto nos consumidores.

REGRAS DE NEGÓCIO
─────────────────
• NUNCA adicione lógica, classes ou validações aqui.
• A fonte única de verdade é `app.config`.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

# ==============================================================================
# VALIDAÇÃO DE DEPENDÊNCIA (Fail-Fast)
# ==============================================================================
try:
    from app.config import Settings as _Settings
    from app.config import settings as _settings
except ImportError as exc:
    raise ImportError(
        "Falha crítica: Não foi possível importar Settings de app.config. "
        "Verifique se o arquivo backend/app/config.py existe e está válido. "
        f"Erro original: {exc}"
    ) from exc

# ==============================================================================
# TYPE HINTS PARA IDEs (Autocomplete)
# ==============================================================================
if TYPE_CHECKING:
    from app.config import Settings as SettingsType
    from app.config import settings as settingsType

# ==============================================================================
# REEXPORTAÇÃO PÚBLICA
# ==============================================================================
Settings: type = _Settings
settings: object = _settings

__all__ = ["Settings", "settings"]

# ==============================================================================
# LOG DE INICIALIZAÇÃO
# ==============================================================================
_logger = logging.getLogger(__name__)
_logger.debug(
    "app.core.config carregado (façade) | environment=%s",
    getattr(_settings, "environment", "desconhecido"),
)