/**
 * EcoChatBot - Sistema de Atendimento
 * 
 * Arquivo: canal.model.ts
 * Descricao: Define as interfaces para canais de comunicacao contratados.
 * Canal = Instancia de uma tecnologia de comunicacao que a empresa contratou.
 * 
 * NOTA IMPORTANTE:
 * - Canal = Instancia de uma TELEFONIA/TECNOLOGIA (WhatsApp, Telegram, Discord, PABX VOIP, etc.)
 * - Departamento = Area de negocio (Atendimento Geral, Vendas, Suporte, etc.)
 * - Uma empresa pode ter N canais do MESMO tipo (ex: 2 canais WhatsApp com numeros diferentes)
 * - Cada canal pertence a UM telefone (numero)
 * - Cada canal pode ter N conexoes ativas (ex: uma conexao WABA e uma QR Code para o mesmo WhatsApp)
 * 
 * Autor: Aldemir Querioz
 * Data: 2026-10-05
 * Versao: 2.0.0
 */

import { Departamento } from './departamento.model';
import { Menu } from './menu.model';
import { Atendimento } from './atendimento.model';

/**
 * TipoCanal - Tipos de meios de comunicacao disponiveis
 * 
 * MEIOS DE COMUNICACAO (TECNOLOGIAS):
 * - whatsapp: WhatsApp Business API ou WhatsApp Web
 * - telegram: Telegram Bot API
 * - email: Envio de emails via SMTP
 * - chat: Chat Web integrado
 * - discord: Discord Bot/Integration
 * - pabx_voip: PABX VOIP para chamadas telefonicas
 * 
 * NOTA: Estes sao os tipos de canais que a empresa pode contratar.
 * Uma empresa pode ter varios canais do mesmo tipo (ex: 2 WhatsApp).
 */
export type TipoCanal = 'whatsapp' | 'telegram' | 'email' | 'chat' | 'discord' | 'pabx_voip';

/**
 * StatusCanal - Estados possiveis de um canal
 * - ativo: Canal ativo e operacional
 * - inativo: Canal inativo
 * - teste: Canal em modo de teste
 * - suspenso: Canal suspenso temporariamente
 */
export type StatusCanal = 'ativo' | 'inativo' | 'teste' | 'suspenso';

/**
 * Canal - Interface principal que representa um canal de comunicacao contratado
 * 
 * RELACIONAMENTOS:
 * - Conexao: Atraves de conexoes (1:N) - Um canal pode ter varias conexoes ativas
 * - Departamento: Atraves de departamentoId (N:1) - Um canal pertence a UM departamento padrao
 * - Menu: Atraves de menus (1:N) - Um canal pode ter varios menus
 * - Atendimento: Atraves de atendimentos (1:N) - Um canal pode ter varios atendimentos
 * - Usuario: Atraves de usuarios (M:N viaUsuarioCanal) - Um canal pode ser usado por varios usuarios
 * - Campanha: Atraves de campanhas (N:N via Conexao) - Um canal pode ser usado em campanhas
 * 
 * DESCRICAO:
 * Representa um canal de comunicacao no sistema, que e uma instancia de uma
 * tecnologia de comunicacao que a empresa contratou (WhatsApp, Telegram, Email, etc.).
 * 
 * Cada canal:
 * - Tem um TIPO (tecnologia: whatsapp, telegram, etc.)
 * - Pode ter um ou mais NUMEROS DE TELEFONE associados
 * - Pertence a um DEPARTAMENTO padrao
 * - Pode ter varias CONEXOES ativas (ex: WABA + QR Code para o mesmo WhatsApp)
 * - Tem MENUS associados (opcoes apresentadas ao cliente)
 * - Recebe ATENDIMENTOS (conversas)
 * 
 * DESCRICAO DOS CAMPOS:
 * - id: Identificador unico do canal (PK)
 * - nome: Nome/apelido do canal (ex: "WhatsApp Comercial", "PABX Recepcao")
 * - descricao: Descricao do canal - opcional
 * - tipo: Tipo do canal (TipoCanal) - a tecnologia (whatsapp, telegram, discord, etc.)
 * - telefone: Numero de telefone associado - opcional (pode ser null para email/chat)
 * - departamentoId: FK para o departamento padrao - opcional
 * - departamentoNome: Nome do departamento associado - opcional
 * - status: Status do canal (StatusCanal)
 * - ativo: Indica se o canal esta ativo
 * - criadoEm: Data/hora de criacao (formato ISO) - opcional
 * 
 * EXEMPLOS:
 * - Canal 1: tipo=whatsapp, telefone=55-11-9999-9999, nome="WhatsApp Vendas"
 * - Canal 2: tipo=whatsapp, telefone=55-11-8888-8888, nome="WhatsApp Suporte"
 * - Canal 3: tipo=telegram, nome="Telegram Geral"
 * - Canal 4: tipo=pabx_voip, telefone=55-11-7777-7777, nome="PABX Central"
 * 
 * NOTA:
 * - Uma empresa pode ter MULTIPLOS canais do MESMO tipo (ex: 2 WhatsApp)
 * - Cada canal e identificado por seu tipo + telefone (quando aplicavel)
 * - O campo 'telefone' e opcional para canais como Email ou Chat Web
 */
export interface Canal {
  id: number;
  nome: string;  // Apelido do canal
  descricao?: string;
  tipo: TipoCanal;  // Tipo de tecnologia: whatsapp, telegram, discord, pabx_voip, etc.
  telefone?: string;  // Numero associado (opcional para email/chat)
  departamentoId?: Departamento['id'];
  departamentoNome?: string;
  status: StatusCanal;
  ativo: boolean;
  criadoEm?: string;
}

/**
 * MODELOS RELACIONADOS:
 * 
 * 1. Conexao (conexao.model.ts)
 *    - id: number (PK)
 *    - canalId: Canal['id'] (FK)
 *    - tipo: TipoConexao (waba, qrcode, api, webhook)
 *    - ... outros campos
 * 
 * 2. Departamento (departamento.model.ts)
 *    - id: number (PK)
 *    - nome: string
 *    - descricao?: string
 *    - status?: 'ativo' | 'inativo'
 * 
 * 3. Menu (menu.model.ts)
 *    - id: number (PK)
 *    - canalId: Canal['id'] (FK)
 *    - ... outros campos
 * 
 * 4. Atendimento (atendimento.model.ts)
 *    - id: number (PK)
 *    - canalId: Canal['id'] (FK)
 *    - ... outros campos
 * 
 * REGRAS DE NEGOCIO:
 * - Canal -> Conexao: 1:N (Um canal pode ter varias conexoes)
 * - Canal -> Departamento: N:1 (Um canal pertence a UM departamento padrao)
 * - Canal -> Menu: 1:N (Um canal pode ter varios menus)
 * - Canal -> Atendimento: 1:N (Um canal pode ter varios atendimentos)
 * - Canal -> Usuario: M:N (Um canal pode ser usado por varios usuarios)
 * - O campo 'tipo' determina a tecnologia do canal
 * - O campo 'telefone' e opcional para canais sem numero (email, chat)
 * - Uma empresa pode ter N canais do mesmo tipo (ex: 2 WhatsApp com numeros diferentes)
 */
