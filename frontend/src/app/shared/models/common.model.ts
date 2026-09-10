export interface SelectOption {
    id: number | string;
    nome: string;
}

export interface FiltroBase {
    search?: string;
    departamento?: string;
    atendente?: string;
    status?: string;
}
