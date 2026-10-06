/**
 * EcoChatBot - Sistema de Atendimento
 * 
 * Arquivo: email.model.ts
 * Descricao: Define as interfaces relacionadas ao envio de emails.
 * Este arquivo contem as estruturas de dados para gerenciamento de emails
 * enviados pelo sistema, incluindo status e rastreamento.
 * 
 * Autor: Aldemir Querioz
 * Data: 2026-10-05
 * Versao: 2.0.0
 */

import { Contato } from './contato.model';

/**
 * StatusEmail - Estados possiveis de um email
 * - pendente: Email aguardando envio
 * - enviado: Email enviado com sucesso
 * - erro: Email com falha no envio
 * - simulado: Email de teste/simulacao
 */
export type StatusEmail = 'pendente' | 'enviado' | 'erro' | 'simulado';

/**
 * EmailEnviado - Interface que representa um email ja enviado ou em processamento
 * 
 * RELACIONAMENTOS:
 * - Contato: Atraves de contatoId (N:1) - Um email pode ser associado a um contato
 * 
 * DESCRICAO:
 * Representa um email que foi ou sera enviado pelo sistema.
 * Contem todas as informacoes necessarias para rastreamento e audit.
 * 
 * DESCRICAO DOS CAMPOS:
 * - id: Identificador unico do email (PK)
 * - contatoId: FK para o contato destino - opcional
 * - destinatario: Email do destinatario
 * - assunto: Assunto do email
 * - corpo: Conteudo do email (HTML ou texto)
 * - status: Estado atual do email (StatusEmail)
 * - erroMensagem: Descricao do erro caso status seja 'erro' - opcional
 * - enviadoEm: Data/hora do envio (formato ISO) - opcional
 * - criadoEm: Data/hora da criacao (formato ISO)
 * 
 * USO NO PROJETO:
 * - Historico de emails enviados
 * - Rastreamento de status de envio
 * - Auditoria de comunicacoes
 */
export interface EmailEnviado {
  id: number;
  contatoId?: Contato['id'];
  destinatario: string;
  assunto: string;
  corpo: string;
  status: StatusEmail;
  erroMensagem?: string;
  enviadoEm?: string;
  criadoEm: string;
}

/**
 * EmailEnviarDTO - Data Transfer Object para envio de email
 * 
 * RELACIONAMENTOS:
 * - Contato: Atraves de contatoId (opcional) - Pode ser associado a um contato
 * 
 * DESCRICAO:
 * DTO usado para enviar emails pelo sistema.
 * Contem os campos minimos necessarios para o envio.
 * 
 * DESCRICAO DOS CAMPOS:
 * - destinatario: Email do destinatario (obrigatorio)
 * - assunto: Assunto do email (obrigatorio)
 * - corpo: Conteudo do email (obrigatorio)
 * - contatoId: ID do contato associado - opcional
 * 
 * VALIDACOES:
 * - destinatario: Formato de email valido
 * - assunto: String nao vazia
 * - corpo: String nao vazia
 * 
 * ENDPOINT DE USO:
 * - POST /emails
 * - Body: EmailEnviarDTO
 * - Response: EmailEnviado (com id gerado)
 */
export interface EmailEnviarDTO {
  destinatario: string;
  assunto: string;
  corpo: string;
  contatoId?: Contato['id'];
}

/**
 * MODELOS RELACIONADOS:
 * 
 * 1. Contato (contato.model.ts)
 *    - id: number (PK)
 *    - nome: string
 *    - email?: string
 *    - ... outros campos
 * 
 * REGRAS DE NEGOCIO:
 * - EmailEnviado -> Contato: N:1 (Varios emails podem ser para um contato)
 * - EmailEnviarDTO -> Contato: N:1 (opcional)
 * - Emails em status 'erro' podem ser reenviados
 * - O destinatario deve ser um email valido
 */
