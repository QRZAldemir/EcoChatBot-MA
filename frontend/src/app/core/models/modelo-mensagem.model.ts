export interface ModeloMensagem {
  id: number;
  descricao: string;
  corpo: string;
  arquivo?: string;
  departamentoId?: number;
  departamentoNome?: string;
  ativo: boolean;
  criadoEm?: string;
}
