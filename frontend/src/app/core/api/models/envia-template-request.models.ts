/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TemplateParametro } from './template-parametros.models';
export type EnviarTemplateRequest = {
    contato_nome: string;
    contato_telefone: string;
    conexao_nome: string;
    template_id: string;
    menu_id?: (number | null);
    language?: string;
    header_parameters?: Array<TemplateParametro>;
    body_parameters?: Array<TemplateParametro>;
};

