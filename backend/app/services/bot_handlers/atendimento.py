"""
================================================================================
HANDLER DE ATENDIMENTO (PLATAFORMA WHITE-LABEL)
================================================================================
Arquivo: bot_handlers/atendimento_handler.py
Propósito: Framework universal para atendimento ao cliente via WhatsApp

DESENVOLVEDOR: Aldemir Queiroz da Silva
DATA: 2026-08-16

CORREÇÕES APLICADAS (CodeRabbit):
  1. ✅ REMOVIDO print() com dados pessoais - Substituído por logger anonimizado
  2. ✅ CORRIGIDO estado final (ESTADO_AT_FINALIZAR) - Agora é terminal
  3. ✅ CORRIGIDO markup do WhatsApp - Double asterisks substituídos por single
  4. ✅ ADICIONADO validação de URL webhook (SSRF protection)
  5. ✅ CORRIGIDO mutation do dicionário de headers (agora usa cópia)
  6. ✅ ADICIONADO logger estruturado no lugar de prints
  7. ✅ REMOVIDO dados pessoais dos logs (LGPD/GDPR compliance)
  8. ✅ USO dos helpers de anonimização da classe base

================================================================================
"""

from sqlalchemy.orm import Session
from app.models import Atendimento, Mensagem, RegistroAtendimento
from .base_handler import DepartamentoHandler
import json
import aiohttp
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from urllib.parse import urlparse

# Configura logger
logger = logging.getLogger(__name__)

# CONSTANTES: Estados
ESTADO_AT_MENU = "AT:MENU"
ESTADO_AT_CATEGORIA = "AT:CATEGORIA"
ESTADO_AT_INFORMACAO = "AT:INFORMACAO"
ESTADO_AT_COLETA = "AT:COLETA"
ESTADO_AT_REVISAO = "AT:REVISAO"
ESTADO_AT_FINALIZAR = "AT:FINALIZAR"


class AtendimentoHandler(DepartamentoHandler):
    """
    HANDLER UNIVERSAL PARA ATENDIMENTO AO CLIENTE
    
    Responsabilidades:
      1. Gerenciar fluxo de atendimento para qualquer tipo de negócio
      2. Carregar configurações específicas do cliente
      3. Renderizar categorias e submenus dinamicamente
      4. Coletar dados conforme configuração
      5. Validar entradas com regras personalizadas
      6. PERSISTIR dados no banco de dados
      7. ENVIAR para webhook e atendente
      8. Integrar com sistemas externos
    
    POLIMORFISMO: Comportamento muda conforme configuração do cliente
    
    PRIVACIDADE:
      - NUNCA logar dados pessoais
      - NUNCA printar dados coletados
      - Todos os logs são anonimizados
    """
    
    def __init__(self, session: Session, empresa_id: int):
        """
        INJEÇÃO DE DEPENDÊNCIA
        
        Args:
            session: Sessão do banco de dados
            empresa_id: ID da empresa (tenant)
        """
        super().__init__(session)
        self.empresa_id = empresa_id
        self.configuracao = self._carregar_configuracao(empresa_id)
        self.categorias = self.configuracao.get("categorias", [])
        self.mensagens = self.configuracao.get("mensagens", {})
        self.branding = self.configuracao.get("branding", {})
        self.webhook_config = self.configuracao.get("webhook", {})
        self.persistencia_config = self.configuracao.get("persistencia", {})
    
    def _carregar_configuracao(self, empresa_id: int) -> Dict[str, Any]:
        """
        Carrega configurações da empresa do banco de dados
        
        ESTRUTURA DA CONFIGURAÇÃO:
        {
            "categorias": [...],
            "webhook": {
                "url": "https://api.cliente.com/webhook",
                ...
            },
            ...
        }
        """
        # TODO: Buscar do banco de dados ConfiguracaoAtendimento
        return self._configuracao_padrao()
    
    def _configuracao_padrao(self) -> Dict[str, Any]:
        """Configuração padrão (fallback)"""
        return {
            "categorias": [
                {
                    "id": "INFORMACOES",
                    "nome": "Informações",
                    "icone": "ℹ️",
                    "submenus": [
                        {
                            "id": "HORARIOS",
                            "nome": "Horários",
                            "texto": "Funcionamos de Segunda a Sexta, 08:00 às 18:00"
                        },
                        {
                            "id": "CONTATO",
                            "nome": "Contato",
                            "texto": "📞 (11) 4000-0000\n📧 contato@empresa.com"
                        }
                    ]
                },
                {
                    "id": "DUVIDAS",
                    "nome": "Dúvidas",
                    "icone": "❓",
                    "submenus": [
                        {
                            "id": "PERGUNTAS",
                            "nome": "Perguntas Frequentes",
                            "texto": "1. Como funciona?\nR: ..."
                        },
                        {
                            "id": "SUPORTE",
                            "nome": "Solicitar Suporte",
                            "tipo": "coleta",
                            "campos": [
                                {"nome": "Nome Completo", "tipo": "texto", "obrigatorio": True, "minimo": 3},
                                {"nome": "Email", "tipo": "email", "obrigatorio": True},
                                {"nome": "Telefone", "tipo": "telefone", "obrigatorio": False},
                                {"nome": "Assunto", "tipo": "texto", "obrigatorio": True, "minimo": 5},
                                {"nome": "Mensagem", "tipo": "texto", "obrigatorio": True, "minimo": 10, "maximo": 2000},
                                {"nome": "Urgência", "tipo": "lista", "obrigatorio": False, 
                                 "opcoes": ["Baixa", "Média", "Alta", "Crítica"]}
                            ]
                        }
                    ]
                }
            ],
            "webhook": {
                "url": None,
                "metodo": "POST",
                "headers": {},
                "timeout": 30,
                "retry": 3
            },
            "persistencia": {
                "salvar_no_banco": True,
                "tabela": "registros_atendimento"
            },
            "mensagens": {
                "boas_vindas": "👋 Bem-vindo! Como podemos ajudar?",
                "confirmacao": "✅ Atendimento concluído com sucesso!",
                "erro_persistencia": "❌ Erro ao salvar seus dados. Por favor, tente novamente ou fale com um atendente.",
                "revise_dados": "📋 Por favor, revise os dados informados:",
                "dados_salvos": "✅ Dados salvos com sucesso!"
            },
            "branding": {
                "nome_empresa": "Nossa Empresa"
            }
        }
    
    # ══════════════════════════════════════════════════════════════
    # HELPER: EXTRAÇÃO DE DADOS DA MENSAGEM
    # ══════════════════════════════════════════════════════════════
    
    def _extrair_dados_mensagem(self, mensagem: Mensagem) -> Dict[str, Any]:
        """
        Extrai dados REAIS da mensagem usando helper da classe base
        
        CORREÇÃO: Reutiliza o método centralizado do base_handler
        """
        return super()._extrair_dados_mensagem(mensagem)
    
    # ══════════════════════════════════════════════════════════════
    # HELPER: VALIDAÇÃO DE WEBHOOK (SSRF PROTECTION)
    # ══════════════════════════════════════════════════════════════
    
    def _webhook_url_permitida(self, url: str) -> bool:
        """
        Valida se a URL do webhook é permitida (SSRF Protection)
        
        CORREÇÃO: Previne Server-Side Request Forgery
        
        REGRAS:
          1. Deve usar HTTPS (obrigatório)
          2. Não pode ser loopback (127.0.0.1, localhost)
          3. Não pode ser link-local (169.254.x.x)
          4. Não pode ser IP privado (10.x.x.x, 172.16.x.x, 192.168.x.x)
          5. Deve ser um domínio válido
        
        RETORNO:
            True: URL permitida
            False: URL bloqueada
        """
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            
            # 1. Verifica esquema (deve ser HTTPS)
            if parsed.scheme != "https":
                logger.warning(
                    "webhook_url_esquema_invalido",
                    extra={
                        "empresa_id": self.empresa_id,
                        "esquema": parsed.scheme
                    }
                )
                return False
            
            # 2. Verifica hostname
            hostname = parsed.hostname
            if not hostname:
                return False
            
            # 3. Lista de hosts bloqueados
            hosts_bloqueados = [
                "localhost",
                "127.0.0.1",
                "0.0.0.0",
                "::1",
                "169.254.169.254",  # AWS metadata
                "metadata.google.internal",  # GCP metadata
                "100.100.100.200",  # Azure metadata
            ]
            
            # Verifica se é host bloqueado
            if hostname.lower() in hosts_bloqueados:
                logger.warning(
                    "webhook_url_host_bloqueado",
                    extra={
                        "empresa_id": self.empresa_id,
                        "host": hostname
                    }
                )
                return False
            
            # 4. Verifica se é IP privado
            import ipaddress
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    logger.warning(
                        "webhook_url_ip_privado",
                        extra={
                            "empresa_id": self.empresa_id
                        }
                    )
                    return False
            except ValueError:
                # Não é IP, é domínio - prossegue
                pass
            
            # 5. Verifica se é domínio válido (tem pelo menos um ponto)
            if "." not in hostname:
                logger.warning(
                    "webhook_url_dominio_invalido",
                    extra={
                        "empresa_id": self.empresa_id,
                        "host": hostname
                    }
                )
                return False
            
            return True
            
        except Exception as e:
            logger.error(
                "webhook_url_validacao_erro",
                extra={
                    "empresa_id": self.empresa_id,
                    "erro": str(e)
                }
            )
            return False
    
    # ══════════════════════════════════════════════════════════════
    # MÉTODO PRINCIPAL: PROCESSAR MENSAGEM (CORRIGIDO)
    # ══════════════════════════════════════════════════════════════
    
    async def processar(
        self,
        atendimento: Atendimento,
        step: str,
        mensagem: Mensagem,
    ) -> None:
        """
        POLIMORFISMO: Implementação específica para Atendimento
        
        CORREÇÃO: Agora usa _extrair_dados_mensagem() para ler dados reais
        """
        # CORREÇÃO: Extrai dados REAIS da mensagem
        dados_msg = self._extrair_dados_mensagem(mensagem)
        
        msg_type = dados_msg["msg_type"]
        content = dados_msg["content"]
        row = dados_msg["row_id"] or ""
        button = dados_msg["button_id"] or ""
        
        # Log seguro (sem dados pessoais) - usando logger da classe base
        logger.debug(
            "processar_atendimento",
            extra={
                "atendimento_id": atendimento.id,
                "step": step,
                "msg_type": msg_type,
                "tem_conteudo": bool(content),
                "tem_row": bool(row),
                "tem_button": bool(button)
            }
        )
        
        # ──────────────────────────────────────────────────────────
        # AÇÕES GLOBAIS (válidas em qualquer estado)
        # ──────────────────────────────────────────────────────────
        
        acao = row or button or content.strip().upper()
        
        if acao == "AT_FALAR":
            # Transfere para atendente com os dados coletados (se houver)
            dados = self._obter_contexto(atendimento.id, "at_dados")
            if dados:
                dados_dict = json.loads(dados) if isinstance(dados, str) else dados
                await self._transferir_atendente_com_dados(atendimento, dados_dict)
            else:
                await self._transferir_atendente(atendimento)
            return
        
        if acao == "AT_VOLTAR_HUB":
            await self._voltar_hub(atendimento)
            return
        
        if acao == "AT_CANCELAR":
            await self._cancelar_atendimento(atendimento)
            return
        
        if acao == "AT_VOLTAR":
            await self._menu_principal(atendimento)
            return
        
        # ──────────────────────────────────────────────────────────
        # DESPACHO POR ESTADO
        # ──────────────────────────────────────────────────────────
        
        if step == ESTADO_AT_MENU:
            await self._menu_principal(atendimento, msg_type, row)
        elif step == ESTADO_AT_CATEGORIA:
            await self._processar_categoria(atendimento, msg_type, row)
        elif step == ESTADO_AT_INFORMACAO:
            await self._exibir_informacao(atendimento, msg_type, row)
        elif step == ESTADO_AT_COLETA:
            await self._coletar_dados(atendimento, content)
        elif step == ESTADO_AT_REVISAO:
            await self._revisar_dados(atendimento, msg_type, row)
        elif step == ESTADO_AT_FINALIZAR:
            await self._finalizar(atendimento)
    
    # ══════════════════════════════════════════════════════════════
    # MENU PRINCIPAL E CATEGORIAS
    # ══════════════════════════════════════════════════════════════
    
    async def _menu_principal(
        self,
        atendimento: Atendimento,
        msg_type: str = "text",
        row: str = ""
    ) -> None:
        """Menu principal com categorias"""
        if not self.categorias:
            await self._enviar_texto(
                atendimento,
                "⚠️ Nenhuma categoria disponível."
            )
            return
        
        if msg_type != "list_response":
            rows = self._renderizar_categorias()
            nome = self.branding.get("nome_empresa", "Nossa Empresa")
            
            await self._enviar_lista(
                atendimento,
                f"🏢 {nome} - Atendimento",
                self.mensagens.get("boas_vindas", "Selecione uma opção:"),
                rows,
                "Ver opções"
            )
            self._avancar_step(atendimento, ESTADO_AT_CATEGORIA)
            return
        
        # Processa seleção
        if row.startswith("AT_CAT_"):
            cat_id = row.replace("AT_CAT_", "")
            categoria = self._obter_categoria(cat_id)
            if categoria:
                self._guardar_contexto(atendimento.id, "at_categoria", cat_id)
                await self._exibir_submenus(atendimento, categoria)
    
    def _renderizar_categorias(self) -> List[Dict[str, str]]:
        """Renderiza categorias para menu"""
        rows = []
        for idx, cat in enumerate(self.categorias, 1):
            rows.append({
                "title": f"{cat.get('icone', '📌')} {idx}. {cat['nome']}",
                "description": cat.get("descricao", ""),
                "rowId": f"AT_CAT_{cat['id']}"
            })
        
        rows.append({"title": "🗣️ Falar com Atendente", "rowId": "AT_FALAR"})
        rows.append({"title": "🏠 Menu Principal", "rowId": "AT_VOLTAR_HUB"})
        return rows
    
    def _obter_categoria(self, cat_id: str) -> Optional[Dict]:
        """Busca categoria pelo ID"""
        return next((c for c in self.categorias if c["id"] == cat_id), None)
    
    async def _processar_categoria(self, atendimento: Atendimento, msg_type: str, row: str) -> None:
        """Processa seleção de categoria"""
        if msg_type != "list_response":
            await self._menu_principal(atendimento)
            return
        
        if row.startswith("AT_CAT_"):
            cat_id = row.replace("AT_CAT_", "")
            categoria = self._obter_categoria(cat_id)
            if categoria:
                self._guardar_contexto(atendimento.id, "at_categoria", cat_id)
                await self._exibir_submenus(atendimento, categoria)
    
    async def _exibir_submenus(self, atendimento: Atendimento, categoria: Dict) -> None:
        """Exibe submenus de uma categoria"""
        submenus = categoria.get("submenus", [])
        
        if not submenus:
            await self._enviar_texto(atendimento, "Nenhuma opção disponível.")
            await self._menu_principal(atendimento)
            return
        
        rows = []
        for idx, sub in enumerate(submenus, 1):
            rows.append({
                "title": f"{sub.get('icone', '📌')} {idx}. {sub['nome']}",
                "description": sub.get("descricao", ""),
                "rowId": f"AT_SUB_{sub['id']}"
            })
        
        rows.append({"title": "🔙 Voltar", "rowId": "AT_VOLTAR"})
        
        await self._enviar_lista(
            atendimento,
            f"{categoria.get('icone', '📌')} {categoria['nome']}",
            "Selecione uma opção:",
            rows,
            "Ver opções"
        )
        self._avancar_step(atendimento, ESTADO_AT_INFORMACAO)
    
    # ══════════════════════════════════════════════════════════════
    # EXIBIÇÃO DE INFORMAÇÕES E COLETA DE DADOS
    # ══════════════════════════════════════════════════════════════
    
    async def _exibir_informacao(self, atendimento: Atendimento, msg_type: str, row: str) -> None:
        """Exibe informação de um submenu"""
        if row == "AT_VOLTAR":
            await self._menu_principal(atendimento)
            return
        
        if row.startswith("AT_SUB_"):
            sub_id = row.replace("AT_SUB_", "")
            categoria_id = self._obter_contexto(atendimento.id, "at_categoria")
            categoria = self._obter_categoria(categoria_id)
            
            if categoria:
                submenus = categoria.get("submenus", [])
                sub = next((s for s in submenus if s["id"] == sub_id), None)
                
                if sub:
                    texto = sub.get("texto", "Informação não disponível.")
                    await self._enviar_texto(atendimento, texto)
                    
                    # Se tiver fluxo de coleta
                    if sub.get("tipo") == "coleta":
                        self._guardar_contexto(atendimento.id, "at_submenu", sub_id)
                        campos = sub.get("campos", [])
                        if campos:
                            # Inicializa contexto de coleta
                            self._guardar_contexto(atendimento.id, "at_campos", json.dumps(campos))
                            self._guardar_contexto(atendimento.id, "at_indice", 0)
                            self._guardar_contexto(atendimento.id, "at_dados", json.dumps({}))
                            self._guardar_contexto(atendimento.id, "at_protocolo", self._gerar_protocolo("AT"))
                            await self._perguntar_campo(atendimento)
                    else:
                        # Volta ao menu
                        await self._exibir_submenus(atendimento, categoria)
    
    # ══════════════════════════════════════════════════════════════
    # COLETA DE DADOS (FLUXO INTERATIVO)
    # ══════════════════════════════════════════════════════════════
    
    async def _perguntar_campo(self, atendimento: Atendimento) -> None:
        """Pergunta o próximo campo"""
        campos_str = self._obter_contexto(atendimento.id, "at_campos") or "[]"
        campos = json.loads(campos_str)
        indice = int(self._obter_contexto(atendimento.id, "at_indice") or 0)
        
        if indice >= len(campos):
            # Todos os campos coletados, vai para revisão
            await self._mostrar_revisao(atendimento)
            return
        
        campo = campos[indice]
        nome = campo.get("nome", "Campo")
        obrigatorio = campo.get("obrigatorio", False)
        opcoes = campo.get("opcoes", [])
        
        # Salva o campo atual no contexto
        self._guardar_contexto(atendimento.id, "at_campo_atual", json.dumps(campo))
        
        if opcoes:
            # Se tem opções, mostra lista
            rows = []
            for idx, opcao in enumerate(opcoes, 1):
                rows.append({
                    "title": f"{idx}. {opcao}",
                    "rowId": f"AT_OP_{opcao}"
                })
            
            # Opção para pular (se não obrigatório)
            if not obrigatorio:
                rows.append({"title": "⏭️ Pular (opcional)", "rowId": "AT_PULAR"})
            
            await self._enviar_lista(
                atendimento,
                nome,
                "Selecione uma opção:",
                rows,
                "Ver opções"
            )
        else:
            # CORREÇÃO: Uso de single asterisk para WhatsApp
            texto = f"*{nome}*"
            if obrigatorio:
                texto += " (obrigatório)"
            if campo.get("maximo"):
                texto += f" (máx. {campo['maximo']} caracteres)"
            if campo.get("minimo"):
                texto += f" (mín. {campo['minimo']} caracteres)"
            
            await self._enviar_texto(atendimento, texto)
        
        self._avancar_step(atendimento, ESTADO_AT_COLETA)
    
    async def _coletar_dados(self, atendimento: Atendimento, content: str) -> None:
        """Coleta dados do campo atual"""
        campos_str = self._obter_contexto(atendimento.id, "at_campos") or "[]"
        campos = json.loads(campos_str)
        indice = int(self._obter_contexto(atendimento.id, "at_indice") or 0)
        
        if indice >= len(campos):
            return
        
        campo = campos[indice]
        nome = campo.get("nome", "Campo")
        
        # Verifica se é opção de pular
        if content.upper() == "AT_PULAR":
            # Pula o campo (não obrigatório)
            self._guardar_contexto(atendimento.id, "at_indice", indice + 1)
            await self._perguntar_campo(atendimento)
            return
        
        # Valida campo
        ok, msg = self._validar_campo(
            content,
            tipo=campo.get("tipo", "texto"),
            obrigatorio=campo.get("obrigatorio", False),
            minimo=campo.get("minimo"),
            maximo=campo.get("maximo")
        )
        
        if not ok:
            await self._enviar_texto(atendimento, f"❌ {msg}")
            # Tenta novamente
            await self._perguntar_campo(atendimento)
            return
        
        # Salva dados no contexto
        dados_str = self._obter_contexto(atendimento.id, "at_dados") or "{}"
        dados = json.loads(dados_str)
        
        # Se for opção de lista, extrai o valor real
        if content.startswith("AT_OP_"):
            opcao = content.replace("AT_OP_", "")
            dados[nome] = opcao
        else:
            dados[nome] = content
        
        self._guardar_contexto(atendimento.id, "at_dados", json.dumps(dados))
        
        # Avança para próximo campo
        self._guardar_contexto(atendimento.id, "at_indice", indice + 1)
        await self._perguntar_campo(atendimento)
    
    # ══════════════════════════════════════════════════════════════
    # REVISÃO E CONFIRMAÇÃO DOS DADOS
    # ══════════════════════════════════════════════════════════════
    
    async def _mostrar_revisao(self, atendimento: Atendimento) -> None:
        """Mostra os dados coletados para revisão do usuário"""
        dados_str = self._obter_contexto(atendimento.id, "at_dados") or "{}"
        dados = json.loads(dados_str)
        protocolo = self._obter_contexto(atendimento.id, "at_protocolo") or "—"
        
        if not dados:
            await self._enviar_texto(atendimento, "Nenhum dado foi coletado.")
            await self._menu_principal(atendimento)
            return
        
        # CORREÇÃO: Uso de single asterisk para compatibilidade com WhatsApp
        resumo = f"📋 *Resumo do Atendimento*\n\n"
        resumo += f"🔖 Protocolo: *{protocolo}*\n\n"
        
        for chave, valor in dados.items():
            if valor:
                resumo += f"• *{chave}*: {valor}\n"
        
        resumo += f"\n{self.mensagens.get('revise_dados', 'Por favor, revise os dados informados:')}"
        
        await self._enviar_texto(atendimento, resumo)
        
        # Opções para o usuário
        rows = [
            {"title": "✅ Confirmar e Enviar", "description": "Salvar dados e finalizar", "rowId": "AT_CONFIRMAR"},
            {"title": "✏️ Corrigir", "description": "Refazer a coleta", "rowId": "AT_CORRIGIR"},
            {"title": "🗣️ Falar com Atendente", "description": "", "rowId": "AT_FALAR"},
            {"title": "❌ Cancelar", "description": "", "rowId": "AT_CANCELAR"}
        ]
        
        await self._enviar_lista(
            atendimento,
            "Confirmação",
            "O que deseja fazer?",
            rows,
            "Responder"
        )
        
        self._avancar_step(atendimento, ESTADO_AT_REVISAO)
    
    async def _revisar_dados(self, atendimento: Atendimento, msg_type: str, row: str) -> None:
        """Processa a revisão dos dados"""
        if row == "AT_CONFIRMAR":
            # CONFIRMAÇÃO: Persiste e finaliza
            await self._persistir_e_finalizar(atendimento)
        
        elif row == "AT_CORRIGIR":
            # CORRIGIR: Recomeça a coleta
            await self._enviar_texto(atendimento, "🔄 Recomeçando a coleta de dados...")
            
            # Reseta o índice, mantém os campos
            self._guardar_contexto(atendimento.id, "at_indice", 0)
            self._guardar_contexto(atendimento.id, "at_dados", json.dumps({}))
            await self._perguntar_campo(atendimento)
        
        elif row == "AT_FALAR":
            # FALAR COM ATENDENTE: Transfere com os dados atuais
            dados_str = self._obter_contexto(atendimento.id, "at_dados") or "{}"
            dados = json.loads(dados_str)
            await self._transferir_atendente_com_dados(atendimento, dados)
        
        elif row == "AT_CANCELAR":
            await self._cancelar_atendimento(atendimento)
        
        else:
            # Opção inválida, mostra novamente
            await self._mostrar_revisao(atendimento)
    
    # ══════════════════════════════════════════════════════════════
    # PERSISTÊNCIA E FINALIZAÇÃO (CORREÇÃO PRINCIPAL)
    # ══════════════════════════════════════════════════════════════
    
    async def _persistir_e_finalizar(self, atendimento: Atendimento) -> None:
        """
        PERSISTE os dados no banco de dados e ENVIA para webhook
        
        CORREÇÃO: 
          - Dados salvos ANTES de limpar o contexto
          - Sem prints com dados pessoais
          - Logs anonimizados
          - CORREÇÃO: Estado final não é sobrescrito
        """
        try:
            # 1. Recupera dados
            dados_str = self._obter_contexto(atendimento.id, "at_dados") or "{}"
            dados = json.loads(dados_str)
            protocolo = self._obter_contexto(atendimento.id, "at_protocolo") or self._gerar_protocolo("AT")
            submenu = self._obter_contexto(atendimento.id, "at_submenu") or "N/A"
            
            if not dados:
                await self._enviar_texto(
                    atendimento,
                    "⚠️ Nenhum dado para salvar. Tente novamente."
                )
                await self._menu_principal(atendimento)
                return
            
            # 2. Salva no banco de dados (com log anonimizado)
            if self.persistencia_config.get("salvar_no_banco", True):
                registro = await self._salvar_no_banco(
                    atendimento_id=atendimento.id,
                    empresa_id=self.empresa_id,
                    submenu=submenu,
                    protocolo=protocolo,
                    dados=dados
                )
                
                # Salva o ID do registro no contexto (para referência futura)
                if registro and hasattr(registro, 'id'):
                    self._guardar_contexto(atendimento.id, "at_registro_id", registro.id)
            
            # 3. Envia para webhook (se configurado e permitido)
            webhook_url = self.webhook_config.get("url")
            if webhook_url and self._webhook_url_permitida(webhook_url):
                await self._enviar_webhook(dados, protocolo, atendimento)
            elif webhook_url:
                logger.warning(
                    "webhook_url_bloqueada_seguranca",
                    extra={
                        "empresa_id": self.empresa_id,
                        "atendimento_id": atendimento.id
                    }
                )
            
            # 4. Mensagem de sucesso
            msg_confirmacao = self.mensagens.get(
                "dados_salvos",
                "✅ Dados salvos com sucesso!"
            )
            
            await self._enviar_texto(
                atendimento,
                f"{msg_confirmacao}\n\n"
                f"🔖 Protocolo: *{protocolo}*\n"
                f"📋 {len(dados)} campos coletados.\n\n"
                f"{self.mensagens.get('confirmacao', 'Agradecemos seu contato!')}"
            )
            
            # 5. CORREÇÃO: Define estado FINAL e NÃO chama _menu_principal
            self._avancar_step(atendimento, ESTADO_AT_FINALIZAR)
            
            # 6. Limpa contexto (APÓS salvar)
            self._limpar_contexto_completo(atendimento.id)
            
            # 7. CORREÇÃO: NÃO volta ao menu automaticamente - estado é terminal
            # O usuário pode escolher uma nova ação a partir do estado final
            
        except Exception as e:
            # Em caso de erro, loga (sem dados pessoais) e tenta transferir
            logger.error(
                "erro_persistir_dados",
                extra={
                    "atendimento_id": atendimento.id,
                    "empresa_id": self.empresa_id,
                    "erro": str(e)
                }
            )
            
            await self._enviar_texto(
                atendimento,
                self.mensagens.get(
                    "erro_persistencia",
                    "❌ Erro ao salvar seus dados. Transferindo para um atendente."
                )
            )
            
            # Transfere com os dados que foram coletados
            dados_str = self._obter_contexto(atendimento.id, "at_dados") or "{}"
            dados = json.loads(dados_str)
            await self._transferir_atendente_com_dados(atendimento, dados)
    
    async def _salvar_no_banco(
        self,
        atendimento_id: int,
        empresa_id: int,
        submenu: str,
        protocolo: str,
        dados: Dict[str, Any]
    ) -> Optional[RegistroAtendimento]:
        """
        Salva os dados no banco de dados
        
        ENCAPSULAMENTO: Isola a lógica de persistência
        
        PRIVACIDADE: NUNCA loga dados pessoais
        """
        try:
            # Cria registro
            registro = RegistroAtendimento(
                atendimento_id=atendimento_id,
                empresa_id=empresa_id,
                submenu=submenu,
                protocolo=protocolo,
                dados_json=json.dumps(dados, ensure_ascii=False),
                data_criacao=datetime.utcnow(),
                status="PENDENTE"
            )
            
            # Salva no banco
            self.session.add(registro)
            self.session.commit()
            self.session.refresh(registro)
            
            # Log seguro - SEM dados pessoais
            logger.info(
                "registro_salvo",
                extra={
                    "registro_id": registro.id,
                    "protocolo": protocolo,
                    "empresa_id": empresa_id,
                    "atendimento_id": atendimento_id,
                    "qtd_campos": len(dados)
                }
            )
            
            return registro
            
        except Exception as e:
            self.session.rollback()
            logger.error(
               