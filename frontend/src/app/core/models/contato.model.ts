export interface Contato {
  id: number;
  nome: string;
  telefone: string;
  email?: string;
  empresa?: string;
  observacao?: string;
  origem: string;         // manual | atendimento
  ativo: boolean;
  criadoEm?: string;
}
