def decode_jwt_token(token: str) -> dict | None:
    """
    Decodifica e valida um token JWT.

    Args:
        token: String do token JWT (sem o prefixo "Bearer ").

    Returns:
        dict com as claims do JWT se válido. Exemplo:
        {
            "sub": 42,              # user_id
            "empresa_id": 7,        # tenant
            "nivel": "atendente",   # perfil
            "exp": 1720000000       # expiração (timestamp)
        }
        None se o token for inválido (alternativa: levantar exceção).

    Raises:
        Exception: Se o token estiver expirado, malformado ou com assinatura inválida.
    """