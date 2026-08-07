export type StatusEmail = 'pendente' | 'enviado' | 'erro' | 'simulado';

export interface EmailEnviado {
  id: number;
  contatoId?: number;
  destinatario: string;
  assunto: string;
  corpo: string;
  status: StatusEmail;
  erroMensagem?: string;
  enviadoEm?: string;
  criadoEm: string;
}

export interface EmailEnviarDTO {
  destinatario: string;
  assunto: string;
  corpo: string;
  contatoId?: number;
}
