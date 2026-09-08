"""
================================================================================
PROJETO.......: EcoChatBotMarcx — Sistema de Atendimento Digital Configurável
ARQUIVO.......: bot_handlers/agendamento_handler.py
AUTOR.........: Aldemir Queiroz
DATA..........: 08/09/2026
VERSÃO........: 1.0.0

DESCRIÇÃO
Handler universal para agendamentos (plataforma white-label).
Este handler atende QUALQUER modelo de negócio que precise agendar:
  • Clínicas/Hospitais: Consultas, exames, retornos
  • Lojas: Agendamento de visitas, provadores, demonstrações
  • Escolas: Matrículas, reuniões com pais
  • Serviços: Manutenção, consultorias, visitas técnicas
  • Salões/Barbearias: Cortes, procedimentos estéticos
  • E qualquer outro negócio que precise agendar!

CONCEITO-CHAVE: WHITE-LABEL CONFIGURÁVEL
O handler NÃO possui lógica hardcoded de nenhum negócio específico.
Tudo é carregado dinamicamente da configuração da empresa:
  • Serviços oferecidos
  • Campos obrigatórios de cada serviço
  • Mensagens personalizadas
  • Identidade visual (branding)

FLUXO DE ATENDIMENTO (MÁQUINA DE ESTADOS):
  1. AG:MENU        → Exibe lista de serviços disponíveis
  2. AG:SERVICO     → Aguarda seleção do serviço pelo cliente
  3. AG:COLETA      → Coleta dados campo a campo (nome, data, hora, etc.)
  4. AG:REVISAO     → Exibe resumo para o cliente confirmar ou corrigir
  5. AG:CONFIRMACAO → Registra agendamento e finaliza

PRIVACIDADE E LGPD/GDPR:
  • NUNCA logar dados pessoais coletados (nome, telefone, CPF, etc.)
  • Logar apenas IDs de atendimento, hashes e metadados
  • Contexto em memória é limpo ao final do atendimento
================================================================================
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTAÇÕES
# ─────────────────────────────────────────────────────────────────────────────
# Após a refatoração do base_handler.py em módulos separados,
# os imports agora apontam para os arquivos específicos:
#
#   .core        → Classe base DepartamentoHandler (antes em base_handler.py)
#   .validators  → Funções de validação (validar_campo)
#   .utils       → Funções utilitárias (gerar_protocolo)
#   .privacy     → Funções de anonimização (hash_telefone)
#
# Isso segue o Princípio da Responsabilidade Única (SOLID):
# cada arquivo tem UMA única responsabilidade bem definida.
# ─────────────────────────────────────────────────────────────────────────────

from sqlalchemy.orm import Session
from app.models import Atendimento, Mensagem
from .core import DepartamentoHandler
from .validators import validar_campo
from .utils import gerar_protocolo
from .privacy import hash_telefone
import logging
from typing import Optional, Dict, List, Any

# Configuração do logger (mesma convenção do core.py)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES DE ESTADO (MÁQUINA DE ESTADOS)
# ─────────────────────────────────────────────────────────────────────────────
# Cada estado representa uma "fase" do fluxo de agendamento.
# O prefixo "AG:" identifica visualmente que pertence a este handler.
#
# CONCEITO: MÁQUINA DE ESTADOS FINITA (FSM - Finite State Machine)
#   É um modelo computacional onde o sistema pode estar em APENAS UM estado
#   por vez, e transições entre estados são disparadas por eventos (mensagens).
#
#   No Delphi, pensaríamos nisso como uma variável "EstadoAtendimento" do tipo
#   enum, com um case/switch no evento OnMessage decidindo qual procedure chamar.
#
#   Vantagem: código organizado, previsível e fácil de testar.
# ─────────────────────────────────────────────────────────────────────────────

ESTADO_AG_MENU = "AG:MENU"              # Exibindo menu de serviços
ESTADO_AG_SERVICO = "AG:SERVICO"        # Aguardando seleção do serviço
ESTADO_AG_COLETA = "AG:COLETA"          # Coletando dados campo a campo
ESTADO_AG_REVISAO = "AG:REVISAO"        # Cliente revisa os dados antes de confirmar
ESTADO_AG_CONFIRMACAO = "AG:CONFIRMACAO" # Agendamento confirmado (estado final)


# ═════════════════════════════════════════════════════════════════════════════
# CLASSE: AgendamentoHandler
# ═════════════════════════════════════════════════════════════════════════════

class AgendamentoHandler(DepartamentoHandler):
    """
    HANDLER UNIVERSAL PARA AGENDAMENTOS (WHITE-LABEL)
    
    HERANÇA:
      Herda de DepartamentoHandler, reutilizando:
        • Métodos de envio de mensagens (_enviar_texto, _enviar_lista)
        • Gerenciamento de estado (_avancar_step, _voltar_step)
        • Gerenciamento de contexto (_guardar_contexto, _obter_contexto)
        • Transferências (_transferir_atendente, _voltar_hub)
    
    POLIMORFISMO:
      Implementa o método abstrato processar() da classe base,
      definindo a lógica específica para fluxos de agendamento.
    
    RESPONSABILIDADES:
      1. Gerenciar fluxo de agendamentos para qualquer tipo de negócio
      2. Carregar serviços/configurações específicas do cliente (empresa_id)
      3. Coletar dados estruturados de forma configurável
      4. Validar entradas com regras personalizadas por campo
      5. Confirmar e registrar agendamentos no sistema
    """
    
    def __init__(self, session: Session, empresa_id: int):
        """
        CONSTRUTOR
        
        ARGUMENTOS:
            session: Sessão do banco de dados (injetada pelo Factory)
            empresa_id: ID da empresa/tenant (para white-label)
        
        CONCEITO: MULTI-TENANT / WHITE-LABEL
            O parâmetro empresa_id permite que UMA ÚNICA instalação do sistema
            atenda VÁRIAS empresas diferentes, cada uma com suas próprias
            configurações (serviços, mensagens, branding).
            
            No Delphi, seria como ter um DataModule global que carregava
            configurações diferentes conforme o usuário logado.
        """
        # Chama o construtor da classe pai (DepartamentoHandler)
        # Equivalente ao "inherited Create" do Delphi
        super().__init__(session)
        
        self.empresa_id = empresa_id
        
        # Carrega configurações específicas da empresa
        # A estrutura completa está documentada em _carregar_configuracao()
        self.configuracao = self._carregar_configuracao(empresa_id)
        
        # Extrai seções da configuração para acesso rápido
        self.servicos: List[Dict[str, Any]] = self.configuracao.get("servicos", [])
        self.mensagens: Dict[str, str] = self.configuracao.get("mensagens", {})
        self.branding: Dict[str, str] = self.configuracao.get("branding", {})
        
        # Log anonimizado (LGPD) — apenas hash do empresa_id, não dados sensíveis
        logger.info(
            "agendamento_handler_inicializado",
            extra={
                "empresa_id": empresa_id,
                "qtd_servicos": len(self.servicos)
            }
        )
    
    # ═════════════════════════════════════════════════════════════════════════
    # CARREGAMENTO DE CONFIGURAÇÕES
    # ═════════════════════════════════════════════════════════════════════════
    
    def _carregar_configuracao(self, empresa_id: int) -> Dict[str, Any]:
        """
        Carrega configurações da empresa do banco de dados.
        
        ESTRUTURA DA CONFIGURAÇÃO (JSON):
        {
            "servicos": [
                {
                    "id": "CONSULTA",
                    "nome": "Consulta",
                    "icone": "🩺",
                    "descricao": "Agendamento de consulta médica",
                    "campos": [
                        {"nome": "Nome Completo", "tipo": "texto", "obrigatorio": True, "minimo": 3},
                        {"nome": "Data", "tipo": "data", "obrigatorio": True},
                        {"nome": "Horário", "tipo": "hora", "obrigatorio": True},
                        {"nome": "Observações", "tipo": "texto", "obrigatorio": False, "maximo": 500}
                    ]
                }
            ],
            "mensagens": {
                "boas_vindas": "Bem-vindo ao agendamento!",
                "confirmacao": "Agendamento confirmado!"
            },
            "branding": {
                "nome_empresa": "Clínica Saúde Plus"
            }
        }
        
        CONCEITO: CONFIGURAÇÃO DINÂMICA
            Esta é a essência do white-label: o mesmo código atende qualquer
            negócio porque TODA a lógica de negócio está nos dados (banco),
            não no código-fonte.
            
            Para adaptar o sistema a uma nova clínica, loja ou escola, basta
            cadastrar novos serviços e campos — ZERO alteração de código.
        """
        # TODO: Buscar do banco de dados via SQLAlchemy
        # Exemplo:
        #   config = self.session.query(ConfigEmpresa).filter_by(
        #       empresa_id=empresa_id
        #   ).first()
        #   return config.to_dict() if config else self._configuracao_padrao()
        
        # Fallback: retorna configuração padrão para desenvolvimento/testes
        return self._configuracao_padrao()
    
    def _configuracao_padrao(self) -> Dict[str, Any]:
        """
        Configuração padrão (fallback) usada quando não há config no banco.
        
        Esta configuração demonstra TODOS os tipos de campo suportados:
          • texto: texto livre com min/max
          • data: data no formato DD/MM/AAAA
          • hora: hora no formato HH:MM
          • email: validação de formato de e-mail
          • telefone: validação de telefone brasileiro
          • cpf: validação com dígitos verificadores
        """
        return {
            "servicos": [
                {
                    "id": "CONSULTA",
                    "nome": "Consulta",
                    "icone": "🩺",
                    "descricao": "Agendamento de consulta",
                    "campos": [
                        {"nome": "Nome Completo", "tipo": "texto", "obrigatorio": True, "minimo": 3},
                        {"nome": "Data", "tipo": "data", "obrigatorio": True},
                        {"nome": "Horário", "tipo": "hora", "obrigatorio": True},
                        {"nome": "Observações", "tipo": "texto", "obrigatorio": False, "maximo": 500}
                    ]
                }
            ],
            "mensagens": {
                "boas_vindas": "📅 Agendamento de Serviços",
                "confirmacao": "✅ Agendamento confirmado! Agradecemos a preferência."
            },
            "branding": {
                "nome_empresa": "Nossa Empresa"
            }
        }
    
    # ═════════════════════════════════════════════════════════════════════════
    # MÉTODO PRINCIPAL — DESPACHO POR ESTADO
    # ═════════════════════════════════════════════════════════════════════════
    
    async def processar(
        self,
        atendimento: Atendimento,
        step: str,
        mensagem: Mensagem,
    ) -> None:
        """
        POLIMORFISMO: Implementação específica para Agendamentos.
        
        Este método é chamado pelo orquestrador principal do bot sempre que
        uma nova mensagem chega de um atendimento em estado de agendamento.
        
        FLUXO:
          1. Extrai tipo e conteúdo da mensagem
          2. Verifica ações globais (falar com atendente, voltar ao hub, cancelar)
          3. Despacha para o método específico do estado atual
        
        CONCEITO: DESPACHO POR ESTADO (State Dispatch)
            Similar ao "case/switch" do Delphi, mas mais robusto:
            cada estado tem seu próprio método handler, evitando um
            método gigante com centenas de linhas.
        """
        # ── EXTRAÇÃO DO CONTEÚDO DA MENSAGEM ─────────────────────────────
        # TODO: Integrar com formato real da Evolution API
        # A mensagem pode ser: texto, lista (list_response), botão, etc.
        msg_type = getattr(mensagem, 'tipo', 'text') or "text"
        content = getattr(mensagem, 'conteudo', '') or ""
        
        # Se for resposta de lista, extrai o rowId (identificador da opção)
        # row é usado para decisões rápidas (ex: "AG_SERV_CONSULTA")
        row = content.strip().upper() if msg_type == "list_response" else ""
        
        # Log anonimizado (LGPD) — apenas metadados, nunca o conteúdo
        logger.debug(
            "agendamento_processar",
            extra={
                "atendimento_id": atendimento.id,
                "step": step,
                "msg_type": msg_type,
                "telefone_hash": hash_telefone(getattr(atendimento, 'numero', ''))
            }
        )
        
        # ── AÇÕES GLOBAIS (disponíveis em qualquer estado) ───────────────
        # Estas opções permitem ao usuário "escapar" do fluxo a qualquer momento.
        # Equivalente a um menu de emergência no Delphi.
        
        if row == "AG_FALAR":
            await self._transferir_atendente(atendimento)
            return
        
        if row == "AG_VOLTAR_HUB":
            await self._voltar_hub(atendimento)
            return
        
        if row == "AG_CANCELAR":
            self._limpar_contexto_completo(atendimento.id)
            await self._enviar_texto(atendimento, "❌ Agendamento cancelado.")
            await self._voltar_hub(atendimento)
            return
        
        # ── DESPACHO POR ESTADO ──────────────────────────────────────────
        # Cada estado tem seu próprio método handler.
        # Isso mantém o código organizado e fácil de manter.
        
        try:
            if step == ESTADO_AG_MENU:
                await self._menu_principal(atendimento, msg_type, row)
            
            elif step == ESTADO_AG_SERVICO:
                await self._processar_servico(atendimento, msg_type, row)
            
            elif step == ESTADO_AG_COLETA:
                await self._coletar_dados(atendimento, content)
            
            elif step == ESTADO_AG_REVISAO:
                await self._revisar_agendamento(atendimento, msg_type, row)
            
            elif step == ESTADO_AG_CONFIRMACAO:
                # Estado final — redireciona para o menu principal
                await self._enviar_texto(
                    atendimento,
                    "✅ Seu agendamento já foi confirmado. Digite *MENU* para voltar ao início."
                )
                await self._voltar_hub(atendimento)
            
            else:
                # Estado desconhecido — reset para segurança
                logger.warning(
                    "agendamento_estado_desconhecido",
                    extra={"atendimento_id": atendimento.id, "step": step}
                )
                await self._menu_principal(atendimento)
        
        except Exception as e:
            # Tratamento de erros centralizado — nunca deixa o bot "travar"
            logger.error(
                "agendamento_erro_processamento",
                extra={
                    "atendimento_id": atendimento.id,
                    "step": step,
                    "erro": str(e)
                },
                exc_info=True
            )
            await self._enviar_texto(
                atendimento,
                "⚠️ Ocorreu um erro ao processar seu agendamento. "
                "Por favor, tente novamente ou digite *MENU* para recomeçar."
            )
    
    # ═════════════════════════════════════════════════════════════════════════
    # ESTADO 1: MENU PRINCIPAL
    # ═════════════════════════════════════════════════════════════════════════
    
    async def _menu_principal(
        self,
        atendimento: Atendimento,
        msg_type: str = "text",
        row: str = ""
    ) -> None:
        """
        ESTADO: AG:MENU
        Exibe o menu principal com os serviços disponíveis da empresa.
        
        FLUXO:
          1. Se não há serviços configurados → avisa o usuário
          2. Se é a primeira vez (msg_type != "list_response") → envia lista
          3. Se é resposta da lista → processa a seleção
        """
        # Verifica se há serviços configurados
        if not self.servicos:
            await self._enviar_texto(
                atendimento,
                "⚠️ Nenhum serviço de agendamento disponível no momento.\n"
                "Por favor, entre em contato com nosso atendimento."
            )
            return
        
        # ── PRIMEIRA VISITA: Exibe a lista de serviços ───────────────────
        if msg_type != "list_response":
            rows = self._renderizar_servicos()
            nome_empresa = self.branding.get("nome_empresa", "Nossa Empresa")
            boas_vindas = self.mensagens.get("boas_vindas", "Selecione um serviço:")
            
            await self._enviar_lista(
                atendimento,
                f"📅 {nome_empresa} - Agendamentos",
                boas_vindas,
                rows,
                "Ver serviços"
            )
            
            # Avança para o próximo estado (aguardando seleção)
            self._avancar_step(atendimento, ESTADO_AG_SERVICO)
            return
        
        # ── RESPOSTA DA LISTA: Processa a seleção ────────────────────────
        if row.startswith("AG_SERV_"):
            servico_id = row.replace("AG_SERV_", "")
            servico = self._obter_servico(servico_id)
            
            if servico:
                await self._iniciar_agendamento(atendimento, servico)
            else:
                logger.warning(
                    "agendamento_servico_nao_encontrado",
                    extra={"atendimento_id": atendimento.id, "servico_id": servico_id}
                )
                await self._enviar_texto(
                    atendimento,
                    "⚠️ Serviço não encontrado. Por favor, selecione novamente."
                )
                await self._menu_principal(atendimento)
    
    def _renderizar_servicos(self) -> List[Dict[str, str]]:
        """
        Renderiza a lista de serviços no formato esperado pela Evolution API.
        
        FORMATO DE CADA ROW:
        {
            "title": "🩺 1. Consulta",
            "description": "Agendamento de consulta médica",
            "rowId": "AG_SERV_CONSULTA"
        }
        
        CONCEITO: ADICIONA OPÇÕES FIXAS NO FINAL
            Sempre adiciona "Falar com Atendente" e "Menu Principal"
            como opções de escape, independente dos serviços configurados.
        """
        rows = []
        
        # Renderiza cada serviço com numeração automática
        for idx, servico in enumerate(self.servicos, 1):
            icone = servico.get('icone', '📌')
            nome = servico.get('nome', 'Serviço')
            descricao = servico.get('descricao', '')
            servico_id = servico.get('id', f'SERV_{idx}')
            
            rows.append({
                "title": f"{icone} {idx}. {nome}",
                "description": descricao,
                "rowId": f"AG_SERV_{servico_id}"
            })
        
        # Opções fixas de escape (sempre presentes)
        rows.append({"title": "🗣️ Falar com Atendente", "rowId": "AG_FALAR"})
        rows.append({"title": "🏠 Menu Principal", "rowId": "AG_VOLTAR_HUB"})
        
        return rows
    
    def _obter_servico(self, servico_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca um serviço pelo ID.
        
        CONCEITO: BUSCA LINEAR (O(N))
            Para poucos serviços (< 50), busca linear é eficiente.
            Se houver muitos serviços, considerar usar um dict indexado.
        
        EQUIVALÊNCIA DELPHI:
            Seria como um TList.IndexOf() ou uma busca em TClientDataSet
            com Locate('ID', valor, []).
        """
        return next((s for s in self.servicos if s.get("id") == servico_id), None)
    
    # ═════════════════════════════════════════════════════════════════════════
    # INÍCIO DO AGENDAMENTO
    # ═════════════════════════════════════════════════════════════════════════
    
    async def _iniciar_agendamento(
        self,
        atendimento: Atendimento,
        servico: Dict[str, Any]
    ) -> None:
        """
        Inicia o processo de agendamento para um serviço específico.
        
        FLUXO:
          1. Valida se o serviço possui campos configurados
          2. Inicializa o contexto com os dados do agendamento
          3. Avança para o estado de coleta
          4. Pergunta o primeiro campo
        
        CONCEITO: CONTEXTO COMO "MEMÓRIA DE TRABALHO"
            O contexto funciona como uma "memória de curto prazo" do bot.
            Cada atendimento tem seu próprio contexto isolado, permitindo
            que múltiplos clientes sejam atendidos simultaneamente sem
            interferência entre eles.
            
            No Delphi, seria como um Record ou objeto temporário que
            armazena os dados do formulário enquanto o usuário preenche.
        
        CORREÇÃO CRÍTICA:
            Este método PRECISA ser async porque chama métodos async
            (_enviar_texto, _perguntar_campo). Métodos async só podem
            ser chamados com "await" de dentro de outros métodos async.
        """
        campos = servico.get("campos", [])
        
        # Validação de segurança: serviço sem campos é inválido
        if not campos:
            await self._enviar_texto(
                atendimento,
                "⚠️ Este serviço não está configurado corretamente.\n"
                "Por favor, entre em contato com nosso atendimento."
            )
            logger.error(
                "agendamento_servico_sem_campos",
                extra={
                    "atendimento_id": atendimento.id,
                    "servico_id": servico.get("id")
                }
            )
            return
        
        # ── INICIALIZAÇÃO DO CONTEXTO ────────────────────────────────────
        # CORREÇÃO: Armazena objetos Python diretamente (dict, list, int)
        # em vez de serializar como JSON string.
        #
        # ANTES (ineficiente e frágil):
        #   self._guardar_contexto(atendimento.id, "ag_campos", json.dumps(campos))
        #   campos = json.loads(self._obter_contexto(atendimento.id, "ag_campos"))
        #
        # AGORA (direto e seguro):
        #   self._guardar_contexto(atendimento.id, "ag_campos", campos)
        #   campos = self._obter_contexto(atendimento.id, "ag_campos") or []
        #
        # O método _guardar_contexto da classe base já aceita Any,
        # então não há necessidade de serialização manual.
        
        self._guardar_contexto(atendimento.id, "ag_servico", servico.get('id'))
        self._guardar_contexto(atendimento.id, "ag_campos", campos)
        self._guardar_contexto(atendimento.id, "ag_indice", 0)
        self._guardar_contexto(atendimento.id, "ag_dados", {})
        self._guardar_contexto(
            atendimento.id,
            "ag_protocolo",
            gerar_protocolo("AG")
        )
        
        # Avança para o estado de coleta de dados
        self._avancar_step(atendimento, ESTADO_AG_COLETA)
        
        # Inicia a coleta perguntando o primeiro campo
        await self._perguntar_campo(atendimento)
        
        logger.info(
            "agendamento_iniciado",
            extra={
                "atendimento_id": atendimento.id,
                "servico_id": servico.get("id"),
                "qtd_campos": len(campos)
            }
        )
    
    # ═════════════════════════════════════════════════════════════════════════
    # ESTADO 2: PROCESSAMENTO DE SERVIÇO
    # ═════════════════════════════════════════════════════════════════════════
    
    async def _processar_servico(
        self,
        atendimento: Atendimento,
        msg_type: str,
        row: str
    ) -> None:
        """
        ESTADO: AG:SERVICO
        Processa a seleção de serviço feita pelo cliente.
        """
        # Se não é resposta de lista, reexibe o menu
        if msg_type != "list_response":
            await self._menu_principal(atendimento)
            return
        
        # Processa a seleção do serviço
        if row.startswith("AG_SERV_"):
            servico_id = row.replace("AG_SERV_", "")
            servico = self._obter_servico(servico_id)
            
            if servico:
                await self._iniciar_agendamento(atendimento, servico)
            else:
                await self._enviar_texto(
                    atendimento,
                    "⚠️ Serviço não encontrado. Por favor, selecione novamente."
                )
                await self._menu_principal(atendimento)
    
    # ═════════════════════════════════════════════════════════════════════════
    # ESTADO 3: COLETA DE DADOS
    # ═════════════════════════════════════════════════════════════════════════
    
    async def _perguntar_campo(self, atendimento: Atendimento) -> None:
        """
        Pergunta o próximo campo do agendamento ao cliente.
        
        FLUXO:
          1. Recupera a lista de campos do contexto
          2. Se todos os campos foram coletados → vai para revisão
          3. Caso contrário → pergunta o campo atual
        
        CORREÇÃO CRÍTICA:
            Este método PRECISA ser async porque chama _enviar_texto
            e _mostrar_revisao, que são async.
        """
        # Recupera campos e índice do contexto
        # CORREÇÃO: Sem json.loads — dados já são objetos Python
        campos = self._obter_contexto(atendimento.id, "ag_campos") or []
        indice = self._obter_contexto(atendimento.id, "ag_indice") or 0
        
        # Verifica se todos os campos foram coletados
        if indice >= len(campos):
            await self._mostrar_revisao(atendimento)
            return
        
        # Obtém o campo atual
        campo = campos[indice]
        nome = campo.get("nome", "Campo")
        tipo = campo.get("tipo", "texto")
        obrigatorio = campo.get("obrigatorio", False)
        
        # Monta a mensagem de pergunta
        texto = f"*{nome}*"
        
        if obrigatorio:
            texto += " _(obrigatório)_"
        
        # Adiciona dica de formato conforme o tipo do campo
        dicas_formato = {
            "data": "\n📅 Formato: DD/MM/AAAA (ex: 25/12/2026)",
            "hora": "\n🕐 Formato: HH:MM (ex: 14:30)",
            "email": "\n📧 Exemplo: nome@email.com",
            "telefone": "\n📱 Exemplo: (11) 99999-9999",
            "cpf": "\n🆔 Apenas os 11 dígitos (ex: 12345678909)"
        }
        
        if tipo in dicas_formato:
            texto += dicas_formato[tipo]
        
        await self._enviar_texto(atendimento, texto)
    
    async def _coletar_dados(self, atendimento: Atendimento, content: str) -> None:
        """
        ESTADO: AG:COLETA
        Coleta e valida o dado do campo atual.
        
        FLUXO:
          1. Recupera o campo atual (pelo índice)
          2. Valida o valor informado
          3. Se inválido → pede para digitar novamente
          4. Se válido → salva no contexto e avança para o próximo campo
        """
        # Recupera contexto
        campos = self._obter_contexto(atendimento.id, "ag_campos") or []
        indice = self._obter_contexto(atendimento.id, "ag_indice") or 0
        dados = self._obter_contexto(atendimento.id, "ag_dados") or {}
        
        # Validação de segurança: índice fora do range
        if indice >= len(campos):
            await self._mostrar_revisao(atendimento)
            return
        
        campo = campos[indice]
        nome = campo.get("nome", "Campo")
        
        # ── VALIDAÇÃO DO CAMPO ───────────────────────────────────────────
        # Usa a função validar_campo do módulo validators.py
        # que já implementa validações robustas para:
        #   • texto (min/max), numero, email, telefone, cpf, cnpj,
        #     cep, data, hora, url, senha
        ok, msg_erro = validar_campo(
            content,
            tipo=campo.get("tipo", "texto"),
            obrigatorio=campo.get("obrigatorio", False),
            minimo=campo.get("minimo"),
            maximo=campo.get("maximo")
        )
        
        if not ok:
            # Valor inválido — pede para digitar novamente
            await self._enviar_texto(
                atendimento,
                f"❌ {msg_erro}\n\nPor favor, digite novamente o *{nome}*:"
            )
            # Repergunta o mesmo campo (não avança o índice)
            await self._perguntar_campo(atendimento)
            return
        
        # ── SALVA O DADO NO CONTEXTO ─────────────────────────────────────
        # CORREÇÃO: dados já é um dict, não precisa de json.loads
        dados[nome] = content
        self._guardar_contexto(atendimento.id, "ag_dados", dados)
        
        # Avança para o próximo campo
        self._guardar_contexto(atendimento.id, "ag_indice", indice + 1)
        
        # Log anonimizado (LGPD) — NUNCA loga o valor do campo
        logger.debug(
            "agendamento_campo_coletado",
            extra={
                "atendimento_id": atendimento.id,
                "campo_nome": nome,
                "campo_tipo": campo.get("tipo"),
                "indice": indice + 1,
                "total_campos": len(campos)
            }
        )
        
        # Pergunta o próximo campo (ou vai para revisão se era o último)
        await self._perguntar_campo(atendimento)
    
    # ═════════════════════════════════════════════════════════════════════════
    # ESTADO 4: REVISÃO
    # ═════════════════════════════════════════════════════════════════════════
    
    async def _mostrar_revisao(self, atendimento: Atendimento) -> None:
        """
        Mostra o resumo do agendamento para o cliente revisar antes de confirmar.
        
        FLUXO:
          1. Recupera todos os dados coletados
          2. Monta mensagem formatada com os dados
          3. Exibe lista com opções: Confirmar, Corrigir, Cancelar
          4. Avança para o estado AG:REVISAO
        """
        dados = self._obter_contexto(atendimento.id, "ag_dados") or {}
        protocolo = self._obter_contexto(atendimento.id, "ag_protocolo") or "—"
        
        # ── MONTA O RESUMO ───────────────────────────────────────────────
        # Usa formatação em Markdown do WhatsApp (*negrito*, _itálico_)
        resumo = f"📋 *Resumo do Agendamento*\n\n"
        resumo += f"🔖 Protocolo: *{protocolo}*\n\n"
        resumo += "📌 *Dados informados:*\n"
        
        for chave, valor in dados.items():
            resumo += f"• {chave}: {valor}\n"
        
        resumo += "\n_As informações estão corretas?_"
        
        await self._enviar_texto(atendimento, resumo)
        
        # ── LISTA DE AÇÕES ───────────────────────────────────────────────
        rows = [
            {"title": "✅ Confirmar agendamento", "rowId": "AG_CONFIRMAR"},
            {"title": "✏️ Corrigir algum dado", "rowId": "AG_CORRIGIR"},
            {"title": "❌ Cancelar agendamento", "rowId": "AG_CANCELAR"}
        ]
        
        await self._enviar_lista(
            atendimento,
            "Confirmação",
            "O que você deseja fazer?",
            rows,
            "Responder"
        )
        
        # Avança para o estado de revisão
        self._avancar_step(atendimento, ESTADO_AG_REVISAO)
    
    async def _revisar_agendamento(
        self,
        atendimento: Atendimento,
        msg_type: str,
        row: str
    ) -> None:
        """
        ESTADO: AG:REVISAO
        Processa a decisão do cliente após revisar os dados.
        
        OPÇÕES:
          • AG_CONFIRMAR → Finaliza o agendamento
          • AG_CORRIGIR  → Volta ao menu principal para recomeçar
          • AG_CANCELAR  → Cancela e limpa o contexto
        """
        if row == "AG_CONFIRMAR":
            await self._confirmar_agendamento(atendimento)
        
        elif row == "AG_CORRIGIR":
            # Limpa dados coletados mas mantém o atendimento ativo
            self._guardar_contexto(atendimento.id, "ag_dados", {})
            self._guardar_contexto(atendimento.id, "ag_indice", 0)
            
            await self._enviar_texto(
                atendimento,
                "✏️ Ok, vamos recomeçar. Selecione o serviço novamente:"
            )
            await self._menu_principal(atendimento)
        
        elif row == "AG_CANCELAR":
            self._limpar_contexto_completo(atendimento.id)
            await self._enviar_texto(atendimento, "❌ Agendamento cancelado.")
            await self._voltar_hub(atendimento)
        
        else:
            # Resposta inválida — reexibe as opções
            await self._enviar_texto(
                atendimento,
                "⚠️ Opção inválida. Por favor, selecione uma das opções abaixo:"
            )
            await self._mostrar_revisao(atendimento)
    
    # ═════════════════════════════════════════════════════════════════════════
    # ESTADO 5: CONFIRMAÇÃO
    # ═════════════════════════════════════════════════════════════════════════
    
    async def _confirmar_agendamento(self, atendimento: Atendimento) -> None:
        """
        Confirma e registra o agendamento no sistema.
        
        FLUXO:
          1. Recupera os dados do contexto
          2. Monta mensagem de confirmação
          3. TODO: Salva no banco de dados
          4. TODO: Envia para webhook/ERP
          5. Limpa o contexto
          6. Avança para estado final
        
        IMPORTANTE:
            Este é o ponto onde o agendamento deixa de ser "rascunho"
            e se torna um registro oficial no sistema.
        """
        dados = self._obter_contexto(atendimento.id, "ag_dados") or {}
        protocolo = self._obter_contexto(atendimento.id, "ag_protocolo") or "—"
        servico_id = self._obter_contexto(atendimento.id, "ag_servico") or "—"
        
        # ── MONTA MENSAGEM DE CONFIRMAÇÃO ────────────────────────────────
        msg = f"✅ *Agendamento Confirmado!*\n\n"
        msg += f"🔖 Protocolo: *{protocolo}*\n\n"
        msg += "📌 *Dados:*\n"
        
        for chave, valor in dados.items():
            msg += f"• {chave}: {valor}\n"
        
        msg_confirmacao = self.mensagens.get(
            'confirmacao',
            'Agradecemos a preferência!'
        )
        msg += f"\n{msg_confirmacao}"
        
        await self._enviar_texto(atendimento, msg)
        
        # ── PERSISTÊNCIA (TODO) ──────────────────────────────────────────
        # TODO: Salvar agendamento no banco de dados
        # Exemplo:
        #   agendamento = Agendamento(
        #       protocolo=protocolo,
        #       atendimento_id=atendimento.id,
        #       empresa_id=self.empresa_id,
        #       servico_id=servico_id,
        #       dados=dados,
        #       status="CONFIRMADO"
        #   )
        #   self.session.add(agendamento)
        #   await self.session.commit()
        
        # TODO: Enviar para webhook/ERP (integração com sistemas externos)
        # Exemplo:
        #   await self._enviar_webhook({
        #       "evento": "agendamento_confirmado",
        #       "protocolo": protocolo,
        #       "dados": dados
        #   })
        
        # ── LIMPEZA DO CONTEXTO ──────────────────────────────────────────
        # IMPORTANTE: Limpa o contexto ANTES de avançar o estado
        # para evitar que dados antigos fiquem "sujos" na memória.
        self._limpar_contexto_completo(atendimento.id)
        
        # Avança para o estado final
        self._avancar_step(atendimento, ESTADO_AG_CONFIRMACAO)
        
        # Log de sucesso (LGPD) — apenas metadados, não dados pessoais
        logger.info(
            "agendamento_confirmado",
            extra={
                "atendimento_id": atendimento.id,
                "protocolo": protocolo,
                "servico_id": servico_id,
                "empresa_id": self.empresa_id,
                "qtd_campos": len(dados)
            }
        )