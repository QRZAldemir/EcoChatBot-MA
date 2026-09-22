/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { MenuOpcaoResponse } from './menu-opcao-response.models';
export type MenuResponse = {
    titulo: string;
    descricao?: (string | null);
    rodape?: (string | null);
    texto_botao?: string;
    canal_id?: (number | null);
    ativo?: boolean;
    id: number;
    criado_em: string;
    opcoes?: Array<MenuOpcaoResponse>;
};

