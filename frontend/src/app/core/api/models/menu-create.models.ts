/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { MenuOpcaoCreate } from './menu-opcao-create.models';
export type MenuCreate = {
    titulo: string;
    descricao?: (string | null);
    rodape?: (string | null);
    texto_botao?: string;
    canal_id?: (number | null);
    ativo?: boolean;
    opcoes?: Array<MenuOpcaoCreate>;
};

