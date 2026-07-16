export type StatusAtendimento = 'aberto' | 'fila' | 'em_atendimento' | 'finalizado';

export interface Atendimento {
  id: number;
  protocolo: string;
  telefone?: string;
  nomeContato?: string;
  status: StatusAtendimento;
  departamentoId?: number;
  canalId?: number;
  usuarioId?: number;
  criadoEm?: string;
  atualizadoEm?: string;
}

export interface FiltroAtendimento {
  // canal_id não é filtrável em GET /atendimento/listar (o backend só filtra
  // "canal" = tipo_canal 1/2 nesse endpoint) — por isso não existe aqui.
  departamentoId?: number;
  atendenteUsuarioId?: number;
  status?: StatusAtendimento;
  dataCriacaoInicio?: string; // formato AAAA-MM-DD
  dataCriacaoFim?: string;    // formato AAAA-MM-DD
  limit?: number;
  page?: number;
}
