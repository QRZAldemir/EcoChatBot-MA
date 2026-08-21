"""
================================================================================
HANDLER DE AGENDAMENTOS (PLATAFORMA WHITE-LABEL)
================================================================================
Arquivo: bot_handlers/agendamento_handler.py
Propósito: Framework universal para agendamentos (qualquer modelo de negócio)

DESENVOLVEDOR: Aldemir Queiroz da Silva
DATA: 2026-08-16

Este handler atende QUALQUER modelo de negócio:
  - Clínicas/Hospitais: Consultas, exames
  - Lojas: Agendamento de visitas
  - Escolas: Matrículas, reuniões
  - Serviços: Manutenção, consultorias
  - E qualquer outro negócio que precise agendar!

================================================================================
"""

from sqlalchemy.orm import Session
from app.models import Atendimento, Mensagem
from .base_handler import DepartamentoHandler
import json
from typing import Optional, Dict, List, Any


# CONSTANTES: Estados
ESTADO_AG_MENU = "AG:MENU"
ESTADO_AG_SERVICO = "AG:SERVICO"
ESTADO_AG_COLETA = "AG:COLETA"
ESTADO_AG_REVISAO = "AG:REVISAO"
ESTADO_AG_CONFIRMACAO = "AG:CONFIRMACAO"


class AgendamentoHandler(DepartamentoHandler):
    """
    HANDLER UNIVERSAL PARA AGENDAMENTOS
    
    Responsabilidades:
      1. Gerenciar fluxo de agendamentos para qualquer tipo de negócio
      2. Carregar serviços/configurações específicas do cliente
      3. Coletar dados estruturados de forma configurável
      4. Validar entradas com regras personalizadas
      5. Confirmar e registrar agendamentos
    """
    
    def __init__(self, session: Session, empresa_id: int):
        super().__init__(session)
        self.empresa_id = empresa_id
        self.configuracao = self._carregar_configuracao(empresa_id)
        self.servicos = self.configuracao.get("servicos", [])
        self.mensagens = self.configuracao.get("mensagens", {})
        self.branding = self.configuracao.get("branding", {})
    
    def _carregar_configuracao(self, empresa_id: int) -> Dict[str, Any]:
        """
        Carrega configurações da empresa
        
        ESTRUTURA DA CONFIGURAÇÃO:
        {
            "servicos": [
                {
                    "id": "CONSULTA",
                    "nome": "Consulta",
                    "icone": "🩺",
                    "campos": [
                        {"nome": "Nome", "tipo": "texto", "obrigatorio": True},
                        {"nome": "Data", "tipo": "data", "obrigatorio": True},
                        {"nome": "Horário", "tipo": "hora", "obrigatorio": True}
                    ]
                }
            ],
            "mensagens": {
                "boas_vindas": "Bem-vindo ao agendamento!",
                "confirmacao": "Agendamento confirmado!"
            }
        }
        """
        # TODO: Buscar do banco de dados
        return self._configuracao_padrao()
    
    def _configuracao_padrao(self) -> Dict[str, Any]:
        """Configuração padrão (fallback)"""
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
                "confirmacao": "✅ Agendamento confirmado!"
            },
            "branding": {
                "nome_empresa": "Nossa Empresa"
            }
        }
    
    async def processar(
        self,
        atendimento: Atendimento,
        step: str,
        mensagem: Mensagem,
    ) -> None:
        """
        POLIMORFISMO: Implementação específica para Agendamentos
        """
        # TODO: Recuperar msg_type e content
        msg_type = "text"
        content = ""
        row = content.strip().upper() if msg_type == "list_response" else ""
        
        # Ações globais
        if row == "AG_FALAR":
            await self._transferir_atendente(atendimento)
            return
        
        if row == "AG_VOLTAR_HUB":
            await self._voltar_hub(atendimento)
            return
        
        if row == "AG_CANCELAR":
            self._limpar_contexto_completo(atendimento.id)
            await self._menu_principal(atendimento)
            return
        
        # Despacho por estado
        if step == ESTADO_AG_MENU:
            await self._menu_principal(atendimento, msg_type, row)
        elif step == ESTADO_AG_SERVICO:
            await self._processar_servico(atendimento, msg_type, row)
        elif step == ESTADO_AG_COLETA:
            await self._coletar_dados(atendimento, content)
        elif step == ESTADO_AG_REVISAO:
            await self._revisar_agendamento(atendimento, msg_type, row)
        elif step == ESTADO_AG_CONFIRMACAO:
            await self._confirmar_agendamento(atendimento, row)
    
    async def _menu_principal(
        self,
        atendimento: Atendimento,
        msg_type: str = "text",
        row: str = ""
    ) -> None:
        """Menu principal com serviços"""
        if not self.servicos:
            await self._enviar_texto(atendimento, "⚠️ Nenhum serviço disponível.")
            return
        
        if msg_type != "list_response":
            rows = self._renderizar_servicos()
            nome = self.branding.get("nome_empresa", "Nossa Empresa")
            
            await self._enviar_lista(
                atendimento,
                f"📅 {nome} - Agendamentos",
                self.mensagens.get("boas_vindas", "Selecione um serviço:"),
                rows,
                "Ver serviços"
            )
            self._avancar_step(atendimento, ESTADO_AG_SERVICO)
            return
        
        # Processa seleção
        if row.startswith("AG_SERV_"):
            servico_id = row.replace("AG_SERV_", "")
            servico = self._obter_servico(servico_id)
            if servico:
                self._iniciar_agendamento(atendimento, servico)
    
    def _renderizar_servicos(self) -> List[Dict[str, str]]:
        """Renderiza serviços para menu"""
        rows = []
        for idx, servico in enumerate(self.servicos, 1):
            rows.append({
                "title": f"{servico.get('icone', '📌')} {idx}. {servico['nome']}",
                "description": servico.get("descricao", ""),
                "rowId": f"AG_SERV_{servico['id']}"
            })
        
        rows.append({"title": "🗣️ Falar com Atendente", "rowId": "AG_FALAR"})
        rows.append({"title": "🏠 Menu Principal", "rowId": "AG_VOLTAR_HUB"})
        return rows
    
    def _obter_servico(self, servico_id: str) -> Optional[Dict]:
        """Busca serviço pelo ID"""
        return next((s for s in self.servicos if s["id"] == servico_id), None)
    
    def _iniciar_agendamento(self, atendimento: Atendimento, servico: Dict) -> None:
        """Inicia processo de agendamento"""
        campos = servico.get("campos", [])
        
        if not campos:
            await self._enviar_texto(atendimento, "Serviço não configurado.")
            return
        
        # Inicializa contexto
        self._guardar_contexto(atendimento.id, "ag_servico", servico['id'])
        self._guardar_contexto(atendimento.id, "ag_campos", json.dumps(campos))
        self._guardar_contexto(atendimento.id, "ag_indice", 0)
        self._guardar_contexto(atendimento.id, "ag_dados", json.dumps({}))
        self._guardar_contexto(atendimento.id, "ag_protocolo", self._gerar_protocolo("AG"))
        
        # Começa coleta
        self._avancar_step(atendimento, ESTADO_AG_COLETA)
        self._perguntar_campo(atendimento)
    
    async def _processar_servico(self, atendimento: Atendimento, msg_type: str, row: str) -> None:
        """Processa seleção de serviço"""
        if msg_type != "list_response":
            await self._menu_principal(atendimento)
            return
        
        if row.startswith("AG_SERV_"):
            servico_id = row.replace("AG_SERV_", "")
            servico = self._obter_servico(servico_id)
            if servico:
                self._iniciar_agendamento(atendimento, servico)
    
    async def _perguntar_campo(self, atendimento: Atendimento) -> None:
        """Pergunta o próximo campo"""
        campos_str = self._obter_contexto(atendimento.id, "ag_campos") or "[]"
        campos = json.loads(campos_str)
        indice = int(self._obter_contexto(atendimento.id, "ag_indice") or 0)
        
        if indice >= len(campos):
            await self._mostrar_revisao(atendimento)
            return
        
        campo = campos[indice]
        nome = campo.get("nome", "Campo")
        obrigatorio = campo.get("obrigatorio", False)
        opcoes = campo.get("opcoes", [])
        
        texto = f"*{nome}*"
        if obrigatorio:
            texto += " (obrigatório)"
        
        await self._enviar_texto(atendimento, texto)
        self._avancar_step(atendimento, ESTADO_AG_COLETA)
    
    async def _coletar_dados(self, atendimento: Atendimento, content: str) -> None:
        """Coleta dados do campo atual"""
        campos_str = self._obter_contexto(atendimento.id, "ag_campos") or "[]"
        campos = json.loads(campos_str)
        indice = int(self._obter_contexto(atendimento.id, "ag_indice") or 0)
        
        if indice >= len(campos):
            return
        
        campo = campos[indice]
        nome = campo.get("nome", "Campo")
        
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
            await self._perguntar_campo(atendimento)
            return
        
        # Salva dados
        dados_str = self._obter_contexto(atendimento.id, "ag_dados") or "{}"
        dados = json.loads(dados_str)
        dados[nome] = content
        self._guardar_contexto(atendimento.id, "ag_dados", json.dumps(dados))
        
        # Avança
        self._guardar_contexto(atendimento.id, "ag_indice", indice + 1)
        await self._perguntar_campo(atendimento)
    
    async def _mostrar_revisao(self, atendimento: Atendimento) -> None:
        """Mostra resumo para revisão"""
        dados_str = self._obter_contexto(atendimento.id, "ag_dados") or "{}"
        dados = json.loads(dados_str)
        protocolo = self._obter_contexto(atendimento.id, "ag_protocolo") or "—"
        
        resumo = f"📋 *Resumo do Agendamento*\n\n"
        resumo += f"🔖 Protocolo: *{protocolo}*\n\n"
        
        for chave, valor in dados.items():
            resumo += f"• {chave}: {valor}\n"
        
        resumo += "\nAs informações estão corretas?"
        
        await self._enviar_texto(atendimento, resumo)
        
        rows = [
            {"title": "✅ Confirmar", "rowId": "AG_CONFIRMAR"},
            {"title": "✏️ Corrigir", "rowId": "AG_CORRIGIR"},
            {"title": "❌ Cancelar", "rowId": "AG_CANCELAR"}
        ]
        
        await self._enviar_lista(
            atendimento,
            "Confirmação",
            "Deseja confirmar o agendamento?",
            rows,
            "Responder"
        )
        self._avancar_step(atendimento, ESTADO_AG_REVISAO)
    
    async def _revisar_agendamento(self, atendimento: Atendimento, msg_type: str, row: str) -> None:
        """Processa revisão do agendamento"""
        if row == "AG_CONFIRMAR":
            await self._confirmar_agendamento(atendimento, row)
        elif row == "AG_CORRIGIR":
            # Limpa dados e recomeça
            self._limpar_contexto_completo(atendimento.id)
            await self._menu_principal(atendimento)
        elif row == "AG_CANCELAR":
            self._limpar_contexto_completo(atendimento.id)
            await self._enviar_texto(atendimento, "❌ Agendamento cancelado.")
            await self._menu_principal(atendimento)
    
    async def _confirmar_agendamento(self, atendimento: Atendimento, row: str) -> None:
        """Confirma e registra o agendamento"""
        if row != "AG_CONFIRMAR":
            return
        
        dados_str = self._obter_contexto(atendimento.id, "ag_dados") or "{}"
        dados = json.loads(dados_str)
        protocolo = self._obter_contexto(atendimento.id, "ag_protocolo") or "—"
        
        msg = f"✅ *Agendamento Confirmado!*\n\n"
        msg += f"🔖 Protocolo: *{protocolo}*\n\n"
        msg += "📌 *Dados:*\n"
        for chave, valor in dados.items():
            msg += f"• {chave}: {valor}\n"
        
        msg += f"\n{self.mensagens.get('confirmacao', 'Agradecemos!')}"
        
        await self._enviar_texto(atendimento, msg)
        
        # TODO: Enviar para webhook/ERP
        # TODO: Salvar no banco de dados
        
        self._limpar_contexto_completo(atendimento.id)
        self._avancar_step(atendimento, ESTADO_AG_CONFIRMACAO)