/**
 * EcoChatBot - Sistema de Atendimento
 * 
 * Arquivo: conexao.model.ts
 * Descricao: Define as interfaces para conexoes ativas de canais.
 * Conexao = Instancia ativa de um canal (com credenciais, webhook, etc.).
 * 
 * Autor: Aldemir Querioz
 * Data: 2026-10-05
 * Versao: 2.0.0
 * 
 * NOTA:
 * - Canal = Instancia de uma tecnologia de comunicacao (whatsapp, telegram, etc.)
 * - Conexao = Instancia ativa de um canal (com credenciais para autenticacao)
 * - Uma empresa pode ter varios canais do mesmo tipo (ex: 2 WhatsApp)
 * - Cada canal pode ter varias conexoes ativas
 */

import { Canal } from './canal.model';
import { Usuario } from './usuario.model';

/**
 * TipoConexao - Tipos de conexao possiveis
 * - waba: WhatsApp Business API
 * - qrcode: Conexao via QR Code
 * - api: API generica
 * - webhook: Webhook generico
 */
export type TipoConexao = 'waba' | 'qrcode' | 'api' | 'webhook';

/**
 * StatusConexao - Estados possiveis de uma conexao
 * - conectada: Conexao ativa e operacional
 * - desconectada: Conexao inativa
 * - aguardando: Aguardando autenticacao ou configuracao
 * - erro: Conexao com erro
 */
export type StatusConexao = 'conectada' | 'desconectada' | 'aguardando' | 'erro';

/**
 * Conexao - Interface principal que representa uma conexao ativa de um canal
 * 
 * RELACIONAMENTOS:
 * - Canal: Atraves de canalId (N:1) - Uma conexao pertence a EXATAMENTE UM canal
 * - Campanha: Atraves de campanha.conexaoId (1:N) - Uma conexao pode ser usada por varias campanhas
 * - Usuario: Atraves de usuarios (M:N) - Uma conexao pode ser associada a varios usuarios
 * - Atendimento: Atraves de atendimentos (1:N) - Uma conexao pode ter varios atendimentos
 * 
 * DESCRICAO:
 * Representa uma conexao ativa com um servico externo de mensageria.
 * Contem credenciais, configuracoes de webhook e status de conexao.
 * Cada conexao pertence a um canal contratado e permite o envio/recebimento de mensagens.
 * 
 * DESCRICAO DOS CAMPOS:
 * - id: Identificador unico da conexao (PK)
 * - canalId: FK para o canal ao qual pertence (OBRIGATORIO)
 * - nome: Nome da conexao para identificacao
 * - tipo: Tipo de conexao (TipoConexao) - waba, qrcode, api, webhook
 * - credenciais: JSON com tokens/credenciais (ex: {"token": "...", "phone_id": "..."}) - opcional
 * - webhookToken: Token para validacao de webhook - opcional
 * - webhookUrl: URL do webhook para receber notificacoes - opcional
 * - status: Estado atual da conexao (StatusConexao)
 * - padrao: Indica se e a conexao padrao da empresa
 * - ativo: Indica se a conexao esta ativa
 * - fila: Quantidade de mensagens na fila de processamento
 * - criadoEm: Data/hora de criacao (formato ISO) - opcional
 * 
 * EXEMPLOS:
 * - Conexao 1: canalId=1 (WhatsApp), tipo='waba', credenciais={...}, status='conectada'
 * - Conexao 2: canalId=1 (WhatsApp), tipo='qrcode', qrcodeBase64='...', status='aguardando'
 * - Conexao 3: canalId=2 (Telegram), tipo='api', credenciais={...}, status='conectada'
 * 
 * NOTA IMPORTANTE:
 * - O campo 'telefone' foi MOVIDO para Canal (nao pertence a Conexao)
 * - O campo 'atendimento' (automatico/manual) foi MOVIDO para Canal (nao pertence a Conexao)
 * - O campo 'tipo' (whatsapp/telegram) foi MOVIDO para Canal (nao pertence a Conexao)
 */
export interface Conexao {
  id: number;
  canalId: Canal['id'];  // Canal ao qual pertence (OBRIGATORIO)
  nome: string;
  tipo: TipoConexao;  // Tipo de conexao: waba, qrcode, api, webhook
  credenciais?: string;  // JSON com tokens/credenciais - opcional
  webhookToken?: string;  // Token para validacao de webhook - opcional
  webhookUrl?: string;  // URL do webhook - opcional
  status: StatusConexao;
  padrao: boolean;  // Conexao padrao da empresa
  ativo: boolean;
  fila: number;  // Quantidade de mensagens na fila
  criadoEm?: string;
}

/**
 * ConexaoQRCode - Interface para conexoes que usam QR Code
 * 
 * RELACIONAMENTOS:
 * - Conexao: Extende a interface Conexao
 * 
 * DESCRICAO:
 * Representa os dados especificos para conexoes via QR Code.
 * Herda todos os campos de Conexao e adicona campos do QR Code.
 * 
 * DESCRICAO DOS CAMPOS:
 * - Herda todos os campos de Conexao
 * - qrcodeBase64: Imagem do QR Code em base64 - opcional
 * - pairingCode: Codigo de pareamento para autenticacao - opcional
 * - simulado: Indica se e uma conexao simulada (para testes)
 * - mensagem: Mensagem de status do QR Code - opcional
 * 
 * USO:
 * - Exibicao de QR Code para autenticacao
 * - Gerenciamento de conexoes via QR Code
 * - Pareamento de dispositivos
 */
export interface ConexaoQRCode extends Conexao {
  qrcodeBase64?: string;
  pairingCode?: string;
  simulado: boolean;
  mensagem?: string;
}

/**
 * MODELOS RELACIONADOS:
 * 
 * 1. Canal (canal.model.ts)
 *    - id: number (PK)
 *    - tipo: TipoCanal (whatsapp, telegram, discord, pabx_voip, etc.)
 *    - telefone?: string
 *    - departamentoId?: number
 *    - ... outros campos
 * 
 * 2. Campanha (campanha.model.ts)
 *    - id: number (PK)
 *    - conexaoId: number (FK para Conexao)
 *    - ... outros campos
 * 
 * 3. Usuario (usuario.model.ts)
 *    - id: number (PK)
 *    - conexoes: Conexao[] (relacionamento M:N)
 *    - ... outros campos
 * 
 * REGRAS DE NEGOCIO:
 * - Conexao -> Canal: N:1 (Uma conexao pertence a EXATAMENTE UM canal)
 * - Conexao -> Campanha: 1:N (Uma conexao pode ser usada por varias campanhas)
 * - Conexao -> Usuario: M:N (Varios usuarios podem usar uma conexao)
 * - Conexao -> Atendimento: 1:N (Uma conexao pode ter varios atendimentos)
 * - A conexao padrao (padrao: true) e a principal da empresa
 * - O status e atualizado automaticamente pelo sistema
 * - Cada conexao deve pertencer a um canal valido
 * - O campo 'credenciais' deve ser armazenado de forma segura
 */
