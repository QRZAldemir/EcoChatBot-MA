// models/dashboard.model.ts
export interface Atendimento {
  id?: number;
  protocolo: string;
  nome: string;
  departamento: string;
  atendente: string;
  telefone?: string;
  dataCriacao: Date | string;
  dataFinalizacao?: Date | string;
  status: 'aberto' | 'finalizado' | 'aguardando';
  tipo: 'humano' | 'robo';
  observacao?: string;
  finalizadosSemAtendimento?: string;
  aguardandoAtendimento?: string;
  iniciadoPor?: string;
}

export interface AtendimentoStats {
  total: number;
  humanos: number;
  robos: number;
  emAberto: number;
  tma: number;  // Tempo Médio de Atendimento
  tme: number;  // Tempo Médio de Espera
}

export interface Avaliacao {
  id: number;
  atendimentoId: number;
  nota: number;
  departamento: string;
  data: Date;
  comentario?: string;
}

export interface FilterOptions {
  departamentos: { id: number; nome: string }[];
  atendentes: { id: number; nome: string }[];
  status: { id: string; nome: string }[];
}

export interface FilterValues {
  dataIni?: Date;
  dataFim?: Date;
  departamento?: string;
  atendente?: string;
  status?: string;
  search?: string;
  notaMin?: number;
  notaMax?: number;
}