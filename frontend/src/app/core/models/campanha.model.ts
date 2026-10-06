/**
 * EcoChatBot - Sistema de Atendimento
 * 
 * Arquivo: campanha.model.ts
 * Descricao: Define interfaces e tipos para campanhas de mensagens em massa.
 * 
 * FLUXO DE CAMPANHA:
 * 1. ADMIN cria campanha com Conexao (meio de comunicacao)
 * 2. Campanha envia mensagens para Contatos via Conexao
 * 3. Cada envio gera um CampanhaContatoItem
 * 4. Status de cada item e rastreado individualmente
 * 
 * Autor: Aldemir Querioz
 * Data: 2026-10-05
 * Versao: 2.0.0
 */

import { Contato } from './contato.model';
import { Conexao } from './conexao.model';

/**
 * StatusCampanha - Estados possiveis de uma campanha
 * - rascunho: Criada, nao iniciada
 * - enviando: Em processo de envio
 * - concluida: Finalizada com sucesso
 * - erro: Falhas que impedem conclusao
 */
export type StatusCampanha = 'rascunho' | 'enviando' | 'concluida' | 'erro';

/**
 * Campanha - Interface principal de campanha de mensagens
 * 
 * RELACIONAMENTOS:
 * - Conexao (via conexaoId): N:1 - Usa UMA conexao para envio
 * - CampanhaContatoItem: 1:N - Contem varios itens de contatos
 * - Contato: N:N - Envia para varios contatos
 * 
 * DESCRICAO:
 * Representa uma campanha de envio de mensagens em massa.
 * Cada campanha usa UMA conexao (de um canal) para enviar mensagens
 * para os contatos selecionados.
 * 
 * FLUXO:
 * 1. ADMIN seleciona Conexao (ex: Conexao 1 do Canal WhatsApp)
 * 2. ADMIN seleciona Contatos para a campanha
 * 3. Campanha e enviada via a Conexao
 * 4. Cada envio para um contato gera um CampanhaContatoItem
 * 5. Status de cada item e rastreado
 * 
 * CAMPOS:
 * - id: PK
 * - nome: Nome da campanha
 * - mensagem: Conteudo da mensagem a ser enviada
 * - conexaoId: FK para Conexao (OBRIGATORIO) - conexao usada para envio
 * - status: StatusCampanha - estado atual
 * - totalContatos: Total de contatos na campanha
 * - enviados: Quantidade de mensagens enviadas com sucesso
 * - falhas: Quantidade de mensagens com falha
 * - criadoEm: Data/hora de criacao (formato ISO)
 * - enviadoEm: Data/hora do inicio do envio (formato ISO, opcional)
 * 
 * NOTA:
 * - conexaoId aponta para Conexao, nao para Canal
 * - Uma Conexao pertence a um Canal (ex: Conexao 1 -> Canal WhatsApp)
 * - A Campanha usa a Conexao para enviar, nao o Canal diretamente
 */
export interface Campanha {
  id: number;
  nome: string;
  mensagem: string;
  conexaoId: Conexao['id'];  // FK para Conexao (OBRIGATORIO)
  status: StatusCampanha;
  totalContatos: number;
  enviados: number;
  falhas: number;
  criadoEm: string;
  enviadoEm?: string;
}

/**
 * CampanhaContatoItem - Item de contato em uma campanha
 * 
 * RELACIONAMENTOS:
 * - Campanha: Atraves de CampanhaDetalhe (N:1) - Pertence a uma campanha
 * - Contato: Atraves de contatoId (N:1) - Pertence a um contato
 * 
 * DESCRICAO:
 * Representa o status de envio de uma mensagem para um contato especifico
 * dentro de uma campanha.
 * 
 * CAMPOS:
 * - id: PK
 * - contatoId: FK para Contato (OBRIGATORIO)
 * - status: Status do envio ('pendente', 'enviado', 'falha', 'entregue', 'lida')
 * - erroMensagem: Descricao do erro caso status seja 'falha' - opcional
 * - enviadoEm: Data/hora do envio (formato ISO) - opcional
 * - contato: Objeto Contato embedado (opcional, populado quando necessario)
 */
export interface CampanhaContatoItem {
  id: number;
  contatoId: Contato['id'];  // FK para Contato (OBRIGATORIO)
  status: string;
  erroMensagem?: string;
  enviadoEm?: string;
  contato?: Contato;
}

/**
 * CampanhaDetalhe - Campanha completa com itens de contatos
 * Extende Campanha e adiciona array de CampanhaContatoItem
 */
export interface CampanhaDetalhe extends Campanha {
  contatos: CampanhaContatoItem[];
}

/**
 * CampanhaCreateDTO - DTO para criacao de campanha
 * 
 * RELACIONAMENTOS:
 * - Conexao (via conexaoId): Usa UMA conexao para envio
 * - Contato (via contatoIds): Envia para varios contatos
 * 
 * DESCRICAO:
 * DTO usado para criar uma nova campanha.
 * 
 * CAMPOS OBRIGATORIOS:
 * - nome: string (max 255 caracteres)
 * - mensagem: string (max 4000 caracteres)
 * - conexaoId: Conexao['id'] (OBRIGATORIO) - conexao usada para envio
 * - contatoIds: Contato['id'][] (OBRIGATORIO, minimo 1) - contatos para envio
 * 
 * ENDPOINT DE USO:
 * - POST /campanhas
 * - Body: CampanhaCreateDTO
 * - Response: Campanha (com id gerado)
 */
export interface CampanhaCreateDTO {
  nome: string;
  mensagem: string;
  conexaoId: Conexao['id'];  // Conexao usada para envio (OBRIGATORIO)
  contatoIds: Contato['id'][];  // Contatos para envio (OBRIGATORIO, minimo 1)
}

/**
 * MODELOS RELACIONADOS:
 * 
 * 1. Contato (contato.model.ts)
 *    - id: number (PK)
 *    - nome: string
 *    - telefone: string
 *    - email?: string
 *    - ... outros campos
 * 
 * 2. Conexao (conexao.model.ts)
 *    - id: number (PK)
 *    - canalId: Canal['id'] (FK)
 *    - tipo: TipoConexao (waba, qrcode, api, webhook)
 *    - ... outros campos
 * 
 * 3. Canal (canal.model.ts)
 *    - id: number (PK)
 *    - tipo: TipoCanal (whatsapp, telegram, discord, pabx_voip, etc.)
 *    - telefone?: string
 *    - ... outros campos
 * 
 * REGRAS DE NEGOCIO:
 * - Campanha -> Conexao: N:1 (Uma campanha usa UMA conexao)
 * - Campanha -> CampanhaContatoItem: 1:N (Uma campanha tem varios itens)
 * - CampanhaContatoItem -> Contato: N:1 (Cada item pertence a um contato)
 * - Conexao -> Campanha: 1:N (Uma conexao pode ser usada por varias campanhas)
 * - Contato -> Campanha: 1:N (Um contato pode estar em varias campanhas)
 * - A conexao deve pertencer a um canal ativo
 * - Os contatos devem ser validos e ativos
 */
