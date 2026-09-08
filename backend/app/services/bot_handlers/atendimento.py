"""
================================================================================
HANDLER DE ATENDIMENTO (PLATAFORMA WHITE-LABEL)
================================================================================
Arquivo: bot_handlers/atendimento_handler.py
Propósito: Framework universal para atendimento ao cliente via WhatsApp

DESENVOLVEDOR: Aldemir Queiroz
DATA: 08/09/2026

CORREÇÕES E MELHORIAS APLICADAS:
  1. ✅ REMOVIDO print() com dados pessoais - Substituído por logger anonimizado
  2. ✅ CORRIGIDO estado final (ESTADO_AT_FINALIZAR) - Agora é terminal
  3. ✅ OTIMIZADO o uso de contexto - Armazena objetos Python nativos (dict/list) 
     em vez de strings JSON, evitando json.loads() desnecessários.
  4. ✅ ADICIONADO validação de URL webhook (SSRF protection)
  5. ✅ COMPLETADO o método _salvar_no_banco e adicionado _enviar_webhook
  6. ✅ USO dos helpers de anonimização e validação da classe base (core.py)

================================================================================
"""

from sqlalchemy.orm import Session
from app.models import Atendimento, Mensagem, RegistroAtendimento
from .core import DepartamentoHandler
from .validators import validar_campo
from .utils import gerar_protocolo
from .privacy import hash_telefone

import json
import aiohttp
import asyncio
import logging
import ipaddress
from datetime import datetime
from typing import Optional, Dict, List, Any
from urllib.parse import urlparse

# Configura logger
logger = logging.getLogger(__name__)

# CONSTANTES: Estados da Máquina de Estados
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
      2. Carregar configurações específicas do cliente (empresa_id)
      3. Renderizar categorias e submenus dinamicamente
      4. Coletar dados conforme configuração de campos
      5. Validar entradas com regras personalizadas
      6. PERSISTIR dados no banco de dados
      7. ENVIAR para webhook e atendente humano
    """
    
    def __init__(self, session: Session, empresa_id: int):
        super().__init__(session)
        self.empresa_id = empresa_id
        self.configuracao = self._carregar_configuracao(empresa_id)
        
        # Extração de seções da configuração com fallback seguro
        self.categorias = self.configuracao.get("categorias", [])
        self.mensagens = self.configuracao.get("mensagens", {})
        self.branding = self.configuracao.get("branding", {})
        self.webhook_config = self.configuracao.get("webhook", {})
        self.persistencia_config = self.configuracao.get("persistencia", {})
    
    def _carregar_configuracao(self, empresa_id: int) -> Dict[str, Any]:
        """Carrega configurações da empresa do banco de dados."""
        # TODO: Buscar do banco de dados (ex: session.query(Configuracao).filter_by...)
        return self._configuracao_padrao()
    
    def _configuracao_padrao(self) -> Dict[str, Any]:
        """Configuração padrão (fallback) demonstrando a flexibilidade white-label."""
        return {
            "categorias": [
                {
                    "id": "INFORMACOES",
                    "nome": "Informações",
                    "icone": "ℹ️",
                    "submenus": [
                        {"id": "HORARIOS", "nome": "Horários", "texto": "Funcionamos de Seg a Sex, 08:00 às 18:00"},
                        {"id": "CONTATO", "nome": "Contato", "texto": "📞 (11) 4000-0000\n📧 contato@empresa.com"}
                    ]
                },
                {
                    "id": "SUPORTE",
                    "nome": "Solicitar Suporte",
                    "icone": "🛠️",
                    "submenus": [
                        {
                            "id": "ABRIR_CHAMADO",
                            "nome": "Abrir Chamado",
                            "tipo": "coleta",
                            "campos": [
                                {"nome": "Nome Completo", "tipo": "texto", "obrigatorio": True, "minimo": 3},
                                {"nome": "Email", "tipo": "email", "obrigatorio": True},
                                {"nome": "Assunto", "tipo": "texto", "obrigatorio": True, "minimo": 5},
                                {"nome": "Mensagem", "tipo": "texto", "obrigatorio": True, "minimo": 10, "maximo": 2000},
                                {"nome": "Urgência", "tipo": "lista", "obrigatorio": False, "opcoes": ["Baixa", "Média", "Alta"]}
                            ]
                        }
                    ]
                }
            ],
            "webhook": {"url": None, "metodo": "POST", "headers": {"Content-Type": "application/json"}, "timeout": 10},
            "persistencia": {"salvar_no_banco": True},
            "mensagens": {
                "boas_vindas": "👋 Bem-vindo! Como podemos ajudar?",
                "confirmacao": "✅ Atendimento concluído com sucesso!",
                "erro_persistencia": "❌ Erro ao salvar seus dados. Transferindo para um atendente.",
                "revise_dados": "📋 Por favor, revise os dados informados:"
            },
            "branding": {"nome_empresa": "Nossa Empresa"}
            }

    # ══════════════════════════════════════════════════════════════
    # HELPER: EXTRAÇÃO SEGURA DE DADOS DA MENSAGEM
    # ══════════════════════════════════════════════════════════════
    
    def _extrair_dados_mensagem(self, mensagem: Mensagem) -> Dict[str, Any]:
        """
        Extrai dados da mensagem de forma segura, lidando com diferentes 
        formatos da Evolution API (texto, lista, botão).
        """
        msg_type = getattr(mensagem, 'tipo', 'text') or 'text'
        content = getattr(mensagem, 'conteudo', '') or ''
        
        # Se for resposta de lista ou botão, o conteúdo pode ser o ID da ação
        row_id = content.strip() if msg_type in ["list_response", "button_response"] else ""
        button_id = content.strip() if msg_type == "button_response" else ""
        
        return {
            "msg_type": msg_type,
            "content": content,
            "row_id": row_id,
            "button_id": button_id
        }

    # ══════════════════════════════════════════════════════════════
    # HELPER: VALIDAÇÃO DE WEBHOOK (SSRF PROTECTION)
    # ══════════════════════════════════════════════════════════════
    
    def _webhook_url_permitida(self, url: str) -> bool:
        """Valida se a URL do webhook é permitida, prevenindo Server-Side Request Forgery."""
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            
            # 1. Deve usar HTTPS
            if parsed.scheme != "https":
                return False
            
            hostname = parsed.hostname
            if not hostname:
                return False
            
            # 2. Bloquear hosts de metadados e loopback
            hosts_bloqueados = ["localhost", "127.0.0.1", "0.0.0.0", "::1", "169.254.169.254", "metadata.google.internal"]
            if hostname.lower() in hosts_bloqueados:
                return False
            
            # 3. Bloquear IPs privados
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    return False
            except ValueError:
                pass # É um domínio, prosseguir
            
            # 4. Deve ser um domínio válido (conter pelo menos um ponto)
            if "." not in hostname:
                return False
            
            return True
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════
    # MÉTODO PRINCIPAL: PROCESSAR MENSAGEM
    # ══════════════════════════════════════════════════════════════
    
    async def processar(self, atendimento: Atendimento, step: str, mensagem: Mensagem) -> None:
        dados_msg = self._extrair_dados_mensagem(mensagem)
        msg_type = dados_msg["msg_type"]
        content = dados_msg["content"]
        row = dados_msg["row_id"]
        button = dados_msg["button_id"]
        
        logger.debug("processar_atendimento", extra={
            "atendimento_id": atendimento.id, "step": step, "msg_type": msg_type
        })
        
        # Ações Globais
        acao = (row or button or content).strip().upper()
        
        if acao == "AT_FALAR":
            dados = self._obter_contexto(atendimento.id, "at_dados") or {}
            await self._transferir_atendente_com_dados(atendimento, dados)
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
        
        # Despacho por Estado
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
    # MENU E CATEGORIAS
    # ══════════════════════════════════════════════════════════════
    
    async def _menu_principal(self, atendimento: Atendimento, msg_type: str = "text", row: str = "") -> None:
        if not self.categorias:
            await self._enviar_texto(atendimento, "⚠️ Nenhuma categoria disponível no momento.")
            return
        
        if msg_type != "list_response":
            rows = self._renderizar_categorias()
            nome = self.branding.get("nome_empresa", "Nossa Empresa")
            await self._enviar_lista(atendimento, f"🏢 {nome} - Atendimento", self.mensagens.get("boas_vindas", "Selecione uma opção:"), rows, "Ver opções")
            self._avancar_step(atendimento, ESTADO_AT_CATEGORIA)
            return
        
        if row.startswith("AT_CAT_"):
            cat_id = row.replace("AT_CAT_", "")
            categoria = self._obter_categoria(cat_id)
            if categoria:
                self._guardar_contexto(atendimento.id, "at_categoria", cat_id)
                await self._exibir_submenus(atendimento, categoria)

    def _renderizar_categorias(self) -> List[Dict[str, str]]:
        rows = []
        for idx, cat in enumerate(self.categorias, 1):
            rows.append({"title": f"{cat.get('icone', '📌')} {idx}. {cat['nome']}", "description": cat.get("descricao", ""), "rowId": f"AT_CAT_{cat['id']}"})
        rows.append({"title": "🗣️ Falar com Atendente", "rowId": "AT_FALAR"})
        rows.append({"title": "🏠 Menu Principal", "rowId": "AT_VOLTAR_HUB"})
        return rows

    def _obter_categoria(self, cat_id: str) -> Optional[Dict]:
        return next((c for c in self.categorias if c["id"] == cat_id), None)

    async def _processar_categoria(self, atendimento: Atendimento, msg_type: str, row: str) -> None:
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
        submenus = categoria.get("submenus", [])
        if not submenus:
            await self._enviar_texto(atendimento, "Nenhuma opção disponível nesta categoria.")
            await self._menu_principal(atendimento)
            return
        
        rows = [{"title": f"{sub.get('icone', '📌')} {idx}. {sub['nome']}", "description": sub.get("descricao", ""), "rowId": f"AT_SUB_{sub['id']}"} for idx, sub in enumerate(submenus, 1)]
        rows.append({"title": "🔙 Voltar", "rowId": "AT_VOLTAR"})
        
        await self._enviar_lista(atendimento, f"{categoria.get('icone', '📌')} {categoria['nome']}", "Selecione uma opção:", rows, "Ver opções")
        self._avancar_step(atendimento, ESTADO_AT_INFORMACAO)

    # ══════════════════════════════════════════════════════════════
    # EXIBIÇÃO E COLETA DE DADOS
    # ══════════════════════════════════════════════════════════════
    
    async def _exibir_informacao(self, atendimento: Atendimento, msg_type: str, row: str) -> None:
        if row == "AT_VOLTAR":
            await self._menu_principal(atendimento)
            return
        
        if row.startswith("AT_SUB_"):
            sub_id = row.replace("AT_SUB_", "")
            categoria_id = self._obter_contexto(atendimento.id, "at_categoria")
            categoria = self._obter_categoria(categoria_id)
            
            if categoria:
                sub = next((s for s in categoria.get("submenus", []) if s["id"] == sub_id), None)
                if sub:
                    await self._enviar_texto(atendimento, sub.get("texto", "Informação não disponível."))
                    
                    if sub.get("tipo") == "coleta":
                        campos = sub.get("campos", [])
                        if campos:
                            # OTIMIZAÇÃO: Salvar objetos nativos, não JSON string
                            self._guardar_contexto(atendimento.id, "at_submenu", sub_id)
                            self._guardar_contexto(atendimento.id, "at_campos", campos)
                            self._guardar_contexto(atendimento.id, "at_indice", 0)
                            self._guardar_contexto(atendimento.id, "at_dados", {})
                            self._guardar_contexto(atendimento.id, "at_protocolo", gerar_protocolo("AT"))
                            await self._perguntar_campo(atendimento)
                    else:
                        await self._exibir_submenus(atendimento, categoria)

    async def _perguntar_campo(self, atendimento: Atendimento) -> None:
        # OTIMIZAÇÃO: Leitura direta de objeto, sem json.loads
        campos = self._obter_contexto(atendimento.id, "at_campos") or []
        indice = self._obter_contexto(atendimento.id, "at_indice") or 0
        
        if indice >= len(campos):
            await self._mostrar_revisao(atendimento)
            return
        
        campo = campos[indice]
        nome = campo.get("nome", "Campo")
        obrigatorio = campo.get("obrigatorio", False)
        opcoes = campo.get("opcoes", [])
        
        self._guardar_contexto(atendimento.id, "at_campo_atual", campo)
        
        if opcoes:
            rows = [{"title": f"{idx}. {opcao}", "rowId": f"AT_OP_{opcao}"} for idx, opcao in enumerate(opcoes, 1)]
            if not obrigatorio:
                rows.append({"title": "⏭️ Pular (opcional)", "rowId": "AT_PULAR"})
            
            await self._enviar_lista(atendimento, nome, "Selecione uma opção:", rows, "Ver opções")
        else:
            texto = f"*{nome}*"
            if obrigatorio: texto += " _(obrigatório)_"
            if campo.get("maximo"): texto += f" (máx. {campo['maximo']} caracteres)"
            if campo.get("minimo"): texto += f" (mín. {campo['minimo']} caracteres)"
            await self._enviar_texto(atendimento, texto)
        
        self._avancar_step(atendimento, ESTADO_AT_COLETA)

    async def _coletar_dados(self, atendimento: Atendimento, content: str) -> None:
        campos = self._obter_contexto(atendimento.id, "at_campos") or []
        indice = self._obter_contexto(atendimento.id, "at_indice") or 0
        dados = self._obter_contexto(atendimento.id, "at_dados") or {}
        
        if indice >= len(campos):
            return
        
        campo = campos[indice]
        nome = campo.get("nome", "Campo")
        
        if content.upper() == "AT_PULAR":
            self._guardar_contexto(atendimento.id, "at_indice", indice + 1)
            await self._perguntar_campo(atendimento)
            return
        
        # Validação usando o módulo refatorado
        ok, msg = validar_campo(
            content,
            tipo=campo.get("tipo", "texto"),
            obrigatorio=campo.get("obrigatorio", False),
            minimo=campo.get("minimo"),
            maximo=campo.get("maximo")
        )
        
        if not ok:
            await self._enviar_texto(atendimento, f"❌ {msg}\n\nPor favor, digite novamente:")
            await self._perguntar_campo(atendimento)
            return
        
        # Salva o dado
        if content.startswith("AT_OP_"):
            dados[nome] = content.replace("AT_OP_", "")
        else:
            dados[nome] = content
            
        self._guardar_contexto(atendimento.id, "at_dados", dados)
        self._guardar_contexto(atendimento.id, "at_indice", indice + 1)
        await self._perguntar_campo(atendimento)

    # ══════════════════════════════════════════════════════════════
    # REVISÃO E FINALIZAÇÃO
    # ══════════════════════════════════════════════════════════════
    
    async def _mostrar_revisao(self, atendimento: Atendimento) -> None:
        dados = self._obter_contexto(atendimento.id, "at_dados") or {}
        protocolo = self._obter_contexto(atendimento.id, "at_protocolo") or "—"
        
        if not dados:
            await self._menu_principal(atendimento)
            return
        
        resumo = f"📋 *Resumo do Atendimento*\n\n🔖 Protocolo: *{protocolo}*\n\n"
        for chave, valor in dados.items():
            if valor:
                resumo += f"• *{chave}*: {valor}\n"
        
        resumo += f"\n{self.mensagens.get('revise_dados', 'Por favor, revise os dados informados:')}"
        await self._enviar_texto(atendimento, resumo)
        
        rows = [
            {"title": "✅ Confirmar e Enviar", "rowId": "AT_CONFIRMAR"},
            {"title": "✏️ Corrigir", "rowId": "AT_CORRIGIR"},
            {"title": "🗣️ Falar com Atendente", "rowId": "AT_FALAR"},
            {"title": "❌ Cancelar", "rowId": "AT_CANCELAR"}
        ]
        await self._enviar_lista(atendimento, "Confirmação", "O que deseja fazer?", rows, "Responder")
        self._avancar_step(atendimento, ESTADO_AT_REVISAO)

    async def _revisar_dados(self, atendimento: Atendimento, msg_type: str, row: str) -> None:
        if row == "AT_CONFIRMAR":
            await self._persistir_e_finalizar(atendimento)
        elif row == "AT_CORRIGIR":
            await self._enviar_texto(atendimento, "🔄 Recomeçando a coleta de dados...")
            self._guardar_contexto(atendimento.id, "at_indice", 0)
            self._guardar_contexto(atendimento.id, "at_dados", {})
            await self._perguntar_campo(atendimento)
        elif row == "AT_FALAR":
            dados = self._obter_contexto(atendimento.id, "at_dados") or {}
            await self._transferir_atendente_com_dados(atendimento, dados)
        elif row == "AT_CANCELAR":
            await self._cancelar_atendimento(atendimento)
        else:
            await self._mostrar_revisao(atendimento)

    async def _persistir_e_finalizar(self, atendimento: Atendimento) -> None:
        try:
            dados = self._obter_contexto(atendimento.id, "at_dados") or {}
            protocolo = self._obter_contexto(atendimento.id, "at_protocolo") or gerar_protocolo("AT")
            submenu = self._obter_contexto(atendimento.id, "at_submenu") or "N/A"
            
            if not dados:
                await self._enviar_texto(atendimento, "⚠️ Nenhum dado para salvar.")
                await self._menu_principal(atendimento)
                return
            
            # 1. Salvar no Banco
            if self.persistencia_config.get("salvar_no_banco", True):
                registro = await self._salvar_no_banco(atendimento.id, self.empresa_id, submenu, protocolo, dados)
                if registro and hasattr(registro, 'id'):
                    self._guardar_contexto(atendimento.id, "at_registro_id", registro.id)
            
            # 2. Enviar para Webhook
            webhook_url = self.webhook_config.get("url")
            if webhook_url and self._webhook_url_permitida(webhook_url):
                await self._enviar_webhook(dados, protocolo, atendimento)
            
            # 3. Mensagem de Sucesso
            msg_final = f"✅ Dados salvos com sucesso!\n\n🔖 Protocolo: *{protocolo}*\n📋 {len(dados)} campos coletados.\n\n{self.mensagens.get('confirmacao', 'Agradecemos seu contato!')}"
            await self._enviar_texto(atendimento, msg_final)
            
            # 4. Estado Final e Limpeza
            self._avancar_step(atendimento, ESTADO_AT_FINALIZAR)
            self._limpar_contexto_completo(atendimento.id)
            
        except Exception as e:
            logger.error("erro_persistir_dados", extra={"atendimento_id": atendimento.id, "empresa_id": self.empresa_id, "erro": str(e)})
            await self._enviar_texto(atendimento, self.mensagens.get("erro_persistencia", "❌ Erro ao salvar. Transferindo para um atendente."))
            dados = self._obter_contexto(atendimento.id, "at_dados") or {}
            await self._transferir_atendente_com_dados(atendimento, dados)

    async def _salvar_no_banco(self, atendimento_id: int, empresa_id: int, submenu: str, protocolo: str, dados: Dict[str, Any]) -> Optional[RegistroAtendimento]:
        try:
            registro = RegistroAtendimento(
                atendimento_id=atendimento_id,
                empresa_id=empresa_id,
                submenu=submenu,
                protocolo=protocolo,
                dados_json=json.dumps(dados, ensure_ascii=False),
                data_criacao=datetime.utcnow(),
                status="PENDENTE"
            )
            self.session.add(registro)
            self.session.commit()
            self.session.refresh(registro)
            
            logger.info("registro_salvo", extra={"registro_id": registro.id, "protocolo": protocolo, "empresa_id": empresa_id, "qtd_campos": len(dados)})
            return registro
        except Exception as e:
            self.session.rollback()
            logger.error("erro_bd_salvar_registro", extra={"atendimento_id": atendimento_id, "erro": str(e)})
            return None

    async def _enviar_webhook(self, dados: Dict[str, Any], protocolo: str, atendimento: Atendimento) -> None:
        """Envia os dados coletados para o sistema externo do cliente (White-Label)."""
        url = self.webhook_config.get("url")
        metodo = self.webhook_config.get("metodo", "POST").upper()
        headers = self.webhook_config.get("headers", {}).copy() # Cópia para evitar mutação
        timeout = self.webhook_config.get("timeout", 10)
        
        payload = {
            "evento": "atendimento_concluido",
            "protocolo": protocolo,
            "atendimento_id": atendimento.id,
            "empresa_id": self.empresa_id,
            "dados": dados,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(metodo, url, json=payload, headers=headers, timeout=timeout) as response:
                    if response.status in (200, 201, 202):
                        logger.info("webhook_enviado_sucesso", extra={"atendimento_id": atendimento.id, "status": response.status})
                    else:
                        logger.warning("webhook_resposta_erro", extra={"atendimento_id": atendimento.id, "status": response.status})
        except asyncio.TimeoutError:
            logger.error("webhook_timeout", extra={"atendimento_id": atendimento.id, "url": url})
        except Exception as e:
            logger.error("webhook_falha_conexao", extra={"atendimento_id": atendimento.id, "erro": str(e)})

    # ══════════════════════════════════════════════════════════════
    # MÉTODOS AUXILIARES DE FLUXO
    # ══════════════════════════════════════════════════════════════
    
    async def _transferir_atendente_com_dados(self, atendimento: Atendimento, dados: Dict[str, Any]) -> None:
        """Transfere para atendente humano, anexando os dados já coletados."""
        dados_formatados = "\n".join([f"• {k}: {v}" for k, v in dados.items()])
        msg = f"🗣️ *Transferindo para um atendente...*\n\n_Dados já coletados:_\n{dados_formatados}\n\nAguarde um momento! 😊"
        await self._enviar_texto(atendimento, msg)
        # TODO: Lógica real de fila de atendimento (ex: atualizar status no DB)
        self._limpar_contexto_completo(atendimento.id)

    async def _cancelar_atendimento(self, atendimento: Atendimento) -> None:
        """Cancela o fluxo e limpa o contexto."""
        await self._enviar_texto(atendimento, "❌ Atendimento cancelado. Se precisar de algo, estamos à disposição.")
        self._limpar_contexto_completo(atendimento.id)
        await self._voltar_hub(atendimento)

    async def _finalizar(self, atendimento: Atendimento) -> None:
        """
        Estado terminal. Se o usuário enviar mensagem neste estado, 
        reinicia o fluxo ou transfere, dependendo da regra de negócio.
        """
        await self._enviar_texto(atendimento, "Seu atendimento foi finalizado. Digite *MENU* para iniciar um novo atendimento ou *FALAR* para chamar um atendente.")
        # Opcional: self._avancar_step(atendimento, ESTADO_AT_MENU)