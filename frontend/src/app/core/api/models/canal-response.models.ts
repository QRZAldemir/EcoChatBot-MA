/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DepartamentoResponse } from './departamento-response.models';
export type CanalResponse = {
    nome: string;
    descricao?: (string | null);
    arquivo_menu: string;
    departamento_id?: (number | null);
    ativo?: boolean;
    id: number;
    criado_em: string;
    departamento?: (DepartamentoResponse | null);
};

