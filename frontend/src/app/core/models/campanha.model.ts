import { Contato } from './contato.model';

export type StatusCampanha = 'rascunho' | 'enviando' | 'concluida' | 'erro';

export interface Campanha {
  id: number;
  nome: string;
  mensagem: string;
  conexaoId: number;
  status: StatusCampanha;
  totalContatos: number;
  enviados: number;
  falhas: number;
  criadoEm: string;
  enviadoEm?: string;
}

export interface CampanhaContatoItem {
  id: number;
  contatoId: number;
  status: string;
  erroMensagem?: string;
  enviadoEm?: string;
  contato?: Contato;
}

export interface CampanhaDetalhe extends Campanha {
  contatos: CampanhaContatoItem[];
}

export interface CampanhaCreateDTO {
  nome: string;
  mensagem: string;
  conexaoId: number;
  contatoIds: number[];
}
