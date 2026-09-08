"""
================================================================================
PROJETO.......: EcoChatBotMarcx — Sistema de Atendimento Digital Configurável
ARQUIVO.......: bot_handlers/validators.py
AUTOR.........: Aldemir Queiroz
DATA..........: 08/09/2026
VERSÃO........: 1.0.0

DESCRIÇÃO
Módulo de validação de campos de entrada. Implementa validações genéricas
e reutilizáveis para os tipos de dados mais comuns em formulários de
atendimento: texto, números, e-mail, telefone, CPF, CNPJ, CEP, datas,
horas, URLs e senhas.

CONCEITOS DE VALIDAÇÃO:
1. VALIDAÇÃO DE ENTRADA (Input Validation):
   - Verifica se dados recebidos estão no formato esperado
   - Previne erros de processamento e ataques (SQL Injection, XSS)
   - Melhora a experiência do usuário com mensagens claras

2. EXPRESSÕES REGULARES (Regex):
   - Padrões de texto para matching e extração
   - Sintaxe: r"padrão" (raw string para evitar escape de barras)
   - re.match() → verifica se o INÍCIO da string casa com o padrão
   - re.fullmatch() → verifica se a string INTEIRA casa com o padrão
   - re.sub() → substitui partes da string que casam com o padrão

3. VALIDAÇÃO DE DOCUMENTOS BRASILEIROS:
   - CPF: 11 dígitos com algoritmo de dígitos verificadores
   - CNPJ: 14 dígitos com algoritmo de dígitos verificadores
   - CEP: 8 dígitos no formato XXXXX-XXX

4. VALIDAÇÃO DE DATAS E HORAS:
   - Data: formato DD/MM/AAAA com verificação de data real
   - Hora: formato HH:MM com verificação de hora válida

5. VALIDAÇÃO DE SENHAS:
   - Mínimo 8 caracteres
   - Pelo menos 1 letra maiúscula
   - Pelo menos 1 letra minúscula
   - Pelo menos 1 número
   - Pelo menos 1 caractere especial

RESPONSABILIDADE
Centralizar TODA a lógica de validação em um único lugar.
Se novas regras de validação forem necessárias, alteramos APENAS este arquivo.
================================================================================
"""

import re
from datetime import datetime
from typing import Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÃO PRINCIPAL DE VALIDAÇÃO
# ═══════════════════════════════════════════════════════════════════════════════

def validar_campo(
    valor: str,
    tipo: str = "texto",
    obrigatorio: bool = False,
    minimo: Optional[int] = None,
    maximo: Optional[int] = None,
    regex_personalizado: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Valida um campo de acordo com regras definidas.
    
    ARGUMENTOS:
        valor: str - Valor a ser validado (será convertido para string)
        tipo: str - Tipo de validação (texto, numero, email, telefone, cpf, 
                    cnpj, cep, data, hora, url, senha)
        obrigatorio: bool - Se True, campo não pode estar vazio
        minimo: Optional[int] - Tamanho mínimo (para texto) ou valor mínimo (para numero)
        maximo: Optional[int] - Tamanho máximo (para texto) ou valor máximo (para numero)
        regex_personalizado: Optional[str] - Expressão regular personalizada
    
    RETORNA:
        Tuple[bool, Optional[str]] - (Sucesso, Mensagem_de_Erro)
        Se sucesso: (True, None)
        Se falha: (False, "Mensagem de erro descritiva")
    
    EXEMPLOS DE USO:
        # Validação de e-mail obrigatório
        ok, msg = validar_campo("joao@email.com", tipo="email", obrigatorio=True)
        
        # Validação de telefone com limpeza automática
        ok, msg = validar_campo("(11) 99999-9999", tipo="telefone")
        
        # Validação de CPF com algoritmo de dígitos verificadores
        ok, msg = validar_campo("123.456.789-09", tipo="cpf")
        
        # Validação de senha forte
        ok, msg = validar_campo("Senha@123", tipo="senha")
        
        # Validação com regex personalizado
        ok, msg = validar_campo("ABC123", regex_personalizado=r"^[A-Z]{3}\d{3}$")
    
    TIPOS SUPORTADOS:
        - texto: validação de tamanho (min/max)
        - numero: validação numérica com min/max
        - email: formato de e-mail válido
        - telefone: formato brasileiro (10 ou 11 dígitos)
        - cpf: CPF válido com dígitos verificadores
        - cnpj: CNPJ válido com dígitos verificadores
        - cep: CEP brasileiro (8 dígitos)
        - data: formato DD/MM/AAAA com data real
        - hora: formato HH:MM com hora válida
        - url: URL válida (http/https)
        - senha: senha forte (8+ chars, maiúscula, minúscula, número, especial)
    """
    
    # ─────────────────────────────────────────────────────────────────────────
    # VALIDAÇÃO DE CAMPO OBRIGATÓRIO
    # ─────────────────────────────────────────────────────────────────────────
    # Se o campo é obrigatório e está vazio, retorna erro imediatamente.
    # "not valor" é True se valor for None, string vazia, 0, False, etc.
    if obrigatorio and not valor:
        return False, "Este campo é obrigatório."
    
    # Se o campo não é obrigatório e está vazio, considera válido.
    # Isso permite campos opcionais sem forçar preenchimento.
    if not valor:
        return True, None
    
    # ─────────────────────────────────────────────────────────────────────────
    # NORMALIZAÇÃO DO VALOR
    # ─────────────────────────────────────────────────────────────────────────
    # Converte para string (caso seja int, float, etc.) e remove espaços
    # extras no início e fim.
    #
    # str(valor) → converte qualquer tipo para string
    # .strip() → remove espaços em branco no início e fim
    #
    # Exemplo: "  joao@email.com  " → "joao@email.com"
    valor = str(valor).strip()

    # ─────────────────────────────────────────────────────────────────────────
    # VALIDAÇÃO POR TIPO
    # ─────────────────────────────────────────────────────────────────────────
    
    # ── TIPO: TEXTO ─────────────────────────────────────────────────────────
    # Valida apenas o tamanho (número de caracteres).
    # Usado para nomes, descrições, observações, etc.
    if tipo == "texto":
        if minimo and len(valor) < minimo:
            return False, f"Mínimo de {minimo} caracteres."
        if maximo and len(valor) > maximo:
            return False, f"Máximo de {maximo} caracteres."
            
    # ── TIPO: NÚMERO ────────────────────────────────────────────────────────
    # Valida se é um número válido e se está dentro do intervalo min/max.
    # Aceita inteiros e decimais (ex: "123", "45.67", "-10").
    elif tipo == "numero":
        try:
            # float() converte string para número de ponto flutuante.
            # Se a string não for um número válido, lança ValueError.
            num = float(valor)
            
            # Verifica se está dentro do intervalo especificado.
            # "is not None" é necessário porque 0 é um valor válido,
            # mas "if minimo" seria False para 0.
            if minimo is not None and num < minimo:
                return False, f"Valor mínimo: {minimo}"
            if maximo is not None and num > maximo:
                return False, f"Valor máximo: {maximo}"
                
        except ValueError:
            # Captura o erro quando float() não consegue converter a string.
            return False, "Digite um número válido."
            
    # ── TIPO: E-MAIL ────────────────────────────────────────────────────────
    # Valida formato de e-mail usando regex.
    #
    # REGEX EXPLICADO:
    #   ^[a-zA-Z0-9._%+-]+  → parte local (antes do @): letras, números, ._%+-
    #   @                    → símbolo @ obrigatório
    #   [a-zA-Z0-9.-]+       → domínio: letras, números, .-
    #   \.                   → ponto literal (escapado com \)
    #   [a-zA-Z]{2,}$        → TLD: pelo menos 2 letras (com, br, org, etc.)
    #
    # re.match() → verifica se o padrão casa a partir do INÍCIO da string.
    # Como usamos ^ no início e $ no fim, equivale a fullmatch().
    elif tipo == "email":
        padrao_email = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(padrao_email, valor):
            return False, "E-mail em formato inválido."
            
    # ── TIPO: TELEFONE ──────────────────────────────────────────────────────
    # Valida telefone brasileiro (10 ou 11 dígitos).
    # Aceita formatos com ou sem formatação:
    #   - (11) 99999-9999
    #   - 11999999999
    #   - 11 99999-9999
    #
    # re.sub(r"\D", "", valor) → remove TODOS os caracteres não numéricos.
    # \D é a classe de caracteres que casa com qualquer coisa que NÃO seja dígito.
    #
    # Exemplo: "(11) 99999-9999" → "11999999999"
    elif tipo == "telefone":
        numeros = re.sub(r"\D", "", valor)
        if len(numeros) not in (10, 11):
            return False, "Telefone inválido. Use o formato (XX) XXXXX-XXXX ou apenas os números."
            
    # ── TIPO: CPF ───────────────────────────────────────────────────────────
    # Valida CPF brasileiro com algoritmo de dígitos verificadores.
    #
    # ALGORITMO DO CPF:
    #   1. Remove formatação (pontos e hífen)
    #   2. Verifica se tem 11 dígitos
    #   3. Rejeita CPFs com todos os dígitos iguais (ex: 11111111111)
    #   4. Calcula o 1º dígito verificador
    #   5. Calcula o 2º dígito verificador
    #   6. Compara com os dígitos informados
    #
    # Exemplo de CPF válido: 123.456.789-09
    elif tipo == "cpf":
        numeros = re.sub(r"\D", "", valor)
        
        # Verifica tamanho
        if len(numeros) != 11:
            return False, "CPF deve conter 11 dígitos."
        
        # Rejeita CPFs com todos os dígitos iguais (ex: 11111111111)
        # Esses CPFs passam no algoritmo de dígitos verificadores, mas são inválidos.
        if numeros == numeros[0] * 11:
            return False, "CPF inválido."
        
        # Calcula o 1º dígito verificador
        soma = 0
        for i in range(9):
            soma += int(numeros[i]) * (10 - i)
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        # Verifica o 1º dígito
        if int(numeros[9]) != digito1:
            return False, "CPF inválido."
        
        # Calcula o 2º dígito verificador
        soma = 0
        for i in range(10):
            soma += int(numeros[i]) * (11 - i)
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        # Verifica o 2º dígito
        if int(numeros[10]) != digito2:
            return False, "CPF inválido."
            
    # ── TIPO: CNPJ ──────────────────────────────────────────────────────────
    # Valida CNPJ brasileiro com algoritmo de dígitos verificadores.
    #
    # ALGORITMO DO CNPJ:
    #   1. Remove formatação (pontos, hífen e barra)
    #   2. Verifica se tem 14 dígitos
    #   3. Rejeita CNPJs com todos os dígitos iguais
    #   4. Calcula o 1º dígito verificador (pesos: 5,4,3,2,9,8,7,6,5,4,3,2)
    #   5. Calcula o 2º dígito verificador (pesos: 6,5,4,3,2,9,8,7,6,5,4,3,2)
    #   6. Compara com os dígitos informados
    #
    # Exemplo de CNPJ válido: 11.222.333/0001-81
    elif tipo == "cnpj":
        numeros = re.sub(r"\D", "", valor)
        
        # Verifica tamanho
        if len(numeros) != 14:
            return False, "CNPJ deve conter 14 dígitos."
        
        # Rejeita CNPJs com todos os dígitos iguais
        if numeros == numeros[0] * 14:
            return False, "CNPJ inválido."
        
        # Calcula o 1º dígito verificador
        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(numeros[i]) * pesos1[i] for i in range(12))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        # Verifica o 1º dígito
        if int(numeros[12]) != digito1:
            return False, "CNPJ inválido."
        
        # Calcula o 2º dígito verificador
        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(numeros[i]) * pesos2[i] for i in range(13))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        # Verifica o 2º dígito
        if int(numeros[13]) != digito2:
            return False, "CNPJ inválido."
            
    # ── TIPO: CEP ───────────────────────────────────────────────────────────
    # Valida CEP brasileiro (8 dígitos).
    # Aceita formatos com ou sem hífen:
    #   - 01310-100
    #   - 01310100
    #
    # REGEX EXPLICADO:
    #   ^\d{5}-?\d{3}$
    #   ^        → início da string
    #   \d{5}    → exatamente 5 dígitos
    #   -?       → hífen opcional (? = 0 ou 1 vez)
    #   \d{3}    → exatamente 3 dígitos
    #   $        → fim da string
    elif tipo == "cep":
        if not re.match(r"^\d{5}-?\d{3}$", valor):
            return False, "CEP inválido. Use o formato XXXXX-XXX ou XXXXXXXX."
            
    # ── TIPO: DATA ──────────────────────────────────────────────────────────
    # Valida data no formato DD/MM/AAAA e verifica se é uma data real.
    #
    # ETAPAS:
    #   1. Verifica formato com regex (2 dígitos / 2 dígitos / 4 dígitos)
    #   2. Tenta converter para datetime (valida se a data existe)
    #   3. Se datetime.strptime() falhar, a data é inválida (ex: 31/02/2024)
    #
    # datetime.strptime(valor, "%d/%m/%Y"):
    #   - Converte string para objeto datetime
    #   - %d → dia (01-31)
    #   - %m → mês (01-12)
    #   - %Y → ano com 4 dígitos
    #   - Lança ValueError se a data for inválida
    elif tipo == "data":
        # Verifica formato
        if not re.match(r"^\d{2}/\d{2}/\d{4}$", valor):
            return False, "Formato de data inválido. Use DD/MM/AAAA."
        
        # Verifica se a data é real
        try:
            datetime.strptime(valor, "%d/%m/%Y")
        except ValueError:
            return False, "Data inválida. Verifique se o dia, mês e ano estão corretos."
            
    # ── TIPO: HORA ──────────────────────────────────────────────────────────
    # Valida hora no formato HH:MM.
    #
    # REGEX EXPLICADO:
    #   ^([0-1][0-9]|2[0-3]):[0-5][0-9]$
    #   ^              → início da string
    #   ([0-1][0-9]    → horas de 00 a 19
    #   |              → OU
    #   2[0-3])        → horas de 20 a 23
    #   :              → separador (colon)
    #   [0-5][0-9]     → minutos de 00 a 59
    #   $              → fim da string
    #
    # Exemplos válidos: 00:00, 09:30, 14:45, 23:59
    # Exemplos inválidos: 24:00, 12:60, 9:30 (falta o zero)
    elif tipo == "hora":
        if not re.match(r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$", valor):
            return False, "Formato de hora inválido. Use HH:MM (ex: 14:30)."
    
    # ── TIPO: URL ───────────────────────────────────────────────────────────
    # Valida URL com protocolo http ou https.
    #
    # REGEX EXPLICADO:
    #   ^https?://              → http:// ou https:// (s? = s opcional)
    #   [^\s/$.?#]              → primeiro caractere do domínio (não pode ser espaço, /, $, ., ?, #)
    #   [^\s]*                  → restante da URL (qualquer caractere exceto espaço)
    #   $                       → fim da string
    #
    # Exemplos válidos:
    #   - https://www.google.com
    #   - http://example.com/path?query=value
    #   - https://sub.domain.com:8080/page
    elif tipo == "url":
        if not re.match(r"^https?://[^\s/$.?#].[^\s]*$", valor):
            return False, "URL inválida. Use o formato http:// ou https://..."
    
    # ── TIPO: SENHA ─────────────────────────────────────────────────────────
    # Valida senha forte com requisitos de complexidade.
    #
    # REQUISITOS:
    #   - Mínimo 8 caracteres
    #   - Pelo menos 1 letra maiúscula (A-Z)
    #   - Pelo menos 1 letra minúscula (a-z)
    #   - Pelo menos 1 número (0-9)
    #   - Pelo menos 1 caractere especial (!@#$%^&*(),.?":{}|<>)
    #
    # REGEX EXPLICADO:
    #   (?=.*[A-Z])   → lookahead positivo: exige pelo menos 1 maiúscula
    #   (?=.*[a-z])   → lookahead positivo: exige pelo menos 1 minúscula
    #   (?=.*\d)      → lookahead positivo: exige pelo menos 1 número
    #   (?=.*[!@#$%^&*(),.?":{}|<>]) → lookahead positivo: exige pelo menos 1 especial
    #   .{8,}         → qualquer caractere, mínimo 8 vezes
    #
    # Lookahead (?=...) → verifica se o padrão existe SEM consumir caracteres.
    # Permite verificar múltiplas condições na mesma string.
    elif tipo == "senha":
        if len(valor) < 8:
            return False, "Senha deve ter no mínimo 8 caracteres."
        if not re.search(r"[A-Z]", valor):
            return False, "Senha deve conter pelo menos 1 letra maiúscula."
        if not re.search(r"[a-z]", valor):
            return False, "Senha deve conter pelo menos 1 letra minúscula."
        if not re.search(r"\d", valor):
            return False, "Senha deve conter pelo menos 1 número."
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", valor):
            return False, "Senha deve conter pelo menos 1 caractere especial."
    
    # ─────────────────────────────────────────────────────────────────────────
    # VALIDAÇÃO COM REGEX PERSONALIZADO
    # ─────────────────────────────────────────────────────────────────────────
    # Se um regex personalizado foi fornecido, valida contra ele.
    # Isso permite validações específicas do negócio sem modificar o código.
    #
    # Exemplo: validar código de produto no formato "ABC-123"
    #   validar_campo("ABC-123", regex_personalizado=r"^[A-Z]{3}-\d{3}$")
    if regex_personalizado and not re.match(regex_personalizado, valor):
        return False, "Formato inválido para este campo."
    
    # ─────────────────────────────────────────────────────────────────────────
    # VALIDAÇÃO BEM-SUCEDIDA
    # ─────────────────────────────────────────────────────────────────────────
    # Se passou por todas as validações, retorna sucesso.
    return True, None


# ═══════════════════════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES DE VALIDAÇÃO
# ═══════════════════════════════════════════════════════════════════════════════

def validar_email(email: str) -> bool:
    """
    Valida se um e-mail está em formato válido.
    
    ARGUMENTOS:
        email: str - E-mail a ser validado
    
    RETORNA:
        bool - True se válido, False se inválido
    
    EXEMPLO:
        >>> validar_email("joao@email.com")
        True
        >>> validar_email("email-invalido")
        False
    """
    ok, _ = validar_campo(email, tipo="email")
    return ok


def validar_telefone(telefone: str) -> bool:
    """
    Valida se um telefone brasileiro está em formato válido.
    
    ARGUMENTOS:
        telefone: str - Telefone a ser validado
    
    RETORNA:
        bool - True se válido, False se inválido
    
    EXEMPLO:
        >>> validar_telefone("(11) 99999-9999")
        True
        >>> validar_telefone("123")
        False
    """
    ok, _ = validar_campo(telefone, tipo="telefone")
    return ok


def validar_cpf(cpf: str) -> bool:
    """
    Valida se um CPF brasileiro é válido (com dígitos verificadores).
    
    ARGUMENTOS:
        cpf: str - CPF a ser validado
    
    RETORNA:
        bool - True se válido, False se inválido
    
    EXEMPLO:
        >>> validar_cpf("123.456.789-09")
        True
        >>> validar_cpf("11111111111")
        False
    """
    ok, _ = validar_campo(cpf, tipo="cpf")
    return ok


def validar_cnpj(cnpj: str) -> bool:
    """
    Valida se um CNPJ brasileiro é válido (com dígitos verificadores).
    
    ARGUMENTOS:
        cnpj: str - CNPJ a ser validado
    
    RETORNA:
        bool - True se válido, False se inválido
    
    EXEMPLO:
        >>> validar_cnpj("11.222.333/0001-81")
        True
        >>> validar_cnpj("11111111111111")
        False
    """
    ok, _ = validar_campo(cnpj, tipo="cnpj")
    return ok


def validar_senha_forte(senha: str) -> Tuple[bool, Optional[str]]:
    """
    Valida se uma senha atende aos requisitos de complexidade.
    
    ARGUMENTOS:
        senha: str - Senha a ser validada
    
    RETORNA:
        Tuple[bool, Optional[str]] - (Sucesso, Mensagem_de_Erro)
    
    EXEMPLO:
        >>> validar_senha_forte("Senha@123")
        (True, None)
        >>> validar_senha_forte("123")
        (False, "Senha deve ter no mínimo 8 caracteres.")
    """
    return validar_campo(senha, tipo="senha")