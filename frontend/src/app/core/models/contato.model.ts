/**
 * EcoChatBot - Sistema de Atendimento
 * 
 * Arquivo: contato.model.ts
 * Descricao: Define as interfaces relacionadas aos contatos.
 * Este arquivo contem as estruturas de dados para gerenciamento de contatos
 * de clientes e destinatarios de mensagens.
 * 
 * Autor: Aldemir Querioz
 * Data: 2026-10-05
 * Versao: 2.0.0
 * 
 * NOTA IMPORTANTE:
 * - Contato = Dados de um cliente ou destinatario
 * - Um Contato pode estar em varias Campanhas (via CampanhaContatoItem)
 * - Um Contato pode ter varios Emails enviados (via EmailEnviado)
 * - Um Contato pode ter varios Atendimentos (via telefone)
 */

import { CampanhaContatoItem } from './campanha.model';

/**
 * Contato - Interface principal que representa um contato
 * 
 * RELACIONAMENTOS:
 * - CampanhaContatoItem: Atraves de campanhaContatoItem.contatoId (1:N) - Um contato pode estar em varias campanhas
 * - EmailEnviado: Atraves de emailEnviado.contatoId (1:N) - Um contato pode ter varios emails enviados
 * - Atendimento: Atraves de atendimento.telefone (N:N) - Contatos podem ser associados a atendimentos
 * 
 * DESCRICAO:
 * Representa um contato (cliente, destinatario) no sistema.
 * Contem informacoes basicas para identificacao e comunicacao.
 * 
 * DESCRICAO DOS CAMPOS:
 * - id: Identificador unico do contato (PK)
 * - nome: Nome do contato
 * - telefone: Telefone principal (formato: DDD + numero)
 * - email: Email do contato - opcional
 * - empresa: Empresa do contato - opcional
 * - observacao: Observacoes adicionais - opcional
 * - origem: Origem do contato ('manual' | 'atendimento')
 * - ativo: Indica se o contato esta ativo
 * - criadoEm: Data/hora de criacao (formato ISO) - opcional
 * 
 * ORIGENS POSSIVEIS:
 * - manual: Contato cadastrado manualmente
 * - atendimento: Contato criado a partir de um atendimento
 * 
 * USO NO PROJETO:
 * - Lista de contatos para envio de mensagens
 * - Destinatarios de campanhas
 * - Historico de comunicacao
 */
export interface Contato {
  id: number;
  nome: string;
  telefone: string;
  email?: string;
  empresa?: string;
  observacao?: string;
  origem: 'manual' | 'atendimento';  // Tipos de origem
  ativo: boolean;
  criadoEm?: string;
}

/**
 * MODELOS RELACIONADOS:
 * 
 * 1. CampanhaContatoItem (campanha.model.ts)
 *    - id: number (PK)
 *    - contatoId: number (FK)
 *    - status: string
 *    - contato?: Contato
 * 
 * 2. EmailEnviado (email.model.ts)
 *    - id: number (PK)
 *    - contatoId?: number (FK)
 *    - destinatario: string
 *    - ... outros campos
 * 
 * REGRAS DE NEGOCIO:
 * - Contato -> CampanhaContatoItem: 1:N (Um contato pode estar em varias campanhas)
 * - Contato -> EmailEnviado: 1:N (Um contato pode ter varios emails enviados)
 * - Contatos inativos (ativo: false) naorecebem mensagens
 * - O telefone e o campo principal para identificacao
 */
