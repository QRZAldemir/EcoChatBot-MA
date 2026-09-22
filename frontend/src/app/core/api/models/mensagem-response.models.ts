/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DepartamentoResponse } from './departamento-response.models';
export type ModeloMensagemResponse = {
    descricao: string;
    corpo: string;
    arquivo?: (string | null);
    departamento_id?: (number | null);
    ativo?: boolean;
    id: number;
    criado_em: string;
    departamento?: (DepartamentoResponse | null);
};

