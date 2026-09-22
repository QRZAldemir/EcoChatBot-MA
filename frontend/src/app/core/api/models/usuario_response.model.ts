/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CanalResponse } from './canal-response.models';
import type { DepartamentoResponse } from './departamento-response.models';
import type { NivelUsuarioResponse } from './nivel-usuario-response.models';
export type UsuarioResponse = {
    nome: string;
    email: string;
    telefone?: (string | null);
    nivel_id: number;
    departamento_id?: (number | null);
    canal_id?: (number | null);
    ativo?: boolean;
    id: number;
    criado_em: string;
    atualizado_em: string;
    nivel?: (NivelUsuarioResponse | null);
    departamento?: (DepartamentoResponse | null);
    canal?: (CanalResponse | null);
};

