"""
================================================================================
MÓDULO: app/services/canal_service.py
AUTOR: Aldemir Queiroz
DATA: 2026-09-16
VERSÃO: 2.0.0
OBJETIVO: Implementa a lógica de negócios para gestão de canais omnichannel.
          Inclui CRUD, validações, configuração de webhooks e métricas.
PASTA: backend/app/services/
================================================================================
"""
import json
import logging
import os
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models import Canal, Cliente, Departamento
from app.schemas.canal import CanalCreate, CanalUpdate, CanalResponse
from app.exceptions import (
    CanalNaoEncontradoError,
    CanalNomeDuplicadoError,
    CanalTipoInvalidoError,
    RecursoInvalidoError
)

logger = logging.getLogger(__name__)


class CanalService:
    """
    Serviço para gestão de canais de comunicação.
    
    Responsabilidades:
        - CRUD completo de canais
        - Validação de unicidade por tenant
        - Configuração automática de webhooks
        - Métricas e estatísticas de uso
        - Isolamento multi-tenant rigoroso
    """

    def __init__(self, db: Session):
        """
        Inicializa o serviço com sessão de banco de dados.
        
        Args:
            db (Session): Sessão SQLAlchemy
        """
        self.db = db

    # ==============================================================================
    # MÉTODOS DE CRUD
    # ==============================================================================
    
    def criar_canal(
        self, 
        data: CanalCreate, 
        cliente_id: int
    ) -> Canal:
        """
        Cria um novo canal para o tenant especificado.
        
        Fluxo:
            1. Valida se o nome já existe para este tenant
            2. Valida o tipo de canal
            3. Valida o departamento (se fornecido)
            4. Serializa configurações JSON
            5. Cria o registro no banco
            6. Configura webhook automaticamente (async)
        
        Args:
            data (CanalCreate): Dados do canal
            cliente_id (int): ID do tenant/empresa
        
        Returns:
            Canal: Canal criado
        
        Raises:
            CanalNomeDuplicadoError: Se nome já existir
            RecursoInvalidoError: Se departamento inválido
        """
        # 1. Validar nome único por tenant
        self._validar_nome_unico(data.nome, cliente_id)
        
        # 2. Validar tipo de canal
        self._validar_tipo_canal(data.tipo)
        
        # 3. Validar departamento (se fornecido)
        if data.departamento_id:
            self._validar_departamento(data.departamento_id, cliente_id)
        
        # 4. Serializar configurações JSON
        configuracao_json = None
        if data.configuracao:
            try:
                configuracao_json = json.dumps(data.configuracao)
            except (TypeError, ValueError) as e:
                logger.error(f"Erro ao serializar configurações: {e}")
                raise RecursoInvalidoError("Configurações em formato inválido")
        
        # 5. Criar canal
        canal = Canal(
            cliente_id=cliente_id,
            nome=data.nome,
            descricao=data.descricao,
            tipo=data.tipo,
            identificador=data.identificador,
            configuracao=configuracao_json,
            departamento_id=data.departamento_id,
            ativo=data.ativo,
            criado_em=datetime.now(timezone.utc)
        )
        
        self.db.add(canal)
        self.db.commit()
        self.db.refresh(canal)
        
        logger.info(f"Canal criado: ID={canal.id}, tipo={canal.tipo}, tenant={cliente_id}")
        
        # 6. Configurar webhook automaticamente (em background)
        # Nota: Em produção, usar Celery/RQ para task assíncrona
        try:
            self._configurar_webhook_async(canal)
        except Exception as e:
            logger.warning(f"Falha ao configurar webhook automaticamente: {e}")
            # Não falha a criação do canal se webhook falhar
        
        return canal

    def buscar_por_id(self, canal_id: int, cliente_id: int) -> Canal:
        """
        Busca canal por ID com validação de tenant.
        
        Args:
            canal_id (int): ID do canal
            cliente_id (int): ID do tenant para isolamento
        
        Returns:
            Canal: Canal encontrado
        
        Raises:
            CanalNaoEncontradoError: Se canal não existir ou pertencer a outro tenant
        """
        canal = self.db.query(Canal).filter(
            Canal.id == canal_id,
            Canal.cliente_id == cliente_id
        ).first()
        
        if not canal:
            raise CanalNaoEncontradoError(
                f"Canal {canal_id} não encontrado ou você não tem permissão"
            )
        
        return canal

    def listar_canais(
        self,
        cliente_id: int,
        page: int = 1,
        limit: int = 50,
        tipo: Optional[str] = None,
        ativo: Optional[bool] = None
    ) -> Tuple[List[Canal], int]:
        """
        Lista canais do tenant com filtros e paginação.
        
        Args:
            cliente_id (int): ID do tenant
            page (int): Número da página (1-based)
            limit (int): Limite de registros por página
            tipo (str, optional): Filtrar por tipo de canal
            ativo (bool, optional): Filtrar por status
        
        Returns:
            Tuple[List[Canal], int]: Lista de canais e total de registros
        """
        # Query base com isolamento de tenant
        query = self.db.query(Canal).filter(Canal.cliente_id == cliente_id)
        
        # Aplicar filtros
        if tipo:
            query = query.filter(Canal.tipo == tipo)
        
        if ativo is not None:
            query = query.filter(Canal.ativo == ativo)
        
        # Contar total
        total = query.count()
        
        # Paginação
        offset = (page - 1) * limit
        canais = query.order_by(Canal.criado_em.desc()).offset(offset).limit(limit).all()
        
        return canais, total

    def atualizar_canal(
        self,
        canal_id: int,
        cliente_id: int,
        data: CanalUpdate
    ) -> Canal:
        """
        Atualiza canal parcialmente.
        
        Args:
            canal_id (int): ID do canal
            cliente_id (int): ID do tenant
            data (CanalUpdate): Dados para atualização
        
        Returns:
            Canal: Canal atualizado
        
        Raises:
            CanalNaoEncontradoError: Se canal não existir
        """
        canal = self.buscar_por_id(canal_id, cliente_id)
        
        # Validar nome único se estiver sendo alterado
        if data.nome and data.nome != canal.nome:
            self._validar_nome_unico(data.nome, cliente_id, exclude_id=canal_id)
        
        # Validar departamento se estiver sendo alterado
        if data.departamento_id and data.departamento_id != canal.departamento_id:
            self._validar_departamento(data.departamento_id, cliente_id)
        
        # Atualizar campos
        update_data = data.model_dump(exclude_unset=True)
        
        # Serializar configurações se fornecidas
        if "configuracao" in update_data and update_data["configuracao"] is not None:
            try:
                update_data["configuracao"] = json.dumps(update_data["configuracao"])
            except (TypeError, ValueError) as e:
                logger.error(f"Erro ao serializar configurações: {e}")
                raise RecursoInvalidoError("Configurações em formato inválido")
        
        # Atualizar timestamp
        update_data["atualizado_em"] = datetime.now(timezone.utc)
        
        for key, value in update_data.items():
            setattr(canal, key, value)
        
        self.db.commit()
        self.db.refresh(canal)
        
        logger.info(f"Canal atualizado: ID={canal.id}")
        
        return canal

    def deletar_canal(self, canal_id: int, cliente_id: int) -> bool:
        """
        Deleta canal (soft delete via cascade).
        
        Args:
            canal_id (int): ID do canal
            cliente_id (int): ID do tenant
        
        Returns:
            bool: True se deletado com sucesso
        
        Raises:
            CanalNaoEncontradoError: Se canal não existir
        """
        canal = self.buscar_por_id(canal_id, cliente_id)
        
        # Verificar se tem atendimentos ativos
        from app.models import Atendimento
        atendimentos_ativos = self.db.query(Atendimento).filter(
            Atendimento.canal_id == canal_id,
            Atendimento.status.in_(["aberto", "fila", "em_atendimento"])
        ).count()
        
        if atendimentos_ativos > 0:
            raise RecursoInvalidoError(
                f"Não é possível deletar canal com {atendimentos_ativos} atendimento(s) ativo(s)"
            )
        
        self.db.delete(canal)
        self.db.commit()
        
        logger.info(f"Canal deletado: ID={canal_id}")
        
        return True

    # ==============================================================================
    # MÉTODOS DE VALIDAÇÃO
    # ==============================================================================
    
    def _validar_nome_unico(
        self, 
        nome: str, 
        cliente_id: int, 
        exclude_id: Optional[int] = None
    ) -> None:
        """
        Valida se o nome do canal é único para o tenant.
        
        Args:
            nome (str): Nome do canal
            cliente_id (int): ID do tenant
            exclude_id (int, optional): ID do canal a excluir (para update)
        
        Raises:
            CanalNomeDuplicadoError: Se nome já existir
        """
        query = self.db.query(Canal).filter(
            Canal.cliente_id == cliente_id,
            func.lower(Canal.nome) == nome.lower().strip()
        )
        
        if exclude_id:
            query = query.filter(Canal.id != exclude_id)
        
        if query.first():
            raise CanalNomeDuplicadoError(
                f"Já existe um canal com o nome '{nome}' para esta empresa"
            )

    def _validar_tipo_canal(self, tipo: str) -> None:
        """
        Valida se o tipo de canal é suportado.
        
        Args:
            tipo (str): Tipo do canal
        
        Raises:
            CanalTipoInvalidoError: Se tipo não for suportado
        """
        tipos_validos = [
            "whatsapp", "telegram", "instagram", "facebook",
            "discord", "voip_telefonia", "email", "chat_web"
        ]
        
        if tipo not in tipos_validos:
            raise CanalTipoInvalidoError(
                f"Tipo de canal '{tipo}' não é suportado. "
                f"Tipos válidos: {', '.join(tipos_validos)}"
            )

    def _validar_departamento(self, departamento_id: int, cliente_id: int) -> None:
        """
        Valida se o departamento existe e pertence ao tenant.
        
        Args:
            departamento_id (int): ID do departamento
            cliente_id (int): ID do tenant
        
        Raises:
            RecursoInvalidoError: Se departamento não existir
        """
        # Nota: Departamento não tem cliente_id no modelo atual
        # Se necessário, adicionar validação de tenant em Departamento
        depto = self.db.query(Departamento).filter(
            Departamento.id == departamento_id,
            Departamento.ativo == True
        ).first()
        
        if not depto:
            raise RecursoInvalidoError(
                "Departamento não encontrado ou inativo"
            )

    # ==============================================================================
    # MÉTODOS DE WEBHOOK
    # ==============================================================================
    
    def _configurar_webhook_async(self, canal: Canal) -> bool:
        """
        Configura webhook na API externa do canal.
        
        Implementações específicas por tipo:
            - WhatsApp (Meta): POST /{phone_number_id}/messages
            - Telegram: POST /bot{token}/setWebhook
            - Instagram: Via Meta Graph API
            - Discord: Via API do Discord
        
        Args:
            canal (Canal): Canal configurado
        
        Returns:
            bool: True se configurado com sucesso
        """
        backend_url = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000")
        webhook_url = f"{backend_url}/api/webhook/{canal.tipo}/{canal.id}"
        
        try:
            if canal.tipo == "telegram":
                return self._configurar_webhook_telegram(canal, webhook_url)
            
            elif canal.tipo == "whatsapp":
                return self._configurar_webhook_whatsapp(canal, webhook_url)
            
            elif canal.tipo in ("instagram", "facebook"):
                return self._configurar_webhook_meta(canal, webhook_url)
            
            elif canal.tipo == "discord":
                return self._configurar_webhook_discord(canal, webhook_url)
            
            else:
                logger.info(f"Webhook não necessário para tipo: {canal.tipo}")
                return True
        
        except Exception as e:
            logger.error(f"Erro ao configurar webhook: {e}")
            return False

    def _configurar_webhook_telegram(self, canal: Canal, webhook_url: str) -> bool:
        """
        Configura webhook do Telegram Bot API.
        
        Args:
            canal (Canal): Canal Telegram
            webhook_url (str): URL do webhook
        
        Returns:
            bool: Sucesso da operação
        """
        import httpx
        
        token = canal.identificador
        url = f"https://api.telegram.org/bot{token}/setWebhook"
        
        payload = {
            "url": webhook_url,
            "allowed_updates": ["message", "callback_query", "edited_message"],
            "max_connections": 100
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                
                if result.get("ok"):
                    logger.info(f"Webhook Telegram configurado: {webhook_url}")
                    
                    # Atualizar último sync
                    canal.ultimo_sync = datetime.now(timezone.utc)
                    canal.webhook_url = webhook_url
                    self.db.commit()
                    
                    return True
                else:
                    logger.error(f"Telegram API error: {result}")
                    return False
        
        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP ao configurar webhook Telegram: {e}")
            return False

    def _configurar_webhook_whatsapp(self, canal: Canal, webhook_url: str) -> bool:
        """
        Configura webhook do WhatsApp (Meta Cloud API).
        
        Nota: A configuração do webhook é feita no painel da Meta,
        mas podemos validar a URL via API.
        
        Args:
            canal (Canal): Canal WhatsApp
            webhook_url (str): URL do webhook
        
        Returns:
            bool: Sucesso da operação
        """
        # Para Meta Cloud API, o webhook é configurado no App Dashboard
        # Aqui apenas registramos a URL no banco
        canal.webhook_url = webhook_url
        canal.ultimo_sync = datetime.now(timezone.utc)
        self.db.commit()
        
        logger.info(f"Webhook WhatsApp registrado: {webhook_url}")
        return True

    def _configurar_webhook_meta(self, canal: Canal, webhook_url: str) -> bool:
        """
        Configura webhook do Instagram/Facebook (Meta Graph API).
        
        Args:
            canal (Canal): Canal Instagram/Facebook
            webhook_url (str): URL do webhook
        
        Returns:
            bool: Sucesso da operação
        """
        # Similar ao WhatsApp - configuração via Meta App Dashboard
        canal.webhook_url = webhook_url
        canal.ultimo_sync = datetime.now(timezone.utc)
        self.db.commit()
        
        logger.info(f"Webhook Meta registrado: {webhook_url}")
        return True

    def _configurar_webhook_discord(self, canal: Canal, webhook_url: str) -> bool:
        """
        Configura webhook do Discord API.
        
        Args:
            canal (Canal): Canal Discord
            webhook_url (str): URL do webhook
        
        Returns:
            bool: Sucesso da operação
        """
        import httpx
        
        # Discord usa Interactions Endpoint URL
        config = canal.configuracao_json
        app_id = config.get("app_id")
        
        if not app_id:
            logger.warning("App ID não configurado para Discord")
            return False
        
        url = f"https://discord.com/api/v10/applications/{app_id}/interaction-endpoint"
        
        headers = {
            "Authorization": f"Bot {canal.identificador}",
            "Content-Type": "application/json"
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.put(url, json={"url": webhook_url}, headers=headers)
                response.raise_for_status()
                
                canal.webhook_url = webhook_url
                canal.ultimo_sync = datetime.now(timezone.utc)
                self.db.commit()
                
                logger.info(f"Webhook Discord configurado: {webhook_url}")
                return True
        
        except httpx.HTTPError as e:
            logger.error(f"Erro ao configurar webhook Discord: {e}")
            return False

    # ==============================================================================
    # MÉTODOS DE MÉTRICAS
    # ==============================================================================
    
    def obter_metricas_canal(self, canal_id: int, cliente_id: int) -> Dict[str, Any]:
        """
        Obtém métricas detalhadas do canal.
        
        Args:
            canal_id (int): ID do canal
            cliente_id (int): ID do tenant
        
        Returns:
            Dict: Métricas do canal
        """
        canal = self.buscar_por_id(canal_id, cliente_id)
        
        from app.models import Atendimento, Mensagem
        from datetime import datetime, timedelta
        
        hoje = datetime.now(timezone.utc).date()
        
        # Contagem de atendimentos
        atendimentos_hoje = self.db.query(Atendimento).filter(
            Atendimento.canal_id == canal_id,
            func.date(Atendimento.criado_em) == hoje
        ).count()
        
        atendimentos_ativos = self.db.query(Atendimento).filter(
            Atendimento.canal_id == canal_id,
            Atendimento.status.in_(["aberto", "fila", "em_atendimento"])
        ).count()
        
        # Mensagens
        mensagens_enviadas = self.db.query(Mensagem).filter(
            Mensagem.canal_id == canal_id,
            Mensagem.tipo == "enviada",
            func.date(Mensagem.criado_em) == hoje
        ).count()
        
        mensagens_recebidas = self.db.query(Mensagem).filter(
            Mensagem.canal_id == canal_id,
            Mensagem.tipo == "recebida",
            func.date(Mensagem.criado_em) == hoje
        ).count()
        
        return {
            "canal_id": canal.id,
            "canal_nome": canal.nome,
            "tipo": canal.tipo,
            "atendimentos_hoje": atendimentos_hoje,
            "atendimentos_ativos": atendimentos_ativos,
            "mensagens_enviadas_hoje": mensagens_enviadas,
            "mensagens_recebidas_hoje": mensagens_recebidas,
            "status": "ativo" if canal.ativo else "inativo"
        }

    def contar_canais_por_tipo(self, cliente_id: int) -> Dict[str, int]:
        """
        Conta canais ativos por tipo para faturamento.
        
        Args:
            cliente_id (int): ID do tenant
        
        Returns:
            Dict[str, int]: Contagem por tipo
        """
        resultados = self.db.query(
            Canal.tipo,
            func.count(Canal.id).label("quantidade")
        ).filter(
            Canal.cliente_id == cliente_id,
            Canal.ativo == True
        ).group_by(Canal.tipo).all()
        
        return {tipo: qtd for tipo, qtd in resultados}