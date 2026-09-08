"""
================================================================================
MÓDULO DE UTILITÁRIOS
================================================================================
DESENVOLVEDOR: Aldemir Queiroz
DATA: 2026-08-16
PROPÓSITO: Funções auxiliares de formatação e geração de identificadores.
================================================================================
"""
import uuid
from datetime import datetime

def formatar_data(data: str) -> str:
    """Formata data ISO (YYYY-MM-DD) para exibição (DD/MM/AAAA)."""
    try:
        dt = datetime.strptime(data, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return data

def formatar_moeda(valor: float) -> str:
    """Formata valor monetário para padrão brasileiro."""
    return f"R$ {valor:.2f}"

def formatar_telefone(telefone: str) -> str:
    """Formata telefone para exibição amigável."""
    try:
        num = "".join(filter(str.isdigit, telefone))
        if len(num) == 11:
            return f"({num[:2]}) {num[2:7]}-{num[7:]}"
        elif len(num) == 10:
            return f"({num[:2]}) {num[2:6]}-{num[6:]}"
        return telefone
    except Exception:
        return telefone

def gerar_protocolo(prefixo: str = "PROT") -> str:
    """
    Gera um protocolo único para rastreamento.
    Formato: PREFIXO-YYYYMMDD-XXXXXX (ex: PROT-20260816-A1B2C3)
    """
    data_str = datetime.utcnow().strftime('%Y%m%d')
    uuid_curto = uuid.uuid4().hex[:6].upper()
    return f"{prefixo}-{data_str}-{uuid_curto}"