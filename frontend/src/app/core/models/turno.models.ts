export interface TurnoDia {
  ini: string;
  fim: string;
}

export interface TurnoDias {
  dom: TurnoDia[];
  seg: TurnoDia[];
  ter: TurnoDia[];
  qua: TurnoDia[];
  qui: TurnoDia[];
  sex: TurnoDia[];
  sab: TurnoDia[];
}

export interface Turno {
  id: number;
  desc: string;
  dias: TurnoDias;
  acao: string;
  msgAndamento: string;
  msgEncerramento: string;
  status: 'ativo' | 'inativo';
}

export const DIAS_SEMANA = [
  { key: 'dom', label: 'Dom' },
  { key: 'seg', label: 'Seg' },
  { key: 'ter', label: 'Ter' },
  { key: 'qua', label: 'Qua' },
  { key: 'qui', label: 'Qui' },
  { key: 'sex', label: 'Sex' },
  { key: 'sab', label: 'Sáb' }
] as const;