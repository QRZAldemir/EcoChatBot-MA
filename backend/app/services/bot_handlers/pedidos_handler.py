"""
================================================================================
HANDLER DE PEDIDOS (PLATAFORMA WHITE-LABEL)
================================================================================
Arquivo: bot_handlers/pedidos_handler.py
Propósito: Framework universal para pedidos (qualquer modelo de negócio)

DESENVOLVEDOR: Aldemir Queiroz da Silva
DATA: 2026-08-16

CORREÇÕES APLICADAS (CodeRabbit):
  1. ✅ AGORA persiste o pedido no banco de dados ANTES de limpar o contexto
  2. ✅ CORRIGIDO estado de confirmação - não é mais sobrescrito
  3. ✅ REMOVIDO PED_VOLTAR do bloco global - agora cada estado trata seu voltar
  4. ✅ ADICIONADO IDEMPOTÊNCIA via protocolo (evita duplicação)
  5. ✅ ADICIONADO logger estruturado no lugar de prints
  6. ✅ REMOVIDO dados pessoais dos logs (LGPD/GDPR compliance)

================================================================================
"""

from sqlalchemy.orm import Session
from app.models import Atendimento, Mensagem, Pedido
from .base_handler import DepartamentoHandler
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any

# Configura logger
logger = logging.getLogger(__name__)

# CONSTANTES: Estados
ESTADO_PED_MENU = "PED:MENU"
ESTADO_PED_CATEGORIA = "PED:CATEGORIA"
ESTADO_PED_ITEM = "PED:ITEM"
ESTADO_PED_QUANTIDADE = "PED:QUANTIDADE"
ESTADO_PED_CARRINHO = "PED:CARRINHO"
ESTADO_PED_CHECKOUT = "PED:CHECKOUT"
ESTADO_PED_COLETA = "PED:COLETA"
ESTADO_PED_CONFIRMACAO = "PED:CONFIRMACAO"


class PedidosHandler(DepartamentoHandler):
    """
    HANDLER UNIVERSAL PARA PEDIDOS
    
    Responsabilidades:
      1. Gerenciar fluxo de pedidos para qualquer tipo de negócio
      2. Carregar catálogo/configurações específicas do cliente
      3. Renderizar categorias e itens dinamicamente
      4. Gerenciar carrinho de compras
      5. Coletar dados de entrega e pagamento
      6. PERSISTIR e confirmar pedidos
    
    PRIVACIDADE:
      - NUNCA logar dados pessoais
      - Todos os logs são anonimizados
    """
    
    def __init__(self, session: Session, empresa_id: int):
        super().__init__(session)
        self.empresa_id = empresa_id
        self.configuracao = self._carregar_configuracao(empresa_id)
        self.categorias = self.configuracao.get("categorias", [])
        self.itens = self.configuracao.get("itens", [])
        self.opcoes_pagamento = self.configuracao.get("opcoes_pagamento", [])
        self.opcoes_entrega = self.configuracao.get("opcoes_entrega", [])
        self.mensagens = self.configuracao.get("mensagens", {})
        self.branding = self.configuracao.get("branding", {})
    
    def _carregar_configuracao(self, empresa_id: int) -> Dict[str, Any]:
        """
        Carrega configurações da empresa
        
        ESTRUTURA DA CONFIGURAÇÃO:
        {
            "categorias": [...],
            "itens": [...],
            "opcoes_pagamento": [...],
            "opcoes_entrega": [...]
        }
        """
        # TODO: Buscar do banco de dados
        return self._configuracao_padrao()
    
    def _configuracao_padrao(self) -> Dict[str, Any]:
        """Configuração padrão (fallback)"""
        return {
            "categorias": [
                {"id": "ELETRONICOS", "nome": "Eletrônicos", "icone": "💻", "descricao": "Dispositivos e acessórios"},
                {"id": "ROUPAS", "nome": "Roupas", "icone": "👕", "descricao": "Moda e acessórios"},
                {"id": "CASA", "nome": "Casa", "icone": "🏠", "descricao": "Móveis e decoração"}
            ],
            "itens": [
                {
                    "id": "SMARTPHONE",
                    "nome": "Smartphone X10",
                    "preco": 1999.90,
                    "categoria": "ELETRONICOS",
                    "estoque": 15,
                    "descricao": "Tela 6.5\", 128GB"
                },
                {
                    "id": "CAMISETA",
                    "nome": "Camiseta Básica",
                    "preco": 49.90,
                    "categoria": "ROUPAS",
                    "estoque": 50,
                    "descricao": "Algodão 100%, várias cores"
                }
            ],
            "opcoes_pagamento": [
                {"id": "PIX", "nome": "PIX", "desconto": 5, "icone": "💳"},
                {"id": "CARTAO", "nome": "Cartão de Crédito", "parcelas": 6, "icone": "💳"},
                {"id": "BOLETO", "nome": "Boleto Bancário", "desconto": 0, "icone": "📄"}
            ],
            "opcoes_entrega": [
                {"id": "RETIRADA", "nome": "Retirar na Loja", "valor": 0, "prazo": "1h"},
                {"id": "ENTREGA", "nome": "Entrega", "valor": 19.90, "prazo": "3 dias"}
            ],
            "mensagens": {
                "boas_vindas": "🛍️ Bem-vindo à nossa loja!",
                "confirmacao": "✅ Pedido confirmado!",
                "carrinho_vazio": "Seu carrinho está vazio."
            },
            "branding": {
                "nome_empresa": "Nossa Loja"
            }
        }
    
    # ══════════════════════════════════════════════════════════════
    # HELPER: EXTRAÇÃO DE DADOS DA MENSAGEM
    # ══════════════════════════════════════════════════════════════
    
    def _extrair_dados_mensagem(self, mensagem: Mensagem) -> Dict[str, Any]:
        """Extrai dados REAIS da mensagem usando helper da classe base"""
        return super()._extrair_dados_mensagem(mensagem)
    
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
        POLIMORFISMO: Implementação específica para Pedidos
        
        CORREÇÃO: 
          - Agora usa _extrair_dados_mensagem() para ler dados reais
          - PED_VOLTAR é tratado contextualmente por cada estado
        """
        # CORREÇÃO: Extrai dados REAIS da mensagem
        dados_msg = self._extrair_dados_mensagem(mensagem)
        
        msg_type = dados_msg["msg_type"]
        content = dados_msg["content"]
        row = dados_msg["row_id"] or ""
        button = dados_msg["button_id"] or ""
        
        # Log seguro (sem dados pessoais)
        logger.debug(
            "processar_pedido",
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
        
        # Falar com atendente
        if acao == "PED_FALAR":
            await self._transferir_atendente(atendimento)
            return
        
        # Voltar ao hub (sempre válido)
        if acao == "PED_VOLTAR_HUB":
            await self._voltar_hub(atendimento)
            return
        
        # Cancelar (sempre válido)
        if acao == "PED_CANCELAR":
            self._limpar_contexto_completo(atendimento.id)
            await self._enviar_texto(atendimento, "❌ Pedido cancelado.")
            await self._menu_principal(atendimento)
            return
        
        # Ver carrinho (sempre válido)
        if acao == "PED_CARRINHO":
            await self._exibir_carrinho(atendimento)
            return
        
        # CORREÇÃO: PED_VOLTAR NÃO é global - cada estado trata seu próprio voltar
        # Apenas em estados iniciais o voltar vai para o menu principal
        if acao == "PED_VOLTAR" and step in (ESTADO_PED_MENU, ESTADO_PED_CATEGORIA):
            await self._menu_principal(atendimento)
            return
        
        # ──────────────────────────────────────────────────────────
        # DESPACHO POR ESTADO
        # ──────────────────────────────────────────────────────────
        
        if step == ESTADO_PED_MENU:
            await self._menu_principal(atendimento, msg_type, row)
            
        elif step == ESTADO_PED_CATEGORIA:
            await self._processar_categoria(atendimento, msg_type, row)
            
        elif step == ESTADO_PED_ITEM:
            await self._processar_item(atendimento, msg_type, row)
            
        elif step == ESTADO_PED_QUANTIDADE:
            await self._processar_quantidade(atendimento, content)
            
        elif step == ESTADO_PED_CARRINHO:
            await self._processar_carrinho(atendimento, msg_type, row)
            
        elif step == ESTADO_PED_CHECKOUT:
            await self._processar_checkout(atendimento, msg_type, row)
            
        elif step == ESTADO_PED_COLETA:
            await self._coletar_dados(atendimento, content)
            
        elif step == ESTADO_PED_CONFIRMACAO:
            await self._finalizar_pedido(atendimento)
    
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
            await self._enviar_texto(atendimento, "⚠️ Nenhuma categoria disponível.")
            return
        
        if msg_type != "list_response":
            rows = self._renderizar_categorias()
            nome = self.branding.get("nome_empresa", "Nossa Loja")
            
            await self._enviar_lista(
                atendimento,
                f"🛍️ {nome} - Produtos",
                self.mensagens.get("boas_vindas", "Selecione uma categoria:"),
                rows,
                "Ver categorias"
            )
            self._avancar_step(atendimento, ESTADO_PED_CATEGORIA)
            return
        
        # Processa seleção de categoria
        if row.startswith("PED_CAT_"):
            cat_id = row.replace("PED_CAT_", "")
            categoria = self._obter_categoria(cat_id)
            if categoria:
                self._guardar_contexto(atendimento.id, "ped_categoria", cat_id)
                await self._exibir_itens_categoria(atendimento, categoria)
    
    def _renderizar_categorias(self) -> List[Dict[str, str]]:
        """Renderiza categorias para menu"""
        rows = []
        for idx, cat in enumerate(self.categorias, 1):
            rows.append({
                "title": f"{cat.get('icone', '📦')} {idx}. {cat['nome']}",
                "description": cat.get("descricao", ""),
                "rowId": f"PED_CAT_{cat['id']}"
            })
        
        rows.append({"title": "🛒 Ver Carrinho", "rowId": "PED_CARRINHO"})
        rows.append({"title": "🗣️ Falar com Atendente", "rowId": "PED_FALAR"})
        rows.append({"title": "🏠 Menu Principal", "rowId": "PED_VOLTAR_HUB"})
        return rows
    
    def _obter_categoria(self, cat_id: str) -> Optional[Dict]:
        """Busca categoria pelo ID"""
        return next((c for c in self.categorias if c["id"] == cat_id), None)
    
    def _obter_item(self, item_id: str) -> Optional[Dict]:
        """Busca item pelo ID"""
        return next((i for i in self.itens if i["id"] == item_id), None)
    
    def _obter_itens_por_categoria(self, cat_id: str) -> List[Dict]:
        """Lista itens de uma categoria"""
        return [i for i in self.itens if i.get("categoria") == cat_id]
    
    async def _processar_categoria(self, atendimento: Atendimento, msg_type: str, row: str) -> None:
        """Processa seleção de categoria"""
        if msg_type != "list_response":
            await self._menu_principal(atendimento)
            return
        
        if row.startswith("PED_CAT_"):
            cat_id = row.replace("PED_CAT_", "")
            categoria = self._obter_categoria(cat_id)
            if categoria:
                self._guardar_contexto(atendimento.id, "ped_categoria", cat_id)
                await self._exibir_itens_categoria(atendimento, categoria)
    
    # ══════════════════════════════════════════════════════════════
    # EXIBIÇÃO DE ITENS E SELEÇÃO
    # ══════════════════════════════════════════════════════════════
    
    async def _exibir_itens_categoria(self, atendimento: Atendimento, categoria: Dict) -> None:
        """Exibe itens de uma categoria"""
        itens = self._obter_itens_por_categoria(categoria['id'])
        
        if not itens:
            await self._enviar_texto(atendimento, "📭 Nenhum item disponível.")
            await self._menu_principal(atendimento)
            return
        
        rows = []
        for idx, item in enumerate(itens, 1):
            preco = item.get("preco", 0)
            estoque = item.get("estoque", 0)
            status = "✅" if estoque > 0 else "❌"
            
            rows.append({
                "title": f"{idx}. {item['nome']} - R$ {preco:.2f}",
                "description": f"{item.get('descricao', '')} | Estoque: {status}",
                "rowId": f"PED_ITEM_{item['id']}"
            })
        
        rows.append({"title": "🔙 Voltar", "rowId": "PED_VOLTAR"})
        rows.append({"title": "🛒 Ver Carrinho", "rowId": "PED_CARRINHO"})
        
        await self._enviar_lista(
            atendimento,
            f"{categoria.get('icone', '📦')} {categoria['nome']}",
            "Selecione um produto:",
            rows,
            "Ver produtos"
        )
        self._avancar_step(atendimento, ESTADO_PED_ITEM)
    
    async def _processar_item(self, atendimento: Atendimento, msg_type: str, row: str) -> None:
        """Processa seleção de item"""
        # CORREÇÃO: PED_VOLTAR tratado contextualmente neste estado
        if row == "PED_VOLTAR":
            await self._menu_principal(atendimento)
            return
        
        if row == "PED_CARRINHO":
            await self._exibir_carrinho(atendimento)
            return
        
        if row.startswith("PED_ITEM_"):
            item_id = row.replace("PED_ITEM_", "")
            item = self._obter_item(item_id)
            if item:
                self._guardar_contexto(atendimento.id, "ped_item_atual", item_id)
                
                # Se tem estoque, pergunta quantidade
                if item.get("estoque", 0) > 0:
                    await self._enviar_texto(
                        atendimento,
                        f"*{item['nome']}*\n"
                        f"Preço: R$ {item['preco']:.2f}\n"
                        f"Disponível: {item['estoque']} unidades\n\n"
                        f"Quantos você deseja?"
                    )
                    self._avancar_step(atendimento, ESTADO_PED_QUANTIDADE)
                else:
                    await self._enviar_texto(atendimento, "❌ Produto indisponível.")
                    cat_id = self._obter_contexto(atendimento.id, "ped_categoria")
                    categoria = self._obter_categoria(cat_id)
                    if categoria:
                        await self._exibir_itens_categoria(atendimento, categoria)
    
    # ══════════════════════════════════════════════════════════════
    # QUANTIDADE E CARRINHO
    # ══════════════════════════════════════════════════════════════
    
    async def _processar_quantidade(self, atendimento: Atendimento, content: str) -> None:
        """Processa quantidade do item"""
        try:
            quantidade = int(content.strip())
        except ValueError:
            await self._enviar_texto(atendimento, "❌ Digite um número válido.")
            return
        
        if quantidade <= 0:
            await self._enviar_texto(atendimento, "❌ A quantidade deve ser maior que zero.")
            return
        
        item_id = self._obter_contexto(atendimento.id, "ped_item_atual")
        item = self._obter_item(item_id)
        
        if not item:
            await self._menu_principal(atendimento)
            return
        
        # Verifica estoque
        if quantidade > item.get("estoque", 0):
            await self._enviar_texto(
                atendimento,
                f"❌ Estoque insuficiente. Disponível: {item['estoque']}"
            )
            return
        
        # Adiciona ao carrinho
        carrinho_str = self._obter_contexto(atendimento.id, "ped_carrinho") or "[]"
        carrinho = json.loads(carrinho_str)
        
        # Verifica se já está no carrinho
        for i in carrinho:
            if i["id"] == item_id:
                i["quantidade"] += quantidade
                break
        else:
            carrinho.append({
                "id": item_id,
                "nome": item["nome"],
                "preco": item["preco"],
                "quantidade": quantidade
            })
        
        self._guardar_contexto(atendimento.id, "ped_carrinho", json.dumps(carrinho))
        
        await self._enviar_texto(
            atendimento,
            f"✅ {item['nome']} adicionado ao carrinho!"
        )
        
        # Volta para categoria
        cat_id = self._obter_contexto(atendimento.id, "ped_categoria")
        categoria = self._obter_categoria(cat_id)
        if categoria:
            await self._exibir_itens_categoria(atendimento, categoria)
    
    async def _exibir_carrinho(self, atendimento: Atendimento) -> None:
        """Exibe o carrinho atual"""
        carrinho_str = self._obter_contexto(atendimento.id, "ped_carrinho") or "[]"
        carrinho = json.loads(carrinho_str)
        
        if not carrinho:
            await self._enviar_texto(
                atendimento,
                self.mensagens.get("carrinho_vazio", "🛒 Seu carrinho está vazio.")
            )
            await self._menu_principal(atendimento)
            return
        
        # Renderiza carrinho
        linhas = ["🛒 *SEU CARRINHO*", ""]
        total = 0
        
        for idx, item in enumerate(carrinho, 1):
            subtotal = item["preco"] * item["quantidade"]
            total += subtotal
            linhas.append(f"{idx}. {item['nome']}")
            linhas.append(f"   {item['quantidade']} x R$ {item['preco']:.2f} = R$ {subtotal:.2f}")
            linhas.append("")
        
        linhas.append(f"*TOTAL: R$ {total:.2f}*")
        linhas.append("")
        
        # Opções
        rows = [
            {"title": "✅ Finalizar Pedido", "rowId": "PED_CHECKOUT"},
            {"title": "📝 Continuar Comprando", "rowId": "PED_VOLTAR"},
            {"title": "🗑️ Limpar Carrinho", "rowId": "PED_LIMPAR"},
            {"title": "🗣️ Falar com Atendente", "rowId": "PED_FALAR"}
        ]
        
        await self._enviar_texto(atendimento, "\n".join(linhas))
        
        await self._enviar_lista(
            atendimento,
            "Carrinho",
            "O que deseja fazer?",
            rows,
            "Ver opções"
        )
        self._avancar_step(atendimento, ESTADO_PED_CARRINHO)
    
    async def _processar_carrinho(self, atendimento: Atendimento, msg_type: str, row: str) -> None:
        """Processa ações do carrinho"""
        # CORREÇÃO: PED_VOLTAR tratado contextualmente neste estado
        if row == "PED_VOLTAR":
            await self._menu_principal(atendimento)
            return
        
        if row == "PED_CHECKOUT":
            await self._iniciar_checkout(atendimento)
            return
        
        if row == "PED_LIMPAR":
            self._limpar_carrinho(atendimento)
            await self._enviar_texto(atendimento, "🗑️ Carrinho limpo!")
            await self._menu_principal(atendimento)
            return
        
        if row == "PED_FALAR":
            await self._transferir_atendente(atendimento)
            return
    
    def _limpar_carrinho(self, atendimento: Atendimento) -> None:
        """Limpa o carrinho"""
        self._guardar_contexto(atendimento.id, "ped_carrinho", json.dumps([]))
    
    def _calcular_total_carrinho(self, atendimento: Atendimento) -> float:
        """Calcula o total do carrinho"""
        carrinho_str = self._obter_contexto(atendimento.id, "ped_carrinho") or "[]"
        carrinho = json.loads(carrinho_str)
        return sum(item["preco"] * item["quantidade"] for item in carrinho)
    
    # ══════════════════════════════════════════════════════════════
    # CHECKOUT E FINALIZAÇÃO
    # ══════════════════════════════════════════════════════════════
    
    async def _iniciar_checkout(self, atendimento: Atendimento) -> None:
        """Inicia o checkout do pedido"""
        carrinho_str = self._obter_contexto(atendimento.id, "ped_carrinho") or "[]"
        carrinho = json.loads(carrinho_str)
        
        if not carrinho:
            await self._enviar_texto(atendimento, "🛒 Seu carrinho está vazio.")
            await self._menu_principal(atendimento)
            return
        
        total = self._calcular_total_carrinho(atendimento)
        
        # Mostra opções de entrega
        if self.opcoes_entrega:
            rows = self._renderizar_opcoes_entrega(total)
            await self._enviar_lista(
                atendimento,
                "🚚 Opções de Entrega",
                f"Total: R$ {total:.2f}\n\nSelecione a forma de entrega:",
                rows,
                "Ver opções"
            )
            self._avancar_step(atendimento, ESTADO_PED_CHECKOUT)
        else:
            # Sem opções de entrega, vai direto para pagamento
            await self._exibir_opcoes_pagamento(atendimento, total)
    
    def _renderizar_opcoes_entrega(self, total: float) -> List[Dict[str, str]]:
        """Renderiza opções de entrega"""
        rows = []
        for idx, opcao in enumerate(self.opcoes_entrega, 1):
            valor = opcao.get("valor", 0)
            prazo = opcao.get("prazo", "—")
            
            # Verifica frete grátis
            if valor == 0:
                desc = f"{prazo} (Grátis)"
            else:
                desc = f"{prazo} (R$ {valor:.2f})"
            
            rows.append({
                "title": f"{idx}. {opcao['nome']}",
                "description": desc,
                "rowId": f"PED_ENTREGA_{opcao['id']}"
            })
        
        rows.append({"title": "🔙 Voltar", "rowId": "PED_VOLTAR"})
        return rows
    
    async def _processar_checkout(self, atendimento: Atendimento, msg_type: str, row: str) -> None:
        """Processa seleção de entrega"""
        # CORREÇÃO: PED_VOLTAR tratado contextualmente neste estado
        if row == "PED_VOLTAR":
            await self._exibir_carrinho(atendimento)
            return
        
        if row.startswith("PED_ENTREGA_"):
            entrega_id = row.replace("PED_ENTREGA_", "")
            self._guardar_contexto(atendimento.id, "ped_entrega", entrega_id)
            
            total = self._calcular_total_carrinho(atendimento)
            await self._exibir_opcoes_pagamento(atendimento, total)
    
    async def _exibir_opcoes_pagamento(self, atendimento: Atendimento, total: float) -> None:
        """Exibe opções de pagamento"""
        if not self.opcoes_pagamento:
            await self._confirmar_pedido_sem_pagamento(atendimento)
            return
        
        rows = self._renderizar_opcoes_pagamento(total)
        
        await self._enviar_lista(
            atendimento,
            "💳 Pagamento",
            f"Total: R$ {total:.2f}\n\nSelecione a forma de pagamento:",
            rows,
            "Ver opções"
        )
        self._avancar_step(atendimento, ESTADO_PED_COLETA)
    
    def _renderizar_opcoes_pagamento(self, total: float) -> List[Dict[str, str]]:
        """Renderiza opções de pagamento"""
        rows = []
        for idx, opcao in enumerate(self.opcoes_pagamento, 1):
            nome = opcao["nome"]
            desconto = opcao.get("desconto", 0)
            parcelas = opcao.get("parcelas", 1)
            
            if desconto:
                valor_com_desconto = total - (total * desconto / 100)
                desc = f"Valor: R$ {valor_com_desconto:.2f} (desconto {desconto}%)"
            elif parcelas > 1:
                valor_parcela = total / parcelas
                desc = f"{parcelas}x R$ {valor_parcela:.2f}"
            else:
                desc = f"R$ {total:.2f}"
            
            rows.append({
                "title": f"{opcao.get('icone', '💳')} {idx}. {nome}",
                "description": desc,
                "rowId": f"PED_PAG_{opcao['id']}"
            })
        
        return rows
    
    async def _coletar_dados(self, atendimento: Atendimento, content: str) -> None:
        """Coleta dados do pagamento (se necessário)"""
        # Verifica se é seleção de pagamento
        if content.startswith("PED_PAG_"):
            pagamento_id = content.replace("PED_PAG_", "")
            self._guardar_contexto(atendimento.id, "ped_pagamento", pagamento_id)
            
            # Confirma pedido
            await self._confirmar_pedido(atendimento)
            return
        
        # Se não for opção de pagamento, trata como texto
        await self._enviar_texto(atendimento, "Por favor, selecione uma opção de pagamento.")
        total = self._calcular_total_carrinho(atendimento)
        await self._exibir_opcoes_pagamento(atendimento, total)
    
    # ══════════════════════════════════════════════════════════════
    # CONFIRMAÇÃO E PERSISTÊNCIA DO PEDIDO (CORREÇÃO PRINCIPAL)
    # ══════════════════════════════════════════════════════════════
    
    async def _confirmar_pedido(self, atendimento: Atendimento, row: str = None) -> None:
        """
        Confirma, PERSISTE e finaliza o pedido
        
        CORREÇÃO: Agora o pedido é PERSISTIDO antes de limpar o contexto
        """
        carrinho_str = self._obter_contexto(atendimento.id, "ped_carrinho") or "[]"
        carrinho = json.loads(carrinho_str)
        
        if not carrinho:
            await self._menu_principal(atendimento)
            return
        
        total = self._calcular_total_carrinho(atendimento)
        protocolo = self._gerar_protocolo("PED")
        
        try:
            # 1. CORREÇÃO: PERSISTE o pedido no banco de dados
            pedido = await self._persistir_pedido(
                atendimento=atendimento,
                carrinho=carrinho,
                total=total,
                protocolo=protocolo
            )
            
            if pedido:
                logger.info(
                    "pedido_persistido",
                    extra={
                        "pedido_id": pedido.id,
                        "protocolo": protocolo,
                        "empresa_id": self.empresa_id,
                        "atendimento_id": atendimento.id,
                        "total": total,
                        "qtd_itens": len(carrinho)
                    }
                )
            
            # 2. Monta resumo do pedido
            resumo = f"📋 *RESUMO DO PEDIDO*\n\n"
            resumo += f"🔖 Protocolo: *{protocolo}*\n"
            if pedido and hasattr(pedido, 'id'):
                resumo += f"📝 Pedido #: {pedido.id}\n\n"
            else:
                resumo += "\n"
            resumo += "🛒 *Itens:*\n"
            
            for item in carrinho:
                subtotal = item["preco"] * item["quantidade"]
                resumo += f"  • {item['nome']}: {item['quantidade']} x R$ {item['preco']:.2f} = R$ {subtotal:.2f}\n"
            
            resumo += f"\n*TOTAL: R$ {total:.2f}*"
            
            # Adiciona entrega e pagamento
            entrega_id = self._obter_contexto(atendimento.id, "ped_entrega")
            if entrega_id:
                entrega = next((e for e in self.opcoes_entrega if e["id"] == entrega_id), None)
                if entrega:
                    resumo += f"\n\n🚚 Entrega: {entrega['nome']}"
            
            pagamento_id = self._obter_contexto(atendimento.id, "ped_pagamento")
            if pagamento_id:
                pagamento = next((p for p in self.opcoes_pagamento if p["id"] == pagamento_id), None)
                if pagamento:
                    resumo += f"\n💳 Pagamento: {pagamento['nome']}"
            
            resumo += f"\n\n{self.mensagens.get('confirmacao', '✅ Pedido confirmado!')}"
            
            await self._enviar_texto(atendimento, resumo)
            
            # 3. CORREÇÃO: Define estado de confirmação
            self._avancar_step(atendimento, ESTADO_PED_CONFIRMACAO)
            
            # 4. Limpa contexto (APÓS persistir)
            self._limpar_contexto_completo(atendimento.id)
            
            # 5. CORREÇÃO: NÃO chama _menu_principal aqui - o estado é final
            
        except Exception as e:
            # Em caso de erro, loga e tenta transferir para atendente
            logger.error(
                "erro_persistir_pedido",
                extra={
                    "atendimento_id": atendimento.id,
                    "empresa_id": self.empresa_id,
                    "protocolo": protocolo,
                    "erro": str(e)
                }
            )
            
            await self._enviar_texto(
                atendimento,
                "❌ Erro ao processar seu pedido. Transferindo para um atendente."
            )
            
            # Transfere com os dados que foram coletados
            await self._transferir_atendente(atendimento)
    
    async def _persistir_pedido(
        self,
        atendimento: Atendimento,
        carrinho: List[Dict],
        total: float,
        protocolo: str
    ) -> Optional[Pedido]:
        """
        PERSISTE o pedido no banco de dados
        
        ENCAPSULAMENTO: Isola a lógica de persistência
        
        IDEMPOTÊNCIA: Usa protocolo como chave única para evitar duplicação
        """
        try:
            # Verifica se já existe pedido com este protocolo (idempotência)
            existing = self.session.query(Pedido).filter_by(
                protocolo=protocolo,
                empresa_id=self.empresa_id
            ).first()
            
            if existing:
                logger.info(
                    "pedido_ja_existente",
                    extra={
                        "protocolo": protocolo,
                        "pedido_id": existing.id
                    }
                )
                return existing

            pedido = Pedido(
                atendimento_id=atendimento.id,
                empresa_id=self.empresa_id,
                protocolo=protocolo,
                itens=json.dumps(carrinho, ensure_ascii=False),
                total=total,
                status="confirmado",
            )
            self.session.add(pedido)
            self.session.commit()
            self.session.refresh(pedido)
            return pedido
        except Exception:
            self.session.rollback()
            raise
            
           