"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EcoChatBot-MA · Security (hash de senha síncrono)
Codinome: EcoChatBot-MA
───────────────────────────────────────────────────────────────────────────
@file     security.py
@module   Backend / App / Core
@author   Aldemir Queiroz
@since    2026
@version  1.0.0
───────────────────────────────────────────────────────────────────────────

FUNCIONALIDADE
──────────────
    Fornece `get_password_hash` e `verify_password` em versão SÍNCRONA.

    `app/security.py` já tinha `hash_senha`/`verificar_senha`, mas ambas são
    `async` (usam anyio para não bloquear o event loop). Os 37 chamadores de
    `app.core.security` estão em métodos síncronos de `UsuarioService` e em
    rotas que gravam `Usuario.senha_hash` — uma função async ali quebraria.

    O algoritmo é o mesmo já usado no projeto: passlib + bcrypt, via
    CryptContext(schemes=["bcrypt"], deprecated="auto").

RELACIONAMENTO
──────────────
    app.config  (fonte única de Settings)
    app.core.security  (bcrypt síncrono)
    Consumidores: app/services/usuario_service.py, app/routers/usuario_routers.py,
                  app/services/webhook_service.py, app/integrations/*.py

REGRAS DE NEGÓCIO
─────────────────
    • bcrypt com `deprecated="auto"`: hashes antigos continuam verificando e são
      re-criptografados no próximo login.
    • Nunca logar nem devolver a senha em texto puro.
    • `verify_password` retorna False em vez de levantar: hash corrompido no
      banco não pode derrubar a requisição nem revelar que o usuário existe.
"""


from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(senha: str) -> str:
    """
    Gera o hash bcrypt da senha, pronto para `Usuario.senha_hash`.

    Args:
        senha (str): senha em texto puro.

    Returns:
        str: hash bcrypt, incluindo sal e algoritmo.
    """
    return _pwd_context.hash(senha)


def verify_password(senha: str, hash_senha: str) -> bool:
    """
    Confere a senha contra o hash guardado no banco.

    Nunca levanta exceção: hash ausente ou corrompido retorna False, para não
    diferenciar "senha errada" de "conta inexistente" na resposta da API.

    Args:
        senha (str): senha em texto puro.
        hash_senha (str): hash bcrypt vindo do banco.

    Returns:
        bool: True somente se a senha conferir.
    """
    if not hash_senha:
        return False
    try:
        return _pwd_context.verify(senha, hash_senha)
    except Exception:
        return False


__all__ = ["get_password_hash", "verify_password"]
