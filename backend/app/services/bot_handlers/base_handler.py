"""
================================================================================
PROJETO.......: EcoChatBotMarcx — Sistema de Atendimento Digital Configurável
ARQUIVO.......: bot_handlers/base_handler.py
AUTOR.........: Aldemir Queiroz
DATA..........: 08/09/2026
VERSÃO........: 1.0.0

PROPÓSITO:
Classe base abstrata para todos os handlers de departamento. 
Fornece a espinha dorsal (core) para comunicação, gerenciamento de estado, 
contexto e validações, sendo 100% agnóstica ao modelo de negócio (White-Label).

CONCEITOS OOP APLICADOS:
  1. HERANÇA: Handlers específicos (ex: Agendamento) herdam desta classe.
  2. POLIMORFISMO: O método 'processar' é sobrescrito em cada filho.
  3. ENCAPSULAMENTO: Métodos com '_' são protegidos (uso interno da classe).
  4. ABSTRAÇÃO: Define um contrato que os filhos são obrigados a seguir.

PRIVACIDADE E LGPD/GDPR:
  - NUNCA logar dados pessoais (nome, telefone, email, CPF, etc.).
  - Logar apenas IDs, hashes e metadados não identificáveis.
  - Usar logger estruturado para auditoria.
================================================================================
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTAÇÕES PADRÃO DO PYTHON E BIBLIOTECAS EXTERNAS
# ─────────────────────────────────────────────────────────────────────────────
from abc import ABC, abstractmethod
# SINTAXE PYTHON: 'abc' (Abstract Base Classes) é o módulo nativo para criar 
# classes que não podem ser instanciadas diretamente, servindo apenas como modelo.

from sqlalchemy.orm import Session
# SINTAXE PYTHON: Importa a classe 'Session' do ORM SQLAlchemy para tipagem.

from app.models import Atendimento, Mensagem
from datetime import datetime
import json
import uuid
import re
import hashlib
import logging
from typing import Optional, Dict, List, Any, Tuple
# SINTAXE PYTHON: O módulo 'typing' permite "Type Hinting" (Dicas de Tipo).
# Isso não afeta a execução, mas ajuda o editor (VS Code) e verificadores (mypy)
# a encontrar erros antes de rodar o código.
#   Optional[X]  -> Pode ser do tipo X ou None.
#   Dict[K, V]   -> Dicionário com chaves do tipo K e valores do tipo V.
#   List[X]      -> Lista contendo elementos do tipo X.
#   Any          -> Qualquer tipo de dado (use com moderação).
#   Tuple[A, B]  -> Tupla com tipos específicos (ex: bool e string).

# Configura logger para este módulo específico
# SINTAXE PYTHON: __name__ é uma variável mágica que contém o nome do arquivo atual.
# Isso garante que os logs saiam com o prefixo "bot_handlers.base_handler".
logger = logging.getLogger(__name__)


# SINTAXE PYTHON: Herdamos de 'ABC' para tornar esta uma Classe Base Abstrata.
class DepartamentoHandler(ABC):
    """
    CLASSE BASE: Handler de Departamento
    
    Responsabilidades:
      1. Gerenciar estado do atendimento (Máquina de Estados)
      2. Enviar mensagens (texto, lista, botões, arquivos)
      3. Gerenciar contexto (memória de curto prazo do atendimento)
      4. Transferir entre departamentos ou para humano
      5. Fornecer métodos utilitários de validação e formatação
    """
    
    def __init__(self, session: Session):
        """
        CONSTRUTOR DA CLASSE
        
        SINTAXE PYTHON: '__init__' é o método construtor (equivalente ao 'Create' 
        de uma classe no Delphi). 'self' é a referência à instância atual do objeto 
        (equivalente ao 'Self' ou 'Sender' do Delphi, mas obrigatório como 1º parâmetro).
        
        Args:
            session: Sessão do banco de dados (Injeção de Dependência)
        """
        self.session = session
        # Dicionário aninhado para cache em memória. 
        # Estrutura: { atendimento_id: { "chave": "valor" } }
        self.contexto_cache: Dict[int, Dict[str, Any]] = {}
        
    # ══════════════════════════════════════════════════════════════
    # 1. MÉTODOS ABSTRATOS (Contrato para as classes filhas)
    # ══════════════════════════════════════════════════════════════
    
    @abstractmethod
    async def processar(
        self,
        atendimento: Atendimento,
        step: str,
        mensagem: Mensagem,
    ) -> None:
        """
        MÉTODO ABSTRATO: Processa a mensagem do departamento.
        
        SINTAXE PYTHON: O decorador '@abstractmethod' obriga qualquer classe que 
        herde de 'DepartamentoHandler' a implementar este método. Se não implementar, 
        o Python lança um erro em tempo de criação do objeto.
        
        SINTAXE PYTHON: 'async def' define uma corrotina (função assíncrona). 
        Ela pode usar 'await' para operações de I/O (banco, API) sem travar o servidor.
        """
        raise NotImplementedError("O método 'processar' deve ser implementado pela classe filha.")
    
    # ══════════════════════════════════════════════════════════════
    # 2. MÉTODOS DE COMUNICAÇÃO (Encapsulamento da API Externa)
    # ══════════════════════════════════════════════════════════════
    
    async def _enviar_texto(self, atendimento: Atendimento, texto: str) -> None:
        """Envia mensagem de texto. Prefixo '_' indica método protegido (interno)."""
        # TODO: Integrar com Evolution API aqui (ex: await self.evolution.send_text(...))
        
        # SINTAXE PYTHON: hasattr(obj, 'attr') verifica se o objeto tem o atributo, 
        # evitando erros de 'AttributeError' se o modelo mudar.
        telefone_hash = self._hash_telefone(atendimento.numero) if hasattr(atendimento, 'numero') else None
        
        logger.info(
            "acao_enviar_texto",
            extra={
                "atendimento_id": atendimento.id,
                "tamanho_texto": len(texto), # len() retorna o tamanho da string
                "telefone_hash": telefone_hash
            }
        )
    
    async def _enviar_lista(
        self,
        atendimento: Atendimento,
        titulo: str,
        descricao: str,
        rows: List[Dict[str, str]],
        botao_texto: str = "Ver opções", # SINTAXE: Parâmetro com valor padrão
    ) -> None:
        """Envia lista interativa (menu) para o WhatsApp."""
        # TODO: Integrar com Evolution API
        
        logger.info(
            "acao_enviar_lista",
            extra={
                "atendimento_id": atendimento.id,
                "qtd_opcoes": len(rows),
                "telefone_hash": self._hash_telefone(atendimento.numero) if hasattr(atendimento, 'numero') else None
            }
        )

    async def _enviar_botoes(self, atendimento: Atendimento, texto: str, botoes: List[Dict[str, str]]) -> None:
        """Envia botões interativos."""
        # TODO: Integrar com Evolution API
        logger.info("acao_enviar_botoes", extra={"atendimento_id": atendimento.id, "qtd_botoes": len(botoes)})

    async def _enviar_arquivo(self, atendimento: Atendimento, arquivo: str, legenda: str = "") -> None:
        """Envia mídia (imagem, documento, áudio, vídeo)."""
        # TODO: Integrar com Evolution API
        logger.info(
            "acao_enviar_arquivo",
            extra={
                "atendimento_id": atendimento.id,
                "tipo_arquivo": self._detectar_tipo_arquivo(arquivo),
            }
        )
    
    # ══════════════════════════════════════════════════════════════
    # 3. GERENCIAMENTO DE ESTADO (Máquina de Estados Finita)
    # ══════════════════════════════════════════════════════════════
    
    def _avancar_step(self, atendimento: Atendimento, novo_step: str) -> None:
        """Avança o atendimento para o próximo estado."""
        atendimento.step = novo_step
        # TODO: self.session.commit() (Persistir a mudança no banco)
        
        logger.debug("mudanca_estado", extra={"atendimento_id": atendimento.id, "novo_step": novo_step})
    
    def _voltar_step(self, atendimento: Atendimento, step_anterior: str) -> None:
        """Regressa o atendimento para um estado anterior (ex: correção de dado)."""
        atendimento.step = step_anterior
        # TODO: self.session.commit()
        
        logger.debug("mudanca_estado_regresso", extra={"atendimento_id": atendimento.id, "step_anterior": step_anterior})
    
    async def _resetar_atendimento(self, atendimento: Atendimento) -> None:
        """Cancela o fluxo atual e retorna ao menu principal (Hub)."""
        self._limpar_contexto_completo(atendimento.id)
        self._avancar_step(atendimento, "AGUARDAR_HUB")
        # TODO: Chamar método para enviar o menu hub
        
        logger.info("atendimento_resetado", extra={"atendimento_id": atendimento.id})
    
    # ══════════════════════════════════════════════════════════════
    # 4. GERENCIAMENTO DE CONTEXTO (Memória da Sessão)
    # ══════════════════════════════════════════════════════════════
    
    def _guardar_contexto(self, atendimento_id: int, chave: str, valor: Any) -> None:
        """
        Guarda um dado na memória temporária do atendimento.
        SINTAXE PYTHON: Dicionários em Python são Hash Maps. Acesso é O(1) (muito rápido).
        """
        # SINTAXE PYTHON: Se a chave (atendimento_id) não existe, cria um dicionário vazio {}
        if atendimento_id not in self.contexto_cache:
            self.contexto_cache[atendimento_id] = {}
            
        self.contexto_cache[atendimento_id][chave] = valor
        # TODO: Salvar também no banco de dados para persistência entre reinícios
        
        # SINTAXE PYTHON: 'isinstance' é a forma segura de verificar o tipo de uma variável.
        if isinstance(valor, dict):
            valor_info = f"dict({len(valor)} keys)" # SINTAXE: f-string (formatação moderna)
        elif isinstance(valor, list):
            valor_info = f"list({len(valor)} items)"
        elif isinstance(valor, str):
            valor_info = f"str({len(valor)} chars)"
        else:
            valor_info = type(valor).__name__ # Pega o nome do tipo (ex: 'int', 'float')
        
        logger.debug(
            "contexto_salvo",
            extra={
                "atendimento_id": atendimento_id,
                "chave": chave,
                "tipo_valor": valor_info,
                "eh_sensivel": self._is_chave_sensivel(chave)
            }
        )
    
    def _obter_contexto(self, atendimento_id: int, chave: str) -> Optional[Any]:
        """Recupera um dado do contexto. Retorna None se não existir."""
        # SINTAXE PYTHON: .get() é seguro. Se a chave não existir, retorna o padrão (None) 
        # em vez de lançar um erro 'KeyError'.
        if atendimento_id in self.contexto_cache:
            return self.contexto_cache[atendimento_id].get(chave)
        return None
    
    def _deletar_contexto(self, atendimento_id: int, chave: str) -> None:
        """Remove uma chave específica do contexto."""
        if atendimento_id in self.contexto_cache:
            # SINTAXE PYTHON: 'del' remove a chave do dicionário.
            # Usamos .get() ou 'in' antes para evitar KeyError.
            if chave in self.contexto_cache[atendimento_id]:
                del self.contexto_cache[atendimento_id][chave]
                
        logger.debug("contexto_chave_removida", extra={"atendimento_id": atendimento_id, "chave": chave})
    
    def _limpar_contexto_completo(self, atendimento_id: int) -> None:
        """Wipe total da memória deste atendimento."""
        qtd_chaves = 0
        if atendimento_id in self.contexto_cache:
            qtd_chaves = len(self.contexto_cache[atendimento_id])
            self.contexto_cache[atendimento_id] = {} # Reatribui a um dicionário vazio
            
        logger.debug("contexto_limpo_total", extra={"atendimento_id": atendimento_id, "qtd_chaves_removidas": qtd_chaves})
    
    # ══════════════════════════════════════════════════════════════
    # 5. MÉTODOS DE TRANSFERÊNCIA E ROTEAMENTO
    # ══════════════════════════════════════════════════════════════
    
    async def _transferir_atendente(self, atendimento: Atendimento, mensagem: str = "🗣️ Transferindo para um atendente. Aguarde! 😊") -> None:
        """Encaminha a conversa para a fila de atendimento humano."""
        await self._enviar_texto(atendimento, mensagem)
        # TODO: Atualizar status no banco para "EM_ATENDIMENTO" e notificar fila
        
        logger.info("transferencia_humano_solicitada", extra={"atendimento_id": atendimento.id})
    
    async def _transferir_departamento(self, atendimento: Atendimento, departamento: str, mensagem: str = "🔄 Transferindo...") -> None:
        """Muda o contexto do handler para outro departamento (Polimorfismo em ação)."""
        await self._enviar_texto(atendimento, mensagem)
        # TODO: Alterar o 'step' do atendimento para o estado inicial do novo departamento
        
        logger.info("transferencia_departamento", extra={"atendimento_id": atendimento.id, "destino": departamento})
    
    async def _voltar_hub(self, atendimento: Atendimento) -> None:
        """Retorna ao menu principal, limpando a memória da conversa anterior."""
        await self._enviar_texto(atendimento, "🏠 Retornando ao Menu Principal...")
        self._limpar_contexto_completo(atendimento.id)
        self._avancar_step(atendimento, "AGUARDAR_HUB")
        
        logger.info("retorno_ao_hub", extra={"atendimento_id": atendimento.id})
    
    # ══════════════════════════════════════════════════════════════
    # 6. MÉTODOS UTILITÁRIOS DE VALIDAÇÃO (White-Label)
    # ══════════════════════════════════════════════════════════════
    
    def _validar_campo(
        self,
        valor: str,
        tipo: str = "texto",
        obrigatorio: bool = False,
        minimo: Optional[int] = None,
        maximo: Optional[int] = None,
        regex: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida um campo de entrada.
        RETORNO: Tupla (Sucesso: bool, Mensagem_de_Erro: str ou None)
        """
        if obrigatorio and not valor: # 'not valor' é True se for string vazia "" ou None
            return False, "Este campo é obrigatório."
        
        if not valor:
            return True, None # Campo opcional e vazio é considerado válido
        
        # SINTAXE PYTHON: 'valor.strip()' remove espaços em branco no início e fim.
        valor = str(valor).strip()

        if tipo == "texto":
            if minimo and len(valor) < minimo:
                return False, f"Mínimo de {minimo} caracteres."
            if maximo and len(valor) > maximo:
                return False, f"Máximo de {maximo} caracteres."
                
        elif tipo == "numero":
            # SINTAXE PYTHON: try/except é o padrão para tratamento de erros (como try/finally no Delphi)
            try:
                num = float(valor)
                if minimo is not None and num < minimo: # 'is not None' é a forma pythonica de checar
                    return False, f"Valor mínimo: {minimo}"
                if maximo is not None and num > maximo:
                    return False, f"Valor máximo: {maximo}"
            except ValueError:
                return False, "Digite um número válido."
                
        elif tipo == "email":
            # SINTAXE PYTHON: r"..." é uma 'raw string'. O 'r' impede que o Python interprete 
            # barras invertidas (\) como caracteres de escape, essencial para Regex.
            padrao = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(padrao, valor): # re.match verifica se a string CASA com o padrão desde o início
                return False, "E-mail em formato inválido."
                
        elif tipo == "telefone":
            # Limpa tudo que não for dígito antes de validar
            numeros = re.sub(r"\D", "", valor) # \D significa "qualquer coisa que NÃO seja dígito"
            if len(numeros) not in (10, 11):
                return False, "Telefone inválido. Use (XX) XXXXX-XXXX ou apenas os números."
                
        elif tipo == "cpf":
            numeros = re.sub(r"\D", "", valor)
            if len(numeros) != 11:
                return False, "CPF deve conter 11 dígitos."
            # TODO: Implementar algoritmo de validação dos dígitos verificadores do CPF
                
        elif tipo == "data":
            if not re.match(r"^\d{2}/\d{2}/\d{4}$", valor):
                return False, "Formato de data inválido. Use DD/MM/AAAA."
            # TODO: Usar datetime.strptime para validar se a data é real (ex: rejeitar 31/02/2024)
                
        elif tipo == "hora":
            if not re.match(r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$", valor):
                return False, "Formato de hora inválido. Use HH:MM."
        
        if regex and not re.match(regex, valor):
            return False, "Formato inválido para este campo."
        
        return True, None
    
    # ══════════════════════════════════════════════════════════════
    # 7. MÉTODOS DE FORMATAÇÃO E PRIVACIDADE (LGPD/GDPR)
    # ══════════════════════════════════════════════════════════════
    
    def _formatar_data(self, data: str) -> str:
        """Converte data ISO (YYYY-MM-DD) para padrão brasileiro (DD/MM/AAAA)."""
        try:
            # strptime: String Parse Time (string -> objeto datetime)
            dt = datetime.strptime(data, "%Y-%m-%d")
            # strftime: String Format Time (objeto datetime -> string formatada)
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            return data # Retorna original se falhar
    
    def _formatar_moeda(self, valor: float) -> str:
        """Formata para Real Brasileiro."""
        # SINTAXE PYTHON: :.2f dentro da f-string formata o float com 2 casas decimais.
        return f"R$ {valor:.2f}"
    
    def _formatar_telefone(self, telefone: str) -> str:
        """Formata telefone para exibição amigável."""
        try:
            # SINTAXE PYTHON: Slicing (fatiamento) de string. num[:2] pega os 2 primeiros caracteres.
            num = re.sub(r"\D", "", telefone)
            if len(num) == 11:
                return f"({num[:2]}) {num[2:7]}-{num[7:]}"
            elif len(num) == 10:
                return f"({num[:2]}) {num[2:6]}-{num[6:]}"
            return telefone
        except Exception:
            return telefone
    
    def _hash_telefone(self, telefone: str) -> Optional[str]:
        """
        Gera hash SHA-256 do telefone.
        SINTAXE PYTHON: .encode('utf-8') converte string em bytes (exigido pelo hashlib).
        .hexdigest() retorna a representação hexadecimal da hash.
        [:16] fatia a string, pegando apenas os 16 primeiros caracteres para logs mais limpos.
        """
        if not telefone:
            return None
        return hashlib.sha256(telefone.encode('utf-8')).hexdigest()[:16]
    
    def _is_chave_sensivel(self, chave: str) -> bool:
        """Verifica se o nome da variável indica dado pessoal (LGPD)."""
        chave_lower = chave.lower() # Converte tudo para minúsculo para comparação segura
        termos_sensiveis = [
            'nome', 'telefone', 'email', 'cpf', 'cnpj', 'documento', 
            'endereco', 'nascimento', 'cartao', 'paciente', 'cliente', 
            'responsavel', 'rg', 'celular', 'whatsapp', 'mail', 'rua', 
            'cidade', 'data_nasc', 'nasc', 'banco', 'conta', 'agencia'
        ]
        # SINTAXE PYTHON: 'any()' com generator expression. É extremamente rápido e legível.
        # Retorna True se QUALQUER termo da lista for encontrado dentro da chave.
        return any(termo in chave_lower for termo in termos_sensiveis)
    
    def _detectar_tipo_arquivo(self, arquivo: str) -> str:
        """Identifica a categoria do arquivo pela extensão."""
        if not arquivo:
            return "desconhecido"
        
        extensoes = {
            'jpg': 'imagem', 'jpeg': 'imagem', 'png': 'imagem', 'gif': 'imagem',
            'mp4': 'video', 'mov': 'video', 'avi': 'video',
            'mp3': 'audio', 'wav': 'audio', 'm4a': 'audio',
            'pdf': 'documento', 'doc': 'documento', 'docx': 'documento',
            'xls': 'planilha', 'xlsx': 'planilha', 'txt': 'texto', 'csv': 'texto'
        }
        
        # SINTAXE PYTHON: .split('.') divide a string pelo ponto. [-1] pega o último elemento (a extensão).
        ext = arquivo.split('.')[-1].lower() if '.' in arquivo else ''
        
        # SINTAXE PYTHON: .get(chave, valor_padrao) retorna o valor do dicionário ou o padrão se não achar.
        return extensoes.get(ext, 'desconhecido')
    
    def _gerar_protocolo(self, prefixo: str = "PROT") -> str:
        """
        Gera ID único de rastreamento.
        SINTAXE PYTHON: 
        - datetime.utcnow().strftime('%Y%m%d') -> Data atual YYYYMMDD
        - uuid.uuid4().hex -> Gera string hexadecimal aleatória (ex: 'a1b2c3d4...')
        - [:6].upper() -> Pega os 6 primeiros caracteres e converte para maiúsculo.
        """
        data_str = datetime.utcnow().strftime('%Y%m%d')
        uuid_curto = uuid.uuid4().hex[:6].upper()
        return f"{prefixo}-{data_str}-{uuid_curto}"