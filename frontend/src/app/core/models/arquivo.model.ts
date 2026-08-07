export interface Arquivo {
  id: number;
  nomeOriginal: string;
  tipoMime?: string;
  tamanhoBytes?: number;
  descricao?: string;
  atendimentoId?: number;
  criadoEm: string;
}
