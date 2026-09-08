"""
================================================================================
PROJETO.......: EcoChatBotMarcx — Sistema de Atendimento Digital Configurável
ARQUIVO.......: bot_handlers/privacy.py
AUTOR.........: Aldemir Queiroz
DATA..........: 08/09/2026
VERSÃO........: 1.0.0

DESCRIÇÃO
Módulo responsável por privacidade e anonimização de dados sensíveis.
Implementa funções para garantir conformidade com LGPD (Brasil) e
GDPR (Europa), evitando que dados pessoais sejam expostos em logs
ou processamentos desnecessários.

CONCEITOS DE PRIVACIDADE:
1. LGPD (Lei Geral de Proteção de Dados) - Lei 13.709/2018
   - Dados pessoais: nome, CPF, telefone, e-mail, endereço
   - Dados sensíveis: origem racial, religião, saúde, biometria
   - Princípio da minimização: coletar apenas o necessário

2. ANONIMIZAÇÃO vs PSEUDONIMIZAÇÃO:
   - Anonimização: irreversível (não permite reidentificação)
   - Pseudonimização: reversível com chave (hash com salt)

3. HASH CRIPTOGRÁFICO:
   - Função unidirecional (não tem "des-hash")
   - Mesma entrada → sempre mesma saída (determinístico)
   - SHA-256: algoritmo seguro e amplamente utilizado

RESPONSABILIDADE
Centralizar TODA a lógica de privacidade em um único lugar.
Se a lei mudar ou precisarmos adicionar novos tipos de dados sensíveis,
alteramos APENAS este arquivo.
================================================================================
"""

import hashlib
from typing import Optional, List


# ─────────────────────────────────────────────────────────────────────────────
# LISTA DE TERMOS SENSÍVEIS
# ─────────────────────────────────────────────────────────────────────────────
# Esta lista é usada para identificar se uma chave de contexto contém
# dados pessoais. Se a chave contiver qualquer um destes termos,
# ela é considerada "sensível" e recebe tratamento especial nos logs.
#
# CONVENÇÃO PYTHON:
# Variáveis em MAIÚSCULAS no nível do módulo são consideradas "constantes"
# (embora Python não tenha constantes reais, é uma convenção de estilo).
# ─────────────────────────────────────────────────────────────────────────────

TERMOS_SENSIVEIS: List[str] = [
    # Identificação pessoal
    'nome', 'nome_completo', 'sobrenome',
    'paciente', 'cliente', 'usuario', 'responsavel',
    
    # Contato
    'telefone', 'celular', 'whatsapp', 'email', 'mail',
    
    # Documentos
    'cpf', 'cnpj', 'rg', 'documento', 'carteira',
    
    # Endereço
    'endereco', 'rua', 'avenida', 'bairro', 'cidade', 
    'estado', 'cep', 'pais',
    
    # Dados pessoais sensíveis
    'nascimento', 'data_nasc', 'nasc', 'idade',
    'genero', 'sexo', 'raca', 'etnia', 'religiao',
    
    # Dados financeiros
    'cartao', 'credito', 'debito', 'banco', 'conta',
    'agencia', 'saldo', 'renda', 'salario',
    
    # Dados de saúde (especialmente protegidos pela LGPD)
    'diagnostico', 'doenca', 'medicamento', 'tratamento',
    'convenio', 'plano_saude', 'prontuario'
]


# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÃO: hash_telefone
# ─────────────────────────────────────────────────────────────────────────────
def hash_telefone(telefone: str) -> Optional[str]:
    """
    Gera hash SHA-256 do telefone para logging seguro.
    
    ARGUMENTOS:
        telefone: str - Número de telefone em qualquer formato
        
    RETORNA:
        str | None - Hash de 16 caracteres hexadecimais ou None se vazio
        
    ALGORITMO:
        1. Se telefone for vazio/None → retorna None
        2. Converte string para bytes (UTF-8)
        3. Aplica SHA-256 (gera 256 bits = 32 bytes = 64 chars hex)
        4. Pega apenas os 16 primeiros caracteres (para logs mais curtos)
        5. Retorna o hash em hexadecimal
        
    EXEMPLO:
        >>> hash_telefone("(11) 99999-9999")
        'a3f5b7c9d1e2f4a6'
        
        >>> hash_telefone("")
        None
        
    POR QUE APENAS 16 CARACTERES?
        - 16 chars hex = 64 bits = 18 quintilhões de combinações
        - Suficiente para evitar colisões em logs
        - Mantém logs mais legíveis e curtos
        
    SEGURANÇA:
        - SHA-256 é unidirecional: impossível recuperar o telefone original
        - Determinístico: mesmo telefone sempre gera mesmo hash
        - Útil para rastrear atendimentos sem expor dados pessoais
    """
    if not telefone:
        return None
    
    # encode('utf-8') → converte string para bytes (necessário para hashlib)
    # hashlib.sha256() → cria objeto hash com algoritmo SHA-256
    # .hexdigest() → retorna hash em formato hexadecimal (string)
    # [:16] → fatiamento: pega apenas os 16 primeiros caracteres
    
    return hashlib.sha256(telefone.encode('utf-8')).hexdigest()[:16]


# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÃO: is_chave_sensivel
# ─────────────────────────────────────────────────────────────────────────────
def is_chave_sensivel(chave: str) -> bool:
    """
    Verifica se uma chave de contexto contém dados sensíveis.
    
    ARGUMENTOS:
        chave: str - Nome da chave (ex: "nome_cliente", "telefone_contato")
        
    RETORNA:
        bool - True se a chave contém termo sensível, False caso contrário
        
    ALGORITMO:
        1. Converte chave para minúsculas (case-insensitive)
        2. Percorre lista de termos sensíveis
        3. Se qualquer termo estiver CONTIDO na chave → retorna True
        4. Se nenhum termo for encontrado → retorna False
        
    EXEMPLO:
        >>> is_chave_sensivel("nome_cliente")
        True  # contém "nome"
        
        >>> is_chave_sensivel("telefone_contato")
        True  # contém "telefone"
        
        >>> is_chave_sensivel("departamento_id")
        False  # não contém nenhum termo sensível
        
        >>> is_chave_sensivel("NOME_PACIENTE")
        True  # case-insensitive
        
    USO:
        Nos logs, se is_chave_sensivel() retornar True, o sistema pode:
        - Adicionar alerta visual no log
        - Bloquear a escrita do valor real
        - Enviar notificação para o time de segurança
    """
    chave_lower = chave.lower()
    
    # any() → retorna True se PELO MENOS UM elemento for True
    # Equivalente a um loop "for" com break no primeiro True encontrado
    # Mais eficiente e pythonico que:
    #   for termo in TERMOS_SENSIVEIS:
    #       if termo in chave_lower:
    #           return True
    #   return False
    
    return any(termo in chave_lower for termo in TERMOS_SENSIVEIS)


# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÃO: detectar_tipo_arquivo
# ─────────────────────────────────────────────────────────────────────────────
def detectar_tipo_arquivo(arquivo: str) -> str:
    """
    Detecta o tipo de arquivo pela extensão para logging seguro.
    
    ARGUMENTOS:
        arquivo: str - Nome ou caminho do arquivo (ex: "foto.jpg", "doc.pdf")
        
    RETORNA:
        str - Categoria do arquivo: "imagem", "video", "audio", "documento", 
              "planilha", "texto" ou "desconhecido"
        
    MAPEAMENTO DE EXTENSÕES:
        Imagens:    jpg, jpeg, png, gif, webp, bmp
        Vídeos:     mp4, mov, avi, mkv, webm
        Áudios:     mp3, wav, m4a, ogg, flac
        Documentos: pdf, doc, docx, txt, rtf
        Planilhas:  xls, xlsx, csv, ods
        Outros:     classificados como "desconhecido"
        
    EXEMPLO:
        >>> detectar_tipo_arquivo("foto_paciente.jpg")
        'imagem'
        
        >>> detectar_tipo_arquivo("laudo.pdf")
        'documento'
        
        >>> detectar_tipo_arquivo("audio.m4a")
        'audio'
        
        >>> detectar_tipo_arquivo("")
        'desconhecido'
        
    SEGURANÇA:
        Esta função é usada em logs para registrar o TIPO de arquivo
        enviado/recebido SEM registrar o NOME do arquivo (que pode conter
        dados pessoais como "joao_silva_cpf_123.pdf").
    """
    if not arquivo:
        return "desconhecido"
    
    # Dicionário de mapeamento extensão → categoria
    # Dicionários em Python são O(1) para lookup (muito rápidos)
    extensoes = {
        # Imagens
        'jpg': 'imagem', 'jpeg': 'imagem', 'png': 'imagem', 
        'gif': 'imagem', 'webp': 'imagem', 'bmp': 'imagem',
        
        # Vídeos
        'mp4': 'video', 'mov': 'video', 'avi': 'video',
        'mkv': 'video', 'webm': 'video',
        
        # Áudios
        'mp3': 'audio', 'wav': 'audio', 'm4a': 'audio',
        'ogg': 'audio', 'flac': 'audio',
        
        # Documentos
        'pdf': 'documento', 'doc': 'documento', 'docx': 'documento',
        'txt': 'texto', 'rtf': 'documento',
        
        # Planilhas
        'xls': 'planilha', 'xlsx': 'planilha', 
        'csv': 'texto', 'ods': 'planilha'
    }
    
    # Extrai extensão do arquivo
    # split('.')[-1] → divide por ponto e pega o último elemento
    # .lower() → converte para minúsculas (case-insensitive)
    ext = arquivo.split('.')[-1].lower() if '.' in arquivo else ''
    
    # .get(ext, 'desconhecido') → retorna valor da chave ou padrão se não existir
    return extensoes.get(ext, 'desconhecido')


# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÃO: anonimizar_texto
# ─────────────────────────────────────────────────────────────────────────────
def anonimizar_texto(texto: str, manter_primeiros: int = 3) -> str:
    """
    Anonimiza texto mantendo apenas os primeiros caracteres.
    
    ARGUMENTOS:
        texto: str - Texto original a ser anonimizado
        manter_primeiros: int - Quantidade de caracteres iniciais a manter (padrão: 3)
        
    RETORNA:
        str - Texto anonimizado com asteriscos
        
    EXEMPLO:
        >>> anonimizar_texto("João Silva")
        'Joã*******'
        
        >>> anonimizar_texto("11999999999", manter_primeiros=2)
        '11*********'
        
        >>> anonimizar_texto("joao@email.com", manter_primeiros=4)
        'joao**********'
        
    USO:
        Útil para exibir parcialmente dados em logs de debug ou interfaces
        administrativas, sem expor a informação completa.
    """
    if not texto or len(texto) <= manter_primeiros:
        return texto
    
    # Mantém os primeiros N caracteres e substitui o resto por asteriscos
    return texto[:manter_primeiros] + '*' * (len(texto) - manter_primeiros)