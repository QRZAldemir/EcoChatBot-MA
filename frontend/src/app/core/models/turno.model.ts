export interface TurnoDia {
    ini: string;
    fim: string;
}

export type DiaSemana = 'dom' | 'seg' | 'ter' | 'qua' | 'qui' | 'sex' | 'sab';

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

export const DIAS_SEMANA: Array<{ key: DiaSemana; label: string }> = [
    { key: 'dom', label: 'Dom' },
    { key: 'seg', label: 'Seg' },
    { key: 'ter', label: 'Ter' },
    { key: 'qua', label: 'Qua' },
    { key: 'qui', label: 'Qui' },
    { key: 'sex', label: 'Sex' },
    { key: 'sab', label: 'Sáb' }
];
