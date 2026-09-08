"""
================================================================================
BASE HANDLER - NÚCLEO DO SISTEMA
================================================================================
Arquivo: bot_handlers/base_handler.py
Propósito: Classe base para todos os handlers (similar ao ZigChat)

DESENVOLVEDOR: Aldemir Queiroz
DATA: 2026-08-16

CONCEITOS OOP:
  1. HERANÇA: Todos os handlers herdam desta classe base
  2. POLIMORFISMO: Cada handler implementa processar() de forma diferente
  3. ENCAPSULAMENTO: Métodos protegidos (_) para uso interno
  4. ABSTRAÇÃO: Interface comum para todos os departamentos
  5. REUTILIZAÇÃO: Código compartilhado entre todos os handlers

PRIVACIDADE E LGPD/GDPR:
  - NUNCA logar dados pessoais (nome, telefone, email, CPF, etc.)
  - Logar apenas IDs e metadados não identificáveis
  - Usar logger estruturado com níveis apropriados
  - Remover dados sensíveis antes de qualquer saída

================================================================================
"""

from sqlalchemy.orm import Session
from app.models import Atendimento, Mensagem
from datetime import datetime
import json
import uuid
import re
import hashlib
import logging
from typing import Optional, Dict, List, Any, Tuple

# Configura logger para o módulo
logger = logging.getLogger(__name__)


class DepartamentoHandler:
    """
    CLASSE BASE: Handler de Departamento
    
    Responsabilidades:
      1. Gerenciar estado do atendimento
      2. Enviar mensagens (texto, lista, botões)
      3. Gerenciar contexto do atendimento
      4. Transferir entre departamentos
      5. Métodos utilitários para todos os handlers
    
    ABSTRAÇÃO: Esta classe não deve ser instanciada diretamente
    
    PRIVACIDADE:
      - Todos os logs são anonimizados
      - Dados pessoais NUNCA são impressos
      - Apenas IDs e metadados são registrados
    """
    
    def __init__(self, session: Session):
        """
        INJEÇÃO DE DEPENDÊNCIA
        
        Args:
            session: Sessão do banco de dados
        """
        self.session = session
        self.contexto_cache: Dict[int, Dict[str, Any]] = {}  # Cache para contexto em memória
        
    # ══════════════════════════════════════════════════════════════
    # MÉTODOS ABSTRATOS (Devem ser implementados pelos filhos)
    # ══════════════════════════════════════════════════════════════
    
    async def processar(
        self,
        atendimento: Atendimento,
        step: str,
        mensagem: Mensagem,
    ) -> None:
        """
        MÉTODO ABSTRATO: Processa mensagem do departamento
        
        POLIMORFISMO: Cada handler implementa sua própria lógica
        
        Args:
            atendimento: Objeto atendimento
            step: Estado atual
            mensagem: Mensagem recebida
        """
        raise NotImplementedError("Método processar deve ser implementado")
    
    # ══════════════════════════════════════════════════════════════
    # MÉTODOS DE COMUNICAÇÃO (ENVIO DE MENSAGENS)
    # ══════════════════════════════════════════════════════════════
    
    async def _enviar_texto(self, atendimento: Atendimento, texto: str) -> None:
        """
        Envia mensagem de texto para o WhatsApp
        
        ENCAPSULAMENTO: Isola a lógica de envio de mensagens
        
        SINTAXE:
            - Método assíncrono (async/await)
            - Recebe atendimento e texto
            - TODO: Integrar com Evolution API
        
        PRIVACIDADE:
            - Loga apenas ID do atendimento
            - NÃO loga conteúdo da mensagem
        """
        # TODO: Enviar mensagem via Evolution API
        
        # Log anonimizado - apenas ID, sem dados pessoais
        logger.info(
            "enviar_texto",
            extra={
                "atendimento_id": atendimento.id,
                "tamanho_texto": len(texto),
                "telefone_hash": self._hash_telefone(atendimento.numero) if hasattr(atendimento, 'numero') else None
            }
        )
    
    async def _enviar_lista(
        self,
        atendimento: Atendimento,
        titulo: str,
        descricao: str,
        rows: List[Dict[str, str]],
        botao_texto: str = "Ver opções",
    ) -> None:
        """
        Envia lista interativa para o WhatsApp
        
        ENCAPSULAMENTO: Isola a lógica de envio de listas
        
        FORMATO (Evolution API):
        {
            "title": "Título",
            "description": "Descrição",
            "buttonText": "Ver opções",
            "sections": [{
                "rows": [
                    {"title": "Opção 1", "description": "Descrição", "rowId": "ID_1"},
                    {"title": "Opção 2", "description": "Descrição", "rowId": "ID_2"}
                ]
            }]
        }
        
        PRIVACIDADE:
            - Loga apenas metadados
            - NÃO loga títulos ou descrições que possam conter dados pessoais
        """
        # TODO: Enviar lista via Evolution API
        
        # Log anonimizado
        logger.info(
            "enviar_lista",
            extra={
                "atendimento_id": atendimento.id,
                "qtd_rows": len(rows),
                "botao_texto": botao_texto,
                "telefone_hash": self._hash_telefone(atendimento.numero) if hasattr(atendimento, 'numero') else None
            }
        )
    
    async def _enviar_botoes(
        self,
        atendimento: Atendimento,
        texto: str,
        botoes: List[Dict[str, str]],
    ) -> None:
        """
        Envia botões interativos para o WhatsApp
        
        ENCAPSULAMENTO: Isola a lógica de envio de botões
        
        FORMATO (Evolution API):
        {
            "text": "Texto da mensagem",
            "buttons": [
                {"id": "ID_1", "text": "Botão 1"},
                {"id": "ID_2", "text": "Botão 2"}
            ]
        }
        
        PRIVACIDADE:
            - NÃO loga texto da mensagem
            - NÃO loga labels dos botões
        """
        # TODO: Enviar botões via Evolution API
        
        logger.info(
            "enviar_botoes",
            extra={
                "atendimento_id": atendimento.id,
                "qtd_botoes": len(botoes),
                "telefone_hash": self._hash_telefone(atendimento.numero) if hasattr(atendimento, 'numero') else None
            }
        )
    
    async def _enviar_arquivo(
        self,
        atendimento: Atendimento,
        arquivo: str,
        legenda: str = "",
    ) -> None:
        """
        Envia arquivo (imagem, documento, áudio, vídeo) para o WhatsApp
        
        ENCAPSULAMENTO: Isola a lógica de envio de arquivos
        
        PRIVACIDADE:
            - Loga apenas tipo de arquivo
            - NÃO loga nome do arquivo ou legenda
        """
        # TODO: Enviar arquivo via Evolution API
        
        logger.info(
            "enviar_arquivo",
            extra={
                "atendimento_id": atendimento.id,
                "tipo_arquivo": self._detectar_tipo_arquivo(arquivo),
                "telefone_hash": self._hash_telefone(atendimento.numero) if hasattr(atendimento, 'numero') else None
            }
        )
    
    # ══════════════════════════════════════════════════════════════
    # MÉTODOS DE GERENCIAMENTO DE ESTADO
    # ══════════════════════════════════════════════════════════════
    
    def _avancar_step(self, atendimento: Atendimento, novo_step: str) -> None:
        """
        Avança para o próximo estado (step)
        
        ENCAPSULAMENTO: Gerencia a máquina de estados
        
        SINTAXE:
            - Atualiza o campo step do atendimento
            - Persiste no banco de dados
        
        PRIVACIDADE:
            - Loga apenas IDs e steps
            - Nenhum dado pessoal
        """
        atendimento.step = novo_step
        # TODO: self.session.commit()
        
        logger.debug(
            "avancar_step",
            extra={
                "atendimento_id": atendimento.id,
                "novo_step": novo_step
            }
        )
    
    def _voltar_step(self, atendimento: Atendimento, step_anterior: str) -> None:
        """
        Volta para um estado anterior
        
        Útil para "corrigir" ou "voltar" no fluxo
        
        PRIVACIDADE:
            - Loga apenas IDs e steps
            - Nenhum dado pessoal
        """
        atendimento.step = step_anterior
        # TODO: self.session.commit()
        
        logger.debug(
            "voltar_step",
            extra={
                "atendimento_id": atendimento.id,
                "step_anterior": step_anterior
            }
        )
    
    async def _resetar_atendimento(self, atendimento: Atendimento) -> None:
        """
        Reseta o atendimento para o menu principal
        
        Útil quando o usuário cancela ou conclui um fluxo
        
        PRIVACIDADE:
            - Loga apenas ID do atendimento
        """
        self._limpar_contexto_completo(atendimento.id)
        self._avancar_step(atendimento, "AGUARDAR_HUB")
        # TODO: Enviar menu principal
        
        logger.info(
            "resetar_atendimento",
            extra={
                "atendimento_id": atendimento.id
            }
        )
    
    # ══════════════════════════════════════════════════════════════
    # MÉTODOS DE GERENCIAMENTO DE CONTEXTO
    # ══════════════════════════════════════════════════════════════
    
    def _guardar_contexto(self, atendimento_id: int, chave: str, valor: Any) -> None:
        """
        Guarda dados no contexto do atendimento
        
        ENCAPSULAMENTO: Gerencia o contexto do atendimento
        
        SINTAXE:
            - Chave: Nome do campo (ex: "nome_cliente")
            - Valor: Qualquer tipo serializável (string, int, dict, list)
            - Persiste no cache e no banco de dados
        
        PRIVACIDADE:
            - NUNCA loga o valor, mesmo que parcial
            - Loga apenas chave e tamanho do valor
            - Se for dict, loga número de chaves
        """
        # Salva no cache
        if atendimento_id not in self.contexto_cache:
            self.contexto_cache[atendimento_id] = {}
        self.contexto_cache[atendimento_id][chave] = valor
        
        # TODO: Salvar no banco de dados
        
        # Calcula tamanho/tipo do valor sem expor conteúdo
        if isinstance(valor, dict):
            valor_info = f"dict({len(valor)} keys)"
        elif isinstance(valor, list):
            valor_info = f"list({len(valor)} items)"
        elif isinstance(valor, str):
            valor_info = f"str({len(valor)} chars)"
        elif isinstance(valor, (int, float, bool)):
            valor_info = type(valor).__name__
        else:
            valor_info = type(valor).__name__
        
        # Log anonimizado - NUNCA loga o valor real
        logger.debug(
            "guardar_contexto",
            extra={
                "atendimento_id": atendimento_id,
                "chave": chave,
                "valor_tipo": valor_info,
                "chave_eh_sensivel": self._is_chave_sensivel(chave)
            }
        )
    
    def _obter_contexto(self, atendimento_id: int, chave: str) -> Optional[Any]:
        """
        Recupera dados do contexto do atendimento
        
        RETURN: Valor da chave ou None se não existir
        
        PRIVACIDADE:
            - NUNCA loga o valor retornado
        """
        # Busca no cache
        if atendimento_id in self.contexto_cache:
            return self.contexto_cache[atendimento_id].get(chave)
        
        # TODO: Buscar no banco de dados
        return None
    
    def _deletar_contexto(self, atendimento_id: int, chave: str) -> None:
        """Remove uma chave do contexto"""
        if atendimento_id in self.contexto_cache:
            if chave in self.contexto_cache[atendimento_id]:
                del self.contexto_cache[atendimento_id][chave]
        # TODO: Remover do banco de dados
        
        logger.debug(
            "deletar_contexto",
            extra={
                "atendimento_id": atendimento_id,
                "chave": chave
            }
        )
    
    def _limpar_contexto_completo(self, atendimento_id: int) -> None:
        """Limpa todo o contexto do atendimento"""
        if atendimento_id in self.contexto_cache:
            qtd_chaves = len(self.contexto_cache[atendimento_id])
            self.contexto_cache[atendimento_id] = {}
        # TODO: Limpar no banco de dados
        
        logger.debug(
            "limpar_contexto_completo",
            extra={
                "atendimento_id": atendimento_id,
                "qtd_chaves_removidas": qtd_chaves if 'qtd_chaves' in locals() else 0
            }
        )
    
    # ══════════════════════════════════════════════════════════════
    # MÉTODOS DE TRANSFERÊNCIA
    # ══════════════════════════════════════════════════════════════
    
    async def _transferir_atendente(
        self,
        atendimento: Atendimento,
        mensagem: str = "🗣️ Transferindo para um atendente. Aguarde! 😊"
    ) -> None:
        """
        Transfere para um atendente humano
        
        ENCAPSULAMENTO: Gerencia a fila de atendimento
        
        FLUXO:
            1. Envia mensagem de confirmação
            2. Adiciona à fila de atendentes
            3. Atualiza status do atendimento
        
        PRIVACIDADE:
            - NUNCA loga telefone ou dados pessoais
            - Loga apenas IDs e metadados
        """
        await self._enviar_texto(atendimento, mensagem)
        
        # TODO: Adicionar à fila de atendentes
        # TODO: Atualizar status para "em_atendimento"
        
        logger.info(
            "transferir_atendente",
            extra={
                "atendimento_id": atendimento.id,
                "telefone_hash": self._hash_telefone(atendimento.numero) if hasattr(atendimento, 'numero') else None
            }
        )
    
    async def _transferir_departamento(
        self,
        atendimento: Atendimento,
        departamento: str,
        mensagem: str = "🔄 Transferindo para outro departamento..."
    ) -> None:
        """
        Transfere para outro departamento
        
        POLIMORFISMO: Pode transferir para qualquer handler
        
        Args:
            departamento: Nome do departamento (ex: "AGENDAMENTO", "PEDIDOS")
        
        PRIVACIDADE:
            - NUNCA loga telefone ou dados pessoais
        """
        await self._enviar_texto(atendimento, mensagem)
        
        # TODO: Mudar estado para o departamento destino
        
        logger.info(
            "transferir_departamento",
            extra={
                "atendimento_id": atendimento.id,
                "departamento": departamento,
                "telefone_hash": self._hash_telefone(atendimento.numero) if hasattr(atendimento, 'numero') else None
            }
        )
    
    async def _voltar_hub(self, atendimento: Atendimento) -> None:
        """
        Volta para o menu principal (hub)
        
        ENCAPSULAMENTO: Retorna ao menu principal
        
        PRIVACIDADE:
            - NUNCA loga dados pessoais
        """
        await self._enviar_texto(atendimento, "🏠 Retornando ao Menu Principal...")
        self._limpar_contexto_completo(atendimento.id)
        self._avancar_step(atendimento, "AGUARDAR_HUB")
        
        # TODO: Enviar menu hub
        
        logger.info(
            "voltar_hub",
            extra={
                "atendimento_id": atendimento.id
            }
        )
    
    # ══════════════════════════════════════════════════════════════
    # MÉTODOS UTILITÁRIOS
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
        Valida um campo de acordo com regras definidas
        
        ABSTRAÇÃO: Validação genérica reutilizável
        
        SINTAXE:
            - tipo: texto, numero, email, telefone, cpf, data, hora
            - obrigatorio: se o campo é obrigatório
            - minimo/maximo: para números ou texto
            - regex: expressão regular personalizada
        
        EXEMPLO:
            ok, msg = self._validar_campo(
                "joao@gmail.com", 
                tipo="email", 
                obrigatorio=True
            )
        
        PRIVACIDADE:
            - NUNCA loga o valor sendo validado
            - Apenas loga o resultado da validação (sucesso/erro)
        """
        # Campo obrigatório
        if obrigatorio and not valor:
            logger.debug(
                "validacao_campo_obrigatorio_falhou",
                extra={"tipo": tipo}
            )
            return False, "Este campo é obrigatório."
        
        if not valor:
            return True, None
        
        # Validações por tipo
        if tipo == "texto":
            if minimo and len(valor) < minimo:
                return False, f"Mínimo de {minimo} caracteres."
            if maximo and len(valor) > maximo:
                return False, f"Máximo de {maximo} caracteres."
                
        elif tipo == "numero":
            try:
                num = float(valor)
                if minimo is not None and num < minimo:
                    return False, f"Valor mínimo: {minimo}"
                if maximo is not None and num > maximo:
                    return False, f"Valor máximo: {maximo}"
            except ValueError:
                return False, "Digite um número válido."
                
        elif tipo == "email":
            padrao = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(padrao, valor):
                return False, "Email inválido."
                
        elif tipo == "telefone":
            padrao = r"^\([0-9]{2}\) [0-9]{4,5}-[0-9]{4}$"
            if not re.match(padrao, valor):
                return False, "Formato: (XX) XXXXX-XXXX"
                
        elif tipo == "cpf":
            if not re.match(r"^[0-9]{11}$", valor):
                return False, "CPF inválido."
            # TODO: Validação de dígitos verificadores do CPF
                
        elif tipo == "data":
            if not re.match(r"^\d{2}/\d{2}/\d{4}$", valor):
                return False, "Formato: DD/MM/AAAA"
            # TODO: Validar data real (30/02/2024, etc.)
                
        elif tipo == "hora":
            if not re.match(r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$", valor):
                return False, "Formato: HH:MM"
        
        # Regex personalizado
        if regex:
            if not re.match(regex, valor):
                return False, "Formato inválido."
        
        logger.debug(
            "validacao_campo_sucesso",
            extra={"tipo": tipo}
        )
        
        return True, None
    
    # ══════════════════════════════════════════════════════════════
    # MÉTODOS DE FORMATAÇÃO (Seguros para logging)
    # ══════════════════════════════════════════════════════════════
    
    def _formatar_data(self, data: str) -> str:
        """Formata data para exibição"""
        try:
            dt = datetime.strptime(data, "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            return data
    
    def _formatar_moeda(self, valor: float) -> str:
        """Formata valor monetário"""
        return f"R$ {valor:.2f}"
    
    def _formatar_telefone(self, telefone: str) -> str:
        """Formata telefone para exibição"""
        try:
            num = re.sub(r"\D", "", telefone)
            if len(num) == 11:
                return f"({num[:2]}) {num[2:7]}-{num[7:]}"
            elif len(num) == 10:
                return f"({num[:2]}) {num[2:6]}-{num[6:]}"
            return telefone
        except Exception:
            return telefone
    
    # ══════════════════════════════════════════════════════════════
    # MÉTODOS DE ANONIMIZAÇÃO PARA LOGGING (PRIVACIDADE)
    # ══════════════════════════════════════════════════════════════
    
    def _hash_telefone(self, telefone: str) -> Optional[str]:
        """
        Gera hash do telefone para logging seguro
        
        PRIVACIDADE:
            - Hash unidirecional (SHA-256)
            - Não permite recuperar o telefone original
            - Útil para rastrear atendimentos sem expor dados
        """
        if not telefone:
            return None
        
        return hashlib.sha256(telefone.encode('utf-8')).hexdigest()[:16]
    
    def _is_chave_sensivel(self, chave: str) -> bool:
        """
        Verifica se a chave contém dados sensíveis
        
        LISTA DE CHAVES SENSÍVEIS:
            - nome, nome_completo, paciente, cliente
            - telefone, celular, whatsapp
            - email, mail
            - cpf, cnpj, documento, rg
            - endereco, rua, cidade
            - data_nascimento, nascimento
            - cartao, credito, debito, banco
        """
        chave_lower = chave.lower()
        termos_sensiveis = [
            'nome', 'telefone', 'email', 'cpf', 'cnpj', 
            'documento', 'endereco', 'nascimento', 'cartao',
            'paciente', 'cliente', 'responsavel', 'rg',
            'celular', 'whatsapp', 'mail', 'rua', 'cidade',
            'data_nasc', 'nasc', 'banco', 'conta', 'agencia'
        ]
        
        for termo in termos_sensiveis:
            if termo in chave_lower:
                return True
        return False
    
    def _detectar_tipo_arquivo(self, arquivo: str) -> str:
        """Detecta tipo de arquivo pela extensão (seguro para logging)"""
        if not arquivo:
            return "desconhecido"
        
        extensoes = {
            'jpg': 'imagem', 'jpeg': 'imagem', 'png': 'imagem', 'gif': 'imagem',
            'mp4': 'video', 'mov': 'video', 'avi': 'video',
            'mp3': 'audio', 'wav': 'audio', 'm4a': 'audio',
            'pdf': 'documento', 'doc': 'documento', 'docx': 'documento',
            'xls': 'planilha', 'xlsx': 'planilha',
            'txt': 'texto', 'csv': 'texto'
        }
        
        ext = arquivo.split('.')[-1].lower() if '.' in arquivo else ''
        return extensoes.get(ext, 'desconhecido')
    
    def _gerar_protocolo(self, prefixo: str = "PROT") -> str:
        """
        Gera um protocolo único para rastreamento
        
        FORMATO: PREFIXO-YYYYMMDD-XXXXXX
        EXEMPLO: PROT-20260816-A1B2C3
        
        SINTAXE:
            - datetime.utcnow(): Data/hora UTC
            - strftime(): Formata data
            - uuid.uuid4(): Gera UUID aleatório
            - .hex[:6].upper(): Pega 6 primeiros caracteres hex
        """
        return f"{prefixo}-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"